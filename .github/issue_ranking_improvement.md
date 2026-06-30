## Ranking Improvement Plan: From Skill -16% to Top 3

**Date:** 2026-06-30  
**Author:** @kinhluan  
**Labels:** `ranking`, `strategy`, `improvement`

---

## Current Situation (The Problem)

| Metric | kinhluan-momo | Top Agent (jason) | Gap |
|--------|---------------|-------------------|-----|
| **Skill %** | **-16%** | **55%** | **-71 points** |
| Accuracy % | 50% | 75% | -25 points |
| Matches scored | 2 | 12 | -10 matches |
| Status | Provisional | Official | Not on leaderboard |

**We are NOT on the leaderboard.** Only 9 agents appear, and we are excluded because we are provisional (`n < 5`). We need **3 more scored matches** just to appear, and many more to climb.

**Why -16% skill?** Our mean Brier score is ~0.29 (worse than random 0.25). One bad prediction (m075: Germany 1-1 Paraguay, Brier = 0.41) dragged us down.

---

## WHY We Are Behind

### 1. Late Start = Fewer Scored Matches

Top agents have `n = 50–72` scored matches. We have `n = 2`. Even if we predict perfectly from now on, we cannot catch up in **absolute score** — but we CAN catch up in **Skill %** if our future predictions are better calibrated.

**Key insight:** The leaderboard ranks by Skill %, not total points. A smaller `n` means higher variance, but also faster recovery.

### 2. Overconfidence in Knockout Matches

Our model assigned Germany **64%** to advance vs Paraguay. The match was a 1-1 draw, and Paraguay won on penalties. The model was **overconfident**.

**Why overconfidence happens:**
- Elo (20%) and xG (25%) heavily favor historically strong teams
- Injury weight (10%) is too low to offset 3 missing starters
- No "draw → penalty" adjustment in knockout format

### 3. Static TEAM_DB = Stale Data

Our team database (`batch_predict.py`) uses **pre-tournament** data:
- Form arrays are initialized, not updated after each match
- Injury counts are guesses, not live data
- No betting odds integration (weight = 20% but always 0.50)

Top agents likely refresh data dynamically.

### 4. No News/Injury Monitoring Before Submission

We ran auto-agent in **fast mode** (`--news` skipped). This means:
- No RSS feed check for last-minute injuries
- No NewsAPI check for team news
- No adjustment based on breaking information

For m075, Germany's 3 injuries were already in TEAM_DB — but if new injuries happened after our data snapshot, we missed them.

---

## HOW to Improve

### Phase 1: Immediate Fixes (Next 5 Matches)

Goal: Get `n >= 5`, exit provisional, appear on leaderboard.

#### ✅ DO

1. **Run with `--news` flag for every prediction**
   ```bash
   ./wc26.sh auto-agent --news --live
   ```
   This checks RSS + NewsAPI for injuries, suspensions, lineup changes.

2. **Manually verify injury counts before high-stakes matches**
   - Check WhoScored, Transfermarkt, or official team Twitter
   - If a team has 2+ injuries, **reduce home_prob by 3-5%**

3. **Cap confidence at 60% for predicted draws**
   - When model predicts 1-1 or 0-0, the knockout winner is ~50/50 (penalties)
   - Submit [0.55, 0.45] instead of [0.64, 0.36]

4. **Focus on early matches (higher round weights)**
   - Round of 32: weight = 1.0×
   - Round of 16: weight = 1.25×
   - These rounds determine 66.7% of final score
   - **Every early match matters more than later ones**

5. **Update TEAM_DB after every match result**
   - Add result to form array (shift left, append new)
   - Update H2H record for the specific pair
   - Reduce xG slightly for teams that underperformed

#### ❌ DON'T

1. **Don't chase losses with extreme probabilities**
   - If we are behind, do NOT submit [0.90, 0.10] hoping for a big win
   - Brier score punishes overconfidence quadratically
   - A 90% prediction that loses = Brier = 0.81 (disaster)

2. **Don't ignore the draw → penalty problem**
   - Knockout matches that end 1-1 are NOT 50/50 in our model
   - The model predicts score, then converts to binary naively
   - **Fix:** When predicted score is a draw, set binary to [0.52, 0.48] max

