"""
OptimizationAgent - Identifies optimal racing line from fastest lap
Creates benchmark data for comparison
"""

import os
import pandas as pd
import fastf1
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../config/.env'))

class OptimizationAgent:
    def __init__(self, year=2023, grand_prix="Australian", session="R"):
        self.year = year
        self.grand_prix = grand_prix
        self.session = session
        self.data_dir = Path(os.getenv("DATA_DIR", "./data"))
        self.data_dir.mkdir(exist_ok=True)

    def fetch_session(self):
        """Fetch session data"""
        print(f"[Optimization] Fetching {self.year} {self.grand_prix} GP {self.session} session...")
        session = fastf1.get_session(self.year, self.grand_prix, self.session)
        session.load(telemetry=True)
        return session

    def find_fastest_lap(self, session, driver_codes=None):
        """Find fastest lap among specified drivers"""
        if driver_codes is None:
            driver_codes = ["VER", "ALO"]

        print(f"[Optimization] Finding fastest lap among {driver_codes}...")

        fastest_lap = None
        fastest_time = float('inf')
        fastest_driver = None

        for driver_code in driver_codes:
            try:
                driver_laps = session.laps.pick_driver(driver_code)
                valid_laps = driver_laps[driver_laps['IsAccurate']]

                if not valid_laps.empty:
                    best_lap = valid_laps.iloc[valid_laps['LapTime'].argmin()]
                    lap_time = best_lap['LapTime'].total_seconds()

                    if lap_time < fastest_time:
                        fastest_time = lap_time
                        fastest_lap = best_lap
                        fastest_driver = driver_code
                        print(f"[Optimization] {driver_code} best lap: {lap_time:.2f}s")
            except Exception as e:
                print(f"[Optimization] Error processing {driver_code}: {e}")

        if fastest_lap is not None:
            print(f"[Optimization] Fastest lap: {fastest_driver} with {fastest_time:.2f}s")
            return fastest_lap, fastest_driver, fastest_time

        return None, None, None

    def extract_optimal_line(self, lap):
        """Extract telemetry from fastest lap as optimal line"""
        print(f"[Optimization] Extracting optimal line telemetry...")
        try:
            car_data = lap.get_car_data().add_distance()
            car_data = car_data[['Time', 'Distance', 'Speed', 'Throttle', 'Brake', 'RPM', 'DRS', 'X', 'Y', 'Z']].copy()
            car_data['IsOptimal'] = True

            # Calculate relative time
            car_data['RelativeTime'] = (car_data['Time'] - car_data['Time'].iloc[0]).dt.total_seconds()

            print(f"[Optimization] Extracted {len(car_data)} data points from optimal lap")
            return car_data
        except Exception as e:
            print(f"[Optimization] Error extracting optimal line: {e}")
            raise

    def create_lookup_function(self, optimal_data):
        """Create a lookup function for optimal parameters at any distance"""
        def get_optimal_at_distance(distance):
            """Get optimal params at given distance along track"""
            idx = (optimal_data['Distance'] - distance).abs().argmin()
            row = optimal_data.iloc[idx]
            return {
                'distance': row['Distance'],
                'speed': row['Speed'],
                'throttle': row['Throttle'],
                'brake': row['Brake'],
                'time': row['RelativeTime'],
                'x': row['X'],
                'y': row['Y'],
                'z': row['Z']
            }

        return get_optimal_at_distance

    def save_optimal_benchmark(self, optimal_data, driver):
        """Save optimal line benchmark"""
        filepath = self.data_dir / f"{driver}_optimal_line.csv"
        optimal_data.to_csv(filepath, index=False)
        print(f"[Optimization] Saved optimal line to {filepath}")

        # Create summary stats
        summary = {
            'Driver': driver,
            'TotalDistance': optimal_data['Distance'].max(),
            'LapTime': optimal_data['RelativeTime'].max(),
            'AvgSpeed': optimal_data['Speed'].mean(),
            'MaxSpeed': optimal_data['Speed'].max(),
            'MinSpeed': optimal_data['Speed'].min()
        }

        summary_df = pd.DataFrame([summary])
        summary_filepath = self.data_dir / f"{driver}_optimal_summary.csv"
        summary_df.to_csv(summary_filepath, index=False)
        print(f"[Optimization] Saved summary to {summary_filepath}")

        return filepath, summary

    def run(self, driver_codes=None):
        """Main execution"""
        if driver_codes is None:
            driver_codes = ["VER", "ALO"]

        print(f"\n{'='*60}")
        print(f"OptimizationAgent: Finding Optimal Racing Line")
        print(f"{'='*60}\n")

        session = self.fetch_session()
        fastest_lap, driver, lap_time = self.find_fastest_lap(session, driver_codes)

        if fastest_lap is None:
            print("[Optimization] Failed to find fastest lap")
            return None, None

        optimal_line = self.extract_optimal_line(fastest_lap)
        benchmark_path, summary = self.save_optimal_benchmark(optimal_line, driver)

        print(f"\n[Optimization] Optimization complete!")
        print(f"[Optimization] Ghost car driver: {driver}")
        print(f"[Optimization] Optimal lap time: {lap_time:.2f}s")
        print(f"[Optimization] Track length: {summary[0]['TotalDistance']:.0f}m")

        return optimal_line, summary[0]


if __name__ == "__main__":
    agent = OptimizationAgent(year=2023, grand_prix="Australian", session="R")
    optimal_line, summary = agent.run(driver_codes=["VER", "ALO"])
