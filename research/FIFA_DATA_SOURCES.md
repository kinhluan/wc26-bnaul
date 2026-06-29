# FIFA Football Data Sources — Research for wc26-bnaul

> **Mục tiêu:** Tìm nguồn dữ liệu bóng đá miễn phí/có phí để cải thiện dự đoán ClawCup

---

## 1. FIFA Enhanced Football Intelligence (EFI)

### Tổng quan

**EFI** là hệ thống thu thập và trình bày dữ liệu thống kê trận đấu hiện đại của FIFA. Được triển khai từ World Cup 2022.

### Đặc điểm kỹ thuật

| Đặc điểm | Chi tiết |
|----------|----------|
| **Nguồn dữ liệu** | Multi-camera optical tracking system |
| **Loại dữ liệu** | Tracking data (on-ball + off-ball movements) |
| **Độ trễ** | < 30 giây sau sự kiện |
| **Xử lý** | 2 giây cho event-based metrics |
| **Định dạng** | PDF sau trận, snippets trong broadcast |

### Các chỉ số EFI chính

| Chỉ số | Mô tả | Ứng dụng cho dự đoán |
|---------|-------|---------------------|
| **Possession Control** | In Contest / Out of Play / Team possession | Đánh giá kiểm soát thực sự |
| **Phases of Play** | Build-Up, Progression, Final Third, Counter Attack | Phân tích lối chơi |
| **Line Breaks** | Pass/Cross/Ball Progression qua defensive lines | Đánh giá khả năng xuyên phá |
| **Receptions & Offers** | Vị trí nhận bóng, di chuyển có bóng/không bóng | Phân tích chiến thuật |
| **Line Heights & Team Lengths** | Khoảng cách defensive line, chiều rộng đội hình | Đánh giá hình thái phòng ngự/tấn công |
| **Forced Turnovers** | Mất bóng do áp lực phòng ngự | Đánh giá pressing hiệu quả |
| **Defensive Pressure** | Direct Pressure, Pushing On, Pressing Direction | Phân tích pressing |
| **Ball Recovery Time** | Thời gian giành lại bóng sau mất bóng | Đánh giá pressing và tổ chức |

### API Access

| Nguồn | Trạng thái | Chi phí | Ghi chú |
|-------|-----------|---------|---------|
| **FIFA Training Centre** | Public PDF | Free | Sau trận, không real-time |
| **FIFA Data Hub** | Internal only | N/A | Chỉ cho stakeholders (broadcasters, teams) |
| **Open-source implementation** | GitHub: doganparlak/EFI | Free | Reproduce WC 2022 data, không có live API |

### Kết luận về EFI

> **Không có public API miễn phí.** Dữ liệu EFI chỉ available qua:
> 1. PDF sau trận trên FIFA Training Centre
> 2. Broadcast snippets (real-time nhưng không structured)
> 3. Internal FIFA Data Hub (yêu cầu quan hệ đối tác)

---

## 2. FIFA Match Performance Indicators (MPIs)

### Tổng quan

MPIs là các chỉ số hiệu suất trận đấu được FIFA thu thập qua các nhà cung cấp dữ liệu bên thứ ba (Data Sports Group, Enetpulse, v.v.)

### Các chỉ số MPI

| Chỉ số | Nguồn | API Available |
|--------|-------|--------------|
| Goals, Assists | Event data | ✅ Có qua API-Football, football-data.org |
| Shots, Shots on Target | Event data | ✅ Có qua API-Football, football-data.org |
| Possession % | Event data | ✅ Có qua API-Football, football-data.org |
| Passes, Pass Accuracy | Event data | ✅ Có qua API-Football, football-data.org |
| Tackles, Interceptions | Event data | ✅ Có qua API-Football (paid) |
| xG (Expected Goals) | Tracking data | ⚠️ Chỉ có qua paid APIs (Sportmonks, TheStatsAPI) |
| Heatmaps | Tracking data | ❌ Không có public API |
| Player tracking | Tracking data | ❌ Không có public API |

### Kết luận về MPIs

> MPIs cơ bản (goals, shots, possession) có sẵn qua free APIs. MPIs nâng cao (xG, heatmaps, tracking) chỉ có qua paid APIs hoặc không có public access.

---

## 3. Free Football APIs (Khuyến nghị cho wc26-bnaul)

### 3.1 football-data.org (Best Free Option)

| Đặc điểm | Chi tiết |
|-----------|----------|
| **Free tier** | 12 competitions, 10 req/min |
| **World Cup** | ✅ Included trong free tier |
| **Dữ liệu** | Fixtures, results, standings, scorers |
| **Player stats** | ❌ Cần paid add-on (€29/mo) |
| **Real-time** | ⚠️ Slightly delayed |
| **Đăng ký** | Free API key sau signup |

**Endpoints hữu ích:**
```
GET /v4/competitions/WC/matches          # All World Cup matches
GET /v4/matches/{id}                     # Match details
GET /v4/competitions/WC/standings       # Group standings
GET /v4/competitions/WC/scorers        # Top scorers
```

