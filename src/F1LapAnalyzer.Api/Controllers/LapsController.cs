using F1LapAnalyzer.Core.Models;
using F1LapAnalyzer.Core.Services;
using Microsoft.AspNetCore.Mvc;

namespace F1LapAnalyzer.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class LapsController : ControllerBase
{
    private readonly IOpenF1Service _openF1Service;

    public LapsController(IOpenF1Service openF1Service)
    {
        _openF1Service = openF1Service;
    }

    [HttpGet("session/{sessionKey}")]
    public async Task<ActionResult<List<LapTime>>> GetLapTimes(int sessionKey)
    {
        var lapTimes = await _openF1Service.GetLapTimesAsync(sessionKey);
        return Ok(lapTimes);
    }

    [HttpGet("session/{sessionKey}/driver/{driverNumber}")]
    public async Task<ActionResult<List<LapTime>>> GetLapTimesForDriver(int sessionKey, int driverNumber)
    {
        var lapTimes = await _openF1Service.GetLapTimesAsync(sessionKey, driverNumber);
        return Ok(lapTimes);
    }

    [HttpGet("session/{sessionKey}/fastest")]
    public async Task<ActionResult<LapTime>> GetFastestLap(int sessionKey)
    {
        var lapTimes = await _openF1Service.GetLapTimesAsync(sessionKey);
        var fastestLap = lapTimes
            .Where(l => l.LapDuration.HasValue)
            .OrderBy(l => l.LapDuration)
            .FirstOrDefault();

        if (fastestLap == null)
        {
            return NotFound("No valid lap times found for this session.");
        }

        return Ok(fastestLap);
    }
}
