using UnityEngine;

/// <summary>
/// F1CarController - Controls car position and visualization during replay
/// </summary>
public class F1CarController : MonoBehaviour
{
    [SerializeField] private F1ReplaySystem replaySystem;
    [SerializeField] private float positionScale = 10f;
    [SerializeField] private Material carMaterial;
    [SerializeField] private TrailRenderer trailRenderer;

    private Vector3 previousPosition;
    private Rigidbody rb;

void Start()
    {
        if (replaySystem == null)
            replaySystem = FindFirstObjectByType<F1ReplaySystem>();

        rb = GetComponent<Rigidbody>();
        previousPosition = transform.position;

        // Setup trail
        if (trailRenderer != null)
            trailRenderer.Clear();
    }

void Update()
    {
        if (replaySystem == null)
            return;

        // Update position from replay data
        Vector3 targetPosition = replaySystem.GetCurrentPosition() * positionScale;
        transform.position = targetPosition;

        // Update speed indicator color
        float speed = replaySystem.GetCurrentSpeed();
        UpdateSpeedColor(speed);

        // Calculate rotation based on movement direction
        Vector3 direction = transform.position - previousPosition;
        if (direction.magnitude > 0.01f)
        {
            transform.rotation = Quaternion.LookRotation(direction);
        }

        previousPosition = transform.position;
    }

    void UpdateSpeedColor(float speed)
    {
        if (carMaterial == null)
            return;

        // Normalize speed to 0-1 (max 350 km/h)
        float speedNormalized = Mathf.Clamp01(speed / 350f);

        // Interpolate color from blue (slow) -> yellow -> red (fast)
        Color color;
        if (speedNormalized < 0.5f)
        {
            color = Color.Lerp(Color.blue, Color.yellow, speedNormalized * 2f);
        }
        else
        {
            color = Color.Lerp(Color.yellow, Color.red, (speedNormalized - 0.5f) * 2f);
        }

        carMaterial.SetColor("_BaseColor", color);
    }

    public void ResetTrail()
    {
        if (trailRenderer != null)
            trailRenderer.Clear();
    }
}
