# wc26-bnaul — Research Log & Lessons Learned

Nhật ký nghiên cứu và những gì đã học được từ dự án ClawCup.

---

## 📅 Timeline

| Thời gian | Hoạt động | Kết quả |
|-----------|-----------|---------|
| 11:40 | Nhận token & secret từ user | `wca_fys30-...` + `wca_sec_GmHNtX...` |
| 11:41 | Tạo plan & folder `wc26-bnaul` | Plan approved |
| 11:42 | Viết `wc26_bnaul.py` CLI agent | HMAC signing + 4 commands |
| 11:46 | Test API — `me` & `fixtures` | Agent: `kinhluan-momo`, 15 matches predicted |
| 11:49 | Fix HMAC signing bug | Switch from `requests` to `urllib.request` |
| 11:51 | Submit 15/15 Round of 32 predictions | All binary knockout predictions submitted |
| 12:00 | Refactor to uv + pyproject.toml | Modern Python project setup |
| 12:06 | Push to GitHub | https://github.com/kinhluan/wc26-bnaul |
| 12:30 | Phân tích chiến thuật | STRATEGY.md — optimal play analysis |
| 13:00 | Viết edge_finder.py | 8 edge cases analyzed |
| 13:30 | Monte Carlo simulation (10,000 runs) | simulate.py — validate optimal strategy |
| 14:00 | Cross-validate với bookmaker industry | BOOKMAKER_VALIDATION.md |
| 14:12 | Tìm academic papers | IARPA, Gneiting 2007, Tetlock Superforecasting |
| 14:15 | Implement 3 tools mới | news_monitor, backtest, reasoning_analyzer |
| 14:20 | Cấu trúc lại project | src/, docs/, research/, tests/ |

---

## 🔬 Experiments & Results

### Experiment 1: Calibration Strategy Comparison

**Method:** Monte Carlo simulation, 10,000 runs, 31 knockout matches
**Variables:** 6 calibration strategies (truthful, over-confident, under-confident, max-confident, conservative, random)
**Metric:** Expected Skill%

| Strategy | Mean Skill% | vs Truthful | Verdict |
|----------|------------|-------------|---------|
| **Truthful** | **18.61%** | baseline | ✅ Optimal |
| Over-confident | 16.00% | -2.61% | ❌ Worse |
| Under-confident | 18.46% | -0.14% | ⚠️ Slightly worse |
| Max-confident | **-24.52%** | **-43.13%** | ❌❌ Catastrophic |
| Conservative | 6.40% | -12.21% | ❌ Worse |
| Random | -32.41% | -51.01% | ❌❌ Worst |

**Finding:** Truthful submission minimizes expected Brier. Mathematical proof: `d/dp E[Brier] = 2p - 2π = 0 → p = π`

### Experiment 2: Effort Allocation

**Method:** Same MC framework, 4 effort allocation strategies
**Variables:** uniform, early_focus, late_focus, optimal_weighted

| Allocation | Mean Skill% | Verdict |
|-----------|------------|---------|
| Uniform | 18.99% | ✅ Good |
| Early focus | 18.84% | ✅ Good |
| Late focus | 17.64% | ❌ Worse |
| Optimal weighted | 17.24% | ⚠️ Counter-intuitive |

**Finding:** Early rounds (Ro32+Ro16) = 66.7% total weight. Late focus underperforms despite high per-match weight due to variance.

### Experiment 3: Resubmit Value

**Method:** Vary info_quality from 0% to 100%
**Variables:** resubmit enabled/disabled, info quality

| Info Quality | Mean Skill% | Gain |
|-------------|------------|------|
| No resubmit | 19.04% | baseline |
| 0% (random) | 18.84% | -0.20% |
| 30% | 18.98% | +0.06% |
| 50% | 19.40% | **+0.36%** |
| 70% | 19.48% | **+0.44%** |
| 100% | 19.82% | **+0.78%** |

**Finding:** Resubmit value increases linearly with info quality. Even 30% info quality provides measurable improvement.

### Experiment 4: Historical Backtest (2014, 2018, 2022)

**Method:** 45 historical World Cup knockout matches
**Caveat:** Estimated true probabilities have hindsight bias

| Strategy | Skill% | Mean RPS | Accuracy |
|----------|--------|----------|----------|
| **over_confident** | **39.22%** | 0.1395 | 82.2% |
| truthful | 23.52% | 0.1837 | 77.8% |
| max_confident | 20.42% | 0.1743 | 82.2% |

**⚠️ SURPRISING:** Over-confident beats truthful on historical data!

**Explanation:**
- Hindsight bias in estimated probabilities
- Small sample (45 matches) → high variance
- Many favorites won in 2014-2022 → over-confidence "lucky"

**Lesson:** Historical backtest ≠ future performance. True probabilities unknowable ex-ante.

---

## 📚 Literature Review

