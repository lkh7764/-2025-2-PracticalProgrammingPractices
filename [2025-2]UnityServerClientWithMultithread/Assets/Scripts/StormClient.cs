using UnityEngine;

using System.Text;
using System.Net.Sockets;
using System.Threading.Tasks;

public class StormClient : MonoBehaviour
{
    public float StormIntensity;
    public Vector3 WindDir;

    private TcpClient client;
    private NetworkStream stream;


    [System.Serializable] class PlayerPacket { public float energy; }
    [System.Serializable] class StormPacket { public float intensity; public float[] windDir; }


    protected async void Start()
    {
        Debug.Log("Receiver Start 호출됨");
        client = new TcpClient();
        await client.ConnectAsync("127.0.0.1", 8000);

        Debug.Log("서버 연결 완료");
        stream = client.GetStream();

        _ = sendLoop();
        _ = receiveLoop();
    }


    private async Task sendLoop()
    {
        while(true)
        {
            float energe = Input.GetMouseButton(0) ? 1f : 0.2f;
            var json = JsonUtility.ToJson(new PlayerPacket { energy = energe }) + "\n";
            byte[] data = Encoding.UTF8.GetBytes(json);

            await stream.WriteAsync(data, 0, data.Length);
            await Task.Delay(500);
        }
    }
    private async Task receiveLoop()
    {
        byte[] buf = new byte[1024];
        while (true)
        {
            int byteRead = await stream.ReadAsync(buf, 0, buf.Length);
            if (byteRead > 0)
            {
                string json = Encoding.UTF8.GetString(buf, 0, byteRead);
                var packet = JsonUtility.FromJson<StormPacket>(json);

                StormIntensity = packet.intensity;
                WindDir = new Vector3(packet.windDir[0], packet.windDir[1], packet.windDir[2]);
            }
        }
    }
}
