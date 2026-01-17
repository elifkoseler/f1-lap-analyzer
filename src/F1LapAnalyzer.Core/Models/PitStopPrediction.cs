using System.Text.Json.Serialization;

namespace F1LapAnalyzer.Core.Models;

public class LapData
{
    [JsonPropertyName("lap_number")]
    public int LapNumber { get; set; }

    [JsonPropertyName("lap_duration")]
    public double LapDuration { get; set; }

    [JsonPropertyName("stint_lap")]
    public int StintLap { get; set; }

    [JsonPropertyName("tire_compound")]
    public string TireCompound { get; set; } = "MEDIUM";
}

public class PitStopRequest
{
    [JsonPropertyName("laps")]
    public List<LapData> Laps { get; set; } = new();

    [JsonPropertyName("degradation_threshold")]
    public double DegradationThreshold { get; set; } = 2.0;

    [JsonPropertyName("max_stint_length")]
    public int MaxStintLength { get; set; } = 40;
}

public class PitStopPrediction
{
    [JsonPropertyName("optimal_pit_lap")]
    public int OptimalPitLap { get; set; }

    public int WindowStart { get; set; }

    public int WindowEnd { get; set; }

    [JsonPropertyName("confidence")]
    public double Confidence { get; set; }

    [JsonPropertyName("degradation_rate")]
    public double DegradationRate { get; set; }

    public string Recommendation { get; set; } = string.Empty;

    [JsonPropertyName("predicted_lap_times")]
    public List<double> PredictedLapTimes { get; set; } = new();

    [JsonPropertyName("tire_compound")]
    public string TireCompound { get; set; } = string.Empty;

    [JsonPropertyName("laps_analyzed")]
    public int LapsAnalyzed { get; set; }
}
