using System.Net.Http.Json;
using F1LapAnalyzer.Core.Models;

namespace F1LapAnalyzer.Core.Services;

public class PitStopPredictionService : IPitStopPredictionService
{
    private readonly HttpClient _httpClient;
    private const string MlServiceUrl = "http://localhost:8000/predict/pitstop";

    public PitStopPredictionService(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public async Task<PitStopPrediction> PredictPitStopAsync(List<LapTime> laps, string tireCompound = "MEDIUM")
    {
        if (laps == null || laps.Count < 3)
        {
            throw new ArgumentException("Need at least 3 laps for prediction");
        }

        // Filter valid laps (must have lap duration)
        var validLaps = laps
            .Where(l => l.LapDuration.HasValue && l.LapDuration.Value > 0)
            .OrderBy(l => l.LapNumber)
            .ToList();

        if (validLaps.Count < 3)
        {
            throw new ArgumentException("Need at least 3 valid laps with duration for prediction");
        }

        // Transform to request format
        // Calculate stint lap (assuming continuous stint from first lap)
        var lapDataList = new List<LapData>();
        var firstLapNumber = validLaps.First().LapNumber;

        foreach (var lap in validLaps)
        {
            lapDataList.Add(new LapData
            {
                LapNumber = lap.LapNumber,
                LapDuration = lap.LapDuration!.Value,
                StintLap = lap.LapNumber - firstLapNumber + 1,
                TireCompound = tireCompound
            });
        }

        var request = new PitStopRequest
        {
            Laps = lapDataList,
            DegradationThreshold = 2.0,
            MaxStintLength = 40
        };

        // Call ML service
        var response = await _httpClient.PostAsJsonAsync(MlServiceUrl, request);
        response.EnsureSuccessStatusCode();

        var prediction = await response.Content.ReadFromJsonAsync<PitStopPrediction>();

        if (prediction == null)
        {
            throw new InvalidOperationException("Failed to deserialize prediction response");
        }

        // Calculate window and recommendation
        prediction.WindowStart = Math.Max(1, prediction.OptimalPitLap - 2);
        prediction.WindowEnd = prediction.OptimalPitLap + 2;
        prediction.Recommendation = GenerateRecommendation(prediction);

        return prediction;
    }

    private static string GenerateRecommendation(PitStopPrediction prediction)
    {
        if (prediction.Confidence < 0.3)
        {
            return "Low confidence prediction - insufficient data or inconsistent lap times";
        }

        if (prediction.DegradationRate <= 0)
        {
            return "Tires showing no degradation - extend stint as long as possible";
        }

        if (prediction.DegradationRate < 0.03)
        {
            return $"Low tire degradation ({prediction.DegradationRate:F3}s/lap) - can extend stint beyond lap {prediction.OptimalPitLap}";
        }

        if (prediction.DegradationRate < 0.07)
        {
            return $"Moderate tire degradation ({prediction.DegradationRate:F3}s/lap) - pit window around lap {prediction.OptimalPitLap}";
        }

        return $"High tire degradation ({prediction.DegradationRate:F3}s/lap) - consider pitting before lap {prediction.OptimalPitLap}";
    }
}
