[![GitHub repo size](https://img.shields.io/github/repo-size/amirmotefaker/ai-football-prediction-engine-world-cup-2026?style=flat-square&color=blue)](https://github.com/amirmotefaker/ai-football-prediction-engine-world-cup-2026)
[![GitHub stars](https://img.shields.io/github/stars/amirmotefaker/ai-football-prediction-engine-world-cup-2026?style=social)](https://github.com/amirmotefaker/ai-football-prediction-engine-world-cup-2026)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-Compatible-blue)](https://github.com/amirmottefaker/ai-football-prediction-engine-world-cup-2026)
[![AI](https://img.shields.io/badge/AI-Powered-green)](https://github.com/amirmottefaker/ai-football-prediction-engine-world-cup-2026)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)](https://github.com/amirmottefaker/ai-football-prediction-engine-world-cup-2026)

# ⚽ AI Football Prediction Engine - World Cup 2026

> A production-grade AI system for probabilistic football match prediction using statistical modeling, Poisson simulation, and tactical analysis — inspired by Opta & FiveThirtyEight. Built specifically for the **FIFA World Cup 2026**.

---

## 🎯 Features

- ✅ Match outcome probabilities (Win / Draw / Lose)
- ✅ Top 5 scoreline predictions via Monte Carlo simulation
- ✅ Tactical breakdown (formation clash, pressing, key duels)
- ✅ Environmental modifiers (altitude, weather, fatigue)
- ✅ Upset risk detection
- ✅ Team Strength Index (TSI) scoring
- ✅ Compatible with ChatGPT (GPT-4o) and OpenAI API

---

## 🚀 Quick Start

### Option A — Use the System Prompt directly (No code needed)

1. Open [`system-prompt/system_prompt_v2.md`](./system-prompt/system_prompt_v2.md)
2. Copy the full prompt
3. Paste as the **System** message in ChatGPT (GPT-4o recommended)
4. Send your match request in this format:

```
Predict: France vs Brazil
Stage: Semi-Final
Venue: MetLife Stadium, New Jersey
Date: 2026-07-14
Formation A: 4-3-3 | Formation B: 4-2-3-1
Key Absence A: none | Key Absence B: none
Days Rest: France 5 | Brazil 4
Weather: 26°C, partly cloudy
Altitude: 10m
```

### Option B — Use via Python (OpenAI API)

```bash
git clone https://github.com/AmirMotefaker/ai-football-prediction-engine-world-cup-2026.git
cd ai-football-prediction-engine-world-cup-2026
pip install -r requirements.txt
python api/predictor.py
```

---

## ⚙️ How It Works

The engine uses a 6-step hybrid pipeline:

| Step | Component | Description |
|------|-----------|-------------|
| 1 | **TSI Calculator** | Weighted team strength from FIFA rank, ELO, xG, form |
| 2 | **xG Model** | Bivariate Poisson with altitude, fatigue, weather modifiers |
| 3 | **Monte Carlo** | 10,000 match simulations → outcome probabilities |
| 4 | **Tactical Overlay** | Formation clash, pressing style, key duel analysis |
| 5 | **Context Engine** | Knockout pressure, H2H history, psychological factors |
| 6 | **Confidence Score** | Data quality rating + uncertainty quantification |

---

## 📁 Repository Structure

```
ai-football-prediction-engine-world-cup-2026/
├── system-prompt/
│   └── system_prompt_v2.md     ← Start here (AI prompt)
├── engine/
│   ├── poisson_model.py        ← xG + λ calculation
│   ├── monte_carlo.py          ← 10,000-iteration simulator
│   └── tsi_calculator.py       ← Team Strength Index
├── data/
│   ├── teams.json              ← 48 teams stats & ELO
│   └── venues.json             ← WC2026 venues + altitude
├── api/
│   └── predictor.py            ← OpenAI API integration
├── examples/
│   └── brazil-vs-argentina.md  ← Sample predictions
├── docs/
│   └── methodology.md          ← Technical documentation
├── requirements.txt
└── README.md
```

---

## 📊 Sample Output

```
🏟️  MATCH PREVIEW
Brazil vs Argentina | Semi-Final | MetLife Stadium | 2026-07-14

📊 TEAM STRENGTH
TSI — Brazil: 87.3 | Argentina: 84.1

🎯 PROBABILITIES
Brazil WIN:    48%  ████████░░
DRAW:          24%  ████░░░░░░
Argentina WIN: 28%  █████░░░░░

🔢 TOP SCORELINES
1-0  →  12.4%
1-1  →  10.8%
2-1  →   9.3%
0-0  →   7.1%
2-0  →   6.9%

⚠️  UPSET RISK: MEDIUM
Confidence: HIGH | Data Quality: ⭐⭐⭐⭐⭐
```

---

## 🧠 System Prompt Modes

Once you load the system prompt in ChatGPT, you can use these special commands:

| Command | Description |
|---------|-------------|
| `[TOURNAMENT MODE]` | Simulate the full WC2026 bracket from any stage |
| `[DEEP DIVE: Brazil]` | Full squad report, tactical identity, stage probabilities |
| `[UPSET SCANNER]` | Flag all high-risk matches in the upcoming matchday |
| `[COMPARE: Spain vs France]` | Head-to-head history + statistical comparison |
| `[WHAT-IF: Mbappe is injured]` | Re-run prediction with a hypothetical change |

---

## 📐 Prediction Methodology

### Team Strength Index (TSI)

| Component | Weight |
|-----------|--------|
| FIFA World Ranking (inverse-normalized) | 20% |
| ELO Rating | 25% |
| xG For (avg last 10 matches) | 15% |
| xG Against (avg last 10 matches) | 15% |
| Form Score (last 5 WC qualifiers) | 15% |
| Squad Depth & Availability | 10% |

### Environmental Modifiers

| Factor | Effect |
|--------|--------|
| Home nation (USA / Canada / Mexico) | +8% win probability |
| Altitude > 1500m | +5% xG variance |
| Altitude > 2200m | +12% xG variance |
| Rest < 3 days | −10% xG |
| Extreme heat > 32°C | −6% xG both teams |
| Knockout stage | −8% goal expectancy, +5% draw |

---

## 📁 Examples

See [`/examples/`](./examples/) for complete match prediction samples including:

- Group stage match (low-stakes, open play)
- Knockout match (high pressure, tactical)
- Upset scenario (TSI gap < 8 points)
- Host nation match (crowd factor applied)

---

## 🤝 Contributing

Contributions are welcome! Please read [`CONTRIBUTING.md`](./CONTRIBUTING.md) before submitting a pull request.

Areas where help is needed:

- Expanding the team dataset with more recent xG data
- Adding more example predictions
- Building a web interface (Streamlit / Gradio)
- Improving the Monte Carlo performance

---

## ⚠️ Disclaimer

This system is **probabilistic, not deterministic**.
Football contains inherent randomness — no model achieves 100% accuracy.
Designed for **simulation and analytical purposes only**.
Not financial or betting advice.

---

## 📜 License

MIT License — free to use, fork, and contribute.

---

## 👤 Author

**Amir Mottefaker**
Built with ❤️ for the football analytics community.

---

## 🔎 Keywords

football prediction AI · World Cup 2026 · sports analytics · probabilistic model · Poisson distribution · Monte Carlo simulation · xG model · tactical football analysis · prompt engineering · GPT-4o sports · open source
