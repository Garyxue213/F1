"""
Data Server - Serves F1 telemetry and analysis data to Unity
Provides REST API for real-time data access during replay
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import csv
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
ANALYSIS_DIR = Path(os.getenv("ANALYSIS_DIR", "./analysis"))
AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "./audio"))


def load_csv_data(filepath):
    """Load CSV file as list of dicts"""
    data = []
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
    except Exception as e:
        print(f"Error loading CSV {filepath}: {e}")
    return data


def load_json_data(filepath):
    """Load JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON {filepath}: {e}")
        return None


@app.route('/', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'F1 Race Analysis Data Server',
        'version': '1.0'
    })


@app.route('/api/telemetry/<driver>', methods=['GET'])
def get_telemetry(driver):
    """Get telemetry data for a driver"""
    filepath = DATA_DIR / f"{driver}_telemetry.csv"

    if not filepath.exists():
        return jsonify({'error': f'Telemetry not found for {driver}'}), 404

    data = load_csv_data(filepath)

    # Convert numeric strings to numbers
    for point in data:
        for key in ['Time', 'Distance', 'Speed', 'Throttle', 'Brake', 'RPM', 'X', 'Y', 'Z']:
            if key in point:
                try:
                    point[key] = float(point[key])
                except:
                    pass

    return jsonify({
        'driver': driver,
        'count': len(data),
        'data': data
    })


@app.route('/api/optimal-line/<driver>', methods=['GET'])
def get_optimal_line(driver):
    """Get optimal line data"""
    filepath = DATA_DIR / f"{driver}_optimal_line.csv"

    if not filepath.exists():
        return jsonify({'error': f'Optimal line not found for {driver}'}), 404

    data = load_csv_data(filepath)

    # Convert numeric strings
    for point in data:
        for key in ['Time', 'Distance', 'Speed', 'Throttle', 'Brake', 'RPM', 'X', 'Y', 'Z', 'RelativeTime']:
            if key in point:
                try:
                    point[key] = float(point[key])
                except:
                    pass

    return jsonify({
        'driver': driver,
        'count': len(data),
        'data': data
    })


@app.route('/api/analysis/<driver>', methods=['GET'])
def get_analysis(driver):
    """Get analysis data for a driver"""
    filepath = ANALYSIS_DIR / f"{driver}_analysis.json"

    if not filepath.exists():
        return jsonify({'error': f'Analysis not found for {driver}'}), 404

    data = load_json_data(filepath)

    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'Failed to load analysis'}), 500


@app.route('/api/commentary/<driver>', methods=['GET'])
def get_commentary(driver):
    """Get commentary data with timestamps"""
    filepath = AUDIO_DIR / f"{driver}_commentary.csv"

    if not filepath.exists():
        return jsonify({'error': f'Commentary not found for {driver}'}), 404

    data = load_csv_data(filepath)

    # Convert numeric fields
    for item in data:
        for key in ['timestamp', 'speed_delta']:
            if key in item:
                try:
                    item[key] = float(item[key])
                except:
                    pass

    return jsonify({
        'driver': driver,
        'count': len(data),
        'data': data
    })


@app.route('/api/replay-data/<driver>', methods=['GET'])
def get_replay_data(driver):
    """Get all data needed for replay (telemetry + analysis + commentary)"""
    try:
        telemetry_file = DATA_DIR / f"{driver}_telemetry.csv"
        analysis_file = ANALYSIS_DIR / f"{driver}_analysis.json"
        commentary_file = AUDIO_DIR / f"{driver}_commentary.csv"

        telemetry = load_csv_data(telemetry_file) if telemetry_file.exists() else []
        analysis = load_json_data(analysis_file) if analysis_file.exists() else {}
        commentary = load_csv_data(commentary_file) if commentary_file.exists() else []

        # Convert numeric fields
        for point in telemetry:
            for key in ['Time', 'Distance', 'Speed', 'Throttle', 'Brake', 'RPM', 'X', 'Y', 'Z']:
                if key in point:
                    try:
                        point[key] = float(point[key])
                    except:
                        pass

        for item in commentary:
            for key in ['timestamp', 'speed_delta']:
                if key in item:
                    try:
                        item[key] = float(item[key])
                    except:
                        pass

        return jsonify({
            'driver': driver,
            'telemetry': {
                'count': len(telemetry),
                'data': telemetry[:1000]  # Limit to first 1000 points
            },
            'analysis': analysis,
            'commentary': {
                'count': len(commentary),
                'data': commentary
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/drivers', methods=['GET'])
def get_available_drivers():
    """Get list of available drivers"""
    drivers = set()

    # Find all drivers from telemetry files
    for file in DATA_DIR.glob('*_telemetry.csv'):
        driver = file.name.replace('_telemetry.csv', '')
        drivers.add(driver)

    return jsonify({
        'drivers': sorted(list(drivers))
    })


@app.route('/api/audio/<path:filename>', methods=['GET'])
def get_audio_file(filename):
    """Serve audio files"""
    filepath = AUDIO_DIR / filename

    if not filepath.exists():
        return jsonify({'error': 'Audio file not found'}), 404

    with open(filepath, 'rb') as f:
        audio_data = f.read()

    return audio_data, 200, {'Content-Type': 'audio/mpeg'}


@app.route('/api/race-summary', methods=['GET'])
def get_race_summary():
    """Get race summary with optimal line info"""
    try:
        summaries = {}

        for file in DATA_DIR.glob('*_optimal_summary.csv'):
            driver_name = file.name.replace('_optimal_summary.csv', '')
            data = load_csv_data(file)
            if data:
                summaries[driver_name] = data[0]

        return jsonify({
            'race': 'F1 2023 Australian GP',
            'drivers': summaries
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting F1 Data Server on http://localhost:5000")
    print("Available endpoints:")
    print("  GET /api/telemetry/<driver>")
    print("  GET /api/optimal-line/<driver>")
    print("  GET /api/analysis/<driver>")
    print("  GET /api/commentary/<driver>")
    print("  GET /api/replay-data/<driver>")
    print("  GET /api/drivers")
    print("  GET /api/race-summary")

    app.run(debug=True, host='0.0.0.0', port=5000)
