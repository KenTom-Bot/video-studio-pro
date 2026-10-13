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
import uuid
import io
from PIL import Image
from datetime import datetime, timedelta, date

st.set_page_config(page_title="Đạo Diễn AI - Hệ Thống Kịch Bản Pro", page_icon="🎬", layout="wide")

ga_script = """
<script>
    if (!window.parent.document.getElementById('ga-script')) {
        var script = document.createElement('script');
        script.id = 'ga-script';
        script.src = "https://www.googletagmanager.com/gtag/js?id=G-19YJP7NJ6W";
        script.async = true;
        window.parent.document.head.appendChild(script);

        var script2 = document.createElement('script');
        script2.innerHTML = `
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'G-19YJP7NJ6W');
        `;
        window.parent.document.head.appendChild(script2);
    }
</script>
"""
components.html(ga_script, width=0, height=0)

def lock_ui():
    st.markdown("""
    <style>
        div[data-testid="stAppViewContainer"] { pointer-events: none; opacity: 0.65; transition: opacity 0.3s ease; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
    .header-container { text-align: center; padding: 1.2rem; background: radial-gradient(circle, rgba(255,75,75,0.08) 0%, rgba(255,255,255,0) 70%); border-radius: 16px; margin-bottom: 1rem; }
    .main-title { font-size: 2.2rem !important; font-weight: 900 !important; background: linear-gradient(90deg, #ff0050 0%, #ff5252 50%, #ff7300 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    div[data-testid="stButton"] > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button[kind="primary"] { background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important; color: white !important; border-radius: 8px !important; font-weight: bold; width: 100%; }
    div[data-testid="stButton"] > button[kind="secondary"], div[data-testid="stFormSubmitButton"] > button[kind="secondary"] { background: linear-gradient(135deg, #ff4b4b 0%, #ff7300 100%) !important; color: #ffffff !important; box-shadow: 0 3px 8px rgba(255, 75, 75, 0.35) !important; padding: 0.55rem 1rem !important; font-weight: bold !important; border: none !important; width: 100%; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 3px 8px; border-radius: 4px; font-size: 11px; border: 1px solid #bbf7d0; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 3px 8px; border-radius: 4px; font-size: 11px; border: 1px solid #fde68a; }
    .detail-header-box { background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%); border: 1.5px solid #bfdbfe; border-radius: 12px; padding: 16px 20px; margin-bottom: 22px; color: #1e3a8a; line-height: 1.8; box-shadow: 0 3px 10px rgba(0,0,0,0.03); }
    .voiceover-text { color: #15803d; background: #f0fdf4; padding: 12px 14px; border-radius: 8px; font-size: 15.5px; border: 1px solid #bbf7d0; display: block; width: 100%; margin-top: 4px; line-height: 1.8; white-space: pre-line; }
    .timing-badge { font-size: 13px; font-weight: 700; color: #1e40af; background: #dbeafe; padding: 3px 8px; border-radius: 5px; border: 1px solid #bfdbfe; display: inline-block; margin-bottom: 6px; }
    div[data-testid="stFileUploader"] section { padding: 4px; min-height: 2rem; border: 1.5px dashed #cbd5e1 !important; background-color: #f8fafc !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div { background-color: #f8fafc !important; border: 1.5px solid #cbd5e1 !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

ALL_MODULES = ["🛒 TikTok Shop & Bán Hàng", "🌟 Viral & Xây Kênh"]
ADMIN_EMAIL = "binhnguyenmedia.vn@gmail.com"

@st.cache_resource
def init_supabase():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None
supabase = init_supabase()

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
client = genai.Client(api_key=api_key) if api_key else None

def count_words(text: str) -> int:
    return len(re.findall(r'\b\w+\b', text)) if text else 0

def calculate_speech_duration(text: str) -> float:
    words = count_words(text)
    commas = text.count(',') + text.count(';')
    return round((words / 3.9) + (commas * 0.25), 1)

def is_valid_phone(phone):
    phone = phone.strip()
    return phone.isdigit() and phone.startswith('0') and 9 <= len(phone) <= 11

def compress_image_bytes(uploaded_file, max_dimension=1024, quality=80):
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        out_buffer = io.BytesIO()
        img.save(out_buffer, format="JPEG", quality=quality, optimize=True)
        return out_buffer.getvalue(), "image/jpeg"
    except Exception:
        return uploaded_file.getvalue(), (uploaded_file.type or "image/jpeg")

POLICY_REPLACEMENTS = {
    r'\btuyệt\s*đối\b': 'rất',
    r'\bhoàn\s*toàn\b': 'thực sự',
    r'\b100\s*%\b': 'rất nhiều',
    r'\bchắc\s*chắn\b': 'rất có thể',
    r'\bcam\s*kết\b': 'an tâm',
    r'\bdứt\s*điểm\b': 'cải thiện',
    r'\bđặc\s*trị\b': 'hỗ trợ',
    r'\bkhỏi\s*hẳn\b': 'đỡ hẳn',
    r'\bvĩnh\s*viễn\b': 'lâu dài',
    r'\bchuẩn\s*đét\b': 'vừa vặn',
    r'\bchữa\s*khỏi\b': 'hỗ trợ'
}

def sanitize_policy_text(text: str) -> str:
    if not text: return ""
    cleaned = text
    for pattern, rep in POLICY_REPLACEMENTS.items():
        cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    return cleaned

def load_licensed_accounts():
    accs = {ADMIN_EMAIL: {"roles": ALL_MODULES, "phone": "0869628316", "expires_at": "2099-12-31", "password": "admin", "plan_type": "VIP", "active_session_id": ""}}
    if not supabase: return accs
    try:
        res = supabase.table("licensed_accounts").select("*").execute()
        for row in res.data:
            accs[row["email"]] = {
                "roles": row.get("roles", ALL_MODULES), "phone": row.get("phone", ""),
                "password": row.get("password", ""), "expires_at": row.get("expires_at", "2099-12-31"),
                "plan_type": row.get("plan_type", "Trial"), "daily_usage_count": row.get("daily_usage_count", 0),
                "last_generation_date": row.get("last_generation_date", ""), "active_session_id": row.get("active_session_id", "")
            }
    except: pass
    return accs

def save_single_account(email, acc_data):
    if not supabase or email == ADMIN_EMAIL: return
    try: supabase.table("licensed_accounts").upsert({"email": email, **acc_data}).execute()
    except: pass

def delete_single_account(email):
    if not supabase or email == ADMIN_EMAIL: return
    try: supabase.table("licensed_accounts").delete().eq("email", email).execute()
    except: pass

def check_usage_limit(email, is_detailing=False):
    if email == ADMIN_EMAIL: return True, ""
    acc = st.session_state.licensed_accounts.get(email)
    if not acc: return False, "Lỗi xác thực tài khoản."
    if datetime.now() > datetime.strptime(acc.get("expires_at", "2099-12-31"), "%Y-%m-%d"):
        return False, "Tài khoản đã hết hạn. Vui lòng gia hạn!"
    plan = acc.get("plan_type", "Trial")
    if plan == "VIP": return True, ""
    limit = {"Advanced": 20, "Basic": 10, "Trial": 3}.get(plan, 3)
    today = datetime.now().strftime("%Y-%m-%d")
    if acc.get("last_generation_date") != today:
        acc["daily_usage_count"] = 0
        acc["last_generation_date"] = today
    if is_detailing:
        if acc.get("daily_usage_count", 0) >= limit: return False, f"Hết lượt tạo chi tiết kịch bản ({limit}/{limit}) hôm nay!"
        acc["daily_usage_count"] += 1
        save_single_account(email, acc)
    return True, ""

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
            setTimeout(() => {{ document.getElementById("{html_id}").innerText = "{button_label}"; }}, 2000);
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
    if isinstance(field_val, list): return "<br>".join([f"• {str(item)}" for item in field_val])
    text = str(field_val).strip()
    return "".join([f"<div style='margin-left: 10px; margin-top: 3px;'>• {line.strip()}</div>" for line in text.split('<br>') if line.strip()])

if "session_id" not in st.session_state: st.session_state.session_id = str(uuid.uuid4())
for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", load_licensed_accounts()),
    ("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []),
    ("generated_details", {}), ("content_analysis", None), ("active_script_id", None),
    ("current_input_context", ""), ("current_product_data_saved", None), ("current_product_data", None),
    ("reset_key", 0), ("scroll_to_top", False), ("scroll_to_detail", False),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"),
    ("last_mode", ""), ("last_style", ""), ("last_narrator", ""),
    ("target_duration_instruction", ""), ("character_profiles", []), ("current_project_id", None),
    ("saved_reference_images", []), ("show_all_projects", False), ("show_all_admin_accounts", False),
    ("current_processing_id", None)
]:
    if key not in st.session_state: st.session_state[key] = default_val

if st.session_state.is_logged_in and st.session_state.current_email != ADMIN_EMAIL:
    current_acc_lock = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
    if current_acc_lock.get("active_session_id") != st.session_state.session_id:
        st.error("🚨 TÀI KHOẢN ĐANG ĐĂNG NHẬP Ở THIẾT BỊ KHÁC.")
        if st.button("🔌 Sử dụng trên thiết bị này", type="primary"):
            st.session_state.licensed_accounts[st.session_state.current_email]["active_session_id"] = st.session_state.session_id
            save_single_account(st.session_state.current_email, st.session_state.licensed_accounts[st.session_state.current_email])
            st.rerun()
        st.stop()

if st.session_state.scroll_to_top:
    components.html("<script>window.parent.scrollTo({top: 0, behavior: 'smooth'});</script>", height=0)
    st.session_state.scroll_to_top = False

if st.session_state.scroll_to_detail:
    components.html("""
    <script>
        setTimeout(function() {
            var el = window.parent.document.getElementById('detailed-view-anchor');
            if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }
            else { window.parent.scrollTo({top: 400, behavior: 'smooth'}); }
        }, 300);
    </script>
    """, height=0)
    st.session_state.scroll_to_detail = False

def repair_and_parse_json(text_content: str):
    cleaned = re.sub(r'```(?:json)?', '', text_content).strip()
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    candidate = match.group(0) if match else cleaned

    def try_parse(s):
        try:
            p = json.loads(s, strict=False)
            return p[0] if isinstance(p, list) and len(p) > 0 else p
        except Exception: return None

    res = try_parse(candidate)
    if res is not None: return res

    fixed = candidate.rstrip(", \n\r\t")
    fixed += "}" if fixed.count("{") > fixed.count("}") else ""
    fixed += "]" if fixed.count("[") > fixed.count("]") else ""
    res = try_parse(fixed)
    if res is not None: return res

    try:
        py_str = candidate.replace('true', 'True').replace('false', 'False').replace('null', 'None')
        parsed = ast.literal_eval(py_str)
        return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else parsed
    except Exception:
        raise Exception("AI sinh JSON lỗi cấu trúc. Vui lòng thử lại.")

def call_gemini(contents, sys_inst="Bạn là AI hỗ trợ JSON.", max_tokens=7000):
    model_name = "gemini-3.8-flash"
    for attempt in range(2):
        try:
            res = client.models.generate_content(
                model=model_name, contents=contents,
                config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.7, max_output_tokens=max_tokens)
            )
            return repair_and_parse_json(res.text)
        except Exception as e:
            if "404" in str(e).lower() or "not_found" in str(e).lower(): model_name = "gemini-3.8-flash-lite"
            if attempt == 1: raise e
            time.sleep(1)

def build_voice_direction(mode, num_chars, character_profiles):
    is_tiktok_shop = "TikTok Shop" in mode
    if num_chars <= 1:
        if is_tiktok_shop:
            return "Giọng [Nam/Nữ] HÀ NỘI GỐC 100%, tốc độ NHANH, DỒN DẬP, METRONOME (4.2 - 4.5 từ/s)."
        else:
            return "Giọng [Nam/Nữ] HÀ NỘI GỐC 100%, nhịp độ biến thiên linh hoạt theo cảm xúc kịch bản."
    else:
        directions = []
        for p in character_profiles:
            r = str(p.get('role', '')).lower()
            if any(k in r for k in ["bé", "con", "trẻ", "nhỏ", "gái", "trai", "em"]):
                v = f"Diễn viên {p['id']} ({p['role']}): Giọng thiếu nhi miền Bắc líu lo, ngây thơ, ngọng nghịu đáng yêu."
            elif any(k in r for k in ["bố", "ba", "chồng", "anh", "nam"]):
                v = f"Diễn viên {p['id']} ({p['role']}): Giọng nam miền Bắc trầm ấm, tự nhiên."
            elif any(k in r for k in ["ông", "bà", "già"]):
                v = f"Diễn viên {p['id']} ({p['role']}): Giọng người lớn tuổi miền Bắc từ tốn, ấm áp."
            else:
                v = f"Diễn viên {p['id']} ({p['role']}): Giọng nữ Hà Nội chuẩn, dịu dàng, ấm áp."
            directions.append(v)
        return " | ".join(directions)

def generate_char_rules_string(profiles):
    if not profiles: return "KOC_IDENTITY: 100% người Việt Nam bản địa (East Asian/Vietnamese ethnicity), tóc đen tự nhiên, khóa kiểu tóc và trang phục cố định."
    rules = "DANH SÁCH DIỄN VIÊN (KHÓA 100% NGƯỜI VIỆT THUẦN TÚY):\n"
    for p in profiles: 
        rules += f" - Diễn viên {p['id']} ({p['role']}): 100% thuần Việt, tóc đen tự nhiên, mắt đen, khóa kiểu tóc và trang phục cố định suốt 4 cảnh.\n"
    return rules

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, angle):
    is_multi = (num_chars >= 2)
    format_direction = f"ĐỊNH DẠNG: TIỂU PHẨM ĐỐI THOẠI {num_chars} NHÂN VẬT THUẦN VIỆT." if is_multi else "ĐỊNH DẠNG: ĐỘC THOẠI KOC THUẦN VIỆT."
    strat_cmd = "BẠN PHẢI MIX ĐA DẠNG 5 GÓC ĐỘ NỘI DUNG." if "Tự động mix" in angle else f"VIẾT CẢ 5 KỊCH BẢN THEO: '{angle}'."
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL TIKTOK SHOP & VIRAL TRIỆU VIEW VIỆT NAM. PHONG CÁCH: {style}
    {strat_cmd} | {format_direction}
    
    🛑 BỘ LỌC CHÍNH SÁCH BÁN HÀNG VIỆT NAM (100%):
    1. CẤM: 'tuyệt đối', 'hoàn toàn', '100%', 'chắc chắn', 'cam kết', 'dứt điểm', 'đặc trị', 'khỏi hẳn', 'vĩnh viễn', 'chuẩn đét', 'chữa khỏi'.
       - DÙNG: 'hỗ trợ', 'cải thiện', 'tiện ích', 'đáng thử', 'ưng ý', 'an tâm'.
    2. NHÂN VẬT: 100% người Việt bản địa. Tuyệt đối cấm mặt Tây/ngoại quốc.
    3. {char_rules}
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction, num_chars, character_profiles):
    is_on_camera = "On-camera" in narrator_mode
    is_multi = (num_chars >= 2)
    is_viral = "Viral" in mode
    voice_guidance = build_voice_direction(mode, num_chars, character_profiles)

    dialogue_type_rule = f"""
    🛑 QUY TẮC ĐỐI THOẠI {num_chars} NHÂN VẬT:
    - Tách từng câu thoại rõ ràng theo tên vai: (Mẹ: "..." | Bé: "...").
    - Giọng trẻ em líu lo ngây thơ ngọng nghịu; Mẹ dịu dàng; Bố đĩnh đạc.
    """ if is_multi else """
    🛑 QUY TẮC ĐỘC THOẠI KOC:
    - Lời thoại là một đoạn văn liền mạch 1 giọng đọc KOC Hà Nội chuẩn.
    """

    outro_instruction = """
    🛑 CẢNH 4 (KẾT BÀI VIRAL): Cả nhà cười tươi, vẫy tay chào camera. Thoại kêu gọi follow tự nhiên.
    """ if is_viral else """
    🛑 CẢNH 4 (CHỐT DEAL TIKTOK SHOP): Lồng ghép sản phẩm làm đạo cụ tự nhiên từ Cảnh 2 và 3. Cảnh 4 kêu gọi mua hàng tinh tế hướng về góc trái.
    """

    audio_cmd = "Chèn `Audio:` vào `vid_p`." if is_on_camera else "Không chèn thoại vào `vid_p`."

    return f"""
    BẠN LÀ BẬC THẦY BIÊN KỊCH TIKTOK THỰC CHIẾN TẠI VIỆT NAM. PHONG CÁCH: {style}
    CHỈ ĐẠO GIỌNG ĐỌC: {voice_guidance}
    {dialogue_type_rule}
    {outro_instruction}
    
    🛑 KHÓA THỜI LƯỢNG & SỐ TỪ CHUẨN XÁC:
    - CẢNH 1 (6 GIÂY): TỐI ĐA 18 - 22 TỪ (tối đa 2 dấu phẩy). TUYỆT ĐỐI CẤM vượt quá 22 từ!
    - CẢNH 2 (8 GIÂY): TỐI ĐA 26 - 30 TỪ (tối đa 3 dấu phẩy).
    - CẢNH 3 (10 GIÂY): TỐI ĐA 34 - 38 TỪ (tối đa 4 dấu phẩy).
    - CẢNH 4 (6 GIÂY): TỐI ĐA 18 - 22 TỪ (tối đa 2 dấu phẩy).

    🛑 BỘ LỌC CHÍNH SÁCH BÁN HÀNG: CẤM 'tuyệt đối', 'hoàn toàn', '100%', 'cam kết', 'dứt điểm', 'đặc trị', 'khỏi hẳn', 'vĩnh viễn', 'chữa khỏi'.

    🛑 CÔNG THÁI HỌC THỰC TẾ & KHÓA SẮC TỘC THUẦN VIỆT (ERGONOMICS & 100% ETHNICITY LOCK):
    1. 100% NGƯỜI VIỆT BẢN ĐỊA: Đặt đầu mọi prompt: "Authentic native Vietnamese person, natural Vietnamese features, black hair, warm skin tone". Cuối mọi prompt: "Negative prompt: Caucasian, white, European, blonde hair, blue eyes, foreign face".
    2. HÀNH ĐỘNG THỰC TẾ ĐỜI THƯỜNG (REALISTIC ERGONOMICS):
       - Khi xem lớp lót trong áo khoác: Phải kéo khóa trước xuống một nửa và mở nhẹ vạt áo trước ngực để xem lớp lót lưới tổ ong, hoặc cởi hẳn áo cầm tay. CẤM kéo lật ngược vạt áo từ sau lưng khi áo đang cài kín!
       - Khi thử chăn ga: Hai tay vuốt nhẹ mặt nỉ, kéo căng góc chun bọc mép đệm.
       - Khi nấu ăn: Đồ nóng có khói bốc nghi ngút (*rising steam vapors*), dầu sôi xèo xèo.
    3. KHÓA 1 SẢN PHẨM: "Strictly single hero product instance: NO duplicate ghost products, NO floating items, NO telekinesis. Physically grounded realistic human handling."
    4. TRIỆT TIÊU ICON GIỎ HÀNG, NÚT BẤM: "NO yellow shopping cart icons, NO floating buttons, NO UI overlays, NO text, NO subtitles. Clean pristine frame."
    5. {audio_cmd}
    6. {char_rules}
    """

def create_scene_details(target_id, mode, style):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if sc["id"] == target_id), None)
    if not outline: return
    
    narrator_mode = outline.get("narrator_mode", st.session_state.get("last_narrator", "On-camera"))
    char_profiles = outline.get("character_profiles", st.session_state.get("character_profiles", []))
    char_rules = generate_char_rules_string(char_profiles)
    num_chars = outline.get("actors", outline.get("actor_count", len(char_profiles) if char_profiles else 1))
    is_multi = (num_chars >= 2)
    is_viral = "Viral" in mode
    
    is_on_camera = "On-camera" in narrator_mode
    prod_data_ctx = json.dumps(st.session_state.get('current_product_data_saved'), ensure_ascii=False)
    dna_data_ctx = json.dumps(st.session_state.get('content_analysis'), ensure_ascii=False)
    voice_guidance = build_voice_direction(mode, num_chars, char_profiles)
    
    audio_instruction = 'Chèn: Audio: "[CHÉP ĐỦ 100% LỜI THOẠI PHÂN VAI]", Layered SFX: [SFX thực tế]' if is_on_camera else 'Chỉ chèn Layered SFX thực tế, không chèn thoại.'
    fixed_title = outline.get('title', 'Kịch bản chi tiết')
    fixed_hook = sanitize_policy_text(outline.get('hook', ''))

    format_guideline = f"""
    - TIỂU PHẨM {num_chars} NHÂN VẬT THUẦN VIỆT: Lời thoại tách từng câu (Mẹ: "..." | Bé: "...").
    - BỐ CỤC: Bố trí TẤT CẢ nhân vật cùng xuất hiện trong 1 khung hình dọc 9:16. 100% người Việt thuần túy.
    """ if is_multi else """
    - ĐỘC THOẠI KOC: Lời thoại liền mạch 1 giọng Hà Nội chuẩn.
    """

    prompt_text = f"""
    DỮ LIỆU: {prod_data_ctx} | DNA: {dna_data_ctx}
    KỊCH BẢN #{target_id}: TIÊU ĐỀ: '{fixed_title}' | HOOK CẢNH 1: '{fixed_hook}' | BỐI CẢNH: {outline.get('setting', 'Phòng khách gia đình ấm cúng')}
    THUYẾT MINH: {audio_instruction} | LOẠI: {mode} | CHỈ ĐẠO GIỌNG: {voice_guidance}
    {format_guideline}
    
    🛑 LỆNH CƯỠNG CHẾ KHÓA THỜI LƯỢNG, SẮC TỘC VÀ HÀNH VI THỰC TẾ:
    1. CẢNH 1 (6s): Lời thoại 18-22 từ (tối đa 2 dấu phẩy). CẤM vượt quá 22 từ!
    2. CẢNH 2 (8s): Lời thoại 26-30 từ (tối đa 3 dấu phẩy).
    3. CẢNH 3 (10s): Lời thoại 34-38 từ (tối đa 4 dấu phẩy).
    4. CẢNH 4 (6s): Lời thoại 18-22 từ (tối đa 2 dấu phẩy).
    5. CẤM TỪ: 'tuyệt đối', 'hoàn toàn', '100%', 'cam kết', 'dứt điểm', 'đặc trị', 'khỏi hẳn', 'vĩnh viễn'.
    6. HÀNH ĐỘNG THỰC TẾ CHUẨN CÔNG THÁI HỌC: Mọi thao tác kiểm tra/sử dụng sản phẩm phải tự nhiên, hợp lý, không kéo vặn áo kỳ dị.
    7. 100% NGƯỜI VIỆT THUẦN TÚY: Đặt 'Authentic native Vietnamese' lên đầu prompt. Thêm 'Negative prompt: Caucasian, white, European, blonde hair, blue eyes' ở cuối prompt.
    
    TRẢ VỀ JSON:
    {{
        "title": "{fixed_title}",
        "total_dur": "Khoảng 30 giây",
        "voice": {{"tone": "{voice_guidance}"}},
        "outfit_vi": "Trang phục và kiểu tóc đồng bộ của từng nhân vật",
        "director_summary": "⏱ <b>Thời lượng:</b> Khoảng 30 giây (Chuẩn 4 phân cảnh AIDA) | 🎙 <b>Chỉ đạo giọng:</b> {voice_guidance}<br>👨‍👩‍👧 <b>Đồng nhất diện mạo:</b> 100% nhân vật Việt Nam thuần túy, khóa kiểu tóc và trang phục đồng bộ xuyên suốt<br>🎯 <b>Sản phẩm & Hành vi:</b> Khóa 1 sản phẩm Hero SKU, thao tác chuẩn công thái học đời thực",
        "global_identity_en": "Authentic native Vietnamese persons with natural Vietnamese facial features and warm skin tone. EXACT LOCKED HAIRSTYLE AND OUTFIT for each character invariant across all scenes. Negative: Caucasian, white people, European, blonde hair, blue eyes.",
        "global_outfit_en": "Matching locked authentic outfits for all characters, invariant across all scenes.",
        "global_setting_en": "Authentic warm Vietnamese home room setting, invariant across all scenes.",
        "prod_dna": "Photorealistic description matching the reference product with realistic physical details, locked across all scenes.",
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention", "dur": "6s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh cảnh 1 với chi tiết giác quan thực tế...",
                "action_en": "Cinematic vertical 9:16 eye-level shot. Authentic native Vietnamese characters. Natural plausible human interaction. Negative: Caucasian, European, unnatural contortion.",
                "director": "Attention | Hook mở màn (18-22 từ) | SFX kích thích thính giác | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại mở đầu dựa trên câu hook gốc '{fixed_hook}' TUÂN THỦ NGHIÊM NGẶT từ 18 đến 22 từ...",
                "img_p": "Vertical 9:16 photo. Authentic native Vietnamese person. [global_setting_en]. Characters: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Strictly single product instance, realistic human handling. Strictly pure camera footage: NO yellow shopping cart icons, NO floating buttons, NO text, NO subtitles, NO UI overlays. Negative prompt: Caucasian, white, European, blonde hair, blue eyes, foreign face.",
                "vid_p": "Vertical 9:16 video. Authentic native Vietnamese person. [global_setting_en]. Characters: [global_identity_en] wearing [global_outfit_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ 100% LỜI THOẠI CẢNH 1]\\", Layered SFX: [tiếng thở dài/tiếng thực tế]. Product: [prod_dna]. Strictly single product instance: NO duplicate ghost products, NO floating items, NO telekinesis. Strictly pure live-action footage: NO yellow shopping cart icons, NO floating buttons, NO text, NO subtitles. Negative prompt: Caucasian, white, European, blonde hair, blue eyes."
            }},
            {{
                "scene": 2, "aida_stage": "Interest", "dur": "8s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh giải pháp xuất hiện với thao tác thực tế...",
                "action_en": "Dynamic satisfying demonstration showing realistic physical handling (e.g. unzipping front zipper halfway to show breathable inner lining, or gently smoothing bedsheet corners). Same locked Vietnamese characters.",
                "director": "Interest | Thao tác giải phóng nỗi đau (26-30 từ) | SFX thực tế | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại tự nhiên nối tiếp TUÂN THỦ NGHIÊM NGẶT từ 26 đến 30 từ...",
                "img_p": "Vertical 9:16 photo. Authentic native Vietnamese person. Satisfying realistic ergonomic handling. [global_setting_en]. Characters: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Negative prompt: Caucasian, white, European, blonde hair, blue eyes, unnatural handling.",
                "vid_p": "Vertical 9:16 video. Authentic native Vietnamese person. Realistic ergonomic interaction matching spoken dialogue. [global_setting_en]. Characters: [global_identity_en] wearing [global_outfit_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ 100% LỜI THOẠI CẢNH 2]\\", Layered SFX: [tiếng kéo khóa/tiếng vải thực tế]. Product: [prod_dna]. Strictly single product. Negative prompt: Caucasian, white, European, blonde hair, blue eyes."
            }},
            {{
                "scene": 3, "aida_stage": "Desire", "dur": "10s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh trải nghiệm giác quan & cảm xúc...",
                "action_en": "Heartwarming tactile sensory visual showcasing genuine happiness, comfort, and realistic physical textures. Physically plausible natural handling.",
                "director": "Desire | Trực quan hóa giá trị giác quan (34-38 từ) | SFX sống động | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại sâu sắc gắn kết TUÂN THỦ NGHIÊM NGẶT từ 34 đến 38 từ...",
                "img_p": "Vertical 9:16 photo. Authentic native Vietnamese person. Luxurious tactile sensory presentation. [global_setting_en]. Characters: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Negative prompt: Caucasian, white, European, blonde hair, blue eyes.",
                "vid_p": "Vertical 9:16 video. Authentic native Vietnamese person. Warm connection matching dialogue. [global_setting_en]. Characters: [global_identity_en] wearing [global_outfit_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ 100% LỜI THOẠI CẢNH 3]\\", Layered SFX: [tiếng vải mềm/tiếng cười thực tế]. Product: [prod_dna]. Negative prompt: Caucasian, white, European, blonde hair, blue eyes."
            }},
            {{
                "scene": 4, "aida_stage": "Action", "dur": "6s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh kết thúc...",
                "action_en": "Warm confident closing gesture: Authentic Vietnamese characters smiling, child waving or character gesturing warmly downward with open hand.",
                "director": "Action | Kêu gọi hành động tự nhiên / Đòn bẩy giá (18-22 từ) | SFX tươi vui | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại kết bài TUÂN THỦ NGHIÊM NGẶT từ 18 đến 22 từ...",
                "img_p": "Vertical 9:16 photo. Authentic native Vietnamese person. [global_setting_en]. Characters: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Negative prompt: Caucasian, white, European, blonde hair, blue eyes.",
                "vid_p": "Vertical 9:16 video. Authentic native Vietnamese person. [global_setting_en]. Characters: [global_identity_en] wearing [global_outfit_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ 100% LỜI THOẠI CẢNH 4]\\", Layered SFX: [tiếng chuông vui tai]. Product: [prod_dna]. Negative prompt: Caucasian, white, European, blonde hair, blue eyes."
            }}
        ]
    }}
    """
    
    payload = ["REFERENCE PRODUCT IMAGES:"]
    saved_imgs = st.session_state.get("saved_reference_images", [])
    if saved_imgs:
        for img_bytes, img_mime in saved_imgs:
            payload.append(types.Part.from_bytes(data=img_bytes, mime_type=img_mime))
    payload.append(prompt_text)

    res = call_gemini(payload, get_sys_inst_details(mode, style, narrator_mode, char_rules, "Khoảng 30 giây", num_chars, char_profiles), max_tokens=7000)
    if not res or "scenes" not in res: raise Exception("AI JSON Error.")
    
    for scn in res.get("scenes", []):
        if "voiceover" in scn: scn["voiceover"] = sanitize_policy_text(scn["voiceover"])
        if "director" in scn: scn["director"] = sanitize_policy_text(scn["director"])
            
    st.session_state.generated_details[target_id] = res

def generate_more_scripts(angle, num_chars, extra_char_inputs, narrator_mode_more, duration_inst, char_profiles):
    mode = st.session_state.get("last_mode", "Bán Hàng")
    style = st.session_state.get("last_style", "Điện ảnh")
    char_rules = generate_char_rules_string(char_profiles)
    cur_len = len(st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts)
    prod_ctx = f"INPUT: {st.session_state.current_input_context}"
    dna_ctx = f"DNA: {json.dumps(st.session_state.content_analysis, ensure_ascii=False)}" if st.session_state.content_analysis else ""
    
    prompt = f"""
    {prod_ctx} | {dna_ctx}
    Sinh 5 kịch bản mới chuẩn AIDA: '{angle}'. Diễn viên: {num_chars} người Việt.
    TUÂN THỦ CHÍNH SÁCH: CẤM 'tuyệt đối', 'hoàn toàn', '100%', 'cam kết', 'dứt điểm', 'đặc trị', 'khỏi hẳn'.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên kịch bản mới", "setting": "Bối cảnh...", "hook": "Câu hook 3s đầu ngắn gọn...", "actors": {num_chars} }}
        ]
    }}
    BẮT BUỘC ĐỦ 5 KỊCH BẢN.
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, narrator_mode_more, char_rules, num_chars, angle), max_tokens=3000)
    more_scripts = res.get("outlines", res.get("script_outlines", []))
    for idx, sc in enumerate(more_scripts):
        if "hook" in sc: sc["hook"] = sanitize_policy_text(sc["hook"])
        sc.update({"id": cur_len + idx + 1, "duration_instruction": duration_inst, "narrator_mode": narrator_mode_more, "character_profiles": char_profiles, "actors": num_chars})
    return more_scripts

