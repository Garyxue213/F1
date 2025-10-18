# 🏁 Project Apex - Quick Start Guide

## ⚡ 5-Minute Setup

### Step 1: Initialize (1 minute)
```bash
cd /Users/gary/Desktop/HackTX/F1-RacingSim
bash setup.sh
```

### Step 2: Add API Keys (2 minutes)
Edit `config/.env`:
```bash
nano config/.env
```

Add your keys:
```env
GEMINI_API_KEY=your_gemini_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

Save and exit.

### Step 3: Generate Analysis Data (2 minutes)
```bash
python orchestrator.py --year 2023 --grand-prix Australian --drivers VER,ALO --skip-audio
```

**What you get:**
- `data/VER_telemetry.csv` - Verstappen's lap data
- `data/ALO_telemetry.csv` - Alonso's lap data
- `data/VER_optimal_line.csv` - Optimal racing line
- `analysis/ALO_analysis.json` - AI insights with timestamps
- `replay_manifest.json` - Unity configuration

---

## 🎮 Running the Replay

### Terminal 1: Start Data Server
```bash
python data_server.py
# Server runs on http://localhost:5000
```

### Terminal 2: Run Unity
1. Open Unity project
2. Create a Canvas with UI elements:
   - `TimeDisplay` (Text)
   - `SpeedDisplay` (Text)
   - `CommentaryDisplay` (Text)
   - `PlayButton` (Button)
   - `PauseButton` (Button)
   - `PlaybackSpeedDropdown` (Dropdown)
   - `DriverDropdown` (Dropdown)
   - `SeekSlider` (Slider)
   - `SpeedIndicator` (Image)

3. Create GameObjects:
   - Add `F1ReplaySystem` component to main game object
   - Add `F1CarController` component to car model

4. Press Play in Unity Editor

### Controls
- **▶️ Play** - Start replay
- **⏸️ Pause** - Pause replay
- **Playback Speed** - 0.25x to 4.0x
- **Seek Slider** - Jump to any moment
- **Driver Dropdown** - Switch between VER/ALO
- **Speed Indicator** - Color-coded speed (blue→red)

---

## 📊 Verify Installation

### Check Data Files
```bash
ls -la data/
ls -la analysis/
ls -la audio/
```

### Test API Server
```bash
# Open new terminal while server is running
curl http://localhost:5000/api/drivers
curl http://localhost:5000/api/telemetry/ALO
curl http://localhost:5000/api/analysis/ALO
```

### Expected Output
```json
{
  "drivers": ["VER", "ALO"]
}
```

---

## 🎯 Demo Mode (No API Costs)

### Generate Analysis Without Audio
```bash
python orchestrator.py --year 2023 --grand-prix Australian --drivers VER,ALO --skip-audio
```

This saves money by:
- ✅ Generating telemetry CSVs
- ✅ Creating Gemini insights
- ✅ Generating commentary CSVs
- ❌ Skipping ElevenLabs audio generation

Commentary text is still available in CSVs for display.

---

## 🐛 Troubleshooting

### "FastF1 timeout"
```bash
# Wait 30 seconds and try again (API rate limit)
sleep 30
python orchestrator.py --year 2023 --grand-prix Australian --drivers VER,ALO --skip-audio
```

### "Gemini API error"
- Check your API key in `config/.env`
- Verify API is enabled in Google Cloud Console
- Check quota/rate limits

### "No telemetry displayed in Unity"
- Ensure CSV files exist in `data/`
- Check paths in F1ReplaySystem inspector
- Verify CSV format (comma-separated values)

### "Server won't start"
```bash
# Check if port 5000 is in use
lsof -i :5000
# Kill process if needed
kill -9 <PID>
```

---

## 📈 Understanding the Output

### Telemetry CSV
```
Time,Distance,Speed,Throttle,Brake,RPM,DRS,X,Y,Z,...
0.0,0.0,150.5,0.75,0.0,12000,0,1234.5,0,5678.9,...
0.1,15.0,152.3,0.76,0.0,12100,0,1235.2,0,5679.1,...
```

**Meaning:**
- `Time`: Seconds into lap
- `Distance`: Meters along track
- `Speed`: km/h
- `Throttle`: 0.0 - 1.0 (0% - 100%)
- `Brake`: 0.0 - 1.0 (0% - 100%)
- `X, Y, Z`: Track position coordinates

### Analysis JSON
```json
{
  "driver": "ALO",
  "optimal_reference": "VER",
  "insights": [
    {
      "timestamp": 15.3,
      "insight": "Braking 5m too late, losing apex speed.",
      "speed_delta": -2.5
    }
  ]
}
```

**Meaning:**
- `timestamp`: When in lap (seconds)
- `insight`: AI analysis from Gemini
- `speed_delta`: Speed difference from optimal (-2.5 = 2.5 km/h slower)

### Commentary CSV
```
timestamp,text,type,speed_delta
15.3,Braking 5m too late...,insight,-2.5
```

**Meaning:**
- `timestamp`: When to play commentary
- `text`: What to say
- `type`: Type of commentary (insight/event/intro)

---

## 🎬 Full Demo Flow

```bash
# Terminal 1: Generate analysis
python orchestrator.py --year 2023 --grand-prix Australian --drivers VER,ALO --skip-audio

