import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from supabase import create_client, Client
import json
import base64
import os
import re
import time
import ast
from datetime import datetime, timedelta

# ==============================================================================
# 1. CẤU HÌNH GIAO DIỆN & KẾT NỐI
# ==============================================================================
st.set_page_config(page_title="Universal AI Video Studio Pro", page_icon="🎬", layout="wide")

st.markdown("""
<style>
    .header-container { text-align: center; padding: 1.2rem; background: radial-gradient(circle, rgba(255,75,75,0.08) 0%, rgba(255,255,255,0) 70%); border-radius: 16px; margin-bottom: 1rem; }
    .main-title { font-size: 2.2rem !important; font-weight: 900 !important; background: linear-gradient(90deg, #ff0050 0%, #ff5252 50%, #ff7300 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important; color: white !important; border-radius: 8px !important; font-weight: bold; width: 100%; }
    div[data-testid="stButton"] > button[kind="secondary"] { background: linear-gradient(135deg, #ff4b4b 0%, #ff7300 100%) !important; color: #ffffff !important; box-shadow: 0 3px 8px rgba(255, 75, 75, 0.35) !important; padding: 0.55rem 1rem !important; font-weight: bold !important; border: none !important; }
    div[data-testid="stButton"] > button[kind="secondary"]:hover { transform: translateY(-1px) !important; box-shadow: 0 5px 14px rgba(255, 75, 75, 0.5) !important; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 3px 8px; border-radius: 4px; font-size: 11px; border: 1px solid #bbf7d0; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 3px 8px; border-radius: 4px; font-size: 11px; border: 1px solid #fde68a; }
    .custom-card { background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
    .support-box { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1.5px solid #86efac; border-radius: 12px; padding: 12px; text-align: center; margin-top: 15px; }
    .btn-zalo { background: #0068FF; color: white !important; font-weight: 900; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 15px; border: 1px solid #0056d6; }
    .btn-fb { background: #1877F2; color: white !important; font-weight: 900; padding: 8px 24px; border-radius: 8px; text-decoration: none; font-size: 16px; border: 1px solid #166fe5; font-family: serif; }
    .btn-tt { background: #000000; color: white !important; font-weight: 900; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 15px; border: 1px solid #333; }
    .social-icons-container { display: flex; gap: 12px; justify-content: center; margin-top: 10px; margin-bottom: 10px; }
    @keyframes pulse { 0% { transform: scale(0.98); opacity: 0.8; } 50% { transform: scale(1.01); opacity: 1; } 100% { transform: scale(0.98); opacity: 0.8; } }
    .loading-pulse { animation: pulse 1.5s infinite ease-in-out; color: #d90429; font-weight: 800; text-align: center; padding: 25px; background: #fef2f2; border: 2px dashed #fca5a5; border-radius: 12px; margin: 20px 0; }
    .detail-header-box { background: #eff6ff; border: 1.5px solid #bfdbfe; border-radius: 10px; padding: 15px; margin-bottom: 20px; color: #1e3a8a; }
    .voiceover-text { color: #15803d; background: #f0fdf4; padding: 4px 8px; border-radius: 6px; font-family: monospace; font-size: 15px; border: 1px solid #bbf7d0; }
    .scrollable-sidebar-container { max-height: 380px; overflow-y: auto; padding-right: 5px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

ALL_MODULES = ["🛒 TikTok Shop & Bán Hàng", "🌟 Viral & Xây Kênh"]
ADMIN_EMAIL = "binhnguyenmedia.vn@gmail.com"
ACCOUNTS_FILE = "accounts.json"

@st.cache_resource
def init_supabase():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None
supabase = init_supabase()

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
client = genai.Client(api_key=api_key) if api_key else None

def load_licensed_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {ADMIN_EMAIL: {"roles": ALL_MODULES, "phone": "0968484369", "expires_at": "2099-12-31"}}

def save_licensed_accounts(acc_dict):
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(acc_dict, f, ensure_ascii=False, indent=2)
    except: pass

def safe_copy_button(text_to_copy: str, button_label: str = "📋 Sao Chép Prompt"):
    b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    html_id = f"btn_{int(time.time()*10000)}_{len(text_to_copy)}"
    html_code = f"""
    <button id="{html_id}" style="background:#16a34a; color:white; border:none; padding:8px 16px; font-size:13px; font-weight:700; border-radius:6px; cursor:pointer; width:100%; transition: 0.2s;">{button_label}</button>
    <script>
    document.getElementById("{html_id}").addEventListener("click", function() {{
        const text = decodeURIComponent(escape(atob("{b64}")));
        navigator.clipboard.writeText(text).then(function() {{
            document.getElementById("{html_id}").innerText = "✅ Đã sao chép!";
            document.getElementById("{html_id}").style.background = "#15803d";
            setTimeout(function() {{
                document.getElementById("{html_id}").innerText = "{button_label}";
                document.getElementById("{html_id}").style.background = "#16a34a";
            }}, 2000);
        }}).catch(function(err) {{
            const textArea = document.createElement("textarea");
            textArea.value = text; document.body.appendChild(textArea); textArea.select();
            try {{ document.execCommand('copy'); document.getElementById("{html_id}").innerText = "✅ Đã sao chép!"; }} catch (e) {{}}
            document.body.removeChild(textArea);
        }});
    }});
    </script>
    """
    components.html(html_code, height=45)

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict): return "<br>".join([f"• <b>{str(k).replace('_', ' ').title()}:</b> {str(v)}" for k, v in field_val.items()])
    elif isinstance(field_val, list): return "<br>".join([f"• {str(item)}" for item in field_val])
    text = str(field_val).strip()
    text = re.sub(r'<<\.?', '', text).replace('<b>', '').replace('</b>', '')
    lines = [l.strip() for l in text.split('<br>') if l.strip()]
    formatted = [f"<div style='margin-top: 6px;'>{line}</div>" if line.startswith('•') else f"<div style='margin-left: 15px; margin-top: 4px;'>• {line}</div>" for line in lines if line]
    return "".join(formatted) if formatted else text

for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", load_licensed_accounts()),
    ("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []),
    ("generated_details", {}), ("content_analysis", None), ("active_script_id", None),
    ("current_input_context", ""), ("current_product_data_saved", None), ("current_product_data", None),
    ("action_trigger", None), ("action_param", None), ("reset_key", 0),
    ("scroll_to_top", False),
    ("extra_angle_type", "⚡ Dạng Flash Sale & Deal hời (Tập trung chốt đơn)"),
    ("extra_num_chars", 1),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"),
    ("last_mode", ""), ("last_style", ""), ("last_aspect", "9:16 (Dọc TikTok/Reels)"), ("last_narrator", ""),
    ("character_profiles", []), ("editing_acc_email", None), ("current_project_id", None)
]:
    if key not in st.session_state: st.session_state[key] = default_val

if st.session_state.scroll_to_top:
    components.html("<script>window.parent.scrollTo({top: 0, behavior: 'smooth'});</script>", height=0)
    st.session_state.scroll_to_top = False

# ==============================================================================
# 2. HÀM AI LÕI & CHÍNH SÁCH KIỂM DUYỆT SẢN PHẨM & NGỮ ĐIỆU CHUYÊN SÂU
# ==============================================================================
def clean_and_parse_json(text_content: str):
    cleaned = re.sub(r'```(?:json)?', '', text_content).strip()
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    if match: cleaned = match.group(0)
    try:
        parsed = json.loads(cleaned, strict=False)
        return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else parsed
    except json.JSONDecodeError:
        try:
            py_str = cleaned.replace('true', 'True').replace('false', 'False').replace('null', 'None')
            parsed = ast.literal_eval(py_str)
            return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else parsed
        except Exception:
            raise Exception("AI sinh JSON lỗi cấu trúc. Vui lòng thử lại.")

def call_gemini(contents, sys_inst="Bạn là AI hỗ trợ JSON."):
    for attempt in range(3):
        try:
            res = client.models.generate_content(
                model="gemini-3.6-flash", contents=contents,
                config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.7)
            )
            return clean_and_parse_json(res.text)
        except Exception as e:
            if attempt == 2: raise e
            time.sleep(2)

def generate_char_rules_string(profiles):
    if not profiles: return "🔹 NHÂN VẬT & DIỆN MẠO: Giữ nguyên 100% khuôn mặt, kiểu tóc, vóc dáng của diễn viên gốc."
    rules = "🔹 KHÓA CỨNG DIỆN MẠO KOC & ĐỒNG NHẤT 100%:\n"
    for p in profiles: 
        rules += f"   + Nhân vật {p['id']} ({p['role']}): Bắt buộc sử dụng lệnh 'Character {p['id']} featuring exact facial identity, exact hairstyle, exact body shape, and exact reference image {p['id']}' trong mọi khung hình.\n"
    return rules

def get_dynamic_realtime_context():
    now = datetime.now()
    month = now.month
    year = now.year
    if month in [12, 1, 2]: season_desc = f"Mùa Đông / Tết Nguyên Đán ({month}/{year})."
    elif month in [3, 4, 5]: season_desc = f"Mùa Xuân / Giao mùa ({month}/{year})."
    elif month in [6, 7, 8]: season_desc = f"Mùa Hè / Nắng Nóng ({month}/{year})."
    else: season_desc = f"Mùa Thu / Se Lạnh ({month}/{year})."
    return f"THỜI GIAN THỰC TẾ: {season_desc}. Toàn bộ bối cảnh, ánh sáng, trang phục phải phản ánh chính xác thời điểm thực tế này."

def get_system_instructions_for_details(mode, style, aspect, narrator_mode, char_rules):
    time_ctx = get_dynamic_realtime_context()
    is_on_camera = "On-camera" in narrator_mode
    narrator_instruction = "Nhân vật xuất hiện trực tiếp nói chuyện trước ống kính, đồng bộ khẩu hình miệng (Lip-sync khớp lời thoại)." if is_on_camera else "Lồng tiếng ngoài khung hình (Off-screen voiceover), tập trung quay cận cảnh sản phẩm và bối cảnh."
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL CHO VEO 3 VÀ IMAGEN 3. THỂ LOẠI: {mode} | PHONG CÁCH: {style} | ĐỊNH DẠNG: {aspect}
    {time_ctx}
    🛑 QUY TẮC AN TOÀN SẢN PHẨM & CHÍNH SÁCH NỀN TẢNG (TIKTOK SHOP, SHOPEE VIDEO, REELS, SHORTS...):
    1. DANH MỤC CẤM & HẠN CHẾ: 
       - CẤM TUYỆT ĐỐI các sản phẩm y dược, thuốc chữa bệnh, thực phẩm chức năng cam kết trị bệnh triệt để.
       - Ngành Mẹ & Bé / Trẻ em: Tuyệt đối không để trẻ em một mình trong cảnh quay, không chứa yếu tố nguy hiểm, không dùng từ ngữ phóng đại y tế.
    2. CẤM BÁO GIÁ CỤ THỂ: Tuyệt đối KHÔNG đưa giá tiền bằng con số (VD: cấm "99k", "150 nghìn"). Chỉ dùng từ hướng dẫn ưu đãi ("deal hời", "giá sốc góc màn hình").
    3. HÌNH THỨC THUYẾT MINH: {narrator_instruction}
    4. ĐẠO DIỄN NGỮ ĐIỆU & SFX (BẮT BUỘC ĐỊNH DẠNG RÕ RÀNG): Phải chỉ định rõ Giới tính & Vùng miền chuẩn (VD: "Giọng Nữ Miền Bắc (chuẩn)" hoặc "Giọng Nam Miền Bắc (chuẩn)"), kết hợp cùng Tông giọng và Mục đích ngữ điệu cụ thể (VD: "nhịp độ nhanh, dồn dập, nhằm kích thích hối hả chốt đơn").
    5. ĐỒNG NHẤT 100%: Giữ nguyên trang phục, kiểu tóc, khuôn mặt KOC và bối cảnh ở mọi cảnh.
    6. CƠ CHẾ CẢNH NỐI TIẾP & ANCHOR FRAME: Dùng "Chuyển cảnh mới (Tạo ảnh mới)" hoặc "Cảnh nối tiếp (Dùng lại ảnh cuối)" với lệnh neo hình `holding the final frame steady as a reference anchor`.
    7. {char_rules}
    """

def create_scene_details(target_id, mode, style, aspect, narrator_mode, char_rules):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if sc["id"] == target_id), None)
    if not outline: return
    
    time_ctx = get_dynamic_realtime_context()
    is_on_camera = "On-camera" in narrator_mode
    
    if is_on_camera:
        vid_p_1 = "Vertical 9:16 video, strict standard Northern Vietnamese accent, character talking directly to camera, speaking the Vietnamese line: 'Trằn trọc cả đêm... vì chăn ga cũ vừa hầm nóng, vừa rít da?' with perfect lip-sync matching the speech, maintaining exact facial identity, exact hairstyle, and exact outfit from reference..."
        vid_p_2 = "Extreme close-up shot, strict standard Northern Vietnamese accent, character talking directly to camera, speaking the Vietnamese line: 'Thời tiết sang thu rồi..., đổi ngay bộ chăn ga lụa Thái này thôi!' with perfect lip-sync matching the speech, holding the final frame steady as a reference anchor for the next shot..."
    else:
        vid_p_1 = "Vertical 9:16 video, strict standard Northern Vietnamese accent, off-screen voiceover with emotional pauses, maintaining exact outfit and setting..."
        vid_p_2 = "Extreme close-up shot, strict standard Northern Vietnamese accent, off-screen voiceover, holding the final frame steady as a reference anchor..."

    prompt = f"""
    {time_ctx}
    Viết chi tiết kịch bản ID {target_id}: '{outline.get('title')}'. Hook: {outline.get('target_hook')}. Bối cảnh: {outline.get('setting_style')}.
    THUYẾT MINH: {'Nhân vật xuất hiện nói chuyện trực tiếp, lip-sync khớp khẩu hình miệng' if is_on_camera else 'Lồng tiếng ngoài khung hình, tập trung show sản phẩm'}.
    TRẢ VỀ ĐÚNG 1 DICT JSON GỒM CÁC KEY SAU:
    {{
        "title": "{outline.get('title')}",
        "total_estimated_duration": "24s (0.4 phút)",
        "script_outfit_setup": "Nữ diễn viên mặc bộ đồ lụa dài tay màu kem beige đồng bộ từ áo đến quần dài, đi dép trong nhà màu trắng, tóc buộc gọn gàng",
        "voice_profile": {{"gender": "Nữ", "tone": "nhịp độ linh hoạt theo cảm xúc kịch bản, giọng Miền Bắc chuẩn, giữ nguyên âm sắc"}},
        "scenes": [
            {{
                "scene_number": 1, "duration": "8s", "transition_type": "Chuyển cảnh mới (Tạo ảnh mới)", "scene_setting": "Góc toàn cảnh phòng ngủ ấm cúng...",
                "voice_director_vn": "Giọng Nữ Miền Bắc (chuẩn) — Tông giọng trầm lắng, ngắt nghỉ cảm xúc, nhằm khơi gợi nỗi đau khó ngủ.", "voiceover_vi": "Trằn trọc cả đêm... vì chăn ga cũ vừa hầm nóng, vừa rít da?",
                "image_prompt": "Cinematic vertical 9:16 photo of...", "video_prompt": "{vid_p_1}"
            }},
            {{
                "scene_number": 2, "duration": "6s", "transition_type": "Cảnh nối tiếp (Dùng lại ảnh cuối)", "scene_setting": "Góc quay cận cảnh tiếp nối...",
                "voice_director_vn": "Giọng Nữ Miền Bắc (chuẩn) — Tông giọng hào hứng, dồn dập, nhằm kích thích chốt đơn ngay.", "voiceover_vi": "Thời tiết sang thu rồi..., đổi ngay bộ chăn ga lụa Thái này thôi!",
                "image_prompt": "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video", "video_prompt": "{vid_p_2}"
            }}
        ]
    }}
    Lưu ý: "scenes" phải có 3 hoặc 4 phần tử. Các "duration" CHỈ được là "4s", "6s", "8s". TUYỆT ĐỐI CẤM BÁO GIÁ CỤ THỂ VÀ VI PHẠM Y TẾ/MẸ BÉ. KHÔNG DÙNG DẤU NGOẶC KÉP CHƯA ESCAPE.
    """
    res = call_gemini([prompt], get_system_instructions_for_details(mode, style, aspect, narrator_mode, char_rules))
    st.session_state.generated_details[target_id] = res

