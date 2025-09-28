using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ProblemChild : MonoBehaviour
{
    public static long AdditionalMemory = 1;
    public static long AdditionalInterval = 10000;
    public float LifeTime = 0.5f;


    public char[] IndependentVariable;


    protected void Start()
    {
        IndependentVariable = new char[AdditionalMemory];
        AdditionalMemory += AdditionalInterval;

        Destroy(gameObject, LifeTime);
    }
}