### 3.2 API-Football (via RapidAPI)

| Đặc điểm | Chi tiết |
|-----------|----------|
| **Free tier** | 100 requests/day |
| **Coverage** | 1,200+ leagues |
| **World Cup** | ✅ league=1, season=2026 |
| **Player stats** | ✅ Có trên free tier |
| **Real-time** | ✅ Live scores, 15s update |
| **Đăng ký** | Free API key qua RapidAPI |

**Endpoints hữu ích:**
```
GET /v3/fixtures?league=1&season=2026   # All WC fixtures
GET /v3/fixtures?live=all                 # Live matches
GET /v3/fixtures/players?id={fixture}    # Player stats per match
GET /v3/injuries?league=1&season=2026    # Injuries
GET /v3/predictions?fixture={id}          # AI predictions
GET /v3/odds?fixture={id}                # Pre-match odds
```

### 3.3 OpenLigaDB (No API Key Required)

| Đặc điểm | Chi tiết |
|-----------|----------|
| **API Key** | ❌ Không cần |
| **Coverage** | German football only |
| **World Cup** | ❌ Không cover |
| **Ghi chú** | Không phù hợp cho World Cup |

### 3.4 StatsBomb Open Data (Dataset, không phải API)

| Đặc điểm | Chi tiết |
|-----------|----------|
| **Loại** | GitHub-published dataset |
| **Dữ liệu** | Event data, xG, shot data |
| **World Cup** | ✅ Có WC 2022 data |
| **Real-time** | ❌ Không, offline dataset |
| **Ứng dụng** | ML research, portfolio projects |

**GitHub:** https://github.com/statsbomb/open-data

---

## 4. Paid Football APIs (Nếu cần nâng cấp)

### 4.1 Sportmonks

| Plan | Giá | Dữ liệu |
|------|-----|---------|
| Free | €0 | 2 leagues (Danish + Scottish) |
| Starter | €29/mo | 5 leagues |
| Growth | €99/mo | 30 leagues |
| Pro | €249/mo | 120 leagues |

**Add-ons:** xG, predictions, news, widgets

### 4.2 TheStatsAPI

| Plan | Giá | Dữ liệu |
|------|-----|---------|
| Starter | $50/mo | 150 competitions, 84,000+ players, 10 years history |
| **Ưu điểm** | Flat rate, xG included | Không cần mua nhiều add-ons |

### 4.3 Data Sports Group (DSG)

| Đặc điểm | Chi tiết |
|-----------|----------|
| **FIFA Partner** | ✅ Official data provider |
| **Dữ liệu** | Real-time scores, stats, ball tracking, player events |
| **Giá** | Custom (enterprise) |
| **API** | JSON/XML, WebSocket |

---

## 5. Khuyến nghị cho wc26-bnaul

### Tier 1: Immediate (Free)

| Nguồn | Dữ liệu | Cách dùng |
|-------|---------|-----------|
| **football-data.org** | Fixtures, results, standings | Theo dõi lịch thi đấu, kết quả |
| **API-Football** | Player stats, injuries, live scores | Phân tích phong độ cầu thủ, chấn thương |
| **FIFA Training Centre** | EFI PDFs sau trận | Phân tích chiến thuật post-match |

### Tier 2: Short-term (Paid ~$19-50/mo)

| Nguồn | Dữ liệu | Cách dùng |
|-------|---------|-----------|
| **API-Football Pro** | $19/mo, 7,500 req/day | Real-time player stats, predictions |
| **TheStatsAPI** | $50/mo, xG included | Expected goals, advanced metrics |

### Tier 3: Long-term (Enterprise)

| Nguồn | Dữ liệu | Cách dùng |
|-------|---------|-----------|
| **Data Sports Group** | Custom pricing | Ball tracking, real-time event data |
| **FIFA Partnership** | Internal | EFI real-time, tracking data |

---

## 6. Kết luận

### Về EFI và MPIs

| Câu hỏi | Trả lời |
|---------|---------|
| **Có public API miễn phí cho EFI?** | ❌ Không. Chỉ có PDF sau trận |
| **Có public API miễn phí cho MPIs?** | ⚠️ Chỉ có MPIs cơ bản (goals, shots, possession) |
| **Có thể lấy real-time tracking data?** | ❌ Không, chỉ có qua paid enterprise APIs |
| **Có thể lấy xG miễn phí?** | ⚠️ StatsBomb Open Data (offline), hoặc paid APIs |

### Khuyến nghị hành động

1. **Ngay lập tức:** Đăng ký football-data.org (free) + API-Football (free tier) để lấy fixtures, results, player stats
2. **Ngắn hạn:** Nâng cấp API-Football Pro ($19/mo) để có real-time player stats và predictions
3. **Trung hạn:** Theo dõi FIFA Training Centre PDFs sau mỗi trận để cập nhật EFI metrics
4. **Dài hạn:** Cân nhắc TheStatsAPI ($50/mo) nếu cần xG và advanced metrics

---

*Research date: 2026-06-29*
*Agent: wc26-bnaul*
