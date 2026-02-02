using System;

namespace OtonomArabaArayuz.Models
{
    public class TelemetryData
    {
        public double Speed { get; set; } // cm/s or m/s
        public double Distance { get; set; } // cm
        public double Angle { get; set; } // Derece (0-360)
        public DateTime Timestamp { get; set; }

        public TelemetryData()
        {
            Timestamp = DateTime.Now;
        }
    }
}
