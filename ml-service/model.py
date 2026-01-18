import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from dataclasses import dataclass


@dataclass
class PitStopPrediction:
    optimal_pit_lap: int
    confidence: float
    degradation_rate: float
    r2_score: float
    laps_analyzed: int
    predicted_lap_times: list[float]
    is_degrading: bool
    recommendation: str


class TireDegradationModel:
    """
    Model to analyze tire degradation and predict optimal pit stop windows.
    Uses polynomial regression (degree 2) for better tire degradation curve fitting.
    """
    
    MIN_LAPS_REQUIRED = 5
    
    def __init__(self, degradation_threshold: float = 2.0):
        """
        Args:
            degradation_threshold: Maximum acceptable lap time increase (seconds)
                                   before recommending a pit stop
        """
        # Polynomial regression pipeline (degree 2)
        self.model = Pipeline([
            ('poly', PolynomialFeatures(degree=2, include_bias=False)),
            ('linear', LinearRegression())
        ])
        self.degradation_threshold = degradation_threshold
        self.is_fitted = False
        self.base_lap_time: float = 0.0
        self.degradation_rate: float = 0.0  # Linear component (avg degradation per lap)
        self.r_squared: float = 0.0
        self.laps_analyzed: int = 0
        self.lap_time_std: float = 0.0
        self.is_degrading: bool = True
        
    def _remove_outliers(self, stint_laps: np.ndarray, lap_durations: np.ndarray) -> tuple:
        """
        Remove outliers using 2 standard deviations from mean.
        Removes pit in/out laps, safety car periods, and mistakes.
        """
        mean_time = np.mean(lap_durations)
        std_time = np.std(lap_durations)
        
        if std_time == 0:
            return stint_laps, lap_durations
        
        # Keep laps within 2 standard deviations
        mask = np.abs(lap_durations - mean_time) < 2 * std_time
        
        # Ensure we keep at least MIN_LAPS_REQUIRED laps
        if np.sum(mask) < self.MIN_LAPS_REQUIRED:
            # If too few laps after outlier removal, keep the closest ones to the mean
            deviations = np.abs(lap_durations - mean_time)
            sorted_indices = np.argsort(deviations)
            mask = np.zeros(len(lap_durations), dtype=bool)
            mask[sorted_indices[:self.MIN_LAPS_REQUIRED]] = True
        
        return stint_laps[mask], lap_durations[mask]
        
    def fit(self, stint_laps: list[int], lap_durations: list[float]) -> "TireDegradationModel":
        """
        Learn the degradation pattern from lap times.
        
        Args:
            stint_laps: List of lap numbers within the stint (1, 2, 3, ...)
            lap_durations: List of corresponding lap durations in seconds
            
        Returns:
            self for method chaining
        """
        if len(stint_laps) < self.MIN_LAPS_REQUIRED or len(lap_durations) < self.MIN_LAPS_REQUIRED:
            raise ValueError(f"Need at least {self.MIN_LAPS_REQUIRED} laps for reliable prediction")
            
        if len(stint_laps) != len(lap_durations):
            raise ValueError("stint_laps and lap_durations must have same length")
        
        X = np.array(stint_laps).reshape(-1, 1)
        y = np.array(lap_durations)
        
        # Remove outliers
        X_clean, y_clean = self._remove_outliers(X.flatten(), y)
        X_clean = X_clean.reshape(-1, 1)
        
        self.laps_analyzed = len(X_clean)
        
        if self.laps_analyzed < self.MIN_LAPS_REQUIRED:
            raise ValueError(f"Only {self.laps_analyzed} clean laps after outlier removal. Need at least {self.MIN_LAPS_REQUIRED}.")
        
        # Fit polynomial regression
        self.model.fit(X_clean, y_clean)
        
        # Store cleaned lap time statistics
        self.lap_time_std = np.std(y_clean)
        self.base_lap_time = np.min(y_clean)  # Fastest clean lap as baseline
        
        # Calculate degradation rate as average slope (linear approximation)
        # For polynomial: y = a*x^2 + b*x + c, degradation rate ≈ b (linear component)
        linear_model = LinearRegression()
        linear_model.fit(X_clean, y_clean)
        self.degradation_rate = linear_model.coef_[0]
        
        # Determine if tires are actually degrading
        first_half_avg = np.mean(y_clean[:len(y_clean)//2]) if len(y_clean) > 1 else y_clean[0]
        second_half_avg = np.mean(y_clean[len(y_clean)//2:]) if len(y_clean) > 1 else y_clean[0]
        self.is_degrading = second_half_avg > first_half_avg
        
        # Calculate R-squared for model fit quality
        y_pred = self.model.predict(X_clean)
        ss_res = np.sum((y_clean - y_pred) ** 2)
        ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
        self.r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        self.r_squared = max(0.0, min(1.0, self.r_squared))  # Clamp to [0, 1]
        
        self.is_fitted = True
        return self
    
    def predict_lap_time(self, stint_lap: int) -> float:
        """Predict lap time for a given stint lap number."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")
        return float(self.model.predict([[stint_lap]])[0])
    
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
        future_laps = list(range(current_stint_lap, max_stint_length + 1))
        predicted_times = [self.predict_lap_time(lap) for lap in future_laps]
        
        # Find optimal pit lap based on degradation threshold
        optimal_pit_lap = max_stint_length  # Default to max if no threshold crossed
        
        if self.is_degrading and self.degradation_rate > 0:
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
        
        # Calculate confidence
        confidence = self._calculate_confidence()
        
        # Generate recommendation
        recommendation = self._generate_recommendation(optimal_pit_lap)
        
        return PitStopPrediction(
            optimal_pit_lap=optimal_pit_lap,
            confidence=round(confidence, 3),
            degradation_rate=round(self.degradation_rate, 4),
            r2_score=round(self.r_squared, 3),
            laps_analyzed=self.laps_analyzed,
            predicted_lap_times=[round(t, 3) for t in predicted_times[:10]],
            is_degrading=self.is_degrading,
            recommendation=recommendation
        )
    
    def _calculate_confidence(self) -> float:
        """
        Calculate prediction confidence based on:
        - R² score (40%): How well the model fits the data
        - Number of laps (30%): More data = higher confidence (max at 15 laps)
        - Lap time consistency (30%): Lower std dev = higher confidence
        
        Formula: confidence = (r2 * 0.4) + (min(laps/15, 1) * 0.3) + ((1 - norm_std) * 0.3)
        """
        if not self.is_fitted:
            return 0.0
        
        # Component 1: R² score (40%)
        r2_component = max(0.0, self.r_squared) * 0.4
        
        # Component 2: Number of laps (30%) - max confidence at 15+ laps
        laps_component = min(self.laps_analyzed / 15.0, 1.0) * 0.3
        
        # Component 3: Lap time consistency (30%)
        # Normalize std dev - typical F1 lap time std is 0.3-1.5 seconds
        # Lower std = more consistent = higher confidence
        if self.base_lap_time > 0:
            normalized_std = min(self.lap_time_std / self.base_lap_time, 0.05) / 0.05  # Cap at 5% variation
        else:
            normalized_std = 1.0
        consistency_component = (1.0 - normalized_std) * 0.3
        
        confidence = r2_component + laps_component + consistency_component
        
        # Penalty for unreasonable degradation rates
        if abs(self.degradation_rate) > 0.3:  # More than 0.3s/lap is unusual
            confidence *= 0.7
        
        return max(0.0, min(1.0, confidence))
    
    def _generate_recommendation(self, optimal_pit_lap: int) -> str:
        """
        Generate a human-readable recommendation based on the analysis.
        """
        if not self.is_degrading:
            if self.degradation_rate < -0.02:
                return "Tires improving significantly - driver gaining pace or track evolution. Extend stint."
            else:
                return "Tires stable or slightly improving - no significant degradation detected. Extend stint."
        
        deg_rate = abs(self.degradation_rate)
        
        if deg_rate < 0.02:
            return f"Minimal tire degradation ({deg_rate:.3f}s/lap) - tires in good condition. Can extend beyond lap {optimal_pit_lap}."
        elif deg_rate < 0.05:
            return f"Low tire degradation ({deg_rate:.3f}s/lap) - tires wearing normally. Optimal pit window around lap {optimal_pit_lap}."
        elif deg_rate < 0.08:
            return f"Moderate tire degradation ({deg_rate:.3f}s/lap) - consider pitting around lap {optimal_pit_lap}."
        elif deg_rate < 0.12:
            return f"High tire degradation ({deg_rate:.3f}s/lap) - pit soon, ideally before lap {optimal_pit_lap}."
        else:
            return f"Severe tire degradation ({deg_rate:.3f}s/lap) - pit immediately if possible. Tires critically worn."
