import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "larper_master.csv"


def analyze_trend(trend_name):
    df = pd.read_csv(DATA_FILE)

    df["date"] = pd.to_datetime(df["date"])

    trend_df = df[
        df["trend_name"].str.lower() == trend_name.lower()
        ].copy()

    if trend_df.empty:
        return {
            "error": f"Trend '{trend_name}' not found."
        }

    trend_df = trend_df.sort_values("date")

    values = trend_df["search_interest"].tolist()

    if len(values) < 6:
        return {
            "error": "Not enough data points for prediction."
        }


    # =====================================================
    # BASIC METRICS
    # =====================================================

    current_value = values[-1]

    peak_value = max(values)

    overall_average = sum(values) / len(values)


    # Recent 3 readings
    recent = values[-3:]

    # Previous 3 readings
    previous = values[-6:-3]

    recent_average = sum(recent) / len(recent)
    previous_average = sum(previous) / len(previous)


    # =====================================================
    # GROWTH RATE
    # =====================================================

    if previous_average == 0:
        growth_rate = 0
    else:
        growth_rate = (
                              (recent_average - previous_average)
                              / previous_average
                      ) * 100


    # =====================================================
    # DISTANCE FROM PEAK
    # =====================================================

    if peak_value == 0:
        distance_from_peak = 0
    else:
        distance_from_peak = (
                                     (peak_value - current_value)
                                     / peak_value
                             ) * 100


    # =====================================================
    # MOMENTUM
    # =====================================================

    last_change = values[-1] - values[-2]

    previous_change = values[-2] - values[-3]

    momentum = last_change - previous_change


    # =====================================================
    # CURRENT STATUS
    # =====================================================

    if recent_average >= 75:
        status = "Very Popular"

    elif growth_rate >= 20:
        status = "Growing Fast"

    elif growth_rate >= 5:
        status = "Growing"

    elif growth_rate <= -20:
        status = "Losing Popularity"

    elif distance_from_peak >= 35:
        status = "Fading"

    else:
        status = "Stable"


    # =====================================================
    # PREDICTION
    # =====================================================

    if growth_rate >= 15 and momentum >= 0:
        prediction = "Likely to Keep Growing"
        recommendation = "JOIN NOW"

    elif growth_rate >= 5:
        prediction = "Still Growing, But Watch Closely"
        recommendation = "MOVE FAST"

    elif growth_rate < 0 and distance_from_peak >= 20:
        prediction = "Likely to Lose Popularity"
        recommendation = "TRY SOMETHING SIMILAR"

    elif growth_rate <= -20:
        prediction = "Likely to Keep Declining"
        recommendation = "SKIP"

    else:
        prediction = "Likely to Stay Stable"
        recommendation = "MONITOR"


    # =====================================================
    # CONFIDENCE SCORE
    # =====================================================

    confidence = 60

    confidence += min(abs(growth_rate), 20)

    confidence += min(abs(momentum), 10)

    if distance_from_peak > 20:
        confidence += 5

    confidence = int(min(confidence, 95))


    # =====================================================
    # EXPLANATION
    # =====================================================

    reasons = []

    if growth_rate > 10:
        reasons.append("Search interest is rising quickly.")

    elif growth_rate < -10:
        reasons.append("Search interest is falling.")

    else:
        reasons.append("Search interest is relatively stable.")


    if distance_from_peak > 30:
        reasons.append(
            "Current interest is far below its recent peak."
        )

    elif distance_from_peak < 10:
        reasons.append(
            "Current interest remains close to its recent peak."
        )


    if momentum > 0:
        reasons.append(
            "Recent momentum is improving."
        )

    elif momentum < 0:
        reasons.append(
            "Recent momentum is slowing down."
        )


    # =====================================================
    # RETURN RESULTS
    # =====================================================

    return {
        "trend": trend_name,
        "category": trend_df.iloc[0]["category"],
        "current_interest": round(current_value, 1),
        "peak_interest": round(peak_value, 1),
        "recent_average": round(recent_average, 1),
        "growth_rate": round(growth_rate, 1),
        "distance_from_peak": round(distance_from_peak, 1),
        "momentum": round(momentum, 1),
        "status": status,
        "prediction": prediction,
        "confidence": confidence,
        "recommendation": recommendation,
        "reasons": reasons
    }


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":

    trend = input(
        "Enter a trend name: "
    )

    result = analyze_trend(trend)

    print("\n")
    print("=" * 50)
    print("LARPER TREND ANALYSIS")
    print("=" * 50)

    if "error" in result:
        print(result["error"])

    else:
        print(f"\nTrend: {result['trend']}")
        print(f"Category: {result['category']}")

        print("\nCURRENT STATUS")
        print(result["status"])

        print("\nAI PREDICTION")
        print(result["prediction"])

        print("\nCONFIDENCE")
        print(f"{result['confidence']}%")

        print("\nRECOMMENDATION")
        print(result["recommendation"])

        print("\nWHY?")
        for reason in result["reasons"]:
            print(f"- {reason}")

        print("\nMETRICS")
        print(
            f"Current interest: "
            f"{result['current_interest']}"
        )

        print(
            f"Peak interest: "
            f"{result['peak_interest']}"
        )

        print(
            f"Growth rate: "
            f"{result['growth_rate']}%"
        )

        print(
            f"Distance from peak: "
            f"{result['distance_from_peak']}%"
        )