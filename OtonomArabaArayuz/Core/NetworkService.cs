using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using OtonomArabaArayuz.Models;

namespace OtonomArabaArayuz.Core
{
    public class NetworkService
    {
        private TcpListener _listener;
        private CancellationTokenSource _cts;
        public event Action<TelemetryData> OnDataReceived;
        public event Action<string> OnLog;

        private TcpClient _connectedClient; // Aktif istemciyi sakla

        public async Task StartServerAsync(int port)
        {
            try
            {
                _listener = new TcpListener(IPAddress.Any, port);
                _listener.Start();
                OnLog?.Invoke($"Server {port} portunda başlatıldı. Bağlantı bekleniyor...");

                _cts = new CancellationTokenSource();

                while (!_cts.Token.IsCancellationRequested)
                {
                    try
                    {
                        var client = await _listener.AcceptTcpClientAsync();
                        OnLog?.Invoke("Yeni bir istemci bağlandı!");
                        _connectedClient = client; // İstemciyi kaydet
                        _ = HandleClientAsync(client, _cts.Token);
                    }
                    catch (ObjectDisposedException)
                    {
                        break; 
                    }
                }
            }
            catch (Exception ex)
            {
                OnLog?.Invoke($"Server Hatası: {ex.Message}");
            }
        }
        
        public async Task SendData(string message)
        {
            if (_connectedClient != null && _connectedClient.Connected)
            {
                try
                {
                    byte[] data = Encoding.UTF8.GetBytes(message);
                    await _connectedClient.GetStream().WriteAsync(data, 0, data.Length);
                }
                catch (Exception ex)
                {
                    OnLog?.Invoke($"Veri gönderme hatası: {ex.Message}");
                }
            }
        }

        public void StopServer()
        {
            _cts?.Cancel();
            _listener?.Stop();
            _connectedClient?.Close();
            OnLog?.Invoke("Server durduruldu.");
        }

        private async Task HandleClientAsync(TcpClient client, CancellationToken token)
        {
            using (client)
            using (var stream = client.GetStream())
            {
                byte[] buffer = new byte[1024];
                try
                {
                    while (!token.IsCancellationRequested && client.Connected)
                    {
                        int bytesRead = await stream.ReadAsync(buffer, 0, buffer.Length, token);
                        if (bytesRead == 0) break;

                        string data = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                        ProcessData(data);
                    }
                }
                catch (Exception ex)
                {
                    OnLog?.Invoke($"Bağlantı kesildi: {ex.Message}");
                }
            }
            if (_connectedClient == client) _connectedClient = null;
            OnLog?.Invoke("İstemci ayrıldı.");
        }

        private void ProcessData(string rawData)
        {
            try
            {
                // Basit parser
                // Gelen veri parçalı olabilir veya birden fazla paket birleşik olabilir.
                // Bu örnek basit tutulmuştur. Gerçekte buffer yönetimi gerekebilir.
                var packets = rawData.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);

                foreach (var packet in packets)
                {
                    var telemetry = new TelemetryData();
                    var parts = packet.Split(';');
                    foreach (var part in parts)
                    {
                        var kv = part.Split(':');
                        if (kv.Length == 2)
                        {
                            if (kv[0] == "SPEED") telemetry.Speed = double.Parse(kv[1], System.Globalization.CultureInfo.InvariantCulture);
                            if (kv[0] == "DIST") telemetry.Distance = double.Parse(kv[1], System.Globalization.CultureInfo.InvariantCulture);
                            if (kv[0] == "ANGLE") telemetry.Angle = double.Parse(kv[1], System.Globalization.CultureInfo.InvariantCulture);
                        }
                    }
                    OnDataReceived?.Invoke(telemetry);
                }
            }
            catch (Exception ex)
            {
                OnLog?.Invoke($"Veri işleme hatası: {ex.Message} (Veri: {rawData})");
            }
        }
    }
}
