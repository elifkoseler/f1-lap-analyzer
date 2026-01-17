using F1LapAnalyzer.Core.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Configure CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

// Register OpenF1Service with HttpClient
builder.Services.AddHttpClient<IOpenF1Service, OpenF1Service>();

// Register LapAnalysisService
builder.Services.AddScoped<ILapAnalysisService, LapAnalysisService>();

// Register PitStopPredictionService with HttpClient and configuration
var mlServiceUrl = builder.Configuration["ML_SERVICE_URL"] ?? "http://localhost:8000";
builder.Services.AddHttpClient<IPitStopPredictionService, PitStopPredictionService>(
    (serviceProvider, httpClient) => new PitStopPredictionService(httpClient, mlServiceUrl));

var app = builder.Build();

app.UseCors("AllowAll");

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.MapControllers();

app.Run();
