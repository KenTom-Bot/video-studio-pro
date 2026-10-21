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
import math
from PIL import Image
from datetime import datetime, timedelta, date

# ==============================================================================
# 1. CẤU HÌNH GIAO DIỆN & GA4
# ==============================================================================
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
        script2.innerHTML = `window.dataLayer = window.dataLayer || []; function gtag(){dataLayer.push(arguments);} gtag('js', new Date()); gtag('config', 'G-19YJP7NJ6W');`;
        window.parent.document.head.appendChild(script2);
    }
</script>
"""
components.html(ga_script, width=0, height=0)

def lock_ui():
    st.markdown("""
    <style>
        div[data-testid="stAppViewContainer"], div[data-testid="stSidebar"] { pointer-events: none !important; user-select: none !important; }
        button, div[data-testid="stButton"] button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"] {
            pointer-events: none !important; opacity: 0.35 !important; cursor: not-allowed !important; filter: grayscale(60%) !important;
        }
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
    .detail-header-box { background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%); border: 1.5px solid #bfdbfe; border-radius: 12px; padding: 14px 18px; margin-bottom: 20px; color: #1e3a8a; line-height: 1.7; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
    .voiceover-text { color: #15803d; background: #f0fdf4; padding: 12px 14px; border-radius: 8px; font-size: 15.5px; border: 1px solid #bbf7d0; display: block; width: 100%; margin-top: 4px; line-height: 1.8; white-space: pre-line; }
    .timing-badge { font-size: 13.5px; font-weight: 700; color: #1e40af; background: #dbeafe; padding: 4px 10px; border-radius: 6px; border: 1px solid #bfdbfe; display: inline-block; margin-bottom: 6px; }
    div[data-testid="stFileUploader"] section { padding: 4px; min-height: 2rem; border: 1.5px dashed #cbd5e1 !important; background-color: #f8fafc !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div { background-color: #f8fafc !important; border: 1.5px solid #cbd5e1 !important; border-radius: 8px !important; }
    .dna-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 20px; margin-bottom: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.02); height: 100%; }
    .dna-card-title { font-size: 15.5px; font-weight: 800; color: #1e3a8a; margin-bottom: 12px; padding-bottom: 6px; border-bottom: 1.5px solid #f1f5f9; display: flex; align-items: center; gap: 6px; }
    .dna-row { margin-bottom: 9px; line-height: 1.65; }
    .dna-label { font-weight: 700; color: #0f172a; font-size: 14px; display: inline-block; margin-right: 5px; }
    .dna-text { font-weight: 400 !important; color: #334155 !important; font-size: 14px !important; line-height: 1.65 !important; }
    .dna-bullet { margin-left: 10px; margin-top: 3px; color: #334155; font-weight: 400; font-size: 14px; line-height: 1.65; }
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

def calculate_speech_duration(text: str, is_tiktok_shop: bool = True) -> float:
    words = count_words(text)
    commas = text.count(',') + text.count(';')
    periods = text.count('.') + text.count('!') + text.count('?')
    rate = 4.8 if is_tiktok_shop else 4.0
    comma_pause = 0.08 if is_tiktok_shop else 0.12
    period_pause = 0.12 if is_tiktok_shop else 0.20
    return round((words / rate) + (commas * comma_pause) + (periods * period_pause), 1)

def is_valid_phone(phone):
    phone = phone.strip()
    return phone.isdigit() and phone.startswith('0') and 9 <= len(phone) <= 11

def compress_image_bytes(uploaded_file, max_dimension=768, quality=75):
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        out_buffer = io.BytesIO()
        img.save(out_buffer, format="JPEG", quality=quality, optimize=True)
        return out_buffer.getvalue(), "image/jpeg"
    except Exception:
        return uploaded_file.getvalue(), (uploaded_file.type or "image/jpeg")

def clean_html(raw_html: str) -> str:
    if not raw_html: return ""
    return "\n".join(line.strip() for line in raw_html.strip().splitlines() if line.strip())

# ==============================================================================
# THUẬT TOÁN PHIÊN ÂM TIỀN TỆ TIẾNG VIỆT & TÂM LÝ HỌC NEO GIÁ
# ==============================================================================
def number_to_vietnamese_words(n: int) -> str:
    if n == 0: return "không đồng"
    digits = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    def read_block_3(num_str, is_highest=False):
        num_str = num_str.zfill(3)
        h, t, u = int(num_str[0]), int(num_str[1]), int(num_str[2])
        res = []
        if not is_highest or h > 0: res.append(digits[h] + " trăm")
        if t == 0 and u == 0: pass
        elif t == 0 and u != 0:
            if not is_highest or h > 0: res.append("linh " + digits[u])
            else: res.append(digits[u])
        elif t == 1:
            res.append("mười")
            if u == 1: res.append("một")
            elif u == 4: res.append("bốn")
            elif u == 5: res.append("lăm")
            elif u != 0: res.append(digits[u])
        else:
            res.append(digits[t] + " mươi")
            if u == 1: res.append("mốt")
            elif u == 4: res.append("bốn")
            elif u == 5: res.append("lăm")
            elif u != 0: res.append(digits[u])
        return " ".join(res)

    s = str(abs(n))
    groups = []
    while s:
        groups.append(s[-3:])
        s = s[:-3]
    units = ["", "nghìn", "triệu", "tỷ"]
    result_parts = []
    for i in range(len(groups) - 1, -1, -1):
        val = int(groups[i])
        if val > 0:
            part = read_block_3(groups[i], is_highest=(i == len(groups) - 1))
            if units[i]: part += " " + units[i]
            result_parts.append(part)
    text = " ".join(result_parts).strip()
    return re.sub(r'\s+', ' ', text).strip() + " đồng"

def extract_and_convert_prices_in_text(raw_text: str) -> str:
    if not raw_text: return ""
    def replace_k(match):
        return number_to_vietnamese_words(int(match.group(1)) * 1000).replace(" đồng", "")
    text = re.sub(r'\b(\d{1,4})\s*[kK]\b', replace_k, raw_text)
    def replace_num(match):
        num_str = match.group(1).replace('.', '').replace(',', '')
        try:
            val = int(num_str)
            if val >= 1000: return number_to_vietnamese_words(val).replace(" đồng", "")
        except: pass
        return match.group(0)
    return re.sub(r'(\b\d{1,3}(?:[.,]\d{3})+\b)', replace_num, text)

def convert_to_soft_price_range(price_text: str, is_orig: bool = False, exact_raw_str: str = "") -> str:
    combined = f"{exact_raw_str} {price_text}".lower().strip()
    num_matches = [int(n.replace('.', '').replace(',', '')) for n in re.findall(r'\b\d{1,3}(?:[.,]\d{3})+\b', combined)]
    if num_matches:
        val = num_matches[0]
        if is_orig:
            if 100000 <= val <= 125000: return "gần một trăm hai mươi nghìn"
            ceil_ten = math.ceil(val / 10000) * 10000
            return f"gần {number_to_vietnamese_words(ceil_ten).replace(' đồng', '')}"
        else:
            if val < 50000: return "mấy chục nghìn"
            floor_ten = math.floor(val / 10000) * 10000
            return f"hơn {number_to_vietnamese_words(floor_ten).replace(' đồng', '')}"
    p_lower = re.sub(r'^(?:khoảng\s+|hơn\s+|tầm\s+|gần\s+)+', '', str(price_text).lower().strip()).strip()
    return f"gần {p_lower}" if is_orig else f"hơn {p_lower}"

# ==============================================================================
# HÀM XÁC ĐỊNH NHÂN KHẨU HỌC KOC: ƯU TIÊN USER > AI TỰ ĐỘNG
# ==============================================================================
def get_demographics_description(char_profiles, ai_koc_persona_en=""):
    # Kiểm tra xem người dùng có nhập vai trò cụ thể không
    user_roles = [p.get("role", "").strip() for p in (char_profiles or []) if p.get("role", "").strip()]
    
    # TRƯỜNG HỢP 1: NGƯỜI DÙNG KHÔNG NHẬP GÌ -> SỬ DỤNG PHÂN TÍCH TỰ ĐỘNG CỦA AI
    if not user_roles:
        if ai_koc_persona_en and len(ai_koc_persona_en.strip()) > 8:
            gender = "male" if any(k in ai_koc_persona_en.lower() for k in ["man", "father", "male", "boy", "gentleman"]) else "female"
            return gender, ai_koc_persona_en.strip().capitalize()
        return "female", "A 28-year-old native Vietnamese woman"
    
    # TRƯỜNG HỢP 2: NGƯỜI DÙNG ĐÃ NHẬP VAI TRÒ -> LẤY NGƯỜI DÙNG LÀM ƯU TIÊN TUYỆT ĐỐI
    parts = []
    primary_gender = "female"
    for idx, p in enumerate(char_profiles):
        role_lower = str(p.get("role", "")).lower().strip()
        if not role_lower:
            desc = "a native Vietnamese person"
        elif any(k in role_lower for k in ["bố", "ba", "chồng", "bác trai", "nam", "anh", "thanh niên"]):
            desc = f"a native Vietnamese young man ({p['role']})"
            if idx == 0: primary_gender = "male"
        elif any(k in role_lower for k in ["ông", "già", "bác già", "nông dân", "làm vườn"]):
            desc = f"a native Vietnamese mature gentleman ({p['role']})"
            if idx == 0: primary_gender = "male"
        elif any(k in role_lower for k in ["bà", "bà nội", "bà ngoại"]):
            desc = f"a native Vietnamese elderly woman ({p['role']})"
            if idx == 0: primary_gender = "female"
        elif any(k in role_lower for k in ["bé trai", "con trai"]):
            desc = f"a cute native Vietnamese boy ({p['role']})"
            if idx == 0: primary_gender = "male"
        elif any(k in role_lower for k in ["bé gái", "con gái", "bé"]):
            desc = f"a cute native Vietnamese girl ({p['role']})"
            if idx == 0: primary_gender = "female"
        else:
            desc = f"a native Vietnamese woman ({p['role']})"
            if idx == 0: primary_gender = "female"
        parts.append(desc)
    return primary_gender, (parts[0].capitalize() if len(parts) == 1 else " and ".join(parts).capitalize())

def sanitize_third_party_ip(text: str) -> str:
    if not text: return ""
    cleaned = text
    for p in [r'\btiktok\s*(?:shop)?\b', r'\bshopee\b', r'\blazada\b', r'\bfacebook\b', r'\binstagram\b', r'\byoutube\b']:
        cleaned = re.sub(p, 'commercial marketplace', cleaned, flags=re.IGNORECASE)
    return re.sub(r'\b(?:osaka|panasonic|philips|lock&lock|emoon|nike|apple)\b', 'custom premium brand', cleaned, flags=re.IGNORECASE)

POLICY_REPLACEMENTS = {
    r'\ban\s*toàn\s*tuyệt\s*đối\b': 'cực kỳ an toàn', r'\byên\s*tâm\s*tuyệt\s*đối\b': 'cực kỳ yên tâm',
    r'\btuyệt\s*đối\b': 'rất', r'\bhoàn\s*toàn\b': 'thực sự', r'\b100\s*%\b': 'rất nhiều',
    r'\btrợ\s*giá\b': 'giảm giá sâu có hạn', r'\bphiên\s*live\b': 'đợt ưu đãi này', r'\btrên\s*live\b': 'đợt này'
}

SOUTHERN_TO_HANOI = {
    r'\báp\s*mã\b': 'nay giảm', r'\báp\s*voucher\b': 'nay giảm', r'\bngàn\b': 'nghìn',
    r'\bchiên\b': 'rán', r'\bxài\b': 'dùng', r'\btui\b': 'tôi', r'\bnghen\b': 'nhé', r'\bnha\b': 'nhé',
    r'\bbữa\s*nay\b': 'hôm nay', r'\bmấy\s*bà\b': 'các chị em', r'\bmấy\s*chế\b': 'các chị em'
}

def clean_and_normalize_voiceover(text: str) -> str:
    if not text: return ""
    cleaned = text
    for pattern, rep in SOUTHERN_TO_HANOI.items(): cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    for pattern, rep in POLICY_REPLACEMENTS.items(): cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    cleaned = extract_and_convert_prices_in_text(cleaned)
    for pattern, rep in [(r'\b(?:tư|tứ)\s+mươi\b', 'bốn mươi'), (r'\bmười\s+(?:tư|tứ)\b', 'mười bốn'), (r'\b1\s*trăm\b', 'một trăm')]:
        cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    return cleaned

def format_product_name_bold(text: str) -> str:
    clean = clean_and_normalize_voiceover(str(text or "").strip())
    if ":" in clean:
        parts = clean.split(":", 1)
        return f"<b style='color:#0f172a; font-weight:800; font-size:15px;'>{parts[0].strip()}</b>: {parts[1].strip()}"
    return f"<b style='color:#0f172a; font-weight:800; font-size:15px;'>{clean}</b>"

def format_ocr_prices(ca_data: dict) -> str:
    if not isinstance(ca_data, dict): return "<span style='color:#dc2626; font-weight:700;'>Chưa xác định</span>"
    exact_orig = ca_data.get('exact_original_price_ocr', '')
    exact_sale = ca_data.get('exact_sale_price_ocr', '')
    if exact_orig and exact_sale:
        return f"<b style='color:#475569;'>Giá gốc:</b> <span style='color:#64748b; text-decoration:line-through; font-weight:700;'>{exact_orig}</span> &nbsp;|&nbsp; <b style='color:#dc2626;'>Giá giảm:</b> <span style='color:#dc2626; font-weight:800;'>{exact_sale}</span>"
    return "<span style='color:#dc2626; font-weight:700;'>Chưa xác định</span>"

def sanitize_veo3_prompt(prompt_text: str) -> str:
    if not prompt_text: return ""
    p = re.sub(r'\bgesturing\s+(?:warmly\s+)?(?:toward\s+)?corner\b', 'sharing recommendations with an open-palm hand gesture', prompt_text, flags=re.IGNORECASE)
    return sanitize_third_party_ip(p)

def clean_analysis_text(text) -> str:
    pattern = r'^(?:SẢN PHẨM LÀ GÌ|MỤC ĐÍCH|ĐỐI TƯỢNG|LÝ DO MUA)\s*:\s*'
    return clean_and_normalize_voiceover(re.sub(pattern, '', str(text or '').strip(), flags=re.IGNORECASE).strip())

# ==============================================================================
# QUẢN TRỊ TÀI KHOẢN & DỰ ÁN
# ==============================================================================
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
                "last_generation_date": "", "active_session_id": ""
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
    if datetime.now() > datetime.strptime(acc.get("expires_at", "2099-12-31"), "%Y-%m-%d"): return False, "Tài khoản của bạn đã hết hạn sử dụng."
    plan = acc.get("plan_type", "Trial")
    if plan == "VIP": return True, ""
    limit = {"Advanced": 20, "Basic": 10, "Trial": 3}.get(plan, 3)
    today = datetime.now().strftime("%Y-%m-%d")
    if acc.get("last_generation_date") != today:
        acc["daily_usage_count"] = 0
        acc["last_generation_date"] = today
    if is_detailing:
        if acc.get("daily_usage_count", 0) >= limit: return False, f"Hết lượt tạo ({limit}/{limit}) hôm nay! Vui lòng nâng cấp gói."
        acc["daily_usage_count"] += 1
        save_single_account(email, acc)
    return True, ""

def safe_copy_button(text_to_copy: str, button_label: str = "📋 Sao Chép Prompt", custom_color: str = "#16a34a"):
    b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    html_id = f"btn_{int(time.time()*10000)}_{len(text_to_copy)}"
    components.html(f"""
    <button id="{html_id}" style="background:{custom_color}; color:white; border:none; padding:7px 14px; font-size:12.5px; font-weight:700; border-radius:6px; cursor:pointer; width:100%;">{button_label}</button>
    <script>
    document.getElementById("{html_id}").addEventListener("click", function() {{
        const text = decodeURIComponent(escape(atob("{b64}")));
        navigator.clipboard.writeText(text).then(() => {{
            document.getElementById("{html_id}").innerText = "✅ Đã sao chép!";
            setTimeout(() => {{ document.getElementById("{html_id}").innerText = "{button_label}"; }}, 2000);
        }});
    }});
    </script>
    """, height=42)

def save_project_to_db(email, title, payload_data, project_id=None):
    if not supabase: return False, "Chưa kết nối cơ sở dữ liệu."
    try:
        clean_content = json.loads(json.dumps(payload_data, default=str))
        if project_id:
            res = supabase.table("saved_projects").update({"project_title": title, "script_content": clean_content}).eq("id", project_id).execute()
            if res.data: return True, "Đã cập nhật dự án thành công!"
        res = supabase.table("saved_projects").insert({"user_email": email, "project_title": title, "script_content": clean_content}).execute()
        if res.data:
            st.session_state.current_project_id = res.data[0]['id']
            return True, "Đã lưu thành dự án mới thành công!"
        return False, "Không thể lưu dữ liệu dự án."
    except Exception as e: return False, str(e)

# ==============================================================================
# KHỞI TẠO STATE
# ==============================================================================
if "session_id" not in st.session_state: st.session_state.session_id = str(uuid.uuid4())
for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", load_licensed_accounts()),
    ("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []),
    ("generated_details", {}), ("content_analysis", None), ("active_script_id", None),
    ("current_input_context", ""), ("current_product_data_saved", None), ("current_product_data", None),
    ("reset_key", 0), ("scroll_to_top", False), ("scroll_to_detail", False),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"),
    ("last_mode", "🛒 TikTok Shop & Bán Hàng"), ("last_style", "Điện Ảnh Chân Thực"), ("last_narrator", "On-camera"),
    ("last_presentation_format", "🌟 1. Bán Ước Mơ & Thành Quả Xã Hội (Outcome-First & Social Proof)"),
    ("character_profiles", []), ("current_project_id", None), ("saved_reference_images", []),
    ("show_all_projects", False), ("show_all_admin_accounts", False),
    ("current_processing_id", None), ("current_cloning_id", None)
]:
    if key not in st.session_state: st.session_state[key] = default_val

is_system_busy = (st.session_state.get("current_processing_id") is not None or st.session_state.get("current_cloning_id") is not None)
if is_system_busy: lock_ui()

def repair_and_parse_json(text_content: str):
    cleaned = re.sub(r'```(?:json)?', '', str(text_content or '')).strip()
    try: return json.loads(cleaned, strict=False)
    except: pass
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    if match:
        try: return json.loads(match.group(0), strict=False)
        except: pass
    raise Exception("Lỗi cấu trúc phản hồi từ AI. Vui lòng bấm tạo lại.")

# SỬ DỤNG DANH SÁCH MODEL ỔN ĐỊNH ĐỂ TRIỆT TIÊU 404
def call_gemini(contents, sys_inst="Bạn là AI hỗ trợ JSON.", max_tokens=6500):
    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.5-flash"]
    last_err = None
    for model_name in models_to_try:
        for attempt in range(3):
            try:
                res = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_inst,
                        response_mime_type="application/json",
                        temperature=0.7,
                        max_output_tokens=max_tokens
                    )
                )
                return repair_and_parse_json(res.text)
            except Exception as e:
                last_err = e
                time.sleep((attempt + 1) * 2.0)
    raise Exception(f"Google API tạm thời gián đoạn. Vui lòng thử lại sau vài giây! (Chi tiết: {last_err})")

def build_voice_direction(mode, num_chars, character_profiles):
    is_tiktok_shop = ("Viral" not in mode)
    speed_txt = "tốc độ dồn dập (4.8 - 5.2 từ/s), dứt khoát" if is_tiktok_shop else "tốc độ tự nhiên, truyền cảm (3.8 - 4.2 từ/s)"
    return f"100% Giọng Hà Nội chuẩn bản địa, phát âm tròn vành rõ chữ, số 4 đọc là 'bốn', {speed_txt}. Khẩu ngữ đời thường, tự nhiên."

def generate_char_rules_string(profiles):
    return "100% người Việt Nam bản địa, nhân vật hư cấu đời thường, tóc đen tuyền tự nhiên, giữ nguyên duy nhất 1 khuôn mặt và 1 kiểu tóc suốt các cảnh."

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, angle, custom_note="", presentation_format=""):
    is_viral = ("Viral" in mode)
    viral_dir = "VIRAL & XÂY KÊNH: Kéo Follow, chia sẻ mẹo thật, không bán hàng, không báo giá." if is_viral else "TIKTOK SHOP: Kịch bản 1 Nỗi đau, Kịch bản 2 Bán ước mơ, Kịch bản 3 Đập tan định kiến, Kịch bản 4 Trải nghiệm đời sống, Kịch bản 5 Flash Sale kích cầu khoảng giá."
    return f"""
    TỔNG ĐẠO DIỄN VIDEO TRIỆU VIEW. PHONG CÁCH: {style}.
    {viral_dir}
    Ghi chú ưu tiên: {custom_note}
    QUY TẮC CỐT LÕI:
    - BẮT BUỘC TỰ ĐỘNG PHÂN TÍCH CHÂN DUNG KOC PHÙ HỢP NHẤT VỚI SẢN PHẨM (Ví dụ: giàn cây/thổi lá -> nam/bác 35-50t; đồ bếp -> mẹ trẻ/nội trợ 28-35t; mỹ phẩm -> nữ 22-26t; công nghệ -> nam 24-28t).
    - Nếu người dùng đã tự nhập vai trò diễn viên thì lấy thông tin người dùng làm ưu tiên cao nhất!
    - Mỗi kịch bản chọn 1 BỐI CẢNH ĐỜI THỰC KHÁC NHAU.
    - CÂU THOẠI: 100% Giọng Hà Nội chuẩn, dùng 'nghìn', số 4 đọc 'bốn', viết rõ 'một trăm'. CẤM 'ngàn', 'trợ giá'.
    - Lời thoại bắt đầu ngay từ 0.00s.
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction, num_chars, character_profiles, custom_note="", presentation_format="", self_pronoun="em", audience_pronoun="các chị em", setting_archetype="", is_fixed_location=True, is_flash_sale=False):
    outro_rule = f"""
    CÔNG THỨC KẾT BÀI SOFT-SELL TỰ NHIÊN (TRIỆT TIÊU CẢM GIÁC BÁN HÀNG):
    - TUYỆT ĐỐI CẤM: Không báo giá tiền, không mã giảm giá, không voucher, không giục giã mua hàng!
    - Câu kết Cảnh cuối là lời khuyên chân thành: '{audience_pronoun.capitalize()} nào thích [kết quả đẹp/tiện lợi] thì đừng bỏ qua em này nhé, bấm góc trái tham khảo thử nha!'
    """ if not is_flash_sale else f"""
    CÔNG THỨC CHỐT DEAL FLASH SALE: Báo khoảng giá an toàn: 'Bình thường khoảng [giá gốc làm tròn lên], nay giảm sâu chỉ còn khoảng [giá sale làm tròn xuống] thôi... {audience_pronoun} bấm góc trái kiểm tra tài khoản mình xem nhé!'
    """

    return f"""
    TỔNG ĐẠO DIỄN VIDEO THƯƠNG MẠI 100% VIRAL BLUEPRINT. PHONG CÁCH: {style}.
    {outro_rule}
    Ghi chú riêng: {custom_note}

    🛑 5 NGUYÊN TẮC BẮT BUỘC ĐỂ ĐẠT 100% NHƯ VIDEO MẪU:
    1. PHÂN CẢNH ĐỘNG (DYNAMIC 4-6 SCENES): Tự động chọn 4, 5 hoặc 6 phân cảnh phù hợp với sản phẩm để mạch truyện tự nhiên, đủ các nấc: Hook -> Soi ngàm -> Hành động vật lý -> Thành quả mãn nhãn -> Ứng dụng đời sống -> Cầm sản phẩm khuyên dùng.
    2. KHÓA 1 NGUYÊN LIỆU THỬ NGHIỆM DUY NHẤT: Cả kịch bản chỉ theo sát 1 nguyên liệu (ví dụ thịt heo làm nem thì chỉ thịt heo, cấm đổi màu cối sang xoài hay đá).
    3. 1 SHOT = 1 VI HÀNH ĐỘNG (MICRO-ACTION): Mỗi cảnh chỉ làm đúng 1 hành động dứt khoát (Cảnh 2: gõ ngàm khóa; Cảnh 3: dao cuộn; Cảnh 4: thìa múc thịt dẻo).
    4. KHÓA MẶT BÀN & BỐI CẢNH CỐ ĐỊNH: Bàn bếp đá cẩm thạch trắng, cấm tự ý đổi sang bàn gỗ; đồ ngoài trời đặt trên sàn bê tông, cấm kê bàn ăn giữa sân.
    5. KHỬ NHẠC NỀN & KHÓI GIẢ: 100% âm thanh Foley tự nhiên + Voiceover từ 0.00s. Luồng khí thổi phải trong suốt vô hình, không khói trắng.
    """

def create_scene_details(target_id, mode, style):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if str(sc.get("id")) == str(target_id)), None)
    if not outline: raise Exception("Không tìm thấy kịch bản.")

    char_profiles = outline.get("character_profiles", st.session_state.get("character_profiles", []))
    char_rules = generate_char_rules_string(char_profiles)
    num_chars = outline.get("actors", 1)
    current_active_mode = mode or st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    is_tiktok_shop = ("Viral" not in current_active_mode)

    fixed_title = outline.get('title', 'Kịch bản chi tiết')
    fixed_hook = clean_and_normalize_voiceover(outline.get('hook', ''))
    fixed_setting_base = outline.get('setting', 'Không gian thực tế phù hợp')
    user_custom_note = outline.get("custom_note") or st.session_state.get("current_input_context", "").strip()
    presentation_format = outline.get("presentation_format") or st.session_state.get("last_presentation_format", "")

    is_flash_sale = any(k in f"{fixed_title} {user_custom_note} {presentation_format}".lower() for k in ["flash sale", "deal", "giá hời", "kịch bản 5"])
    dna = st.session_state.get("content_analysis") or {}

    # LẤY CHÂN DUNG KOC PHÙ HỢP TỪ AI PHÂN TÍCH (NẾU USER KHÔNG NHẬP)
    ai_koc_data = dna.get("koc_demographic_analysis", {})
    ai_persona_en = ai_koc_data.get("persona_en", "") if isinstance(ai_koc_data, dict) else ""
    detected_gender, detected_demographic_en = get_demographics_description(char_profiles, ai_persona_en)

    raw_orig = dna.get("original_price_spoken", "ba trăm năm mươi nghìn")
    raw_sale = dna.get("sale_price_spoken", "hai trăm chín mươi nghìn")
    soft_orig = convert_to_soft_price_range(raw_orig, is_orig=True)
    soft_sale = convert_to_soft_price_range(raw_sale, is_orig=False)

    self_pronoun = dna.get("self_pronoun", "em")
    audience_pronoun = dna.get("audience_pronoun", "các chị em")
    hero_color = dna.get("hero_sku_color", "chuẩn ảnh")
    raw_prod = sanitize_third_party_ip(dna.get("what_and_unique", "sản phẩm"))
    clean_prod = f"{hero_color} {raw_prod}".strip()

    if any(k in fixed_setting_base.lower() for k in ["sân", "vườn", "ngoài trời", "thổi lá", "cây"]):
        locked_setting = "clean concrete patio yard with tidy garden background"
        wardrobe = "rugged olive-green polo shirt, durable dark cargo work trousers, outdoor sneakers"
    elif any(k in fixed_setting_base.lower() for k in ["bếp", "kitchen", "nấu", "xay", "thịt", "nồi"]):
        locked_setting = "bright modern kitchen behind a clean white marble countertop"
        wardrobe = "cream-white casual t-shirt, beige linen apron, comfortable trousers, indoor slippers"
    else:
        locked_setting = "tidy modern living space"
        wardrobe = "clean casual lifestyle attire with comfortable footwear"

    prompt_text = f"""
    SẢN PHẨM: {clean_prod} | TIÊU ĐỀ: '{fixed_title}' | BỐI CẢNH: {locked_setting}
    TRANG PHỤC KHÓA: {wardrobe}
    DIỄN VIÊN / KOC: {detected_demographic_en}
    ĐẠI TỪ: '{self_pronoun}' - '{audience_pronoun}'
    ĐỊNH HƯỚNG CHỐT: {'BÁO KHOẢNG GIÁ FLASH SALE' if is_flash_sale else 'SOFT-SELL TỰ NHIÊN, CẤM NHẮC GIÁ'}
    YÊU CẦU ĐẶC BIỆT: {user_custom_note}

    TỰ ĐỘNG XÁC ĐỊNH SỐ PHÂN CẢNH TỐI ƯU (4, 5 HOẶC 6 CẢNH) ĐỂ NỘI DUNG MƯỢT MÀ VÀ ĐỦ NẤC CHUYỂN BIẾN.
    TRẢ VỀ JSON HỢP LỆ VỚI KHÓA "scenes" CHỨA DANH SÁCH CÁC PHÂN CẢNH, MỖI CẢNH CÓ: scene (số), aida_stage, setting, setting_en, camera_shot, action_en, sfx, director, voiceover.
    """
    sys_inst = get_sys_inst_details(current_active_mode, style, "On-camera", char_rules, "10s", num_chars, char_profiles, user_custom_note, presentation_format, self_pronoun, audience_pronoun, fixed_setting_base, True, is_flash_sale)
    res = call_gemini([prompt_text], sys_inst)
    if not res:
        raise Exception("AI không phản hồi hoặc trả về dữ liệu rỗng. Vui lòng bấm tạo lại.")
    
    # Tự động chuẩn hóa nếu AI trả về trực tiếp danh sách [...]
    if isinstance(res, list):
        scenes = res
        res = {"title": fixed_title, "scenes": scenes}
    elif isinstance(res, dict):
        scenes = res.get("scenes") or res.get("script") or []
    else:
        scenes = []

    if not scenes:
        raise Exception("Không trích xuất được danh sách phân cảnh từ AI. Vui lòng thử lại.")
    num_scenes = len(scenes)
    total_sec = 0.0

    neg_prompt = "background music, bmg, soundtrack, white smoke, steam, fog, changing food type, morphing ingredients, wooden table changing to marble, dropping product, text, watermark, blurry"

    for idx, scn in enumerate(scenes, 1):
        scn["scene"] = idx
        vo = clean_and_normalize_voiceover(scn.get("voiceover", ""))
        scn["voiceover"] = vo
        speech_sec = calculate_speech_duration(vo, is_tiktok_shop)
        dur = min(10, max(4, math.ceil(speech_sec + 1.2)))
        scn["dur"] = f"{dur}s"
        scn["actual_speech_sec"] = speech_sec
        total_sec += dur

        shot = scn.get("camera_shot", "Vertical 9:16 eye-level medium shot")
        act = scn.get("action_en", "operating product with steady hands")
        sfx = scn.get("sfx", "Natural Foley sound")
        chaining_txt = f"Continuing seamlessly from previous scene angle on the same surface: " if idx > 1 else ""

        if idx == num_scenes and not is_flash_sale:
            act = f"First, holding {clean_prod} firmly in both hands facing camera; then smiling warmly to share natural recommendation"

        scn["img_p"] = f"{shot}, commercial photography, {locked_setting}, {detected_demographic_en}, wearing {wardrobe}, {act}, featuring {clean_prod}, 8k resolution, natural daylight --ar 9:16 --style raw --v 6.1"
        scn["vid_p"] = f"{shot}, live-action. {chaining_txt}Setting: {locked_setting}. Subject: {detected_demographic_en} in {wardrobe}. Action: {act}. Visibly speaks dialogue once with lip-sync from 0.00s, then closes mouth smiling warmly. Spoken in native Northern Vietnamese Hanoi accent: \"{vo}\". Strictly natural Foley SFX: [{sfx}], zero background music, no BGM. Pure camera footage, no text."
        scn["vid_neg"] = neg_prompt

    res["total_dur"] = f"Khoảng {int(total_sec)} giây ({num_scenes} phân cảnh)"
    price_badge = f"💰 Khoảng giá: Bình thường khoảng {soft_orig}, nay giảm khoảng {soft_sale}" if is_flash_sale else "🌿 Lời khuyên Soft-sell tự nhiên (Không nhắc giá tiền)"
    res["director_summary"] = f"⏱ <b>Thời lượng:</b> Khoảng {int(total_sec)}s ({num_scenes} phân cảnh tự động) | 🎬 <b>Hình thức:</b> {presentation_format}<br>👤 <b>Chân dung KOC:</b> {detected_demographic_en}<br>👗 <b>Trang phục & Bối cảnh:</b> {wardrobe} tại {locked_setting}<br>🔇 <b>Âm thanh:</b> Thuần Foley & Thoại trực tiếp (Zero BGM) | {price_badge}"

    st.session_state.generated_details[int(target_id)] = res
    st.session_state.generated_details[str(target_id)] = res

def clone_script(script_id):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    style = st.session_state.get("last_style", "Điện Ảnh Chân Thực")
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if str(sc.get("id")) == str(script_id)), None)
    if not target: return []
    cur_len = len(all_combined)
    prompt = f"Nhân bản 5 biến thể kịch bản thoại bám sát kịch bản #{script_id}: '{target.get('title')}', giữ nguyên đòn bẩy tâm lý. Trả về JSON có khóa 'outlines' danh sách gồm title, setting, hook."
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, "On-camera", "", 1, "Nhân bản"))
    return [{
        "id": cur_len + idx + 1, "title": cl.get("title", f"Biến thể #{cur_len + idx + 1}"),
        "setting": cl.get("setting", "Bối cảnh sinh hoạt"), "hook": clean_and_normalize_voiceover(cl.get("hook", "")),
        "actors": target.get("actors", 1), "character_profiles": target.get("character_profiles", []),
        "presentation_format": target.get("presentation_format", "")
    } for idx, cl in enumerate(res.get("outlines", []))]

def generate_more_scripts(angle, num_chars, extra_char_inputs, narrator_mode_more, duration_inst, char_profiles, extra_note="", presentation_format=""):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    style = st.session_state.get("last_style", "Điện Ảnh Chân Thực")
    cur_len = len(st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts)
    prompt = f"Tạo 5 kịch bản góc độ '{angle}', ghi chú: '{extra_note}'. Trả về JSON có khóa 'outlines' gồm title, setting, hook."
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, "On-camera", "", num_chars, angle, extra_note, presentation_format))
    return [{
        "id": cur_len + idx + 1, "title": sc.get("title", f"Kịch bản #{cur_len + idx + 1}"),
        "setting": sc.get("setting", "Bối cảnh đời thực"), "hook": clean_and_normalize_voiceover(sc.get("hook", "")),
        "actors": num_chars, "character_profiles": char_profiles, "presentation_format": presentation_format
    } for idx, sc in enumerate(res.get("outlines", []))]

# ==============================================================================
# THANH BÊN (SIDEBAR) & QUẢN TRỊ ADMIN TOÀN NĂNG
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        tabs = st.tabs(["🔐 Đăng Nhập", "🚀 Đăng Ký"])
        with tabs[0]:
            with st.form("login_form", border=False):
                email_input = st.text_input("Email:", key="f_login_email")
                pass_input = st.text_input("Mật khẩu:", type="password", key="f_login_pass")
                if st.form_submit_button("🔑 Đăng Nhập", type="primary", use_container_width=True):
                    email_c, pass_c = email_input.strip(), pass_input.strip()
                    if email_c in st.session_state.licensed_accounts and st.session_state.licensed_accounts[email_c].get("password") == pass_c:
                        st.session_state.licensed_accounts[email_c]["active_session_id"] = st.session_state.session_id
                        save_single_account(email_c, st.session_state.licensed_accounts[email_c])
                        st.session_state.is_logged_in = True
                        st.session_state.current_email = email_c
                        st.rerun()
                    else: st.error("❌ Email hoặc mật khẩu không đúng!")
            with st.expander("❓ Quên mật khẩu?"):
                st.info("💡 Liên hệ Hotline / Zalo Admin: **0869 628 316** để được cấp lại mật khẩu ngay lập tức.")
        with tabs[1]:
            with st.form("register_form", border=False):
                r_email = st.text_input("Email đăng ký:")
                r_phone = st.text_input("Số điện thoại:")
                r_pass = st.text_input("Mật khẩu mới:", type="password")
                if st.form_submit_button("🚀 Đăng Ký", type="secondary", use_container_width=True):
                    if r_email.strip() and r_phone.strip() and r_pass.strip() and is_valid_phone(r_phone):
                        exp = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[r_email.strip()] = {
                            "roles": ALL_MODULES, "phone": r_phone.strip(), "password": r_pass.strip(),
                            "expires_at": exp, "plan_type": "Trial", "daily_usage_count": 0,
                            "last_generation_date": "", "active_session_id": ""
                        }
                        save_single_account(r_email.strip(), st.session_state.licensed_accounts[r_email.strip()])
                        st.session_state.is_logged_in = True
                        st.session_state.current_email = r_email.strip()
                        st.rerun()
                    else: st.error("⚠️ Thông tin đăng ký không hợp lệ hoặc số điện thoại sai định dạng.")
    else:
        st.markdown("### 🗂 DỰ ÁN")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True, disabled=is_system_busy):
            st.session_state.reset_key += 1
            st.session_state.update({
                "all_scripts": [], "cloned_scripts": [], "expanded_scripts": [],
                "generated_details": {}, "content_analysis": None, "active_script_id": None,
                "current_input_context": "", "current_product_data_saved": None, "current_product_data": None,
                "current_project_id": None, "saved_reference_images": []
            })
            st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
            st.rerun()

        st.session_state.active_project_title = st.text_input("Tên dự án hiện tại:", value=st.session_state.active_project_title)
        c_s1, c_s2 = st.columns(2)
        if c_s1.button("💾 Lưu Dự Án", use_container_width=True, disabled=is_system_busy):
            payload = {k: st.session_state[k] for k in ["content_analysis", "all_scripts", "cloned_scripts", "expanded_scripts", "generated_details", "character_profiles", "current_input_context"]}
            succ, msg = save_project_to_db(st.session_state.current_email, st.session_state.active_project_title, payload, st.session_state.current_project_id)
            if succ: st.toast(f"✅ {msg}")
            else: st.error(msg)
        if c_s2.button("📑 Lưu Bản Mới", use_container_width=True, disabled=is_system_busy, help="Lưu dữ liệu hiện tại thành một dự án mới độc lập hoàn toàn"):
            payload = {k: st.session_state[k] for k in ["content_analysis", "all_scripts", "cloned_scripts", "expanded_scripts", "generated_details", "character_profiles", "current_input_context"]}
            succ, msg = save_project_to_db(st.session_state.current_email, f"{st.session_state.active_project_title} (Bản sao)", payload, project_id=None)
            if succ:
                st.session_state.active_project_title = f"{st.session_state.active_project_title} (Bản sao)"
                st.toast("✅ Đã lưu thành dự án bản sao mới!"); time.sleep(0.3); st.rerun()
            else: st.error(msg)

        st.markdown("---")
        st.markdown("### 📂 KHO DỰ ÁN")
        is_admin_user = (st.session_state.current_email == ADMIN_EMAIL)
        all_projects = []
        if supabase:
            try:
                res = supabase.table("saved_projects").select("*").order("created_at", desc=True).execute() if is_admin_user else supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
                all_projects = res.data or []
            except: pass

        if is_admin_user and all_projects:
            creator_emails = sorted(list(set(p.get("user_email", "") for p in all_projects if p.get("user_email"))))
            sel_creator = st.selectbox("👤 Lọc theo thành viên:", ["Tất cả thành viên"] + creator_emails)
            if sel_creator != "Tất cả thành viên":
                all_projects = [p for p in all_projects if p.get("user_email") == sel_creator]

        search_proj = st.text_input("🔍 Tìm kiếm dự án:", placeholder="Nhập tên dự án...", key="search_proj_inp")
        display_projects = [p for p in all_projects if search_proj.strip().lower() in p['project_title'].lower()] if search_proj.strip() else (all_projects if st.session_state.show_all_projects else all_projects[:3])

        for p in display_projects:
            with st.expander(f"🎬 {p['project_title']}"):
                if is_admin_user:
                    st.caption(f"👤 Tạo bởi: `{p.get('user_email', 'N/A')}` | 📅 Ngày tạo: {p.get('created_at', '')[:10]}")
                
                new_p_name = st.text_input("Đổi tên dự án:", value=p['project_title'], key=f"ren_txt_{p['id']}")
                if st.button("✏️ Cập Nhật Tên", key=f"ren_btn_{p['id']}", use_container_width=True, disabled=is_system_busy):
                    if new_p_name.strip() and new_p_name.strip() != p['project_title']:
                        supabase.table("saved_projects").update({"project_title": new_p_name.strip()}).eq("id", p['id']).execute()
                        if str(st.session_state.get("current_project_id")) == str(p['id']):
                            st.session_state.active_project_title = new_p_name.strip()
                        st.toast("✅ Đã đổi tên dự án thành công!"); time.sleep(0.3); st.rerun()

                col_o, col_d = st.columns(2)
                if col_o.button("📂 Mở", key=f"o_{p['id']}", use_container_width=True, disabled=is_system_busy):
                    sd = p.get("script_content", {})
                    st.session_state.update({
                        "content_analysis": sd.get("content_analysis"), "all_scripts": sd.get("all_scripts", []),
                        "cloned_scripts": sd.get("cloned_scripts", []), "expanded_scripts": sd.get("expanded_scripts", []),
                        "generated_details": sd.get("generated_details", {}), "character_profiles": sd.get("character_profiles", []),
                        "current_input_context": sd.get("current_input_context", ""), "current_project_id": p['id'],
                        "active_project_title": p['project_title'], "scroll_to_detail": True
                    })
                    st.rerun()
                if col_d.button("🗑 Xóa", key=f"d_{p['id']}", type="secondary", use_container_width=True, disabled=is_system_busy):
                    supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                    if str(st.session_state.get("current_project_id")) == str(p['id']):
                        st.session_state.current_project_id = None
                    st.toast("✅ Đã xóa dự án thành công!"); time.sleep(0.3); st.rerun()

        if len(all_projects) > 3 and not search_proj.strip():
            if st.session_state.show_all_projects:
                if st.button("🔼 Thu gọn kho dự án", use_container_width=True, disabled=is_system_busy):
                    st.session_state.show_all_projects = False; st.rerun()
            else:
                if st.button(f"🔽 Xem thêm {len(all_projects)-3} dự án", use_container_width=True, disabled=is_system_busy):
                    st.session_state.show_all_projects = True; st.rerun()

        if is_admin_user:
            st.markdown("---")
            st.markdown("### ⚙ QUẢN TRỊ ADMIN")
            with st.expander("➕ Cấp Quyền Mới"):
                adm_acc = st.text_input("Email tài khoản:", key="adm_acc")
                adm_phone = st.text_input("SĐT tài khoản:", key="adm_phone")
                adm_pass = st.text_input("Mật khẩu ban đầu:", value="123456", key="adm_pass")
                adm_roles_choice = st.multiselect("Thể loại cho phép:", ALL_MODULES, default=ALL_MODULES, key="adm_roles")
                adm_plan = st.radio("Gói cước:", ["Trial", "Basic", "Advanced", "VIP"], horizontal=True, key="adm_plan")
                adm_dur = st.selectbox("Thời hạn cấp quyền:", ["3 Ngày", "7 Ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "Vĩnh viễn", "Tùy chỉnh (Chọn ngày)"], key="adm_dur")
                
                calc_exp = "2099-12-31"
                if adm_dur == "Tùy chỉnh (Chọn ngày)":
                    cust_d = st.date_input("Chọn ngày hết hạn:", value=date.today() + timedelta(days=30), min_value=date.today(), key="adm_custom_d")
                    calc_exp = cust_d.strftime("%Y-%m-%d")
                elif adm_dur != "Vĩnh viễn":
                    dur_map = {"3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730}
                    calc_exp = (datetime.now() + timedelta(days=dur_map.get(adm_dur, 30))).strftime("%Y-%m-%d")

                if st.button("💾 Cấp Quyền Tài Khoản", type="primary", use_container_width=True, key="btn_save_grant"):
                    if adm_acc.strip() and adm_phone.strip() and adm_pass.strip():
                        st.session_state.licensed_accounts[adm_acc.strip()] = {
                            "roles": adm_roles_choice, "phone": adm_phone.strip(), "password": adm_pass.strip(),
                            "expires_at": calc_exp, "plan_type": adm_plan, "daily_usage_count": 0,
                            "last_generation_date": "", "active_session_id": ""
                        }
                        save_single_account(adm_acc.strip(), st.session_state.licensed_accounts[adm_acc.strip()])
                        st.toast(f"✅ Đã cấp quyền tài khoản đến ngày {calc_exp}!"); time.sleep(0.4); st.rerun()
                    else: st.error("Vui lòng điền đủ thông tin.")

            search_acc = st.text_input("🔍 Tìm tài khoản:", placeholder="Nhập Email hoặc SĐT...", key="search_acc_input")
            other_accs = [item for item in st.session_state.licensed_accounts.items() if item[0] != ADMIN_EMAIL]
            filt_accs = [item for item in other_accs if search_acc.strip().lower() in item[0].lower() or search_acc.strip() in item[1].get('phone', '')] if search_acc.strip() else (other_accs if st.session_state.show_all_admin_accounts else other_accs[:3])

            for acc_mail, info in filt_accs:
                with st.expander(f"👤 {acc_mail} ({info.get('plan_type')})"):
                    st.write(f"📞 SĐT: `{info.get('phone', 'N/A')}` | ⏳ Hạn: `{info.get('expires_at')}`")
                    new_u_pass = st.text_input("🔑 Đổi mật khẩu:", value=info.get("password", ""), key=f"pass_e_{acc_mail}")
                    if st.button("⚡ Đặt 123456", key=f"rst_{acc_mail}", use_container_width=True):
                        st.session_state.licensed_accounts[acc_mail]["password"] = "123456"
                        save_single_account(acc_mail, st.session_state.licensed_accounts[acc_mail])
                        st.toast("✅ Đã reset mật khẩu về '123456'!"); time.sleep(0.3); st.rerun()

                    new_roles = st.multiselect("Đổi thể loại:", ALL_MODULES, default=info.get("roles", ALL_MODULES), key=f"r_e_{acc_mail}")
                    new_plan = st.selectbox("Đổi gói cước:", ["Trial", "Basic", "Advanced", "VIP"], index=["Trial", "Basic", "Advanced", "VIP"].index(info.get("plan_type", "Trial")), key=f"p_e_{acc_mail}")
                    renew_choice = st.selectbox("Gia hạn thời gian:", ["Giữ nguyên hạn hiện tại", "3 Ngày", "7 Ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "Vĩnh viễn", "Tùy chỉnh (Chọn ngày)"], key=f"rn_e_{acc_mail}")
                    
                    target_exp = info.get("expires_at", "2099-12-31")
                    if renew_choice == "Tùy chỉnh (Chọn ngày)":
                        try: cur_d = datetime.strptime(info.get("expires_at", ""), "%Y-%m-%d").date()
                        except: cur_d = date.today() + timedelta(days=30)
                        cust_rd = st.date_input("Chọn ngày hết hạn mới:", value=cur_d, min_value=date.today(), key=f"rd_e_{acc_mail}")
                        target_exp = cust_rd.strftime("%Y-%m-%d")
                    elif renew_choice == "Vĩnh viễn": target_exp = "2099-12-31"
                    elif renew_choice != "Giữ nguyên hạn hiện tại":
                        dur_map = {"3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730}
                        target_exp = (datetime.now() + timedelta(days=dur_map.get(renew_choice, 30))).strftime("%Y-%m-%d")

                    col_u1, col_u2 = st.columns(2)
                    if col_u1.button("🔄 Cập Nhật", key=f"save_u_{acc_mail}", use_container_width=True):
                        st.session_state.licensed_accounts[acc_mail]["password"] = new_u_pass.strip()
                        st.session_state.licensed_accounts[acc_mail]["roles"] = new_roles
                        st.session_state.licensed_accounts[acc_mail]["plan_type"] = new_plan
                        st.session_state.licensed_accounts[acc_mail]["expires_at"] = target_exp
                        save_single_account(acc_mail, st.session_state.licensed_accounts[acc_mail])
                        st.toast("✅ Đã cập nhật tài khoản thành công!"); time.sleep(0.3); st.rerun()
                    if col_u2.button("🗑 Xóa", key=f"del_u_{acc_mail}", type="secondary", use_container_width=True):
                        delete_single_account(acc_mail)
                        if acc_mail in st.session_state.licensed_accounts: del st.session_state.licensed_accounts[acc_mail]
                        st.toast("✅ Đã xóa tài khoản!"); time.sleep(0.3); st.rerun()

            if len(other_accs) > 3 and not search_acc.strip():
                if st.session_state.show_all_admin_accounts:
                    if st.button("🔼 Thu gọn danh sách tài khoản", use_container_width=True):
                        st.session_state.show_all_admin_accounts = False; st.rerun()
                else:
                    if st.button(f"🔽 Xem thêm {len(other_accs)-3} tài khoản", use_container_width=True):
                        st.session_state.show_all_admin_accounts = True; st.rerun()

        st.markdown("---")
        support_iframe_code = """
        <!DOCTYPE html><html><head><meta charset="utf-8">
        <style>* { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, sans-serif; } .support-container { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1.5px solid #86efac; border-radius: 14px; padding: 12px 10px; text-align: center; } .support-title { font-size: 14px; font-weight: 800; color: #15803d; margin-bottom: 7px; display: flex; align-items: center; justify-content: center; gap: 6px; } .hotline-card { background: linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%); border-radius: 10px; padding: 8px 6px; text-align: center; } .hotline-label { color: #fecdd3 !important; font-size: 12.5px; font-weight: 700; margin-bottom: 3px; display: flex; align-items: center; justify-content: center; gap: 5px; } .hotline-number { color: #ffffff !important; font-size: 20px; font-weight: 900; letter-spacing: 1.2px; line-height: 1.2; text-shadow: 0 1px 3px rgba(0,0,0,0.35); }</style></head>
        <body><div class="support-container"><div class="support-title"><svg style="width: 17px; height: 17px; fill: #15803d;" viewBox="0 0 24 24"><path d="M12 1a9 9 0 0 0-9 9v7c0 1.66 1.34 3 3 3h3v-8H5v-2a7 7 0 0 1 14 0v2h-4v8h3c.55 0 1-.45 1-1v-4.18A3 3 0 0 0 21 14V10a9 9 0 0 0-9-9z"/></svg><span>HỖ TRỢ TRỰC TIẾP</span></div><div class="hotline-card"><div class="hotline-label"><span>Hotline / Zalo:</span></div><div class="hotline-number">0869 628 316</div></div></div></body></html>
        """
        components.html(support_iframe_code, height=115)
        
        u_info = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        u_plan = u_info.get("plan_type", "Trial")
        u_used = u_info.get("daily_usage_count", 0) if u_info.get("last_generation_date") == datetime.now().strftime("%Y-%m-%d") else 0
        u_lim = "Không giới hạn" if u_plan == "VIP" else (20 if u_plan == "Advanced" else (10 if u_plan == "Basic" else 3))
        st.info(f"**GÓI {u_plan.upper()}**\n\n• Email: {st.session_state.current_email}\n• Đã tạo: **{u_used}/{u_lim}**\n• Hạn dùng: {u_info.get('expires_at')}")

        if st.button("🚪 Đăng Xuất", disabled=is_system_busy):
            st.session_state.is_logged_in = False
            st.rerun()

if not st.session_state.is_logged_in: st.info("👈 Vui lòng đăng nhập ở thanh bên."); st.stop()

# ==============================================================================
# GIAO DIỆN CHÍNH (MAIN WORKSPACE)
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Đạo Diễn AI - Hệ Thống Kịch Bản Pro</div></div>""", unsafe_allow_html=True)
mode = st.selectbox("🎯 Thể loại:", ALL_MODULES, key=f"mode_{st.session_state.reset_key}")
is_viral_mode = ("Viral" in mode)

up_files, custom_note = [], ""
viral_persona, viral_topic = "", ""
if is_viral_mode:
    col_v1, col_v2 = st.columns(2)
    viral_persona = col_v1.text_input("👤 Định vị Kênh:", placeholder="Ví dụ: Mẹ bỉm sữa thông thái, KOC chuyên gia đời sống...", key=f"viral_persona_{st.session_state.reset_key}")
    viral_topic = col_v2.text_area("💡 Chủ đề / Mẹo:", height=68, placeholder="Ví dụ: Mẹo dọn sạch lá khô sân vườn trong 2 phút, bí quyết giữ giàn cây xanh tốt...", key=f"viral_topic_{st.session_state.reset_key}")
    up_files = st.file_uploader("📦 Upload Ảnh:", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_viral_{st.session_state.reset_key}")
    
    if up_files:
        with st.expander(f"👁 Xem lại {len(up_files)} ảnh đã tải lên", expanded=False):
            n_cols = min(len(up_files), 4)
            cols = st.columns(n_cols)
            for idx, f in enumerate(up_files):
                cols[idx % n_cols].image(f, caption=f"Ảnh {idx + 1}", use_container_width=True)
                
    custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất - ví dụ: giàn mướp trĩu quả, thịt xay dẻo quánh):", key=f"custom_note_viral_{st.session_state.reset_key}")
    hero_sku_override = ""
else:
    col_f1, col_f2 = st.columns([2, 1])
    up_files = col_f1.file_uploader("📦 Upload Ảnh SP (Quét OCR Giá, Hero SKU & Bảng màu):", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_prod_{st.session_state.reset_key}")
    hero_sku_override = col_f2.text_input("🎯 Màu / SKU ưu tiên (Tùy chọn):", placeholder="Ví dụ: Nâu, Cối thủy tinh, Hồng Pastel...", key=f"sku_{st.session_state.reset_key}")
    
    if up_files:
        with st.expander(f"👁 Xem lại {len(up_files)} ảnh đã tải lên", expanded=False):
            n_cols = min(len(up_files), 4)
            cols = st.columns(n_cols)
            for idx, f in enumerate(up_files):
                cols[idx % n_cols].image(f, caption=f"Ảnh {idx + 1}", use_container_width=True)
                
    custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất - ví dụ: chuyên đề xay thịt ba chỉ làm nem dẻo quánh):", key=f"custom_note_prod_{st.session_state.reset_key}")

presentation_format_opts = [
    "🌟 1. Bán Ước Mơ & Thành Quả Xã Hội (Outcome-First & Social Proof)",
    "🔥 2. Nỗi Đau & Giải Pháp Thực Tế (Problem-Solving & Setup Proof)",
    "⚡ 3. Đòn Bẩy Flash Sale & Kích Cầu Giá (Price-Anchor CTA)",
    "📦 4. Review & Bóc Hộp Soi Chi Tiết (Freshly Unboxed)"
]
selected_format = st.selectbox("🎬 Hình thức video:", presentation_format_opts, key=f"pres_{st.session_state.reset_key}")

# Module chọn số lượng diễn viên & nhập vai trò (Để trống = AI tự chọn)
num_chars_input = st.number_input("👤 Số lượng diễn viên (1 = Độc thoại KOC, ≥2 = Tiểu phẩm đối thoại):", min_value=1, max_value=4, value=1, key=f"chars_num_{st.session_state.reset_key}")
char_inputs = []
for i in range(num_chars_input):
    col_c1, col_c2 = st.columns([2, 1])
    c_role = col_c1.text_input(
        f"Vai trò Diễn viên {i+1} (Để trống để AI tự phân tích phù hợp):",
        value="",
        placeholder="Để trống = AI tự phân tích (hoặc nhập: Bác làm vườn 45t, Mẹ bỉm 28t...)",
        key=f"role_{i}_{st.session_state.reset_key}"
    )
    c_img = col_c2.file_uploader(f"Ảnh Diễn viên {i+1} (Tùy chọn):", type=["jpg", "png"], key=f"cimg_{i}_{st.session_state.reset_key}")
    char_inputs.append({"id": i+1, "role": c_role.strip(), "file": c_img})

if st.button("🚀 Phân Tích & Tạo Kịch Bản", type="primary", use_container_width=True, disabled=is_system_busy):
    with st.spinner("⏳ Đang phân tích dữ liệu sản phẩm, lựa chọn KOC phù hợp và xây dựng 5 kịch bản..."):
        try:
            st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
            st.session_state["saved_reference_images"] = [compress_image_bytes(f, 768, 75) for f in up_files] if up_files else []
            
            # Gợi ý cho AI nếu người dùng để trống
            user_roles_specified = [c["role"] for c in char_inputs if c["role"]]
            koc_directive = f"Người dùng đã chỉ định diễn viên: {', '.join(user_roles_specified)}. Bắt buộc tuân thủ 100%!" if user_roles_specified else "Người dùng để trống vai trò diễn viên: BẮT BUỘC bạn phải tự động phân tích sản phẩm và bối cảnh để chọn ra chân dung KOC phù hợp nhất (Ví dụ: giàn cây/thổi lá -> nam/bác 35-50t; đồ bếp -> mẹ trẻ/nội trợ 28-35t; mỹ phẩm -> nữ 22-26t; công nghệ -> nam 24-28t). Trả về trong 'koc_demographic_analysis'!"

            prompt = f"""
            PHÂN TÍCH SẢN PHẨM & TẠO 5 KỊCH BẢN CHUẨN THƯƠNG MẠI:
            - Ghi chú riêng: '{custom_note}' | SKU ưu tiên: '{hero_sku_override}'.
            - {koc_directive}
            - BẮT BUỘC 5 KỊCH BẢN ĐẠI DIỆN CHO 5 GÓC ĐỘ: Nỗi đau, Bán ước mơ, Đập tan định kiến, Lifestyle POV, Flash Sale.
            TRẢ VỀ JSON:
            {{
                "content_analysis": {{
                    "self_pronoun": "em", "audience_pronoun": "các chị em",
                    "setting_archetype": "Bối cảnh chuẩn mực đời thực phù hợp sản phẩm",
                    "hero_sku_color": "{hero_sku_override or 'chuẩn ảnh'}",
                    "what_and_unique": "[Tên sản phẩm]: [USP độc bản]",
                    "target_audience": "Tệp khách hàng mục tiêu",
                    "pain_points": "Nỗi đau thực tế lớn nhất",
                    "why_buy": "Lý do thuyết phục không thể từ chối",
                    "where_and_convenience": "Hoàn cảnh ứng dụng và sự tiện lợi",
                    "hook_element": "Yếu tố giật gân 3 giây đầu",
                    "recommended_format": "{selected_format}",
                    "how_to_use": "Thao tác chuẩn đời thực",
                    "product_dimensions": "Kích thước 3 chiều đời thực",
                    "koc_demographic_analysis": {{
                        "gender": "male hoặc female",
                        "persona_vi": "Mô tả chân dung KOC phù hợp bằng tiếng Việt (ví dụ: Người đàn ông 35 tuổi thích chăm sóc sân vườn)",
                        "persona_en": "a 35-year-old native Vietnamese man with a friendly practical look"
                    }},
                    "visceral_demonstration_dna": {{
                        "visual_punch_vi": "Cú sốc thị giác giật nảy 3 giây đầu",
                        "stress_test_vi": "Thử thách cực hạn / soi ngàm cơ học",
                        "satisfying_payoff_vi": "Kết quả biến đổi cực kỳ đã mắt"
                    }},
                    "universal_sensory_matrix": {{
                        "category_type_vi": "Ngành hàng thực tế",
                        "tactile_feel": "Xúc giác chân thực",
                        "visual_aesthetic": "Thị giác ấn tượng",
                        "auditory_asmr": "Âm thanh ASMR thực tế đời sống",
                        "functional_delight": "Cảm xúc thỏa mãn tiện lợi"
                    }},
                    "spatial_asymmetry_analysis": {{
                        "has_asymmetry": false, "feature_type": "none", "anatomical_location_vi": "none"
                    }},
                    "exact_original_price_ocr": "350.000đ", "exact_sale_price_ocr": "290.000đ",
                    "original_price_spoken": "ba trăm năm mươi nghìn đồng", "sale_price_spoken": "hai trăm chín mươi nghìn đồng"
                }},
                "outlines": [
                    {{"id": 1, "title": "Nỗi Đau & Rào Cản Thực Tế", "setting": "Bối cảnh đời thực 1", "hook": "Câu hook ngắn gọn KOC nói trực tiếp..."}},
                    {{"id": 2, "title": "Bán Ước Mơ & Chứng Thực Xã Hội", "setting": "Bối cảnh đời thực 2", "hook": "Câu hook tò mò xã hội..."}},
                    {{"id": 3, "title": "Đập Tan Định Kiến Cũ", "setting": "Bối cảnh đời thực 3", "hook": "..."}},
                    {{"id": 4, "title": "Trải Nghiệm Đời Sống (Lifestyle POV)", "setting": "Bối cảnh đời thực 4", "hook": "..."}},
                    {{"id": 5, "title": "Đòn Bẩy Flash Sale & Kích Cầu", "setting": "Bối cảnh đời thực 5", "hook": "..."}}
                ]
            }}
            """
            payload = ["IMAGES:"] + [types.Part.from_bytes(data=cb, mime_type=cm) for cb, cm in st.session_state["saved_reference_images"]]
            for c in char_inputs:
                if c.get("file"):
                    cb, cm = compress_image_bytes(c['file'], 768, 75)
                    payload.extend([f"ACTOR {c['id']} FACE ONLY:", types.Part.from_bytes(data=cb, mime_type=cm)])
            payload.append(prompt)

            res = call_gemini(payload, get_sys_inst_outlines(mode, "Điện Ảnh Chân Thực", "On-camera", "", num_chars_input, "Tự động mix", custom_note, selected_format))
            st.session_state.content_analysis = res.get("content_analysis", {})
            outlines = res.get("outlines", [])
            for o in outlines: o["presentation_format"] = selected_format
            st.session_state.update({"all_scripts": outlines, "cloned_scripts": [], "expanded_scripts": [], "generated_details": {}, "active_script_id": None})
            st.rerun()
        except Exception as e: st.error(f"Lỗi: {e}")

# ==============================================================================
# BẢNG PHÂN TÍCH DNA 2 CỘT ĐỐI XỨNG (HIỂN THỊ ĐỦ 7 THẺ)
# ==============================================================================
ca = st.session_state.content_analysis
if isinstance(ca, dict) and ca.get("target_audience"):
    st.divider()
    st.markdown("### 🔍 **Phân Tích Chi Tiết Sản Phẩm & Kịch Bản**")
    
    koc_auto_desc = ca.get('koc_demographic_analysis', {}).get('persona_vi', 'Tự động chọn KOC phù hợp') if isinstance(ca.get('koc_demographic_analysis'), dict) else 'Tự động chọn KOC'
    user_specified_actors = [p['role'] for p in st.session_state.get('character_profiles', []) if p.get('role')]
    koc_final_display = f"👤 <b>KOC:</b> {', '.join(user_specified_actors)} (Người dùng chỉ định)" if user_specified_actors else f"🤖 <b>KOC tự động:</b> {koc_auto_desc}"

    # Hàng 1: Thẻ 1 & 2
    c_r1_l, c_r1_r = st.columns(2)
    with c_r1_l:
        st.markdown(clean_html(f"""
        <div class="dna-card">
            <div class="dna-card-title">🎯 1. Chân Dung Khách Hàng & Hook 3s</div>
            <div class="dna-row"><span class="dna-label">👥 Tệp khách hàng:</span><span class="dna-text">{ca.get('target_audience')}</span></div>
            <div class="dna-row"><span class="dna-label">💔 Nỗi đau thực tế:</span><span class="dna-text">{ca.get('pain_points')}</span></div>
            <div class="dna-row"><span class="dna-label" style="color:#d90429;">⚡ Yếu tố Hook 3s:</span><span class="dna-text" style="color:#d90429; font-weight:700;">{ca.get('hook_element')}</span></div>
            <div class="dna-row"><span class="dna-label">🎬 Hình thức tối ưu:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{ca.get('recommended_format')}</span></div>
        </div>
        """), unsafe_allow_html=True)
    with c_r1_r:
        st.markdown(clean_html(f"""
        <div class="dna-card">
            <div class="dna-card-title">🔥 2. Diễn Viên KOC & Mã Màu Bán Chạy</div>
            <div class="dna-row"><span class="dna-label">🎭 Chân dung KOC:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{koc_final_display}</span></div>
            <div class="dna-row"><span class="dna-label">⭐ SKU ưu tiên làm video:</span><span class="dna-text" style="color:#dc2626; font-weight:700;">{ca.get('hero_sku_color')}</span></div>
            <div class="dna-row"><span class="dna-label">🗣 Nhân xưng chuẩn:</span><span class="dna-text" style="color:#15803d; font-weight:700;">Xưng '{ca.get('self_pronoun')}' - Gọi '{ca.get('audience_pronoun')}'</span></div>
            <div class="dna-row"><span class="dna-label">🏙 Chuẩn bối cảnh:</span><span class="dna-text">{ca.get('setting_archetype')}</span></div>
        </div>
        """), unsafe_allow_html=True)

    # Hàng 2: Thẻ 3 & 4
    c_r2_l, c_r2_r = st.columns(2)
    with c_r2_l:
        st.markdown(clean_html(f"""
        <div class="dna-card">
            <div class="dna-card-title">💎 3. Giải Phẫu Sản Phẩm & Nội Dung</div>
            <div class="dna-row"><span class="dna-label">📦 Điểm đặc biệt:</span><span class="dna-text">{format_product_name_bold(ca.get('what_and_unique'))}</span></div>
            <div class="dna-row"><span class="dna-label">🔥 Tại sao nên mua:</span><span class="dna-text">{ca.get('why_buy')}</span></div>
            <div class="dna-row"><span class="dna-label">🛠 Thao tác chuẩn:</span><span class="dna-text">{ca.get('how_to_use')}</span></div>
        </div>
        """), unsafe_allow_html=True)
    with c_r2_r:
        st.markdown(clean_html(f"""
        <div class="dna-card">
            <div class="dna-card-title">⚙ 4. Động Lực Học Thị Giác & Mức Giá</div>
            <div class="dna-row"><span class="dna-label">📐 Kích thước thực tế:</span><span class="dna-text">{ca.get('product_dimensions')}</span></div>
            <div class="dna-row"><span class="dna-label">💰 Mức giá (OCR):</span><span class="dna-text">{format_ocr_prices(ca)}</span></div>
            <div class="dna-row"><span class="dna-label" style="color:#15803d;">🎯 Định hướng chốt:</span><span class="dna-text" style="color:#15803d; font-weight:700;">Soft-sell tự nhiên (Không nhắc giá ở 4 kịch bản thường)</span></div>
        </div>
        """), unsafe_allow_html=True)

    # Hàng 3: Thẻ 5 & 6
    v_demo = ca.get('visceral_demonstration_dna', {})
    s_mat = ca.get('universal_sensory_matrix', {})
    c_r3_l, c_r3_r = st.columns(2)
    with c_r3_l:
        st.markdown(clean_html(f"""
        <div class="dna-card" style="border-left: 4px solid #059669;">
            <div class="dna-card-title" style="color:#047857;">⚡ 5. Động Lực Học Thị Giác & Thử Thách Cực Hạn</div>
            <div class="dna-row"><span class="dna-label">🥊 Cú sốc thị giác Cảnh 1:</span><span class="dna-text">{v_demo.get('visual_punch_vi')}</span></div>
            <div class="dna-row"><span class="dna-label">🔬 Thử thách thực tế Cảnh 2:</span><span class="dna-text">{v_demo.get('stress_test_vi')}</span></div>
            <div class="dna-row"><span class="dna-label">✨ Biến đổi đã mắt Cảnh 3:</span><span class="dna-text" style="color:#b45309; font-weight:700;">{v_demo.get('satisfying_payoff_vi')}</span></div>
        </div>
        """), unsafe_allow_html=True)
    with c_r3_r:
        st.markdown(clean_html(f"""
        <div class="dna-card" style="border-left: 4px solid #f97316;">
            <div class="dna-card-title" style="color:#ea580c;">✨ 6. Kích Hoạt Đa Giác Quan Đời Sống (ASMR)</div>
            <div class="dna-row"><span class="dna-label">🖐 Xúc giác:</span><span class="dna-text">{s_mat.get('tactile_feel')}</span></div>
            <div class="dna-row"><span class="dna-label">👁 Thị giác:</span><span class="dna-text">{s_mat.get('visual_aesthetic')}</span></div>
            <div class="dna-row"><span class="dna-label">👂 Thính giác ASMR:</span><span class="dna-text" style="color:#15803d; font-weight:700;">{s_mat.get('auditory_asmr')}</span></div>
        </div>
        """), unsafe_allow_html=True)

# ==============================================================================
# DANH SÁCH KỊCH BẢN & CHI TIẾT PHÂN CẢNH
# ==============================================================================
all_sc = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
if all_sc:
    st.divider()
    if st.session_state.active_script_id is not None:
        active_id = st.session_state.active_script_id
        asc = st.session_state.generated_details.get(int(active_id), {})
        scenes_list = asc.get("scenes", [])
        num_scenes = len(scenes_list)

        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(asc.get('title', '')).upper()} ({num_scenes} PHÂN CẢNH TỰ ĐỘNG)**")
        st.markdown(f"<div class='detail-header-box'>{asc.get('director_summary', '')}</div>", unsafe_allow_html=True)

        for idx, scn in enumerate(scenes_list, 1):
            st.markdown(f"#### 📍 Phân cảnh {idx}/{num_scenes} - Giai đoạn {scn.get('aida_stage')} (⏱ {scn.get('dur')})")
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting')}* | **Âm thanh Foley:** *{scn.get('sfx')}*")
            st.markdown(f"**💬 Thoại on-camera từ 0.00s:** <div class='voiceover-text'>{scn.get('voiceover')}</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🖼 Prompt Ảnh (Midjourney):**")
                st.code(scn.get('img_p', ''), language="text")
                safe_copy_button(scn.get('img_p', ''), f"📋 Sao Chép Prompt Ảnh Cảnh {idx}")
                if idx > 1: st.caption("💡 *Mẹo mỏ neo:* Dùng link ảnh Cảnh 1 làm mỏ neo: `--cref [URL_ẢNH_CẢNH_1] --cw 100`")
            with c2:
                st.markdown("**🎥 Prompt Video (Veo 3 / Kling AI):**")
                st.code(scn.get('vid_p', ''), language="text")
                safe_copy_button(scn.get('vid_p', ''), f"📋 Sao Chép Prompt Video Cảnh {idx}")
                if idx > 1: st.caption(f"🎞 *Kỹ thuật nối mượt 100%:* Cắt Last-Frame của Cảnh {idx-1} nạp làm Start-Frame cho Cảnh {idx} này!")

            with st.expander(f"🛡 Negative Prompt Chuyên Biệt Cảnh {idx}", expanded=False):
                st.code(scn.get('vid_neg', ''), language="text")
                safe_copy_button(scn.get('vid_neg', ''), f"📋 Sao Chép Negative Prompt Cảnh {idx}", custom_color="#475569")
            st.markdown("---")

    comp_sc = [sc for sc in all_sc if int(sc.get("id")) in st.session_state.generated_details]
    pend_sc = [sc for sc in all_sc if int(sc.get("id")) not in st.session_state.generated_details]

    if comp_sc:
        st.markdown("### 🎬 **1. Kịch Bản ĐÃ Dựng Chi Tiết**")
        for sc in comp_sc:
            sc_id = sc["id"]
            with st.container(border=True):
                c1, c2, c3 = st.columns([2.5, 1, 1])
                c1.markdown(f"**#{sc_id}. {sc.get('title')}**")
                c1.caption(f"⚡ *{sc.get('hook')}*")
                if c2.button("👁 Xem lại", key=f"v_{sc_id}", use_container_width=True):
                    st.session_state.active_script_id = int(sc_id); st.rerun()
                if c3.button("🚀 Nhân bản", key=f"c_{sc_id}", type="primary", use_container_width=True):
                    clones = clone_script(sc_id)
                    st.session_state.cloned_scripts.extend(clones)
                    st.toast("✅ Đã nhân bản 5 kịch bản!"); st.rerun()

    if pend_sc:
        st.markdown("### ⏳ **2. Kịch Bản Chờ Dựng**")
        for sc in pend_sc:
            sc_id = sc["id"]
            with st.container(border=True):
                c1, c2 = st.columns([3, 1.2])
                c1.markdown(f"**#{sc_id}. {sc.get('title')}** <span class=badge-pending>CHỜ DỰNG</span>", unsafe_allow_html=True)
                c1.caption(f"⚡ *{sc.get('hook')}*")
                if c2.button("✨ Tạo chi tiết ngay", key=f"g_{sc_id}", type="secondary", use_container_width=True):
                    with st.spinner(f"Đang dựng kịch bản #{sc_id}..."):
                        create_scene_details(sc_id, mode, "Điện Ảnh Chân Thực")
                        st.session_state.active_script_id = int(sc_id); st.rerun()

    # ==========================================================================
    # GỌI THÊM 5 KỊCH BẢN MỚI
    # ==========================================================================
    st.divider()
    st.markdown("### ➕ **Gọi Thêm 5 Kịch Bản Mới**")
    cg1, cg2 = st.columns([2, 1])
    c_ang = cg1.selectbox("🧭 Chiến lược mới:", ["🌟 Tự động mix (1 Flash Sale + 4 Tự Nhiên)", "🌿 Chia sẻ & Bán Ước Mơ", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến", "⚡ Flash Sale & Deal hời"])
    extra_custom_note = cg2.text_input("Ghi chú bổ sung:")
    if st.button("🚀 Tạo Thêm 5 Kịch Bản", type="primary", use_container_width=True):
        new_sc = generate_more_scripts(c_ang, 1, [], "On-camera", "10s", [], extra_custom_note, selected_format)
        st.session_state.expanded_scripts.extend(new_sc)
        st.toast("✅ Đã sinh thêm 5 kịch bản mới!"); st.rerun()
