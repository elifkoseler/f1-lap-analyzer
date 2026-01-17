namespace F1LapAnalyzer.Core.Models;

public class DriverSummary
{
    public int DriverNumber { get; set; }
    public string DriverName { get; set; } = string.Empty;
    public string TeamName { get; set; } = string.Empty;
    public double? FastestLap { get; set; }
    public double? AverageLap { get; set; }
    public int TotalLaps { get; set; }
    public double? GapToLeader { get; set; }
}

public class SessionSummary
{
    public int SessionKey { get; set; }
    public List<DriverSummary> Drivers { get; set; } = new();
}
