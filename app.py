"""
Bellabeat Smart Device Usage Analysis — single-file Streamlit app.

Deliberately built as ONE file with no src/ or pages/ subfolders, and it
expects the six Fitbit CSVs to sit in the SAME folder as this script
(no data/ subfolder either). This makes the whole app immune to the
"folder structure didn't survive the GitHub upload" problem — every
file involved is flat, so there is nothing for an upload tool to
flatten incorrectly.

To deploy: upload this file, requirements.txt, and the six CSVs, all
loose, into the same GitHub repo. Set Streamlit Cloud's main file path
to app.py. That's it — no folders required anywhere.
"""
from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------
st.set_page_config(page_title="Bellabeat Analysis", page_icon="🌿", layout="wide")

ROOT = Path(__file__).resolve().parent  # CSVs live right next to this script
PRODUCT = "Bellabeat Leaf"
NAVY, TEAL, ORANGE = "#1F3A5F", "#2A7F8E", "#E07A34"

sns.set_theme(style="whitegrid", rc={
    "axes.edgecolor": "#CBD5DB", "axes.titleweight": "bold", "font.size": 10,
})

RAW_FILES = {
    "raw_daily_activity": "dailyActivity_merged.csv",
    "raw_sleep_day": "sleepDay_merged.csv",
    "raw_hourly_steps": "hourlySteps_merged.csv",
    "raw_hourly_calories": "hourlyCalories_merged.csv",
    "raw_hourly_intensities": "hourlyIntensities_merged.csv",
    "raw_weight_log": "weightLogInfo_merged.csv",
}

