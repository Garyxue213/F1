"""
Project Apex - Main Orchestrator
Chains all agents together: DataIngestion -> Optimization -> Analysis -> Commentary
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add agents to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from agents.data_ingestion_agent import DataIngestionAgent
from agents.optimization_agent import OptimizationAgent
from agents.analysis_agent import AnalysisAgent
from agents.commentary_agent import CommentaryAgent


class ProjectApexOrchestrator:
    def __init__(self, year=2023, grand_prix="Australian", session="R"):
        self.year = year
        self.grand_prix = grand_prix
        self.session = session
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log(self, message):
        """Print timestamped log message"""
        print(f"[{self.timestamp}] {message}")

    def run_pipeline(self, driver_codes=None, skip_commentary_audio=False):
        """Execute complete analysis pipeline"""
        if driver_codes is None:
            driver_codes = ["VER", "ALO"]

        print("\n" + "="*80)
        print("PROJECT APEX - F1 Race Analysis System")
        print(f"Race: {self.year} {self.grand_prix} GP")
        print(f"Drivers: {', '.join(driver_codes)}")
        print("="*80 + "\n")

        try:
            # Step 1: Data Ingestion
            print("\n[STEP 1/4] DATA INGESTION")
            print("-" * 80)
            data_agent = DataIngestionAgent(year=self.year, grand_prix=self.grand_prix, session=self.session)
            telemetry_data = data_agent.run(driver_codes=driver_codes)

            if telemetry_data is None:
                print("[PIPELINE] Failed at data ingestion step")
                return False

            # Step 2: Optimization (find optimal line)
            print("\n[STEP 2/4] OPTIMIZATION - Finding Optimal Racing Line")
            print("-" * 80)
            opt_agent = OptimizationAgent(year=self.year, grand_prix=self.grand_prix, session=self.session)
            optimal_line, optimal_summary = opt_agent.run(driver_codes=driver_codes)

            if optimal_line is None:
                print("[PIPELINE] Failed at optimization step")
                return False

            optimal_driver = optimal_summary['Driver'] if optimal_summary else driver_codes[0]

            # Step 3: Analysis (compare drivers to optimal)
            print("\n[STEP 3/4] ANALYSIS - Generating Performance Insights")
            print("-" * 80)
            analysis_agent = AnalysisAgent()

            # Analyze all drivers except the one used for optimal
            analysis_drivers = [d for d in driver_codes if d != optimal_driver]
            insights = analysis_agent.run(driver_codes=analysis_drivers, optimal_driver=optimal_driver)

            if insights is None:
                print("[PIPELINE] Failed at analysis step")
                return False

            # Step 4: Commentary (generate audio)
            print("\n[STEP 4/4] COMMENTARY - Generating Audio Commentary")
            print("-" * 80)
            commentary_agent = CommentaryAgent()
            commentary = commentary_agent.run(driver_codes=analysis_drivers, skip_audio=skip_commentary_audio)

            if commentary is None:
                print("[PIPELINE] Failed at commentary step")
                return False

            # Pipeline complete
            print("\n" + "="*80)
            print("PIPELINE EXECUTION COMPLETE!")
            print("="*80)
            print("\nGenerated Files:")
            print(f"  Telemetry: data/*_telemetry.csv")
            print(f"  Optimal Line: data/*_optimal_line.csv")
            print(f"  Analysis: analysis/*_analysis.json")
            print(f"  Commentary: audio/*_commentary.csv")
            print(f"  Audio Files: audio/*_commentary_*.mp3")
            print("\nReady for Unity replay system integration!\n")

            return True

        except Exception as e:
            print(f"\n[PIPELINE ERROR] {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_replay_manifest(self):
        """Generate manifest for Unity replay system"""
        manifest = {
            'race': {
                'year': self.year,
                'grand_prix': self.grand_prix,
                'session': self.session
            },
            'data_files': {
                'telemetry': 'data/combined_telemetry.csv',
                'optimal_line': 'data/{DRIVER}_optimal_line.csv',
                'analysis': 'analysis/{DRIVER}_analysis.json',
                'commentary': 'audio/{DRIVER}_commentary.csv'
            },
            'replay_config': {
                'frame_rate': 30,
                'default_speed': 1.0,
                'playback_speeds': [0.25, 0.5, 1.0, 1.5, 2.0, 4.0]
            }
        }

        manifest_path = Path("replay_manifest.json")
        import json
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"[ORCHESTRATOR] Generated replay manifest: {manifest_path}")
        return manifest


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Project Apex - F1 Race Analysis System")
    parser.add_argument("--year", type=int, default=2023, help="Race year")
    parser.add_argument("--grand-prix", type=str, default="Australian", help="Grand Prix name")
    parser.add_argument("--session", type=str, default="R", help="Session type (R=Race, Q=Quali)")
    parser.add_argument("--drivers", type=str, default="VER,ALO", help="Drivers to analyze (comma-separated)")
    parser.add_argument("--skip-audio", action="store_true", help="Skip ElevenLabs audio generation")
    parser.add_argument("--manifest-only", action="store_true", help="Only generate replay manifest")

    args = parser.parse_args()

    orchestrator = ProjectApexOrchestrator(
        year=args.year,
        grand_prix=args.grand_prix,
        session=args.session
    )

    if args.manifest_only:
        orchestrator.generate_replay_manifest()
    else:
        driver_list = [d.strip().upper() for d in args.drivers.split(',')]
        success = orchestrator.run_pipeline(driver_codes=driver_list, skip_commentary_audio=args.skip_audio)

        if success:
            orchestrator.generate_replay_manifest()
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
