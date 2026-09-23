# Bellabeat Smart Device Usage Analysis

A Streamlit app for the Bellabeat / Fitbit case study: cleans the Fitbit
dataset in SQL (SQLite), runs the analysis, and presents a dashboard and
marketing recommendations.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Structure

```
app.py                        Overview page (business task, stakeholders)
pages/
  1_Data_and_Cleaning.py      Data sources, limitations, cleaning steps (with SQL)
  2_SQL_Analysis.py           Every analysis query, its result, and a takeaway
  3_Dashboard.py              Charts and key findings
  4_Recommendations.py        Marketing recommendations tied to findings
src/
  db.py                       Loads the CSVs into SQLite and runs 01_clean.sql
  analysis.py                 Named analysis queries (used by pages 2 and 3)
  common.py                   Cached DB connection, cached query runner, chart styling
sql/
  01_clean.sql                Cleaning script (dates, dedup, joins, flags)
  02_analysis.sql             Reference copy of every analysis query
eda/
  bellabeat_eda.py            Standalone pandas EDA (no SQL) — data-quality
                               inventory, descriptive stats, the same
                               groupings as 02_analysis.sql, and saved charts
  figures/                    PNG charts written by bellabeat_eda.py
data/                         The six Fitbit CSVs the app uses
```

## Run the standalone EDA

```bash
cd bellabeat_app
python eda/bellabeat_eda.py
```

This is independent of the Streamlit app's SQLite pipeline — it loads and
cleans the CSVs directly in pandas, prints a data-quality inventory and
descriptive statistics, reproduces every grouping in `sql/02_analysis.sql`
as a pandas cross-check, and saves five charts to `eda/figures/`.

## Data

`FitBit Fitness Tracker Data` (Kaggle, CC0, via user Mobius) — 30+ users,
minute-level Fitbit exports collected 03.12.2016-05.12.2016. This app uses:
`dailyActivity_merged.csv`, `sleepDay_merged.csv`, `hourlySteps_merged.csv`,
`hourlyCalories_merged.csv`, `hourlyIntensities_merged.csv`,
`weightLogInfo_merged.csv`.

## Notes

- The SQLite database is built in memory each time the app starts
  (`src/db.py`), so there's nothing to migrate — just drop in updated CSVs.
- Charts are Matplotlib/Seaborn, embedded directly in the Streamlit pages.
- Swap `PRODUCT` in `src/common.py` if you want the recommendations page to
  focus on a different Bellabeat product (e.g. Time, Spring, membership app).
