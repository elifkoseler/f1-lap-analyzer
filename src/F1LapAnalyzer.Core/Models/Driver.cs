using System.Text.Json.Serialization;

namespace F1LapAnalyzer.Core.Models;

public class Driver
{
    [JsonPropertyName("driver_number")]
    public int DriverNumber { get; set; }

    [JsonPropertyName("full_name")]
    public string FullName { get; set; } = string.Empty;

    [JsonPropertyName("team_name")]
    public string TeamName { get; set; } = string.Empty;

    [JsonPropertyName("name_acronym")]
    public string NameAcronym { get; set; } = string.Empty;
}
