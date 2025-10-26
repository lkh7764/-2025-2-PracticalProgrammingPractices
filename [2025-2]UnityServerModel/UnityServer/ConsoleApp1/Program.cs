using System.Net;
using System.Net.Sockets;

using System.Text;
using System.Text.Json;

using System.Collections.Concurrent;


class Server
{
    static ConcurrentDictionary<TcpClient, float> playerEnergies = new ConcurrentDictionary<TcpClient, float>();

    static async Task Main()
    {
        TcpListener listener = new TcpListener(IPAddress.Any, 8000);
        listener.Start();
        Console.WriteLine("=====Server Start=====");

        _ = BroadcastLoop();
        while(true)
        {
            var client = await listener.AcceptTcpClientAsync();
            playerEnergies[client] = 0f;
            _ = HandleClientAsync(client);
        }
    }
    static async Task BroadcastLoop()
    {
        Random rnd = new Random();
        while (true)
        {
            float avgEnergy = playerEnergies.Count > 0 ? (float)playerEnergies.Values.Average() : 0.1f;
            var packet = new StormPacket
            (
                intensity: Math.Clamp(avgEnergy + (float)rnd.NextDouble() * 0.2f, 0f, 1f),
                windDir: new float[] { (float)rnd.NextDouble(), 0f, (float)rnd.NextDouble() }
            );

            string json = JsonSerializer.Serialize(packet) + "\n";
            byte[] data = Encoding.UTF8.GetBytes(json);
            foreach (var client in playerEnergies.Keys.ToList())
            {
                try
                {
                    if (client == null || !client.Connected)
                    {
                        playerEnergies.TryRemove(client, out _);
                        client?.Close();
                        continue;
                    }

                    var stream = client.GetStream();
                    if (stream == null || !stream.CanWrite)
                    {
                        playerEnergies.TryRemove(client, out _);
                        client?.Close();
                        continue;
                    }

                    await stream.WriteAsync(data, 0, data.Length);
                }
                catch (IOException)
                {
                    playerEnergies.TryRemove(client, out _);
                    client.Close();
                }
                catch (ObjectDisposedException)
                {
                    playerEnergies.TryRemove(client, out _);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[Broadcast] 예외 발생: {ex.Message}");
                    playerEnergies.TryRemove(client, out _);
                }
            }

            await Task.Delay(1000);
        }
    }
    static async Task HandleClientAsync(TcpClient client)
    {
        var stream = client.GetStream();
        byte[] buffer = new byte[1024];
        try
        {
            while (client.Connected)
            {
                if (!stream.CanRead) break;  // 스트림이 읽기 불가면 종료

                int bytesRead = 0;
                try
                {
                    bytesRead = await stream.ReadAsync(buffer, 0, buffer.Length);
                }
                catch (IOException)
                {
                    Console.WriteLine("-----Client Network Error-----");
                    break;
                }
                catch (ObjectDisposedException)
                {
                    Console.WriteLine("-----Closed Stream-----");
                    break;
                }

                if (bytesRead <= 0)
                {
                    Console.WriteLine("-----Connection Finished-----");
                    break;
                }

                Console.WriteLine("-----Client Connect Successly-----");
                string json = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                try
                {
                    var packet = JsonSerializer.Deserialize<PlayerPacket>(json);
                    playerEnergies[client] = packet.energy;
                }
                catch { }
            }
        }
        finally
        {
            Console.WriteLine("-----Client Connection Finished-----");
            playerEnergies.TryRemove(client, out _);
            client.Close();
        }
    }


    record PlayerPacket(float energy);
    record StormPacket(float intensity, float[] windDir);
}