CLEAN_SQL = """
DROP TABLE IF EXISTS daily_activity;
DROP TABLE IF EXISTS sleep_day;
DROP TABLE IF EXISTS hourly_activity;
DROP TABLE IF EXISTS weight_log;

CREATE TABLE daily_activity AS
WITH split AS (
    SELECT DISTINCT *,
           substr(ActivityDate, 1, instr(ActivityDate, '/') - 1) AS m,
           substr(ActivityDate, instr(ActivityDate, '/') + 1)    AS rest
    FROM raw_daily_activity
), split2 AS (
    SELECT *,
           substr(rest, 1, instr(rest, '/') - 1) AS d,
           substr(rest, instr(rest, '/') + 1)    AS y
    FROM split
), iso AS (
    SELECT *, printf('%s-%02d-%02d', y, m, d) AS activity_date FROM split2
)
SELECT
    Id                                              AS user_id,
    activity_date,
    CAST(strftime('%w', activity_date) AS INTEGER)  AS weekday_num,
    CASE strftime('%w', activity_date)
         WHEN '0' THEN 'Sunday'    WHEN '1' THEN 'Monday'   WHEN '2' THEN 'Tuesday'
         WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'
         ELSE 'Saturday' END                        AS weekday,
    CASE WHEN strftime('%w', activity_date) IN ('0', '6')
         THEN 'Weekend' ELSE 'Weekday' END          AS day_type,
    TotalSteps                                      AS total_steps,
    TotalDistance                                   AS total_distance,
    VeryActiveMinutes                               AS very_active_min,
    FairlyActiveMinutes                             AS fairly_active_min,
    LightlyActiveMinutes                            AS lightly_active_min,
    SedentaryMinutes                                AS sedentary_min,
    Calories                                        AS calories,
    CASE WHEN TotalSteps > 0 THEN 1 ELSE 0 END      AS valid_day
FROM iso;

CREATE TABLE sleep_day AS
WITH dedup AS (
    SELECT DISTINCT Id, SleepDay, TotalSleepRecords, TotalMinutesAsleep, TotalTimeInBed
    FROM raw_sleep_day
), s1 AS (
    SELECT *, substr(SleepDay, 1, instr(SleepDay, ' ') - 1) AS dpart FROM dedup
), s2 AS (
    SELECT *, substr(dpart, 1, instr(dpart, '/') - 1) AS m,
              substr(dpart, instr(dpart, '/') + 1)    AS rest FROM s1
), s3 AS (
    SELECT *, substr(rest, 1, instr(rest, '/') - 1) AS d,
              substr(rest, instr(rest, '/') + 1)    AS y FROM s2
)
SELECT
    Id                                                    AS user_id,
    printf('%s-%02d-%02d', y, m, d)                       AS sleep_date,
    TotalMinutesAsleep                                    AS minutes_asleep,
    TotalTimeInBed                                        AS minutes_in_bed,
    ROUND(TotalMinutesAsleep / 60.0, 2)                   AS hours_asleep,
    ROUND(100.0 * TotalMinutesAsleep / TotalTimeInBed, 1) AS sleep_efficiency_pct
FROM s3;

CREATE TABLE hourly_activity AS
WITH joined AS (
    SELECT s.Id, s.ActivityHour, s.StepTotal, c.Calories,
           i.TotalIntensity, i.AverageIntensity
    FROM raw_hourly_steps s
    JOIN raw_hourly_calories    c ON c.Id = s.Id AND c.ActivityHour = s.ActivityHour
    JOIN raw_hourly_intensities i ON i.Id = s.Id AND i.ActivityHour = s.ActivityHour
), h1 AS (
    SELECT *, substr(ActivityHour, 1, instr(ActivityHour, ' ') - 1) AS dpart,
              substr(ActivityHour, instr(ActivityHour, ' ') + 1)    AS tpart
    FROM joined
), h2 AS (
    SELECT *, substr(dpart, 1, instr(dpart, '/') - 1)                  AS m,
              substr(dpart, instr(dpart, '/') + 1)                     AS rest,
              CAST(substr(tpart, 1, instr(tpart, ':') - 1) AS INTEGER) AS h12,
              substr(tpart, -2)                                        AS ampm
    FROM h1
), h3 AS (
    SELECT *, substr(rest, 1, instr(rest, '/') - 1) AS d,
              substr(rest, instr(rest, '/') + 1)    AS y
    FROM h2
)
SELECT
    Id                                                      AS user_id,
    printf('%s-%02d-%02d', y, m, d)                         AS activity_date,
    (h12 % 12) + CASE WHEN ampm = 'PM' THEN 12 ELSE 0 END   AS hour_of_day,
    StepTotal                                               AS steps,
    Calories                                                AS calories,
    TotalIntensity                                          AS total_intensity
FROM h3;

CREATE TABLE weight_log AS
WITH w1 AS (
    SELECT *, substr(Date, 1, instr(Date, ' ') - 1) AS dpart FROM raw_weight_log
), w2 AS (
    SELECT *, substr(dpart, 1, instr(dpart, '/') - 1) AS m,
              substr(dpart, instr(dpart, '/') + 1)    AS rest FROM w1
), w3 AS (
    SELECT *, substr(rest, 1, instr(rest, '/') - 1) AS d,
              substr(rest, instr(rest, '/') + 1)    AS y FROM w2
)
SELECT
    Id                                                  AS user_id,
    printf('%s-%02d-%02d', y, m, d)                     AS log_date,
    ROUND(WeightKg, 1)                                  AS weight_kg,
    ROUND(BMI, 1)                                       AS bmi
FROM w3;
"""


@st.cache_resource(show_spinner="Loading and cleaning the Fitbit data...")
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    for table, filename in RAW_FILES.items():
        df = pd.read_csv(ROOT / filename)
        if table == "raw_weight_log":
            df["IsManualReport"] = df["IsManualReport"].astype(str)
        df.to_sql(table, conn, if_exists="replace", index=False)
    conn.executescript(CLEAN_SQL)
    conn.commit()
    return conn


def q(sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, get_connection())


def new_fig(w=7, h=3.8):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    return fig, ax


