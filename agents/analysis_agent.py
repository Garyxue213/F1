"""
AnalysisAgent - Uses Gemini API to analyze driver performance vs optimal line
Generates insights with timestamps for commentary system
"""

import os
import pandas as pd
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import timedelta

load_dotenv(os.path.join(os.path.dirname(__file__), '../config/.env'))

class AnalysisAgent:
    def __init__(self):
        self.data_dir = Path(os.getenv("DATA_DIR", "./data"))
        self.analysis_dir = Path(os.getenv("ANALYSIS_DIR", "./analysis"))
        self.analysis_dir.mkdir(exist_ok=True)

        # Configure Gemini API
        self.api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def load_telemetry_data(self, driver_code):
        """Load driver telemetry from CSV"""
        filepath = self.data_dir / f"{driver_code}_telemetry.csv"
        if not filepath.exists():
            print(f"[Analysis] Telemetry file not found: {filepath}")
            return None

        df = pd.read_csv(filepath)
        print(f"[Analysis] Loaded {len(df)} telemetry points for {driver_code}")
        return df

    def load_optimal_line(self, driver_code):
        """Load optimal line benchmark"""
        filepath = self.data_dir / f"{driver_code}_optimal_line.csv"
        if not filepath.exists():
            print(f"[Analysis] Optimal line file not found: {filepath}")
            return None

        df = pd.read_csv(filepath)
        print(f"[Analysis] Loaded optimal line with {len(df)} points")
        return df

    def extract_track_sections(self, optimal_data, section_length=300):
        """Break lap into sections for analysis"""
        sections = []
        max_distance = optimal_data['Distance'].max()

        for start_dist in range(0, int(max_distance), section_length):
            end_dist = min(start_dist + section_length, max_distance)
            sections.append({
                'start': start_dist,
                'end': end_dist,
                'mid': (start_dist + end_dist) / 2
            })

        return sections

    def compare_section(self, driver_data, optimal_data, section):
        """Compare driver vs optimal in a track section"""
        start, end = section['start'], section['end']

        # Extract section data
        driver_section = driver_data[
            (driver_data['Distance'] >= start) &
            (driver_data['Distance'] <= end)
        ]
        optimal_section = optimal_data[
            (optimal_data['Distance'] >= start) &
            (optimal_data['Distance'] <= end)
        ]

        if driver_section.empty or optimal_section.empty:
            return None

        # Calculate metrics
        metrics = {
            'section_start': start,
            'section_end': end,
            'driver_avg_speed': driver_section['Speed'].mean(),
            'optimal_avg_speed': optimal_section['Speed'].mean(),
            'driver_avg_throttle': driver_section['Throttle'].mean(),
            'optimal_avg_throttle': optimal_section['Throttle'].mean(),
            'driver_avg_brake': driver_section['Brake'].mean(),
            'optimal_avg_brake': optimal_section['Brake'].mean(),
            'driver_min_speed': driver_section['Speed'].min(),
            'optimal_min_speed': optimal_section['Speed'].min(),
            'driver_max_speed': driver_section['Speed'].max(),
            'optimal_max_speed': optimal_section['Speed'].max(),
        }

        # Add timestamp
        if 'RelativeTime' in optimal_section.columns:
            metrics['timestamp'] = optimal_section.iloc[len(optimal_section)//2]['RelativeTime']
        else:
            metrics['timestamp'] = (end - start) / 100  # Approximate

        return metrics

    def generate_insight(self, driver_code, optimal_driver, metrics):
        """Use Gemini to generate analytical insight"""
        try:
            prompt = f"""You are 'Apex', an elite Formula 1 performance engineer analyzing driver telemetry.

Analyze this data for track section {metrics['section_start']:.0f}m - {metrics['section_end']:.0f}m:

OPTIMAL LINE ({optimal_driver}):
- Average Speed: {metrics['optimal_avg_speed']:.1f} km/h
- Min Speed (apex): {metrics['optimal_min_speed']:.1f} km/h
- Max Speed: {metrics['optimal_max_speed']:.1f} km/h
- Throttle: {metrics['optimal_avg_throttle']:.0f}%
- Braking: {metrics['optimal_avg_brake']:.0f}%

LIVE DRIVER ({driver_code}):
- Average Speed: {metrics['driver_avg_speed']:.1f} km/h
- Min Speed (apex): {metrics['driver_min_speed']:.1f} km/h
- Max Speed: {metrics['driver_max_speed']:.1f} km/h
- Throttle: {metrics['driver_avg_throttle']:.0f}%
- Braking: {metrics['driver_avg_brake']:.0f}%

Provide a single, concise insight (max 25 words) explaining the performance difference and time gain/loss. Focus on cause and effect, not just data."""

            response = self.model.generate_content(prompt)
            insight_text = response.text.strip()

            # Clean up the insight
            if len(insight_text) > 150:
                insight_text = insight_text[:150] + "..."

            return insight_text
        except Exception as e:
            print(f"[Analysis] Error generating insight: {e}")
            return f"Speed delta: {metrics['driver_avg_speed'] - metrics['optimal_avg_speed']:+.1f} km/h"

    def detect_events(self, driver_data, optimal_data):
        """Detect significant events (lock-ups, high speed, etc.)"""
        events = []

        # Detect lock-ups (rapid brake application)
        for idx in range(1, len(driver_data)):
            brake_delta = driver_data.iloc[idx]['Brake'] - driver_data.iloc[idx-1]['Brake']
            if brake_delta > 0.5:  # Sudden brake application
                events.append({
                    'type': 'brake_lock',
                    'timestamp': driver_data.iloc[idx]['RelativeTime'] if 'RelativeTime' in driver_data.columns else idx,
                    'distance': driver_data.iloc[idx]['Distance'],
                    'severity': brake_delta
                })

        # Detect high speed sections
        high_speed_threshold = driver_data['Speed'].quantile(0.85)
        for idx in range(len(driver_data)):
            if driver_data.iloc[idx]['Speed'] > high_speed_threshold:
                if not events or events[-1]['type'] != 'high_speed':
                    events.append({
                        'type': 'high_speed',
                        'timestamp': driver_data.iloc[idx]['RelativeTime'] if 'RelativeTime' in driver_data.columns else idx,
                        'distance': driver_data.iloc[idx]['Distance'],
                        'speed': driver_data.iloc[idx]['Speed']
                    })

        return events

    def save_analysis(self, analysis_data, driver_code):
        """Save analysis to JSON"""
        filepath = self.analysis_dir / f"{driver_code}_analysis.json"
        with open(filepath, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        print(f"[Analysis] Saved analysis to {filepath}")
        return filepath

    def run(self, driver_codes=None, optimal_driver="VER"):
        """Main execution"""
        if driver_codes is None:
            driver_codes = ["ALO"]  # Analyze ALO against optimal

        print(f"\n{'='*60}")
        print(f"AnalysisAgent: Generating Performance Insights")
        print(f"{'='*60}\n")

        # Load optimal line
        optimal_data = self.load_optimal_line(optimal_driver)
        if optimal_data is None:
            print("[Analysis] Cannot load optimal line data")
            return None

        # Analyze each driver
        all_insights = {}
        sections = self.extract_track_sections(optimal_data, section_length=300)

        for driver_code in driver_codes:
            print(f"\n[Analysis] Analyzing {driver_code}...")

            driver_data = self.load_telemetry_data(driver_code)
            if driver_data is None:
                continue

            insights = []
            for section in sections:
                metrics = self.compare_section(driver_data, optimal_data, section)
                if metrics is None:
                    continue

                insight_text = self.generate_insight(driver_code, optimal_driver, metrics)

                insight_obj = {
                    'timestamp': metrics['timestamp'],
                    'section_start': metrics['section_start'],
                    'section_end': metrics['section_end'],
                    'insight': insight_text,
                    'speed_delta': metrics['driver_avg_speed'] - metrics['optimal_avg_speed'],
                    'metrics': metrics
                }
                insights.append(insight_obj)

            # Detect events
            events = self.detect_events(driver_data, optimal_data)

            analysis_data = {
                'driver': driver_code,
                'optimal_reference': optimal_driver,
                'insights': insights,
                'events': events
            }

            self.save_analysis(analysis_data, driver_code)
            all_insights[driver_code] = analysis_data

        print(f"\n[Analysis] Analysis complete!")
        return all_insights


if __name__ == "__main__":
    agent = AnalysisAgent()
    insights = agent.run(driver_codes=["ALO"], optimal_driver="VER")
