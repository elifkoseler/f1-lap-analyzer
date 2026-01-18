using F1LapAnalyzer.Core.Models;
using F1LapAnalyzer.Core.Services;
using Microsoft.AspNetCore.Mvc;

namespace F1LapAnalyzer.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class PredictionController : ControllerBase
{
    private readonly IOpenF1Service _openF1Service;
    private readonly IPitStopPredictionService _pitStopPredictionService;

    public PredictionController(
        IOpenF1Service openF1Service,
        IPitStopPredictionService pitStopPredictionService)
    {
        _openF1Service = openF1Service;
        _pitStopPredictionService = pitStopPredictionService;
    }

    [HttpGet("pitstop/session/{sessionKey}/driver/{driverNumber}")]
    public async Task<ActionResult<PitStopPrediction>> GetPitStopPrediction(
        int sessionKey,
        int driverNumber,
        [FromQuery] string tireCompound = "MEDIUM")
    {
        try
        {
            // Fetch driver's laps from OpenF1
            var laps = await _openF1Service.GetLapTimesAsync(sessionKey, driverNumber);

            if (laps == null || laps.Count == 0)
            {
                return NotFound($"No laps found for driver {driverNumber} in session {sessionKey}");
            }

            // Get prediction from ML service
            var prediction = await _pitStopPredictionService.PredictPitStopAsync(laps, tireCompound);

            return Ok(prediction);
        }
        catch (ArgumentException ex)
        {
            return BadRequest(ex.Message);
        }
        catch (HttpRequestException ex)
        {
            return StatusCode(503, $"ML service unavailable: {ex.Message}");
        }
        catch (Exception ex)
        {
            return StatusCode(500, $"Prediction failed: {ex.Message}");
        }
    }

    [HttpGet("strategy-impact/session/{sessionKey}/driver/{driverNumber}/pitlap/{pitLap}")]
    public async Task<ActionResult<StrategyImpactResponse>> GetStrategyImpact(
        int sessionKey,
        int driverNumber,
        int pitLap)
    {
        try
        {
            // Fetch all laps for the session
            var allLaps = await _openF1Service.GetLapTimesAsync(sessionKey);
            var drivers = await _openF1Service.GetDriversAsync(sessionKey);

            if (allLaps == null || allLaps.Count == 0)
            {
                return NotFound($"No laps found for session {sessionKey}");
            }

            // Build driver data from laps
            var driverLookup = drivers.ToDictionary(d => d.DriverNumber);
            var driversData = new List<DriverLapData>();

            var lapsByDriver = allLaps
                .Where(l => l.LapDuration.HasValue && l.LapDuration.Value > 0 && l.LapNumber <= pitLap)
                .GroupBy(l => l.DriverNumber);

            foreach (var group in lapsByDriver)
            {
                var driverLaps = group.OrderBy(l => l.LapNumber).ToList();
                if (driverLaps.Count == 0) continue;

                var validLapTimes = driverLaps
                    .Where(l => l.LapDuration.HasValue)
                    .Select(l => l.LapDuration!.Value)
                    .ToList();

                if (validLapTimes.Count == 0) continue;

                // Filter out obvious outliers (pit laps, etc.)
                var median = validLapTimes.OrderBy(t => t).ElementAt(validLapTimes.Count / 2);
                var cleanLapTimes = validLapTimes.Where(t => t < median * 1.15).ToList();

                if (cleanLapTimes.Count == 0) cleanLapTimes = validLapTimes;

                var totalTime = validLapTimes.Sum();
                var avgLapTime = cleanLapTimes.Average();

                driverLookup.TryGetValue(group.Key, out var driverInfo);

                driversData.Add(new DriverLapData
                {
                    DriverNumber = group.Key,
                    DriverName = driverInfo?.FullName ?? $"Driver #{group.Key}",
                    TotalTime = totalTime,
                    AvgLapTime = avgLapTime,
                    LapsCompleted = driverLaps.Count
                });
            }

            if (!driversData.Any(d => d.DriverNumber == driverNumber))
            {
                return NotFound($"Driver {driverNumber} not found in session {sessionKey}");
            }

            // Create strategy impact request
            var request = new StrategyImpactRequest
            {
                TargetDriverNumber = driverNumber,
                PitLap = pitLap,
                DriversData = driversData,
                PitStopTime = 22.0,
                FreshTireAdvantage = 0.5,
                FreshTireLaps = 5
            };

            var result = await _pitStopPredictionService.GetStrategyImpactAsync(request);

            return Ok(result);
        }
        catch (HttpRequestException ex)
        {
            return StatusCode(503, $"ML service unavailable: {ex.Message}");
        }
        catch (Exception ex)
        {
            return StatusCode(500, $"Strategy impact calculation failed: {ex.Message}");
        }
    }
}
