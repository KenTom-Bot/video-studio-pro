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
    div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important; color: white !important; border-radius: 8px !important; font-weight: bold; }
    div[data-testid="stButton"] > button[kind="secondary"] { background: linear-gradient(135deg, #ff4b4b 0%, #ff7300 100%) !important; color: #ffffff !important; box-shadow: 0 3px 8px rgba(255, 75, 75, 0.35) !important; padding: 0.55rem 1rem !important; font-weight: bold !important; border: none !important; }
    div[data-testid="stButton"] > button[kind="secondary"]:hover { transform: translateY(-1px) !important; box-shadow: 0 5px 14px rgba(255, 75, 75, 0.5) !important; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .custom-card { background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
    .support-box { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1.5px solid #86efac; border-radius: 12px; padding: 12px; text-align: center; margin-top: 15px; }
    .btn-zalo { background: #0068FF; color: white !important; font-weight: 900; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 15px; border: 1px solid #0056d6; }
    .btn-fb { background: #1877F2; color: white !important; font-weight: 900; padding: 8px 24px; border-radius: 8px; text-decoration: none; font-size: 16px; border: 1px solid #166fe5; font-family: serif; }
    .btn-tt { background: #000000; color: white !important; font-weight: 900; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 15px; border: 1px solid #333; }
    .social-icons-container { display: flex; gap: 12px; justify-content: center; margin-top: 10px; margin-bottom: 10px; }
    .hotline-text { text-align: center; font-weight: 800; color: #d90429; font-size: 1.2rem; margin-bottom: 5px; }
    @keyframes pulse { 0% { transform: scale(0.98); opacity: 0.8; } 50% { transform: scale(1.01); opacity: 1; } 100% { transform: scale(0.98); opacity: 0.8; } }
    .loading-pulse { animation: pulse 1.5s infinite ease-in-out; color: #d90429; font-weight: 800; text-align: center; padding: 25px; background: #fef2f2; border: 2px dashed #fca5a5; border-radius: 12px; margin: 20px 0; }
    .detail-header-box { background: #eff6ff; border: 1.5px solid #bfdbfe; border-radius: 10px; padding: 15px; margin-bottom: 20px; color: #1e3a8a; }
    .voiceover-text { color: #15803d; background: #f0fdf4; padding: 4px 8px; border-radius: 6px; font-family: monospace; font-size: 15px; border: 1px solid #bbf7d0; }
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
    return {ADMIN_EMAIL: {"roles": ALL_MODULES, "expires_at": "2099-12-31"}}

def save_licensed_accounts(acc_dict):
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(acc_dict, f, ensure_ascii=False, indent=2)
    except: pass

# Hàm tạo nút Copy Prompt mạnh mẽ (Không bị lỗi trình duyệt)
def safe_copy_button(text_to_copy: str, button_label: str = "📋 Sao Chép Prompt"):
    b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    html_code = f"""
    <button id="copy-btn" style="background:#16a34a; color:white; border:none; padding:8px 16px; font-size:13px; font-weight:700; border-radius:6px; cursor:pointer; width:100%;">{button_label}</button>
    <script>
    document.getElementById("copy-btn").addEventListener("click", function() {{
        const text = decodeURIComponent(escape(atob("{b64}")));
        navigator.clipboard.writeText(text).then(function() {{
            document.getElementById("copy-btn").innerText = "✅ Đã sao chép!";
            document.getElementById("copy-btn").style.background = "#15803d";
            setTimeout(function() {{
                document.getElementById("copy-btn").innerText = "{button_label}";
                document.getElementById("copy-btn").style.background = "#16a34a";
            }}, 2000);
        }}).catch(function(err) {{
            const textArea = document.createElement("textarea");
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {{ document.execCommand('copy'); document.getElementById("copy-btn").innerText = "✅ Đã sao chép!"; }} catch (e) {{}}
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
    ("current_product_data", None), ("current_input_context", ""),
    ("action_trigger", None), ("action_param", None), ("reset_key", 0),
    ("scroll_to_top", False),
    ("extra_angle_type", "⚡ Dạng Flash Sale & Deal hời (Tập trung chốt đơn)"),
    ("extra_num_chars", 1), ("extra_duration_mins", 1.0),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}")
]:
    if key not in st.session_state: st.session_state[key] = default_val

if st.session_state.scroll_to_top:
    components.html("<script>window.parent.scrollTo({top: 0, behavior: 'smooth'});</script>", height=0)
    st.session_state.scroll_to_top = False

# ==============================================================================
# 2. HÀM AI LÕI & CHÍNH SÁCH
# ==============================================================================
def clean_json(text):
    cleaned = re.sub(r'```(?:json)?', '', text).strip()
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    try: return json.loads(match.group(0) if match else cleaned)[0] if isinstance(json.loads(match.group(0) if match else cleaned), list) else json.loads(match.group(0) if match else cleaned)
    except: return {}

def call_gemini(contents, sys_inst="Bạn là AI hỗ trợ JSON."):
    res = client.models.generate_content(
        model="gemini-3.6-flash", contents=contents,
        config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.7)
    )
    return clean_json(res.text)

def generate_char_rules_string(profiles):
    if not profiles: return "🔹 NHÂN VẬT: Linh hoạt theo kịch bản."
    rules = "🔹 KHÓA KHUÔN MẶT KOC:\n"
    for p in profiles: rules += f"   + Nhân vật {p['id']} ({p['role']}): Dùng lệnh 'Character {p['id']} featuring exact identity of reference image {p['id']}'.\n"
    return rules

def get_system_instructions_for_details(mode, style, aspect, narrator_mode, char_rules):
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL CHO VEO 3 VÀ IMAGEN 3. THỂ LOẠI: {mode} | PHONG CÁCH: {style} | ĐỊNH DẠNG: {aspect}
    🛑 QUY TẮC BẮT BUỘC KHÔNG ĐƯỢC VI PHẠM:
    1. TỰ ĐỘNG CÂN ĐỐI THỜI LƯỢNG & SỐ CẢNH: Tự động phân bổ kịch bản thành ĐÚNG 3 HOẶC 4 PHÂN CẢNH.
    2. CHỈ DÙNG MỐC THỜI GIAN CHUẨN: Mỗi phân cảnh BẮT BUỘC CHỈ ĐƯỢC PHÉP dài 4s, 6s, hoặc 8s (TUYỆT ĐỐI KHÔNG DÙNG 10s hoặc số lẻ).
    3. CẤM BÁO GIÁ: Tuyệt đối KHÔNG đưa giá tiền cụ thể bằng con số vào kịch bản.
    4. NỐI LỀN MẠCH (MATCH CUT): Nếu cảnh là nối tiếp cảnh trước (Match Cut), phần 'image_prompt' BẮT BUỘC phải ghi: "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video".
    5. VẬT LÝ & SẢN PHẨM: Giữ nguyên 100% hình dáng sản phẩm gốc. Miêu tả rõ ràng các định luật vật lý (gió, nước, bóng đổ) vào Video prompt.
    6. GIỌNG NÓI ({narrator_mode}): Lời thoại phải đúng chính tả, dễ đọc, ngắt nghỉ rõ ràng. {char_rules}
    """

def create_scene_details(target_id, mode, style, aspect, narrator_mode, char_rules):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if sc["id"] == target_id), None)
    if not outline: return
    
    prompt = f"""
    Viết chi tiết kịch bản ID {target_id}: '{outline.get('title')}'. Hook: {outline.get('target_hook')}. Bối cảnh: {outline.get('setting_style')}.
    
    TRẢ VỀ ĐÚNG 1 DICT JSON GỒM CÁC KEY SAU:
    {{
        "title": "{outline.get('title')}",
        "total_estimated_duration": "24s (0.4 phút)",
        "script_outfit_setup": "Nữ diễn viên mặc đồ lụa màu kem, đi dép trắng...",
        "voice_profile": {{"gender": "Nữ", "tone": "nhịp độ nhanh, dồn dập, nhiệt huyết"}},
        "scenes": [
            {{
                "scene_number": 1,
                "duration": "8s",
                "transition_type": "Mở đầu (Master Anchor Shot)",
                "scene_setting": "Góc toàn cảnh (Wide Anchor Shot)...",
                "voice_director_vn": "Giọng Nữ Miền Bắc chuẩn (Hà Nội)...",
                "voiceover_vi": "Trằn trọc cả đêm... vì chăn ga cũ vừa hầm nóng vừa rít da?",
                "image_prompt": "Cinematic vertical 9:16 photo of...",
                "video_prompt": "Vertical 9:16 video, slow camera zoom in..."
            }},
            {{
                "scene_number": 2,
                "duration": "6s",
                "transition_type": "Nối liền mạch (Match Cut)",
                "scene_setting": "Góc quay cận cảnh...",
                "voice_director_vn": "Nhấn giọng hào hứng...",
                "voiceover_vi": "Thời tiết sang thu rồi..., đổi ngay bộ chăn ga lụa Thái này thôi!",
                "image_prompt": "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video",
                "video_prompt": "Extreme close-up shot..."
            }}
        ]
    }}
    Lưu ý: "scenes" chỉ được có 3 hoặc 4 phần tử. Các "duration" chỉ được phép là "4s", "6s", hoặc "8s".
    """
    res = call_gemini([prompt], get_system_instructions_for_details(mode, style, aspect, narrator_mode, char_rules))
    st.session_state.generated_details[target_id] = res

def clone_script(script_id):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if sc["id"] == script_id), None)
    cur_len = len(all_combined)
    prompt = f"Nhân bản kịch bản gốc: {json.dumps(target, ensure_ascii=False)}. Tạo 5 biến thể mới. Format JSON key 'script_outlines' (id từ {cur_len+1})."
    res = call_gemini([prompt], "Bạn là Đạo diễn Content TikTok.")
    clones = res.get("script_outlines", [])
    for idx, cl in enumerate(clones): cl["id"] = cur_len + idx + 1
    return clones

def generate_more_scripts(angle, num_chars, duration_mins):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    cur_len = len(all_combined)
    prod_ctx = f"SẢN PHẨM: {json.dumps(st.session_state.current_product_data, ensure_ascii=False)}" if st.session_state.current_product_data else ""
    prompt = f"{prod_ctx}\nYÊU CẦU MỚI: Thể loại '{angle}', {num_chars} nhân vật, thời lượng {duration_mins} phút.\nTạo thêm 5 kịch bản MỚI. Format JSON key 'script_outlines' (id từ {cur_len+1})."
    res = call_gemini([prompt], "Bạn là Đạo diễn Content TikTok.")
    more_scripts = res.get("script_outlines", [])
    for idx, sc in enumerate(more_scripts): sc["id"] = cur_len + idx + 1
    return more_scripts

def save_project_to_db(email, title, content_list):
    if not supabase: return "Chưa kết nối Database Supabase."
    try:
        clean_content = json.loads(json.dumps(content_list, default=str)) 
        data = {"user_email": email, "project_title": title, "script_content": clean_content}
        supabase.table("saved_projects").insert(data).execute()
        return True
    except Exception as e:
        return str(e)

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
    div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important; color: white !important; border-radius: 8px !important; font-weight: bold; }
    div[data-testid="stButton"] > button[kind="secondary"] { background: linear-gradient(135deg, #ff4b4b 0%, #ff7300 100%) !important; color: #ffffff !important; box-shadow: 0 3px 8px rgba(255, 75, 75, 0.35) !important; padding: 0.55rem 1rem !important; font-weight: bold !important; border: none !important; }
    div[data-testid="stButton"] > button[kind="secondary"]:hover { transform: translateY(-1px) !important; box-shadow: 0 5px 14px rgba(255, 75, 75, 0.5) !important; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .custom-card { background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
    .support-box { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1.5px solid #86efac; border-radius: 12px; padding: 12px; text-align: center; margin-top: 15px; }
    .btn-zalo { background: #0068FF; color: white !important; font-weight: 900; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 15px; border: 1px solid #0056d6; }
    .btn-fb { background: #1877F2; color: white !important; font-weight: 900; padding: 8px 24px; border-radius: 8px; text-decoration: none; font-size: 16px; border: 1px solid #166fe5; font-family: serif; }
    .btn-tt { background: #000000; color: white !important; font-weight: 900; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 15px; border: 1px solid #333; }
    .social-icons-container { display: flex; gap: 12px; justify-content: center; margin-top: 10px; margin-bottom: 10px; }
    .hotline-text { text-align: center; font-weight: 800; color: #d90429; font-size: 1.2rem; margin-bottom: 5px; }
    @keyframes pulse { 0% { transform: scale(0.98); opacity: 0.8; } 50% { transform: scale(1.01); opacity: 1; } 100% { transform: scale(0.98); opacity: 0.8; } }
    .loading-pulse { animation: pulse 1.5s infinite ease-in-out; color: #d90429; font-weight: 800; text-align: center; padding: 25px; background: #fef2f2; border: 2px dashed #fca5a5; border-radius: 12px; margin: 20px 0; }
    .detail-header-box { background: #eff6ff; border: 1.5px solid #bfdbfe; border-radius: 10px; padding: 15px; margin-bottom: 20px; color: #1e3a8a; }
    .voiceover-text { color: #15803d; background: #f0fdf4; padding: 4px 8px; border-radius: 6px; font-family: monospace; font-size: 15px; border: 1px solid #bbf7d0; }
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
    return {ADMIN_EMAIL: {"roles": ALL_MODULES, "expires_at": "2099-12-31"}}

def save_licensed_accounts(acc_dict):
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(acc_dict, f, ensure_ascii=False, indent=2)
    except: pass

# Hàm tạo nút Copy Prompt mạnh mẽ (Không bị lỗi trình duyệt)
def safe_copy_button(text_to_copy: str, button_label: str = "📋 Sao Chép Prompt"):
    b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    html_code = f"""
    <button id="copy-btn" style="background:#16a34a; color:white; border:none; padding:8px 16px; font-size:13px; font-weight:700; border-radius:6px; cursor:pointer; width:100%;">{button_label}</button>
    <script>
    document.getElementById("copy-btn").addEventListener("click", function() {{
        const text = decodeURIComponent(escape(atob("{b64}")));
        navigator.clipboard.writeText(text).then(function() {{
            document.getElementById("copy-btn").innerText = "✅ Đã sao chép!";
            document.getElementById("copy-btn").style.background = "#15803d";
            setTimeout(function() {{
                document.getElementById("copy-btn").innerText = "{button_label}";
                document.getElementById("copy-btn").style.background = "#16a34a";
            }}, 2000);
        }}).catch(function(err) {{
            const textArea = document.createElement("textarea");
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {{ document.execCommand('copy'); document.getElementById("copy-btn").innerText = "✅ Đã sao chép!"; }} catch (e) {{}}
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
    ("current_product_data", None), ("current_input_context", ""),
    ("action_trigger", None), ("action_param", None), ("reset_key", 0),
    ("scroll_to_top", False),
    ("extra_angle_type", "⚡ Dạng Flash Sale & Deal hời (Tập trung chốt đơn)"),
    ("extra_num_chars", 1), ("extra_duration_mins", 1.0),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}")
]:
    if key not in st.session_state: st.session_state[key] = default_val

if st.session_state.scroll_to_top:
    components.html("<script>window.parent.scrollTo({top: 0, behavior: 'smooth'});</script>", height=0)
    st.session_state.scroll_to_top = False

# ==============================================================================
# 2. HÀM AI LÕI & CHÍNH SÁCH
# ==============================================================================
def clean_json(text):
    cleaned = re.sub(r'```(?:json)?', '', text).strip()
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    try: return json.loads(match.group(0) if match else cleaned)[0] if isinstance(json.loads(match.group(0) if match else cleaned), list) else json.loads(match.group(0) if match else cleaned)
    except: return {}

def call_gemini(contents, sys_inst="Bạn là AI hỗ trợ JSON."):
    res = client.models.generate_content(
        model="gemini-3.6-flash", contents=contents,
        config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.7)
    )
    return clean_json(res.text)

def generate_char_rules_string(profiles):
    if not profiles: return "🔹 NHÂN VẬT: Linh hoạt theo kịch bản."
    rules = "🔹 KHÓA KHUÔN MẶT KOC:\n"
    for p in profiles: rules += f"   + Nhân vật {p['id']} ({p['role']}): Dùng lệnh 'Character {p['id']} featuring exact identity of reference image {p['id']}'.\n"
    return rules

def get_system_instructions_for_details(mode, style, aspect, narrator_mode, char_rules):
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL CHO VEO 3 VÀ IMAGEN 3. THỂ LOẠI: {mode} | PHONG CÁCH: {style} | ĐỊNH DẠNG: {aspect}
    🛑 QUY TẮC BẮT BUỘC KHÔNG ĐƯỢC VI PHẠM:
    1. TỰ ĐỘNG CÂN ĐỐI THỜI LƯỢNG & SỐ CẢNH: Tự động phân bổ kịch bản thành ĐÚNG 3 HOẶC 4 PHÂN CẢNH.
    2. CHỈ DÙNG MỐC THỜI GIAN CHUẨN: Mỗi phân cảnh BẮT BUỘC CHỈ ĐƯỢC PHÉP dài 4s, 6s, hoặc 8s (TUYỆT ĐỐI KHÔNG DÙNG 10s hoặc số lẻ).
    3. CẤM BÁO GIÁ: Tuyệt đối KHÔNG đưa giá tiền cụ thể bằng con số vào kịch bản.
    4. NỐI LỀN MẠCH (MATCH CUT): Nếu cảnh là nối tiếp cảnh trước (Match Cut), phần 'image_prompt' BẮT BUỘC phải ghi: "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video".
    5. VẬT LÝ & SẢN PHẨM: Giữ nguyên 100% hình dáng sản phẩm gốc. Miêu tả rõ ràng các định luật vật lý (gió, nước, bóng đổ) vào Video prompt.
    6. GIỌNG NÓI ({narrator_mode}): Lời thoại phải đúng chính tả, dễ đọc, ngắt nghỉ rõ ràng. {char_rules}
    """

def create_scene_details(target_id, mode, style, aspect, narrator_mode, char_rules):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if sc["id"] == target_id), None)
    if not outline: return
    
    prompt = f"""
    Viết chi tiết kịch bản ID {target_id}: '{outline.get('title')}'. Hook: {outline.get('target_hook')}. Bối cảnh: {outline.get('setting_style')}.
    
    TRẢ VỀ ĐÚNG 1 DICT JSON GỒM CÁC KEY SAU:
    {{
        "title": "{outline.get('title')}",
        "total_estimated_duration": "24s (0.4 phút)",
        "script_outfit_setup": "Nữ diễn viên mặc đồ lụa màu kem, đi dép trắng...",
        "voice_profile": {{"gender": "Nữ", "tone": "nhịp độ nhanh, dồn dập, nhiệt huyết"}},
        "scenes": [
            {{
                "scene_number": 1,
                "duration": "8s",
                "transition_type": "Mở đầu (Master Anchor Shot)",
                "scene_setting": "Góc toàn cảnh (Wide Anchor Shot)...",
                "voice_director_vn": "Giọng Nữ Miền Bắc chuẩn (Hà Nội)...",
                "voiceover_vi": "Trằn trọc cả đêm... vì chăn ga cũ vừa hầm nóng vừa rít da?",
                "image_prompt": "Cinematic vertical 9:16 photo of...",
                "video_prompt": "Vertical 9:16 video, slow camera zoom in..."
            }},
            {{
                "scene_number": 2,
                "duration": "6s",
                "transition_type": "Nối liền mạch (Match Cut)",
                "scene_setting": "Góc quay cận cảnh...",
                "voice_director_vn": "Nhấn giọng hào hứng...",
                "voiceover_vi": "Thời tiết sang thu rồi..., đổi ngay bộ chăn ga lụa Thái này thôi!",
                "image_prompt": "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video",
                "video_prompt": "Extreme close-up shot..."
            }}
        ]
    }}
    Lưu ý: "scenes" chỉ được có 3 hoặc 4 phần tử. Các "duration" chỉ được phép là "4s", "6s", hoặc "8s".
    """
    res = call_gemini([prompt], get_system_instructions_for_details(mode, style, aspect, narrator_mode, char_rules))
    st.session_state.generated_details[target_id] = res

def clone_script(script_id):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if sc["id"] == script_id), None)
    cur_len = len(all_combined)
    prompt = f"Nhân bản kịch bản gốc: {json.dumps(target, ensure_ascii=False)}. Tạo 5 biến thể mới. Format JSON key 'script_outlines' (id từ {cur_len+1})."
    res = call_gemini([prompt], "Bạn là Đạo diễn Content TikTok.")
    clones = res.get("script_outlines", [])
    for idx, cl in enumerate(clones): cl["id"] = cur_len + idx + 1
    return clones

def generate_more_scripts(angle, num_chars, duration_mins):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    cur_len = len(all_combined)
    prod_ctx = f"SẢN PHẨM: {json.dumps(st.session_state.current_product_data, ensure_ascii=False)}" if st.session_state.current_product_data else ""
    prompt = f"{prod_ctx}\nYÊU CẦU MỚI: Thể loại '{angle}', {num_chars} nhân vật, thời lượng {duration_mins} phút.\nTạo thêm 5 kịch bản MỚI. Format JSON key 'script_outlines' (id từ {cur_len+1})."
    res = call_gemini([prompt], "Bạn là Đạo diễn Content TikTok.")
    more_scripts = res.get("script_outlines", [])
    for idx, sc in enumerate(more_scripts): sc["id"] = cur_len + idx + 1
    return more_scripts

def save_project_to_db(email, title, content_list):
    if not supabase: return "Chưa kết nối Database Supabase."
    try:
        clean_content = json.loads(json.dumps(content_list, default=str)) 
        data = {"user_email": email, "project_title": title, "script_content": clean_content}
        supabase.table("saved_projects").insert(data).execute()
        return True
    except Exception as e:
        return str(e)

# ==============================================================================
# 3. THANH BÊN (SIDEBAR)
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        st.markdown("### 🔐 ĐĂNG NHẬP")
        email_input = st.text_input("Nhập Email:", key="login_email_input")
        if st.button("🔑 Đăng Nhập", type="primary"):
            email_check = email_input.strip()
            if email_check in st.session_state.licensed_accounts:
                acc_info = st.session_state.licensed_accounts[email_check]
                exp_date_str = acc_info.get("expires_at", "2099-12-31")
                try:
                    if datetime.now() > datetime.strptime(exp_date_str, "%Y-%m-%d"):
                        st.error(f"❌ Tài khoản hết hạn: {exp_date_str}!")
                        st.stop()
                except: pass
                st.session_state.is_logged_in = True
                st.session_state.current_email = email_check
                st.toast("✅ Đăng nhập thành công!")
                st.rerun()
            else: 
                st.error("Tài khoản chưa được cấp quyền!")
    else:
        st.markdown("### 🗂 LÀM VIỆC")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True):
            st.session_state.all_scripts, st.session_state.cloned_scripts, st.session_state.expanded_scripts = [], [], []
            st.session_state.generated_details, st.session_state.content_analysis = {}, None
            st.session_state.active_script_id = None
            st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
            st.session_state.reset_key += 1 
            st.toast("✅ Đã dọn dẹp và mở dự án mới sạch sẽ!")
            st.rerun()
            
        st.session_state.active_project_title = st.text_input("Tên dự án hiện tại:", st.session_state.active_project_title)
        if st.button("💾 Lưu Dự Án Này", use_container_width=True):
            all_com = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
            if not all_com: 
                st.warning("⚠️ Chưa có kịch bản nào để lưu!")
            else:
                save_result = save_project_to_db(st.session_state.current_email, st.session_state.active_project_title, all_com)
                if save_result is True:
                    st.toast("✅ Đã lưu dự án vào Database thành công!")
                else:
                    st.error(f"❌ Lỗi Database: {save_result}")
        
        st.markdown("---")
        
        st.markdown("### 📂 KHO LƯU TRỮ")
        if not supabase: st.error("Chưa kết nối Database.")
        else:
            try:
                if st.session_state.current_email == ADMIN_EMAIL: res = supabase.table("saved_projects").select("*").order("created_at", desc=True).execute()
                else: res = supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
                projects = res.data
            except: projects = []

            if not projects: st.info("Chưa có dự án nào.")
            else:
                for p in projects:
                    with st.expander(f"🎬 {p['project_title']}"):
                        st.caption(f"{p['created_at'][:10]}")
                        if st.session_state.current_email == ADMIN_EMAIL: st.caption(f"Tạo bởi: {p['user_email']}")
                        for i, sc in enumerate(p.get("script_content", [])): st.write(f"- {sc.get('title', 'Idea')}")
                        if st.button("🗑️ Xóa", key=f"del_{p['id']}", use_container_width=True):
                            supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                            st.toast("✅ Đã xóa dự án!")
                            st.rerun()

        if st.session_state.current_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙️ QUẢN TRỊ ADMIN")
            with st.form("add_license"):
                new_acc = st.text_input("Email cấp quyền:")
                assigned_modules = st.multiselect("Phân quyền thể loại:", options=ALL_MODULES, default=ALL_MODULES)
                duration_opt = st.selectbox("Thời hạn:", ["Dùng thử 3 ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "3 Năm", "5 Năm", "10 Năm", "Vĩnh viễn (Trọn đời)"])
                if st.form_submit_button("💾 Cấp Quyền"):
                    exp_date = "2099-12-31" if "Vĩnh viễn" in duration_opt else (datetime.now() + timedelta(days=3 if "Dùng thử" in duration_opt else {"1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730, "3 Năm": 1095, "5 Năm": 1825, "10 Năm": 3650}.get(duration_opt, 30))).strftime("%Y-%m-%d")
                    st.session_state.licensed_accounts[new_acc.strip()] = {"roles": assigned_modules, "expires_at": exp_date}
                    save_licensed_accounts(st.session_state.licensed_accounts)
                    st.toast(f"✅ Đã cấp quyền cho {new_acc}!")
            
            if st.session_state.licensed_accounts:
                with st.expander(f"📋 Danh sách tài khoản ({len(st.session_state.licensed_accounts)})"):
                    for acc, info in list(st.session_state.licensed_accounts.items()):
                        st.markdown(f"**👤 {acc}**")
                        st.caption(f"Quyền: {', '.join(info.get('roles', ALL_MODULES))}")
                        st.caption(f"Hết hạn: {info.get('expires_at')}")
                        if acc != ADMIN_EMAIL and st.button(f"🗑️ Xóa {acc}", key=f"del_acc_{acc}"):
                            del st.session_state.licensed_accounts[acc]
                            save_licensed_accounts(st.session_state.licensed_accounts)
                            st.toast("✅ Đã xóa tài khoản!")
                            st.rerun()

        st.markdown("---")
        st.markdown("""
        <div class="support-box">
            <b style="color: #166534; font-size: 0.95rem;">💬 Cần Hỗ Trợ / Mua Gói?</b><br>
            <p style="font-size: 0.85rem; color: #15803d; margin: 6px 0 8px 0;">Kết nối ngay với chúng tôi:</p>
            <div class="social-icons-container">
                <a href="#" class="btn-zalo" target="_blank">Zalo</a>
                <a href="#" class="btn-fb" target="_blank">f</a>
                <a href="#" class="btn-tt" target="_blank">♪</a>
            </div>
            <div style="font-weight: 700; color: #166534; font-size: 12px; margin-top: 8px;">📞 Hotline: 0968.484.369</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🔐 TÀI KHOẢN")
        st.success(f"Đang dùng: {st.session_state.current_email}")
        if st.button("🚪 Đăng Xuất"):
            st.session_state.is_logged_in = False
            st.toast("✅ Đã đăng xuất!")
            st.rerun()

if not st.session_state.is_logged_in:
    st.info("👈 Vui lòng đăng nhập ở thanh công cụ bên trái.")
    st.stop()
