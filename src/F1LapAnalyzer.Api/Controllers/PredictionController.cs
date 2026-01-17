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
}
