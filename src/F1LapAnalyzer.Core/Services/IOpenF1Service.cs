using F1LapAnalyzer.Core.Models;

namespace F1LapAnalyzer.Core.Services;

public interface IOpenF1Service
{
    Task<List<LapTime>> GetLapTimesAsync(int sessionKey, int? driverNumber = null);
    Task<List<Driver>> GetDriversAsync(int sessionKey);
}
