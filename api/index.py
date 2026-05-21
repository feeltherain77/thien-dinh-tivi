from http.server import BaseHTTPRequestHandler
import requests
import re
import json
import hashlib

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Dùng trung gian AllOrigins lách Cloudflare chặn bot của Vercel
        PROXY_URL = "https://api.allorigins.win/get?url=https://sv2.thiendinh3.live/trang-chu"
        
        channels_list = []
        
        try:
            response = requests.get(PROXY_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                html = data.get('contents', '')
                
                # Quét link các trận đấu trên trang chủ
                raw_matches = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
                
                for href, content in raw_matches:
                    match_url = href.strip()
                    
                    if not any(keyword in match_url for keyword in ['/match/', '/live/', '/truc-tiep/', '/xem']):
                        continue
                        
                    if match_url.startswith('/'):
                        match_url = "https://sv2.thiendinh3.live" + match_url
                        
                    # Chặn quét trùng lặp dữ liệu
                    if any(c['sources'][0]['contents'][0]['streams'][0]['stream_links'][0]['url'] == match_url for c in channels_list if c.get('sources')):
                        continue

                    # Làm sạch HTML bóc chữ lấy thông tin trận đấu
                    clean_content = re.sub(r'<[^>]+>', ' ', content)
                    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                    
                    if len(clean_content) < 5:
                        continue

                    # Tách lấy Giờ thi đấu (xx:xx)
                    time_search = re.search(r'(\d{2}:\d{2})', clean_content)
                    match_time = time_search.group(1) if time_search else "LIVE"

                    # Tách lấy tên BLV
                    blv_search = re.search(r'(BLV\s+[^<|\s]+)', clean_content, re.IGNORECASE)
                    blv_name = blv_search.group(1).strip() if blv_search else "Mỳ Tôm"

                    # Tách lấy Logo trận đấu
                    logo_search = re.search(r'(?:src|data-src)="([^"]+)"', content)
                    match_logo = logo_search.group(1) if logo_search else "https://sv2.thiendinh3.live/assets/images/logo.png"
                    if match_logo.startswith('/'):
                        match_logo = "https://sv2.thiendinh3.live" + match_logo

                    # Tách lấy tên trận đấu (Xóa giờ và BLV ra khỏi chuỗi tên)
                    match_name = clean_content.replace(match_time, "").replace(blv_name, "").strip()
                    match_name = " ".join(match_name.split())
                    if not match_name or len(match_name) < 3:
                        match_name = "Trận Đấu Đang Diễn Ra"

                    # Tạo mã ID băm để đồng bộ các nhánh con
                    hash_id = hashlib.md5(match_url.encode('utf-8')).hexdigest()[:12]

                    # 👑 XÂY DỰNG KHUÔN 6 TẦNG CHUẨN ĐÉT HỘI QUÁN TV
                    channels_list.append({
                        "id": f"td-{hash_id}",
                        "name": f"⚽ {match_name} | {match_time}",
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
                            {
                                "text": "● Live" if match_time == "LIVE" else f"⏳ {match_time}",
                                "position": "top-left",
                                "color": "#00ffffff",
                                "text_color": "#ff0000" if match_time == "LIVE" else "#d54f1a"
                            }
                        ],
                        "sources": [
                            {
                                "id": f"src-{hash_id}",
                                "name": "Thiên Đình",
                                "contents": [
                                    {
                                        "id": f"ctx-{hash_id}",
                                        "name": match_name,
                                        "streams": [
                                            {
                                                "id": f"strm-{hash_id}",
                                                "name": f"BLV {blv_name}",
                                                "stream_links": [
                                                    {
                                                        "id": f"lnk-{hash_id}",
                                                        "name": "Link 1",
                                                        "type": "webview", # Sử dụng webview để hiển thị player của web
                                                        "default": True,
                                                        "url": match_url
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    })
        exceptException as e:
            pass

        # Bản backup phòng hờ lúc không cào được trận nào hoặc lỗi kết nối
        if not channels_list:
            channels_list.append({
                "id": "td-fallback",
                "name": "⚽ Vào trang chủ Thiên Đình TV | LIVE",
                "type": "single",
                "display": "thumbnail-only",
                "enable_detail": False,
                "image": {
                    "padding": 1,
                    "background_color": "#ececec",
                    "display": "contain",
                    "url": "https://sv2.thiendinh3.live/assets/images/logo.png"
                },
                "labels": [{"text": "● Live", "position": "top-left", "color": "#00ffffff", "text_color": "#ff0000"}],
                "sources": [
                    {
                        "id": "src-fallback",
                        "name": "Thiên Đình",
                        "contents": [
                            {
                                "id": "ctx-fallback",
                                "name": "Trang Chủ",
                                "streams": [
                                    {
                                        "id": "strm-fallback",
                                        "name": "Mặc Định",
                                        "stream_links": [
                                            {
                                                "id": "lnk-fallback",
                                                "name": "Link Gốc",
                                                "type": "webview",
                                                "default": True,
                                                "url": "https://sv2.thiendinh3.live/trang-chu"
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            })

        # 👑 BỌC ĐẦU FILE Y HỆT DỮ LIỆU GỐC CỦA HỘI QUÁN TV
        monplayer_json = {
            "id": "thiendinh",
            "url": "https://thiendinh-tivi.vercel.app", # Thay bằng link Vercel của bạn nếu thích
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
                                 
