def calculate_team_strength(form, squad, tactics, defense, external):
    return (
        form * 0.30 +
        squad * 0.25 +
        tactics * 0.20 +
        defense * 0.15 +
        external * 0.10
    )
