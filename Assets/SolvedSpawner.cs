using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class SolvedSpawner : MonoBehaviour
{
    // variable
    public GameObject ProblemChildPrefab;
    public Transform ObjectParent;


    public Queue<GameObject> objPool;


    // spawning
    private float interval = 0.01f;
    private IEnumerator spawn()
    {
        while (true)
        {
            yield return new WaitForSecondsRealtime(interval);
            if (!dequeueChild()) createNewObj();
        }
    }
    private bool dequeueChild()
    {
        if (objPool.Count == 0) return false;

        objPool.Dequeue().SetActive(true);
        return true;
    }
    private void createNewObj()
    {
        GameObject newObj = Instantiate(ProblemChildPrefab, ObjectParent);
        newObj.GetComponent<SolvedChild>().spawner = this;
        newObj.SetActive(true);
    }
    

    public void ReturnToPool(GameObject child)
    {
        child.SetActive(false);
        objPool.Enqueue(child);
    }


    // life cycle
    protected void Start()
    {
        objPool = new Queue<GameObject>();
        StartCoroutine(spawn());
    }
}
