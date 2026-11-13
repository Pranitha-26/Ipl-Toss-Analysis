"""
IPL 2026 Toss Impact Analysis
Usage: python ipl_2026_analysis.py matches.csv

Works with the IPL 2026 file that has these columns:
match_id, date, venue, team1, team2, stage, toss_winner, toss_decision,
match_result, match_winner (and others, which are ignored)
"""
import sys
import pandas as pd

path = sys.argv[1] if len(sys.argv) > 1 else "matches.csv"
df = pd.read_csv(path)
print("Rows loaded:", len(df))

# ---------- 1. Clean ----------
df = df.drop_duplicates()

# Tidy text columns (remove extra spaces)
for col in ["venue", "team1", "team2", "toss_winner", "toss_decision", "match_winner"]:
    df[col] = df[col].astype("string").str.strip()

df["toss_decision"] = df["toss_decision"].str.lower()
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# Keep only matches that produced a winner (drops no-result / abandoned)
teams = set(df["team1"].dropna()) | set(df["team2"].dropna())
before = len(df)
df = df[df["match_winner"].isin(teams)].copy()
print(f"Matches with a result: {len(df)} (dropped {before - len(df)})")

# Safety check: toss winner names must match team names
bad = df[~df["toss_winner"].isin(teams)]
if len(bad):
    print("\nWARNING: toss_winner names that don't match team1/team2:")
    print(bad["toss_winner"].unique())

# ---------- 2. Toss analysis ----------
df["toss_winner_won_match"] = df["toss_winner"] == df["match_winner"]
overall = df["toss_winner_won_match"].mean() * 100
print(f"\nToss winner also won the match: {overall:.1f}% "
      f"({int(df['toss_winner_won_match'].sum())} of {len(df)} matches)")

# ---------- 3. Bat first vs field first (the toss choice) ----------
by_decision = (
    df.groupby("toss_decision")["toss_winner_won_match"]
    .agg(["count", "mean"])
    .rename(columns={"count": "matches", "mean": "toss_winner_win_rate"})
)
by_decision["toss_winner_win_rate"] = (by_decision["toss_winner_win_rate"] * 100).round(1)
print("\nWhen the toss winner chose to...")
print(by_decision)

# ---------- 4. Chasing vs defending (independent of who won the toss) ----------
df["bat_first_team"] = df.apply(
    lambda r: r["toss_winner"] if r["toss_decision"] == "bat"
    else (r["team2"] if r["toss_winner"] == r["team1"] else r["team1"]),
    axis=1,
)
df["batting_first_won"] = df["bat_first_team"] == df["match_winner"]
bf = df["batting_first_won"].mean() * 100
print(f"\nTeam batting first won: {bf:.1f}%  |  Chasing team won: {100 - bf:.1f}%")

# ---------- 5. Venue view ----------
venue = (
    df.groupby("venue")
    .agg(matches=("match_id", "count"),
         toss_winner_win_rate=("toss_winner_won_match", "mean"),
         batting_first_win_rate=("batting_first_won", "mean"))
)
venue["toss_winner_win_rate"] = (venue["toss_winner_win_rate"] * 100).round(1)
venue["batting_first_win_rate"] = (venue["batting_first_win_rate"] * 100).round(1)
venue = venue.sort_values("matches", ascending=False)
print("\nBy venue (small samples, read with care):")
print(venue)

# ---------- 6. Team view ----------
team_rows = []
for t in sorted(teams):
    won_toss = df[df["toss_winner"] == t]
    team_rows.append({
        "team": t,
        "tosses_won": len(won_toss),
        "won_match_after_toss": int(won_toss["toss_winner_won_match"].sum()),
    })
team_df = pd.DataFrame(team_rows)
print("\nBy team:")
print(team_df)

# ---------- 7. Save for Power BI ----------
df.to_csv("ipl_clean.csv", index=False)
by_decision.to_csv("toss_by_decision.csv")
venue.to_csv("toss_by_venue.csv")
team_df.to_csv("toss_by_team.csv", index=False)
print("\nSaved: ipl_clean.csv, toss_by_decision.csv, toss_by_venue.csv, toss_by_team.csv")