def clone_script(script_id):
    mode = st.session_state.get("last_mode", "Bán Hàng")
    style = st.session_state.get("last_style", "Điện ảnh")
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if sc["id"] == script_id), None)
    cur_len = len(all_combined)
    num_chars = target.get("actors", target.get("actor_count", 1))
    
    prompt = f"Nhân bản kịch bản #{script_id}: {json.dumps(target, ensure_ascii=False)} thành 5 biến thể AIDA mới tuân thủ chính sách, CẤM từ cam kết."
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, target.get("narrator_mode", ""), "", num_chars, "Gốc"), max_tokens=3000)
    clones = res.get("outlines", res.get("script_outlines", []))
    for idx, cl in enumerate(clones):
        if "hook" in cl: cl["hook"] = sanitize_policy_text(cl["hook"])
        cl.update({"id": cur_len + idx + 1, "duration_instruction": target.get("duration_instruction", ""), "narrator_mode": target.get("narrator_mode", ""), "character_profiles": target.get("character_profiles", []), "actors": num_chars})
    return clones

def save_project_to_db(email, title, payload_data, project_id=None):
    if not supabase: return "Chưa kết nối Supabase."
    try:
        clean_content = json.loads(json.dumps(payload_data, default=str))
        if project_id: supabase.table("saved_projects").update({"project_title": title, "script_content": clean_content}).eq("id", project_id).execute()
        else:
            res = supabase.table("saved_projects").insert({"user_email": email, "project_title": title, "script_content": clean_content}).execute()
            if res.data: st.session_state.current_project_id = res.data[0]['id']
        return True
    except Exception as e: return str(e)

