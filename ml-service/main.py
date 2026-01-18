from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from model import TireDegradationModel, PitStopPrediction

app = FastAPI(
    title="F1 Pit Stop Prediction Service",
    description="ML service for predicting optimal pit stop windows based on tire degradation",
    version="2.1.0"
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
    r2_score: float = Field(..., description="Model fit quality (0-1)")
    laps_analyzed: int = Field(..., description="Number of clean laps used in analysis")
    predicted_lap_times: list[float] = Field(..., description="Predicted times for next laps")
    tire_compound: str = Field(..., description="Tire compound analyzed")
    is_degrading: bool = Field(..., description="Whether tires are actually degrading")
    recommendation: str = Field(..., description="Human-readable strategy recommendation")


# Strategy Impact Models
class DriverLapData(BaseModel):
    driver_number: int
    driver_name: str
    total_time: float  # Cumulative race time at pit lap
    avg_lap_time: float
    laps_completed: int


class StrategyImpactRequest(BaseModel):
    target_driver_number: int = Field(..., description="Driver number for pit stop analysis")
    pit_lap: int = Field(..., description="Suggested lap to pit")
    drivers_data: list[DriverLapData] = Field(..., description="All drivers' race data")
    pit_stop_time: float = Field(default=22.0, description="Pit stop time loss in seconds")
    fresh_tire_advantage: float = Field(default=0.5, description="Seconds per lap faster on fresh tires")
    fresh_tire_laps: int = Field(default=5, description="Number of laps with fresh tire advantage")


class NearbyDriver(BaseModel):
    driver_number: int
    driver_name: str
    gap: float  # Positive = behind, Negative = ahead
    position: int


class StrategyImpactResponse(BaseModel):
    current_position: int
    projected_position: int
    position_change: int  # Positive = gained positions, Negative = lost
    time_lost_in_pit: float
    time_gained_fresh_tires: float
    net_time_impact: float
    ahead_of: list[NearbyDriver]  # Drivers we'd come out ahead of
    behind_of: list[NearbyDriver]  # Drivers we'd come out behind


@app.get("/")
async def root():
    return {
        "service": "F1 Pit Stop Prediction",
        "version": "2.1.0",
        "endpoints": {
            "POST /predict/pitstop": "Predict optimal pit stop window",
            "POST /predict/strategy-impact": "Calculate position impact of pit stop"
        },
        "features": [
            "Polynomial regression (degree 2) for tire degradation curves",
            "Automatic outlier detection (2 std dev)",
            "Confidence scoring based on R², data quantity, and consistency",
            "Degradation direction detection (degrading vs improving)",
            "Strategy impact analysis with position projections"
        ]
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/predict/pitstop", response_model=PitStopResponse)
async def predict_pitstop(request: PitStopRequest):
    """
    Predict the optimal pit stop window based on tire degradation analysis.
    
    Uses polynomial regression to model tire degradation curves and
    predicts when performance will degrade beyond acceptable threshold.
    """
    if not request.laps:
        raise HTTPException(status_code=400, detail="No lap data provided")
    
    min_laps = TireDegradationModel.MIN_LAPS_REQUIRED
    
    if len(request.laps) < min_laps:
        raise HTTPException(
            status_code=400, 
            detail=f"Need at least {min_laps} laps for reliable prediction"
        )
    
    # Extract stint laps and durations
    stint_laps = [lap.stint_lap for lap in request.laps]
    lap_durations = [lap.lap_duration for lap in request.laps]
    tire_compound = request.laps[0].tire_compound
    
    # Pre-filter obviously invalid laps
    valid_laps = []
    valid_durations = []
    median_duration = sorted(lap_durations)[len(lap_durations) // 2]
    
    for stint_lap, duration in zip(stint_laps, lap_durations):
        if duration < median_duration * 1.2:
            valid_laps.append(stint_lap)
            valid_durations.append(duration)
    
    if len(valid_laps) < min_laps:
        valid_laps = stint_laps
        valid_durations = lap_durations
    
    try:
        model = TireDegradationModel(
            degradation_threshold=request.degradation_threshold
        )
        model.fit(valid_laps, valid_durations)
        
        current_stint_lap = max(stint_laps)
        
        prediction = model.predict_pit_window(
            current_stint_lap=current_stint_lap,
            max_stint_length=request.max_stint_length
        )
        
        return PitStopResponse(
            optimal_pit_lap=prediction.optimal_pit_lap,
            confidence=prediction.confidence,
            degradation_rate=prediction.degradation_rate,
            r2_score=prediction.r2_score,
            laps_analyzed=prediction.laps_analyzed,
            predicted_lap_times=prediction.predicted_lap_times,
            tire_compound=tire_compound,
            is_degrading=prediction.is_degrading,
            recommendation=prediction.recommendation
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/strategy-impact", response_model=StrategyImpactResponse)
async def predict_strategy_impact(request: StrategyImpactRequest):
    """
    Calculate the position impact of a pit stop strategy.
    
    Simulates what happens when a driver pits on a specific lap:
    - Time lost during pit stop (default 22 seconds)
    - Time gained from fresh tire advantage (default 0.5s/lap for 5 laps)
    - Projected position after pit stop
    - Nearby drivers after pit exit
    """
    if not request.drivers_data:
        raise HTTPException(status_code=400, detail="No driver data provided")
    
    # Find target driver
    target_driver = None
    for driver in request.drivers_data:
        if driver.driver_number == request.target_driver_number:
            target_driver = driver
            break
    
    if not target_driver:
        raise HTTPException(status_code=404, detail=f"Driver {request.target_driver_number} not found")
    
    # Sort drivers by total time to get current positions
    sorted_drivers = sorted(request.drivers_data, key=lambda d: d.total_time)
    
    # Find current position
    current_position = 1
    for i, driver in enumerate(sorted_drivers):
        if driver.driver_number == request.target_driver_number:
            current_position = i + 1
            break
    
    # Calculate time impact
    time_lost_in_pit = request.pit_stop_time
    time_gained_fresh_tires = request.fresh_tire_advantage * request.fresh_tire_laps
    net_time_impact = time_lost_in_pit - time_gained_fresh_tires
    
    # Calculate projected race time after pit
    target_projected_time = target_driver.total_time + time_lost_in_pit
    
    # For other drivers, project their time assuming they continue at avg pace
    # and don't pit (simplified model)
    projected_standings = []
    for driver in request.drivers_data:
        if driver.driver_number == request.target_driver_number:
            projected_standings.append({
                'driver_number': driver.driver_number,
                'driver_name': driver.driver_name,
                'projected_time': target_projected_time,
                'is_target': True
            })
        else:
            # Assume other drivers continue at their average pace
            # Add one lap of racing time (the pit lap)
            projected_time = driver.total_time + driver.avg_lap_time
            projected_standings.append({
                'driver_number': driver.driver_number,
                'driver_name': driver.driver_name,
                'projected_time': projected_time,
                'is_target': False
            })
    
    # Sort by projected time
    projected_standings.sort(key=lambda x: x['projected_time'])
    
    # Find projected position
    projected_position = 1
    for i, driver in enumerate(projected_standings):
        if driver['is_target']:
            projected_position = i + 1
            break
    
    position_change = current_position - projected_position  # Positive = gained positions
    
    # Find nearby drivers after pit
    ahead_of = []
    behind_of = []
    
    target_idx = next(i for i, d in enumerate(projected_standings) if d['is_target'])
    
    # Drivers we'd come out ahead of (up to 3)
    for i in range(target_idx + 1, min(target_idx + 4, len(projected_standings))):
        driver = projected_standings[i]
        gap = driver['projected_time'] - target_projected_time
        ahead_of.append(NearbyDriver(
            driver_number=driver['driver_number'],
            driver_name=driver['driver_name'],
            gap=round(gap, 3),
            position=i + 1
        ))
    
    # Drivers we'd come out behind (up to 3)
    for i in range(max(0, target_idx - 3), target_idx):
        driver = projected_standings[i]
        gap = target_projected_time - driver['projected_time']
        behind_of.append(NearbyDriver(
            driver_number=driver['driver_number'],
            driver_name=driver['driver_name'],
            gap=round(gap, 3),
            position=i + 1
        ))
    
    # Reverse behind_of so closest driver is first
    behind_of.reverse()
    
    return StrategyImpactResponse(
        current_position=current_position,
        projected_position=projected_position,
        position_change=position_change,
        time_lost_in_pit=round(time_lost_in_pit, 3),
        time_gained_fresh_tires=round(time_gained_fresh_tires, 3),
        net_time_impact=round(net_time_impact, 3),
        ahead_of=ahead_of,
        behind_of=behind_of
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
