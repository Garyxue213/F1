# Project Apex - AI-Driven F1 Race Analysis System

An advanced multi-agent AI system that analyzes Formula 1 telemetry data, compares driver performance against optimal racing lines, generates expert insights using Google Gemini, and delivers dynamic audio commentary via ElevenLabs TTS.

## 🏁 System Architecture

```
DataIngestionAgent
       ↓
  (FastF1 API)
       ↓
OptimizationAgent
       ↓
  (Find Optimal Line)
       ↓
AnalysisAgent (Gemini API)
       ↓
  (Generate Insights)
       ↓
CommentaryAgent (ElevenLabs)
       ↓
  (Audio Generation)
       ↓
Unity Replay System
       ↓
  (Visualization + Commentary)
```

## 📋 Features

- **Real-time F1 Data Analysis**: Fetches live telemetry from 2023 Australian GP
- **AI-Powered Insights**: Uses Google Gemini to generate expert performance analysis
- **Dynamic Commentary**: ElevenLabs TTS converts insights to broadcast-quality audio
- **Interactive Replay System**: Unity-based visualization with speed control
- **Timestamp Synchronization**: Commentary plays at exact race moments (overtaking, crashes, lap summaries)
- **Event Detection**: Identifies significant driving moments (brake lock-ups, high-speed zones)
- **Performance Metrics**: Detailed comparison of driver vs optimal lap data

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js (for MCP server, optional)
- Unity 2021.3+ (for replay visualization)
- API Keys:
  - Google Gemini API Key
  - ElevenLabs API Key

### Installation

1. **Clone and Setup**
```bash
cd /Users/gary/Desktop/HackTX/F1-RacingSim
pip install -r requirements.txt
```

2. **Configure API Keys**
Edit `config/.env`:
```env
GEMINI_API_KEY=your_gemini_key
ELEVENLABS_API_KEY=your_elevenlabs_key
F1_YEAR=2023
F1_GRAND_PRIX=Australian
F1_SESSION=R
F1_DRIVERS=["VER", "ALO"]
```

3. **Run the Analysis Pipeline**
```bash
python orchestrator.py --year 2023 --grand-prix Australian --drivers VER,ALO --skip-audio
```

This generates:
- `data/VER_telemetry.csv` - Verstappen telemetry
- `data/ALO_telemetry.csv` - Alonso telemetry
- `data/VER_optimal_line.csv` - Optimal racing line (fastest lap)
- `analysis/ALO_analysis.json` - Performance insights
- `audio/ALO_commentary.csv` - Timed commentary
- `replay_manifest.json` - Replay configuration

### Running Agents Individually

```bash
# Step 1: Fetch telemetry data
python -m agents.data_ingestion_agent

# Step 2: Find optimal racing line
python -m agents.optimization_agent

# Step 3: Generate AI insights (requires Gemini API)
python -m agents.analysis_agent

# Step 4: Generate audio commentary (requires ElevenLabs API)
python -m agents.commentary_agent --skip-audio  # or remove --skip-audio to enable TTS
```

### Data Server (for Unity)

```bash
python data_server.py
# Server runs on http://localhost:5000

# Test endpoints:
curl http://localhost:5000/api/drivers
curl http://localhost:5000/api/telemetry/ALO
curl http://localhost:5000/api/analysis/ALO
curl http://localhost:5000/api/commentary/ALO
```

## 📊 Data Formats

### Telemetry CSV
```
Time,Distance,Speed,Throttle,Brake,RPM,DRS,X,Y,Z,Driver,LapNumber,LapTime
0.0,0.0,150.5,0.75,0.0,12000,0,1234.5,0,5678.9,VER,1,95.234
...
```

### Analysis JSON
```json
{
  "driver": "ALO",
  "optimal_reference": "VER",
  "insights": [
    {
      "timestamp": 15.3,
      "section_start": 0,
      "section_end": 300,
      "insight": "Braking 5m too late, compromising apex speed.",
      "speed_delta": -2.5
    }
  ],
  "events": [
    {
      "type": "brake_lock",
      "timestamp": 45.2,
      "distance": 2345.0,
      "severity": 0.85
    }
  ]
}
```

