"""
CommentaryAgent - Converts analysis insights to timed audio commentary
Uses ElevenLabs API for text-to-speech
"""

import os
import json
import csv
from pathlib import Path
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv(os.path.join(os.path.dirname(__file__), '../config/.env'))

class CommentaryAgent:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.data_dir = Path(os.getenv("DATA_DIR", "./data"))
        self.analysis_dir = Path(os.getenv("ANALYSIS_DIR", "./analysis"))
        self.audio_dir = Path(os.getenv("AUDIO_DIR", "./audio"))
        self.audio_dir.mkdir(exist_ok=True)

        self.base_url = "https://api.elevenlabs.io/v1"
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice

    def load_analysis(self, driver_code):
        """Load analysis insights from JSON"""
        filepath = self.analysis_dir / f"{driver_code}_analysis.json"
        if not filepath.exists():
            print(f"[Commentary] Analysis file not found: {filepath}")
            return None

        with open(filepath, 'r') as f:
            data = json.load(f)

        print(f"[Commentary] Loaded analysis with {len(data.get('insights', []))} insights")
        return data

    def create_commentary_script(self, analysis_data, driver_code):
        """Create full commentary script with timestamps"""
        insights = analysis_data.get('insights', [])
        events = analysis_data.get('events', [])

        commentary_items = []

        # Add intro
        commentary_items.append({
            'timestamp': 0.0,
            'text': f"Analyzing {driver_code}'s lap performance.",
            'type': 'intro'
        })

        # Add section insights
        for insight in insights:
            commentary_items.append({
                'timestamp': insight.get('timestamp', 0),
                'text': insight.get('insight', 'Data mismatch detected.'),
                'type': 'insight',
                'speed_delta': insight.get('speed_delta', 0)
            })

        # Add events
        for event in events:
            event_type = event.get('type', 'unknown')
            timestamp = event.get('timestamp', 0)

            if event_type == 'brake_lock':
                text = f"Brake application at distance {event.get('distance', 0):.0f} meters."
            elif event_type == 'high_speed':
                text = f"High speed zone detected. Speed: {event.get('speed', 0):.0f} km/h."
            else:
                text = f"Event detected: {event_type}"

            commentary_items.append({
                'timestamp': timestamp,
                'text': text,
                'type': 'event'
            })

        # Sort by timestamp
        commentary_items.sort(key=lambda x: x['timestamp'])

        return commentary_items

    def synthesize_speech(self, text):
        """Call ElevenLabs API to generate speech"""
        try:
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"

            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }

            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                return response.content
            else:
                print(f"[Commentary] ElevenLabs error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"[Commentary] Error synthesizing speech: {e}")
            return None

    def save_commentary_csv(self, commentary_items, driver_code):
        """Save commentary with timestamps to CSV for replay system"""
        filepath = self.audio_dir / f"{driver_code}_commentary.csv"

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'text', 'type', 'speed_delta', 'audio_file'])
            writer.writeheader()

            for idx, item in enumerate(commentary_items):
                row = {
                    'timestamp': item.get('timestamp', 0),
                    'text': item.get('text', ''),
                    'type': item.get('type', ''),
                    'speed_delta': item.get('speed_delta', 0),
                    'audio_file': f"{driver_code}_commentary_{idx}.mp3"
                }
                writer.writerow(row)

        print(f"[Commentary] Saved commentary CSV to {filepath}")
        return filepath

    def save_commentary_json(self, commentary_items, driver_code):
        """Save commentary as JSON for debugging"""
        filepath = self.audio_dir / f"{driver_code}_commentary.json"

        with open(filepath, 'w') as f:
            json.dump(commentary_items, f, indent=2, default=str)

        print(f"[Commentary] Saved commentary JSON to {filepath}")
        return filepath

    def generate_audio_files(self, commentary_items, driver_code, skip_audio=False):
        """Generate audio files for each commentary item"""
        print(f"[Commentary] Generating audio files for {driver_code}...")

        for idx, item in enumerate(commentary_items):
            text = item.get('text', '')
            if not text or len(text.strip()) == 0:
                print(f"[Commentary] Skipping empty text at index {idx}")
                continue

            print(f"[Commentary] Generating audio {idx+1}/{len(commentary_items)}: '{text[:50]}...'")

            if not skip_audio:
                audio_content = self.synthesize_speech(text)

                if audio_content:
                    audio_file = self.audio_dir / f"{driver_code}_commentary_{idx}.mp3"
                    with open(audio_file, 'wb') as f:
                        f.write(audio_content)
                    print(f"[Commentary] Saved audio to {audio_file}")
                else:
                    print(f"[Commentary] Failed to generate audio for item {idx}")
            else:
                print(f"[Commentary] Skipping audio generation (demo mode)")

    def run(self, driver_codes=None, skip_audio=False):
        """Main execution"""
        if driver_codes is None:
            driver_codes = ["ALO"]

        print(f"\n{'='*60}")
        print(f"CommentaryAgent: Generating Commentary Audio")
        print(f"{'='*60}\n")

        all_commentary = {}

        for driver_code in driver_codes:
            print(f"\n[Commentary] Processing {driver_code}...")

            # Load analysis
            analysis_data = self.load_analysis(driver_code)
            if analysis_data is None:
                continue

            # Create commentary script
            commentary_items = self.create_commentary_script(analysis_data, driver_code)
            print(f"[Commentary] Created {len(commentary_items)} commentary items")

            # Save CSVs
            self.save_commentary_csv(commentary_items, driver_code)
            self.save_commentary_json(commentary_items, driver_code)

            # Generate audio (optionally skip for demo)
            if not skip_audio:
                self.generate_audio_files(commentary_items, driver_code, skip_audio=skip_audio)

            all_commentary[driver_code] = commentary_items

        print(f"\n[Commentary] Commentary generation complete!")
        return all_commentary


if __name__ == "__main__":
    agent = CommentaryAgent()
    # Set skip_audio=True for demo mode without ElevenLabs calls
    commentary = agent.run(driver_codes=["ALO"], skip_audio=False)
