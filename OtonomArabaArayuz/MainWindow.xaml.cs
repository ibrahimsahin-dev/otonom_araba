using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;
using OtonomArabaArayuz.Core;
using OtonomArabaArayuz.Models;

namespace OtonomArabaArayuz
{
    public partial class MainWindow : Window
    {
        private NetworkService _networkService;
        private bool _isServerRunning = false;
        
        // Map Variables
        private Ellipse _carMarker;
        private Polyline _pathLine;
        private double _currentX = 0; // cm
        private double _currentY = 0; // cm
        private double _lastDistance = 0;
        private double _currentAngle = 0; // Derece (0 = Yukarı/Kuzey)
        
        // Scale: 1 px = 1 cm (basitlik için) -> Harita büyüdükçe zoom gerekebilir
        private double _scale = 0.5; // 1 cm = 0.5 px
        private double _centerX = 0;
        private double _centerY = 0;

        public MainWindow()
        {
            InitializeComponent();
            _networkService = new NetworkService();
            _networkService.OnDataReceived += NetworkService_OnDataReceived;
            _networkService.OnLog += NetworkService_OnLog;
            
            InitMap();
            Log("Uygulama başlatıldı. Harita hazır.");
        }
        
        private void InitMap()
        {
            // Araba imleci
            _carMarker = new Ellipse
            {
                Width = 20,
                Height = 20,
                Fill = Brushes.Yellow,
                Stroke = Brushes.Orange,
                StrokeThickness = 2
            };
            
            // Rota çizgisi
            _pathLine = new Polyline
            {
                Stroke = Brushes.Cyan,
                StrokeThickness = 2,
                Opacity = 0.6
            };
            
            // Öncelikle Canvas üzerine ekleyelim (Pozisyonlama SizeChanged'de yapılacak)
            mapCanvas.Children.Add(_pathLine);
            mapCanvas.Children.Add(_carMarker);
        }

        private void mapCanvas_SizeChanged(object sender, SizeChangedEventArgs e)
        {
            DrawGrid();
            UpdateCarPosition();
        }

        private void DrawGrid()
        {
            // Grid çizgilerini yeniden çiz
            // Eski grid çizgilerini temizle (Sadece grid çizgilerini, aracı değil)
            // Kolaylık olsun diye her şeyi temizleyip aracı tekrar ekleyelim
            mapCanvas.Children.Clear();
            mapCanvas.Children.Add(_pathLine);
            mapCanvas.Children.Add(_carMarker);

            double width = mapCanvas.ActualWidth;
            double height = mapCanvas.ActualHeight;
            _centerX = width / 2;
            _centerY = height / 2;

            double step = 20; // Daha küçük grid (20px)

            for (double x = 0; x < width; x += step)
            {
                Line line = new Line
                {
                    X1 = x, Y1 = 0,
                    X2 = x, Y2 = height,
                    Stroke = new SolidColorBrush(Color.FromRgb(40, 40, 40)),
                    StrokeThickness = 1
                };
                mapCanvas.Children.Insert(0, line); // En alta ekle
            }

            for (double y = 0; y < height; y += step)
            {
                Line line = new Line
                {
                    X1 = 0, Y1 = y,
                    X2 = width, Y2 = y,
                    Stroke = new SolidColorBrush(Color.FromRgb(40, 40, 40)),
                    StrokeThickness = 1
                };
                mapCanvas.Children.Insert(0, line);
            }
            
            // Merkez çizgileri (X-Y ekseni)
             Line axisX = new Line { X1=0, Y1=_centerY, X2=width, Y2=_centerY, Stroke=Brushes.Gray, StrokeThickness=1 };
             Line axisY = new Line { X1=_centerX, Y1=0, X2=_centerX, Y2=height, Stroke=Brushes.Gray, StrokeThickness=1 };
             mapCanvas.Children.Insert(1, axisX);
             mapCanvas.Children.Insert(1, axisY);
        }

        private async void btnConnect_Click(object sender, RoutedEventArgs e)
        {
            if (!_isServerRunning)
            {
                if (int.TryParse(txtPort.Text, out int port))
                {
                    btnConnect.Content = "Durdur";
                    btnConnect.Background = Brushes.Crimson;
                    _isServerRunning = true;
                    txtPort.IsEnabled = false;
                    await _networkService.StartServerAsync(port);
                }
                else
                {
                    Log("Geçersiz Port Numarası!");
                }
            }
            else
            {
                _networkService.StopServer();
                btnConnect.Content = "Server Başlat";
                btnConnect.Background = new SolidColorBrush(Color.FromRgb(0, 122, 204));
                _isServerRunning = false;
                txtPort.IsEnabled = true;
            }
        }

        private void NetworkService_OnDataReceived(TelemetryData data)
        {
            Dispatcher.Invoke(() =>
            {
                lblSpeed.Text = data.Speed.ToString("F1");
                lblDistance.Text = data.Distance.ToString("F1");
                pbSpeed.Value = data.Speed;

                // Harita Simülasyonu
                // Gelen ANGLE verisini kullan (0-360)
                _currentAngle = data.Angle; 
                
                double deltaDist = data.Distance - _lastDistance;
                if (deltaDist < 0) deltaDist = 0; // Reset durumu vb. için
                _lastDistance = data.Distance;

                // Açı yönünde ilerle
                // (0 derece = Kuzey = -Y yönü Canvas'ta)
                // Açıyı Radyana çevir
                double angleRad = (_currentAngle - 90) * (Math.PI / 180.0); 
                
                _currentX += deltaDist * Math.Cos(angleRad);
                _currentY += deltaDist * Math.Sin(angleRad);

                lblPosX.Text = $"{_currentX:F1} (Açı: {_currentAngle:F1})";
                lblPosY.Text = _currentY.ToString("F1");

                UpdateCarPosition();
            });
        }
        
        private void UpdateCarPosition()
        {
            // Canvas koordinatlarına çevir (Merkez + Offset)
            double screenX = _centerX + (_currentX * _scale);
            double screenY = _centerY + (_currentY * _scale);
            
            Canvas.SetLeft(_carMarker, screenX - 10); // Marker center
            Canvas.SetTop(_carMarker, screenY - 10);
            
            _pathLine.Points.Add(new Point(screenX, screenY));
            
            // Eğer harita dışına çıkarsa temizleme veya scale etme eklenebilir
        }

        private void NetworkService_OnLog(string message)
        {
            Dispatcher.Invoke(() => Log(message));
        }

        private void Log(string message)
        {
            string logMsg = $"[{DateTime.Now:HH:mm:ss}] {message}";
            lstLog.Items.Insert(0, logMsg);
        }
    }
}