def clone_script(script_id):
    mode = st.session_state.get("last_mode", "Bán Hàng")
    style = st.session_state.get("last_style", "Điện ảnh")
    aspect = st.session_state.get("last_aspect", "9:16 (Dọc TikTok/Reels)")
    narrator = st.session_state.get("last_narrator", "On-camera")
    char_rules = generate_char_rules_string(st.session_state.get("character_profiles", []))
    
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if sc["id"] == script_id), None)
    cur_len = len(all_combined)
    
    time_ctx = get_dynamic_realtime_context()
    dna_str = json.dumps(st.session_state.content_analysis, ensure_ascii=False) if st.session_state.content_analysis else "Chưa có dữ liệu"
    
    prompt = f"""
    {time_ctx}
    DỮ LIỆU SẢN PHẨM GỐC: {dna_str}
    Nhân bản kịch bản gốc: {json.dumps(target, ensure_ascii=False)}. 
    Dựa BẮT BUỘC vào dữ liệu Sản phẩm Gốc ở trên, tạo chính xác 5 biến thể mới tuân thủ tuyệt đối chính sách (không báo giá, không vi phạm y tế/mẹ bé), có đầy đủ dấu câu ngắt nghỉ cảm xúc. 
    BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON GỒM CÁC KEY SAU:
    {{
        "script_outlines": [
            {{
                "id": {cur_len+1},
                "title": "Tên kịch bản",
                "setting_style": "Bối cảnh thực tế",
                "target_hook": "Viết 2-3 câu tóm tắt chi tiết diễn biến kịch bản và câu thoại Hook mở đầu an toàn chính sách"
            }}
        ]
    }}
    LƯU Ý: TRẢ VỀ ĐÚNG 5 PHẦN TỬ TRONG MẢNG `script_outlines`. CẤM BÁO GIÁ VÀ VI PHẠM Y TẾ.
    """
    res = call_gemini([prompt], get_system_instructions_for_details(mode, style, aspect, narrator_mode, char_rules))
    clones = res.get("script_outlines", [])
    for idx, cl in enumerate(clones): cl["id"] = cur_len + idx + 1
    return clones

