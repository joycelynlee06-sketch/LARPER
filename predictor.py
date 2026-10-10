
import pandas as pd
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "larper_master.csv"
COLLECTION_FILE = BASE_DIR / "my_collection.json"


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

    recent = values[-3:]
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
                                     (peak_value - current_value) / peak_value
                             ) * 100

    # =====================================================
    # MOMENTUM
    # =====================================================

    last_change = values[-1] - values[-2]
    previous_change = values[-2] - values[-3]
    momentum = last_change - previous_change

    # =====================================================
    # TREND STATUS
    # =====================================================

    if growth_rate <= -10:
        status = "Losing Popularity"

    elif current_value >= 80 and growth_rate >= 0:
        status = "Too Crowded"

    elif current_value >= 70:
        status = "Very Popular Now"

    elif growth_rate >= 15:
        status = "Growing Fast"

    else:
        status = "Starting"

    # =====================================================
    # PREDICTION
    # =====================================================

    if growth_rate >= 15 and momentum >= 0:
        prediction = "Likely to Keep Growing"

    elif growth_rate >= 5:
        prediction = "Still Growing, But Watch Closely"

    elif growth_rate < 0 and distance_from_peak >= 20:
        prediction = "Likely to Lose Popularity"

    elif growth_rate <= -20:
        prediction = "Likely to Keep Declining"

    else:
        prediction = "Likely to Stay Stable"

    # =====================================================
    # CHANCE IT WILL DIE SOON
    # =====================================================

    if growth_rate <= -20 and distance_from_peak >= 30:
        fading_risk = "High"

    elif growth_rate < 0 or distance_from_peak >= 30:
        fading_risk = "Medium"

    else:
        fading_risk = "Low"

    # =====================================================
    # RECOMMENDATION TAG
    # =====================================================

    if status == "Losing Popularity" or fading_risk == "High":
        recommendation = "SKIP"

    elif status == "Too Crowded":
        recommendation = "TRY SOMETHING SIMILAR"

    elif status == "Growing Fast" and fading_risk == "Low":
        recommendation = "JOIN NOW"

    elif status == "Starting" and fading_risk == "Low":
        recommendation = "JOIN NOW"

    elif status == "Very Popular Now" and fading_risk != "High":
        recommendation = "TRY SOMETHING SIMILAR"

    else:
        recommendation = "TRY SOMETHING SIMILAR"

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
        reasons.append("Recent momentum is improving.")

    elif momentum < 0:
        reasons.append("Recent momentum is slowing down.")

    # =====================================================
    # RETURN RESULTS
    # =====================================================

    return {
        "trend": trend_name,
        "category": trend_df.iloc[0]["category"],
        "current_interest": round(current_value, 1),
        "peak_interest": round(peak_value, 1),
        "growth_rate": round(growth_rate, 1),
        "status": status,
        "prediction": prediction,
        "fading_risk": fading_risk,
        "recommendation": recommendation,
        "reasons": reasons
    }


# =====================================================
# STAR / SAVE FAVORITE TREND
# =====================================================

def load_collection():
    if not COLLECTION_FILE.exists():
        return []

    try:
        with open(COLLECTION_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


def star_trend(result):
    collection = load_collection()

    for item in collection:
        if item["trend"].lower() == result["trend"].lower():
            print(f"\n⭐ {result['trend']} is already in your collection.")
            return

    collection.append({
        "trend": result["trend"],
        "category": str(result["category"]),
        "status": result["status"],
        "growth_rate": result["growth_rate"],
        "recommendation": result["recommendation"]
    })

    with open(COLLECTION_FILE, "w", encoding="utf-8") as file:
        json.dump(collection, file, indent=4, ensure_ascii=False)

    print(f"\n⭐ {result['trend']} added to your collection!")


# =====================================================
# VIEW STARRED TRENDS
# =====================================================

def view_collection():
    collection = load_collection()

    print("\n" + "=" * 50)
    print("MY FAVORITE TRENDS ⭐")
    print("=" * 50)

    if not collection:
        print("You haven't starred any trends yet.")
        return

    for item in collection:
        print(f"\n⭐ {item['trend']}")
        print(f"Category: {item['category']}")
        print(f"Trend Status: {item['status']}")
        print(f"Growth Rate: {item['growth_rate']:+.1f}%")
        print(f"Recommendation: {item['recommendation']}")


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":

    trend = input("Enter a trend name: ")

    result = analyze_trend(trend)

    print("\n")
    print("=" * 50)
    print("LARPER TREND ANALYSIS")
    print("=" * 50)

    if "error" in result:
        print(result["error"])

    else:
        print(f"\nTrend: {result['trend']}")

        print("\nTREND STATUS")
        print(result["status"])

        print("\nHOW FAST IS IT GROWING?")
        print(f"{result['growth_rate']:+.1f}% change")

        print("\nCHANCE IT WILL DIE SOON?")
        print(result["fading_risk"])

        print("\nWORTH JOINING?")
        print(result["recommendation"])

        print("\nWHY?")
        for reason in result["reasons"]:
            print(f"- {reason}")

        # Star this trend
        choice = input("\n⭐ Add this trend to your favorites? (y/n): ")

        if choice.lower() == "y":
            star_trend(result)

    # View collection
    choice = input("\nView your favorite trends? (y/n): ")

    if choice.lower() == "y":
        view_collection()