### Papers Found

| Paper | Author | Year | Citations | Key Finding |
|-------|--------|------|-----------|-------------|
| Strictly Proper Scoring Rules | Gneiting & Raftery | 2007 | 8,317 | Brier is strictly proper; proof via convex analysis |
| IARPA ACE Tournament | Tetlock et al. | 2011-2015 | — | Brier score used in 4-year forecasting tournament |
| Superforecasting | Tetlock | 2015 | — | "Only way to game Brier is to report true probability" |
| Forecaster Evaluation | Merkle | 2021 | 1 | Model-based scoring for tournaments |
| Agentic Forecasting | Hsieh et al. | 2024 | — | RTF framework on Manifold Markets |
| Foresight Learning | Turtel et al. | 2026 | — | RL with proper scoring rewards |

### Industry Sources

| Source | Type | Key Insight |
|--------|------|-------------|
| GammaStack | Bookmaker tech | Overround = 105.1% for 5% margin |
| MyBookie | Sportsbook | Vig = hidden commission in odds |
| Sports-AI.dev | AI betting | Overconfidence corrupts edge calculations |
| MetricGate | ML metrics | Proper scoring rules cannot be gamed |

---

## 🧠 Key Insights & Lessons

### 1. Proper Scoring Rules are "Un-gameable"

> "A biased forecaster will perform worse in these metrics than an honest forecaster."
> — Merkle (2021)

**Lesson:** Không thể cheat Brier score. Chiến thuật duy nhất = truthful submission.

### 2. ClawCup ≠ Bookmaker

| | ClawCup | Bookmaker |
|--|---------|-----------|
| Goal | Calibration accuracy | Profit margin |
| Optimal | True probability | True prob + margin |
| Over-confidence | Punished | Irrelevant |

**Lesson:** Đây là 2 game khác nhau. Chiến thuật optimal cho ClawCup khác với cá cược.

### 3. Early Rounds Dominate Weight

| Round | Matches | Weight | Contribution |
|-------|---------|--------|-------------|
| Ro32 | 16 | 1× | 41.0% |
| Ro16 | 8 | 1.25× | 25.6% |
| QF+SF+Final | 7 | 1.5-3× | 33.3% |

**Lesson:** Tập trung calibrate tốt ở early rounds. Đừng "all-in" vào Final.

### 4. Resubmit = Information Advantage

**Lesson:** Gửi conservative sớm → monitor news → resubmit nếu có thông tin mới. Đây là feature hợp lệ, không phải exploit.

### 5. Historical Backtest ≠ Truth

**Lesson:** Hindsight bias làm over-confident trông tốt hơn. True probabilities không thể biết trước match. MC simulation đáng tin hơn backtest.

---

## 🛠️ Technical Lessons

### Python & uv

- **uv** nhanh hơn pip/conda rất nhiều
- `pyproject.toml` + `uv.lock` = reproducible environment
- `uv run` thay thế `source .venv/bin/activate`

### API Design

- HMAC signing với `urllib.request` ổn định hơn `requests` (tránh re-encoding)
- `sort_keys=True` trong JSON serialization = consistent signing
- Environment variables cho secrets (không hardcode)

### Git Workflow

- Commit message format: `type: description`
- Types: feat, fix, docs, research, test
- Push thường xuyên, không để code local quá lâu

---

## 🎯 What Worked Well

1. ✅ **Mathematical proof** → Simulation → Cross-validation (3-layer validation)
2. ✅ **Modular design** — mỗi file có 1 responsibility rõ ràng
3. ✅ **Documentation as code** — STRATEGY.md, RESEARCH_DESIGN.md
4. ✅ **Version control** — tất cả changes tracked, revertable

## ❌ What Could Be Better

1. ❌ **News monitor** — chưa integrate real APIs (placeholder)
2. ❌ **Backtest** — small sample, hindsight bias
3. ❌ **Reasoning analyzer** — chưa test với real ClawCup public API
4. ❌ **Tests** — chưa viết unit tests

---

## 🔮 Next Steps

1. **Integrate real news APIs** (NewsAPI, RSS, Twitter/X)
2. **Write unit tests** cho tất cả modules
3. **Collect more historical data** (World Cup 2010, 2006, 2002...)
4. **Monitor actual ClawCup results** và so sánh với predictions
5. **Publish findings** — blog post hoặc paper về optimal strategy in weighted RPS

---

## 📊 Final Stats

- **Lines of code:** ~2,500
- **Files created:** 15
- **Commits:** 5
- **Simulations run:** 10,000+ per config
- **Historical matches analyzed:** 45
- **Edge cases found:** 8
- **Academic papers cited:** 6
- **Industry sources:** 4

---

*Project: wc26-bnaul*
*Date: 2026-06-29*
*Agent: kinhluan-momo*
*Repository: https://github.com/kinhluan/wc26-bnaul*
