using F1LapAnalyzer.Core.Models;
using F1LapAnalyzer.Core.Services;
using Microsoft.AspNetCore.Mvc;

namespace F1LapAnalyzer.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class DriversController : ControllerBase
{
    private readonly IOpenF1Service _openF1Service;

    public DriversController(IOpenF1Service openF1Service)
    {
        _openF1Service = openF1Service;
    }

    [HttpGet("session/{sessionKey}")]
    public async Task<ActionResult<List<Driver>>> GetDrivers(int sessionKey)
    {
        var drivers = await _openF1Service.GetDriversAsync(sessionKey);
        return Ok(drivers);
    }
}
