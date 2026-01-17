import numpy as np
from sklearn.linear_model import LinearRegression
from dataclasses import dataclass


@dataclass
class PitStopPrediction:
    optimal_pit_lap: int
    confidence: float
    degradation_rate: float
    predicted_lap_times: list[float]


class TireDegradationModel:
    """
    Model to analyze tire degradation and predict optimal pit stop windows.
    Uses linear regression to model lap time degradation over stint length.
    """
    
    def __init__(self, degradation_threshold: float = 2.0):
        """
        Args:
            degradation_threshold: Maximum acceptable lap time increase (seconds)
                                   before recommending a pit stop
        """
        self.model = LinearRegression()
        self.degradation_threshold = degradation_threshold
        self.is_fitted = False
        self.base_lap_time: float = 0.0
        self.degradation_rate: float = 0.0
        self.r_squared: float = 0.0
        
    def fit(self, stint_laps: list[int], lap_durations: list[float]) -> "TireDegradationModel":
        """
        Learn the degradation pattern from lap times.
        
        Args:
            stint_laps: List of lap numbers within the stint (1, 2, 3, ...)
            lap_durations: List of corresponding lap durations in seconds
            
        Returns:
            self for method chaining
        """
        if len(stint_laps) < 2 or len(lap_durations) < 2:
            raise ValueError("Need at least 2 laps to fit degradation model")
            
        if len(stint_laps) != len(lap_durations):
            raise ValueError("stint_laps and lap_durations must have same length")
        
        X = np.array(stint_laps).reshape(-1, 1)
        y = np.array(lap_durations)
        
        # Remove outliers (pit in/out laps, safety cars, etc.)
        # Simple outlier removal: remove laps > 2 std from mean
        mean_time = np.mean(y)
        std_time = np.std(y)
        mask = np.abs(y - mean_time) < 2 * std_time
        
        if np.sum(mask) < 2:
            # Not enough data after outlier removal, use all data
            mask = np.ones(len(y), dtype=bool)
        
        X_clean = X[mask]
        y_clean = y[mask]
        
        self.model.fit(X_clean, y_clean)
        
        self.base_lap_time = self.model.intercept_
        self.degradation_rate = self.model.coef_[0]
        
        # Calculate R-squared for confidence
        y_pred = self.model.predict(X_clean)
        ss_res = np.sum((y_clean - y_pred) ** 2)
        ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
        self.r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        self.is_fitted = True
        return self
    
    def predict_lap_time(self, stint_lap: int) -> float:
        """Predict lap time for a given stint lap number."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")
        return self.model.predict([[stint_lap]])[0]
    
    def predict_pit_window(
        self, 
        current_stint_lap: int, 
        max_stint_length: int = 40
    ) -> PitStopPrediction:
        """
        Predict the optimal pit stop window based on tire degradation.
        
        Args:
            current_stint_lap: Current lap number in the stint
            max_stint_length: Maximum possible stint length
            
        Returns:
            PitStopPrediction with optimal pit lap and related metrics
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")
        
        # Calculate predicted lap times for future laps
        future_laps = range(current_stint_lap, max_stint_length + 1)
        predicted_times = [self.predict_lap_time(lap) for lap in future_laps]
        
        # Find optimal pit lap based on degradation threshold
        optimal_pit_lap = max_stint_length  # Default to max if no threshold crossed
        
        if self.degradation_rate > 0:
            # Positive degradation (times getting slower)
            # Find when lap time exceeds base + threshold
            threshold_time = self.base_lap_time + self.degradation_threshold
            
            for lap, predicted_time in zip(future_laps, predicted_times):
                if predicted_time > threshold_time:
                    optimal_pit_lap = lap
                    break
        else:
            # Negative or zero degradation (tires improving or stable)
            # Push stint to maximum
            optimal_pit_lap = max_stint_length
        
        # Ensure optimal pit lap is at least current lap + 1
        optimal_pit_lap = max(optimal_pit_lap, current_stint_lap + 1)
        
        # Calculate confidence based on R-squared and data quality
        confidence = self._calculate_confidence()
        
        return PitStopPrediction(
            optimal_pit_lap=optimal_pit_lap,
            confidence=confidence,
            degradation_rate=round(self.degradation_rate, 4),
            predicted_lap_times=[round(t, 3) for t in predicted_times[:10]]  # Next 10 laps
        )
    
    def _calculate_confidence(self) -> float:
        """
        Calculate prediction confidence based on model fit quality.
        """
        if not self.is_fitted:
            return 0.0
        
        # Base confidence on R-squared
        confidence = max(0.0, min(1.0, self.r_squared))
        
        # Adjust for degradation rate reasonableness
        # Typical F1 degradation is 0.01-0.1 seconds per lap
        if 0.01 <= abs(self.degradation_rate) <= 0.15:
            confidence *= 1.0  # Reasonable range
        elif 0.005 <= abs(self.degradation_rate) <= 0.2:
            confidence *= 0.8  # Slightly outside normal
        else:
            confidence *= 0.5  # Unusual degradation
        
        return round(confidence, 3)