with st.sidebar:
    if not st.session_state.is_logged_in:
        tabs = st.tabs(["🔐 Đăng Nhập", "🚀 Đăng Ký Dùng Thử"])
        with tabs[0]:
            with st.form("login_form", border=False):
                email_input = st.text_input("Email:", key="f_login_email", autocomplete="new-password")
                pass_input = st.text_input("Mật khẩu:", type="password", key="f_login_pass", autocomplete="new-password")
                submit_login = st.form_submit_button("🔑 Đăng Nhập", type="primary", use_container_width=True)
                
                if submit_login:
                    email_c, pass_c = email_input.strip(), pass_input.strip()
                    if not email_c or not pass_c:
                        st.error("⚠️ Vui lòng nhập đầy đủ Email và Mật khẩu!")
                    elif email_c in st.session_state.licensed_accounts:
                        acc_data = st.session_state.licensed_accounts[email_c]
                        if acc_data.get("password") == pass_c:
                            st.session_state.licensed_accounts[email_c]["active_session_id"] = st.session_state.session_id
                            save_single_account(email_c, st.session_state.licensed_accounts[email_c])
                            st.session_state.is_logged_in = True
                            st.session_state.current_email = email_c
                            st.toast("✅ Đăng nhập thành công!")
                            time.sleep(0.4)
                            st.rerun()
                        else:
                            st.error("❌ Mật khẩu không chính xác!")
                    else:
                        st.error("❌ Email chưa được cấp quyền sử dụng!")
                        
        with tabs[1]:
            with st.form("register_form", border=False):
                r_email = st.text_input("Email đăng ký:", key="f_reg_email", autocomplete="new-password")
                r_phone = st.text_input("Số điện thoại:", key="f_reg_phone", autocomplete="new-password")
                r_pass = st.text_input("Mật khẩu mới:", type="password", key="f_reg_pass", autocomplete="new-password")
                r_purpose = st.selectbox("🎯 Mục đích chính bạn dùng app:", ["🛒 Tiếp thị liên kết / Bán hàng TikTok Shop", "🌟 Xây kênh thương hiệu / Video Viral", "⚡ Cả hai thể loại"], key="f_reg_purpose")
                submit_reg = st.form_submit_button("🚀 Đăng Ký Nhận 3 Lượt/Ngày", type="secondary", use_container_width=True)
                
                if submit_reg:
                    email_r, phone_r, pass_r = r_email.strip(), r_phone.strip(), r_pass.strip()
                    if not email_r or not phone_r or not pass_r:
                        st.error("⚠️ Vui lòng điền đủ tất cả các trường!")
                    elif not is_valid_phone(phone_r):
                        st.error("⚠️ Số điện thoại không hợp lệ!")
                    elif email_r in st.session_state.licensed_accounts:
                        st.error("⚠️ Email này đã tồn tại!")
                    else:
                        exp = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                        assigned_roles = ["🛒 TikTok Shop & Bán Hàng"] if "Tiếp thị liên kết" in r_purpose else (["🌟 Viral & Xây Kênh"] if "Xây kênh" in r_purpose else ALL_MODULES)
                        st.session_state.licensed_accounts[email_r] = {
                            "roles": assigned_roles, "phone": phone_r, "password": pass_r,
                            "expires_at": exp, "plan_type": "Trial", "daily_usage_count": 0,
                            "last_generation_date": "", "active_session_id": st.session_state.session_id
                        }
                        save_single_account(email_r, st.session_state.licensed_accounts[email_r])
                        st.session_state.is_logged_in = True
                        st.session_state.current_email = email_r
                        st.toast("✅ Đăng ký thành công!")
                        time.sleep(0.4)
                        st.rerun()
    else:
        st.markdown("### 🗂 DỰ ÁN")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True):
            st.session_state.update({k: v for k, v in [("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []), ("generated_details", {}), ("content_analysis", None), ("active_script_id", None), ("current_input_context", ""), ("current_project_id", None), ("saved_reference_images", []), ("current_processing_id", None)]})
            st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
            st.rerun()
            
        st.session_state.active_project_title = st.text_input("Tên dự án:", value=st.session_state.active_project_title)
        if st.button("💾 Lưu Dự Án Này", use_container_width=True):
            payload = {k: st.session_state[k] for k in ["content_analysis", "all_scripts", "cloned_scripts", "expanded_scripts", "generated_details", "character_profiles", "current_input_context"]}
            if save_project_to_db(st.session_state.current_email, st.session_state.active_project_title, payload, st.session_state.current_project_id):
                st.toast("✅ Đã lưu dự án!")
        
        st.markdown("---")
        st.markdown("### 📂 KHO DỰ ÁN")
        if supabase:
            try:
                res = supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
                all_projects = res.data or []
            except: all_projects = []

            search_proj = st.text_input("🔍 Tìm kiếm dự án:", placeholder="Nhập tên dự án...", key="search_proj_input")
            display_projects = [p for p in all_projects if search_proj.strip().lower() in p['project_title'].lower()] if search_proj.strip() else (all_projects if st.session_state.show_all_projects else all_projects[:3])

            if not display_projects:
                st.info("Chưa có dự án nào.")
            else:
                for p in display_projects:
                    with st.expander(f"🎬 {p['project_title']}"):
                        col_o, col_d = st.columns(2)
                        if col_o.button("📂 Mở", key=f"o_{p['id']}", use_container_width=True):
                            sd = p.get("script_content", {})
                            st.session_state.update({
                                "content_analysis": sd.get("content_analysis"), "all_scripts": sd.get("all_scripts", []),
                                "cloned_scripts": sd.get("cloned_scripts", []), "expanded_scripts": sd.get("expanded_scripts", []),
                                "generated_details": {int(k): v for k, v in sd.get("generated_details", {}).items()},
                                "character_profiles": sd.get("character_profiles", []), "current_project_id": p['id'], "active_project_title": p['project_title'],
                                "scroll_to_detail": True
                            })
                            st.rerun()
                        if col_d.button("🗑 Xóa", key=f"d_{p['id']}", type="secondary", use_container_width=True):
                            supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                            st.toast("✅ Đã xóa!")
                            time.sleep(0.3); st.rerun()

                if not search_proj.strip() and len(all_projects) > 3:
                    if st.session_state.show_all_projects:
                        if st.button("🔼 Thu gọn kho dự án", use_container_width=True):
                            st.session_state.show_all_projects = False
                            st.rerun()
                    else:
                        if st.button(f"🔽 Xem thêm {len(all_projects)-3} dự án", use_container_width=True):
                            st.session_state.show_all_projects = True
                            st.rerun()

        if st.session_state.current_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙ QUẢN TRỊ ADMIN")
            with st.expander("➕ Cấp Quyền Tài Khoản Mới", expanded=False):
                adm_acc = st.text_input("Email:", autocomplete="new-password", key="adm_in_acc")
                adm_phone = st.text_input("SĐT:", autocomplete="new-password", key="adm_in_phone")
                adm_pass = st.text_input("Mật khẩu:", value="123456", autocomplete="new-password", key="adm_in_pass")
                adm_roles_choice = st.multiselect("🎯 Thể loại cấp quyền:", ALL_MODULES, default=ALL_MODULES, key="adm_in_roles")
                adm_plan = st.radio("Gói cước:", ["Trial", "Basic", "Advanced", "VIP"], horizontal=True, key="adm_in_plan")
                adm_dur = st.selectbox("Thời hạn:", ["3 Ngày", "7 Ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "Vĩnh viễn", "Tùy chỉnh (Số ngày)"], key="adm_in_dur")
                
                calculated_exp_str = "2099-12-31"
                if adm_dur == "Tùy chỉnh (Số ngày)":
                    custom_num_days = st.number_input("👉 Số ngày:", min_value=1, max_value=3650, value=30, step=1, key="custom_num_days_input")
                    calculated_exp_str = (datetime.now() + timedelta(days=int(custom_num_days))).strftime("%Y-%m-%d")
                elif adm_dur != "Vĩnh viễn":
                    dur_map = {"3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365}
                    calculated_exp_str = (datetime.now() + timedelta(days=dur_map.get(adm_dur, 30))).strftime("%Y-%m-%d")

                if st.button("💾 Cấp Quyền Tài Khoản", type="primary", use_container_width=True, key="btn_submit_grant_admin"):
                    if adm_acc.strip() and adm_phone.strip() and adm_pass.strip() and adm_roles_choice:
                        st.session_state.licensed_accounts[adm_acc.strip()] = {
                            "roles": adm_roles_choice, "phone": adm_phone.strip(), "password": adm_pass.strip(),
                            "expires_at": calculated_exp_str, "plan_type": adm_plan, "daily_usage_count": 0,
                            "last_generation_date": "", "active_session_id": ""
                        }
                        save_single_account(adm_acc.strip(), st.session_state.licensed_accounts[adm_acc.strip()])
                        st.toast(f"✅ Đã cấp quyền đến {calculated_exp_str}!")
                        time.sleep(0.4); st.rerun()
                    else: st.error("⚠️ Vui lòng nhập đầy đủ thông tin!")

            st.markdown("##### 👥 Danh Sách Tài Khoản & Gia Hạn")
            search_acc = st.text_input("🔍 Tìm tài khoản:", placeholder="Nhập email/SĐT...", key="search_acc_input")
            other_accs = [item for item in st.session_state.licensed_accounts.items() if item[0] != ADMIN_EMAIL]
            filt_accs = [item for item in other_accs if search_acc.strip().lower() in item[0].lower() or search_acc.strip() in item[1].get('phone', '')] if search_acc.strip() else (other_accs if st.session_state.show_all_admin_accounts else other_accs[:3])

            for acc_mail, info in filt_accs:
                with st.expander(f"👤 {acc_mail} ({info.get('plan_type')})"):
                    st.write(f"📞 SĐT: `{info.get('phone', 'N/A')}` | ⏳ Hạn: `{info.get('expires_at')}`")
                    new_roles = st.multiselect("Thể loại:", ALL_MODULES, default=info.get("roles", ALL_MODULES), key=f"roles_sel_{acc_mail}")
                    new_plan = st.selectbox("Gói cước:", ["Trial", "Basic", "Advanced", "VIP"], index=["Trial", "Basic", "Advanced", "VIP"].index(info.get("plan_type", "Trial")), key=f"plan_sel_{acc_mail}")
                    renew_choice = st.selectbox("Gia hạn:", ["Giữ nguyên", "3 Ngày", "7 Ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "Vĩnh viễn"], key=f"renew_opt_{acc_mail}")
                    
                    target_exp_str = info.get("expires_at", "2099-12-31")
                    if renew_choice == "Vĩnh viễn": target_exp_str = "2099-12-31"
                    elif renew_choice != "Giữ nguyên":
                        dur_map = {"3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365}
                        target_exp_str = (datetime.now() + timedelta(days=dur_map.get(renew_choice, 30))).strftime("%Y-%m-%d")

                    c_act1, c_act2 = st.columns(2)
                    if c_act1.button("🔄 Cập Nhật", key=f"save_renew_{acc_mail}", use_container_width=True):
                        st.session_state.licensed_accounts[acc_mail].update({"roles": new_roles, "plan_type": new_plan, "expires_at": target_exp_str})
                        save_single_account(acc_mail, st.session_state.licensed_accounts[acc_mail])
                        st.toast("✅ Đã cập nhật!"); time.sleep(0.4); st.rerun()
                    if c_act2.button("🗑 Xóa", key=f"del_acc_{acc_mail}", type="secondary", use_container_width=True):
                        delete_single_account(acc_mail)
                        del st.session_state.licensed_accounts[acc_mail]
                        st.toast("✅ Đã xóa!"); time.sleep(0.3); st.rerun()

        st.markdown("---")
        support_iframe_code = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
                body { background: transparent; padding: 2px; }
                .support-container { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1.5px solid #86efac; border-radius: 14px; padding: 12px 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
                .support-title { font-size: 14px; font-weight: 800; color: #15803d; margin-bottom: 7px; display: flex; align-items: center; justify-content: center; gap: 6px; letter-spacing: 0.3px; }
                .hotline-card { background: linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%); border-radius: 10px; padding: 8px 6px; box-shadow: 0 3px 8px rgba(153, 27, 27, 0.25); user-select: all; text-align: center; }
                .hotline-label { color: #fecdd3 !important; font-size: 12.5px; font-weight: 700; margin-bottom: 3px; display: flex; align-items: center; justify-content: center; gap: 5px; }
                .hotline-number { color: #ffffff !important; font-size: 20px; font-weight: 900; letter-spacing: 1.2px; line-height: 1.2; text-shadow: 0 1px 3px rgba(0,0,0,0.35); }
            </style>
        </head>
        <body>
            <div class="support-container">
                <div class="support-title">
                    <svg style="width: 17px; height: 17px; fill: #15803d;" viewBox="0 0 24 24"><path d="M12 1a9 9 0 0 0-9 9v7c0 1.66 1.34 3 3 3h3v-8H5v-2a7 7 0 0 1 14 0v2h-4v8h3c.55 0 1-.45 1-1v-4.18A3 3 0 0 0 21 14V10a9 9 0 0 0-9-9z"/></svg>
                    <span>HỖ TRỢ TRỰC TIẾP</span>
                </div>
                <div class="hotline-card">
                    <div class="hotline-label">
                        <svg style="width: 13px; height: 13px; fill: #fecdd3;" viewBox="0 0 24 24"><path d="M6.62 10.79a15.05 15.05 0 0 0 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
                        <span>Hotline / Zalo:</span>
                    </div>
                    <div class="hotline-number">0869 628 316</div>
                </div>
            </div>
        </body>
        </html>
        """
        components.html(support_iframe_code, height=115)

        u_info = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        u_plan = u_info.get("plan_type", "Trial")
        u_used = u_info.get("daily_usage_count", 0) if u_info.get("last_generation_date") == datetime.now().strftime("%Y-%m-%d") else 0
        u_lim = "Không giới hạn" if u_plan == "VIP" else (20 if u_plan == "Advanced" else (10 if u_plan == "Basic" else 3))
        st.info(f"**GÓI {u_plan.upper()}**\n\n• Email: {st.session_state.current_email}\n• Đã tạo: **{u_used}/{u_lim}**\n• Hạn dùng: {u_info.get('expires_at')}")

        if st.button("🚪 Đăng Xuất"): 
            st.session_state.is_logged_in = False
            st.rerun()

if not st.session_state.is_logged_in: st.info("👈 Vui lòng đăng nhập ở thanh bên."); st.stop()

# ==============================================================================
# 5. KHÔNG GIAN SÁNG TẠO CHÍNH
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Đạo Diễn AI - Hệ Thống Kịch Bản Pro</div></div>""", unsafe_allow_html=True)

user_allowed_modules = st.session_state.licensed_accounts.get(st.session_state.current_email, {}).get("roles", ALL_MODULES) or ALL_MODULES
mode = st.selectbox("🎯 Thể loại:", user_allowed_modules, key=f"mode_sel_{st.session_state.reset_key}")
is_viral_mode = "Viral" in mode

up_files, custom_note = [], ""
if is_viral_mode:
    col_v1, col_v2 = st.columns(2)
    viral_persona = col_v1.text_input("👤 Định vị Kênh:")
    viral_topic = col_v2.text_area("💡 Chủ đề / Mẹo:", height=68)
    up_files = st.file_uploader("📦 Upload Ảnh:", type=["jpg", "png"], accept_multiple_files=True)
    custom_note = st.text_area("✍ Ghi chú AI:")
else:
    products_data = supabase.table("products").select("*").execute().data if supabase else []
    if products_data:
        selected_name = st.selectbox("📌 Chọn sản phẩm:", [p["product_name"] for p in products_data])
        st.session_state.current_product_data = next(p for p in products_data if p["product_name"] == selected_name)
    up_files = st.file_uploader("📦 Upload Ảnh SP (Quét OCR Giá, Hero SKU & Bảng màu):", type=["jpg", "png"], accept_multiple_files=True)
    custom_note = st.text_area("✍ Ghi chú AI:")

col_opt1, col_opt2 = st.columns(2)
style = col_opt1.selectbox("🎨 Phong cách:", ["Điện Ảnh Chân Thực", "Hoạt Hình 3D", "Studio Tối Giản"])
angle_options = ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Chia sẻ", "😂 Hài hước"]
initial_angle = col_opt1.selectbox("🧭 Chiến lược:", angle_options)
narrator_mode = col_opt2.selectbox("🎙 Thuyết minh:", ["Nhân vật xuất hiện (On-camera)", "🎙 Lồng tiếng ngoài (Off-screen)"])
num_chars = col_opt2.number_input("👤 Số Diễn viên (1 = Độc thoại KOC, ≥2 = Tiểu phẩm đối thoại):", 1, 8, 1)

char_inputs = []
for i in range(num_chars):
    c_r, c_i = st.columns([2, 1])
    role_default = "Mẹ trẻ 26 tuổi người Việt" if (num_chars >= 2 and i == 0) else ("Bé trai 4 tuổi người Việt" if (num_chars >= 2 and i == 1) else ("Bé gái 1 tuổi người Việt" if (num_chars >= 2 and i == 2) else ""))
    role = c_r.text_input(f"Vai trò NV {i+1}:", value=role_default, key=f"r_{i}")
    c_file = c_i.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"f_{i}", label_visibility="collapsed")
    if c_file: char_inputs.append({"id": i+1, "role": role or f"Diễn viên {i+1}", "file": c_file})

if st.button("🚀 PHÂN TÍCH DNA & SINH 5 KỊCH BẢN ĐA VŨ TRỤ", type="primary", use_container_width=True):
    can_run, msg = check_usage_limit(st.session_state.current_email)
    if not can_run: st.error(msg)
    else:
        with st.spinner("⏳ Đạo diễn AI đang quét OCR bảng màu, nhận diện Hero SKU và phân tích DNA..."):
            try:
                st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs] if char_inputs else [{"id": i+1, "role": f"Diễn viên {i+1}"} for i in range(num_chars)]
                char_rules = generate_char_rules_string(st.session_state.character_profiles)
                st.session_state.update({"last_mode": mode, "last_style": style, "last_narrator": narrator_mode, "current_input_context": custom_note})
                st.session_state.current_product_data_saved = st.session_state.get("current_product_data", {})
                
                st.session_state["saved_reference_images"] = []
                if up_files:
                    for f in up_files:
                        cb, cm = compress_image_bytes(f, 1024, 80)
                        st.session_state["saved_reference_images"].append((cb, cm))

                prompt = f"""
                INPUT: {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)} | NOTE: {custom_note}
                DIỄN VIÊN: {num_chars} nhân vật 100% người Việt bản địa ({', '.join([p['role'] for p in st.session_state.character_profiles])}).
                BẮT BUỘC TRẢ VỀ JSON:
                {{
                    "content_analysis": {{
                        "target_audience": "Tệp khách hàng mục tiêu",
                        "core_value": "Giá trị cốt lõi",
                        "pain_points": "Nỗi đau thực tế",
                        "hook_element": "Yếu tố giật gân 3 giây đầu",
                        "hero_sku_color": "Mã màu bán chạy nhất (Hero SKU)",
                        "color_palette": "Bảng màu toàn bộ",
                        "what_and_unique": "Sản phẩm là gì & điểm độc bản",
                        "target_user": "Sản phẩm dành cho ai",
                        "why_buy": "Tại sao nên mua",
                        "where_and_convenience": "Dùng ở đâu & tiện lợi",
                        "how_to_use": "Cách sử dụng thực tế chuẩn công thái học",
                        "product_size_class": "Phân loại kích thước",
                        "product_color_lock": "Khóa màu sắc và họa tiết Hero SKU",
                        "lid_mechanism": "Cơ chế hoạt động/mở nắp",
                        "detected_prices": "Quét OCR giá tiền",
                        "rounded_price_anchor": "Làm tròn giá niêm yết",
                        "product_dimensions": "Thông số kích thước",
                        "prompt_dna_lock": "Visual DNA cho video"
                    }},
                    "outlines": [
                        {{ "id": 1, "title": "Tên kịch bản 1", "setting": "Bối cảnh chuẩn...", "hook": "Câu hook 3s đầu ngắn gọn...", "actors": {num_chars} }},
                        {{ "id": 2, "title": "Tên kịch bản 2", "setting": "...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 3, "title": "Tên kịch bản 3", "setting": "...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 4, "title": "Tên kịch bản 4", "setting": "...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 5, "title": "Tên kịch bản 5", "setting": "...", "hook": "...", "actors": {num_chars} }}
                    ]
                }}
                """
                payload = ["IMAGES:"]
                for cb, cm in st.session_state["saved_reference_images"]:
                    payload.append(types.Part.from_bytes(data=cb, mime_type=cm))
                for c in char_inputs:
                    cb, cm = compress_image_bytes(c['file'], 768, 80)
                    payload.extend([f"ACTOR {c['id']}:", types.Part.from_bytes(data=cb, mime_type=cm)])
                payload.append(prompt)
                
                res = call_gemini(payload, get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, initial_angle))
                st.session_state.content_analysis = res.get("content_analysis")
                outlines = res.get("outlines", res.get("script_outlines", []))
                for o in outlines: 
                    if "hook" in o: o["hook"] = sanitize_policy_text(o["hook"])
                    o.update({"duration_instruction": "Khoảng 30 giây", "narrator_mode": narrator_mode, "character_profiles": st.session_state.character_profiles, "actors": num_chars})
                st.session_state.update({"all_scripts": outlines, "cloned_scripts": [], "expanded_scripts": [], "generated_details": {}, "active_script_id": None})
                st.toast("✅ Đã phân tích xong đầy đủ DNA!")
            except Exception as e: st.error(f"❌ Lỗi: {e}")

ca = st.session_state.content_analysis
if isinstance(ca, dict):
    st.divider()
    st.markdown("### 🔍 **Phân Tích DNA Chi Tiết Theo Mô Hình AIDA & Hero SKU**")
    with st.container(border=True):
        col_dna1, col_dna2 = st.columns(2)
        col_dna1.markdown(f"##### 🎯 **1. Chân dung Khách hàng & Hook 3s (Attention):**<br><div style='line-height: 1.8;'>{format_analysis_field(ca.get('target_audience', ''))}<br>{format_analysis_field(ca.get('pain_points', ''))}<br><b>⚡ Yếu tố Hook 3s đầu:</b> <span style='color:#d90429; font-weight:bold;'>{ca.get('hook_element', '')}</span></div>", unsafe_allow_html=True)
        col_dna2.markdown(f"##### 🔥 **2. Mã Màu Bán Chạy Nhất (Hero SKU):**<br><div style='line-height: 1.8;'><b>⭐ Mẫu ưu tiên làm video:</b> <span style='color:#d90429; font-size:16px; font-weight:bold;'>{ca.get('hero_sku_color', 'Tự động')}</span><br><b>🎨 Toàn bộ bảng màu:</b> <span style='color:#0284c7;'>{format_analysis_field(ca.get('color_palette', ''))}</span></div>", unsafe_allow_html=True)
        st.markdown(f"--- \n##### 💎 **3. Giải phẫu Sản phẩm Không Lộ Liễu (Interest & Desire):**<br><div style='line-height: 1.8;'><b>📦 Sản phẩm là gì & Điểm đặc biệt:</b> {ca.get('what_and_unique', '')}<br><b>👥 Sản phẩm dành cho ai:</b> {ca.get('target_user', '')}<br><b>🔥 Tại sao nên mua:</b> {ca.get('why_buy', '')}<br><b>📍 Dùng ở đâu & Tiện lợi:</b> {ca.get('where_and_convenience', '')}<br><b>🛠 Cách sử dụng chuẩn đời thực:</b> {ca.get('how_to_use', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"--- \n##### 🏭 **4. Vật lý, Cơ chế & Mức Giá OCR:**<br><div style='line-height: 1.8;'><b>📐 Thông số:</b> {ca.get('product_dimensions', '')}<br><b>🎨 Khóa màu chi tiết:</b> {ca.get('product_color_lock', '')}<br><b>⚙ Cơ chế hoạt động:</b> {ca.get('lid_mechanism', 'Bình thường')}</div><br><b>💰 Mức giá (OCR):</b> {ca.get('detected_prices', '')} (Làm tròn: <b>{ca.get('rounded_price_anchor', '')}</b>)", unsafe_allow_html=True)
    if ca.get('prompt_dna_lock'):
        st.markdown("##### 📌 **Visual DNA Lock:**")
        st.code(ca.get('prompt_dna_lock'), language="text")

all_sc = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
if all_sc:
    st.divider()
    comp_sc = [sc for sc in all_sc if sc["id"] in st.session_state.generated_details]
    pend_sc = [sc for sc in all_sc if sc["id"] not in st.session_state.generated_details]

    if st.session_state.active_script_id is not None:
        st.markdown("<div id='detailed-view-anchor'></div>", unsafe_allow_html=True)
        if st.button("⬅ Thu gọn danh sách kịch bản"):
            st.session_state.active_script_id = None
            st.session_state.scroll_to_top = True
            st.rerun()
            
        asc = st.session_state.generated_details.get(st.session_state.active_script_id, {})
        vp = asc.get("voice", {})
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(asc.get('title')).upper()}**")
        
        director_summary_html = asc.get('director_summary', '')
        if not director_summary_html:
            tone_txt = vp.get('tone', 'Hội thoại tự nhiên')
            outfit_txt = asc.get('outfit_vi', 'Khóa cố định trang phục và kiểu tóc')
            hero_sku_txt = ca.get('hero_sku_color', 'Mẫu mã chuẩn từ ảnh gốc') if isinstance(ca, dict) else 'Mẫu mã chuẩn từ ảnh gốc'
            director_summary_html = f"⏱ <b>Thời lượng:</b> Khoảng 30 giây (Chuẩn 4 phân cảnh AIDA) | 🎙 <b>Chỉ đạo giọng:</b> {tone_txt}<br>👨‍👩‍👧 <b>Đồng nhất diện mạo:</b> 100% nhân vật Việt Nam thuần túy, khóa kiểu tóc và trang phục đồng bộ xuyên suốt<br>🎯 <b>Sản phẩm / Đạo cụ:</b> {hero_sku_txt}"
            
        st.markdown(f"<div class='detail-header-box'>{director_summary_html}</div>", unsafe_allow_html=True)
        
        for idx, scn in enumerate(asc.get("scenes", []), 1):
            vo_text = scn.get('voiceover', '')
            actual_words = count_words(vo_text)
            comma_count = vo_text.count(',')
            speech_sec = calculate_speech_duration(vo_text)
            
            st.markdown(f"#### 📍 Phân cảnh {idx} - Giai đoạn {scn.get('aida_stage')}")
            st.markdown(f"<span class='timing-badge'>⏱ Khung phân cảnh: {scn.get('dur')} | Khớp nhịp đọc thực tế: ~{speech_sec}s ({actual_words} từ, {comma_count} dấu phẩy)</span>", unsafe_allow_html=True)
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting')}*\n\n**🎙 Đạo diễn & SFX:** *{scn.get('director')}*\n\n**💬 Thoại kịch bản:** <div class='voiceover-text'>{vo_text}</div>", unsafe_allow_html=True)
            if scn.get('img_p'): st.markdown("**🖼 Prompt Ảnh (Midjourney / Flux - Khóa 100% người Việt & hành vi thực tế):**"); st.code(img_p := scn.get('img_p'), language="text"); safe_copy_button(img_p, f"📋 Sao Chép Ảnh Cảnh {idx}")
            if scn.get('vid_p'): st.markdown("**🎥 Prompt Video (Veo 3 / Kling AI / Hedra - Khóa 1 sản phẩm & SFX):**"); st.code(vid_p := scn.get('vid_p'), language="text"); safe_copy_button(vid_p, f"📋 Sao Chép Video Cảnh {idx}")
            st.markdown("---")

    st.markdown("### 🎬 **1. Kịch Bản Đã Dựng Chi Tiết**")
    for outline in comp_sc:
        sc_id = outline["id"]
        with st.container(border=True):
            c1, c2, c3 = st.columns([2.5, 1, 1])
            c1.markdown(f"**#{sc_id}. {outline.get('title')}**")
            c1.caption(f"⚡ *{outline.get('hook')}*")
            
            is_busy = st.session_state.current_processing_id is not None
            if sc_id != st.session_state.active_script_id:
                if c2.button("👁 Xem lại", key=f"r_{sc_id}", use_container_width=True, disabled=is_busy):
                    st.session_state.active_script_id = sc_id
                    st.session_state.scroll_to_detail = True
                    st.rerun()
            
            btn_clone_ph = c3.empty()
            if btn_clone_ph.button("🚀 Nhân bản", key=f"c_{sc_id}", type="primary", use_container_width=True, disabled=is_busy):
                can_run, msg = check_usage_limit(st.session_state.current_email)
                if can_run:
                    with st.spinner("⏳ Đang nhân bản 5 biến thể..."):
                        st.session_state.cloned_scripts.extend(clone_script(sc_id))
                        st.toast("✅ Đã nhân bản 5 kịch bản mới!")
                        time.sleep(0.4); st.rerun()
                else: st.error(msg)

    st.markdown("<br>### ⏳ **2. Kịch Bản Chờ Dựng**", unsafe_allow_html=True)
    for outline in pend_sc:
        sc_id = outline["id"]
        with st.container(border=True):
            c1, c2 = st.columns([3, 1.2])
            c1.markdown(f"**#{sc_id}. {outline.get('title')}** <span class=badge-pending>CHỜ DỰNG</span>", unsafe_allow_html=True)
            c1.caption(f"⚡ *{outline.get('hook')}*")
            
            btn_detail_ph = c2.empty()
            if st.session_state.current_processing_id == sc_id:
                btn_detail_ph.markdown("<div style='background: #fffbeb; color: #d97706; border-radius: 8px; padding: 8px; text-align: center; font-size: 13px; font-weight: bold; border: 1px solid #fde68a;'>⏳ Đang dựng 4 cảnh AIDA...</div>", unsafe_allow_html=True)
            else:
                is_another_busy = (st.session_state.current_processing_id is not None)
                if btn_detail_ph.button("✨ Tạo chi tiết ngay", key=f"cr_{sc_id}", type="secondary", use_container_width=True, disabled=is_another_busy):
                    can_run, msg = check_usage_limit(st.session_state.current_email, is_detailing=True)
                    if can_run:
                        st.session_state.current_processing_id = sc_id
                        st.rerun()
                    else: st.error(msg)

    if st.session_state.current_processing_id is not None:
        target_id_to_run = st.session_state.current_processing_id
        lock_ui()
        try:
            with st.spinner(f"⏳ Đang áp dụng bộ lọc chính sách, khóa 100% người Việt và dựng kịch bản #{target_id_to_run}..."):
                create_scene_details(target_id_to_run, st.session_state.last_mode, st.session_state.last_style)
                st.session_state.active_script_id = target_id_to_run
                st.session_state.scroll_to_detail = True
                st.toast(f"✅ Đã hoàn tất dựng kịch bản #{target_id_to_run}!")
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
        finally:
            st.session_state.current_processing_id = None
            time.sleep(0.4)
            st.rerun()

    st.markdown("--- \n##### ➕ **Gọi Thêm 5 Kịch Bản Mới**")
    cg1, cg2, cg3, cg4 = st.columns([1.5, 0.8, 1.2, 1.5])
    a_opts = ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Chia sẻ", "😂 Hài hước"]
    c_ang = cg1.selectbox("🧭 Chiến lược mới:", a_opts, key=f"ea_{st.session_state.reset_key}")
    c_num = cg2.number_input("Số diễn viên:", 1, 8, num_chars, key=f"en_{st.session_state.reset_key}")
    c_dur_choice = cg3.selectbox("⏳ Thời lượng:", ["Tự động (~30s)", "Tùy chỉnh (s)"], key=f"ed_{st.session_state.reset_key}")
    c_dur_str = f"Chính xác {cg3.number_input('Số giây:', 10, 300, 60, key=f'eds_{st.session_state.reset_key}')} giây." if "Tùy" in c_dur_choice else "Khoảng 30 giây."
    c_nar = cg4.selectbox("🎙 Thuyết minh:", ["Nhân vật xuất hiện (On-camera)", "🎙 Lồng tiếng ngoài (Off-screen)"], key=f"ena_{st.session_state.reset_key}")

    e_chars = []
    for i in range(c_num):
        c_r, c_i = st.columns([2, 1])
        e_role = c_r.text_input(f"Vai trò NV {i+1} mới:", key=f"er_{i}_{st.session_state.reset_key}")
        e_file = c_i.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"ef_{i}_{st.session_state.reset_key}", label_visibility="collapsed")
        if e_file: e_chars.append({"id": i+1, "role": e_role or f"Diễn viên {i+1}", "file": e_file})

    btn_more_disabled = (st.session_state.current_processing_id is not None)
    if st.button("🚀 Gọi Thêm 5 Kịch Bản Mới", type="primary", use_container_width=True, disabled=btn_more_disabled):
        can_run, msg = check_usage_limit(st.session_state.current_email)
        if can_run:
            with st.spinner("⏳ Đang sáng tạo thêm 5 kịch bản theo mô hình AIDA..."):
                p_chars = [{"id": c["id"], "role": c["role"]} for c in e_chars] if e_chars else st.session_state.character_profiles
                new_sc = generate_more_scripts(c_ang, c_num, e_chars, c_nar, c_dur_str, p_chars)
                st.session_state.expanded_scripts.extend(new_sc)
                st.toast("✅ Đã sinh thêm 5 kịch bản mới!")
                time.sleep(0.4); st.rerun()
        else: st.error(msg)
