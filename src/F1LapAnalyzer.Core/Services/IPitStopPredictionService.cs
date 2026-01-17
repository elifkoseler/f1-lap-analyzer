using F1LapAnalyzer.Core.Models;

namespace F1LapAnalyzer.Core.Services;

public interface IPitStopPredictionService
{
    Task<PitStopPrediction> PredictPitStopAsync(List<LapTime> laps, string tireCompound = "MEDIUM");
}
