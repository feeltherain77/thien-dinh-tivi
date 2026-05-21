from http.server import BaseHTTPRequestHandler
import requests
import re
import json
import hashlib

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Sử dụng trạm trung chuyển AllOrigins để lách Cloudflare của Thiên Đình
        PROXY_URL = "https://api.allorigins.win/get?url=https://sv2.thiendinh3.live/trang-chu"
        
        channels_list = []
        
        try:
            response = requests.get(PROXY_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                html = data.get('contents', '')
                
                # Quét mọi link trận đấu trên trang chủ
                raw_matches = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
                
                for href, content in raw_matches:
                    match_url = href.strip()
                    
                    if not any(keyword in match_url for keyword in ['/match/', '/live/', '/truc-tiep/', '/xem']):
                        continue
                        
                    if match_url.startswith('/'):
                        match_url = "https://sv2.thiendinh3.live" + match_url
                        
                    # Tránh quét trùng bài
                    if any(c['sources'][0]['contents'][0]['stream_links'][0]['url'] == match_url for c in channels_list if c.get('sources')):
                        continue

                    clean_content = re.sub(r'<[^>]+>', ' ', content)
                    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                    
                    if len(clean_content) < 5:
                        continue

                    # ⏳ Bắt giờ thi đấu
                    time_search = re.search(r'(\d{2}:\d{2})', clean_content)
                    match_time = time_search.group(1) if time_search else "LIVE"

                    # 🎙️ Bắt tên BLV
                    blv_search = re.search(r'(BLV\s+[^<|\s]+)', clean_content, re.IGNORECASE)
                    blv_name = blv_search.group(1).strip() if blv_search else "Mỳ Tôm"

                    # 🖼️ Bắt logo
                    logo_search = re.search(r'(?:src|data-src)="([^"]+)"', content)
                    match_logo = logo_search.group(1) if logo_search else "https://sv2.thiendinh3.live/assets/images/logo.png"
                    if match_logo.startswith('/'):
                        match_logo = "https://sv2.thiendinh3.live" + match_logo

                    # ⚽ Bắt tên trận đấu
                    match_name = clean_content.replace(match_time, "").replace(blv_name, "").strip()
                    match_name = " ".join(match_name.split())
                    if not match_name or len(match_name) < 3:
                        match_name = "Trận Đấu Đang Diễn Ra"

                    # Tạo ID hash cho đồng bộ các tầng dữ liệu
                    hash_id = hashlib.md5(match_url.encode('utf-8')).hexdigest()[:12]

                    # Thêm trận vào danh sách channels theo cấu trúc nâng cao
                    channels_list.append({
                        "id": f"td-{hash_id}",
                        "name": match_name,
                        "type": "single",
                        "display": "thumbnail-only",
                        "enable_detail": False,
                        "image": {
                            "padding": 1,
                            "background_color": "#ececec",
                            "display": "contain",
                            "url": match_logo
                        },
                        "labels": [
                            {"text": f"⏳ {match_time}", "position": "top-left", "color": "#aa000000", "text_color": "#ffffff"},
                            {"text": f"🎙️ {blv_name}", "position": "top-right", "color": "#aa000000", "text_color": "#00ff00"}
                        ],
                        "sources": [
                            {
                                "id": f"src-{hash_id}",
                                "name": "Thiên Đình TV",
                                "contents": [
                                    {
                                        "id": f"ctx-{hash_id}",
                                        "name": "F",
                                        "stream_links": [
                                            {
                                                "id": f"lnk-{hash_id}",
                                                "name": "Link Live",
                                                "url": match_url
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    })
        except:
            pass

        # Dự phòng nếu trống trận
        if not channels_list:
            channels_list.append({
                "id": "td-fallback",
                "name": "Vào trực tiếp trang chủ Thiên Đình TV",
                "type": "single",
                "display": "thumbnail-only",
                "enable_detail": False,
                "image": {
                    "padding": 1,
                    "background_color": "#ececec",
                    "display": "contain",
                    "url": "https://sv2.thiendinh3.live/assets/images/logo.png"
                },
                "labels": [{"text": "LIVE", "position": "top-left", "color": "#ff0000", "text_color": "#ffffff"}],
                "sources": [
                    {
                        "id": "src-fallback",
                        "name": "Thiên Đình TV",
                        "contents": [
                            {
                                "id": "ctx-fallback",
                                "name": "F",
                                "stream_links": [
                                    {"id": "lnk-fallback", "name": "Link Gốc", "url": "https://sv2.thiendinh3.live/trang-chu"}
                                ]
                            }
                        ]
                    }
                ]
            })

        # 👑 BỌC NGOÀI BẰNG CẤU TRÚC GỐC CHUẨN ĐÉT CỦA HỘI QUÁN
        monplayer_json = {
            "id": "thiendinh",
            "url": "https://thiendinh-tivi.vercel.app",  # URL con bot của bạn
            "name": "Thiên Đình TV",
            "color": "#1cb57a",
            "grid_number": 3,
            "image": {
                "type": "cover",
                "url": "https://sv2.thiendinh3.live/assets/images/logo.png"
            },
            "notice": {
                "closeable": True,
                "icon": "https://kaytee1012.github.io/pngegg.png",
                "id": "notice",
                "link": "https://sv2.thiendinh3.live",
                "text": "Chào mừng bạn đến với kênh Thiên Đình TV - Mạnh DZ"
            },
            "groups": [
                {
                    "id": "live",
                    "name": "🔴 Live bóng đá",
                    "display": "vertical",
                    "grid_number": 2,
                    "enable_detail": False,
                    "channels": channels_list
                }
            ]
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*') 
        self.end_headers()
        self.wfile.write(json.dumps(monplayer_json, ensure_ascii=False, indent=2).encode('utf-8'))
        return