3. **Don't submit without checking cutoff time**
   - Each match has a `cutoff_utc` — predictions after this are rejected
   - m076 cutoff: 2026-06-30T00:30:00Z (very soon!)

4. **Don't change weights after every match**
   - Weight suggestions need 10+ matches to be statistically meaningful
   - Changing weights too often = overfitting to noise
   - **Wait until Round of 16 ends** before adjusting

5. **Don't forget that truthful submission is optimal**
   - Our true belief may be 55%, but we feel pressure to submit 65%
   - **Resist this.** Expected Brier is minimized at true belief.
   - Any deviation (over/under-confidence) increases expected loss.

---

### Phase 2: Model Improvements (After 10+ Matches)

#### 1. Implement Non-Linear Injury Penalty

Current: `injury_component = 0.50 - 0.02 * (home_injuries - away_injuries)` (linear)

Proposed: exponential penalty
```python
def injury_penalty(injuries):
    if injuries == 0: return 0.0
    if injuries == 1: return 0.02
    if injuries == 2: return 0.06
    if injuries >= 3: return 0.12  # exponential
```

#### 2. Add "Knockout Mode" Weight Set

| Component | Group Stage | Knockout |
|-----------|-------------|----------|
| Elo | 20% | **15%** |
| xG | 25% | **25%** |
| Form | 15% | **20%** |
| H2H | 10% | **10%** |
| Injury | 10% | **15%** |
| Betting | 20% | **15%** |

Rationale: In single-elimination, recent form and squad health matter more than historical rank.

#### 3. Integrate Live Betting Odds

Current: betting component always returns 0.50 (no data).

Fix: Use API-Football or similar to fetch implied probabilities from bookmakers.
```python
# Pseudo-code
def _betting_component(self, home_team, away_team):
    odds = fetch_betting_odds(home_team, away_team)
    if odds:
        implied_home = 1 / odds['home']
        implied_away = 1 / odds['away']
        return implied_home / (implied_home + implied_away)
    return 0.50  # fallback
```

#### 4. Auto-Update TEAM_DB from API Results

Instead of manual edits, create a script:
```bash
./wc26.sh update-results  # Fetches closed matches, updates TEAM_DB
```
This ensures form, H2H, and Elo are always current.

---

### Phase 3: Psychological / Strategic

#### ✅ DO

- **Trust the math.** Brier score is a strictly proper scoring rule. Truthful submission is optimal.
- **Focus on calibration, not accuracy.** A model that says 60% and wins 60% of the time is better than one that says 90% and wins 70%.
- **Review after every round.** Run `./wc26.sh performance` and `./wc26.sh suggest-weights`.
- **Keep a prediction journal.** Note why we chose each probability. Learn from mistakes.

#### ❌ DON'T

- **Don't panic after one bad match.** Variance is high with small `n`.
- **Don't copy other agents' predictions.** We don't know their methods; they might be worse.
- **Don't submit at the last minute.** Technical issues (API timeout, rate limit) can cause missed predictions.
- **Don't ignore the group stage.** Even though it doesn't count for official scoring, it's free practice.

---

## Expected Timeline

| Milestone | Matches Needed | Target Skill % | Action |
|-----------|---------------|--------------|--------|
| Exit provisional | 5 | Any | Just appear on leaderboard |
| Catch top 50% | 15 | > 20% | Better than wc-kimi (23%) |
| Catch top 3 | 30 | > 30% | Better than phuvinhhung1999 (27%) |
| Challenge #1 | 50+ | > 45% | Close to jason (55%) |

**Realistic goal:** With 29 matches remaining in knockout stage, if we average Brier = 0.18 (Skill = 28%), we can reach **top 3–5**.

**Optimistic goal:** If we average Brier = 0.15 (Skill = 40%), we can challenge **#1–2**.

---

## Action Items

- [ ] Implement `--news` check for all future predictions
- [ ] Add draw → penalty cap (max 55% confidence for predicted draws)
- [ ] Create `update-results` script to auto-refresh TEAM_DB
- [ ] After 10 scored matches, evaluate weight suggestions
- [ ] Consider integrating live betting odds
- [ ] Monitor m076–m078 closely — early matches have highest weight

---

*This is a marathon, not a sprint. The knockout stage has 29 matches left. Every match is an opportunity to learn and improve.*
