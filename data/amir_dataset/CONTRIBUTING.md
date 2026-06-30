# Contributing to AI Football Prediction Engine — World Cup 2026

Thank you for your interest in contributing! This project is open-source and welcomes contributions of all kinds — from data corrections to new features.

---

## 🚀 Quick Start for Contributors

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-football-prediction-engine-world-cup-2026.git
   cd ai-football-prediction-engine-world-cup-2026
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Create a branch** for your change:
   ```bash
   git checkout -b feature/your-feature-name
   ```
5. Make your changes, then **commit** and **push**:
   ```bash
   git add .
   git commit -m "feat: describe your change"
   git push origin feature/your-feature-name
   ```
6. Open a **Pull Request** against `main`

---

## 📋 Ways to Contribute

### 1. Update Team Data (`data/teams.json`)
As the World Cup approaches, FIFA rankings, ELO ratings, form, and squad information change. To update a team:

- Find the team's object in `data/teams.json`
- Update fields like `fifa_rank`, `elo_rating`, `xg_for_avg`, `form_last5`, `key_players`
- Recalculate `tsi` using `engine/tsi_calculator.py`:
  ```bash
  python engine/tsi_calculator.py
  ```
- Keep `form_last5` as exactly 5 entries: `"W"`, `"D"`, or `"L"`

### 2. Update Venue Data (`data/venues.json`)
If altitude, weather averages, or stage assignments need correction, edit the relevant venue object. Keep `altitude_category` consistent with `altitude_meters`:

| Category | Range |
|----------|-------|
| `low` | < 500m |
| `medium` | 500–1499m |
| `high` | 1500–2199m |
| `extreme` | ≥ 2200m |

### 3. Add Example Predictions (`examples/`)
New examples are always welcome! Good candidates:
- A specific upset scenario (TSI gap < 8)
- A host-nation match with crowd factor
- A "Group of Death" fatigue scenario
- Final-stage predictions

Follow the format in existing `examples/example-*.md` files.

### 4. Improve the Engine (`engine/`)
Possible improvements:
- More sophisticated fatigue modeling (travel distance, timezone shifts)
- Head-to-head historical data integration
- Injury-adjusted xG calculations
- Performance optimization for Monte Carlo simulations

All engine changes should include a runnable demo in the `if __name__ == "__main__":` block.

### 5. Build a Web Interface
We'd love a Streamlit or Gradio front-end! If you build one:
- Place it in a new `webapp/` directory
- Include clear setup instructions in a `webapp/README.md`
- Don't hardcode API keys — use environment variables

### 6. Documentation & Translations
- Fix typos, clarify instructions
- Translate `README.md` or the system prompt into other languages (place in `system-prompt/translations/`)

---

## 🧪 Testing Your Changes

Before submitting a PR, run the engine demos to make sure nothing is broken:

```bash
python engine/tsi_calculator.py
python engine/poisson_model.py
python engine/monte_carlo.py
```

If you add new functions, consider adding tests under a `tests/` directory using `pytest`.

---

## 📝 Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use for |
|--------|---------|
| `feat:` | New features |
| `fix:` | Bug fixes |
| `docs:` | Documentation changes |
| `data:` | Dataset updates (teams.json, venues.json) |
| `refactor:` | Code restructuring without behavior change |
| `chore:` | Maintenance tasks (dependencies, configs) |

Example: `data: update Brazil squad after injury to key player`

---

## ⚠️ Data Accuracy Guidelines

- Cite your source when updating statistics (in the PR description)
- FIFA rankings: use the official [FIFA/Coca-Cola World Ranking](https://www.fifa.com/fifa-world-ranking)
- xG data: prefer Opta, FBref, or Understat
- Avoid speculative data — if uncertain, leave a `// TODO` comment explaining what needs verification

---

## 🤝 Code of Conduct

- Be respectful and constructive in discussions
- Focus on football analytics, not personal opinions about teams/players
- This is a model for **simulation and educational purposes** — keep contributions aligned with that spirit

---

## ❓ Questions?

Open an [Issue](https://github.com/AmirMotefaker/ai-football-prediction-engine-world-cup-2026/issues) with the `question` label.

Thank you for helping make this the best open-source World Cup prediction tool! ⚽
