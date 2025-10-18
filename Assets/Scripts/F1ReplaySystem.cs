using UnityEngine;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine.UI;

/// <summary>
/// F1ReplaySystem - Main controller for F1 race replay with telemetry visualization
/// Handles playback speed, seeking, and commentary synchronization
/// </summary>
public class F1ReplaySystem : MonoBehaviour
{
    [System.Serializable]
    public class TelemetryPoint
    {
        public float time;
        public float distance;
        public float speed;
        public float throttle;
        public float brake;
        public float posX;
        public float posY;
        public float posZ;
    }

    [System.Serializable]
    public class Commentary
    {
        public float timestamp;
        public string text;
        public string type;
        public float speedDelta;
        public string audioFile;
    }

    [SerializeField] private string telemetryDataPath = "data/combined_telemetry.csv";
    [SerializeField] private string commentaryDataPath = "audio/";

    [SerializeField] private Text timeDisplay;
    [SerializeField] private Text speedDisplay;
    [SerializeField] private Text commentaryDisplay;
    [SerializeField] private Slider speedSlider;
    [SerializeField] private Slider seekSlider;
    [SerializeField] private Button playButton;
    [SerializeField] private Button pauseButton;
    [SerializeField] private Dropdown driverDropdown;
    [SerializeField] private Dropdown playbackSpeedDropdown;
    [SerializeField] private Image speedIndicator;
    [SerializeField] private LineRenderer trackLineRenderer;

    private List<TelemetryPoint> telemetryData = new List<TelemetryPoint>();
    private List<Commentary> commentaryData = new List<Commentary>();

    private float currentTime = 0f;
    private float maxTime = 0f;
    private float playbackSpeed = 1.0f;
    private bool isPlaying = false;

    private int currentTelemetryIndex = 0;
    private int currentCommentaryIndex = 0;
    private string currentDriver = "ALO";

    private AudioSource audioSource;

    void Start()
    {
        audioSource = GetComponent<AudioSource>();
        if (audioSource == null)
            audioSource = gameObject.AddComponent<AudioSource>();

        // Setup UI
        if (playButton != null)
            playButton.onClick.AddListener(Play);

        if (pauseButton != null)
            pauseButton.onClick.AddListener(Pause);

        if (driverDropdown != null)
            driverDropdown.onValueChanged.AddListener(OnDriverChanged);

        if (playbackSpeedDropdown != null)
            playbackSpeedDropdown.onValueChanged.AddListener(OnPlaybackSpeedChanged);

        if (seekSlider != null)
            seekSlider.onValueChanged.AddListener(OnSeek);

        // Load data
        LoadTelemetryData();
        LoadCommentaryData();

        UpdateUI();
    }

    void Update()
    {
        if (!isPlaying)
            return;

        currentTime += Time.deltaTime * playbackSpeed;

        if (currentTime >= maxTime)
        {
            currentTime = maxTime;
            Pause();
        }

        UpdateTelemetryIndex();
        PlayCommentaryAtTime();
        UpdateUI();
    }

    void LoadTelemetryData()
    {
        string fullPath = Path.Combine(Application.streamingAssetsPath, telemetryDataPath);

        if (!File.Exists(fullPath))
        {
            Debug.LogError($"Telemetry file not found: {fullPath}");
            return;
        }

        string[] lines = File.ReadAllLines(fullPath);

        foreach (string line in lines.Skip(1)) // Skip header
        {
            string[] values = line.Split(',');
            if (values.Length < 9)
                continue;

            TelemetryPoint point = new TelemetryPoint
            {
                time = float.Parse(values[0]),
                distance = float.Parse(values[1]),
                speed = float.Parse(values[2]),
                throttle = float.Parse(values[3]),
                brake = float.Parse(values[4]),
                posX = float.Parse(values[6]),
                posY = 0f, // 2D representation
                posZ = float.Parse(values[7])
            };

            telemetryData.Add(point);
        }

        if (telemetryData.Count > 0)
        {
            maxTime = telemetryData.Last().time;
            Debug.Log($"Loaded {telemetryData.Count} telemetry points. Max time: {maxTime:F2}s");
        }
    }

