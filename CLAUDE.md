# Unity Development with Vibe Unity

This Unity project includes the **Vibe Unity** package for AI-assisted Unity development.

## Available Unity Tools

### HTTP Server API (Preferred - Unity can stay open)

The Unity Editor runs an HTTP server on port 9876 that accepts JSON commands:

```bash
# Test server connectivity
curl http://172.20.32.1:9876/

# Create scene via HTTP API
curl -X POST http://172.20.32.1:9876/execute \
  -H "Content-Type: application/json" \
  -d '{"action":"create-scene","parameters":{"name":"TestScene","path":"Assets/Scenes"}}'

# Add canvas via HTTP API  
curl -X POST http://172.20.32.1:9876/execute \
  -H "Content-Type: application/json" \
  -d '{"action":"add-canvas","parameters":{"name":"MainCanvas"}}'
```

**Available HTTP Actions:**
- `create-scene` - Create Unity scenes with parameters: `name`, `path`, `type`, `addToBuild`
- `add-canvas` - Add UI canvas with parameters: `name`, `renderMode`, `referenceWidth`, `referenceHeight`

### CLI Commands (Fallback - Unity must be closed)

If HTTP server isn't available, use these batch mode commands:

```bash
# Scene creation
vibe-unity create-scene <SCENE_NAME> <SCENE_PATH> [--type TYPE] [--build]

# Canvas management  
vibe-unity add-canvas <CANVAS_NAME> [--mode MODE] [--width WIDTH] [--height HEIGHT]

# UI elements
vibe-unity add-panel <PANEL_NAME> [--parent PARENT] [--width WIDTH] [--height HEIGHT]
vibe-unity add-button <BUTTON_NAME> [--parent PARENT] [--text TEXT]
vibe-unity add-text <TEXT_NAME> [--parent PARENT] [--text CONTENT] [--size SIZE]

# Utilities
vibe-unity list-types     # Show available scene types
vibe-unity --help         # Show all commands
```

## Scene Types Available
- `Empty` - Completely empty scene
- `DefaultGameObjects` - Scene with Main Camera and Directional Light  
- `2D` - 2D optimized scene setup
- `3D` - 3D optimized scene setup with skybox
- `URP` - Universal Render Pipeline optimized (if URP installed)
- `HDRP` - High Definition Render Pipeline optimized (if HDRP installed)

## Canvas Render Modes
- `ScreenSpaceOverlay` - UI renders on top of everything
- `ScreenSpaceCamera` - UI renders with camera perspective
- `WorldSpace` - UI exists in 3D world space

## Usage Examples

```bash
# Create a complete UI setup
vibe-unity create-scene MainMenu Assets/Scenes/UI --type 2D --build
vibe-unity add-canvas MenuCanvas --mode ScreenSpaceOverlay --width 1920 --height 1080
vibe-unity add-panel MenuPanel --parent MenuCanvas --width 600 --height 400
vibe-unity add-button PlayButton --parent MenuPanel --text "Play Game"
vibe-unity add-button SettingsButton --parent MenuPanel --text "Settings"
vibe-unity add-text TitleText --parent MenuPanel --text "Game Title" --size 32

# Create game levels
vibe-unity create-scene Level1 Assets/Scenes/Levels --type 3D --build
vibe-unity create-scene Level2 Assets/Scenes/Levels --type 3D --build
```

## Important Notes

- **HTTP Method**: Preferred method, Unity Editor can stay open
- **CLI Method**: Requires Unity Editor to be closed first
- **WSL Users**: HTTP server handles WSL→Windows communication automatically
- **Firewall**: May need Windows Firewall rule for port 9876 (see Vibe Unity README)
- **Paths**: Use forward slashes in paths (e.g., `Assets/Scenes/UI`)
- **Output**: Commands provide detailed success/error feedback

## Troubleshooting

**HTTP Server Not Responding:**
1. Check Unity Editor console for server startup messages
2. Verify `Tools → Vibe Unity → HTTP Server Enabled` is checked
3. Test Windows firewall: `netstat -an | findstr :9876`
4. For WSL: May need to disable Windows Public firewall temporarily

**CLI Commands Failing:**
1. Ensure Unity Editor is completely closed
2. Verify project path is correct
3. Check Unity installation is accessible

This tool enables rapid Unity scene and UI creation through simple commands!
`# Project Guide for the F1 Hackathon Demo

This document contains the high-level goals, architectural rules, and coding conventions for our Unity F1 racing simulation project. Please adhere to these guidelines for all tasks.

To ensure consistency and guide our AI development, this project will use a central context file.
`# Project Apex: F1 Analysis Agent System
This document defines the roles and master prompts for the AI agents in our Formula 1 telemetry analysis project.

1. High-Level Goal

Analyze historical F1 race data to compare a driver's real-time performance against a pre-calculated optimal racing line. An AI agent (The Strategist) will generate analytical insights, which are then voiced by a Commentary AI.

2. Agent Personas and Responsibilities

