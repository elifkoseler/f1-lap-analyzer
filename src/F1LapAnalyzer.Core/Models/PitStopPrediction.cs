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

// Strategy Impact Models
public class DriverLapData
{
    [JsonPropertyName("driver_number")]
    public int DriverNumber { get; set; }

    [JsonPropertyName("driver_name")]
    public string DriverName { get; set; } = string.Empty;

    [JsonPropertyName("total_time")]
    public double TotalTime { get; set; }

    [JsonPropertyName("avg_lap_time")]
    public double AvgLapTime { get; set; }

    [JsonPropertyName("laps_completed")]
    public int LapsCompleted { get; set; }
}

public class StrategyImpactRequest
{
    [JsonPropertyName("target_driver_number")]
    public int TargetDriverNumber { get; set; }

    [JsonPropertyName("pit_lap")]
    public int PitLap { get; set; }

    [JsonPropertyName("drivers_data")]
    public List<DriverLapData> DriversData { get; set; } = new();

    [JsonPropertyName("pit_stop_time")]
    public double PitStopTime { get; set; } = 22.0;

    [JsonPropertyName("fresh_tire_advantage")]
    public double FreshTireAdvantage { get; set; } = 0.5;

    [JsonPropertyName("fresh_tire_laps")]
    public int FreshTireLaps { get; set; } = 5;
}

public class NearbyDriver
{
    [JsonPropertyName("driver_number")]
    public int DriverNumber { get; set; }

    [JsonPropertyName("driver_name")]
    public string DriverName { get; set; } = string.Empty;

    [JsonPropertyName("gap")]
    public double Gap { get; set; }

    [JsonPropertyName("position")]
    public int Position { get; set; }
}

public class StrategyImpactResponse
{
    [JsonPropertyName("current_position")]
    public int CurrentPosition { get; set; }

    [JsonPropertyName("projected_position")]
    public int ProjectedPosition { get; set; }

    [JsonPropertyName("position_change")]
    public int PositionChange { get; set; }

    [JsonPropertyName("time_lost_in_pit")]
    public double TimeLostInPit { get; set; }

    [JsonPropertyName("time_gained_fresh_tires")]
    public double TimeGainedFreshTires { get; set; }

    [JsonPropertyName("net_time_impact")]
    public double NetTimeImpact { get; set; }

    [JsonPropertyName("ahead_of")]
    public List<NearbyDriver> AheadOf { get; set; } = new();

    [JsonPropertyName("behind_of")]
    public List<NearbyDriver> BehindOf { get; set; } = new();
}