    void LoadCommentaryData()
    {
        string directoryPath = Path.Combine(Application.streamingAssetsPath, commentaryDataPath);
        string csvFile = Path.Combine(directoryPath, $"{currentDriver}_commentary.csv");

        if (!File.Exists(csvFile))
        {
            Debug.LogWarning($"Commentary file not found: {csvFile}");
            return;
        }

        string[] lines = File.ReadAllLines(csvFile);

        foreach (string line in lines.Skip(1)) // Skip header
        {
            string[] values = line.Split(',');
            if (values.Length < 3)
                continue;

            Commentary item = new Commentary
            {
                timestamp = float.Parse(values[0]),
                text = values[1],
                type = values[2],
                speedDelta = values.Length > 3 ? float.Parse(values[3]) : 0f,
                audioFile = values.Length > 4 ? values[4] : ""
            };

            commentaryData.Add(item);
        }

        Debug.Log($"Loaded {commentaryData.Count} commentary items");
    }

    void UpdateTelemetryIndex()
    {
        while (currentTelemetryIndex < telemetryData.Count - 1 &&
               telemetryData[currentTelemetryIndex + 1].time <= currentTime)
        {
            currentTelemetryIndex++;
        }
    }

    void PlayCommentaryAtTime()
    {
        while (currentCommentaryIndex < commentaryData.Count &&
               commentaryData[currentCommentaryIndex].timestamp <= currentTime)
        {
            Commentary comment = commentaryData[currentCommentaryIndex];

            if (commentaryDisplay != null)
                commentaryDisplay.text = comment.text;

            // Load and play audio if available
            if (!string.IsNullOrEmpty(comment.audioFile))
            {
                PlayAudioClip(comment.audioFile);
            }

            currentCommentaryIndex++;
        }
    }

    void PlayAudioClip(string filename)
    {
        // Load audio from resources
        string audioPath = Path.Combine("audio", Path.GetFileNameWithoutExtension(filename));
        AudioClip clip = Resources.Load<AudioClip>(audioPath);

        if (clip != null && audioSource != null)
        {
            audioSource.clip = clip;
            audioSource.Play();
        }
    }

    void UpdateUI()
    {
        if (currentTelemetryIndex < telemetryData.Count)
        {
            TelemetryPoint current = telemetryData[currentTelemetryIndex];

            if (speedDisplay != null)
                speedDisplay.text = $"Speed: {current.speed:F1} km/h";

            if (timeDisplay != null)
                timeDisplay.text = FormatTime(currentTime);

            if (speedIndicator != null)
            {
                float speedPercentage = Mathf.Clamp01(current.speed / 350f); // Max F1 speed ~350 km/h
                speedIndicator.fillAmount = speedPercentage;
            }
        }

        if (seekSlider != null && maxTime > 0)
        {
            seekSlider.value = currentTime / maxTime;
        }
    }

    void OnSeek(float value)
    {
        currentTime = value * maxTime;
        UpdateTelemetryIndex();

        // Reset commentary playback
        currentCommentaryIndex = 0;
        while (currentCommentaryIndex < commentaryData.Count &&
               commentaryData[currentCommentaryIndex].timestamp <= currentTime)
        {
            currentCommentaryIndex++;
        }
    }

    void OnPlaybackSpeedChanged(int index)
    {
        float[] speeds = { 0.25f, 0.5f, 1.0f, 1.5f, 2.0f, 4.0f };
        if (index < speeds.Length)
            playbackSpeed = speeds[index];
    }

    void OnDriverChanged(int index)
    {
        string[] drivers = { "ALO", "VER" };
        if (index < drivers.Length)
        {
            currentDriver = drivers[index];
            commentaryData.Clear();
            currentCommentaryIndex = 0;
            LoadCommentaryData();
        }
    }

    public void Play()
    {
        isPlaying = true;
        if (playButton != null) playButton.interactable = false;
        if (pauseButton != null) pauseButton.interactable = true;
    }

    public void Pause()
    {
        isPlaying = false;
        if (playButton != null) playButton.interactable = true;
        if (pauseButton != null) pauseButton.interactable = false;
    }

    public void Stop()
    {
        Pause();
        currentTime = 0f;
        currentTelemetryIndex = 0;
        currentCommentaryIndex = 0;
        if (audioSource != null)
            audioSource.Stop();
    }

    string FormatTime(float seconds)
    {
        int mins = (int)(seconds / 60f);
        int secs = (int)(seconds % 60f);
        int millis = (int)((seconds % 1f) * 1000f);
        return $"{mins:D2}:{secs:D2}.{millis:D3}";
    }

    public float GetCurrentSpeed()
    {
        if (currentTelemetryIndex < telemetryData.Count)
            return telemetryData[currentTelemetryIndex].speed;
        return 0f;
    }

    public Vector3 GetCurrentPosition()
    {
        if (currentTelemetryIndex < telemetryData.Count)
        {
            TelemetryPoint p = telemetryData[currentTelemetryIndex];
            return new Vector3(p.posX, 0f, p.posZ);
        }
        return Vector3.zero;
    }
}
