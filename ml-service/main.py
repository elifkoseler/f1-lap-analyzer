from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from model import TireDegradationModel, PitStopPrediction

app = FastAPI(
    title="F1 Pit Stop Prediction Service",
    description="ML service for predicting optimal pit stop windows based on tire degradation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LapData(BaseModel):
    lap_number: int = Field(..., description="Overall lap number in the race")
    lap_duration: float = Field(..., description="Lap time in seconds")
    tire_compound: str = Field(..., description="Tire compound (SOFT, MEDIUM, HARD)")
    stint_lap: int = Field(..., description="Lap number within current stint")


class PitStopRequest(BaseModel):
    laps: list[LapData] = Field(..., description="List of lap data for analysis")
    degradation_threshold: float = Field(
        default=2.0, 
        description="Max acceptable lap time increase (seconds) before pit stop"
    )
    max_stint_length: int = Field(
        default=40,
        description="Maximum possible stint length"
    )


class PitStopResponse(BaseModel):
    optimal_pit_lap: int = Field(..., description="Recommended lap to pit")
    confidence: float = Field(..., description="Prediction confidence (0-1)")
    degradation_rate: float = Field(..., description="Seconds lost per lap due to tire wear")
    predicted_lap_times: list[float] = Field(..., description="Predicted times for next laps")
    tire_compound: str = Field(..., description="Tire compound analyzed")
    laps_analyzed: int = Field(..., description="Number of laps used in analysis")


@app.get("/")
async def root():
    return {
        "service": "F1 Pit Stop Prediction",
        "version": "1.0.0",
        "endpoints": {
            "POST /predict/pitstop": "Predict optimal pit stop window"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/predict/pitstop", response_model=PitStopResponse)
async def predict_pitstop(request: PitStopRequest):
    """
    Predict the optimal pit stop window based on tire degradation analysis.
    
    Analyzes lap time progression to determine tire degradation rate and
    predicts when performance will degrade beyond acceptable threshold.
    """
    if not request.laps:
        raise HTTPException(status_code=400, detail="No lap data provided")
    
    if len(request.laps) < 3:
        raise HTTPException(
            status_code=400, 
            detail="Need at least 3 laps for reliable prediction"
        )
    
    # Extract stint laps and durations
    stint_laps = [lap.stint_lap for lap in request.laps]
    lap_durations = [lap.lap_duration for lap in request.laps]
    tire_compound = request.laps[0].tire_compound
    
    # Filter out obviously invalid laps (pit stops, safety cars typically > 20% slower)
    valid_laps = []
    valid_durations = []
    median_duration = sorted(lap_durations)[len(lap_durations) // 2]
    
    for stint_lap, duration in zip(stint_laps, lap_durations):
        if duration < median_duration * 1.2:  # Within 20% of median
            valid_laps.append(stint_lap)
            valid_durations.append(duration)
    
    if len(valid_laps) < 3:
        # Fall back to all data if too much filtered
        valid_laps = stint_laps
        valid_durations = lap_durations
    
    try:
        # Create and fit the degradation model
        model = TireDegradationModel(
            degradation_threshold=request.degradation_threshold
        )
        model.fit(valid_laps, valid_durations)
        
        # Get current stint lap (last lap in the data)
        current_stint_lap = max(stint_laps)
        
        # Predict optimal pit window
        prediction = model.predict_pit_window(
            current_stint_lap=current_stint_lap,
            max_stint_length=request.max_stint_length
        )
        
        return PitStopResponse(
            optimal_pit_lap=prediction.optimal_pit_lap,
            confidence=prediction.confidence,
            degradation_rate=prediction.degradation_rate,
            predicted_lap_times=prediction.predicted_lap_times,
            tire_compound=tire_compound,
            laps_analyzed=len(valid_laps)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