def generate_more_scripts(angle, num_chars):
    mode = st.session_state.get("last_mode", "Bán Hàng")
    style = st.session_state.get("last_style", "Điện ảnh")
    aspect = st.session_state.get("last_aspect", "9:16 (Dọc TikTok/Reels)")
    narrator = st.session_state.get("last_narrator", "On-camera")
    char_rules = generate_char_rules_string(st.session_state.get("character_profiles", []))
    
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    cur_len = len(all_combined)
    
    time_ctx = get_dynamic_realtime_context()
    prod_ctx = f"THÔNG TIN NGƯỜI DÙNG NHẬP: {st.session_state.current_input_context}"
    db_ctx = f"SẢN PHẨM (DB): {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)}" if st.session_state.current_product_data_saved else ""
    dna_ctx = f"DNA SẢN PHẨM GỐC: {json.dumps(st.session_state.content_analysis, ensure_ascii=False)}" if st.session_state.content_analysis else ""
    
    prompt = f"""
    {time_ctx}
    {prod_ctx}
    {db_ctx}
    {dna_ctx}
    
    🛑 YÊU CẦU MỞ RỘNG (BẮT BUỘC TUÂN THỦ CHÍNH SÁCH):
    1. GIỮ NGUYÊN SẢN PHẨM GỐC. CẤM BÁO GIÁ TIỀN CỤ THỂ VÀ CẤM VI PHẠM Y TẾ / MẸ BÉ.
    2. ĐỊNH HƯỚNG CHIẾN LƯỢC: '{angle}'.
    3. THỜI GIAN THỰC & CẢM XÚC: Kịch bản phải phù hợp với thời điểm hiện tại, có dấu câu ngắt nghỉ rõ ràng.
    4. SỐ LƯỢNG DIỄN VIÊN: {num_chars} nhân vật.
    5. BẮT BUỘC TẠO CHÍNH XÁC 5 KỊCH BẢN MỚI TRONG MẢNG `script_outlines`.
    
    BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON GỒM CÁC KEY SAU:
    {{
        "script_outlines": [
            {{
                "id": {cur_len+1},
                "title": "Tên kịch bản chuẩn chiến lược",
                "setting_style": "Bối cảnh thực tế",
                "target_hook": "Viết 2-3 câu tóm tắt chi tiết diễn biến kịch bản theo đúng chiến lược '{angle}' kèm câu thoại Hook mở đầu an toàn"
            }}
        ]
    }}
    LƯU Ý: TRẢ VỀ ĐÚNG 5 PHẦN TỬ. CẤM BÁO GIÁ.
    """
    res = call_gemini([prompt], get_system_instructions_for_details(mode, style, aspect, narrator_mode, char_rules))
    more_scripts = res.get("script_outlines", [])
    for idx, sc in enumerate(more_scripts): sc["id"] = cur_len + idx + 1
    return more_scripts

