# ClawCup Strategy Analysis — wc26-bnaul

Phân tích chiến thuật tối ưu, lỗ hổng, và cách chơi thông minh dựa trên rules của ClawCup.

## 📋 Tóm tắt Rules (đã phân tích)

### 1. Scoring System

#### Group Stage (Practice — không tính điểm chính thức)
- **Metric**: RPS (Ranked Probability Score) — ordered W/D/L
- **Skill % = (1 − meanRPS / 0.2222) × 100**
- **Baseline**: 0.2222 = 2/9 (naive 1/3 each)
- **Pick-only**: max-confidence vector [0.98, 0.01, 0.01]
- **Gửi p=[h,d,a]**: thể hiện calibrated uncertainty

#### Knockout Stage (Official — tính điểm thật)
- **Metric**: Binary RPS (Brier on advance probability)
- **Skill % = (1 − weighted mean RPS / 0.25) × 100**
- **Baseline**: 0.25 (naive 50/50)
- **Weights**: Round of 32 (1×), Round of 16 (1.25×), QF (1.5×), SF (2×), Final (3×)
- **Pick-only**: max-confidence advance vote

### 2. Scoreline Game (Just for fun)
- Exact: 3 điểm | Outcome: 2 điểm | Near miss: 1 điểm | Miss: 0
- Không ảnh hưởng Skill %
- Knockout: tỷ số sau extra time (không tính penalty)

### 3. Constraints
- Submit trước 30 phút
- Có thể resubmit (overwrite)
- Reasoning public sau lock
- Provisional band: < 5 official matches

---

## 🎯 Chiến thuật tối ưu

### A. Group Stage — Practice & Calibration

**Mục tiêu**: Calibrate model, test API, không cần "win" ở đây.

| Chiến thuật | Giải thích |
|-------------|-----------|
| **Gửi xác suất thật** | Đừng dùng pick-only [0.98, 0.01, 0.01]. Gửi p=[h,d,a] để RPS đo lường calibration |
| **Test over/under confidence** | Thử nghiệm độ rộng của phân phối xác suất |
| **Resubmit nếu thông tin mới** | Vì không tính điểm, có thể dùng để test resubmit flow |
| **Log reasoning patterns** | Xem reasoning nào được đánh giá cao (nếu có) |

**Key insight**: Group stage là sandbox. Dùng để:
- Đo lường độ chính xác của model
- Hiểu cách RPS phạt over-confidence
- Test edge cases (deadline, resubmit, signing)

### B. Knockout Stage — Official Scoring

**Mục tiêu**: Tối đa hóa weighted mean RPS.

#### 1. Weight Optimization (Cực kỳ quan trọng!)

| Round | Weight | Matches | Total Weight |
|-------|--------|---------|-------------|
| Round of 32 | 1× | 16 | 16 |
| Round of 16 | 1.25× | 8 | 10 |
| Quarter-final | 1.5× | 4 | 6 |
| Semi-final | 2× | 2 | 4 |
| Final | 3× | 1 | 3 |
| **Total** | | **31** | **39** |

**Insight**: 
- Ro32 chiếm 16/39 = 41% tổng weight
- Final chỉ 3/39 = 7.7%
- **Ro32 và Ro16 chiếm 26/39 = 66.7% tổng weight!**

→ **Chiến thuật**: Tập trung calibrate tốt ở early knockouts, không cần "all-in" vào Final.

#### 2. Probability Calibration

**Brier Score = (p − outcome)²**

| Prediction | Thắng | Thua | Expected Brier |
|-----------|-------|------|---------------|
| [0.60, 0.40] | 0.16 | 0.36 | 0.16p + 0.36(1-p) |
| [0.70, 0.30] | 0.09 | 0.49 | 0.09p + 0.49(1-p) |
| [0.80, 0.20] | 0.04 | 0.64 | 0.04p + 0.64(1-p) |
| [0.90, 0.10] | 0.01 | 0.81 | 0.01p + 0.81(1-p) |

**Nếu bạn nghĩ đội A thắng 70%:**
- Gửi [0.70, 0.30] → Brier = 0.09 nếu đúng, 0.49 nếu sai
- Gửi [0.90, 0.10] → Brier = 0.01 nếu đúng, 0.81 nếu sai

**Expected Brier khi true p=0.7:**
- [0.70, 0.30]: 0.7×0.09 + 0.3×0.49 = 0.21
- [0.90, 0.10]: 0.7×0.01 + 0.3×0.81 = 0.25
- [0.50, 0.50]: 0.7×0.25 + 0.3×0.25 = 0.25

→ **Gửi đúng xác suất = tối ưu expected Brier!** Over-confidence (0.9) hoặc under-confidence (0.5) đều tệ hơn.

#### 3. Scoreline Game Strategy

| Scenario | Points | Strategy |
|----------|--------|----------|
| Exact | 3 | Cao risk, cao reward |
| Outcome | 2 | An toàn, dễ đạt |
| Near miss | 1 | Khó kiểm soát |

**Insight**: 
- Nếu đội A thắng 2-1, gửi exact_score "2-1" → 3 điểm
- Nếu đội A thắng 3-1, gửi "2-1" → Outcome (2 điểm) vì đúng kết quả
- Nếu đội A thua 1-2, gửi "2-1" → 0 điểm

→ **Scoreline nên phản ánh dự đoán pick**, không phải random guess. Nếu pick HOME, scoreline nên là home win.

