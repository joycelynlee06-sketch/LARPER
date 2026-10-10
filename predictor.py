import pandas as pd
from pathlib import Path
import re


# =========================================================
# FILE PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = (
        BASE_DIR
        / "data"
        / "LARPER_template.xlsx"
)


# =========================================================
# BASIC HELPER
# =========================================================

def clamp(value, minimum=0, maximum=100):
    return max(
        minimum,
        min(value, maximum)
    )


# =========================================================
# CONVERT VALUES LIKE:
# 1.5M
# 407.8K
# 13.4k
# INTO REAL NUMBERS
# =========================================================

def parse_number(value):

    if pd.isna(value):
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value)

    text = (
        text
        .strip()
        .upper()
        .replace(",", "")
        .replace(" ", "")
    )

    if text == "":
        return 0.0

    # Fix values such as 524.K
    text = text.replace(".K", "K")
    text = text.replace(".M", "M")
    text = text.replace(".B", "B")

    match = re.match(
        r"^([0-9]*\.?[0-9]+)([KMB]?)$",
        text
    )

    if not match:
        return 0.0

    number = float(
        match.group(1)
    )

    suffix = match.group(2)

    multipliers = {
        "": 1,
        "K": 1_000,
        "M": 1_000_000,
        "B": 1_000_000_000
    }

    return (
            number
            * multipliers[suffix]
    )


# =========================================================
# LOAD SOCIAL DATA
# =========================================================

def load_social_data():

    if not DATA_FILE.exists():

        raise FileNotFoundError(
            f"\nCannot find:\n{DATA_FILE}\n\n"
            "Put LARPER_template.xlsx inside the data folder."
        )

    df = pd.read_excel(
        DATA_FILE,
        sheet_name="Social Metrics"
    )

    # Clean column names
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
    )

    required_columns = [
        "trend_name",
        "category",
        "views",
        "likes",
        "comments",
        "shares"
    ]

    for column in required_columns:

        if column not in df.columns:

            raise ValueError(
                f"Missing column: {column}"
            )

    # -----------------------------------------------------
    # CLEAN TEXT
    # -----------------------------------------------------

    df["trend_name"] = (
        df["trend_name"]
        .astype(str)
        .str.strip()
    )

    df["category"] = (
        df["category"]
        .astype(str)
        .str.strip()
    )

    # -----------------------------------------------------
    # CONVERT SOCIAL NUMBERS
    # -----------------------------------------------------

    metric_columns = [
        "views",
        "likes",
        "comments",
        "shares"
    ]

    for column in metric_columns:

        df[column] = (
            df[column]
            .apply(parse_number)
        )

    # -----------------------------------------------------
    # CONVERT DATE
    # -----------------------------------------------------

    if "date" in df.columns:

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce",
            utc=True
        )

    else:

        df["date"] = pd.NaT

    # -----------------------------------------------------
    # RECALCULATE RATES
    # -----------------------------------------------------

    safe_views = (
        df["views"]
        .replace(0, pd.NA)
    )

    df["engagement_rate"] = (
            (
                    df["likes"]
                    + df["comments"]
                    + df["shares"]
            )
            / safe_views
            * 100
    ).fillna(0)

    df["like_rate"] = (
            df["likes"]
            / safe_views
            * 100
    ).fillna(0)

    df["comment_rate"] = (
            df["comments"]
            / safe_views
            * 100
    ).fillna(0)

    df["share_rate"] = (
            df["shares"]
            / safe_views
            * 100
    ).fillna(0)

    # -----------------------------------------------------
    # CALCULATE AGE + VIEWS PER DAY
    # -----------------------------------------------------

    now = pd.Timestamp.now(
        tz="UTC"
    )

    def calculate_age(date):

        if pd.isna(date):
            return 1.0

        age = (
                      now - date
              ).total_seconds() / 86400

        return max(
            age,
            1.0
        )

    df["age_days"] = (
        df["date"]
        .apply(calculate_age)
    )

    df["views_per_day"] = (
            df["views"]
            / df["age_days"]
    )

    return df


# =========================================================
# BUILD BENCHMARKS
# =========================================================

def build_benchmarks(df):

    benchmark = (
        df[
            df["views"] > 0
            ]
        .groupby(
            [
                "trend_name",
                "category"
            ],
            as_index=False
        )
        .agg(
            avg_views_per_day=(
                "views_per_day",
                "mean"
            ),

            avg_engagement=(
                "engagement_rate",
                "mean"
            ),

            total_views=(
                "views",
                "sum"
            )
        )
    )

    return benchmark