def save_project_to_db(email, title, payload_data, project_id=None):
    if not supabase: return "Chưa kết nối Database Supabase."
    try:
        clean_content = json.loads(json.dumps(payload_data, default=str)) 
        if project_id:
            supabase.table("saved_projects").update({
                "project_title": title,
                "script_content": clean_content
            }).eq("id", project_id).execute()
        else:
            data = {"user_email": email, "project_title": title, "script_content": clean_content}
            res = supabase.table("saved_projects").insert(data).execute()
            if res.data and len(res.data) > 0:
                st.session_state.current_project_id = res.data[0]['id']
        return True
    except Exception as e:
        err_msg = str(e)
        if "Name or service not known" in err_msg or "Errno -2" in err_msg:
            return "Sai đường link Supabase (Thiếu https:// hoặc bị lỗi đánh máy) trong cài đặt Secrets."
        return err_msg

# ==============================================================================
# 3. THANH BÊN (SIDEBAR) & TÀI KHOẢN
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        st.markdown("### 🔐 ĐĂNG NHẬP")
        email_input = st.text_input("Nhập Email:", key="login_email_input")
        if st.button("🔑 Đăng Nhập", type="primary"):
            with st.spinner("⏳ Đang xác thực đăng nhập..."):
                email_check = email_input.strip()
                if email_check in st.session_state.licensed_accounts:
                    acc_info = st.session_state.licensed_accounts[email_check]
                    exp_date_str = acc_info.get("expires_at", "2099-12-31")
                    try:
                        exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
                        if datetime.now() > exp_date:
                            st.error(f"❌ Tài khoản đã hết hạn vào ngày {exp_date_str}! Vui lòng liên hệ Admin để gia hạn.")
                            st.stop()
                    except: pass
                    
                    st.session_state.is_logged_in = True
                    st.session_state.current_email = email_check
                    st.toast("✅ Đăng nhập thành công!")
                    st.rerun()
                else: 
                    st.error("Tài khoản chưa được cấp quyền!")
    else:
        current_acc = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        exp_date_str = current_acc.get("expires_at", "2099-12-31")
        if current_acc and st.session_state.current_email != ADMIN_EMAIL:
            try:
                exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
                days_left = (exp_date - datetime.now()).days
                if 0 <= days_left <= 7:
                    st.warning(f"⚠️ **CẢNH BÁO:** Tài khoản của bạn sẽ hết hạn sau **{days_left} ngày nữa** ({exp_date_str}). Vui lòng liên hệ hotline bên dưới để gia hạn!")
            except: pass

        st.markdown("### 🗂 LÀM VIỆC")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True):
            with st.spinner("⏳ Đang khởi tạo dự án mới..."):
                st.session_state.all_scripts, st.session_state.cloned_scripts, st.session_state.expanded_scripts = [], [], []
                st.session_state.generated_details, st.session_state.content_analysis = {}, None
                st.session_state.active_script_id = None
                st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
                st.session_state.current_input_context = ""
                st.session_state.current_product_data_saved = None
                st.session_state.character_profiles = []
                st.session_state.current_project_id = None
                st.session_state.reset_key += 1 
                st.toast("✅ Đã dọn dẹp và mở dự án mới sạch sẽ!")
                st.rerun()
            
        st.session_state.active_project_title = st.text_input("Tên dự án hiện tại:", st.session_state.active_project_title)
        if st.button("💾 Lưu Dự Án Này", use_container_width=True):
            with st.spinner("⏳ Đang lưu dữ liệu dự án vào Database... Vui lòng đợi..."):
                all_com = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
                if not all_com: 
                    st.warning("⚠️ Chưa có kịch bản nào để lưu!")
                else:
                    payload = {
                        "content_analysis": st.session_state.content_analysis,
                        "all_scripts": st.session_state.all_scripts,
                        "cloned_scripts": st.session_state.cloned_scripts,
                        "expanded_scripts": st.session_state.expanded_scripts,
                        "generated_details": st.session_state.generated_details,
                        "character_profiles": st.session_state.character_profiles,
                        "current_input_context": st.session_state.current_input_context
                    }
                    save_result = save_project_to_db(st.session_state.current_email, st.session_state.active_project_title, payload, st.session_state.current_project_id)
                    if save_result is True:
                        st.toast("✅ Đã cập nhật và lưu dự án thành công!")
                    else:
                        st.error(f"❌ {save_result}")
        
        st.markdown("---")
        st.markdown("### 📂 KHO LƯU TRỮ")
        if not supabase: st.error("Chưa kết nối Database.")
        else:
            try:
                if st.session_state.current_email == ADMIN_EMAIL: res = supabase.table("saved_projects").select("*").order("created_at", desc=True).execute()
                else: res = supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
                projects = res.data
            except: projects = []

            search_proj = st.text_input("🔍 Tìm kiếm dự án:", placeholder="Nhập tên hoặc ngày...", key="search_proj_input")
            if search_proj:
                projects = [p for p in projects if search_proj.lower() in p['project_title'].lower() or search_proj in p['created_at']]

            if not projects: st.info("Không tìm thấy dự án phù hợp.")
            else:
                st.markdown("<div class='scrollable-sidebar-container'>", unsafe_allow_html=True)
                for p in projects:
                    with st.expander(f"🎬 {p['project_title']}"):
                        st.caption(f"📅 {p['created_at'][:10]}")
                        if st.session_state.current_email == ADMIN_EMAIL: 
                            st.caption(f"👤 Tạo bởi: {p['user_email']}")
                        
                        col_open, col_del = st.columns(2)
                        with col_open:
                            if st.button("📂 Mở", key=f"open_{p['id']}", use_container_width=True):
                                with st.spinner("⏳ Đang khôi phục dữ liệu dự án..."):
                                    saved_data = p.get("script_content", {})
                                    if isinstance(saved_data, dict) and "all_scripts" in saved_data:
                                        st.session_state.content_analysis = saved_data.get("content_analysis")
                                        st.session_state.all_scripts = saved_data.get("all_scripts", [])
                                        st.session_state.cloned_scripts = saved_data.get("cloned_scripts", [])
                                        st.session_state.expanded_scripts = saved_data.get("expanded_scripts", [])
                                        raw_details = saved_data.get("generated_details", {})
                                        st.session_state.generated_details = {int(k): v for k, v in raw_details.items()} if raw_details else {}
                                        st.session_state.character_profiles = saved_data.get("character_profiles", [])
                                        st.session_state.current_input_context = saved_data.get("current_input_context", "")
                                    elif isinstance(saved_data, list):
                                        st.session_state.all_scripts = saved_data
                                        st.session_state.content_analysis = None
                                        st.session_state.cloned_scripts = []
                                        st.session_state.expanded_scripts = []
                                        st.session_state.generated_details = {}
                                    
                                    st.session_state.current_project_id = p['id']
                                    st.session_state.active_project_title = p['project_title']
                                    st.session_state.active_script_id = None
                                    st.session_state.reset_key += 1
                                    st.session_state.scroll_to_top = True
                                    st.toast("✅ Đã khôi phục toàn bộ không gian dự án!")
                                    st.rerun()
                        with col_del:
                            if st.button("🗑️ Xóa", key=f"del_{p['id']}", type="secondary", use_container_width=True):
                                supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                                st.toast("✅ Đã xóa dự án!")
                                st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        # QUẢN TRỊ ADMIN
        if st.session_state.current_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙️ QUẢN TRỊ ADMIN")
            
            st.markdown("##### 🚨 Khách Sắp/Đã Hết Hạn")
            expired_or_soon = []
            for acc, info in st.session_state.licensed_accounts.items():
                if acc == ADMIN_EMAIL: continue
                exp_str = info.get("expires_at", "2099-12-31")
                try:
                    exp_dt = datetime.strptime(exp_str, "%Y-%m-%d")
                    d_left = (exp_dt - datetime.now()).days
                    if d_left <= 7:
                        expired_or_soon.append((acc, info.get('phone', ''), d_left, exp_str))
                except: pass
            
            if expired_or_soon:
                for cust, phone, d_left, exp_str in expired_or_soon:
                    status_text = f"Đã quá hạn {abs(d_left)} ngày" if d_left < 0 else (f"Hết hạn hôm nay!" if d_left == 0 else f"Còn {d_left} ngày")
                    with st.container(border=True):
                        st.markdown(f"**👤 {cust}**")
                        st.caption(f"📞 SĐT: {phone or 'Chưa có'}<br>⚠️ Trạng thái: <b>{status_text}</b> ({exp_str})", unsafe_allow_html=True)
                        if phone:
                            clean_phone = re.sub(r'\D', '', phone)
                            st.markdown(f"<a href='[https://zalo.me/](https://zalo.me/){clean_phone}' target='_blank' style='background:#0068ff; color:white; padding:5px 12px; border-radius:6px; text-decoration:none; font-size:12px; font-weight:700; display:inline-block; margin-top:5px;'>💬 Nhắn Zalo nhắc hạn</a>", unsafe_allow_html=True)
            else:
                st.caption("✅ Không có khách nào sắp hết hạn trong 7 ngày tới.")
            
            st.markdown("---")
            with st.form("add_license"):
                st.markdown("##### ➕ Cấp Quyền Khách Hàng Mới")
                new_acc = st.text_input("Email khách hàng:")
                new_phone = st.text_input("Số điện thoại (SĐT):", placeholder="Vd: 0968484369")
                assigned_modules = st.multiselect("Phân quyền thể loại:", options=ALL_MODULES, default=ALL_MODULES)
                duration_opt = st.selectbox("Thời hạn:", ["Dùng thử 3 ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "3 Năm", "5 Năm", "10 Năm", "Vĩnh viễn (Trọn đời)"])
                if st.form_submit_button("💾 Cấp Quyền & Lưu SĐT"):
                    with st.spinner("⏳ Đang cấp quyền..."):
                        exp_date = "2099-12-31" if "Vĩnh viễn" in duration_opt else (datetime.now() + timedelta(days=3 if "Dùng thử" in duration_opt else {"1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730, "3 Năm": 1095, "5 Năm": 1825, "10 Năm": 3650}.get(duration_opt, 30))).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[new_acc.strip()] = {
                            "roles": assigned_modules, 
                            "phone": new_phone.strip(), 
                            "expires_at": exp_date
                        }
                        save_licensed_accounts(st.session_state.licensed_accounts)
                        st.toast(f"✅ Đã lưu thông tin cho {new_acc}!")
                        st.rerun()
            
            search_cust = st.text_input("🔍 Tìm kiếm khách hàng:", placeholder="Nhập Email hoặc SĐT", key="search_cust_input")
            filtered_accs = list(st.session_state.licensed_accounts.items())
            if search_cust:
                filtered_accs = [(acc, info) for acc, info in filtered_accs if search_cust.lower() in acc.lower() or search_cust in str(info.get('phone', ''))]

            if filtered_accs:
                st.markdown(f"##### 📋 Danh sách Khách hàng ({len(filtered_accs)})")
                st.markdown("<div class='scrollable-sidebar-container'>", unsafe_allow_html=True)
                for acc, info in filtered_accs:
                    with st.container(border=True):
                        st.markdown(f"**👤 {acc}**")
                        phone_val = info.get('phone', '')
                        roles_val = info.get('roles', ALL_MODULES)
                        exp_val = info.get('expires_at', '2099-12-31')
                        st.caption(f"📞 SĐT: {phone_val or 'Chưa có'}<br>• Quyền: {', '.join(roles_val)}<br>• Hết hạn: {exp_val}", unsafe_allow_html=True)
                        
                        if phone_val:
                            clean_p = re.sub(r'\D', '', phone_val)
                            st.markdown(f"<a href='[https://zalo.me/](https://zalo.me/){clean_p}' target='_blank' style='background:#0068ff; color:white; padding:4px 10px; border-radius:4px; text-decoration:none; font-size:11px; font-weight:700; display:inline-block; margin-bottom:5px;'>💬 Nhắn Zalo</a>", unsafe_allow_html=True)
                        
                        if acc != ADMIN_EMAIL:
                            col_up, col_del = st.columns(2)
                            with col_up:
                                if st.button("✏️ Sửa", key=f"edit_acc_{acc}", use_container_width=True):
                                    st.session_state.editing_acc_email = acc
                            with col_del:
                                if st.button(f"🗑 Xóa", key=f"del_acc_{acc}", type="secondary", use_container_width=True):
                                    del st.session_state.licensed_accounts[acc]
                                    save_licensed_accounts(st.session_state.licensed_accounts)
                                    st.toast("✅ Đã xóa tài khoản!")
                                    st.rerun()
                        
                        if st.session_state.get("editing_acc_email") == acc:
                            with st.form(f"update_form_{acc}" ):
                                st.markdown(f"**Cập nhật cho: {acc}**")
                                upd_phone = st.text_input("SĐT mới:", value=phone_val, key=f"upd_p_{acc}")
                                upd_roles = st.multiselect("Phân quyền thể loại:", options=ALL_MODULES, default=roles_val, key=f"upd_r_{acc}")
                                upd_exp = st.text_input("Ngày hết hạn (YYYY-MM-DD):", value=exp_val, key=f"upd_e_{acc}")
                                if st.form_submit_button("💾 Lưu Cập Nhật"):
                                    with st.spinner("⏳ Đang lưu cập nhật..."):
                                        st.session_state.licensed_accounts[acc] = {
                                            "roles": upd_roles,
                                            "phone": upd_phone.strip(),
                                            "expires_at": upd_exp.strip()
                                        }
                                        save_licensed_accounts(st.session_state.licensed_accounts)
                                        st.session_state.editing_acc_email = None
                                        st.toast("✅ Đã cập nhật tài khoản thành công!")
                                        st.rerun()
                    st.markdown("---")
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div class="support-box">
            <b style="color: #166534; font-size: 0.95rem;">💬 Cần Hỗ Trợ / Mua Gói?</b><br>
            <p style="font-size: 0.85rem; color: #15803d; margin: 6px 0 8px 0;">Kết nối ngay với chúng tôi:</p>
            <div class="social-icons-container">
                <a href="[https://zalo.me/0968484369](https://zalo.me/0968484369)" target="_blank" class="btn-zalo">Zalo</a>
                <a href="[https://facebook.com/](https://facebook.com/)" target="_blank" class="btn-fb">f</a>
                <a href="[https://tiktok.com/](https://tiktok.com/)" target="_blank" class="btn-tt">♪</a>
            </div>
            <div style="font-weight: 700; color: #166534; font-size: 12px; margin-top: 8px;">📞 Hotline: 0968.484.369</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🔐 TÀI KHOẢN")
        st.success(f"Đang dùng: {st.session_state.current_email}")
        if st.button("🚪 Đăng Xuất"):
            st.session_state.is_logged_in = False
            st.toast("✅ Đăng xuất!")
            st.rerun()

if not st.session_state.is_logged_in:
    st.info("👈 Vui lòng đăng nhập ở thanh công cụ bên trái.")
    st.stop()

# ==============================================================================
# 5. KHÔNG GIAN SÁNG TẠO CHÍNH
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div></div>""", unsafe_allow_html=True)

current_acc_info = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
allowed_categories = [m for m in ALL_MODULES if m in current_acc_info.get("roles", ALL_MODULES)]
if not allowed_categories: allowed_categories = ALL_MODULES

if supabase:
    try: products_data = supabase.table("products").select("*").execute().data
    except: products_data = []
    
    if products_data:
        prod_names = [p["product_name"] for p in products_data]
        selected_name = st.selectbox("📌 Chọn sản phẩm từ Database:", options=prod_names, key=f"select_prod_main_{st.session_state.reset_key}")
        st.session_state.current_product_data = next(p for p in products_data if p["product_name"] == selected_name)
        prod = st.session_state.current_product_data
        
        with st.container(border=True):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**💰 Hoa hồng:** <span style='color:#15803d; font-weight:900;'>{prod.get('commission_percent', 0)}%</span>", unsafe_allow_html=True)
                st.markdown(f"**🎯 Tệp khách hàng:** {prod.get('target_audience', '')}")
            with col_b:
                st.markdown(f"**🧠 Insight:** {prod.get('product_insight', '')}")
                st.markdown(f"**💔 Nỗi đau:** {prod.get('pain_points', '')}")

st.markdown("---")
st.markdown("### ⚙️ Thiết Lập Đạo Diễn & Nguồn Ảnh")
col_m, col_s, col_r = st.columns(3)
with col_m: mode = st.selectbox("🎯 Thể loại (Đã được phân quyền):", allowed_categories, key=f"mode_sel_{st.session_state.reset_key}")
with col_s: style = st.selectbox("🎨 Phong cách hình ảnh:", ["Điện Ảnh Chân Thực", "Hoạt Hình 3D", "Hoạt Hình 2D / Anime", "Studio Tối Giản"], key=f"style_sel_{st.session_state.reset_key}")
with col_r: aspect = st.selectbox("Khung hình:", ["9:16 (Dọc TikTok/Reels)", "16:9 (Ngang YouTube)"], key=f"aspect_sel_{st.session_state.reset_key}")

narrator_mode = st.selectbox("🎙️ Thuyết minh & Nhân vật:", ["Nhân vật xuất hiện nói chuyện (On-camera, Lip-sync)", "🎙️ Lồng tiếng ngoài (Off-screen, Show sản phẩm)"], key=f"narrator_sel_{st.session_state.reset_key}")

col_p_img, col_c_img = st.columns([1, 1])
with col_p_img:
    up_files = st.file_uploader("📦 Ảnh SP/Bối cảnh (Sẽ được AI giữ nguyên gốc 100%):", type=["jpg", "png"], accept_multiple_files=True, key=f"up_main_files_{st.session_state.reset_key}")
with col_c_img:
    num_chars = st.number_input("👤 Số lượng Diễn viên (Tối đa 8):", min_value=0, max_value=8, step=1, key=f"num_chars_main_{st.session_state.reset_key}")

char_inputs = []
if num_chars > 0:
    for i in range(0, num_chars, 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < num_chars:
                idx = i + j
                with cols[j]:
                    c_role = st.text_input(f"Vai trò NV {idx+1}", key=f"role_{idx}_{st.session_state.reset_key}")
                    c_file = st.file_uploader(f"Ảnh NV {idx+1}", type=["jpg", "png"], key=f"file_{idx}_{st.session_state.reset_key}", label_visibility="collapsed")
                    if c_file and c_role: char_inputs.append({"id": idx+1, "role": c_role, "file": c_file})

custom_note = st.text_area("✍️ Ghi chú đặc biệt cho AI:", key=f"note_main_{st.session_state.reset_key}")

if st.button("🚀 PHÂN TÍCH DNA & SINH 5 KỊCH BẢN ĐA VŨ TRỤ", type="primary", use_container_width=True):
    with st.spinner("⏳ Đạo diễn AI đang phân tích dữ liệu sản phẩm, tâm lý khách hàng và sinh 5 kịch bản chuẩn chiến lược... Vui lòng đợi..."):
        try:
            st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
            char_rules = generate_char_rules_string(st.session_state.character_profiles)
            st.session_state.last_mode = mode
            st.session_state.last_style = style
            st.session_state.last_aspect = aspect
            st.session_state.last_narrator = narrator_mode
            st.session_state.current_input_context = custom_note
            st.session_state.current_product_data_saved = st.session_state.get("current_product_data")
            st.session_state.current_project_id = None
            
            time_ctx = get_dynamic_realtime_context()
            prod_ctx = f"SẢN PHẨM: {json.dumps(st.session_state.get('current_product_data'), ensure_ascii=False)}" if st.session_state.get("current_product_data") else ""
            prompt = f"""
            {time_ctx}
            {prod_ctx}
            GHI CHÚ DỰ ÁN: {custom_note}
            BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON CHUẨN GỒM CÁC KEY SAU:
            {{
                "content_analysis": {{
                    "primary_target_audience": "Nhận diện TỆP KHÁCH HÀNG",
                    "mechanical_and_accessories": "Kiểu dáng, chất liệu",
                    "customer_pain_points": "Nỗi đau khách hàng",
                    "core_desires": "Mong muốn cốt lõi",
                    "emotional_or_usp_hook": "USP độc quyền",
                    "visual_physics_rules": "Quy chuẩn vật lý",
                    "prompt_dna_lock": "Khóa thị giác"
                }},
                "script_outlines": [ 
                    {{
                        "id": 1, 
                        "title": "Tên kịch bản", 
                        "setting_style": "Bối cảnh thực tế", 
                        "target_hook": "Viết 2-3 câu tóm tắt chi tiết diễn biến kịch bản và câu thoại Hook mở đầu an toàn"
                    }} 
                ]
            }}
            YÊU CẦU: Tạo chính xác 5 kịch bản khác nhau phù hợp với thời điểm hiện tại, cấm báo giá.
            LƯU Ý CỰC KỲ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG DÙNG DẤU NGOẶC KÉP CHƯA ESCAPE BÊN TRONG CÁC GIÁ TRỊ STRING JSON.
            """
            
            payload = []
            if up_files:
                payload.append("ẢNH SẢN PHẨM / VẬT THỂ THAM CHIẾU:")
                for f in up_files: payload.append(types.Part.from_bytes(data=f.getvalue(), mime_type=f.type if f.type else "image/jpeg"))
            if char_inputs:
                for c in char_inputs:
                    payload.append(f"ẢNH NHÂN VẬT THAM CHIẾU {c['id']} - VAI TRÒ: {c['role']}:")
                    payload.append(types.Part.from_bytes(data=c['file'].getvalue(), mime_type=c['file'].type if c['file'].type else "image/jpeg"))
            payload.append(prompt)
            
            res = call_gemini(payload, get_system_instructions_for_details(mode, style, aspect, narrator_mode, char_rules))
            
            if not res or "script_outlines" not in res:
                st.error("❌ AI không trả về đúng định dạng JSON. Vui lòng thử lại!")
            else:
                st.session_state.content_analysis = res.get("content_analysis")
                st.session_state.all_scripts = res.get("script_outlines", [])
                st.session_state.cloned_scripts = []
                st.session_state.expanded_scripts = []
                st.session_state.generated_details = {}
                st.session_state.active_script_id = None
                st.session_state.scroll_to_top = True
                st.toast("✅ Đã sinh xong 5 kịch bản và phân tích DNA!")
                time.sleep(0.5)
                st.rerun()
        except Exception as e:
            st.error(f"❌ Lỗi xử lý AI: {str(e)}")

# ==================== HIỂN THỊ PHÂN TÍCH DNA ====================
if st.session_state.content_analysis and isinstance(st.session_state.content_analysis, dict):
    st.divider()
    st.markdown(f"### 🔍 **Phân Tích DNA Chi Tiết Đa Tầng**")
    ca = st.session_state.content_analysis
    with st.container(border=True):
        st.markdown("##### 🎯 **1. Chân dung Khách hàng & Nỗi đau:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Tệp khách hàng mục tiêu:</b> {format_analysis_field(ca.get('primary_target_audience', 'N/A'))}<br>{format_analysis_field(ca.get('customer_pain_points', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 🏭 **2. Thông số Cốt lõi & Vật lý:**")
        st.markdown(f"<div style='line-height: 1.8;'>{format_analysis_field(ca.get('mechanical_and_accessories', 'N/A'))}<br>• <b>Vật lý:</b> {format_analysis_field(ca.get('visual_physics_rules', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 💡 **3. Mong muốn cốt lõi & USP:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Mong muốn:</b> {format_analysis_field(ca.get('core_desires', 'N/A'))}<br>• <b>USP:</b> {format_analysis_field(ca.get('emotional_or_usp_hook', 'N/A'))}</div>", unsafe_allow_html=True)
    st.markdown("##### 📌 **Chuỗi khóa thị giác (Visual DNA Lock):**")
    st.code(str(ca.get('prompt_dna_lock', 'N/A')), language="text")

# ==============================================================================
# 6. DANH SÁCH KỊCH BẢN & XEM CHI TIẾT
# ==============================================================================
all_combined_scripts_list = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts

if all_combined_scripts_list:
    st.divider()
    
    completed_scripts = [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) in st.session_state.generated_details]
    pending_scripts = [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) not in st.session_state.generated_details]

    if st.session_state.active_script_id is not None:
        if st.button("⬅ Thu gọn và Quay lại danh sách tổng"):
            st.session_state.active_script_id = None
            st.session_state.scroll_to_top = True
            st.rerun()
        
        active_sc = st.session_state.generated_details[st.session_state.active_script_id]
        if isinstance(active_sc, list): active_sc = active_sc[0] if active_sc else {}
        vp = active_sc.get("voice_profile", {})
        if isinstance(vp, str): vp = {"gender": "Nữ", "tone": vp}
        
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(active_sc.get('title', 'KỊCH BẢN')).upper()}**")
        st.markdown(f"""
        <div class='detail-header-box'>
            ⏱️ Thời lượng: <b>{active_sc.get('total_estimated_duration', '24s (0.4 phút)')}</b> | 
            🎙️ Giọng: <b>{vp.get('gender', 'Nữ')} ({vp.get('tone', 'nhịp độ nhanh, dồn dập')})</b> | 
            👔 Trang phục toàn diện: <b>{active_sc.get('script_outfit_setup', 'Mặc định theo kịch bản')}</b> | 
            📐 Khung hình: <b>{st.session_state.get('last_aspect', '9:16 (Dọc TikTok/Reels)')}</b>
        </div>
        """, unsafe_allow_html=True)
        
        scenes = active_sc.get("scenes", [])
        if isinstance(scenes, dict): scenes = [scenes]
        for idx, scene in enumerate(scenes, 1):
            trans_type = scene.get('transition_type', 'Chuyển cảnh mới (Tạo ảnh mới)')
            st.markdown(f"#### 📍 Phân cảnh {idx} ({scene.get('duration', '8s')}) — [ {trans_type} ]")
            st.markdown(f"🏛️ **Bối cảnh & Miêu tả:** *{scene.get('scene_setting', '')}*")
            st.markdown(f"**🎙️ Đạo diễn ngữ điệu & SFX:** *{scene.get('voice_director_vn', '')}*")
            st.markdown(f"**💬 Thoại & Âm thanh (Chuẩn chính tả):** <span class='voiceover-text'>{scene.get('voiceover_vi', '')}</span>", unsafe_allow_html=True)
            
            img_p = scene.get('image_prompt', '')
            is_linked_scene = "nối tiếp" in trans_type.lower() or "dùng lại ảnh cuối" in img_p.lower() or "tham chiếu" in img_p.lower()
            
            if is_linked_scene:
                st.info("🔗 **Cảnh nối tiếp:** Không cần tạo ảnh mới. Hãy sử dụng khung hình cuối của Cảnh trước làm ảnh tham chiếu (Image-to-Video) cho cảnh này.")
            else:
                if img_p: 
                    st.markdown(f"**🖼️ Prompt Ảnh (Imagen 3):**")
                    st.code(img_p, language="text")
                    safe_copy_button(img_p, f"📋 Sao Chép Prompt Ảnh Cảnh {idx}")
            
            vid_p = scene.get('video_prompt', '')
            if vid_p: 
                st.markdown(f"**🎥 Prompt Video (Veo 3):**")
                st.code(vid_p, language="text")
                safe_copy_button(vid_p, f"📋 Sao Chép Prompt Video Cảnh {idx}")
            st.markdown("---")

    st.markdown("### 🎬 **1. Kịch Bản Đã Hoàn Thiện Chi Tiết (Sẵn Sàng Sản Xuất & Nhân Bản)**")
    if not completed_scripts:
        st.info("💡 Chưa có kịch bản nào được tạo chi tiết.")
    else:
        for outline in completed_scripts:
            sc_id = int(outline.get("id", 0))
            is_current = (sc_id == st.session_state.active_script_id)
            with st.container(border=True):
                col_i1, col_btn1, col_btn2 = st.columns([2.5, 1, 1])
                with col_i1:
                    badge = " <span class='badge-ready'>ĐANG XEM</span>" if is_current else ""
                    st.markdown(f"**#{sc_id}. {outline.get('title')}**{badge}", unsafe_allow_html=True)
                    hook_val = outline.get('target_hook', '')
                    if not hook_val or str(hook_val).strip().lower() in ['none', 'null', '']: hook_val = "Kịch bản tập trung làm nổi bật USP sản phẩm."
                    st.caption(f"⚡ **Tóm tắt & Hook:** *{hook_val}*")
                with col_btn1:
                    if not is_current:
                        if st.button("👁️ Xem lại", key=f"btn_rev_{sc_id}", use_container_width=True):
                            st.session_state.active_script_id = sc_id
                            st.session_state.scroll_to_top = True
                            st.rerun()
                with col_btn2:
                    if st.button("🚀 Nhân bản (Clone)", key=f"btn_clone_{sc_id}", type="primary", use_container_width=True):
                        st.session_state.action_trigger = "clone_script"
                        st.session_state.action_param = sc_id
                        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ⏳ **2. Kịch Bản Đang Chờ Tạo Chi Tiết**")
    if not pending_scripts:
        st.success("🎉 Tất cả các kịch bản trong danh sách đã được tạo chi tiết thành công.")
    else:
        for outline in pending_scripts:
            sc_id = int(outline.get("id", 0))
            with st.container(border=True):
                col_i2, col_a2 = st.columns([3, 1.2])
                with col_i2:
                    st.markdown(f"**#{sc_id}. {outline.get('title')}** — <span class='badge-pending'>ĐANG CHỜ</span>", unsafe_allow_html=True)
                    hook_val = outline.get('target_hook', '')
                    if not hook_val or str(hook_val).strip().lower() in ['none', 'null', '']: hook_val = "Kịch bản tập trung làm nổi bật USP sản phẩm."
                    st.caption(f"⚡ **Tóm tắt & Hook:** *{hook_val}*")
                with col_a2:
                    if st.button("✨ Tạo chi tiết ngay", key=f"btn_cre_{sc_id}", type="secondary", use_container_width=True):
                        st.session_state.action_trigger = "create_detail"
                        st.session_state.action_param = sc_id
                        st.rerun()

    st.markdown("---")
    with st.container(border=True):
        st.markdown("##### ➕ **Tùy Chỉnh & Gọi Thêm Kịch Bản Mới**")
        col_g1, col_g2 = st.columns([2, 1])
        with col_g1:
            st.session_state.extra_angle_type = st.selectbox("Định hướng chiến lược:", ["⚡ Flash Sale & Deal hời (Tập trung chốt đơn)", "🎭 Tình huống đời sống / Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Mẹo vặt / Chia sẻ", "😂 Tình huống hài hước"], key=f"extra_angle_selectbox_main_{st.session_state.reset_key}")
        with col_g2:
            st.session_state.extra_num_chars = st.number_input("Số diễn viên:", min_value=1, max_value=8, value=1, step=1, key=f"extra_num_chars_main_{st.session_state.reset_key}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        # Căn chỉnh nút bấm ra chính giữa màn hình
        c_l, c_btn, c_r = st.columns([1, 2, 1])
        with c_btn:
            if st.button("🚀 Gọi Thêm 5 Kịch Bản Mới", key="btn_add_main", type="primary", use_container_width=True):
                st.session_state.action_trigger = "generate_more"
                st.rerun()