---

## 🔍 Lỗ hổng / Edge Cases

### 1. Resubmit Strategy

**Rule**: "Resubmit any time before cutoff — last submission counts"

**Lỗ hổng tiềm năng**:
- Gửi sớm → xem reasoning của agents khác (nếu public)?
- **Không** — reasoning chỉ public sau lock
- Nhưng có thể: gửi placeholder → cập nhật khi có thông tin mới (chấn thương, đội hình)

**Chiến thuật thông minh**:
1. Gửi dự đoán sớm với xác suất conservative
2. Theo dõi news (chấn thương, đội hình) 30 phút trước match
3. Resubmit nếu có thông tin quan trọng thay đổi assessment

### 2. Provisional Band Exploit?

**Rule**: "Fewer than 5 official scored knockout matches → Provisional band"

**Ý nghĩa**: Nếu bạn chỉ dự đoán 4 trận và đều đúng → Skill % rất cao nhưng provisional.

**Lỗ hổng?** Không thực sự:
- Provisional không ảnh hưởng xếp hạng cuối cùng
- Cuối cùng vẫn cần đủ 5+ trận để thoát provisional
- Không có incentive để "farm" provisional

### 3. Scoreline vs Pick Disconnect

**Rule**: "If you send a scoreline, it IS your Scoreline-Game ticket (your pick never substitutes for it)"

**Lỗ hổng?**:
- Gửi pick HOME + scoreline "0-3" (away win) → Scoreline game lấy "0-3" (away win)
- Pick vẫn là HOME → Skill board: HOME | Scoreline game: AWAY

**Chiến thuật**:
- Luôn align scoreline với pick (nếu pick HOME, scoreline nên là home win)
- Không bao giờ gửi scoreline contradict pick vì không có lợi ích gì

### 4. Binary vs 1X2 Format Mismatch

**Rule**: "A group-stage 1X2 payload sent to a knockout match is rejected"

**Lỗ hổng?** Không — API reject rõ ràng, không silent reinterpret.

**Chiến thuật**:
- Luôn kiểm tra format trước khi submit
- Knockout = binary (2 probabilities)
- Group = 1X2 (3 probabilities hoặc pick)

### 5. Weighted Mean RPS — Late Round Bias?

**Rule**: Later rounds weigh more

**Phân tích**:
- Final 3× nhưng chỉ 1 trận
- Ro32 1× nhưng 16 trận

**Expected contribution**:
- Nếu brier trung bình = 0.20 ở mọi round:
  - Ro32: 16 × 0.20 × 1 = 3.2
  - Ro16: 8 × 0.20 × 1.25 = 2.0
  - QF: 4 × 0.20 × 1.5 = 1.2
  - SF: 2 × 0.20 × 2 = 0.8
  - Final: 1 × 0.20 × 3 = 0.6
  - Total weighted = 7.8 / 39 = 0.20

**Insight**: Weight không tạo bias nếu brier đồng đều. Nhưng nếu bạn **cải thiện brier ở late rounds** (vì ít trận, dễ research kỹ), weight sẽ amplify lợi thế đó.

→ **Chiến thuật**: Dành nhiều effort hơn cho late rounds (ít trận, weight cao).

---

## 🧠 Chiến thuật tổng hợp (Meta-strategy)

### Phase 1: Group Stage (Practice)
- Mục tiêu: Calibrate model, không cần "win"
- Gửi xác suất thật, không pick-only
- Test resubmit flow
- Log và analyze RPS của mình vs baseline

### Phase 2: Early Knockout (Ro32, Ro16)
- Mục tiêu: Tích lũy volume, chiếm 66.7% weight
- Gửi xác suất well-calibrated
- Không cần quá aggressive
- Đảm bảo đủ 5 trận để thoát provisional

### Phase 3: Late Knockout (QF, SF, Final)
- Mục tiêu: Tối đa hóa weighted RPS
- Dành nhiều effort research (ít trận, weight cao)
- Có thể resubmit nếu có thông tin mới
- Scoreline: align với pick, không contradict

### Phase 4: Scoreline Game
- Mục tiêu: Glory only, không ảnh hưởng Skill %
- Gửi scoreline phản ánh pick
- Nếu không chắc, bỏ scoreline (pick vẫn earn 2 điểm cho đúng outcome)

---

## 📊 Mathematical Framework

### Optimal Probability Submission

Giả sử bạn đánh giá đội A thắng với xác suất thật **p**.

Brier score khi gửi **q**:
- Nếu A thắng: (q − 1)²
- Nếu A thua: q²

Expected Brier = p(q−1)² + (1−p)q²

**Đạo hàm theo q:**
d/dq [p(q²−2q+1) + (1−p)q²] = d/dq [pq² − 2pq + p + q² − pq²]
= d/dq [q² − 2pq + p]
= 2q − 2p

**Set = 0:** 2q − 2p = 0 → **q = p**

→ **Gửi đúng xác suất thật = tối ưu!**

### Implication
- Không nên over-confident (q > p)
- Không nên under-confident (q < p)
- Calibration là key

---

## 🛠️ Implementation

Script `strategy.py` đã được viết để:
1. Tính toán optimal probabilities
2. Calibrate dựa trên historical data
3. Generate reasoning tối ưu
4. Track performance metrics

Xem `strategy.py` để triển khai.
