from flask import Flask, render_template, request
import pandas as pd
from pathlib import Path

from predictor import analyze_trend


app = Flask(__name__)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = (
        BASE_DIR
        / "data"
        / "larper_master.csv"
)


# =========================================================
# LOAD OPTIONS
# =========================================================

def get_categories():

    df = pd.read_csv(DATA_FILE)

    return sorted(
        df["category"]
        .dropna()
        .unique()
        .tolist()
    )


def get_trends():

    df = pd.read_csv(DATA_FILE)

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

        options[category] = sorted(trends)

    return options


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# CHECK TREND
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
    trend_options = get_trends()


    if request.method == "POST":

        trend = request.form.get(
            "trend"
        )

        if not trend:

            return render_template(

                "check.html",

                categories=categories,

                trend_options=trend_options,

                error="Please select a trend."
            )


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
# START
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )