using System.Net.Http.Json;
using F1LapAnalyzer.Core.Models;

namespace F1LapAnalyzer.Core.Services;

public class OpenF1Service : IOpenF1Service
{
    private readonly HttpClient _httpClient;

    public OpenF1Service(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public async Task<List<LapTime>> GetLapTimesAsync(int sessionKey, int? driverNumber = null)
    {
        var url = $"https://api.openf1.org/v1/laps?session_key={sessionKey}";
        if (driverNumber.HasValue)
        {
            url += $"&driver_number={driverNumber.Value}";
        }

        var response = await _httpClient.GetFromJsonAsync<List<LapTime>>(url);
        return response ?? new List<LapTime>();
    }

    public async Task<List<Driver>> GetDriversAsync(int sessionKey)
    {
        var url = $"https://api.openf1.org/v1/drivers?session_key={sessionKey}";
        var response = await _httpClient.GetFromJsonAsync<List<Driver>>(url);
        return response ?? new List<Driver>();
    }
}