### Commentary CSV
```
timestamp,text,type,speed_delta,audio_file
0.0,Analyzing ALO's lap performance.,intro,0.0,ALO_commentary_0.mp3
15.3,Braking 5m too late...,insight,-2.5,ALO_commentary_1.mp3
...
```

## 🎮 Unity Integration

1. **Import Scripts**
   - Copy `Assets/Scripts/*.cs` to your Unity project

2. **Setup Scene**
   - Create Canvas with UI elements:
     - Text: TimeDisplay, SpeedDisplay, CommentaryDisplay
     - Slider: PlaybackSpeedSlider, SeekSlider
     - Dropdown: DriverDropdown, PlaybackSpeedDropdown
     - Buttons: PlayButton, PauseButton

3. **Attach F1ReplaySystem**
   - Add `F1ReplaySystem` component to game object
   - Configure UI references in inspector
   - Set telemetry and commentary data paths

4. **Run Replay**
   - Press Play in Unity
   - Select driver from dropdown
   - Use playback controls
   - Commentary syncs with replay

## 🔍 Event Detection

The system detects and timestamps:
- **Brake Lock-ups**: Sudden brake applications
- **High-Speed Zones**: Sections above 85th percentile speed
- **Overtaking Moments**: Speed delta changes
- **Lap Summaries**: End-of-lap commentary

## 📈 Performance Metrics

For each track section:
- Average speed comparison
- Apex speed (minimum speed)
- Throttle/brake application patterns
- Time gains/losses vs optimal
- Track position (X, Y, Z coordinates)

## 🔐 Security

- API keys stored in `.env` (not in version control)
- Data files not included in repo
- HTTPS for external API calls
- CORS configured for local development

## 📁 Project Structure

```
F1-RacingSim/
├── config/
│   └── .env                    # API keys and configuration
├── agents/
│   ├── data_ingestion_agent.py # Fetches F1 data
│   ├── optimization_agent.py   # Finds optimal line
│   ├── analysis_agent.py       # Gemini insights
│   └── commentary_agent.py     # ElevenLabs TTS
├── Assets/Scripts/
│   ├── F1ReplaySystem.cs       # Main replay controller
│   └── F1CarController.cs      # Car visualization
├── data/                       # Generated telemetry CSVs
├── analysis/                   # Generated analysis JSONs
├── audio/                      # Generated audio files
├── orchestrator.py             # Pipeline orchestrator
├── data_server.py              # Flask API server
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🎯 Next Steps

1. Run orchestrator to generate analysis data
2. Start data server: `python data_server.py`
3. Open Unity project and run replay scene
4. Select driver and enjoy synchronized commentary!

## 🐛 Troubleshooting

### "FastF1 API timeout"
- Wait a few minutes - FastF1 rate limits requests
- Check your internet connection

### "Gemini API error"
- Verify API key in `.env`
- Check Gemini API quota/billing

### "ElevenLabs API error"
- Use `--skip-audio` flag during development
- Verify API key and account balance

### "No telemetry data loaded in Unity"
- Ensure CSV files are in `Assets/StreamingAssets/data/`
- Check file paths in F1ReplaySystem inspector

### "Commentary not syncing"
- Verify commentary CSV is being loaded
- Check timestamps in analysis data

## 📚 References

- [FastF1 Documentation](https://docs.fastf1.dev/)
- [Google Gemini API](https://ai.google.dev/)
- [ElevenLabs API](https://elevenlabs.io/docs)
- [Formula 1 2023 Season](https://www.formula1.com/)

## 🎓 hackathon Submission

**Event**: HackTX 2024
**Category**: AI/Machine Learning + Game Development
**Team**: Project Apex

## 📝 License

MIT License - See LICENSE file

---

**Built with**: Python • Google Gemini • ElevenLabs • Unity • FastF1
# F1
