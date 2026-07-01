import sys
import os
import json

# Thêm thư mục src vào sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from wc26_bnaul.json_db import gather_match_context

def main():
    match_id = "m080"
    home = "England"
    away = "DR Congo"
    
    # Lấy toàn bộ data tĩnh + data đã làm giàu (Coach, Referee, Betting, Injury)
    context = gather_match_context(match_id, home, away, ref_name="Michael Oliver")
    
    prompt = f"""Bạn là trợ lý AI chuyên nghiệp phân tích bóng đá (Kimi).

Tôi có một mô hình học máy (Ensemble Model) dự đoán bóng đá. Dưới đây là toàn bộ thông số dữ liệu JSON cực kỳ chi tiết của trận đấu sắp tới (Match ID: {match_id} | {home} vs {away}) đã được hệ thống của tôi tổng hợp và làm giàu (bao gồm Elo, phong độ, chiến thuật HLV, tình hình chấn thương, thống kê trọng tài và tỷ lệ kèo nhà cái):

{json.dumps(context, indent=2, ensure_ascii=False)}

Dựa trên bộ dữ liệu toàn diện này, hãy phân tích định tính chuyên sâu và đưa ra:
1. Nhận định tổng quan về cục diện trận đấu (Ảnh hưởng của chấn thương, sự khắc chế trong chiến thuật của 2 HLV, xu hướng của trọng tài và đánh giá từ nhà cái).
2. Đề xuất điều chỉnh tỷ lệ dự đoán: Đề xuất TĂNG (+) hay GIẢM (-) bao nhiêu % tỷ lệ thắng cho đội {home} so với mức tính toán thuần túy từ Elo? 
(Ví dụ: "Vì {home} mất Bukayo Saka (is_injured: true) và nhà cái đang hạ kèo, tôi đề xuất giảm -3.5% tỷ lệ thắng cho {home}")."""

    print(prompt)

if __name__ == "__main__":
    main()
