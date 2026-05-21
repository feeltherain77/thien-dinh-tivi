from http.server import BaseHTTPRequestHandler
import requests
import re
import json

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        TARGET_URL = "https://sv2.thiendinh3.live/trang-chu"
        
        # BỘ HEADER GIẢ LẬP TRÌNH DUYỆT XỊN ĐỂ QUA MẶT CLOUDFLARE/CHẶN BOT
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1"
        }
        
        urls_list = []
        
        try:
            response = requests.get(TARGET_URL, headers=headers, timeout=10)
            if response.status_code == 200:
                html = response.text
                
                # QUÉT CỰC MẠNH: Tìm mọi thẻ chứa đường link trên toàn bộ trang web
                raw_matches = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
                
                for href, content in raw_matches:
                    match_url = href.strip()
                    
                    # Lọc: Chỉ lấy những link có dấu hiệu là link xem bóng đá (chứa từ khóa live, match, truc-tiep, xem...)
                    if not any(keyword in match_url for keyword in ['/match/', '/live/', '/truc-tiep/', '/xem']):
                        continue
                        
                    if match_url.startswith('/'):
                        match_url = "https://sv2.thiendinh3.live" + match_url
                        
                    if any(u['url'] == match_url for u in urls_list):
                        continue

                    # Làm sạch HTML bên trong để bóc chữ
                    clean_content = re.sub(r'<[^>]+>', ' ', content)
                    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                    
                    if len(clean_content) < 5: # Bỏ qua các nút bấm rác
                        continue

                    # Bắt Giờ (xx:xx)
                    time_search = re.search(r'(\d{2}:\d{2})', clean_content)
                    match_time = time_search.group(1) if time_search else "LIVE"

                    # Bắt BLV
                    blv_search = re.search(r'(BLV\s+\w+)', clean_content, re.IGNORECASE)
                    blv_name = blv_search.group(1) if blv_search else "Sôi Động"

                    # Xóa giờ và BLV khỏi tên
                    match_name = clean_content.replace(match_time, "").replace(blv_name, "").strip()
                    if len(match_name) < 3:
                        match_name = "Trận đấu đang diễn ra"

                    display_name = f"[{match_time}] {match_name} ({blv_name})"
                    
                    # 🚀 CẤU TRÚC JSON "NHÁI" THEO BẢN PRO CỦA HỘI QUÁN
                    urls_list.append({
                        "name": display_name,
                        "url": match_url,
                        "logo": "https://sv2.thiendinh3.live/assets/images/logo.png",
                        "group": "Thiên Đình TV Live",
                        "display": "thumbnail-only",       # Code giao diện pro
                        "background_color": "#1c1c1c"      # Code giao diện pro
                    })
        except Exception as e:
            pass

        # Vẫn giữ 1 dòng dự phòng để biết bot có bị chết hay không
        if not urls_list:
            urls_list.append({
                "name": "[LỖI/TRỐNG] Không quét được hoặc chưa có trận",
                "url": TARGET_URL,
                "logo": "https://sv2.thiendinh3.live/assets/images/logo.png",
                "group": "Thiên Đình TV",
                "display": "thumbnail-only"
            })

        monplayer_json = {
            "name": "Thiên Đình TV",
            "author": "Mạnh DZ",
            "urls": urls_list
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*') 
        self.end_headers()
        self.wfile.write(json.dumps(monplayer_json, ensure_ascii=False, indent=2).encode('utf-8'))
        return
        