# ---------------------------------------------------------------------
# Named queries (same as the multi-page version)
# ---------------------------------------------------------------------
QUERIES = {
    "weekday_summary": """
        SELECT weekday, weekday_num,
               ROUND(AVG(total_steps), 0) AS avg_steps,
               ROUND(AVG(calories), 0)    AS avg_calories,
               COUNT(*)                   AS n_days
        FROM daily_activity WHERE valid_day = 1
        GROUP BY weekday_num ORDER BY weekday_num;""",
    "hourly_summary": """
        SELECT hour_of_day,
               ROUND(AVG(steps), 1)           AS avg_steps,
               ROUND(AVG(calories), 1)        AS avg_calories,
               ROUND(AVG(total_intensity), 2) AS avg_intensity
        FROM hourly_activity GROUP BY hour_of_day ORDER BY hour_of_day;""",
    "weekday_vs_weekend": """
        SELECT day_type,
               ROUND(AVG(total_steps), 0)     AS avg_steps,
               ROUND(AVG(very_active_min), 1) AS avg_very_active_min,
               ROUND(AVG(sedentary_min), 0)   AS avg_sedentary_min,
               ROUND(AVG(calories), 0)        AS avg_calories
        FROM daily_activity WHERE valid_day = 1 GROUP BY day_type;""",
    "user_segments": """
        SELECT user_id, COUNT(*) AS logged_days,
               ROUND(AVG(total_steps), 0) AS avg_steps,
               CASE WHEN AVG(total_steps) < 5000 THEN 'Lightly Active'
                    WHEN AVG(total_steps) < 10000 THEN 'Moderately Active'
                    ELSE 'Highly Active' END AS segment
        FROM daily_activity WHERE valid_day = 1 GROUP BY user_id;""",
    "activity_vs_sleep": """
        SELECT d.user_id, d.activity_date, d.total_steps, d.sedentary_min,
               s.minutes_asleep, s.sleep_efficiency_pct
        FROM daily_activity d
        JOIN sleep_day s ON d.user_id = s.user_id AND d.activity_date = s.sleep_date
        WHERE d.valid_day = 1;""",
    "wear_consistency": """
        SELECT user_id, COUNT(*) AS days_in_data, SUM(valid_day) AS days_worn,
               ROUND(100.0 * SUM(valid_day) / COUNT(*), 1) AS pct_days_worn
        FROM daily_activity GROUP BY user_id ORDER BY pct_days_worn;""",
}


# ---------------------------------------------------------------------
# Page sections (rendered as tabs instead of separate page files)
# ---------------------------------------------------------------------
def section_overview():
    st.title("Bellabeat Smart Device Usage Analysis")
    st.caption("How consumers use their fitness trackers, and what it means for Bellabeat's marketing strategy.")
    st.divider()
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Business task")
        st.markdown(f"""
Bellabeat is a high-tech company that makes health-focused smart devices for women.
Co-founder and Chief Creative Officer **Urška Sršen** wants to know **how consumers
are already using their smart devices**, so that Bellabeat's marketing team can turn
those habits into growth opportunities.

This app analyzes public Fitbit fitness-tracker data as a proxy for smart-device
usage, and focuses the resulting recommendations on one Bellabeat product,
the **{PRODUCT}**.
""")
    with col2:
        st.subheader("Stakeholders")
        st.markdown("""
**Primary**
- Urška Sršen — co-founder, Chief Creative Officer
- Sando Mur — co-founder, executive team

**Secondary**
- Bellabeat marketing analytics team
""")


def section_data_cleaning():
    st.title("Data Sources and Cleaning")
    st.subheader("Data source")
    st.markdown("""
**FitBit Fitness Tracker Data** (Kaggle, via user Mobius, CC0 Public Domain).
Thirty-three eligible Fitbit users consented to submit personal tracker data
via a survey distributed on Amazon Mechanical Turk between **03.12.2016 and
05.12.2016**.
""")
    st.subheader("Known limitations")
    st.markdown("""
- Only **33 users** logged daily activity and just **24** logged sleep.
- No age, sex, or profession is recorded.
- The data is from **2016** and may not reflect current usage habits.
- Weight data is too sparse (8 users) to analyze reliably.
""")
    st.divider()
    st.subheader("Cleaned tables")
    tabs = st.tabs(["daily_activity", "sleep_day", "hourly_activity", "weight_log"])
    for tab, name in zip(tabs, ["daily_activity", "sleep_day", "hourly_activity", "weight_log"]):
        with tab:
            st.dataframe(q(f"SELECT * FROM {name} LIMIT 8"), width="stretch")


