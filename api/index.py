from http.server import BaseHTTPRequestHandler
import requests
import re
import json

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        TARGET_URL = "https://sv2.thiendinh3.live/trang-chu"
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        urls_list = []
        
        try:
            # Tải nội dung HTML của trang web với thời gian chờ tối đa 5 giây
            response = requests.get(TARGET_URL, headers=headers, timeout=5)
            if response.status_code == 200:
                html = response.text
                
                # BƯỚC 1: Cắt nhỏ HTML thành từng khối trận đấu để quét chính xác, không bị lẫn lộn dữ liệu
                # Thuật toán tìm các khối div/a có cấu trúc chứa thông tin trận đấu
                cards = re.findall(r'<(?:div|a)[^>]*class="[^"]*(?:match|item|live|card)[^"]*"[^>]*>.*? </(?:div|a)>', html, re.DOTALL)
                
                if not cards:
                    # Phương án dự phòng nếu cấu trúc class thay đổi: tìm trực tiếp theo cụm thẻ chứa link trận
                    cards = re.findall(r'<a[^>]*href="/(?:match|live)/[^"]*".*?</a>', html, re.DOTALL)

                for card in cards:
                    # 🔗 1. BẮT ĐƯỜNG DẪN TRẬN ĐẤU
                    link_match = re.search(r'href="((?:https://sv2.thiendinh3.live)?/(?:match|live)/[^"]+)"', card)
                    if not link_match:
                        continue
                    match_url = link_match.group(1)
                    if match_url.startswith('/'):
                        match_url = "https://sv2.thiendinh3.live" + match_url
                        
                    # Loại bỏ trùng lặp nếu trận đấu bị quét hai lần
                    if any(u['url'] == match_url for u in urls_list):
                        continue

                    # ⏳ 2. BẮT GIỜ THI ĐẤU
                    # Tìm định dạng giờ xx:xx hoặc các thẻ chứa class time
                    time_match = re.search(r'(?:class="[^"]*time[^"]*"[^>]*>|>\s*)(\d{2}:\d{2})', card)
                    match_time = time_match.group(1) if time_match else "Đang đá"

                    # 🎙️ 3. BẮT TÊN BÌNH LUẬN VIÊN
                    blv_match = re.search(r'(?:class="[^"]*(?:blv|caster|comment)[^"]*"[^>]*>|>\s*)(BLV\s+[^<]+)', card, re.IGNORECASE)
                    blv_name = blv_match.group(1).strip() if blv_match else "Chưa có BLV"

                    # 🖼️ 4. BẮT LOGO TRẬN ĐẤU (Ưu tiên logo đội bóng hoặc banner trận đấu)
                    logo_match = re.search(r'<img[^>]*(?:src|data-src)="([^"]+)"', card)
                    match_logo = logo_match.group(1) if logo_match else ""
                    if match_logo.startswith('/'):
                        match_logo = "https://sv2.thiendinh3.live" + match_logo
                    if not match_logo:
                        match_logo = "https://sv2.thiendinh3.live/assets/images/logo.png"

                    # ⚽ 5. BẮT TÊN TRẬN ĐẤU
                    # Tìm thẻ tiêu đề chứa tên 2 đội bóng
                    title_match = re.search(r'<(?:h2|h3|h4|p)[^>]*class="[^"]*(?:title|name|team)[^"]*"[^>]*>(.*?)</', card, re.DOTALL)
                    if title_match:
                        match_name = title_match.group(1)
                    else:
                        # Tự động lọc sạch các thẻ HTML để lấy chuỗi chữ tên trận nếu không khớp class
                        match_name = re.sub(r'<[^>]+>', ' ', card)
                        match_name = match_name.replace(match_time, "").replace(blv_name, "").strip()
                    
                    # Làm sạch khoảng trắng thừa
                    match_name = " ".join(match_name.split())
                    if len(match_name) > 60: # Giới hạn ký tự tránh làm xấu giao diện app
                        match_name = match_name[:57] + "..."

                    # Gộp thông tin theo chuẩn định dạng MonPlayer hiển thị trực quan nhất
                    display_name = f"[{match_time}] {match_name} ({blv_name})"
                    
                    urls_list.append({
                        "name": display_name,
                        "url": match_url,
                        "logo": match_logo,
                        "group": "Thiên Đình TV - Trực Tiếp"
                    })
        except:
            pass

        # Dữ liệu cứu cánh nếu trang web bảo trì hoặc chưa đến giờ đá
        if not urls_list:
            urls_list.append({
                "name": "[LIVE] Ghé thăm Thiên Đình TV (Chưa có trận)",
                "url": TARGET_URL,
                "logo": "https://sv2.thiendinh3.live/assets/images/logo.png",
                "group": "Thiên Đình TV"
            })

        # Tạo cấu trúc JSON hoàn chỉnh cho MonPlayer
        monplayer_json = {
            "name": "Thiên Đình TV Auto",
            "author": "Mạnh DZ",
            "urls": urls_list
        }

        # Trả kết quả về dưới dạng file .json chuẩn mã hóa UTF-8 tiếng Việt
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*') # Bật CORS cấp quyền cho MonPlayer đọc dữ liệu
        self.end_headers()
        self.wfile.write(json.dumps(monplayer_json, ensure_ascii=False, indent=2).encode('utf-8'))
        return
                      
