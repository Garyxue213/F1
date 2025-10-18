
Project Apex: An AI-Driven Framework for F1 Race Analysis


Introduction: The Millisecond War

In Formula 1, victory is measured in thousandths of a second. While drivers battle on track, a parallel war is waged on the pit wall and in team factories, where engineers and strategists analyze terabytes of data to find the smallest competitive edge. They run millions of simulations to predict tire wear, fuel consumption, and the optimal racing line—the theoretical fastest path around the circuit.
The challenge is not a lack of data, but a surplus of it. During a live race, the sheer volume of telemetry can overwhelm human analysts. The critical insights—the subtle deviations from the optimal line that gain or lose a few milliseconds in a corner—are often buried in the noise.
This document outlines the architecture for Project Apex, a multi-agent AI system designed to solve this problem. It ingests real-world race data, uses a simulation agent to define the optimal performance baseline, and deploys a dedicated analysis agent to identify and articulate these marginal gains and losses in real-time, voiced by a synthetic race engineer.
This project will be based on the 2023 australian grand prix.

Section 1: The Architectural Blueprint - A Multi-Agent System

A complex, real-time task like this requires more than a single monolithic script; it demands a team of specialists. Our solution is architected as a system of four distinct AI agents, each with a specific role. They operate in a pipeline, passing structured data and insights to one another.
The Data Ingestion Agent ("The Collector"): This agent's sole responsibility is to connect to historical F1 data sources, load the telemetry for a specific race, and prepare it for analysis. It acts as the system's gateway to the real world.
The Simulation & Optimization Agent ("The Ghost"): This agent takes the raw data from The Collector and performs the crucial task of defining "optimal." It processes the telemetry to establish the benchmark racing line and performance parameters that will be used for comparison.
The Analysis Agent ("The Strategist"): This is the core intelligence of our system. Powered by a large language model like Gemini, this agent receives two streams of data in real-time: the live telemetry from a driver and the corresponding optimal data from The Ghost. Its job is to perform a comparative analysis and generate concise, actionable insights in natural language.
The Commentary Agent ("The Voice"): The final link in the chain. This agent takes the text-based insights from The Strategist and uses the ElevenLabs API to convert them into low-latency, broadcast-quality audio commentary.1
This decoupled, agent-based architecture allows for modularity and scalability, enabling each component to perform its specialized task with maximum efficiency.

Section 2: Data Acquisition - Replaying a Legendary Duel



The Data Ingestion Agent in Detail

This agent's primary tool is the FastF1 Python library, a powerful open-source package for accessing F1 data.5
Core Logic:
Data Loading: It uses fastf1.get_session() to connect and load the session data. Crucially, it enables telemetry loading: session.load(telemetry=True). This fetches the detailed, point-by-point data for each car on every lap.8
Data Selection: The agent identifies the top contenders (Verstappen and Norris) and isolates their lap data using session.laps.pick_driver('VER') and session.laps.pick_driver('NOR').
Data Preparation: For each driver, the agent iterates through their laps and retrieves the full telemetry dataset for each lap using .get_car_data().add_distance(). This provides a Pandas DataFrame containing critical channels like Speed, Throttle, Brake, RPM, DRS, and the essential X, Y, Z spatial coordinates.10
The output of this agent is a clean, structured collection of telemetry data for the two lead drivers, ready to be passed to the next agent in the pipeline.

Section 3: The Quest for Perfection - The Simulation & Optimization Agent

The concept of an "optimal racing line" is complex. It's the path that minimizes lap time by perfectly balancing braking, turn-in, apex speed, and corner exit acceleration.11 A true calculation requires sophisticated vehicle dynamics models. For our system, we will use a professional data-driven shortcut.

The Ghost Agent in Detail

This agent defines the optimal line not through pure physics simulation, but by extracting it from the best performance demonstrated in the real race.
Core Logic:
Identify the "Perfect Lap": The agent analyzes all loaded lap data from the top drivers and identifies the single fastest lap of the race using session.laps.pick_fastest().
Extract Telemetry: It retrieves the full, high-resolution telemetry for this single "perfect lap." This dataset—the sequence of speeds, throttle inputs, brake pressures, and X/Y coordinates—becomes our Optimal Racing Line Benchmark.
Data Structuring: The agent processes this benchmark lap into a lookup table or a function where, for any given distance d along the lap, one can instantly retrieve the optimal parameters (speed, throttle, brake, position).
The output of The Ghost is this benchmark dataset. It is no longer just raw data; it is the "ghost car" that our analysis agent will race against.

Section 4: The Analyst in the Machine - The Gemini Agent

This is where raw data is transformed into human-understandable intelligence. The Strategist agent continuously compares a driver's live performance against the ghost lap.

The Strategist Agent in Detail

This agent is built around a powerful Large Language Model (LLM) like Google's Gemini, accessed via its API.
Core Logic:
Real-Time Data Slicing: The agent receives the "live" telemetry data for a driver on their current lap (in our replay, this is just the data for lap N). It also receives the benchmark data from The Ghost.
Comparative Analysis Prompting: At key points on the track (e.g., corner entry, apex, exit), the agent queries the LLM with a highly specific prompt. This prompt includes the telemetry data for both the live driver and the ghost car over the last few hundred meters.
Example Master Prompt for The Strategist (Gemini):
"You are an elite Formula 1 race strategist. Your task is to analyze two sets of telemetry data for the section between 1500m and 1800m of the lap, which covers the entry and apex of Turn 7.
Optimal Line Data (Ghost Car):
Braking Point: 1550m
Min Speed at Apex (1675m): 145 km/h
Throttle Application Point: 1680m
Live Driver Data (Driver 'NOR'):
Braking Point: 1560m
Min Speed at Apex (1675m): 142 km/h
Throttle Application Point: 1675m
Based on this data, provide a concise, expert analysis (max 20 words) explaining the performance difference. Focus on the cause and effect. Is the driver gaining or losing time, and why?"
Insight Generation: The LLM processes this prompt and returns a concise, analytical insight.
Expected Output: "Norris is braking 10 meters later, but sacrificing apex speed. This is costing him approximately one-tenth through this corner complex."
Expected Output: "Verstappen is applying the throttle 5 meters earlier on exit, giving him a better drive onto the following straight. This should gain him time."
The output of this agent is a stream of text-based, high-level strategic insights.

Section 5: The Voice of the Race - The Commentary Agent

The final agent translates the Strategist's insights into an immersive audio experience.

The Voice Agent in Detail

This agent uses the ElevenLabs API, specifically its low-latency models, to provide real-time audio feedback.2
Core Logic:
Receive Insight: The agent receives the text string from The Strategist (e.g., "Norris is braking 10 meters later...").
API Call: It makes an immediate API call to ElevenLabs, sending the text to be converted to speech. For real-time applications, using the streaming endpoint is crucial to begin playback as soon as the first audio chunks are received, minimizing perceived delay.14
Audio Playback: The agent plays the returned audio stream through the system's audio output.
The result is a dynamic, AI-driven commentary that provides deep, data-backed insights into the race as it unfolds, explaining exactly how the top drivers are fighting for every millisecond.

Section 6: Project Guide and Master Prompts (claude.md)

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

3. Master Prompt for the AnalysisAgent (Gemini)

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
Now, analyze the following data:"
`
