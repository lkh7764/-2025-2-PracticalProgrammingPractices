using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class SolvedChild : MonoBehaviour
{
    public static int AdditionalMemory = 1;
    public static int AdditionalInterval = 10000;
    public float LifeTime = 0.5f;


    public List<char> IndependentVariable;
    public SolvedSpawner spawner;


    protected void OnEnable()
    {
        IndependentVariable = new List<char>(AdditionalInterval);
        AdditionalMemory += AdditionalInterval;

        Destroy(gameObject, LifeTime);
    }
    private IEnumerator disable()
    {
        yield return new WaitForSecondsRealtime(LifeTime);

        spawner.ReturnToPool(gameObject);
    }
}
