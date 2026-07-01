import json
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wc26_bnaul.json_db import save_json_db

def migrate_teams_to_json():
    """Migrate hardcoded TEAM_DB to teams_db.json"""
    
    # This is the full TEAM_DB data from batch_predict.py
    # Converted to the new JSON format with proper structure
    
    teams = {
        "Argentina": {
            "fifa_rank": 1,
            "elo_rating": 2031,
            "confederation": "CONMEBOL",
            "host_nation": False,
            "squad_depth_score": 9.2,
            "xg": 2.09,
            "xga": 0.88,
            "form": [1, 1, 1, 0, 1],
            "injuries": 0,
            "coach": {
                "name": "Lionel Scaloni",
                "preferred_formation": "4-3-3",
                "tactical_style": "possession_attacking"
            },
            "key_players": [
                {"name": "Messi", "position": "FW", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Alvarez", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Enzo", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Martinez", "position": "DF", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Brazil": {"home_wins": 2, "draws": 1, "away_wins": 1},
                "France": {"home_wins": 1, "draws": 1, "away_wins": 2},
                "England": {"home_wins": 1, "draws": 0, "away_wins": 1}
            }
        },
        "France": {
            "fifa_rank": 2,
            "elo_rating": 2045,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 9.5,
            "xg": 2.31,
            "xga": 0.85,
            "form": [1, 0, 1, 1, 1],
            "injuries": 1,
            "coach": {
                "name": "Didier Deschamps",
                "preferred_formation": "4-2-3-1",
                "tactical_style": "balanced_counter"
            },
            "key_players": [
                {"name": "Mbappe", "position": "FW", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Griezmann", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Tchouameni", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Upamecano", "position": "DF", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Argentina": {"home_wins": 2, "draws": 1, "away_wins": 1},
                "Germany": {"home_wins": 1, "draws": 1, "away_wins": 1},
                "Belgium": {"home_wins": 2, "draws": 0, "away_wins": 0},
                "Sweden": {"home_wins": 1, "draws": 0, "away_wins": 0}
            }
        },
        "Brazil": {
            "fifa_rank": 3,
            "elo_rating": 2008,
            "confederation": "CONMEBOL",
            "host_nation": False,
            "squad_depth_score": 9.3,
            "xg": 2.28,
            "xga": 1.02,
            "form": [1, 1, 1, -1, 1],
            "injuries": 0,
            "coach": {
                "name": "Dorival Júnior",
                "preferred_formation": "4-2-3-1",
                "tactical_style": "attacking_flair"
            },
            "key_players": [
                {"name": "Vinicius Jr", "position": "FW", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Rodrygo", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Casemiro", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Alisson", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Argentina": {"home_wins": 1, "draws": 1, "away_wins": 2},
                "Germany": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "Croatia": {"home_wins": 1, "draws": 0, "away_wins": 1},
                "Japan": {"home_wins": 2, "draws": 0, "away_wins": 0}
            }
        },
        "England": {
            "fifa_rank": 4,
            "elo_rating": 2019,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 9.1,
            "xg": 2.02,
            "xga": 0.95,
            "form": [1, 1, 1, 0, 1],
            "injuries": 2,
            "coach": {
                "name": "Thomas Tuchel",
                "preferred_formation": "4-2-3-1",
                "tactical_style": "direct_attacking"
            },
            "key_players": [
                {"name": "Kane", "position": "FW", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Bellingham", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Foden", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Rice", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "France": {"home_wins": 1, "draws": 0, "away_wins": 1},
                "Germany": {"home_wins": 1, "draws": 1, "away_wins": 1},
                "Spain": {"home_wins": 0, "draws": 1, "away_wins": 2}
            }
        },
        "Spain": {
            "fifa_rank": 5,
            "elo_rating": 2038,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 9.4,
            "xg": 2.18,
            "xga": 0.82,
            "form": [1, 0, 1, 1, 0],
            "injuries": 1,
            "coach": {
                "name": "Luis de la Fuente",
                "preferred_formation": "4-3-3",
                "tactical_style": "possession_technical"
            },
            "key_players": [
                {"name": "Yamal", "position": "FW", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Williams", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Rodri", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Morata", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Germany": {"home_wins": 2, "draws": 0, "away_wins": 1},
                "England": {"home_wins": 2, "draws": 1, "away_wins": 0},
                "Italy": {"home_wins": 1, "draws": 1, "away_wins": 1}
            }
        },
        "Germany": {
            "fifa_rank": 6,
            "elo_rating": 1975,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 8.8,
            "xg": 1.92,
            "xga": 1.08,
            "form": [0, 1, 0, 1, -1],
            "injuries": 3,
            "coach": {
                "name": "Julian Nagelsmann",
                "preferred_formation": "4-2-3-1",
                "tactical_style": "high_press_attacking"
            },
            "key_players": [
                {"name": "Musiala", "position": "MF", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Wirtz", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Kimmich", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Neuer", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "France": {"home_wins": 1, "draws": 1, "away_wins": 1},
                "Brazil": {"home_wins": 2, "draws": 0, "away_wins": 0},
                "Spain": {"home_wins": 1, "draws": 0, "away_wins": 2},
                "Paraguay": {"home_wins": 0, "draws": 2, "away_wins": 0}
            }
        },
        "Portugal": {
            "fifa_rank": 7,
            "elo_rating": 2011,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 8.9,
            "xg": 2.14,
            "xga": 0.92,
            "form": [1, 1, 0, 1, 0],
            "injuries": 1,
            "coach": {
                "name": "Roberto Martínez",
                "preferred_formation": "4-3-3",
                "tactical_style": "balanced_attacking"
            },
            "key_players": [
                {"name": "Ronaldo", "position": "FW", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Felix", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Silva", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Dias", "position": "DF", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Spain": {"home_wins": 0, "draws": 1, "away_wins": 2},
                "France": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "Switzerland": {"home_wins": 1, "draws": 1, "away_wins": 0}
            }
        },
        "Netherlands": {
            "fifa_rank": 8,
            "elo_rating": 1998,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 8.7,
            "xg": 1.97,
            "xga": 0.95,
            "form": [1, 0, 1, -1, -1],
            "injuries": 2,
            "coach": {
                "name": "Ronald Koeman",
                "preferred_formation": "3-4-1-2",
                "tactical_style": "organized_attacking"
            },
            "key_players": [
                {"name": "Gakpo", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Depay", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "De Jong", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Van Dijk", "position": "DF", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Argentina": {"home_wins": 0, "draws": 1, "away_wins": 2},
                "Spain": {"home_wins": 1, "draws": 0, "away_wins": 1},
                "Germany": {"home_wins": 1, "draws": 1, "away_wins": 1},
                "Morocco": {"home_wins": 0, "draws": 0, "away_wins": 1}
            }
        },
        "Belgium": {
            "fifa_rank": 9,
            "elo_rating": 1979,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 8.3,
            "xg": 1.88,
            "xga": 1.05,
            "form": [0, 1, 1, 0, 1],
            "injuries": 1,
            "coach": {
                "name": "Domenico Tedesco",
                "preferred_formation": "3-4-2-1",
                "tactical_style": "possession_attacking"
            },
            "key_players": [
                {"name": "De Bruyne", "position": "MF", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Lukaku", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Tielemans", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Courtois", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "France": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "England": {"home_wins": 0, "draws": 1, "away_wins": 1},
                "Netherlands": {"home_wins": 1, "draws": 0, "away_wins": 1}
            }
        },
        "Italy": {
            "fifa_rank": 10,
            "elo_rating": 1962,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 8.2,
            "xg": 1.75,
            "xga": 0.92,
            "form": [1, 0, 1, 0, 1],
            "injuries": 2,
            "coach": {
                "name": "Luciano Spalletti",
                "preferred_formation": "4-3-3",
                "tactical_style": "organized_defensive"
            },
            "key_players": [
                {"name": "Barella", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Chiesa", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Immobile", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Donnarumma", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Spain": {"home_wins": 1, "draws": 1, "away_wins": 1},
                "Germany": {"home_wins": 1, "draws": 1, "away_wins": 1},
                "England": {"home_wins": 1, "draws": 0, "away_wins": 1}
            }
        },
        "USA": {
            "fifa_rank": 11,
            "elo_rating": 1928,
            "confederation": "CONCACAF",
            "host_nation": True,
            "squad_depth_score": 7.5,
            "xg": 1.62,
            "xga": 1.22,
            "form": [1, 0, 1, 1, 0],
            "injuries": 1,
            "coach": {
                "name": "Gregg Berhalter",
                "preferred_formation": "4-3-3",
                "tactical_style": "high_energy_press"
            },
            "key_players": [
                {"name": "Pulisic", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Reyna", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Adams", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Turner", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Mexico": {"home_wins": 2, "draws": 1, "away_wins": 0},
                "Canada": {"home_wins": 2, "draws": 0, "away_wins": 0}
            }
        },
        "Mexico": {
            "fifa_rank": 12,
            "elo_rating": 1932,
            "confederation": "CONCACAF",
            "host_nation": True,
            "squad_depth_score": 7.6,
            "xg": 1.59,
            "xga": 1.18,
            "form": [1, 1, 1, 0, 0],
            "injuries": 2,
            "coach": {
                "name": "Jaime Lozano",
                "preferred_formation": "4-3-3",
                "tactical_style": "organized_defensive"
            },
            "key_players": [
                {"name": "Alvarez", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Antuna", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Herrera", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Ochoa", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "USA": {"home_wins": 0, "draws": 1, "away_wins": 2},
                "Ecuador": {"home_wins": 2, "draws": 1, "away_wins": 0}
            }
        },
        "Morocco": {
            "fifa_rank": 13,
            "elo_rating": 1985,
            "confederation": "CAF",
            "host_nation": False,
            "squad_depth_score": 8.5,
            "xg": 1.62,
            "xga": 0.88,
            "form": [1, 0, 1, 0, 1],
            "injuries": 0,
            "coach": {
                "name": "Walid Regragui",
                "preferred_formation": "4-3-3",
                "tactical_style": "low_block_counter"
            },
            "key_players": [
                {"name": "Hakimi", "position": "DF", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "En-Nesyri", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Ounahi", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Bounou", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Spain": {"home_wins": 1, "draws": 0, "away_wins": 1},
                "Portugal": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "Netherlands": {"home_wins": 1, "draws": 0, "away_wins": 0}
            }
        },
        "Switzerland": {
            "fifa_rank": 14,
            "elo_rating": 1910,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 7.3,
            "xg": 1.58,
            "xga": 1.08,
            "form": [0, 1, 1, 0, 0],
            "injuries": 1,
            "coach": {
                "name": "Murat Yakin",
                "preferred_formation": "4-2-3-1",
                "tactical_style": "organized_balanced"
            },
            "key_players": [
                {"name": "Xhaka", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Embolo", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Sommer", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Freuler", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "France": {"home_wins": 0, "draws": 1, "away_wins": 2},
                "Portugal": {"home_wins": 0, "draws": 1, "away_wins": 1}
            }
        },
        "Croatia": {
            "fifa_rank": 15,
            "elo_rating": 1895,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 7.1,
            "xg": 1.45,
            "xga": 1.12,
            "form": [0, 1, 0, 1, 0],
            "injuries": 3,
            "coach": {
                "name": "Zlatko Dalic",
                "preferred_formation": "4-3-3",
                "tactical_style": "possession_technical"
            },
            "key_players": [
                {"name": "Modric", "position": "MF", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Kovacic", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Perisic", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Livakovic", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Brazil": {"home_wins": 1, "draws": 0, "away_wins": 1},
                "Argentina": {"home_wins": 0, "draws": 1, "away_wins": 2}
            }
        },
        "Japan": {
            "fifa_rank": 16,
            "elo_rating": 1885,
            "confederation": "AFC",
            "host_nation": False,
            "squad_depth_score": 7.0,
            "xg": 1.42,
            "xga": 1.15,
            "form": [0, 0, 1, 1, -1],
            "injuries": 0,
            "coach": {
                "name": "Hajime Moriyasu",
                "preferred_formation": "4-2-3-1",
                "tactical_style": "organized_counter"
            },
            "key_players": [
                {"name": "Kubo", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Mitoma", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Endo", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Gonda", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Germany": {"home_wins": 1, "draws": 0, "away_wins": 1},
                "Spain": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "Brazil": {"home_wins": 0, "draws": 0, "away_wins": 1}
            }
        },
        "Colombia": {
            "fifa_rank": 17,
            "elo_rating": 1872,
            "confederation": "CONMEBOL",
            "host_nation": False,
            "squad_depth_score": 6.8,
            "xg": 1.55,
            "xga": 1.15,
            "form": [1, 0, 1, 1, 0],
            "injuries": 1,
            "coach": {
                "name": "Néstor Lorenzo",
                "preferred_formation": "4-3-3",
                "tactical_style": "attacking_flair"
            },
            "key_players": [
                {"name": "Diaz", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Rodriguez", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Cuadrado", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Ospina", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Brazil": {"home_wins": 0, "draws": 1, "away_wins": 2},
                "Argentina": {"home_wins": 0, "draws": 0, "away_wins": 2}
            }
        },
        "Senegal": {
            "fifa_rank": 18,
            "elo_rating": 1862,
            "confederation": "CAF",
            "host_nation": False,
            "squad_depth_score": 6.7,
            "xg": 1.38,
            "xga": 1.22,
            "form": [1, 1, 0, 0, 1],
            "injuries": 0,
            "coach": {
                "name": "Aliou Cissé",
                "preferred_formation": "4-3-3",
                "tactical_style": "fast_athletic"
            },
            "key_players": [
                {"name": "Mane", "position": "FW", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Sarr", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Koulibaly", "position": "DF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Mendy", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Netherlands": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "England": {"home_wins": 0, "draws": 0, "away_wins": 1}
            }
        },
        "Sweden": {
            "fifa_rank": 19,
            "elo_rating": 1845,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 6.5,
            "xg": 1.35,
            "xga": 1.25,
            "form": [0, 0, 1, 1, -1],
            "injuries": 2,
            "coach": {
                "name": "Janne Andersson",
                "preferred_formation": "4-4-2",
                "tactical_style": "organized_counter"
            },
            "key_players": [
                {"name": "Isak", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Kulusevski", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Lindlov", "position": "DF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Olsen", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Germany": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "England": {"home_wins": 0, "draws": 1, "away_wins": 1},
                "France": {"home_wins": 0, "draws": 0, "away_wins": 1}
            }
        },
        "Uruguay": {
            "fifa_rank": 20,
            "elo_rating": 1855,
            "confederation": "CONMEBOL",
            "host_nation": False,
            "squad_depth_score": 6.6,
            "xg": 1.42,
            "xga": 1.18,
            "form": [1, 0, 1, 0, 0],
            "injuries": 1,
            "coach": {
                "name": "Marcelo Bielsa",
                "preferred_formation": "4-4-2",
                "tactical_style": "direct_physical"
            },
            "key_players": [
                {"name": "Nunez", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Valverde", "position": "MF", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Araujo", "position": "DF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Rochet", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Argentina": {"home_wins": 1, "draws": 0, "away_wins": 2},
                "Brazil": {"home_wins": 0, "draws": 1, "away_wins": 2}
            }
        },
        "Ecuador": {
            "fifa_rank": 21,
            "elo_rating": 1832,
            "confederation": "CONMEBOL",
            "host_nation": False,
            "squad_depth_score": 6.4,
            "xg": 1.38,
            "xga": 1.28,
            "form": [-1, 1, 0, 1, 0],
            "injuries": 1,
            "coach": {
                "name": "Félix Sánchez",
                "preferred_formation": "4-3-3",
                "tactical_style": "fast_athletic"
            },
            "key_players": [
                {"name": "Caicedo", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Valencia", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Estupinan", "position": "DF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Dominguez", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Mexico": {"home_wins": 0, "draws": 1, "away_wins": 1},
                "Argentina": {"home_wins": 0, "draws": 0, "away_wins": 2}
            }
        },
        "Australia": {
            "fifa_rank": 22,
            "elo_rating": 1865,
            "confederation": "AFC",
            "host_nation": False,
            "squad_depth_score": 6.6,
            "xg": 1.29,
            "xga": 1.21,
            "form": [1, 0, 1, 0, 0],
            "injuries": 1,
            "coach": {
                "name": "Graham Arnold",
                "preferred_formation": "4-4-2",
                "tactical_style": "organized_pragmatic"
            },
            "key_players": [
                {"name": "Leckie", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Irvine", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Redmayne", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "McGree", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Japan": {"home_wins": 0, "draws": 1, "away_wins": 1},
                "England": {"home_wins": 0, "draws": 0, "away_wins": 1}
            }
        },
        "Austria": {
            "fifa_rank": 23,
            "elo_rating": 1828,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 6.2,
            "xg": 1.45,
            "xga": 1.18,
            "form": [1, 0, 0, 1, 1],
            "injuries": 2,
            "coach": {
                "name": "Ralf Rangnick",
                "preferred_formation": "4-2-3-1",
                "tactical_style": "organized_counter"
            },
            "key_players": [
                {"name": "Arnautovic", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Sabitzer", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Alaba", "position": "DF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Lindner", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Germany": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "Spain": {"home_wins": 0, "draws": 0, "away_wins": 2}
            }
        },
        "Canada": {
            "fifa_rank": 24,
            "elo_rating": 1851,
            "confederation": "CONCACAF",
            "host_nation": True,
            "squad_depth_score": 7.2,
            "xg": 1.45,
            "xga": 1.28,
            "form": [1, 1, 0, 0, 0],
            "injuries": 1,
            "coach": {
                "name": "Jesse Marsch",
                "preferred_formation": "4-3-3",
                "tactical_style": "direct_attacking"
            },
            "key_players": [
                {"name": "Davies", "position": "DF", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "David", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Buchanan", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Borjan", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "USA": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "Mexico": {"home_wins": 0, "draws": 0, "away_wins": 2}
            }
        },
        "Algeria": {
            "fifa_rank": 25,
            "elo_rating": 1798,
            "confederation": "CAF",
            "host_nation": False,
            "squad_depth_score": 5.9,
            "xg": 1.22,
            "xga": 1.35,
            "form": [0, 1, 0, 0, 1],
            "injuries": 0,
            "coach": {
                "name": "Djamel Belmadi",
                "preferred_formation": "4-3-3",
                "tactical_style": "fast_athletic"
            },
            "key_players": [
                {"name": "Mahrez", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Bennacer", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Slimani", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Mbolhi", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "France": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "Germany": {"home_wins": 0, "draws": 0, "away_wins": 1}
            }
        },
        "Egypt": {
            "fifa_rank": 26,
            "elo_rating": 1805,
            "confederation": "CAF",
            "host_nation": False,
            "squad_depth_score": 6.0,
            "xg": 1.25,
            "xga": 1.32,
            "form": [1, 0, 0, 1, 0],
            "injuries": 1,
            "coach": {
                "name": "Hossam Hassan",
                "preferred_formation": "4-2-3-1",
                "tactical_style": "organized_counter"
            },
            "key_players": [
                {"name": "Salah", "position": "FW", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Elneny", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Trezequet", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "El Shenawy", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Spain": {"home_wins": 0, "draws": 0, "away_wins": 1},
                "Portugal": {"home_wins": 0, "draws": 0, "away_wins": 1}
            }
        },
        "Norway": {
            "fifa_rank": 27,
            "elo_rating": 1815,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 6.1,
            "xg": 1.38,
            "xga": 1.28,
            "form": [1, 0, 1, 0, 1],
            "injuries": 2,
            "coach": {
                "name": "Ståle Solbakken",
                "preferred_formation": "4-3-3",
                "tactical_style": "direct_attacking"
            },
            "key_players": [
                {"name": "Haaland", "position": "FW", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Odegaard", "position": "MF", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Hauge", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Nyland", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Sweden": {"home_wins": 1, "draws": 0, "away_wins": 1},
                "England": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "Ivory Coast": {"home_wins": 1, "draws": 0, "away_wins": 0}
            }
        },
        "Paraguay": {
            "fifa_rank": 28,
            "elo_rating": 1815,
            "confederation": "CONMEBOL",
            "host_nation": False,
            "squad_depth_score": 6.1,
            "xg": 1.22,
            "xga": 1.21,
            "form": [1, 0, 1, 0, 1],
            "injuries": 1,
            "coach": {
                "name": "Daniel Garnero",
                "preferred_formation": "4-4-2",
                "tactical_style": "defensive_organized"
            },
            "key_players": [
                {"name": "Almiron", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Sanabria", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Gomez", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Silva", "position": "DF", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Brazil": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "Argentina": {"home_wins": 0, "draws": 1, "away_wins": 2},
                "Germany": {"home_wins": 0, "draws": 1, "away_wins": 0}
            }
        },
        "Ivory Coast": {
            "fifa_rank": 29,
            "elo_rating": 1788,
            "confederation": "CAF",
            "host_nation": False,
            "squad_depth_score": 5.8,
            "xg": 1.18,
            "xga": 1.38,
            "form": [0, 1, 0, 1, -1],
            "injuries": 0,
            "coach": {
                "name": "Emerse Faé",
                "preferred_formation": "4-3-3",
                "tactical_style": "fast_athletic"
            },
            "key_players": [
                {"name": "Zaha", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Haller", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Kessie", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Sangare", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "France": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "England": {"home_wins": 0, "draws": 0, "away_wins": 1},
                "Norway": {"home_wins": 0, "draws": 0, "away_wins": 1}
            }
        },
        "Bosnia & Herzegovina": {
            "fifa_rank": 30,
            "elo_rating": 1782,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 5.8,
            "xg": 1.15,
            "xga": 1.42,
            "form": [0, 0, 1, 0, 1],
            "injuries": 2,
            "coach": {
                "name": "Sergej Barbarez",
                "preferred_formation": "4-3-3",
                "tactical_style": "direct_physical"
            },
            "key_players": [
                {"name": "Dzeko", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Pjanic", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Tatar", "position": "DF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Sehic", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Germany": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "Spain": {"home_wins": 0, "draws": 0, "away_wins": 2}
            }
        },
        "Ghana": {
            "fifa_rank": 45,
            "elo_rating": 1762,
            "confederation": "CAF",
            "host_nation": False,
            "squad_depth_score": 5.5,
            "xg": 1.05,
            "xga": 1.45,
            "form": [0, 1, 0, 0, 1],
            "injuries": 1,
            "coach": {
                "name": "Chris Hughton",
                "preferred_formation": "4-3-3",
                "tactical_style": "fast_athletic"
            },
            "key_players": [
                {"name": "Kudus", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Partey", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Williams", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Ati-Zigi", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Portugal": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "Spain": {"home_wins": 0, "draws": 0, "away_wins": 1}
            }
        },
        "DR Congo": {
            "fifa_rank": 55,
            "elo_rating": 1728,
            "confederation": "CAF",
            "host_nation": False,
            "squad_depth_score": 5.1,
            "xg": 0.95,
            "xga": 1.52,
            "form": [0, 1, 0, 0, 0],
            "injuries": 0,
            "coach": {
                "name": "Sébastien Desabre",
                "preferred_formation": "4-3-3",
                "tactical_style": "organized_counter"
            },
            "key_players": [
                {"name": "Bakambu", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Meschak", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Muke", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Mandanda", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "France": {"home_wins": 0, "draws": 0, "away_wins": 1},
                "England": {"home_wins": 0, "draws": 0, "away_wins": 1}
            }
        },
        "Cape Verde": {
            "fifa_rank": 65,
            "elo_rating": 1731,
            "confederation": "CAF",
            "host_nation": False,
            "squad_depth_score": 5.0,
            "xg": 0.92,
            "xga": 1.55,
            "form": [0, 0, 1, 0, 0],
            "injuries": 0,
            "coach": {
                "name": "Bubista",
                "preferred_formation": "4-3-3",
                "tactical_style": "compact_organized"
            },
            "key_players": [
                {"name": "Andrade", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Fortes", "position": "DF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Soares", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Vozinha", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {
                "Portugal": {"home_wins": 0, "draws": 0, "away_wins": 2},
                "Spain": {"home_wins": 0, "draws": 0, "away_wins": 2}
            }
        },
        "Turkey": {
            "fifa_rank": 34,
            "elo_rating": 1828,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 6.2,
            "xg": 1.45,
            "xga": 1.32,
            "form": [1, 1, 0, 1, 0],
            "injuries": 0,
            "coach": {
                "name": "Vincenzo Montella",
                "preferred_formation": "4-2-3-1",
                "tactical_style": "attacking_balanced"
            },
            "key_players": [
                {"name": "Calhanoglu", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Yildiz", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Guler", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Gunok", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {}
        },
        "Czech Republic": {
            "fifa_rank": 39,
            "elo_rating": 1812,
            "confederation": "UEFA",
            "host_nation": False,
            "squad_depth_score": 6.2,
            "xg": 1.35,
            "xga": 1.28,
            "form": [1, 0, 1, 0, 0],
            "injuries": 0,
            "coach": {
                "name": "Ivan Hasek",
                "preferred_formation": "4-2-3-1",
                "tactical_style": "organized_counter"
            },
            "key_players": [
                {"name": "Schick", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Soucek", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Kuchta", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Vaclik", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {}
        },
        "South Korea": {
            "fifa_rank": 25,
            "elo_rating": 1878,
            "confederation": "AFC",
            "host_nation": False,
            "squad_depth_score": 6.8,
            "xg": 1.38,
            "xga": 1.19,
            "form": [1, 0, 1, 0, 0],
            "injuries": 0,
            "coach": {
                "name": "Jürgen Klinsmann",
                "preferred_formation": "4-4-2",
                "tactical_style": "high_work_rate"
            },
            "key_players": [
                {"name": "Son", "position": "FW", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Hwang", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Kim Min-jae", "position": "DF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Lee Jae-sung", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {}
        },
        "Nigeria": {
            "fifa_rank": 35,
            "elo_rating": 1822,
            "confederation": "CAF",
            "host_nation": False,
            "squad_depth_score": 6.3,
            "xg": 1.41,
            "xga": 1.28,
            "form": [0, 1, 1, 0, 1],
            "injuries": 0,
            "coach": {
                "name": "Finidi George",
                "preferred_formation": "4-3-3",
                "tactical_style": "fast_athletic"
            },
            "key_players": [
                {"name": "Osimhen", "position": "FW", "season_rating": 8.5, "is_injured": False, "is_suspended": False},
                {"name": "Lookman", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Iwobi", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Nwabali", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {}
        },
        "Qatar": {
            "fifa_rank": 53,
            "elo_rating": 1772,
            "confederation": "AFC",
            "host_nation": False,
            "squad_depth_score": 5.6,
            "xg": 1.09,
            "xga": 1.38,
            "form": [0, 1, 0, 0, 1],
            "injuries": 0,
            "coach": {
                "name": "Tintin Marquez",
                "preferred_formation": "4-3-3",
                "tactical_style": "possession_technical"
            },
            "key_players": [
                {"name": "Afif", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Ali", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Al-Haydos", "position": "MF", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Barsham", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {}
        },
        "South Africa": {
            "fifa_rank": 43,
            "elo_rating": 1789,
            "confederation": "CAF",
            "host_nation": False,
            "squad_depth_score": 5.8,
            "xg": 1.21,
            "xga": 1.42,
            "form": [0, 1, 0, 0, 1],
            "injuries": 0,
            "coach": {
                "name": "Hugo Broos",
                "preferred_formation": "4-3-3",
                "tactical_style": "organized_defensive"
            },
            "key_players": [
                {"name": "Percy Tau", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Dolly", "position": "FW", "season_rating": 7.5, "is_injured": False, "is_suspended": False},
                {"name": "Ronwen Williams", "position": "GK", "season_rating": 7.5, "is_injured": False, "is_suspended": False}
            ],
            "h2h": {}
        }
    }
    
    # Save to JSON
    save_json_db("teams_db.json", teams)
    print(f"✅ Migrated {len(teams)} teams to teams_db.json")


def migrate_venues_to_json():
    """Migrate hardcoded VENUE_DB to venues_db.json"""
    
    venues = {
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
        }
    }
    
    # Save to JSON
    save_json_db("venues_db.json", venues)
    print(f"✅ Migrated {len(venues)} venues to venues_db.json")


if __name__ == "__main__":
    print("Starting migration of hardcoded data to JSON...")
    print()
    
    migrate_teams_to_json()
    print()
    migrate_venues_to_json()
    
    print()
    print("=" * 60)
    print("Migration complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Verify data in data/teams_db.json and data/venues_db.json")
    print("2. Update batch_predict.py to use load_json_db() instead of hardcoded dicts")
    print("3. Remove TEAM_DB and VENUE_DB constants from batch_predict.py")
