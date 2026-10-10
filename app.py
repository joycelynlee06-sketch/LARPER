from flask import Flask, render_template, request
import pandas as pd
from pathlib import Path

from predictor import analyze_trend


# =========================================================
# APP
# =========================================================

app = Flask(__name__)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = (
        BASE_DIR
        / "data"
        / "LARPER_template.xlsx"
)


# =========================================================
# LOAD SOCIAL DATA FOR DROPDOWNS
# =========================================================

def load_social_data():

    df = pd.read_excel(
        DATA_FILE,
        sheet_name="Social Metrics"
    )

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
    )

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

    return df


# =========================================================
# CATEGORY LIST
# =========================================================

def get_categories():

    df = load_social_data()

    categories = (
        df["category"]
        .dropna()
        .unique()
        .tolist()
    )

    return sorted(
        categories
    )


# =========================================================
# TREND OPTIONS BY CATEGORY
# =========================================================

def get_trend_options():

    df = load_social_data()

    options = {}

    for category in (
            df["category"]
                    .dropna()
                    .unique()
    ):

        trends = (
            df[
                df["category"]
                == category
                ]["trend_name"]
            .dropna()
            .unique()
            .tolist()
        )

        options[category] = sorted(
            trends
        )

    return options


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# CHECK TREND PAGE
# =========================================================

@app.route(
    "/check",
    methods=[
        "GET",
        "POST"
    ]
)
def check():

    categories = get_categories()

    trend_options = (
        get_trend_options()
    )


    if request.method == "POST":

        trend = request.form.get(
            "trend",
            ""
        ).strip()

        purpose = request.form.get(
            "purpose",
            ""
        ).strip()


        # ---------------------------------------------
        # VALIDATION
        # ---------------------------------------------

        if trend == "":

            return render_template(
                "check.html",
                categories=categories,
                trend_options=trend_options,
                error="Please select a trend."
            )


        if purpose == "":

            return render_template(
                "check.html",
                categories=categories,
                trend_options=trend_options,
                error="Please choose what you want to use the trend for."
            )


        # ---------------------------------------------
        # RUN PREDICTOR
        # ---------------------------------------------

        result = analyze_trend(
            trend
        )


        if "error" in result:

            return render_template(
                "check.html",
                categories=categories,
                trend_options=trend_options,
                error=result["error"]
            )


        # Add purpose to result
        result["purpose"] = purpose


        return render_template(
            "result.html",
            result=result
        )


    return render_template(
        "check.html",
        categories=categories,
        trend_options=trend_options
    )


# =========================================================
# COLLECTION PAGE
# =========================================================

@app.route("/collection")
def collection():

    return render_template(
        "collection.html"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )