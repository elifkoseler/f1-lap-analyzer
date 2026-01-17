using System.Text.Json.Serialization;

namespace F1LapAnalyzer.Core.Models;

public class LapTime
{
    [JsonPropertyName("driver_number")]
    public int DriverNumber { get; set; }

    [JsonPropertyName("lap_number")]
    public int LapNumber { get; set; }

    [JsonPropertyName("lap_duration")]
    public double? LapDuration { get; set; }

    [JsonPropertyName("duration_sector_1")]
    public double? Sector1Duration { get; set; }

    [JsonPropertyName("duration_sector_2")]
    public double? Sector2Duration { get; set; }

    [JsonPropertyName("duration_sector_3")]
    public double? Sector3Duration { get; set; }

    [JsonPropertyName("date_start")]
    public DateTime? DateUtc { get; set; }
}