# =========================================================
# ANALYZE ONE TREND
# =========================================================

def analyze_trend(trend_name):

    # FIX EXTRA SPACES
    trend_name = (
        str(trend_name)
        .strip()
    )

    df = load_social_data()

    # -----------------------------------------------------
    # MATCH TREND
    # ignores uppercase/lowercase + extra spaces
    # -----------------------------------------------------

    trend_df = df[
        df["trend_name"]
        .str.strip()
        .str.lower()
        ==
        trend_name.lower()
        ].copy()

    if trend_df.empty:

        return {
            "error":
                f"Trend '{trend_name}' was not found."
        }

    # Remove rows with no actual metrics
    trend_df = trend_df[
        trend_df["views"] > 0
        ].copy()

    if trend_df.empty:

        return {
            "error":
                f"'{trend_name}' does not have social metrics yet."
        }

    # Use official stored trend spelling
    official_trend_name = (
        trend_df.iloc[0]["trend_name"]
    )

    category = (
        trend_df.iloc[0]["category"]
    )

    # =====================================================
    # SORT
    # =====================================================

    if trend_df["date"].notna().sum() >= 2:

        trend_df = (
            trend_df
            .sort_values("date")
            .reset_index(drop=True)
        )

    else:

        trend_df = (
            trend_df
            .reset_index(drop=True)
        )

    # =====================================================
    # TOTAL SOCIAL METRICS
    # =====================================================

    total_views = (
        trend_df["views"].sum()
    )

    total_likes = (
        trend_df["likes"].sum()
    )

    total_comments = (
        trend_df["comments"].sum()
    )

    total_shares = (
        trend_df["shares"].sum()
    )

    average_engagement = (
        trend_df[
            "engagement_rate"
        ].mean()
    )

    average_share_rate = (
        trend_df[
            "share_rate"
        ].mean()
    )

    average_views_per_day = (
        trend_df[
            "views_per_day"
        ].mean()
    )

    # =====================================================
    # RECENT VS OLDER CONTENT
    # =====================================================

    number_of_posts = len(
        trend_df
    )

    if number_of_posts >= 2:

        split_point = max(
            1,
            number_of_posts // 2
        )

        older = trend_df.iloc[
            :split_point
        ]

        recent = trend_df.iloc[
            split_point:
        ]

        older_velocity = (
            older[
                "views_per_day"
            ].mean()
        )

        recent_velocity = (
            recent[
                "views_per_day"
            ].mean()
        )

        older_engagement = (
            older[
                "engagement_rate"
            ].mean()
        )

        recent_engagement = (
            recent[
                "engagement_rate"
            ].mean()
        )

        # -------------------------------------------------
        # GROWTH RATE
        # -------------------------------------------------

        if older_velocity > 0:

            growth_rate = (
                    (
                            recent_velocity
                            - older_velocity
                    )
                    / older_velocity
                    * 100
            )

        else:

            growth_rate = 0

        # -------------------------------------------------
        # ENGAGEMENT CHANGE
        # -------------------------------------------------

        if older_engagement > 0:

            engagement_change = (
                    (
                            recent_engagement
                            - older_engagement
                    )
                    / older_engagement
                    * 100
            )

        else:

            engagement_change = 0

    else:

        growth_rate = 0
        engagement_change = 0

    growth_rate = clamp(
        growth_rate,
        -100,
        200
    )

    engagement_change = clamp(
        engagement_change,
        -100,
        200
    )

    # =====================================================
    # BENCHMARK AGAINST OTHER TRENDS
    # =====================================================

    benchmarks = build_benchmarks(
        df
    )

    category_benchmarks = (
        benchmarks[
            benchmarks["category"]
            == category
            ]
    )

    if len(category_benchmarks) < 3:

        comparison = benchmarks

    else:

        comparison = (
            category_benchmarks
        )

    if comparison.empty:

        velocity_percentile = 50
        engagement_percentile = 50

    else:

        velocity_percentile = (
                (
                        comparison[
                            "avg_views_per_day"
                        ]
                        <= average_views_per_day
                ).mean()
                * 100
        )

        engagement_percentile = (
                (
                        comparison[
                            "avg_engagement"
                        ]
                        <= average_engagement
                ).mean()
                * 100
        )

    # =====================================================
    # HOW FAST IS IT GROWING?
    # =====================================================

    if growth_rate >= 50:

        growth_speed = (
            "Very Fast"
        )

    elif growth_rate >= 20:

        growth_speed = (
            "Fast"
        )

    elif growth_rate >= 5:

        growth_speed = (
            "Steady"
        )

    elif growth_rate > -5:

        growth_speed = (
            "Slow"
        )

    else:

        growth_speed = (
            "Declining"
        )

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
            growth_rate <= -25
            or (
            growth_rate <= -10
            and engagement_change <= -15
    )
    ):

        trend_status = (
            "Losing Popularity"
        )

    elif (
            velocity_percentile >= 70
            and growth_rate <= 5
            and engagement_change < 0
    ):

        trend_status = (
            "Too Crowded"
        )

    elif (
            velocity_percentile >= 70
            and engagement_percentile >= 50
    ):

        trend_status = (
            "Very Popular"
        )

    elif growth_rate >= 20:

        trend_status = (
            "Growing Fast"
        )

    else:

        trend_status = (
            "Just Starting"
        )

    # =====================================================
    # CHANCE IT WILL DIE SOON
    # =====================================================

    death_risk = 25

    if growth_rate < 0:

        death_risk += min(
            abs(growth_rate) * 0.45,
            35
        )

    else:

        death_risk -= min(
            growth_rate * 0.15,
            15
        )

    if engagement_change < 0:

        death_risk += min(
            abs(engagement_change)
            * 0.25,
            20
        )

    if (
            trend_status
            == "Too Crowded"
    ):

        death_risk += 15

    elif (
            trend_status
            == "Losing Popularity"
    ):

        death_risk += 25

    elif (
            trend_status
            == "Growing Fast"
    ):

        death_risk -= 8

    if average_share_rate >= 3:

        death_risk -= 5

    death_risk = int(
        round(
            clamp(
                death_risk
            )
        )
    )

    # =====================================================
    # WORTH JOINING
    # =====================================================

    worth_score = 50

    worth_score += clamp(
        growth_rate * 0.30,
        -25,
        25
    )

    worth_score += (
            (
                    engagement_percentile
                    - 50
            )
            * 0.20
    )

    worth_score += (
            (
                    velocity_percentile
                    - 50
            )
            * 0.15
    )

    if (
            trend_status
            == "Just Starting"
    ):

        worth_score += 10

    elif (
            trend_status
            == "Growing Fast"
    ):

        worth_score += 18

    elif (
            trend_status
            == "Very Popular"
    ):

        worth_score += 7

    elif (
            trend_status
            == "Too Crowded"
    ):

        worth_score -= 18

    elif (
            trend_status
            == "Losing Popularity"
    ):

        worth_score -= 30

    worth_score -= (
            death_risk
            * 0.25
    )

    worth_score = int(
        round(
            clamp(
                worth_score
            )
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

        recommendation = (
            "JOIN NOW"
        )

    elif (
            worth_score >= 35
            and death_risk < 75
    ):

        recommendation = (
            "TRY SOMETHING SIMILAR"
        )

    else:

        recommendation = (
            "SKIP"
        )

    # =====================================================
    # EXPLANATION
    # =====================================================

    reasons = []

    if growth_rate >= 20:

        reasons.append(
            "Recent content is gaining views faster than older content."
        )

    elif growth_rate >= 5:

        reasons.append(
            "Recent content is still gaining momentum."
        )

    elif growth_rate > -5:

        reasons.append(
            "View momentum is mostly stable."
        )

    else:

        reasons.append(
            "Recent content is gaining views more slowly."
        )

    if engagement_change >= 15:

        reasons.append(
            "Likes, comments and shares are becoming stronger."
        )

    elif engagement_change <= -15:

        reasons.append(
            "Audience engagement is weakening."
        )

    else:

        reasons.append(
            "Audience engagement remains relatively stable."
        )

    if velocity_percentile >= 70:

        reasons.append(
            "This trend is attracting strong attention compared with similar trends."
        )

    elif velocity_percentile <= 30:

        reasons.append(
            "The trend still has relatively low reach, which may mean it is still early."
        )

    if (
            trend_status
            == "Too Crowded"
    ):

        reasons.append(
            "Attention is already high while growth is slowing, suggesting saturation."
        )

    reasons = reasons[:3]

    # =====================================================
    # REFERENCE POSTS
    # =====================================================

    references = []

    for _, row in (
            trend_df.iterrows()
    ):

        platform = row.get(
            "platform",
            ""
        )

        content_title = row.get(
            "content_title",
            ""
        )

        content_url = row.get(
            "content_url",
            ""
        )

        thumbnail_url = row.get(
            "thumbnail_url",
            ""
        )

        # clean NaN text
        platform = (
            ""
            if pd.isna(platform)
            else str(platform)
        )

        content_title = (
            ""
            if pd.isna(content_title)
            else str(content_title)
        )

        content_url = (
            ""
            if pd.isna(content_url)
            else str(content_url)
        )

        thumbnail_url = (
            ""
            if pd.isna(thumbnail_url)
            else str(thumbnail_url)
        )

        reference = {

            "platform":
                platform,

            "content_title":
                content_title,

            "content_url":
                content_url,

            "thumbnail_url":
                thumbnail_url,

            "views":
                int(
                    row["views"]
                ),

            "likes":
                int(
                    row["likes"]
                ),

            "comments":
                int(
                    row["comments"]
                ),

            "shares":
                int(
                    row["shares"]
                ),

            "engagement_rate":
                round(
                    row[
                        "engagement_rate"
                    ],
                    2
                )

        }

        references.append(
            reference
        )

    # =====================================================
    # FINAL RESULT
    # =====================================================

    return {

        "trend":
            official_trend_name,

        "category":
            category,

        "trend_status":
            trend_status,

        "growth_rate":
            round(
                growth_rate,
                1
            ),

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

        "total_views":
            int(
                total_views
            ),

        "total_likes":
            int(
                total_likes
            ),

        "total_comments":
            int(
                total_comments
            ),

        "total_shares":
            int(
                total_shares
            ),

        "engagement_rate":
            round(
                average_engagement,
                2
            ),

        "share_rate":
            round(
                average_share_rate,
                2
            ),

        "references":
            references

    }


# =========================================================
# AVAILABLE TRENDS
# =========================================================

def get_available_trends():

    df = load_social_data()

    trends = (
        df[
            df["views"] > 0
            ]["trend_name"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    return sorted(
        trends
    )


# =========================================================
# TERMINAL TEST
# =========================================================

if __name__ == "__main__":

    available = (
        get_available_trends()
    )

    print("\n")
    print("=" * 60)
    print("LARPER SOCIAL TREND PREDICTOR")
    print("=" * 60)

    print(
        "\nAvailable trends:\n"
    )

    for number, trend in enumerate(
            available,
            start=1
    ):

        print(
            f"{number}. {trend}"
        )

    print("\n")

    # IMPORTANT FIX HERE:
    # removes spaces automatically
    choice = input(
        "Enter a trend name: "
    ).strip()

    result = analyze_trend(
        choice
    )

    print("\n")
    print("=" * 60)
    print("LARPER RESULT")
    print("=" * 60)

    if "error" in result:

        print(
            result["error"]
        )

    else:

        print(
            f"\nTrend: "
            f"{result['trend']}"
        )

        print(
            f"Category: "
            f"{result['category']}"
        )

        print(
            "\nTREND STATUS"
        )

        print(
            result[
                "trend_status"
            ]
        )

        print(
            "\nHOW FAST IS IT GROWING?"
        )

        print(
            f"{result['growth_rate']}% "
            f"({result['growth_speed']})"
        )

        print(
            "\nCHANCE IT WILL DIE SOON"
        )

        print(
            f"{result['death_risk']}%"
        )

        print(
            "\nWORTH JOINING"
        )

        print(
            f"{result['worth_score']}/100"
        )

        print(
            "\nRECOMMENDATION"
        )

        print(
            result[
                "recommendation"
            ]
        )

        print(
            "\nSOCIAL SIGNALS"
        )

        print(
            f"Views: "
            f"{result['total_views']:,}"
        )

        print(
            f"Likes: "
            f"{result['total_likes']:,}"
        )

        print(
            f"Comments: "
            f"{result['total_comments']:,}"
        )

        print(
            f"Shares: "
            f"{result['total_shares']:,}"
        )

        print(
            f"Average engagement: "
            f"{result['engagement_rate']}%"
        )

        print(
            "\nWHY?"
        )

        for reason in (
                result["reasons"]
        ):

            print(
                f"- {reason}"
            )

        print(
            "\nREFERENCE POSTS:"
        )

        for reference in (
                result["references"]
        ):

            print(
                f"- "
                f"{reference['content_title']} "
                f"({reference['platform']})"
            )