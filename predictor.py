import pandas as pd
from pathlib import Path


# =========================================================
# FILE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "larper_master.csv"


# =========================================================
# HELPER
# =========================================================

def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(value, maximum))


# =========================================================
# ANALYZE TREND
# =========================================================

def analyze_trend(trend_name):

    # -----------------------------------------------------
    # Load dataset
    # -----------------------------------------------------

    df = pd.read_csv(DATA_FILE)

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    trend_df = df[
        df["trend_name"].str.lower()
        == trend_name.lower()
        ].copy()

    if trend_df.empty:
        return {
            "error": f"Trend '{trend_name}' was not found."
        }

    trend_df = trend_df.sort_values("date")

    values = (
        trend_df["search_interest"]
        .astype(float)
        .tolist()
    )

    if len(values) < 8:
        return {
            "error": "Not enough data to analyse this trend."
        }


    # =====================================================
    # BASIC VALUES
    # =====================================================

    current_interest = values[-1]

    peak_interest = max(values)

    average_interest = sum(values) / len(values)


    # Last 4 readings
    recent_values = values[-4:]

    # Previous 4 readings
    previous_values = values[-8:-4]


    recent_average = (
            sum(recent_values)
            / len(recent_values)
    )

    previous_average = (
            sum(previous_values)
            / len(previous_values)
    )


    # =====================================================
    # GROWTH RATE
    # =====================================================

    if previous_average <= 0:

        if recent_average > 0:
            growth_rate = 100
        else:
            growth_rate = 0

    else:

        growth_rate = (
                              (
                                      recent_average
                                      - previous_average
                              )
                              / previous_average
                      ) * 100


    # Prevent strange extreme values from dominating
    growth_rate = clamp(
        growth_rate,
        -100,
        100
    )


    # =====================================================
    # DISTANCE FROM PEAK
    # =====================================================

    if peak_interest > 0:

        distance_from_peak = (
                                     (
                                             peak_interest
                                             - current_interest
                                     )
                                     / peak_interest
                             ) * 100

    else:

        distance_from_peak = 0


    distance_from_peak = clamp(
        distance_from_peak
    )


    # =====================================================
    # MOMENTUM
    # =====================================================

    latest_change = (
            values[-1]
            - values[-2]
    )

    previous_change = (
            values[-2]
            - values[-3]
    )

    momentum = (
            latest_change
            - previous_change
    )


    # =====================================================
    # HOW FAST IS IT GROWING?
    # =====================================================

    if growth_rate >= 25:

        growth_speed = "Very Fast"

    elif growth_rate >= 10:

        growth_speed = "Fast"

    elif growth_rate >= 3:

        growth_speed = "Steady"

    elif growth_rate > -5:

        growth_speed = "Slow"

    else:

        growth_speed = "Declining"


    # =====================================================
    # TREND STATUS
    #
    # ONLY:
    # Just Starting
    # Growing Fast
    # Very Popular
    # Too Crowded
    # Losing Popularity
    # =====================================================

    if (
            growth_rate <= -15
            or (
            distance_from_peak >= 35
            and growth_rate < 0
    )
    ):

        trend_status = "Losing Popularity"


    elif (
            recent_average >= 70
            and growth_rate <= 5
    ):

        trend_status = "Too Crowded"


    elif (
            peak_interest >= 85
            and growth_rate < 0
            and distance_from_peak < 30
    ):

        trend_status = "Too Crowded"


    elif recent_average >= 65:

        trend_status = "Very Popular"


    elif growth_rate >= 10:

        trend_status = "Growing Fast"


    else:

        trend_status = "Just Starting"


    # =====================================================
    # CHANCE IT WILL DIE SOON
    # =====================================================

    death_risk = 25


    # Falling search interest
    if growth_rate < 0:

        death_risk += min(
            abs(growth_rate) * 0.8,
            30
        )


    # Far away from peak
    death_risk += (
            distance_from_peak * 0.3
    )


    # Momentum slowing
    if momentum < 0:

        death_risk += min(
            abs(momentum) * 1.2,
            15
        )


    # Very popular but growth has stopped
    if (
            recent_average >= 70
            and growth_rate <= 3
    ):

        death_risk += 10


    # Strong growth reduces risk
    if growth_rate >= 15:

        death_risk -= 20


    elif growth_rate >= 5:

        death_risk -= 10


    death_risk = int(
        round(
            clamp(death_risk)
        )
    )


    # =====================================================
    # WORTH JOINING SCORE
    # =====================================================

    worth_score = 65


    # Growth helps
    if growth_rate >= 20:

        worth_score += 20

    elif growth_rate >= 10:

        worth_score += 15

    elif growth_rate >= 3:

        worth_score += 8


    # Status impact
    if trend_status == "Just Starting":

        worth_score += 10


    elif trend_status == "Growing Fast":

        worth_score += 15


    elif trend_status == "Very Popular":

        worth_score += 5


    elif trend_status == "Too Crowded":

        worth_score -= 20


    elif trend_status == "Losing Popularity":

        worth_score -= 35


    # Death risk lowers worth
    worth_score -= (
            death_risk * 0.35
    )


    worth_score = int(
        round(
            clamp(worth_score)
        )
    )


    # =====================================================
    # RECOMMENDATION
    # =====================================================

    if (
            worth_score >= 65
            and death_risk <= 45
            and trend_status
            in [
        "Just Starting",
        "Growing Fast",
        "Very Popular"
    ]
    ):

        recommendation = "JOIN NOW"


    elif (
            worth_score >= 35
            and death_risk < 75
    ):

        recommendation = "TRY SOMETHING SIMILAR"


    else:

        recommendation = "SKIP"


    # =====================================================
    # SIMPLE EXPLANATIONS
    # =====================================================

    reasons = []


    # Growth
    if growth_rate >= 15:

        reasons.append(
            "Search interest is rising quickly."
        )

    elif growth_rate >= 3:

        reasons.append(
            "Search interest is still growing."
        )

    elif growth_rate > -5:

        reasons.append(
            "Search interest has started to slow down."
        )

    else:

        reasons.append(
            "Search interest is declining."
        )


    # Peak
    if distance_from_peak >= 35:

        reasons.append(
            "Interest has dropped far below its recent peak."
        )

    elif distance_from_peak <= 10:

        reasons.append(
            "Interest is still close to its recent peak."
        )


    # Momentum
    if momentum > 3:

        reasons.append(
            "Recent momentum is becoming stronger."
        )

    elif momentum < -3:

        reasons.append(
            "Recent momentum is weakening."
        )


    # Status explanation
    if trend_status == "Too Crowded":

        reasons.append(
            "Interest is already very high but growth is slowing."
        )


    # Only display max 3 reasons
    reasons = reasons[:3]


    # =====================================================
    # RESULT
    # =====================================================

    return {

        "trend": trend_name,

        "category":
            trend_df.iloc[0]["category"],

        "trend_status":
            trend_status,

        "growth_rate":
            round(growth_rate, 1),

        "growth_speed":
            growth_speed,

        "death_risk":
            death_risk,

        "worth_score":
            worth_score,

        "recommendation":
            recommendation,

        "reasons":
            reasons,

        # useful for graph / debugging

        "current_interest":
            round(current_interest, 1),

        "peak_interest":
            round(peak_interest, 1),

        "recent_average":
            round(recent_average, 1),

        "distance_from_peak":
            round(distance_from_peak, 1),

        "history": [
            {
                "date": str(row["date"]),
                "interest": float(row["search_interest"])
            }
            for _, row in trend_df.iterrows()
        ]

    }


# =========================================================
# TERMINAL TEST
# =========================================================

if __name__ == "__main__":

    trend = input(
        "Enter trend name: "
    )

    result = analyze_trend(trend)

    print("\n")

    print("=" * 55)
    print("LARPER TREND ANALYSIS")
    print("=" * 55)


    if "error" in result:

        print(result["error"])


    else:

        print(
            f"\nTrend: "
            f"{result['trend']}"
        )

        print(
            f"Category: "
            f"{result['category']}"
        )


        print("\nTREND STATUS")
        print(
            result["trend_status"]
        )


        print("\nHOW FAST IS IT GROWING?")

        print(
            f"{result['growth_rate']}% "
            f"({result['growth_speed']})"
        )


        print("\nCHANCE IT WILL DIE SOON")

        print(
            f"{result['death_risk']}%"
        )


        print("\nWORTH JOINING")

        print(
            f"{result['worth_score']}/100"
        )


        print("\nRECOMMENDATION")

        print(
            result["recommendation"]
        )


        print("\nWHY?")

        for reason in result["reasons"]:

            print(
                f"- {reason}"
            )