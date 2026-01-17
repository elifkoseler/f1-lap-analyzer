using F1LapAnalyzer.Core.Models;

namespace F1LapAnalyzer.Core.Services;

public interface ILapAnalysisService
{
    SessionSummary GetSessionSummary(List<LapTime> laps, List<Driver> drivers, int sessionKey);
}
