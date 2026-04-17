import numpy as np
from scipy.interpolate import interp1d
from app.inference.model_loader import model_loader


def predict_recurrence(feature_vector: list[float], query_years: int) -> dict:
    """
    Run RSF inference and return recurrence probability
    
    Args:
        feature_vector: 28 features (from Feature Service)
        query_years: How many years to predict (e.g., 5 for 5-year risk)
    
    Returns:
        {
            "probability_pct": float,
            "risk_level": str,
            "survival_curve": list,
            "model_version": str
        }
    """
    # Load model
    model = model_loader.get_model()
    
    # Convert to numpy array
    X = np.array(feature_vector).reshape(1, -1)
    
    if X.shape[1] != 28:
        raise ValueError(f"Expected 28 features, got {X.shape[1]}")
    
    # Get survival function from RSF
    survival_fn = model.predict_survival_function(X)[0]
    
    # Interpolate survival probability at target time
    target_months = query_years * 12
    
    # Get time points and survival probabilities from the step function
    times = survival_fn.x
    survival_probs = survival_fn.y
    
    # Interpolate to get S(target_months)
    interp = interp1d(
        times,
        survival_probs,
        kind='linear',
        bounds_error=False,
        fill_value=(1.0, survival_probs[-1])  # Extrapolate if needed
    )
    
    survival_prob = float(interp(target_months))
    
    # P(recurrence) = 1 - S(t)
    recurrence_prob = 1 - survival_prob
    probability_pct = recurrence_prob * 100
    
    # Determine risk level
    if probability_pct < 15:
        risk_level = "Low"
    elif probability_pct < 35:
        risk_level = "Moderate"
    elif probability_pct < 60:
        risk_level = "High"
    else:
        risk_level = "Very High"
    
    # Generate survival curve for visualization
    time_points = list(range(0, query_years * 12 + 1, 6))  # Every 6 months
    survival_curve = []
    for t in time_points:
        s_t = float(interp(t))
        recur_t = (1 - s_t) * 100
        survival_curve.append({
            "months": t,
            "years": round(t / 12, 1),
            "recurrence_probability_pct": round(recur_t, 1)
        })
    
    return {
        "probability_pct": round(probability_pct, 1),
        "risk_level": risk_level,
        "survival_curve": survival_curve,
        "model_version": model_loader.model_version,
        "interpretation": generate_interpretation(probability_pct, risk_level, query_years)
    }


def generate_interpretation(probability_pct: float, risk_level: str, years: int) -> str:
    """Generate human-readable interpretation"""
    
    if risk_level == "Low":
        return (
            f"Based on your profile, the estimated probability of cancer recurrence "
            f"within {years} years is {probability_pct:.1f}%, which falls in the "
            f"**low risk** category. This suggests a favorable prognosis with the "
            f"current treatment plan."
        )
    elif risk_level == "Moderate":
        return (
            f"Based on your profile, the estimated probability of cancer recurrence "
            f"within {years} years is {probability_pct:.1f}%, which falls in the "
            f"**moderate risk** category. Continue regular follow-up appointments "
            f"and discuss any concerns with your oncologist."
        )
    elif risk_level == "High":
        return (
            f"Based on your profile, the estimated probability of cancer recurrence "
            f"within {years} years is {probability_pct:.1f}%, which falls in the "
            f"**high risk** category. Your medical team may recommend closer monitoring "
            f"or additional preventive measures."
        )
    else:  # Very High
        return (
            f"Based on your profile, the estimated probability of cancer recurrence "
            f"within {years} years is {probability_pct:.1f}%, which falls in the "
            f"**very high risk** category. Please discuss enhanced surveillance and "
            f"treatment options with your oncology team."
        )


        