def section_sql_analysis():
    st.title("SQL Analysis")
    sections = [
        ("Average steps and calories by weekday", "weekday_summary",
         "Tuesday and Saturday have the highest average steps; Sunday is the lowest."),
        ("Average steps, calories and intensity by hour of day", "hourly_summary",
         "Activity ramps up sharply from 6 AM, peaks around midday and again from 5-7 PM."),
        ("Weekday vs weekend", "weekday_vs_weekend",
         "Step counts are similar; sedentary minutes are slightly higher on weekends."),
        ("User segments by average daily steps", "user_segments",
         "Users split into Lightly/Moderately/Highly Active groups."),
        ("Device-wear consistency", "wear_consistency",
         "Wear consistency varies widely — some users log activity far less than others."),
    ]
    for title, name, takeaway in sections:
        st.subheader(title)
        col1, col2 = st.columns(2)
        with col1:
            st.code(QUERIES[name].strip(), language="sql")
        with col2:
            st.dataframe(q(QUERIES[name]), width="stretch", height=240)
        st.success(takeaway, icon="💡")
        st.divider()


def section_dashboard():
    st.title("Dashboard")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Average steps by weekday**")
        df = q(QUERIES["weekday_summary"])
        fig, ax = new_fig()
        colors = [ORANGE if v == df.avg_steps.max() else (TEAL if v == df.avg_steps.min() else NAVY) for v in df.avg_steps]
        ax.bar(df.weekday.str.slice(0, 3), df.avg_steps, color=colors)
        ax.set_ylabel("Avg. total steps")
        st.pyplot(fig, width="stretch")
    with c2:
        st.markdown("**Average steps by hour of day**")
        df = q(QUERIES["hourly_summary"])
        fig, ax = new_fig()
        ax.plot(df.hour_of_day, df.avg_steps, color=NAVY, marker="o", markersize=3)
        ax.set_xlabel("Hour of day")
        ax.set_ylabel("Avg. steps")
        st.pyplot(fig, width="stretch")

    st.divider()
    st.markdown("**Sedentary minutes vs. minutes asleep**")
    sa = q(QUERIES["activity_vs_sleep"])
    corr = sa["sedentary_min"].corr(sa["minutes_asleep"])
    fig, ax = new_fig(9, 4)
    sns.regplot(data=sa, x="sedentary_min", y="minutes_asleep", ax=ax,
                scatter_kws={"alpha": 0.35, "color": NAVY, "s": 18}, line_kws={"color": ORANGE})
    ax.set_title(f"r = {corr:.2f}")
    st.pyplot(fig, width="stretch")
    st.caption(f"Across {len(sa)} matched user-days, more sedentary time is associated with less sleep (r = {corr:.2f}).")


def section_recommendations():
    st.title("Recommendations")
    recs = [
        ("Sunday activity nudge", "Sunday has the lowest average steps of the week.",
         f"Schedule a Sunday-morning notification on the {PRODUCT} app suggesting a short walk."),
        ("Midday and evening activity windows", "Activity peaks around midday and 5-7 PM.",
         "Time reminders to land just before these windows (11 AM and 4:30 PM)."),
        ("Engagement tiers for moderately active users", "Most users average 5,000-10,000 steps/day.",
         "Create a tiered in-app challenge ('9K to 10K') for this middle segment."),
        ("Retention outreach", "Several users log activity on well under 70% of days.",
         "Trigger a re-engagement message after 2-3 consecutive days of no activity."),
        ("Sleep and activity messaging", "Higher sedentary time is linked to shorter sleep.",
         f"Pair the {PRODUCT}'s sleep tracking with activity reminders in marketing."),
    ]
    for title, finding, rec in recs:
        with st.container(border=True):
            st.markdown(f"#### {title}")
            st.markdown(f"**Finding:** {finding}")
            st.markdown(f"**Recommendation:** {rec}")


# ---------------------------------------------------------------------
# Navigation (tabs instead of a pages/ folder)
# ---------------------------------------------------------------------
tab_labels = ["Overview", "Data & Cleaning", "SQL Analysis", "Dashboard", "Recommendations"]
tabs = st.tabs(tab_labels)
sections = [section_overview, section_data_cleaning, section_sql_analysis, section_dashboard, section_recommendations]
for tab, section_fn in zip(tabs, sections):
    with tab:
        section_fn()
