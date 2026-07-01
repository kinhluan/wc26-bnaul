#!/usr/bin/env python3
"""
Fetch advanced football statistics for wc26-bnaul.

This script manages a LOCAL CSV database of advanced stats (xG, xGA, possession, etc.)
that can be updated from multiple sources:
- Manual input (user edits CSV directly)
- FBref (via browser copy-paste or exported CSV)
- Understat API (future)
- Transfermarkt (future)

The workflow:
1. User obtains data from any source (browser, API, etc.)
2. Data is saved to data/advanced_stats.csv
3. This script reads the CSV and updates teams_db.json

Usage:
    # Display current stats
    python3 scripts/fetch_advanced_stats.py --display

    # Update teams_db.json from CSV
    python3 scripts/fetch_advanced_stats.py --update-json

    # Export current teams_db.json to CSV template
    python3 scripts/fetch_advanced_stats.py --export-template

    # Show specific team
    python3 scripts/fetch_advanced_stats.py --display --team England

CSV Format (data/advanced_stats.csv):
    team_name,xg,xga,possession,goals_scored,goals_conceded,shots_per_game,
    shots_on_target_per_game,corners_per_game,fouls_per_game,yellow_cards_per_game,
    red_cards_per_game,matches_played,source,last_updated

Dependencies:
    pip install pandas  # optional, for advanced features
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(PROJECT_ROOT, "src"))

from wc26_bnaul.json_db import load_json_db, save_json_db

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ADVANCED_STATS_CSV = os.path.join(DATA_DIR, "advanced_stats.csv")

# Default CSV columns
CSV_COLUMNS = [
    "team_name",
    "xg",
    "xga",
    "possession",
    "goals_scored",
    "goals_conceded",
    "shots_per_game",
    "shots_on_target_per_game",
    "corners_per_game",
    "fouls_per_game",
    "yellow_cards_per_game",
    "red_cards_per_game",
    "matches_played",
    "source",
    "last_updated",
    "notes",
]

# Team name mapping: CSV name -> teams_db.json key
# Handles common variations in naming
TEAM_NAME_ALIASES = {
    "united states": "USA",
    "us": "USA",
    "usa": "USA",
    "united kingdom": "England",
    "england": "England",
    "bosnia and herzegovina": "Bosnia & Herzegovina",
    "bosnia-herzegovina": "Bosnia & Herzegovina",
    "czech republic": "Czech Republic",
    "czechia": "Czech Republic",
    "south korea": "South Korea",
    "korea republic": "South Korea",
    "korea": "South Korea",
    "dr congo": "DR Congo",
    "democratic republic of congo": "DR Congo",
    "congo dr": "DR Congo",
    "ivory coast": "Ivory Coast",
    "cote d'ivoire": "Ivory Coast",
    "côte d'ivoire": "Ivory Coast",
    "cape verde": "Cape Verde",
    "cabo verde": "Cape Verde",
}


def normalize_team_name(name: str) -> str:
    """Normalize team name to match teams_db.json keys."""
    name_lower = name.strip().lower()

    # Check aliases first
    if name_lower in TEAM_NAME_ALIASES:
        return TEAM_NAME_ALIASES[name_lower]

    # Title case for standard names
    return name.strip().title()


def create_csv_template():
    """Create a CSV template with all teams from teams_db.json."""
    teams_db = load_json_db("teams_db.json")

    if not teams_db:
        print("❌ teams_db.json not found or empty")
        return

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Check if CSV already exists
    if os.path.exists(ADVANCED_STATS_CSV):
        backup_path = f"{ADVANCED_STATS_CSV}.backup.{int(time.time())}"
        print(f"⚠️  CSV already exists. Creating backup: {backup_path}")
        os.rename(ADVANCED_STATS_CSV, backup_path)

    with open(ADVANCED_STATS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        for team_name in sorted(teams_db.keys()):
            team_data = teams_db[team_name]
            row = {
                "team_name": team_name,
                "xg": team_data.get("xg", ""),
                "xga": team_data.get("xga", ""),
                "possession": team_data.get("possession", ""),
                "goals_scored": team_data.get("goals_scored", ""),
                "goals_conceded": team_data.get("goals_conceded", ""),
                "shots_per_game": team_data.get("shots_per_game", ""),
                "shots_on_target_per_game": team_data.get("shots_on_target_per_game", ""),
                "corners_per_game": team_data.get("corners_per_game", ""),
                "fouls_per_game": team_data.get("fouls_per_game", ""),
                "yellow_cards_per_game": team_data.get("yellow_cards_per_game", ""),
                "red_cards_per_game": team_data.get("red_cards_per_game", ""),
                "matches_played": team_data.get("matches_played", ""),
                "source": team_data.get("data_source", "static"),
                "last_updated": team_data.get("last_updated", ""),
                "notes": "",
            }
            writer.writerow(row)

    print(f"✅ Created CSV template: {ADVANCED_STATS_CSV}")
    print(f"   Contains {len(teams_db)} teams")
    print(f"\n📝 Next steps:")
    print(f"   1. Open {ADVANCED_STATS_CSV} in Excel/Google Sheets")
    print(f"   2. Fill in xG, xGA, possession from FBref/Understat/any source")
    print(f"   3. Save the CSV")
    print(f"   4. Run: python3 scripts/fetch_advanced_stats.py --update-json")


def read_csv_stats() -> dict:
    """Read advanced stats from CSV file."""
    if not os.path.exists(ADVANCED_STATS_CSV):
        print(f"❌ CSV file not found: {ADVANCED_STATS_CSV}")
        print(f"   Run: python3 scripts/fetch_advanced_stats.py --export-template")
        return {}

    stats = {}
    with open(ADVANCED_STATS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate headers
        if not reader.fieldnames:
            print("❌ CSV has no headers")
            return {}

        missing_cols = [col for col in ["team_name", "xg", "xga"] if col not in reader.fieldnames]
        if missing_cols:
            print(f"❌ CSV missing required columns: {missing_cols}")
            return {}

        for row in reader:
            team_name = normalize_team_name(row.get("team_name", ""))
            if not team_name:
                continue

            # Parse numeric values
            team_stats = {}
            for col in CSV_COLUMNS:
                if col in ["team_name", "source", "last_updated", "notes"]:
                    continue

                val = row.get(col, "").strip()
                if val:
                    try:
                        team_stats[col] = float(val)
                    except ValueError:
                        pass

            # Add metadata
            if row.get("source"):
                team_stats["source"] = row["source"]
            if row.get("notes"):
                team_stats["notes"] = row["notes"]

            if team_stats:
                stats[team_name] = team_stats

    print(f"✅ Read stats for {len(stats)} teams from CSV")
    return stats


def update_teams_db_from_csv(update_json: bool = False) -> dict:
    """Update teams_db.json with data from CSV."""
    csv_stats = read_csv_stats()
    if not csv_stats:
        return {}

    teams_db = load_json_db("teams_db.json")
    updates = {}
    skipped = []

    for team_name, stats in csv_stats.items():
        if team_name not in teams_db:
            skipped.append(team_name)
            continue

        team_data = teams_db[team_name]
        old_values = {}
        new_values = {}

        # Update fields
        for key, value in stats.items():
            if key in ["source", "notes"]:
                continue

            old_val = team_data.get(key)
            if old_val != value:
                old_values[key] = old_val
                new_values[key] = value
                team_data[key] = value

        # Update metadata
        if stats.get("source"):
            team_data["data_source"] = stats["source"]
        team_data["data_source_csv"] = True
        team_data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if new_values:
            updates[team_name] = {
                "old": old_values,
                "new": new_values,
            }

    if update_json:
        save_json_db("teams_db.json", teams_db)
        print(f"🎉 Saved updates to teams_db.json")
    else:
        print(f"📊 Dry run - {len(updates)} teams would be updated")

    # Print summary
    if updates:
        print(f"\n{'='*60}")
        print("Update Summary")
        print(f"{'='*60}")
        for team, change in updates.items():
            print(f"\n  {team}:")
            for key in change["new"]:
                old_v = change["old"].get(key, "N/A")
                new_v = change["new"][key]
                print(f"    {key}: {old_v} -> {new_v}")

    if skipped:
        print(f"\n⚠️  Skipped {len(skipped)} teams not in teams_db.json:")
        for team in skipped[:10]:
            print(f"    - {team}")
        if len(skipped) > 10:
            print(f"    ... and {len(skipped) - 10} more")

    return updates


def display_stats(team_name: str = None):
    """Display current stats from teams_db.json."""
    teams_db = load_json_db("teams_db.json")

    if not teams_db:
        print("❌ teams_db.json not found or empty")
        return

    if team_name and team_name != "all":
        # Find team (case-insensitive)
        found = None
        for key in teams_db:
            if key.lower() == team_name.lower():
                found = key
                break

        if not found:
            print(f"❌ Team '{team_name}' not found")
            suggestions = [k for k in teams_db if team_name.lower() in k.lower()]
            if suggestions:
                print(f"   Did you mean: {', '.join(suggestions)}?")
            return

        data = teams_db[found]
        print(f"\n{'='*60}")
        print(f"Team: {found}")
        print(f"{'='*60}")

        # Show relevant stats
        stat_keys = [
            "fifa_rank", "elo_rating", "confederation",
            "xg", "xga", "possession",
            "goals_scored", "goals_conceded",
            "shots_per_game", "shots_on_target_per_game",
            "corners_per_game", "fouls_per_game",
            "squad_depth_score", "market_value_eur",
            "form", "injuries",
            "data_source", "data_source_csv", "last_updated",
        ]

        for key in stat_keys:
            if key in data:
                print(f"  {key:30s}: {data[key]}")
    else:
        # Display all teams in table format
        print(f"\n{'='*100}")
        print(f"{'Team':25s} {'xG':>6s} {'xGA':>6s} {'Poss%':>6s} {'Depth':>6s} {'Source':>15s}")
        print(f"{'-'*100}")

        for team in sorted(teams_db.keys()):
            data = teams_db[team]
            xg = data.get("xg", "N/A")
            xga = data.get("xga", "N/A")
            poss = data.get("possession", "N/A")
            depth = data.get("squad_depth_score", "N/A")

            source = "static"
            if data.get("data_source_csv"):
                source = "csv"
            elif data.get("data_source_fbref"):
                source = "fbref"
            elif data.get("data_source"):
                source = data["data_source"]

            print(f"{team:25s} {str(xg):>6s} {str(xga):>6s} {str(poss):>6s} {str(depth):>6s} {source:>15s}")

        print(f"{'='*100}")
        print(f"Total: {len(teams_db)} teams")


def validate_csv():
    """Validate the CSV file format."""
    if not os.path.exists(ADVANCED_STATS_CSV):
        print(f"❌ CSV file not found: {ADVANCED_STATS_CSV}")
        return False

    with open(ADVANCED_STATS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            print("❌ CSV has no headers")
            return False

        print(f"✅ CSV headers: {reader.fieldnames}")

        # Check for required columns
        required = ["team_name", "xg", "xga"]
        missing = [col for col in required if col not in reader.fieldnames]
        if missing:
            print(f"❌ Missing required columns: {missing}")
            return False

        # Count rows
        rows = list(reader)
        print(f"✅ CSV has {len(rows)} data rows")

        # Check for empty xG values
        empty_xg = [row["team_name"] for row in rows if not row.get("xg", "").strip()]
        if empty_xg:
            print(f"⚠️  {len(empty_xg)} teams have empty xG values:")
            for team in empty_xg[:5]:
                print(f"    - {team}")

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Manage advanced football stats for wc26-bnaul",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create CSV template from current teams_db.json
  python3 scripts/fetch_advanced_stats.py --export-template

  # Validate your CSV file
  python3 scripts/fetch_advanced_stats.py --validate

  # Preview updates (dry run)
  python3 scripts/fetch_advanced_stats.py --update-json --dry-run

  # Apply updates to teams_db.json
  python3 scripts/fetch_advanced_stats.py --update-json

  # Display current stats
  python3 scripts/fetch_advanced_stats.py --display

  # Display specific team
  python3 scripts/fetch_advanced_stats.py --display --team England
        """
    )

    parser.add_argument("--export-template", action="store_true",
                        help="Export teams_db.json to CSV template")
    parser.add_argument("--update-json", action="store_true",
                        help="Update teams_db.json from CSV")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without saving")
    parser.add_argument("--display", action="store_true",
                        help="Display current stats")
    parser.add_argument("--team", default="all",
                        help="Team name for --display (default: all)")
    parser.add_argument("--validate", action="store_true",
                        help="Validate CSV format")

    args = parser.parse_args()

    if args.export_template:
        create_csv_template()
        return

    if args.validate:
        validate_csv()
        return

    if args.update_json:
        update_teams_db_from_csv(update_json=not args.dry_run)
        return

    if args.display:
        display_stats(args.team)
        return

    # Default: show help
    parser.print_help()
    print(f"\n{'='*60}")
    print("Quick Start:")
    print(f"{'='*60}")
    print("1. Export template:  python3 scripts/fetch_advanced_stats.py --export-template")
    print("2. Edit CSV:         Open data/advanced_stats.csv and fill in stats")
    print("3. Validate:         python3 scripts/fetch_advanced_stats.py --validate")
    print("4. Preview:          python3 scripts/fetch_advanced_stats.py --update-json --dry-run")
    print("5. Apply:            python3 scripts/fetch_advanced_stats.py --update-json")


if __name__ == "__main__":
    main()