# Terminal 2: Start server
python data_server.py

# Terminal 3: Run Unity (in Unity Editor)
# - Press Play in Unity
# - Select "ALO" from Driver dropdown
# - Press Play button in UI
# - Watch car move and commentary appear
# - Adjust playback speed with dropdown
# - Scrub timeline with slider
```

**Total time: ~5 minutes**

---

## 💾 File Locations Reference

```
/Users/gary/Desktop/HackTX/F1-RacingSim/
├── config/.env                 ← API keys here
├── data/                       ← Generated telemetry
├── analysis/                   ← Generated insights
├── audio/                      ← Generated audio
├── Assets/Scripts/             ← Unity scripts
├── orchestrator.py             ← Run this
├── data_server.py              ← Run this
└── setup.sh                    ← Run this first
```

---

## 🔗 API Endpoints Reference

```bash
# Get available drivers
curl http://localhost:5000/api/drivers

# Get telemetry for a driver
curl http://localhost:5000/api/telemetry/ALO

# Get analysis with insights
curl http://localhost:5000/api/analysis/ALO

# Get commentary with timestamps
curl http://localhost:5000/api/commentary/ALO

# Get everything (for replay)
curl http://localhost:5000/api/replay-data/ALO

# Get race summary
curl http://localhost:5000/api/race-summary
```

---

## ⚙️ Environment Variables

```bash
# Required
GEMINI_API_KEY        # Google Gemini API key
ELEVENLABS_API_KEY    # ElevenLabs API key

# Optional (defaults shown)
F1_YEAR=2023
F1_GRAND_PRIX=Australian
F1_SESSION=R
F1_DRIVERS=["VER", "ALO"]
DATA_DIR=./data
ANALYSIS_DIR=./analysis
AUDIO_DIR=./audio
REPLAY_FRAME_RATE=30
REPLAY_DEFAULT_SPEED=1.0
```

---

## 📞 Common Commands Cheat Sheet

```bash
# Setup
bash setup.sh

# Generate data
python orchestrator.py --year 2023 --grand-prix Australian --drivers VER,ALO --skip-audio

# Start server
python data_server.py

# Test individual agents
python -m agents.data_ingestion_agent
python -m agents.optimization_agent
python -m agents.analysis_agent
python -m agents.commentary_agent

# View files
ls -la data/
ls -la analysis/
ls -la audio/

# Check server
curl http://localhost:5000/

# Stop server (if needed)
# Ctrl+C in terminal
```

---

## ✅ Success Checklist

- [ ] Setup complete (`bash setup.sh`)
- [ ] API keys added (`config/.env`)
- [ ] Orchestrator ran successfully
- [ ] Data files generated (`data/` folder)
- [ ] Data server running (`python data_server.py`)
- [ ] API endpoints responding (`curl http://localhost:5000/api/drivers`)
- [ ] Unity scripts imported
- [ ] UI elements created in Unity
- [ ] F1ReplaySystem component attached
- [ ] Unity replay working
- [ ] Can play/pause/seek
- [ ] Commentary displays
- [ ] Speed changes color

---

**Ready to race! 🏁**
