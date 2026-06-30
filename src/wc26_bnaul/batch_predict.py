#!/usr/bin/env python3
"""
Batch Ensemble Predictions for all open ClawCup matches.

Usage:
    uv run python -m wc26_bnaul.batch_predict --dry-run    # Preview only
    uv run python -m wc26_bnaul.batch_predict --live         # Actually submit
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Load .env
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                value = value.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = value

from wc26_bnaul import api_request
from wc26_bnaul.ensemble_predictor import EnsemblePredictor
from wc26_bnaul.prediction_logger import PredictionLogger

# Initialize logger
logger = PredictionLogger()


# =============================================================================
# TEAM DATA DATABASE (Enhanced with Amir Motefaker Dataset)
# =============================================================================
# Sources:
# - FIFA Rank: FIFA Official Rankings (June 2026)
# - ELO Rating: Adapted from national team ELO methodology (Amir dataset)
# - xG/xGA: Based on recent qualifying campaign averages (Amir dataset)
# - Form: Last 5 matches (W=1, D=0, L=-1)
# - Squad Depth: 0-10 scale (Amir dataset)
# - Key Players: Core squad members (Amir dataset)
# - H2H: Historical head-to-head (manually curated)
# - Injuries: Key players missing (manually updated)
#
# Integration: FIFA rank + ELO rating used together for maximum accuracy
# - ELO is more predictive (accounts for opponent strength)
# - FIFA rank is official and widely recognized
# - Ensemble uses both: ELO(30%) + FIFA-based(10%) = 40% strength component

TEAM_DB = {
    # === TOP 10 (World Cup favorites) ===
    # Amir ELO range: 1975-2045 | FIFA: 1-10 | Squad depth: 8.3-9.5
    "Argentina": {
        "rank": 1, "elo": 2031, "xg": 2.09, "xga": 0.88,
        "form": [1, 1, 1, 0, 1], "form_score": 13,
        "squad_depth": 9.2, "key_players": ["Messi", "Alvarez", "Enzo", "Martinez"],
        "formation": "4-3-3", "tactical_style": "possession_attacking",
        "host_nation": False, "confederation": "CONMEBOL",
        "injuries": 0,
        "h2h": {"Brazil": {"home_wins": 2, "draws": 1, "away_wins": 1}, "France": {"home_wins": 1, "draws": 1, "away_wins": 2}, "England": {"home_wins": 1, "draws": 0, "away_wins": 1}}
    },
    "France": {
        "rank": 2, "elo": 2045, "xg": 2.31, "xga": 0.85,
        "form": [1, 0, 1, 1, 1], "form_score": 13,
        "squad_depth": 9.5, "key_players": ["Mbappe", "Griezmann", "Tchouameni", "Upamecano"],
        "formation": "4-3-3", "tactical_style": "balanced_attacking",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 1,
        "h2h": {"Argentina": {"home_wins": 2, "draws": 1, "away_wins": 1}, "Germany": {"home_wins": 1, "draws": 1, "away_wins": 1}, "Belgium": {"home_wins": 2, "draws": 0, "away_wins": 0}}
    },
    "Brazil": {
        "rank": 3, "elo": 2008, "xg": 2.28, "xga": 1.02,
        "form": [1, 1, 1, -1, 1], "form_score": 12,
        "squad_depth": 9.3, "key_players": ["Vinicius Jr", "Rodrygo", "Casemiro", "Alisson"],
        "formation": "4-2-3-1", "tactical_style": "attacking_flair",
        "host_nation": False, "confederation": "CONMEBOL",
        "injuries": 0,
        "h2h": {"Argentina": {"home_wins": 1, "draws": 1, "away_wins": 2}, "Germany": {"home_wins": 0, "draws": 0, "away_wins": 2}, "Croatia": {"home_wins": 1, "draws": 0, "away_wins": 1}, "Japan": {"home_wins": 1, "draws": 0, "away_wins": 0}}
    },
    "England": {
        "rank": 4, "elo": 2019, "xg": 2.02, "xga": 0.95,
        "form": [1, 1, 1, 0, 1], "form_score": 13,
        "squad_depth": 9.1, "key_players": ["Kane", "Bellingham", "Foden", "Rice"],
        "formation": "4-2-3-1", "tactical_style": "direct_attacking",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 2,
        "h2h": {"France": {"home_wins": 1, "draws": 0, "away_wins": 1}, "Germany": {"home_wins": 1, "draws": 1, "away_wins": 1}, "Spain": {"home_wins": 0, "draws": 1, "away_wins": 2}}
    },
    "Spain": {
        "rank": 5, "elo": 2038, "xg": 2.18, "xga": 0.82,
        "form": [1, 0, 1, 1, 0], "form_score": 11,
        "squad_depth": 9.4, "key_players": ["Yamal", "Williams", "Rodri", "Morata"],
        "formation": "4-3-3", "tactical_style": "possession_technical",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 1,
        "h2h": {"Germany": {"home_wins": 2, "draws": 0, "away_wins": 1}, "England": {"home_wins": 2, "draws": 1, "away_wins": 0}, "Italy": {"home_wins": 1, "draws": 1, "away_wins": 1}}
    },
    "Germany": {
        "rank": 6, "elo": 1975, "xg": 1.92, "xga": 1.08,
        "form": [1, 1, 0, 1, 0], "form_score": 11,
        "squad_depth": 8.8, "key_players": ["Musiala", "Wirtz", "Kimmich", "Neuer"],
        "formation": "4-2-3-1", "tactical_style": "organized_attacking",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 3,
        "h2h": {"France": {"home_wins": 1, "draws": 1, "away_wins": 1}, "Brazil": {"home_wins": 2, "draws": 0, "away_wins": 0}, "Spain": {"home_wins": 1, "draws": 0, "away_wins": 2}, "Paraguay": {"home_wins": 0, "draws": 1, "away_wins": 0}}
    },
    "Portugal": {
        "rank": 7, "elo": 2011, "xg": 2.14, "xga": 0.92,
        "form": [1, 1, 0, 1, 0], "form_score": 11,
        "squad_depth": 8.9, "key_players": ["Ronaldo", "Felix", "Silva", "Dias"],
        "formation": "4-3-3", "tactical_style": "balanced_attacking",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 1,
        "h2h": {"Spain": {"home_wins": 0, "draws": 1, "away_wins": 2}, "France": {"home_wins": 0, "draws": 0, "away_wins": 2}, "Switzerland": {"home_wins": 1, "draws": 1, "away_wins": 0}}
    },
    "Netherlands": {
        "rank": 8, "elo": 1998, "xg": 1.97, "xga": 0.95,
        "form": [0, 1, 0, 1, 1], "form_score": 10,
        "squad_depth": 8.7, "key_players": ["Gakpo", "Depay", "De Jong", "Van Dijk"],
        "formation": "3-4-1-2", "tactical_style": "organized_attacking",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 2,
        "h2h": {"Argentina": {"home_wins": 0, "draws": 1, "away_wins": 2}, "Spain": {"home_wins": 1, "draws": 0, "away_wins": 1}, "Germany": {"home_wins": 1, "draws": 1, "away_wins": 1}}
    },
    "Belgium": {
        "rank": 9, "elo": 1979, "xg": 1.88, "xga": 1.05,
        "form": [0, 1, 1, 0, 1], "form_score": 10,
        "squad_depth": 8.3, "key_players": ["De Bruyne", "Lukaku", "Tielemans", "Courtois"],
        "formation": "3-4-2-1", "tactical_style": "possession_attacking",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 1,
        "h2h": {"France": {"home_wins": 0, "draws": 0, "away_wins": 2}, "England": {"home_wins": 0, "draws": 1, "away_wins": 1}, "Netherlands": {"home_wins": 1, "draws": 0, "away_wins": 1}}
    },
    "Italy": {
        "rank": 10, "elo": 1962, "xg": 1.75, "xga": 0.92,
        "form": [1, 0, 1, 0, 1], "form_score": 10,
        "squad_depth": 8.2, "key_players": ["Barella", "Chiesa", "Immobile", "Donnarumma"],
        "formation": "4-3-3", "tactical_style": "organized_defensive",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 2,
        "h2h": {"Spain": {"home_wins": 1, "draws": 1, "away_wins": 1}, "Germany": {"home_wins": 1, "draws": 1, "away_wins": 1}, "England": {"home_wins": 1, "draws": 0, "away_wins": 1}}
    },
    # === TOP 20 ===
    "USA": {
        "rank": 11, "elo": 1928, "xg": 1.62, "xga": 1.22,
        "form": [1, 0, 1, 1, 0], "form_score": 11,
        "squad_depth": 7.5, "key_players": ["Pulisic", "Reyna", "Adams", "Turner"],
        "formation": "4-3-3", "tactical_style": "high_energy_press",
        "host_nation": True, "confederation": "CONCACAF",
        "injuries": 1,
        "h2h": {"Mexico": {"home_wins": 2, "draws": 1, "away_wins": 0}, "Canada": {"home_wins": 2, "draws": 0, "away_wins": 0}}
    },
    "Mexico": {
        "rank": 12, "elo": 1932, "xg": 1.59, "xga": 1.18,
        "form": [1, 1, 0, 0, 1], "form_score": 11,
        "squad_depth": 7.6, "key_players": ["Alvarez", "Antuna", "Herrera", "Ochoa"],
        "formation": "4-3-3", "tactical_style": "organized_defensive",
        "host_nation": True, "confederation": "CONCACAF",
        "injuries": 2,
        "h2h": {"USA": {"home_wins": 0, "draws": 1, "away_wins": 2}, "Ecuador": {"home_wins": 1, "draws": 1, "away_wins": 0}}
    },
    "Morocco": {
        "rank": 13, "elo": 1985, "xg": 1.62, "xga": 0.88,
        "form": [0, 1, 0, 1, 1], "form_score": 10,
        "squad_depth": 8.5, "key_players": ["Hakimi", "En-Nesyri", "Ounahi", "Bounou"],
        "formation": "4-3-3", "tactical_style": "low_block_counter",
        "host_nation": False, "confederation": "CAF",
        "injuries": 0,
        "h2h": {"Spain": {"home_wins": 1, "draws": 0, "away_wins": 1}, "Portugal": {"home_wins": 0, "draws": 0, "away_wins": 2}}
    },
    "Switzerland": {
        "rank": 14, "elo": 1910, "xg": 1.58, "xga": 1.08,
        "form": [0, 1, 1, 0, 0], "form_score": 9,
        "squad_depth": 7.3, "key_players": ["Xhaka", "Embolo", "Sommer", "Freuler"],
        "formation": "4-2-3-1", "tactical_style": "organized_balanced",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 1,
        "h2h": {"France": {"home_wins": 0, "draws": 1, "away_wins": 2}, "Portugal": {"home_wins": 0, "draws": 1, "away_wins": 1}}
    },
    "Croatia": {
        "rank": 15, "elo": 1895, "xg": 1.45, "xga": 1.12,
        "form": [0, 1, 0, 1, 0], "form_score": 8,
        "squad_depth": 7.1, "key_players": ["Modric", "Kovacic", "Perisic", "Livakovic"],
        "formation": "4-3-3", "tactical_style": "possession_technical",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 3,
        "h2h": {"Brazil": {"home_wins": 1, "draws": 0, "away_wins": 1}, "Argentina": {"home_wins": 0, "draws": 1, "away_wins": 2}}
    },
    "Japan": {
        "rank": 16, "elo": 1885, "xg": 1.42, "xga": 1.15,
        "form": [0, 0, 1, 1, -1], "form_score": 8,
        "squad_depth": 7.0, "key_players": ["Kubo", "Mitoma", "Endo", "Gonda"],
        "formation": "4-2-3-1", "tactical_style": "organized_counter",
        "host_nation": False, "confederation": "AFC",
        "injuries": 0,
        "h2h": {"Germany": {"home_wins": 1, "draws": 0, "away_wins": 1}, "Spain": {"home_wins": 0, "draws": 0, "away_wins": 2}, "Brazil": {"home_wins": 0, "draws": 0, "away_wins": 1}}
    },
    "Colombia": {
        "rank": 17, "elo": 1872, "xg": 1.55, "xga": 1.15,
        "form": [1, 0, 1, 1, 0], "form_score": 10,
        "squad_depth": 6.8, "key_players": ["Diaz", "Rodriguez", "Cuadrado", "Ospina"],
        "formation": "4-3-3", "tactical_style": "attacking_flair",
        "host_nation": False, "confederation": "CONMEBOL",
        "injuries": 1,
        "h2h": {"Brazil": {"home_wins": 0, "draws": 1, "away_wins": 2}, "Argentina": {"home_wins": 0, "draws": 0, "away_wins": 2}}
    },
    "Senegal": {
        "rank": 18, "elo": 1862, "xg": 1.38, "xga": 1.22,
        "form": [1, 1, 0, 0, 1], "form_score": 10,
        "squad_depth": 6.7, "key_players": ["Mane", "Sarr", "Koulibaly", "Mendy"],
        "formation": "4-3-3", "tactical_style": "fast_athletic",
        "host_nation": False, "confederation": "CAF",
        "injuries": 0,
        "h2h": {"Netherlands": {"home_wins": 0, "draws": 0, "away_wins": 2}, "England": {"home_wins": 0, "draws": 0, "away_wins": 1}}
    },
    "Sweden": {
        "rank": 19, "elo": 1845, "xg": 1.35, "xga": 1.25,
        "form": [0, 0, 1, 1, 0], "form_score": 8,
        "squad_depth": 6.5, "key_players": ["Isak", "Kulusevski", "Lindlov", "Olsen"],
        "formation": "4-4-2", "tactical_style": "organized_counter",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 2,
        "h2h": {"Germany": {"home_wins": 0, "draws": 0, "away_wins": 2}, "England": {"home_wins": 0, "draws": 1, "away_wins": 1}}
    },
    "Uruguay": {
        "rank": 20, "elo": 1855, "xg": 1.42, "xga": 1.18,
        "form": [1, 0, 1, 0, 0], "form_score": 8,
        "squad_depth": 6.6, "key_players": ["Nunez", "Valverde", "Araujo", "Rochet"],
        "formation": "4-4-2", "tactical_style": "direct_physical",
        "host_nation": False, "confederation": "CONMEBOL",
        "injuries": 1,
        "h2h": {"Argentina": {"home_wins": 1, "draws": 0, "away_wins": 2}, "Brazil": {"home_wins": 0, "draws": 1, "away_wins": 2}}
    },
    # === TOP 40 ===
    "Ecuador": {
        "rank": 21, "elo": 1832, "xg": 1.38, "xga": 1.28,
        "form": [1, 0, 1, 0, 0], "form_score": 8,
        "squad_depth": 6.4, "key_players": ["Caicedo", "Valencia", "Estupinan", "Dominguez"],
        "formation": "4-3-3", "tactical_style": "fast_athletic",
        "host_nation": False, "confederation": "CONMEBOL",
        "injuries": 1,
        "h2h": {"Mexico": {"home_wins": 0, "draws": 1, "away_wins": 1}, "Argentina": {"home_wins": 0, "draws": 0, "away_wins": 2}}
    },
    "Australia": {
        "rank": 22, "elo": 1865, "xg": 1.29, "xga": 1.21,
        "form": [1, 0, 1, 0, 0], "form_score": 8,
        "squad_depth": 6.6, "key_players": ["Leckie", "Irvine", "Redmayne", "McGree"],
        "formation": "4-4-2", "tactical_style": "organized_pragmatic",
        "host_nation": False, "confederation": "AFC",
        "injuries": 1,
        "h2h": {"Japan": {"home_wins": 0, "draws": 1, "away_wins": 1}, "England": {"home_wins": 0, "draws": 0, "away_wins": 1}}
    },
    "Austria": {
        "rank": 23, "elo": 1828, "xg": 1.45, "xga": 1.18,
        "form": [1, 0, 0, 1, 1], "form_score": 10,
        "squad_depth": 6.2, "key_players": ["Arnautovic", "Sabitzer", "Alaba", "Lindner"],
        "formation": "4-2-3-1", "tactical_style": "organized_counter",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 2,
        "h2h": {"Germany": {"home_wins": 0, "draws": 0, "away_wins": 2}, "Spain": {"home_wins": 0, "draws": 0, "away_wins": 2}}
    },
    "Canada": {
        "rank": 24, "elo": 1851, "xg": 1.45, "xga": 1.28,
        "form": [1, 1, 0, 0, 0], "form_score": 10,
        "squad_depth": 7.2, "key_players": ["Davies", "David", "Buchanan", "Borjan"],
        "formation": "4-3-3", "tactical_style": "direct_attacking",
        "host_nation": True, "confederation": "CONCACAF",
        "injuries": 1,
        "h2h": {"USA": {"home_wins": 0, "draws": 0, "away_wins": 2}, "Mexico": {"home_wins": 0, "draws": 0, "away_wins": 2}}
    },
    "Algeria": {
        "rank": 25, "elo": 1798, "xg": 1.22, "xga": 1.35,
        "form": [0, 1, 0, 0, 1], "form_score": 8,
        "squad_depth": 5.9, "key_players": ["Mahrez", "Bennacer", "Slimani", "Mbolhi"],
        "formation": "4-3-3", "tactical_style": "fast_athletic",
        "host_nation": False, "confederation": "CAF",
        "injuries": 0,
        "h2h": {"France": {"home_wins": 0, "draws": 0, "away_wins": 2}, "Germany": {"home_wins": 0, "draws": 0, "away_wins": 1}}
    },
    "Egypt": {
        "rank": 26, "elo": 1805, "xg": 1.25, "xga": 1.32,
        "form": [1, 0, 0, 1, 0], "form_score": 8,
        "squad_depth": 6.0, "key_players": ["Salah", "Elneny", "Trezequet", "El Shenawy"],
        "formation": "4-2-3-1", "tactical_style": "organized_counter",
        "host_nation": False, "confederation": "CAF",
        "injuries": 1,
        "h2h": {"Spain": {"home_wins": 0, "draws": 0, "away_wins": 1}, "Portugal": {"home_wins": 0, "draws": 0, "away_wins": 1}}
    },
    "Norway": {
        "rank": 27, "elo": 1815, "xg": 1.38, "xga": 1.28,
        "form": [0, 1, 0, 0, 1], "form_score": 8,
        "squad_depth": 6.1, "key_players": ["Haaland", "Odegaard", "Hauge", "Nyland"],
        "formation": "4-3-3", "tactical_style": "direct_attacking",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 2,
        "h2h": {"Sweden": {"home_wins": 1, "draws": 0, "away_wins": 1}, "England": {"home_wins": 0, "draws": 0, "away_wins": 2}}
    },
    "Paraguay": {
        "rank": 28, "elo": 1815, "xg": 1.22, "xga": 1.21,
        "form": [1, 0, 1, 0, 1], "form_score": 9,
        "squad_depth": 6.1, "key_players": ["Almiron", "Sanabria", "Gomez", "Silva"],
        "formation": "4-4-2", "tactical_style": "defensive_organized",
        "host_nation": False, "confederation": "CONMEBOL",
        "injuries": 1,
        "h2h": {"Brazil": {"home_wins": 0, "draws": 0, "away_wins": 2}, "Argentina": {"home_wins": 0, "draws": 1, "away_wins": 2}, "Germany": {"home_wins": 0, "draws": 1, "away_wins": 0}}
    },
    "Ivory Coast": {
        "rank": 29, "elo": 1788, "xg": 1.18, "xga": 1.38,
        "form": [1, 0, 0, 1, 0], "form_score": 8,
        "squad_depth": 5.8, "key_players": ["Zaha", "Haller", "Kessie", "Sangare"],
        "formation": "4-3-3", "tactical_style": "fast_athletic",
        "host_nation": False, "confederation": "CAF",
        "injuries": 0,
        "h2h": {"France": {"home_wins": 0, "draws": 0, "away_wins": 2}, "England": {"home_wins": 0, "draws": 0, "away_wins": 1}}
    },
    "Bosnia & Herzegovina": {
        "rank": 30, "elo": 1782, "xg": 1.15, "xga": 1.42,
        "form": [0, 0, 1, 0, 1], "form_score": 8,
        "squad_depth": 5.8, "key_players": ["Dzeko", "Pjanic", "Tatar", "Sehic"],
        "formation": "4-3-3", "tactical_style": "direct_physical",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 2,
        "h2h": {"Germany": {"home_wins": 0, "draws": 0, "away_wins": 2}, "Spain": {"home_wins": 0, "draws": 0, "away_wins": 2}}
    },
    # === LOWER RANKED ===
    "Ghana": {
        "rank": 45, "elo": 1762, "xg": 1.05, "xga": 1.45,
        "form": [0, 1, 0, 0, 1], "form_score": 7,
        "squad_depth": 5.5, "key_players": ["Kudus", "Partey", "Williams", "Ati-Zigi"],
        "formation": "4-3-3", "tactical_style": "fast_athletic",
        "host_nation": False, "confederation": "CAF",
        "injuries": 1,
        "h2h": {"Portugal": {"home_wins": 0, "draws": 0, "away_wins": 2}, "Spain": {"home_wins": 0, "draws": 0, "away_wins": 1}}
    },
    "DR Congo": {
        "rank": 55, "elo": 1728, "xg": 0.95, "xga": 1.52,
        "form": [0, 1, 0, 0, 0], "form_score": 6,
        "squad_depth": 5.1, "key_players": ["Bakambu", "Meschak", "Muke", "Mandanda"],
        "formation": "4-3-3", "tactical_style": "organized_counter",
        "host_nation": False, "confederation": "CAF",
        "injuries": 0,
        "h2h": {"France": {"home_wins": 0, "draws": 0, "away_wins": 1}, "England": {"home_wins": 0, "draws": 0, "away_wins": 1}}
    },
    "Cape Verde": {
        "rank": 65, "elo": 1731, "xg": 0.92, "xga": 1.55,
        "form": [0, 0, 1, 0, 0], "form_score": 6,
        "squad_depth": 5.0, "key_players": ["Andrade", "Fortes", "Soares", "Vozinha"],
        "formation": "4-3-3", "tactical_style": "compact_organized",
        "host_nation": False, "confederation": "CAF",
        "injuries": 0,
        "h2h": {"Portugal": {"home_wins": 0, "draws": 0, "away_wins": 2}, "Spain": {"home_wins": 0, "draws": 0, "away_wins": 2}}
    },
    # === ADDITIONAL TEAMS FROM AMIR DATASET (not in original TEAM_DB) ===
    "Turkey": {
        "rank": 34, "elo": 1828, "xg": 1.45, "xga": 1.32,
        "form": [1, 1, 0, 1, 0], "form_score": 10,
        "squad_depth": 6.2, "key_players": ["Calhanoglu", "Yildiz", "Guler", "Gunok"],
        "formation": "4-2-3-1", "tactical_style": "attacking_balanced",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 0,
        "h2h": {}
    },
    "Czech Republic": {
        "rank": 39, "elo": 1812, "xg": 1.35, "xga": 1.28,
        "form": [1, 0, 1, 0, 0], "form_score": 9,
        "squad_depth": 6.2, "key_players": ["Schick", "Soucek", "Kuchta", "Vaclik"],
        "formation": "4-2-3-1", "tactical_style": "organized_counter",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 0,
        "h2h": {}
    },
    "South Korea": {
        "rank": 25, "elo": 1878, "xg": 1.38, "xga": 1.19,
        "form": [1, 0, 1, 0, 0], "form_score": 9,
        "squad_depth": 6.8, "key_players": ["Son", "Hwang", "Kim Min-jae", "Lee Jae-sung"],
        "formation": "4-4-2", "tactical_style": "high_work_rate",
        "host_nation": False, "confederation": "AFC",
        "injuries": 0,
        "h2h": {}
    },
    "Nigeria": {
        "rank": 35, "elo": 1822, "xg": 1.41, "xga": 1.28,
        "form": [0, 1, 1, 0, 1], "form_score": 10,
        "squad_depth": 6.3, "key_players": ["Osimhen", "Lookman", "Iwobi", "Nwabali"],
        "formation": "4-3-3", "tactical_style": "fast_athletic",
        "host_nation": False, "confederation": "CAF",
        "injuries": 0,
        "h2h": {}
    },
    "Qatar": {
        "rank": 53, "elo": 1772, "xg": 1.09, "xga": 1.38,
        "form": [0, 1, 0, 0, 1], "form_score": 8,
        "squad_depth": 5.6, "key_players": ["Afif", "Ali", "Al-Haydos", "Barsham"],
        "formation": "4-3-3", "tactical_style": "possession_technical",
        "host_nation": False, "confederation": "AFC",
        "injuries": 0,
        "h2h": {}
    },
    "South Africa": {
        "rank": 43, "elo": 1789, "xg": 1.21, "xga": 1.42,
        "form": [0, 1, 0, 0, 1], "form_score": 9,
        "squad_depth": 5.8, "key_players": ["Percy Tau", "Dolly", "Ronwen Williams"],
        "formation": "4-3-3", "tactical_style": "organized_defensive",
        "host_nation": False, "confederation": "CAF",
        "injuries": 0,
        "h2h": {}
    },
    # === PLACEHOLDER FOR UNKNOWN TEAMS (W74, W75, etc.) ===
    "W74": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W75": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W76": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W77": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W78": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W79": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W80": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W81": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W82": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W83": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W84": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W85": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W86": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W87": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W88": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W89": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W90": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W91": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W92": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W93": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W94": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W95": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W96": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W97": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W98": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W99": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W100": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W101": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "W102": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "L101": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
    "L102": {"rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0], "squad_depth": 5.0, "key_players": [], "formation": "4-3-3", "tactical_style": "balanced", "host_nation": False, "confederation": "UEFA", "injuries": 0},
}


# =============================================================================
# VENUE DATABASE (from Amir Motefaker Dataset)
# =============================================================================

VENUE_DB = {
    "Estadio Azteca": {
        "city": "Mexico City", "country": "Mexico",
        "altitude_m": 2200, "altitude_category": "extreme",
        "xg_modifier": 1.12, "avg_temp_c": 18, "humidity_pct": 55,
        "weather_category": "mild_highland", "weather_modifier": 1.0,
        "surface": "hybrid_grass", "roof": "open", "capacity": 87500,
        "host_nation_venue": True,
    },
    "Estadio Akron": {
        "city": "Guadalajara", "country": "Mexico",
        "altitude_m": 1566, "altitude_category": "high",
        "xg_modifier": 1.05, "avg_temp_c": 23, "humidity_pct": 60,
        "weather_category": "warm_highland", "weather_modifier": 1.0,
        "surface": "natural_grass", "roof": "partial", "capacity": 48000,
        "host_nation_venue": True,
    },
    "Estadio BBVA": {
        "city": "Monterrey", "country": "Mexico",
        "altitude_m": 538, "altitude_category": "medium",
        "xg_modifier": 1.02, "avg_temp_c": 34, "humidity_pct": 45,
        "weather_category": "extreme_heat", "weather_modifier": 0.94,
        "surface": "natural_grass", "roof": "open", "capacity": 53500,
        "host_nation_venue": True,
    },
    "MetLife Stadium": {
        "city": "New York", "country": "USA",
        "altitude_m": 7, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 26, "humidity_pct": 65,
        "weather_category": "warm_humid", "weather_modifier": 1.0,
        "surface": "artificial_turf", "roof": "open", "capacity": 82500,
        "host_nation_venue": True,
    },
    "SoFi Stadium": {
        "city": "Los Angeles", "country": "USA",
        "altitude_m": 32, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 25, "humidity_pct": 55,
        "weather_category": "warm", "weather_modifier": 1.0,
        "surface": "artificial_turf", "roof": "fixed", "capacity": 70240,
        "host_nation_venue": True,
    },
    "AT&T Stadium": {
        "city": "Dallas", "country": "USA",
        "altitude_m": 198, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 33, "humidity_pct": 60,
        "weather_category": "extreme_heat", "weather_modifier": 0.94,
        "surface": "artificial_turf", "roof": "retractable", "capacity": 80000,
        "host_nation_venue": True,
    },
    "Mercedes-Benz Stadium": {
        "city": "Atlanta", "country": "USA",
        "altitude_m": 320, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 29, "humidity_pct": 70,
        "weather_category": "hot_humid", "weather_modifier": 0.96,
        "surface": "artificial_turf", "roof": "retractable", "capacity": 71000,
        "host_nation_venue": True,
    },
    "Hard Rock Stadium": {
        "city": "Miami", "country": "USA",
        "altitude_m": 3, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 31, "humidity_pct": 75,
        "weather_category": "hot_humid", "weather_modifier": 0.96,
        "surface": "natural_grass", "roof": "open", "capacity": 64767,
        "host_nation_venue": True,
    },
    "Levi's Stadium": {
        "city": "San Francisco", "country": "USA",
        "altitude_m": 15, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 22, "humidity_pct": 60,
        "weather_category": "cool_mild", "weather_modifier": 1.0,
        "surface": "natural_grass", "roof": "open", "capacity": 68500,
        "host_nation_venue": True,
    },
    "Lumen Field": {
        "city": "Seattle", "country": "USA",
        "altitude_m": 15, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 19, "humidity_pct": 65,
        "weather_category": "cool_mild", "weather_modifier": 1.0,
        "surface": "artificial_turf", "roof": "open", "capacity": 72000,
        "host_nation_venue": True,
    },
    "Gillette Stadium": {
        "city": "Boston", "country": "USA",
        "altitude_m": 26, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 23, "humidity_pct": 60,
        "weather_category": "mild", "weather_modifier": 1.0,
        "surface": "natural_grass", "roof": "open", "capacity": 65878,
        "host_nation_venue": True,
    },
    "Lincoln Financial Field": {
        "city": "Philadelphia", "country": "USA",
        "altitude_m": 12, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 27, "humidity_pct": 65,
        "weather_category": "warm_humid", "weather_modifier": 1.0,
        "surface": "natural_grass", "roof": "open", "capacity": 69796,
        "host_nation_venue": True,
    },
    "NRG Stadium": {
        "city": "Houston", "country": "USA",
        "altitude_m": 15, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 33, "humidity_pct": 70,
        "weather_category": "extreme_heat", "weather_modifier": 0.94,
        "surface": "artificial_turf", "roof": "retractable", "capacity": 72220,
        "host_nation_venue": True,
    },
    "BC Place": {
        "city": "Vancouver", "country": "Canada",
        "altitude_m": 5, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 20, "humidity_pct": 60,
        "weather_category": "cool_mild", "weather_modifier": 1.0,
        "surface": "artificial_turf", "roof": "fixed", "capacity": 54500,
        "host_nation_venue": True,
    },
    "BMO Field": {
        "city": "Toronto", "country": "Canada",
        "altitude_m": 76, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 24, "humidity_pct": 55,
        "weather_category": "mild", "weather_modifier": 1.0,
        "surface": "natural_grass", "roof": "open", "capacity": 30000,
        "host_nation_venue": True,
    },
    "Arrowhead Stadium": {
        "city": "Kansas City", "country": "USA",
        "altitude_m": 293, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 30, "humidity_pct": 65,
        "weather_category": "hot", "weather_modifier": 0.96,
        "surface": "natural_grass", "roof": "open", "capacity": 76416,
        "host_nation_venue": True,
    },
}


def get_team_data(team_name: str):
    """Get team data from database."""
    return TEAM_DB.get(team_name, {
        "rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5,
        "form": [0, 0, 0, 0, 0], "form_score": 5,
        "squad_depth": 5.0, "key_players": [],
        "formation": "4-3-3", "tactical_style": "balanced",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 0,
    })


def get_venue_data(venue_name: str):
    """Get venue data from database."""
    # Try exact match first
    if venue_name in VENUE_DB:
        return VENUE_DB[venue_name]
    
    # Try partial match
    for vname, vdata in VENUE_DB.items():
        if vname.lower() in venue_name.lower() or vdata["city"].lower() in venue_name.lower():
            return vdata
    
    # Default fallback
    return {
        "city": "Unknown", "country": "USA",
        "altitude_m": 100, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 22, "humidity_pct": 60,
        "weather_category": "mild", "weather_modifier": 1.0,
        "surface": "natural_grass", "roof": "open", "capacity": 50000,
        "host_nation_venue": True,
    }


def predict_match(match_id: str, home: str, away: str, predictor: EnsemblePredictor, venue: str = ""):
    """Run ensemble prediction for a match with H2H, injury, and venue data."""
    home_data = get_team_data(home)
    away_data = get_team_data(away)
    venue_data = get_venue_data(venue) if venue else get_venue_data("")
    
    # Get H2H and injury data from TEAM_DB
    h2h = home_data.get("h2h", {})
    h2h_key = f"{away}"
    h2h_record = h2h.get(h2h_key, {"home_wins": 0, "draws": 0, "away_wins": 0})
    
    result = predictor.predict(
        home_team=home,
        away_team=away,
        home_rank=home_data["rank"],
        away_rank=away_data["rank"],
        home_elo=home_data.get("elo", 1800),
        away_elo=away_data.get("elo", 1800),
        home_xg=home_data["xg"],
        home_xga=home_data["xga"],
        away_xg=away_data["xg"],
        away_xga=away_data["xga"],
        home_form=home_data["form"],
        away_form=away_data["form"],
        h2h_home_wins=h2h_record["home_wins"],
        h2h_draws=h2h_record["draws"],
        h2h_away_wins=h2h_record["away_wins"],
        home_injuries=home_data.get("injuries", 0),
        away_injuries=away_data.get("injuries", 0),
        home_squad_depth=home_data.get("squad_depth", 5.0),
        away_squad_depth=away_data.get("squad_depth", 5.0),
        knockout=True,
        altitude_m=venue_data.get("altitude_m", 0),
        temperature_c=venue_data.get("avg_temp_c", 20),
    )
    
    binary = result.to_binary()
    
    return {
        "match_id": match_id,
        "home": home,
        "away": away,
        "home_prob": binary[0],
        "away_prob": binary[1],
        "score": result.most_likely_score,
        "confidence": result.confidence,
        "components": result.ensemble_components,
    }


def submit_prediction(match_id: str, home_prob: float, away_prob: float, score: str, 
                       dry_run: bool, home: str = "", away: str = "", 
                       components: dict = None, round_name: str = "", weight: float = 1.0):
    """Submit prediction to ClawCup API and log it."""
    if dry_run:
        print(f"  🚫 DRY RUN — Would submit: {match_id} — {home_prob:.2f} / {away_prob:.2f}")
        return True
    
    try:
        api_request("POST", "/predictions", {
            "match_id": match_id,
            "format": "binary",
            "p": [round(home_prob, 2), round(away_prob, 2)],
            "reasoning": f"Ensemble model: ELO + xG + Form + H2H + Squad Depth + Venue",
            "score": score,
        })
        print(f"  ✅ Submitted: {match_id}")
        
        # Log the prediction
        logger.log_prediction(
            match_id=match_id,
            home_team=home,
            away_team=away,
            submitted_probs=[round(home_prob, 2), round(away_prob, 2)],
            components=components or {},
            predicted_score=score,
            reasoning="Ensemble model: ELO + xG + Form + H2H + Squad Depth + Venue",
            round_name=round_name,
            weight=weight,
        )
        
        return True
    except Exception as e:
        print(f"  ❌ Failed: {match_id} — {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Batch ensemble predictions")
    parser.add_argument("--dry-run", action="store_true", help="Preview without submitting")
    parser.add_argument("--live", action="store_true", help="Actually submit")
    
    args = parser.parse_args()
    
    dry_run = not args.live
    
    print("=" * 70)
    print("BATCH ENSEMBLE PREDICTIONS")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    # Get open fixtures
    try:
        data = api_request("GET", "/fixtures?status=open")
        matches = data.get("matches", [])
    except Exception as e:
        print(f"Error fetching fixtures: {e}")
        return
    
    if not matches:
        print("No open fixtures found")
        return
    
    print(f"Found {len(matches)} open matches")
    print()
    
    predictor = EnsemblePredictor()
    
    for match in matches:
        match_id = match["match_id"]
        home = match.get("home", "?")
        away = match.get("away", "?")
        venue = match.get("venue", "")
        
        print(f"Predicting {match_id}: {home} vs {away}")
        if venue:
            print(f"  Venue: {venue}")
        
        result = predict_match(match_id, home, away, predictor, venue)
        
        print(f"  Prediction: {home} {result['home_prob']:.0%} vs {away} {result['away_prob']:.0%}")
        print(f"  Score: {result['score']}")
        print(f"  Confidence: {result['confidence']:.0%}")
        
        # Submit
        submit_prediction(
            match_id=match_id,
            home_prob=result["home_prob"],
            away_prob=result["away_prob"],
            score=result["score"],
            dry_run=dry_run,
            home=home,
            away=away,
            components=result["components"],
        )
        
        print()
    
    print("=" * 70)
    print("Batch predictions complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
