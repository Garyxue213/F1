"""
DataIngestionAgent - Fetches and prepares F1 telemetry data
Loads 2023 Australian GP data for top 2 drivers and exports to CSV
"""

import os
import sys
import pandas as pd
import fastf1
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../config/.env'))

class DataIngestionAgent:
    def __init__(self, year=2023, grand_prix="Australian", session="R"):
        self.year = year
        self.grand_prix = grand_prix
        self.session = session
        self.data_dir = Path(os.getenv("DATA_DIR", "./data"))
        self.data_dir.mkdir(exist_ok=True)

    def fetch_session_data(self):
        """Fetch session data from FastF1"""
        print(f"[DataIngestion] Fetching {self.year} {self.grand_prix} GP {self.session} session...")
        try:
            session = fastf1.get_session(self.year, self.grand_prix, self.session)
            session.load(telemetry=True)
            print(f"[DataIngestion] Session loaded successfully")
            return session
        except Exception as e:
            print(f"[DataIngestion] Error fetching session: {e}")
            raise

    def extract_driver_laps(self, session, driver_code):
        """Extract telemetry for a specific driver"""
        print(f"[DataIngestion] Extracting data for {driver_code}...")
        try:
            driver_laps = session.laps.pick_driver(driver_code)
            if driver_laps.empty:
                print(f"[DataIngestion] No laps found for driver {driver_code}")
                return None

            print(f"[DataIngestion] Found {len(driver_laps)} laps for {driver_code}")
            return driver_laps
        except Exception as e:
            print(f"[DataIngestion] Error extracting laps for {driver_code}: {e}")
            raise

    def prepare_telemetry_data(self, driver_laps, driver_code):
        """Convert lap data to telemetry DataFrame"""
        telemetry_data = []

        for idx, lap in driver_laps.iterrows():
            if lap['IsAccurate']:
                try:
                    car_data = lap.get_car_data().add_distance()
                    car_data['Driver'] = driver_code
                    car_data['LapNumber'] = lap['LapNumber']
                    car_data['LapTime'] = lap['LapTime'].total_seconds() if pd.notna(lap['LapTime']) else None
                    telemetry_data.append(car_data)
                except Exception as e:
                    print(f"[DataIngestion] Warning: Could not process lap {lap['LapNumber']} for {driver_code}: {e}")

        if telemetry_data:
            combined = pd.concat(telemetry_data, ignore_index=True)
            print(f"[DataIngestion] Prepared {len(combined)} telemetry points for {driver_code}")
            return combined
        return None

    def save_to_csv(self, data, filename):
        """Save DataFrame to CSV"""
        filepath = self.data_dir / filename
        data.to_csv(filepath, index=False)
        print(f"[DataIngestion] Saved to {filepath}")
        return filepath

    def run(self, driver_codes=None):
        """Main execution method"""
        if driver_codes is None:
            driver_codes = ["VER", "ALO"]  # Top 2 from 2023 Australian GP

        print(f"\n{'='*60}")
        print(f"DataIngestionAgent: {self.year} {self.grand_prix} GP")
        print(f"{'='*60}\n")

        session = self.fetch_session_data()

        all_telemetry = {}
        for driver_code in driver_codes:
            try:
                driver_laps = self.extract_driver_laps(session, driver_code)
                if driver_laps is not None:
                    telemetry = self.prepare_telemetry_data(driver_laps, driver_code)
                    if telemetry is not None:
                        all_telemetry[driver_code] = telemetry
                        self.save_to_csv(telemetry, f"{driver_code}_telemetry.csv")
            except Exception as e:
                print(f"[DataIngestion] Failed to process {driver_code}: {e}")

        # Save combined telemetry
        if all_telemetry:
            combined = pd.concat(all_telemetry.values(), ignore_index=True)
            self.save_to_csv(combined, "combined_telemetry.csv")
            print(f"\n[DataIngestion] Data ingestion complete!")
            print(f"[DataIngestion] Total data points: {len(combined)}")
            return combined

        return None


if __name__ == "__main__":
    agent = DataIngestionAgent(year=2023, grand_prix="Australian", session="R")
    telemetry = agent.run(driver_codes=["VER", "ALO"])