DataIngestionAgent: A Python script using the Fast-F1 library. Its role is to fetch and cache all necessary lap and telemetry data for a specified race weekend. It must handle errors from the API and structure the data into clean Pandas DataFrames.
OptimizationAgent: A Python script that takes the full race data and identifies the single fastest lap. The telemetry from this lap becomes the "Optimal Line Benchmark." It must be able to provide optimal Speed, Throttle, Brake, and X/Y coordinates for any given Distance along the lap.
AnalysisAgent ("The Strategist"): An AI agent powered by the Gemini API. It receives slices of "live" and "optimal" telemetry data and must generate a concise, expert analysis of the performance differences.
CommentaryAgent: A Python script that takes text input from the AnalysisAgent and streams it to the ElevenLabs Text-to-Speech API for low-latency audio playback. 
ElevenLab key = sk_250c6dd177fea0e7c5d5962dc6fbf0d986dad3f09db46e50

3. Master Prompt for the AnalysisAgent (Gemini)
gemini apy key = AIzaSyDw14QlRqsOM3c8AM_JzApXsD_eBnhBLPo
"You are 'Apex', an elite Formula 1 performance engineer. Your sole purpose is to analyze and compare two sets of telemetry data: the 'Optimal Line' (the fastest possible way through a corner) and the 'Live Driver' data.
Your Task:
You will be given telemetry data for a specific section of the track (e.g., a corner entry, apex, and exit). Compare the two datasets and provide a single, concise insight (maximum 25 words) that a race engineer would give to their driver.
Analysis Rules:
Focus on Cause and Effect: Do not just state the data. Explain why a difference matters. (e.g., "Braking later is causing understeer and a slow exit.")
Quantify When Possible: Use numbers to highlight the difference. (e.g., "You lost 5 km/h at the apex compared to the optimal line.")
Identify Trade-offs: Acknowledge when a driver is sacrificing one area to gain in another. (e.g., "Slower entry, but much better traction on exit.")
Be Decisive: Conclude whether the driver's action resulted in a net time gain or loss through that section.
Example Input Data:
Track Section: Turn 9 (Copse Corner), Silverstone
Optimal Line: Brakes at 75m, min speed 290 km/h, full throttle at apex.
Live Driver: Brakes at 70m, min speed 285 km/h, full throttle 10m after apex.
Example Good Output: "You're braking 5m too late, which is compromising your apex speed and costing time on exit."
Example Bad Output: "The live driver braked at 70m and the optimal was 75m. The speed was 285 km/h." (This just repeats the data).
Now, analyze the following data:
Use fast f1 data mcp
Repo / Server setup (f1-mcp-server)
Clone the server repo (on your machine):
git clone https://github.com/rakeshgangwar/f1-mcp-server.git
cd f1-mcp-server
npm install
# ensure Python and FastF1 are installed for telemetry
# configure MCP entry in your LLM client config to point to this server
Start the server (follow the repo README). Verify via cURL or Postman that an endpoint responds to MCP-style tool requests.
Use the 2023 australian grand prix
After you review these forms, write down any clarifying questions you have so I can answer them.

---

## Clarifying Questions

### 1. Race Data Selection
- CLAUDE.md mentions **2023 Australian Grand Prix** but project.md references **2024 Emilia Romagna**. Which should we use? We should use 2023 Austrailian Grand Prix, only use the top 2 because they were super close to each other into finishing

### 2. Implementation Scope
- Should I build ALL four agents (DataIngestion, Optimization, Analysis, Commentary), or focus on specific ones first?
build all 4, step by step
- Do you have existing Python scripts for any of these agents, or should I start from scratch?
start from scratch

### 3. API Keys & Credentials
- The ElevenLabs and Gemini API keys are in CLAUDE.md. Should I:
  - Move them to a `.env` file for security? yes
  - Set up environment variable handling in the scripts? yes

### 4. Development Priority
- Is this for a **HackTX hackathon submission** (quick demo) or a **production-ready system**?
- Should error handling be robust or is basic functionality acceptable? quick demo

### 5. Data Output Format
- How should the agents communicate (JSON, CSV, in-memory objects)? csv, gemini reads csv, then generate a prompt for eleven labs with timestamps, and elevenlabs should say it at the timestamp.
- Do you need intermediate data files for debugging, or should it be pipeline-based?
intermediate files

### 6. Vibe Unity Integration
- Is Vibe Unity just for reference, or do you want a **Unity UI** to display the F1 analysis results?
- Should the commentary audio play through Unity or standalone?
Use unity to display the results, unity should also simulate the race 

### 7. Testing & Validation
- Do you have sample F1 telemetry data for testing, or should we use live FastF1 API data? use fastf1 to grab the results
- What constitutes success? (e.g., "Generate N insights per lap")
Success is how much time spent on the racing line, or how far off from optimal lap timer
I also want a replay back system of our simulation and we can speed up or slow down, and the commentary should be spoken during the correct timestamp, like if a crash happend, overtaking, and after every lap maybe to say how accurate was the lap.