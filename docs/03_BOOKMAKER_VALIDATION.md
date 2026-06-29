# ClawCup Strategy Validation — Bookmaker Cross-Check

## 📚 Tổng hợp từ nguồn uy tín

### 1. Brier Score là Proper Scoring Rule (Academic Consensus)

**Nguồn**: Berkeley Statistics, TUM Munich, MetricGate, Sports-AI.dev

> "Brier score is a **strictly proper scoring rule** — it is minimised, in expectation, by reporting the true probability."
> — Berkeley Statistics Department

> "A model cannot improve its score by shifting outputs away from the true conditional probability — it can only improve by moving predictions closer to it."
> — MetricGate

**Ý nghĩa**: Đây là lý thuyết đã được chứng minh trong thống kê học. Không phải ý kiến cá nhân hay giả định của ClawCup.

### 2. Bookmaker Odds vs True Probability

**Nguồn**: MyBookie, GammaStack, SportsBettingDime, Predictinho

Bookmaker quy trình:
1. **Estimate true probability**: Dùng model, data, expert analysis
2. **Add overround/vig**: Tăng margin để đảm bảo lợi nhuận
3. **Publish odds**: Implied probability > 100% (overround 2-5% cho major football)

**Ví dụ thực tế** (GammaStack):
- True prob: Man City 55%, Draw 22%, Arsenal 23% = 100%
- Fair odds: 1.82, 4.55, 4.35
- **With 5% overround**: 1.73, 4.33, 4.14 → Implied: 57.8% + 23.1% + 24.2% = 105.1%

**Key insight**: Bookmaker **không** gửi true probability. Họ gửi true probability + margin.

### 3. Miscalibration ảnh hưởng betting profitability

**Nguồn**: Sports-AI.dev

> "If a model is overconfident and assigns 70% to events that occur only 55% of the time, the computed edge is inflated, causing overbetting via Kelly Criterion."

**Ý nghĩa**: Over-confidence không chỉ tệ trong theory — nó thực sự làm bettor mất tiền.

---

## 🔍 So sánh ClawCup vs Bookmaker

| Khía cạnh | ClawCup | Bookmaker |
|-----------|---------|-----------|
| **Mục tiêu** | Maximize Skill% (proper scoring) | Maximize profit (overround) |
| **Incentive** | Truthful calibration | Inflate margin |
| **Scoring** | Brier/RPS (proper) | Payout based on odds |
| **Optimal strategy** | Submit true prob | Price with margin |
| **Risk** | Calibration error | Market imbalance |

**Quan trọng**: ClawCup và bookmaker có **incentive ngược nhau**:
- Bookmaker muốn bạn **sai** (để họ thắng margin)
- ClawCup muốn bạn **đúng** (để đo calibration)

→ Chiến thuật optimal cho ClawCup **khác** chiến thuật optimal cho cá cược!

---

## ✅ Xác nhận đánh giá của chúng ta

### 1. Truthful submission = optimal

**Academic proof** (Brier 1950, Berkeley, TUM):
```
E[Brier] = q(1-q) + (p-q)²

Where:
- q = true probability
- p = submitted probability

Minimum at: p = q (derivative = 0)
```

**Simulation của chúng ta** (10,000 runs):
| Strategy | Mean Skill% | vs Truthful |
|----------|------------|-------------|
| Truthful | 18.61% | baseline |
| Over-confident | 16.00% | -2.61% |
| Max confident | -24.52% | -43.13% |

→ **Khớp hoàn toàn** với theory!

### 2. Bookmaker không dùng truthful submission

Bookmaker **chủ động** không dùng true probability. Họ thêm overround để:
- Đảm bảo profit regardless of outcome
- Bảo vệ against sharp bettors
- Balance book (equal money both sides)

→ Đây là **business model**, không phải optimal prediction strategy.

### 3. Over-confidence bị phạt nặng

**Academic** (Sports-AI.dev):
> "Brier and log loss are strictly proper scoring rules — they reward honest probabilistic forecasts and cannot be gamed."

**Simulation của chúng ta**:
- Max confident (0.99/0.01): Skill% = -24.52% (worse than naive 50/50!)
- Naive 50/50: Skill% = 0% (baseline)

→ Over-confidence **worse than guessing** — đúng như theory dự đoán!

---

## 🎯 Kết luận

### Đánh giá của chúng ta là **ĐÚNG** và đã được xác nhận bởi:

| Nguồn | Xác nhận |
|-------|----------|
| **Berkeley Statistics** | Brier là strictly proper scoring rule |
| **TUM Munich** | Proper scoring rules minimize at true probability |
| **MetricGate** | Cannot improve by shifting from true probability |
| **Sports-AI.dev** | Overconfidence inflates edge, causes ruin |
| **GammaStack** | Bookmaker adds margin, doesn't use true prob |
| **Our simulation** | Truthful > over-confident by 2.6-43pp |

### Key insight:

> **"ClawCup rewards calibration. Bookmakers reward margin. Đây là hai game khác nhau với optimal strategies khác nhau."**

- **Bookmaker optimal**: True prob + margin = maximize profit
- **ClawCup optimal**: True prob (no margin) = maximize Skill%

→ Chiến thuật của chúng ta (truthful submission) là **optimal cho ClawCup**, không phải cho cá cược.

---

## 📚 References

1. Brier, G.W. (1950). Verification of forecasts expressed in terms of probability. *Monthly Weather Review*.
2. Berkeley Statistics Department. Proper Scoring Rules lecture notes.
3. GammaStack (2026). How Do Bookmakers Generate Sports Odds.
4. Sports-AI.dev (2024). AI Model Calibration for Sports Betting.
5. MetricGate (2025). Brier Score vs Log Loss vs Calibration.
6. MyBookie (2026). Bookmaker's Advantage Explained.

---

*Note: ClawCup is non-monetary, not betting. This analysis is for educational purposes only.*
