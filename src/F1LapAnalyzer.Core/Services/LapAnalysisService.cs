using F1LapAnalyzer.Core.Models;

namespace F1LapAnalyzer.Core.Services;

public class LapAnalysisService : ILapAnalysisService
{
    public SessionSummary GetSessionSummary(List<LapTime> laps, List<Driver> drivers, int sessionKey)
    {
        var driverLookup = drivers.ToDictionary(d => d.DriverNumber);

        var driverSummaries = laps
            .GroupBy(l => l.DriverNumber)
            .Select(g =>
            {
                var validLaps = g.Where(l => l.LapDuration.HasValue).ToList();
                var fastestLap = validLaps.Any() ? validLaps.Min(l => l.LapDuration) : null;
                var averageLap = validLaps.Any() ? validLaps.Average(l => l.LapDuration!.Value) : (double?)null;

                driverLookup.TryGetValue(g.Key, out var driver);

                return new DriverSummary
                {
                    DriverNumber = g.Key,
                    DriverName = driver?.FullName ?? string.Empty,
                    TeamName = driver?.TeamName ?? string.Empty,
                    FastestLap = fastestLap,
                    AverageLap = averageLap,
                    TotalLaps = g.Count()
                };
            })
            .ToList();

        // Calculate overall fastest lap
        var overallFastest = driverSummaries
            .Where(d => d.FastestLap.HasValue)
            .Min(d => d.FastestLap);

        // Calculate gap to leader
        foreach (var summary in driverSummaries)
        {
            if (summary.FastestLap.HasValue && overallFastest.HasValue)
            {
                summary.GapToLeader = summary.FastestLap.Value - overallFastest.Value;
            }
        }

        // Sort by fastest lap ascending
        var sortedSummaries = driverSummaries
            .OrderBy(d => d.FastestLap ?? double.MaxValue)
            .ToList();

        return new SessionSummary
        {
            SessionKey = sessionKey,
            Drivers = sortedSummaries
        };
    }
}
