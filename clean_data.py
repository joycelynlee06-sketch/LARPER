import pandas as pd
from pathlib import Path


# =========================================================
# 1. PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


# =========================================================
# 2. FILES + CATEGORIES
# =========================================================

FILES = {
    "food/food_local.csv": "Food",
    "food/food_dessert.csv": "Food",
    "food/food_Japanese.csv": "Food",

    "entertainment/gaming.csv": "Entertainment",
    "entertainment/podcast.csv": "Entertainment",
    "entertainment/socialmedia.csv": "Entertainment",

    "growth/personaldevelopment.csv": "Growth",

    "handcraft/handcraft.csv": "Handcraft",

    "lifestyle/lifestyle.csv": "Lifestyle",
}


# =========================================================
# 3. MANUAL NAME FIXES
# =========================================================

NAME_FIXES = {
    "Pubg Mobile": "PUBG Mobile",
    "Tiktok": "TikTok",
    "Mobile Legends: Bang Bang": "Mobile Legends",
    "Xiaohongshu": "Xiaohongshu",
    "Dubai Chocolate": "Dubai Chocolate",
    "Nasi Lemak": "Nasi Lemak",
    "Ayam Gepuk": "Ayam Gepuk",
    "Ghost Story": "Ghost Story",
    "Fuse Beads": "Fuse Beads",
}


# =========================================================
# 4. CLEAN ONE FILE
# =========================================================

def clean_one_file(file_path, category):
    print(f"\nCleaning: {file_path.name}")

    # Read CSV
    df = pd.read_csv(file_path)

    # Clean column names
    df.columns = df.columns.str.strip()

    # Check that Time exists
    if "Time" not in df.columns:
        raise ValueError(
            f"'Time' column not found in {file_path}"
        )

    # Convert Time to proper datetime
    df["Time"] = pd.to_datetime(
        df["Time"],
        errors="coerce",
        utc=True
    )

    # Convert from wide format:
    #
    # Time | Matcha | Tanghulu | ...
    #
    # into long format:
    #
    # Time | trend_name | search_interest
    #
    df = df.melt(
        id_vars=["Time"],
        var_name="trend_name",
        value_name="search_interest"
    )

    # Add category
    df["category"] = category

    # Clean trend names
    df["trend_name"] = (
        df["trend_name"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    # Fix specific names
    df["trend_name"] = df["trend_name"].replace(NAME_FIXES)

    # Convert search interest to number
    df["search_interest"] = pd.to_numeric(
        df["search_interest"],
        errors="coerce"
    )

    # Remove rows with missing values
    df = df.dropna(
        subset=[
            "Time",
            "trend_name",
            "search_interest"
        ]
    )

    # Google Trends values should normally be 0–100
    df = df[
        (df["search_interest"] >= 0)
        &
        (df["search_interest"] <= 100)
        ]

    return df


# =========================================================
# 5. LOAD + CLEAN ALL FILES
# =========================================================

all_data = []

for relative_path, category in FILES.items():

    file_path = DATA_DIR / relative_path

    # Check if file exists
    if not file_path.exists():
        print(f"\nERROR: File not found:")
        print(file_path)
        print("\nCheck the spelling and folder location.")
        continue

    cleaned_df = clean_one_file(
        file_path,
        category
    )

    all_data.append(cleaned_df)


# =========================================================
# 6. MAKE SURE WE FOUND DATA
# =========================================================

if len(all_data) == 0:
    raise FileNotFoundError(
        "\nNo CSV files were found.\n"
        "Please check your data folder structure."
    )


# =========================================================
# 7. COMBINE ALL FILES
# =========================================================

master = pd.concat(
    all_data,
    ignore_index=True
)


# =========================================================
# 8. REMOVE DUPLICATES
# =========================================================

master = master.drop_duplicates(
    subset=[
        "Time",
        "trend_name",
        "category"
    ]
)


# =========================================================
# 9. RENAME COLUMNS
# =========================================================

master = master.rename(
    columns={
        "Time": "date"
    }
)


# =========================================================
# 10. SORT DATA
# =========================================================

master = master.sort_values(
    by=[
        "category",
        "trend_name",
        "date"
    ]
)


# =========================================================
# 11. RESET INDEX
# =========================================================

master = master.reset_index(
    drop=True
)


# =========================================================
# 12. COLUMN ORDER
# =========================================================

master = master[
    [
        "date",
        "trend_name",
        "category",
        "search_interest"
    ]
]


# =========================================================
# 13. SAVE MASTER DATASET
# =========================================================

OUTPUT_FILE = DATA_DIR / "larper_master.csv"

master.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# 14. PRINT SUMMARY
# =========================================================

print("\n")
print("=" * 60)
print("LARPER DATA CLEANING COMPLETE")
print("=" * 60)

print(f"\nSaved master dataset to:")
print(OUTPUT_FILE)

print("\nDataset size:")
print(f"{master.shape[0]} rows")
print(f"{master.shape[1]} columns")

print("\nCategories:")
for category in master["category"].unique():
    print(f"- {category}")

print("\nAvailable trends:")

for category in master["category"].unique():

    print(f"\n{category}:")

    category_trends = (
        master[
            master["category"] == category
            ]["trend_name"]
        .unique()
    )

    for trend in category_trends:
        print(f"  - {trend}")


print("\nFirst 10 rows:")

print(
    master.head(10).to_string(
        index=False
    )
)


print("\nMissing values:")
print(master.isnull().sum())


print("\nSearch interest range:")

print(
    f"Minimum: {master['search_interest'].min()}"
)

print(
    f"Maximum: {master['search_interest'].max()}"
)


print("\nDONE ✅")