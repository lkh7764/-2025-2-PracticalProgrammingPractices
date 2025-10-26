using Unity.Jobs;
using Unity.Burst;
using Unity.Collections;

using UnityEngine;

public class ParticleStorm : MonoBehaviour
{
    [SerializeField] private int particleCount = 5000;
    [SerializeField] StormClient storm;

    NativeArray<Vector3> positions;
    NativeArray<Vector3> velocities;

    protected void Start()
    {
        positions = new NativeArray<Vector3>(particleCount, Allocator.Persistent);
        velocities = new NativeArray<Vector3>(particleCount, Allocator.Persistent);

        for (int i=0; i<particleCount; ++i)
        {
            positions[i] = Random.insideUnitSphere * 5f;
        }
    }
    protected void Update()
    {
        var job = new ParticleJob
        {
            positions = positions,
            velocities = velocities,
            deltaTime = Time.deltaTime,
            intensity = storm.StormIntensity,
            wind = storm.WindDir
        };

        JobHandle handle = job.Schedule(particleCount, 128);
        handle.Complete();

        for (int i = 0; i < particleCount; i++)
        {
            Debug.DrawRay(positions[i], Vector3.up * 0.1f, 
                Color.Lerp(Color.white, Color.red, storm.StormIntensity));
        }
    }


    protected void OnDestroy()
    {
        positions.Dispose();
        velocities.Dispose();
    }


    [BurstCompile] struct ParticleJob : IJobParallelFor
    {
        public NativeArray<Vector3> positions;
        public NativeArray<Vector3> velocities;

        public float deltaTime;
        public float intensity;

        public Vector3 wind;


        public void Execute(int i)
        {
            Vector3 turbulence = new Vector3(
                Mathf.PerlinNoise(i * 0.01f, intensity) - 0.5f,
                Mathf.PerlinNoise(i * 0.02f, intensity + 1f) - 0.5f,
                Mathf.PerlinNoise(i * 0.03f, intensity + 2f) - 0.5f
            );

            Vector3 force = (wind + turbulence) * intensity * 2f;
            velocities[i] += force * deltaTime;
            velocities[i] *= 0.98f;
            positions[i] += velocities[i] * deltaTime;
            if (positions[i].magnitude > 10f)
            {
                velocities[i] = -positions[i].normalized * 5f;
            }
        }
    }
}
