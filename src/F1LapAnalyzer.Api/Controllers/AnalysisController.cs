using F1LapAnalyzer.Core.Models;
using F1LapAnalyzer.Core.Services;
using Microsoft.AspNetCore.Mvc;

namespace F1LapAnalyzer.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AnalysisController : ControllerBase
{
    private readonly IOpenF1Service _openF1Service;
    private readonly ILapAnalysisService _lapAnalysisService;

    public AnalysisController(IOpenF1Service openF1Service, ILapAnalysisService lapAnalysisService)
    {
        _openF1Service = openF1Service;
        _lapAnalysisService = lapAnalysisService;
    }

    [HttpGet("session/{sessionKey}/summary")]
    public async Task<ActionResult<SessionSummary>> GetSessionSummary(int sessionKey)
    {
        var laps = await _openF1Service.GetLapTimesAsync(sessionKey);
        var drivers = await _openF1Service.GetDriversAsync(sessionKey);

        var summary = _lapAnalysisService.GetSessionSummary(laps, drivers, sessionKey);
        return Ok(summary);
    }
}
