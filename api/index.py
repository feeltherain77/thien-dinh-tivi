from http.server import BaseHTTPRequestHandler
import requests
import re
import json

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        TARGET_URL = "https://sv2.thiendinh3.live/trang-chu"
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        urls_list = []
        
        try:
            response = requests.get(TARGET_URL, headers=headers, timeout=8)
            if response.status_code == 200:
                html = response.text
                
                # Bắt tất cả các thẻ <a> chứa link trận đấu
                raw_matches = re.findall(r'<a[^>]*href="([^"]*(?:/match/|/live/)[^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
                
                for href, content in raw_matches:
                    # Xử lý URL trận đấu
                    match_url = href.strip()
                    if match_url.startswith('/'):
                        match_url = "https://sv2.thiendinh3.live" + match_url
                        
                    if any(u['url'] == match_url for u in urls_list):
                        continue

                    clean_content = re.sub(r'\s+', ' ', content)

                    # ⏳ Bắt giờ thi đấu
                    time_search = re.search(r'(\d{2}:\d{2})', clean_content)
                    match_time = time_search.group(1) if time_search else "LIVE"

                    # 🎙️ Bắt tên BLV
                    blv_search = re.search(r'(BLV\s+[^<|\s]+(?:[^<|\s]+)?)(?:\s+)?', clean_content, re.IGNORECASE)
                    blv_name = blv_search.group(1).strip() if blv_search else "Mỳ Tôm"

                    # 🖼️ Bắt logo trận đấu
                    logo_search = re.search(r'(?:src|data-src)="([^"]+)"', clean_content)
                    match_logo = logo_search.group(1) if logo_search else ""
                    if match_logo.startswith('/'):
                        match_logo = "https://sv2.thiendinh3.live" + match_logo
                    if not match_logo:
                        match_logo = "https://sv2.thiendinh3.live/assets/images/logo.png"

                    # ⚽ Bắt tên trận đấu
                    text_pure = re.sub(r'<[^>]+>', ' ', content)
                    text_pure = text_pure.replace(match_time, "").replace(blv_name, "").strip()
                    match_name = " ".join(text_pure.split())
                    
                    if not match_name or len(match_name) < 3:
                        match_name = "Trận Đấu Đang Diễn Ra"

                    display_name = f"[{match_time}] {match_name} ({blv_name})"
                    
                    urls_list.append({
                        "name": display_name,
                        "url": match_url,
                        "logo": match_logo,
                        "group": "Thiên Đình TV Live"
                    })
        except:
            pass

        if not urls_list:
            urls_list.append({
                "name": "[LIVE] Vào thẳng trang chủ Thiên Đình TV",
                "url": TARGET_URL,
                "logo": "https://sv2.thiendinh3.live/assets/images/logo.png",
                "group": "Thiên Đình TV"
            })

        # Đổi tên hiển thị gốc của danh sách tại đây
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
                    
