# 🏆 wc26-bnaul — ClawCup FIFA World Cup Prediction Agent

> **Skill scope:** Project-specific (wc26-bnaul)  
> **Last updated:** 2026-06-30  
> **Author:** @kinhluan

---

## 1. Strategic Rules (Hard Rules — Never Break)

- `Rule: Brier score is strictly proper → Always submit TRUE belief probability. (Over/under-confidence punished quadratically).`
- `Rule: Knockout predicted draw (1-1, 0-0) → Cap binary at [0.55, 0.45] max. (Penalties are ~50/50 coin flips).`
- `Rule: Team with 2+ injuries → Reduce home_prob by 3-5% before submit. (Injury weight 10% is too low in current model).`
- `Rule: Early rounds (Ro32=1.0×, Ro16=1.25×) → Focus maximum effort. (These determine 66.7% of final score).`
- `Rule: Always run --news flag before submit. (Last-minute injuries/lineup changes are critical).`

---

## 2. Tactical Rules (Context-Dependent)

- `Rule: Static TEAM_DB → Auto-update form + H2H after every match result. (Stale data kills predictions).`
- `Rule: Provisional status (n < 5 scored matches) → Prioritize calibration over bold predictions. (Need to exit provisional ASAP).`
- `Rule: Weight suggestions need 10+ matches → Do NOT adjust weights before Round of 16 ends. (Avoid overfitting to noise).`
- `Rule: Overconfidence (prob > 0.70) → Double-check injury/news data. (High confidence = high Brier risk if wrong).`
- `Rule: Placeholder teams (W74, W75...) → Use default stats but monitor if real team is determined. (Update TEAM_DB immediately).`

---

## 3. Operational Checklist (Before Every Submit)

```
□ Run ./wc26.sh auto-agent --news (not fast mode)
□ Check cutoff_utc — submit BEFORE deadline
□ Verify injury counts for both teams
□ If predicted score is draw → cap binary at [0.55, 0.45]
□ If team has 2+ injuries → reduce favorite's prob by 3-5%
□ Check round weight — early rounds matter more
□ Log prediction to predictions.jsonl
□ After match ends → log result to results.jsonl
□ Update TEAM_DB form + H2H
```

---

## 4. Key Metrics & Benchmarks

| Metric | Good | Great | Current (Ours) |
|--------|------|-------|----------------|
| Brier Score | < 0.20 | < 0.15 | ~0.29 (bad) |
| Skill % | > 20% | > 40% | -16% (terrible) |
| Accuracy | > 60% | > 70% | 50% |
| Calibration | 3+ | 4+ | ? |

**Target:** Reach Skill > 30% after 15 scored matches (top 3 territory).

---

## 5. Common Pitfalls (Learned from m074/m075)

1. **m074 Brazil vs Japan (✅):** Brazil dominated every metric → model correct. Lesson: When favorite has zero injuries + superior form, trust the model.
2. **m075 Germany vs Paraguay (❌):** Germany had 3 injuries, Paraguay had better form → model overconfident at 64%. Lesson: Injuries and form can override historical Elo/xG in knockouts.

---

## 6. Quick Commands

```bash
# Check status
./wc26.sh me
./wc26.sh performance
./wc26.sh suggest-weights

# Predict with news check
./wc26.sh auto-agent --news --live

# Check fixtures
./wc26.sh fixtures --status open
./wc26.sh fixtures --status closed

# Update results (manual)
uv run python -c "from wc26_bnaul.prediction_logger import PredictionLogger; \
  logger = PredictionLogger(); logger.log_result('MATCH_ID', H, A, 'winner')"
```

---

## 7. Related Issues

- **#1** — Match Analysis: m074 & m075 breakdown (why 1 correct, 1 wrong)
- **#2** — Ranking Improvement Plan: From -16% to Top 3

---

*This skill is a living document. Update after every round of matches.*
