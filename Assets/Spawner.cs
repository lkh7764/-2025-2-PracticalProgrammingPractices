using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Spawner : MonoBehaviour
{
    // variable
    public GameObject ProblemChildPrefab;
    public Transform ObjectParent;



    // spawning
    private float interval = 0.01f;
    private IEnumerator spawn()
    {
        while (true)
        {
            yield return new WaitForSecondsRealtime(interval);
            Instantiate(ProblemChildPrefab, ObjectParent);
        }
    }



    // life cycle
    protected void Start()
    {
        StartCoroutine(spawn());
    }
}
