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
    return round((words / rate) + (commas * 0.08) + (periods * 0.14), 1)

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
# BỘ LỌC AN TOÀN VEO 3 & MIDJOURNEY (TRIỆT TIÊU VI PHẠM POLICY)
# ==============================================================================
SAFETY_REPLACEMENTS = {
    r'\bnude\b': 'champagne-beige',
    r'\bcorset\b': 'lace camisole vest',
    r'\bchest\s*pads?\b': 'tailored lining',
    r'\bcleavage\b': 'modest neckline',
    r'\bhugging\s*(?:her\s*)?(?:slim\s*)?waist\b': 'tailored waistline',
    r'\bsexy\b': 'chic',
    r'\bundress(?:ing)?\b': 'wearing',
    r'\bknife\b': 'prep tool',
    r'\bblade\b': 'cutter',
}

def sanitize_prompt_safety(text: str) -> str:
    if not text: return ""
    cleaned = text
    # Khử từ ngữ nhạy cảm
    for pattern, rep in SAFETY_REPLACEMENTS.items():
        cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    # Khử chuỗi tiếng Việt lẫn vào prompt tiếng Anh (ngoại trừ Spoken audio)
    cleaned = re.sub(r'\bauthentic\s+authentic\b', 'authentic', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bstrictly\s+wearing\s+identical\s+wearing\b', 'strictly wearing identical', cleaned, flags=re.IGNORECASE)
    # Lọc bỏ các cụm tiếng Việt rác trong phần mô tả sản phẩm của prompt EN
    cleaned = re.sub(r'Màu\s+da\s*\([^)]*\)\s*Áo\s+Vest[^\.,"]*', 'tailored lace vest', cleaned, flags=re.IGNORECASE)
    # Chặn nhãn sàn TMĐT
    for p in [r'\btiktok\s*(?:shop)?\b', r'\bshopee\b', r'\blazada\b', r'\bfacebook\b']:
        cleaned = re.sub(p, 'retail marketplace', cleaned, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', cleaned).strip()

# ==============================================================================
# QUẢN LÝ TIỀN TỆ & TÂM LÝ HỌC NEO GIÁ
# ==============================================================================
def number_to_vietnamese_words(n: int) -> str:
    if n == 0: return "không đồng"
    digits = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    def read_block_3(num_str, is_highest=False):
        num_str = num_str.zfill(3)
        h, t, u = int(num_str[0]), int(num_str[1]), int(num_str[2])
        res = []
        if not is_highest or h > 0: res.append(digits[h] + " trăm")
        if t == 0 and u != 0: res.append("linh " + digits[u] if not is_highest or h > 0 else digits[u])
        elif t == 1:
            res.append("mười")
            if u == 1: res.append("một")
            elif u == 4: res.append("bốn")
            elif u == 5: res.append("lăm")
            elif u != 0: res.append(digits[u])
        elif t > 1:
            res.append(digits[t] + " mươi")
            if u == 1: res.append("mốt")
            elif u == 4: res.append("bốn")
            elif u == 5: res.append("lăm")
            elif u != 0: res.append(digits[u])
        return " ".join(res)

    s = str(abs(n))
    groups = []
    while s:
        groups.append(s[-3:]); s = s[:-3]
    units = ["", "nghìn", "triệu", "tỷ"]
    result_parts = []
    for i in range(len(groups) - 1, -1, -1):
        val = int(groups[i])
        if val > 0:
            part = read_block_3(groups[i], is_highest=(i == len(groups) - 1))
            if units[i]: part += " " + units[i]
            result_parts.append(part)
    return re.sub(r'\s+', ' ', " ".join(result_parts)).strip() + " đồng"

def extract_numeric_price(raw_text: str) -> int:
    if not raw_text: return 0
    clean = str(raw_text).replace('.', '').replace(',', '').replace('đ', '').replace('k', '000').strip()
    nums = re.findall(r'\b\d{4,9}\b', clean)
    if nums: return int(nums[0])
    nums_short = re.findall(r'\b\d{2,3}\b', clean)
    if nums_short and ('k' in str(raw_text).lower() or 'nghìn' in str(raw_text).lower()):
        return int(nums_short[0]) * 1000
    return 0

def convert_to_soft_price_range(price_text: str, is_orig: bool = False, exact_raw_str: str = "") -> str:
    val = extract_numeric_price(exact_raw_str) or extract_numeric_price(price_text)
    if val <= 0: return "gần ba trăm nghìn" if is_orig else "hơn một trăm bảy mươi nghìn"
    if is_orig:
        if val < 100000: ceil_val = math.ceil(val / 10000) * 10000
        elif val < 1000000: ceil_val = math.ceil(val / 100000) * 100000 if val % 100000 >= 75000 else math.ceil(val / 10000) * 10000
        else: ceil_val = math.ceil(val / 1000000) * 1000000 if val % 1000000 >= 800000 else math.ceil(val / 100000) * 100000
        return f"gần {number_to_vietnamese_words(ceil_val).replace(' đồng', '').strip()}"
    else:
        if val < 50000: return "mấy chục nghìn"
        floor_val = math.floor(val / 10000) * 10000 if val < 1000000 else math.floor(val / 100000) * 100000
        return f"hơn {number_to_vietnamese_words(floor_val).replace(' đồng', '').strip()}"

def extract_and_convert_prices_in_text(raw_text: str) -> str:
    if not raw_text: return ""
    text = re.sub(r'\b(\d{1,4})\s*[kK]\b', lambda m: number_to_vietnamese_words(int(m.group(1)) * 1000).replace(" đồng", ""), raw_text)
    def repl(m):
        try:
            val = int(m.group(1).replace('.', '').replace(',', ''))
            if val >= 1000: return number_to_vietnamese_words(val).replace(" đồng", "")
        except: pass
        return m.group(0)
    return re.sub(r'(\b\d{1,3}(?:[.,]\d{3})+\b)', repl, text)

# ==============================================================================
# NHÂN KHẨU HỌC KOC: ƯU TIÊN USER > TỰ ĐỘNG PHÂN TÍCH THEO SẢN PHẨM
# ==============================================================================
def get_demographics_description(char_profiles, ai_persona_en=""):
    user_roles = [str(p.get("role", "")).strip() for p in (char_profiles or []) if str(p.get("role", "")).strip()]
    if not user_roles and ai_persona_en and len(ai_persona_en.strip()) > 8:
        ai_lower = ai_persona_en.lower()
        gender = "male" if any(k in ai_lower for k in ["man", "male", "boy", "father", "gentleman", "anh", "nam"]) else "female"
        return gender, ai_persona_en.strip().capitalize()
    if not char_profiles or not user_roles:
        return "female", "A 26-year-old native Vietnamese woman"
    
    parts = []
    primary_gender = "female"
    for idx, p in enumerate(char_profiles):
        role_str = str(p.get("role", "")).strip()
        if not role_str: continue
        r_low = role_str.lower()
        is_m = any(k in r_low for k in ["bố", "ba", "chồng", "nam", "anh", "trai", "thanh niên", "ông"])
        desc = f"a native Vietnamese {'young man' if is_m else 'woman'} ({role_str})"
        if idx == 0: primary_gender = "male" if is_m else "female"
        parts.append(desc)
    return primary_gender, (", ".join(parts[:-1]).capitalize() + " and " + parts[-1]) if len(parts) > 1 else parts[0].capitalize()

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
    clean = clean_analysis_text(text)
    if ":" in clean:
        parts = clean.split(":", 1)
        return f"<b style='color:#0f172a; font-weight:800; font-size:15px;'>{parts[0].strip()}</b>: {parts[1].strip()}"
    return f"<b style='color:#0f172a; font-weight:800; font-size:15px;'>{clean}</b>"

def format_ocr_prices(ca_data: dict) -> str:
    if not isinstance(ca_data, dict): return "<span style='color:#dc2626; font-weight:700;'>Chưa xác định</span>"
    exact_orig = ca_data.get('exact_original_price_ocr', '')
    exact_sale = ca_data.get('exact_sale_price_ocr', '')
    if exact_orig and exact_sale:
        return f"<b style='color:#475569;'>Giá gốc:</b> <span style='color:#64748b; text-decoration:line-through; font-weight:700;'>{clean_analysis_text(exact_orig)}</span> &nbsp;|&nbsp; <b style='color:#dc2626;'>Giá giảm:</b> <span style='color:#dc2626; font-weight:800;'>{clean_analysis_text(exact_sale)}</span>"
    return "<span style='color:#dc2626; font-weight:700;'>Chưa xác định</span>"

def clean_analysis_text(text) -> str:
    if not text: return ""
    pattern = r'^(?:SẢN PHẨM LÀ GÌ|MỤC ĐÍCH|ĐỐI TƯỢNG|LÝ DO MUA)\s*:\s*'
    return clean_and_normalize_voiceover(re.sub(pattern, '', str(text).strip(), flags=re.IGNORECASE).strip())

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict): 
        return "<br>".join([f"<span class='dna-label'>{str(k).title()}:</span> <span class='dna-text'>{clean_analysis_text(v)}</span>" for k, v in field_val.items()])
    return f"<span class='dna-text'>{clean_analysis_text(field_val)}</span>"

# ==============================================================================
# SUPABASE & QUẢN TRỊ ADMIN
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
    if not acc: return False, "Lỗi xác thực."
    if datetime.now() > datetime.strptime(acc.get("expires_at", "2099-12-31"), "%Y-%m-%d"): return False, "Tài khoản đã hết hạn."
    plan = acc.get("plan_type", "Trial")
    if plan == "VIP": return True, ""
    limit = {"Advanced": 20, "Basic": 10, "Trial": 3}.get(plan, 3)
    today = datetime.now().strftime("%Y-%m-%d")
    if acc.get("last_generation_date") != today:
        acc["daily_usage_count"] = 0
        acc["last_generation_date"] = today
    if is_detailing:
        if acc.get("daily_usage_count", 0) >= limit: return False, f"Hết lượt tạo ({limit}/{limit}) hôm nay!"
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
    ("last_presentation_format", "🌟 AI Tự Động Phân Tích & Đề Xuất"),
    ("target_duration_instruction", ""), ("character_profiles", []), ("current_project_id", None),
    ("saved_reference_images", []), ("show_all_projects", False), ("show_all_admin_accounts", False),
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

def call_gemini(contents, sys_inst="Bạn là AI hỗ trợ JSON.", max_tokens=6500):
    models_to_try = ["gemini-3.8-flash", "gemini-3.8-flash-lite"]
    last_exception = None
    for model_name in models_to_try:
        for attempt in range(3):
            try:
                res = client.models.generate_content(
                    model=model_name, contents=contents,
                    config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.7, max_output_tokens=max_tokens)
                )
                return repair_and_parse_json(res.text)
            except Exception as e:
                last_exception = e
                time.sleep((attempt + 1) * 1.5)
    raise Exception(f"Google API tạm thời gián đoạn. Vui lòng thử lại sau vài giây! (Chi tiết: {last_exception})")

def build_voice_direction(mode, num_chars, character_profiles):
    is_tiktok_shop = ("Viral" not in mode)
    speed_txt = "tốc độ dồn dập (4.8 - 5.2 từ/s), rướn người, dứt khoát" if is_tiktok_shop else "tốc độ tự nhiên, truyền cảm, chân thực (3.8 - 4.2 từ/s)"
    return f"100% Giọng Hà Nội chuẩn bản địa, phát âm tròn vành rõ chữ, số 4 đọc là 'bốn', {speed_txt}. Phong thái nhất quán suốt các cảnh."

def generate_char_rules_string(profiles):
    return "100% người Việt Nam bản địa, nhân vật hư cấu đời thường, tóc đen tuyền tự nhiên, khóa duy nhất 1 kiểu tóc và 1 khuôn mặt suốt 4 cảnh."

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, angle, custom_note="", presentation_format=""):
    is_viral = ("Viral" in mode)
    viral_dir = "VIRAL & XÂY KÊNH: Kéo Follow, chia sẻ mẹo thật, không bán hàng, không báo giá." if is_viral else "TIKTOK SHOP: Kịch bản tập trung giải quyết vấn đề, trải nghiệm thực tế và chốt deal an toàn."
    return f"""
    TỔNG ĐẠO DIỄN VIDEO TRIỆU VIEW. PHONG CÁCH: {style}.
    {viral_dir}
    Ghi chú ưu tiên: {custom_note}
    QUY TẮC CỐT LÕI:
    - BẮT BUỘC TỰ ĐỘNG PHÂN TÍCH CHÂN DUNG KOC PHÙ HỢP NHẤT VỚI SẢN PHẨM (Ví dụ: chuột gaming/PC -> nam 22-26t; đồ bếp -> mẹ trẻ/nội trợ 28-35t; mỹ phẩm -> nữ 20-25t).
    - Mỗi kịch bản chọn 1 BỐI CẢNH ĐỜI THỰC KHÁC NHAU ăn khớp với sản phẩm.
    - CÂU THOẠI: 100% Giọng Hà Nội chuẩn, dùng 'nghìn', số 4 đọc 'bốn', viết rõ 'một trăm'. CẤM 'ngàn', 'trợ giá'.
    - Lời thoại bắt đầu ngay từ 0.00s.
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction, num_chars, character_profiles, custom_note="", presentation_format="", self_pronoun="em", audience_pronoun="các chị em", setting_archetype="", is_fixed_location=True):
    is_viral = ("Viral" in mode)
    outro_rule = f"""
    CÔNG THỨC KẾT BÀI SOFT-SELL: '{audience_pronoun.capitalize()} nào thích tiện lợi thì tham khảo ngay nhé, bấm góc trái xem thử nha!'
    """ if is_viral else f"""
    CÔNG THỨC CHỐT DEAL FLASH SALE: 'Bình thường khoảng [giá gốc làm tròn lên], nay giảm chỉ còn khoảng [giá sale làm tròn xuống] thôi... {audience_pronoun} bấm góc trái kiểm tra tài khoản mình xem nhé!'
    """
    return f"""
    TỔNG ĐẠO DIỄN VIDEO THƯƠNG MẠI. PHONG CÁCH: {style}.
    {outro_rule}
    Ghi chú riêng: {custom_note}

    🛑 QUY TẮC BẮT BUỘC VỀ TRẢI NGHIỆM THỰC TẾ & AN TOÀN POLICY:
    1. ƯU TIÊN MẶC VÀ TRẢI NGHIỆM THỰC TẾ:
       - Sản phẩm thời trang: ƯU TIÊN KOC MẶC TRỰC TIẾP LÊN NGƯỜI, thể hiện form dáng chuẩn; hoặc cầm trên tay / treo mắc khi phối đồ.
       - Mọi sản phẩm khác: KOC phải cầm, bấm, thao tác, trải nghiệm thực tế trước ống kính.
    2. TRANG PHỤC THÍCH ỨNG CHUẨN XÁC THEO SẢN PHẨM & BỐI CẢNH:
       - Đồ công nghệ / Gaming / PC: Áo phông/polo năng động, hoodie/cardigan trẻ trung, quần jogger/chinos, sneaker. TUYỆT ĐỐI CẤM TẠP DỀ!
       - Đồ bếp: Áo thun/polo gọn gàng, tạp dề nấu ăn.
       - Khóa đồng nhất 100% trang phục, tóc và mặt từ Cảnh 1 đến Cảnh 4.
    3. VIDEO & AUDIO SẠCH 100%:
       - TUYỆT ĐỐI KHÔNG DÙNG TỪ NHẠY CẢM: Thay 'nude' bằng 'champagne-beige/neutral tan', thay 'corset' bằng 'camisole vest', thay 'chest pads' bằng 'tailored lining'.
       - KHÔNG chữ, KHÔNG phụ đề, KHÔNG icon giỏ hàng ảo, KHÔNG watermark.
       - KHÔNG nhạc nền (Zero BGM), chỉ có Spoken Voiceover và âm thanh Foley thực tế.
    """

# ==============================================================================
# TẠO CHI TIẾT PHÂN CẢNH (ĐÃ TỐI ƯU TOKEN & POLICY AN TOÀN)
# ==============================================================================
def create_scene_details(target_id, mode, style):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if str(sc.get("id")) == str(target_id)), None)
    if not outline: raise Exception("Không tìm thấy kịch bản.")

    char_profiles = outline.get("character_profiles", st.session_state.get("character_profiles", []))
    char_rules = generate_char_rules_string(char_profiles)
    num_chars = outline.get("actors", 1)
    current_active_mode = mode or st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    is_tiktok_shop = ("Viral" not in current_active_mode)
    is_viral = ("Viral" in current_active_mode)

    fixed_title = outline.get('title', 'Kịch bản chi tiết')
    fixed_hook = clean_and_normalize_voiceover(outline.get('hook', ''))
    fixed_setting_base = outline.get('setting', 'Không gian thực tế phù hợp')
    user_custom_note = outline.get("custom_note") or st.session_state.get("current_input_context", "").strip()
    presentation_format = outline.get("presentation_format") or st.session_state.get("last_presentation_format", "")

    dna = st.session_state.get("content_analysis") or {}

    # Nhận diện KOC tự động
    ai_koc_data = dna.get("koc_demographic_analysis", {})
    ai_persona_en = ai_koc_data.get("persona_en", "") if isinstance(ai_koc_data, dict) else ""
    detected_gender, detected_demographic_en = get_demographics_description(char_profiles, ai_persona_en)

    # Làm tròn giá chuẩn xác bằng Python
    orig_price_spoken = clean_and_normalize_voiceover(dna.get("original_price_spoken", ""))
    sale_price_spoken = clean_and_normalize_voiceover(dna.get("sale_price_spoken", ""))
    exact_orig_raw = str(dna.get("exact_original_price_ocr", ""))
    exact_sale_raw = str(dna.get("exact_sale_price_ocr", ""))
    soft_orig_price = convert_to_soft_price_range(orig_price_spoken, is_orig=True, exact_raw_str=exact_orig_raw)
    soft_sale_price = convert_to_soft_price_range(sale_price_spoken, is_orig=False, exact_raw_str=exact_sale_raw)

    self_pronoun = dna.get("self_pronoun") or "em"
    audience_pronoun = dna.get("audience_pronoun") or ("các chị em" if not is_viral else "mọi người")

    hero_color_str = dna.get("hero_sku_color", "").strip()
    raw_prod_name = str(dna.get("what_and_unique", "product")).strip()
    if ":" in raw_prod_name: raw_prod_name = raw_prod_name.split(":", 1)[0].strip()
    clean_prod_en = sanitize_prompt_safety(f"authentic {hero_color_str} {raw_prod_name}".strip())

    prompt_text = f"""
    SẢN PHẨM: {clean_prod_en} | TIÊU ĐỀ: '{fixed_title}' | BỐI CẢNH: '{fixed_setting_base}'
    KOC: {detected_demographic_en} | ĐẠI TỪ: '{self_pronoun}' - '{audience_pronoun}'
    YÊU CẦU ĐẶC BIỆT: {user_custom_note}

    CHỈ ĐẠO TRANG PHỤC & HÀNH ĐỘNG:
    1. Thiết kế 1 bộ trang phục 'master_outfit_en' ăn khớp hoàn toàn với {clean_prod_en} và bối cảnh {fixed_setting_base} (Ví dụ đồ công nghệ/gaming tuyệt đối không tạp dề; đồ bếp mới dùng tạp dề). Khóa cứng từ Cảnh 1 đến Cảnh 4.
    2. Nếu là thời trang: ƯU TIÊN KOC MẶC TRÊN NGƯỜI phô diễn form dáng; các đồ khác phải cầm nắm thao tác thực tế.
    3. TUYỆT ĐỐI KHÔNG dùng từ nhạy cảm (dùng 'champagne-beige' thay 'nude', 'camisole vest' thay 'corset').

    TRẢ VỀ JSON:
    {{
        "title": "{fixed_title}",
        "wardrobe_lock": {{
            "outfit_vi": "Mô tả tiếng Việt bộ trang phục phù hợp với {clean_prod_en} và bối cảnh {fixed_setting_base}",
            "master_outfit_en": "Concise English description of clothing and footwear matching {clean_prod_en} and {fixed_setting_base}",
            "hair_and_face_en": "{detected_demographic_en}, neat jet-black hair, warm natural skin tone"
        }},
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention",
                "setting_en": "Concise English setting description",
                "camera_shot": "Vertical 9:16 eye-level medium shot",
                "action_en": "First, holding, wearing, or interacting with {clean_prod_en} naturally; then smoothly speaking to camera",
                "sfx": "Foley natural interaction sound (strictly zero BGM)",
                "director": "Attention | Trải nghiệm thực tế | Thoại on-camera từ 0.00s",
                "voiceover": "Đoạn thoại mở màn (18-35 từ) xưng '{self_pronoun}' gọi '{audience_pronoun}' chuẩn tiếng Hà Nội..."
            }},
            {{
                "scene": 2, "aida_stage": "Interest",
                "setting_en": "Concise English setting description",
                "camera_shot": "Vertical 9:16 eye-level medium close-up",
                "action_en": "Demonstrating key practical feature with steady hands",
                "sfx": "Foley mechanical or fabric interaction sound",
                "director": "Interest | Thao tác trực quan | Thoại on-camera từ 0.00s",
                "voiceover": "Đoạn thoại đào sâu tính năng (20-35 từ)..."
            }},
            {{
                "scene": 3, "aida_stage": "Desire",
                "setting_en": "Concise English setting description",
                "camera_shot": "Vertical 9:16 eye-level lifestyle shot",
                "action_en": "Presenting satisfying outcome smoothly to camera",
                "sfx": "Foley ambient lifestyle sound",
                "director": "Desire | Bằng chứng thực tế | Thoại on-camera từ 0.00s",
                "voiceover": "Đoạn thoại chia sẻ trải nghiệm (20-35 từ)..."
            }},
            {{
                "scene": 4, "aida_stage": "Action",
                "setting_en": "Concise English closing setting",
                "camera_shot": "Vertical 9:16 warm eye-level closing shot",
                "action_en": "Holding or wearing {clean_prod_en} steadily, gesturing warmly with open hands",
                "sfx": "Foley soft chime bell",
                "director": "Action | Chốt deal an toàn",
                "voiceover": "Bình thường khoảng {soft_orig_price}, nay giảm chỉ còn khoảng {soft_sale_price} thôi, nhưng giá từng thời điểm có thể khác nhau tùy đợt ưu đãi, {audience_pronoun} cứ bấm góc trái kiểm tra tài khoản mình xem nhé!"
            }}
        ]
    }}
    """
    sys_inst = get_sys_inst_details(current_active_mode, style, "On-camera", char_rules, "10s", num_chars, char_profiles, user_custom_note, presentation_format, self_pronoun, audience_pronoun, fixed_setting_base, True)
    res = call_gemini([prompt_text], sys_inst, max_tokens=6500)
    if not res: raise Exception("AI không phản hồi dữ liệu. Vui lòng thử lại.")

    scenes = res.get("scenes") or res.get("script") or []
    if not scenes: raise Exception("Không tạo được danh sách phân cảnh. Vui lòng bấm tạo lại.")

    w_lock = res.get("wardrobe_lock", {})
    final_outfit_en = sanitize_prompt_safety(w_lock.get("master_outfit_en", "clean tailored top and trousers, lifestyle footwear"))
    final_outfit_vi = w_lock.get("outfit_vi", "Trang phục thanh lịch hiện đại")
    final_actor_head = sanitize_prompt_safety(w_lock.get("hair_and_face_en", f"{detected_demographic_en}, neat jet-black hair"))

    locked_character_segment = f"{final_actor_head}, strictly wearing {final_outfit_en}"

    base_negative_prompt = (
        "subtitles, text, words, typography, letters, watermark, icons, logos, cart icon, emojis, "
        "background music, musical score, instrumental music, bgm, soundtrack, singing, "
        "opposite gender, celebrity likeness, deepfake, inconsistent scale, deformed hands, extra fingers, "
        "blurry, changing clothes, changing outfit, different facial identity, barefoot, dropping product"
    )

    total_sec = 0.0
    for scn in scenes:
        vo_raw = clean_and_normalize_voiceover(scn.get("voiceover", ""))
        if scn.get("scene") == 4 and not is_viral:
            vo_raw = f"Bình thường khoảng {soft_orig_price}, nay giảm chỉ còn khoảng {soft_sale_price} thôi, nhưng giá từng thời điểm có thể khác nhau tùy đợt ưu đãi, {audience_pronoun} cứ bấm góc trái kiểm tra tài khoản mình xem nhé!"
        scn["voiceover"] = vo_raw

        raw_speech_time = calculate_speech_duration(vo_raw, is_tiktok_shop)
        dynamic_scene_sec = min(10, max(4, math.ceil(raw_speech_time + 1.1)))
        scn["dur"] = f"{dynamic_scene_sec}s"
        scn["actual_speech_sec"] = round(dynamic_scene_sec - 0.8, 1) if raw_speech_time >= dynamic_scene_sec else raw_speech_time
        total_sec += float(dynamic_scene_sec)

        camera_shot = scn.get("camera_shot", "Vertical 9:16 eye-level medium shot")
        sfx_sound = sanitize_prompt_safety(scn.get("sfx", "Natural Foley sound"))
        scene_setting_en = sanitize_prompt_safety(scn.get("setting_en", fixed_setting_base))
        clean_action = sanitize_prompt_safety(scn.get("action_en", f"interacting with {clean_prod_en}"))

        # Prompt Ảnh Midjourney tinh gọn token
        img_core = f"{camera_shot}, live-action photography, {scene_setting_en}, {locked_character_segment}, {clean_action}, featuring {clean_prod_en}, sharp focus --ar 9:16 --style raw --v 6.1"
        scn["img_p"] = sanitize_prompt_safety(img_core)
        scn["img_neg"] = base_negative_prompt

        clean_vo_for_audio = re.sub(r'\.{2,}', '.', vo_raw).strip()

        # Prompt Video Veo 3 chuẩn sweet-spot 65-75 từ
        raw_vid = (
            f"{camera_shot}, live-action footage. Setting: {scene_setting_en}. Subject: {locked_character_segment}. "
            f"Action: {clean_action}, actively using authentic {clean_prod_en}. Character maintains steady grip or wear, never dropping. "
            f"Visibly speaks dialogue once with natural lip-sync from 0.00s, then closes mouth smiling warmly while continuing motion. "
            f"Spoken in native Northern Vietnamese Hanoi accent. Spoken audio: \"{clean_vo_for_audio}\". "
            f"Strictly natural Foley sound effects and spoken voiceover only, zero background music, zero musical score, no BGM. Foley: [{sfx_sound}]. "
            f"Pure camera footage, strictly zero subtitles, no text, no on-screen icons."
        )
        scn["vid_p"] = sanitize_prompt_safety(raw_vid)
        scn["vid_neg"] = base_negative_prompt

    res["scenes"] = scenes
    res["total_dur"] = f"Khoảng {int(total_sec)} giây"
    res["director_summary"] = "<br>".join([
        f"⏱ <b>Thời lượng:</b> Khoảng {int(total_sec)}s | 👤 <b>Khóa KOC:</b> {detected_demographic_en}",
        f"🗣 <b>Đại từ:</b> '{self_pronoun}' - '{audience_pronoun}' | 🏙 <b>Bối cảnh:</b> {fixed_setting_base}",
        f"👗 <b>Trang phục đồng nhất:</b> {final_outfit_vi}",
        f"🎨 <b>Hero SKU:</b> {hero_color_str if hero_color_str else 'Chuẩn ảnh'}",
        f"🔇 <b>Âm thanh:</b> Thuần Foley & Thoại trực tiếp (Zero BGM, Zero Subtitles, Zero Icons)",
        f"💰 <b>Khoảng giá an toàn:</b> Bình thường khoảng {soft_orig_price}, nay giảm khoảng {soft_sale_price}"
    ])

    st.session_state.generated_details[int(target_id)] = res
    st.session_state.generated_details[str(target_id)] = res

def clone_script(script_id):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    style = st.session_state.get("last_style", "Điện Ảnh Chân Thực")
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if str(sc.get("id")) == str(script_id)), None)
    if not target: return []
    cur_len = len(all_combined)
    prompt = f"Nhân bản 5 biến thể thoại bám sát kịch bản #{script_id}: '{target.get('title')}'. Trả về JSON có khóa 'outlines' danh sách gồm title, setting, hook."
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, "On-camera", "", 1, "Nhân bản thoại"))
    clones = res.get("outlines", [])
    return [{
        "id": cur_len + idx + 1, "title": cl.get("title", f"Biến thể #{cur_len + idx + 1}"),
        "setting": cl.get("setting", f"Bối cảnh #{idx+1}"), "hook": clean_and_normalize_voiceover(cl.get("hook", "")),
        "actors": 1, "character_profiles": target.get("character_profiles", []),
        "presentation_format": target.get("presentation_format", "")
    } for idx, cl in enumerate(clones)]

def generate_more_scripts(angle, num_chars, extra_char_inputs, narrator_mode_more, duration_inst, char_profiles, extra_note="", presentation_format=""):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    style = st.session_state.get("last_style", "Điện Ảnh Chân Thực")
    cur_len = len(st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts)
    prompt = f"Tạo 5 kịch bản góc độ '{angle}', ghi chú: '{extra_note}'. Trả về JSON khóa 'outlines' gồm title, setting, hook."
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, "On-camera", "", num_chars, angle, extra_note, presentation_format))
    outlines = res.get("outlines", [])
    return [{
        "id": cur_len + idx + 1, "title": sc.get("title", f"Kịch bản #{cur_len + idx + 1}"),
        "setting": sc.get("setting", "Bối cảnh đời thực"), "hook": clean_and_normalize_voiceover(sc.get("hook", "")),
        "actors": num_chars, "character_profiles": char_profiles, "presentation_format": presentation_format
    } for idx, sc in enumerate(outlines)]

# ==============================================================================
# THANH BÊN (SIDEBAR) & QUẢN TRỊ ADMIN
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
                        st.toast("✅ Đăng nhập thành công!"); time.sleep(0.4); st.rerun()
                    else: st.error("❌ Email hoặc mật khẩu không đúng!")
            with st.expander("❓ Quên mật khẩu?"):
                st.info("💡 Liên hệ Hotline / Zalo Admin: **0869 628 316** để được cấp lại mật khẩu.")
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
                    else: st.error("⚠️ Thông tin đăng ký không hợp lệ!")
    else:
        st.markdown("### 🗂 DỰ ÁN")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True, disabled=is_system_busy):
            st.session_state.reset_key += 1
            st.session_state.update({
                "all_scripts": [], "cloned_scripts": [], "expanded_scripts": [],
                "generated_details": {}, "content_analysis": None, "active_script_id": None,
                "current_input_context": "", "current_product_data_saved": None, "current_product_data": None,
                "current_project_id": None, "saved_reference_images": [], "character_profiles": []
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
        if c_s2.button("📑 Lưu Bản Mới", use_container_width=True, disabled=is_system_busy):
            payload = {k: st.session_state[k] for k in ["content_analysis", "all_scripts", "cloned_scripts", "expanded_scripts", "generated_details", "character_profiles", "current_input_context"]}
            succ, msg = save_project_to_db(st.session_state.current_email, f"{st.session_state.active_project_title} (Bản sao)", payload, project_id=None)
            if succ:
                st.session_state.active_project_title = f"{st.session_state.active_project_title} (Bản sao)"
                st.toast("✅ Đã lưu dự án mới!"); st.rerun()

        st.markdown("---")
        st.markdown("### 📂 KHO DỰ ÁN")
        is_admin_user = (st.session_state.current_email == ADMIN_EMAIL)
        all_projects = []
        if supabase:
            try:
                res = supabase.table("saved_projects").select("*").order("created_at", desc=True).execute() if is_admin_user else supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
                all_projects = res.data or []
            except: pass

        for p in all_projects[:3]:
            with st.expander(f"🎬 {p['project_title']}"):
                col_o, col_d = st.columns(2)
                if col_o.button("📂 Mở", key=f"o_{p['id']}", use_container_width=True):
                    sd = p.get("script_content", {})
                    st.session_state.update({
                        "content_analysis": sd.get("content_analysis"), "all_scripts": sd.get("all_scripts", []),
                        "cloned_scripts": sd.get("cloned_scripts", []), "expanded_scripts": sd.get("expanded_scripts", []),
                        "generated_details": sd.get("generated_details", {}), "character_profiles": sd.get("character_profiles", []),
                        "current_input_context": sd.get("current_input_context", ""), "current_project_id": p['id'],
                        "active_project_title": p['project_title'], "scroll_to_detail": True
                    })
                    st.rerun()
                if col_d.button("🗑 Xóa", key=f"d_{p['id']}", type="secondary", use_container_width=True):
                    supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                    st.rerun()

        if is_admin_user:
            st.markdown("---")
            st.markdown("### ⚙ QUẢN TRỊ ADMIN")
            with st.expander("➕ Cấp Quyền Mới"):
                adm_acc = st.text_input("Email tài khoản:", key="adm_acc")
                adm_phone = st.text_input("SĐT tài khoản:", key="adm_phone")
                adm_pass = st.text_input("Mật khẩu:", value="123456", key="adm_pass")
                adm_plan = st.radio("Gói cước:", ["Trial", "Basic", "Advanced", "VIP"], horizontal=True, key="adm_plan")
                if st.button("💾 Cấp Quyền", type="primary", use_container_width=True):
                    if adm_acc.strip() and adm_phone.strip():
                        st.session_state.licensed_accounts[adm_acc.strip()] = {
                            "roles": ALL_MODULES, "phone": adm_phone.strip(), "password": adm_pass.strip(),
                            "expires_at": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                            "plan_type": adm_plan, "daily_usage_count": 0, "last_generation_date": "", "active_session_id": ""
                        }
                        save_single_account(adm_acc.strip(), st.session_state.licensed_accounts[adm_acc.strip()])
                        st.toast("✅ Đã cấp quyền!"); st.rerun()

        st.markdown("---")
        u_info = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        st.info(f"**GÓI {u_info.get('plan_type', 'Trial').upper()}**\n\n• Email: {st.session_state.current_email}\n• Hạn dùng: {u_info.get('expires_at')}")
        if st.button("🚪 Đăng Xuất"): 
            st.session_state.is_logged_in = False; st.rerun()

if not st.session_state.is_logged_in: st.info("👈 Vui lòng đăng nhập ở thanh bên."); st.stop()

# ==============================================================================
# 5. KHÔNG GIAN SÁNG TẠO CHÍNH
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Đạo Diễn AI - Hệ Thống Kịch Bản Pro</div></div>""", unsafe_allow_html=True)

mode = st.selectbox("🎯 Thể loại:", ALL_MODULES, key=f"mode_sel_{st.session_state.reset_key}")
is_viral_mode = "Viral" in mode

up_files, custom_note = [], ""
viral_persona, viral_topic = "", ""
if is_viral_mode:
    col_v1, col_v2 = st.columns(2)
    viral_persona = col_v1.text_input("👤 Định vị Kênh:", placeholder="Ví dụ: KOC chuyên gia công nghệ, mẹ bỉm...", key=f"viral_p_{st.session_state.reset_key}")
    viral_topic = col_v2.text_area("💡 Chủ đề / Mẹo:", height=68, placeholder="Ví dụ: 3 mẹo setup bàn làm việc...", key=f"viral_t_{st.session_state.reset_key}")
    up_files = st.file_uploader("📦 Upload Ảnh:", type=["jpg", "png"], accept_multiple_files=True, key=f"up_v_{st.session_state.reset_key}")
    custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất):", key=f"cn_v_{st.session_state.reset_key}")
    hero_sku_override = ""
else:
    col_f1, col_f2 = st.columns([2, 1])
    up_files = col_f1.file_uploader("📦 Upload Ảnh SP (Quét OCR Giá & Bảng màu):", type=["jpg", "png"], accept_multiple_files=True, key=f"up_p_{st.session_state.reset_key}")
    hero_sku_override = col_f2.text_input("🎯 Màu / SKU ưu tiên (Tùy chọn):", placeholder="Ví dụ: Đen nhám, Be, Size L...", key=f"sku_{st.session_state.reset_key}")
    custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất):", key=f"cn_p_{st.session_state.reset_key}")

if up_files:
    with st.expander(f"👁 Xem lại {len(up_files)} ảnh đã tải lên", expanded=False):
        cols = st.columns(min(len(up_files), 4))
        for idx, f in enumerate(up_files):
            cols[idx % 4].image(f, caption=f"Ảnh {idx + 1}", use_container_width=True)

col_opt1, col_opt2, col_opt3 = st.columns([1.2, 1.2, 1.2])
style = col_opt1.selectbox("🎨 Phong cách:", ["Điện Ảnh Chân Thực", "Studio Tối Giản", "Hoạt Hình 3D"], key=f"style_{st.session_state.reset_key}")
initial_angle = col_opt1.selectbox("🧭 Chiến lược:", ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến"], key=f"angle_{st.session_state.reset_key}")
selected_presentation_format = col_opt2.selectbox("🎬 Hình thức video:", ["🌟 AI Tự Động Phân Tích & Đề Xuất", "📦 Review & Bóc Hộp", "👶 Trải Nghiệm Đời Sống"], key=f"pres_{st.session_state.reset_key}")
num_chars = col_opt3.number_input("👤 Số Diễn viên (1 = Độc thoại, ≥2 = Đối thoại):", 1, 4, 1, key=f"nc_{st.session_state.reset_key}")

char_inputs = []
for i in range(num_chars):
    c_r, c_i = st.columns([2, 1])
    role = c_r.text_input(f"Vai trò NV {i+1} (Để trống để AI tự phân tích KOC phù hợp):", value="", placeholder="Để trống = AI tự chọn KOC phù hợp nhất", key=f"r_{i}_{st.session_state.reset_key}")
    c_file = c_i.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"f_{i}_{st.session_state.reset_key}", label_visibility="collapsed")
    if c_file or role.strip():
        char_inputs.append({"id": i+1, "role": role.strip(), "file": c_file})

if st.button("🚀 Phân Tích Sản Phẩm & Tạo Kịch Bản", type="primary", use_container_width=True, disabled=is_system_busy):
    can_run, msg = check_usage_limit(st.session_state.current_email)
    if not can_run: st.error(msg)
    else:
        with st.spinner("⏳ Đạo diễn AI đang quét dữ liệu, phân tích KOC phù hợp & thiết lập Kịch bản..."):
            try:
                st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs] if char_inputs else [{"id": i+1, "role": ""} for i in range(num_chars)]
                char_rules = generate_char_rules_string(st.session_state.character_profiles)
                st.session_state.update({
                    "last_mode": mode, "last_style": style, "last_narrator": "On-camera", 
                    "last_presentation_format": selected_presentation_format,
                    "current_input_context": custom_note.strip()
                })
                
                input_context_str = f"KÊNH: '{viral_persona.strip()}' | CHỦ ĐỀ: '{viral_topic.strip()}' | NOTE: '{custom_note.strip()}'" if is_viral_mode else f"NOTE: '{custom_note.strip()}' | SKU: '{hero_sku_override.strip()}'"
                st.session_state["saved_reference_images"] = [compress_image_bytes(f, 768, 75) for f in up_files] if up_files else []

                prompt = f"""
                INPUT: {input_context_str} | THỂ LOẠI: '{mode}' | HÌNH THỨC: '{selected_presentation_format}'
                DIỄN VIÊN: {num_chars} nhân vật người Việt.
                
                QUY CHUẨN KOC:
                - Nếu để trống vai trò: Tự động phân tích sản phẩm để chọn độ tuổi/giới tính KOC thích hợp nhất trong 'koc_demographic_analysis' (Ví dụ đồ công nghệ/PC -> nam 22-26t; đồ bếp -> nữ 28-35t; mỹ phẩm -> nữ 20-25t).
                - Nhận diện đúng đại từ (Đồ công nghệ: 'em' - 'anh em/các bác'; đồ bếp: 'em' - 'các chị em').
                
                BẮT BUỘC TRẢ VỀ JSON:
                {{
                    "content_analysis": {{
                        "self_pronoun": "em",
                        "audience_pronoun": "anh em hoặc các chị em",
                        "setting_archetype": "Bối cảnh chuẩn mực đời thực phù hợp sản phẩm",
                        "is_fixed_location": true,
                        "koc_demographic_analysis": {{
                            "gender": "male hoặc female",
                            "persona_vi": "Mô tả KOC tiếng Việt",
                            "persona_en": "a 24-year-old native Vietnamese young man"
                        }},
                        "exact_original_price_ocr": "Giá gốc OCR",
                        "exact_sale_price_ocr": "Giá sale OCR",
                        "original_price_spoken": "giá gốc bằng chữ",
                        "sale_price_spoken": "giá sale bằng chữ",
                        "target_audience": "Tệp khách hàng mục tiêu",
                        "core_value": "Giá trị cốt lõi",
                        "pain_points": "Nỗi đau thực tế",
                        "hook_element": "Yếu tố giật gân 3 giây đầu",
                        "recommended_format": "Hình thức đề xuất",
                        "format_reason": "Lý do đề xuất",
                        "hero_sku_color": "Mã màu Hero SKU",
                        "color_palette": "Bảng màu toàn bộ",
                        "what_and_unique": "[Tên sản phẩm]: [Điểm độc bản USP]",
                        "target_user": "Đối tượng phù hợp nhất",
                        "why_buy": "Lý do thuyết phục nên mua",
                        "where_and_convenience": "Hoàn cảnh ứng dụng và sự tiện lợi",
                        "product_dimensions": "Kích thước đời thực"
                    }},
                    "outlines": [
                        {{ "id": 1, "title": "Tên kịch bản 1", "setting": "Bối cảnh 1...", "hook": "Câu hook 1...", "actors": {num_chars} }},
                        {{ "id": 2, "title": "Tên kịch bản 2", "setting": "Bối cảnh 2...", "hook": "Câu hook 2...", "actors": {num_chars} }},
                        {{ "id": 3, "title": "Tên kịch bản 3", "setting": "Bối cảnh 3...", "hook": "Câu hook 3...", "actors": {num_chars} }},
                        {{ "id": 4, "title": "Tên kịch bản 4", "setting": "Bối cảnh 4...", "hook": "Câu hook 4...", "actors": {num_chars} }},
                        {{ "id": 5, "title": "Tên kịch bản 5", "setting": "Bối cảnh 5...", "hook": "Câu hook 5...", "actors": {num_chars} }}
                    ]
                }}
                """
                payload = ["IMAGES:"] + [types.Part.from_bytes(data=cb, mime_type=cm) for cb, cm in st.session_state["saved_reference_images"]]
                for c in char_inputs:
                    if c.get("file"):
                        cb, cm = compress_image_bytes(c['file'], 768, 75)
                        payload.extend([f"ACTOR {c['id']}:", types.Part.from_bytes(data=cb, mime_type=cm)])
                payload.append(prompt)
                
                res = call_gemini(payload, get_sys_inst_outlines(mode, style, "On-camera", char_rules, num_chars, initial_angle, custom_note.strip(), selected_presentation_format))
                st.session_state.content_analysis = res.get("content_analysis")
                outlines = res.get("outlines", [])
                for o in outlines:
                    o["hook"] = clean_and_normalize_voiceover(o.get("hook", ""))
                    o.update({"actors": num_chars, "character_profiles": st.session_state.character_profiles, "presentation_format": selected_presentation_format})
                st.session_state.update({"all_scripts": outlines, "cloned_scripts": [], "expanded_scripts": [], "generated_details": {}, "active_script_id": None})
                st.toast("✅ Đã thiết lập kịch bản hoàn hảo!"); st.rerun()
            except Exception as e: st.error(f"❌ Lỗi: {e}")

# ==============================================================================
# BẢNG PHÂN TÍCH DNA ĐỐI XỨNG
# ==============================================================================
ca = st.session_state.content_analysis
if isinstance(ca, dict):
    st.divider()
    st.markdown("### 🔍 **Phân Tích Chi Tiết**")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(clean_html(f"""
        <div class="dna-card">
            <div class="dna-card-title">🎯 1. Chân dung Khách hàng & Hook 3s</div>
            <div class="dna-row"><span class="dna-label">👥 Tệp khách hàng:</span><span class="dna-text">{clean_analysis_text(ca.get('target_audience', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">💔 Nỗi đau thực tế:</span><span class="dna-text">{clean_analysis_text(ca.get('pain_points', ''))}</span></div>
            <div class="dna-row"><span class="dna-label" style="color:#d90429;">⚡ Yếu tố Hook 3s:</span><span class="dna-text" style="color:#d90429; font-weight:600;">{clean_analysis_text(ca.get('hook_element', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">🎬 Hình thức tối ưu:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{clean_analysis_text(ca.get('recommended_format', 'Review'))}</span></div>
        </div>
        """), unsafe_allow_html=True)
    with c2:
        koc_desc = ca.get('koc_demographic_analysis', {}).get('persona_vi', 'Tự động chọn') if isinstance(ca.get('koc_demographic_analysis'), dict) else 'Tự động chọn'
        user_actors = [p['role'] for p in st.session_state.get('character_profiles', []) if str(p.get('role', '')).strip()]
        koc_display = f"👤 {', '.join(user_actors)} (User chỉ định)" if user_actors else f"🤖 {koc_desc} (AI đề xuất)"
        st.markdown(clean_html(f"""
        <div class="dna-card">
            <div class="dna-card-title">🔥 2. Diễn Viên KOC & Mã Màu</div>
            <div class="dna-row"><span class="dna-label">🎭 Chân dung KOC:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{koc_display}</span></div>
            <div class="dna-row"><span class="dna-label">⭐ SKU ưu tiên:</span><span class="dna-text" style="color:#dc2626; font-weight:700;">{clean_analysis_text(ca.get('hero_sku_color', 'Tự động'))}</span></div>
            <div class="dna-row"><span class="dna-label">🗣 Nhân xưng:</span><span class="dna-text" style="color:#15803d; font-weight:700;">'{ca.get('self_pronoun')}' - '{ca.get('audience_pronoun')}'</span></div>
            <div class="dna-row"><span class="dna-label">🏙 Bối cảnh chuẩn:</span><span class="dna-text">{clean_analysis_text(ca.get('setting_archetype', ''))}</span></div>
        </div>
        """), unsafe_allow_html=True)

# ==============================================================================
# DANH SÁCH KỊCH BẢN & CHI TIẾT PHÂN CẢNH
# ==============================================================================
all_sc = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
if all_sc:
    st.divider()
    def is_generated(sc_id): return (int(sc_id) in st.session_state.generated_details or str(sc_id) in st.session_state.generated_details)

    if st.session_state.active_script_id is not None:
        active_id = st.session_state.active_script_id
        asc = st.session_state.generated_details.get(int(active_id), st.session_state.generated_details.get(str(active_id), {}))
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(asc.get('title', '')).upper()}**")
        st.markdown(f"<div class='detail-header-box'>{asc.get('director_summary', '')}</div>", unsafe_allow_html=True)
        
        for idx, scn in enumerate(asc.get("scenes", []), 1):
            vo_text = scn.get('voiceover', '')
            st.markdown(f"#### 📍 Phân cảnh {idx} - Giai đoạn {scn.get('aida_stage')}")
            st.markdown(f"<span class='timing-badge'>⏱ Thời lượng: {scn.get('dur')} | Nhịp đọc: ~{scn.get('actual_speech_sec')}s</span>", unsafe_allow_html=True)
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting_en')}* | **Âm thanh Foley:** *{scn.get('sfx')}*")
            st.markdown(f"**💬 Thoại trực tiếp:** <div class='voiceover-text'>{vo_text}</div>", unsafe_allow_html=True)
            
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                st.markdown("**🖼 Prompt Ảnh (Midjourney):**")
                st.code(scn.get('img_p', ''), language="text")
                safe_copy_button(scn.get('img_p', ''), f"📋 Sao Chép Ảnh Cảnh {idx}")
            with c_p2:
                st.markdown("**🎥 Prompt Video (Veo 3 / Kling - Zero BGM & Zero Text):**")
                st.code(scn.get('vid_p', ''), language="text")
                safe_copy_button(scn.get('vid_p', ''), f"📋 Sao Chép Video Cảnh {idx}")
            st.markdown("---")

    pend_sc = [sc for sc in all_sc if not is_generated(sc.get("id"))]
    comp_sc = [sc for sc in all_sc if is_generated(sc.get("id"))]

    if comp_sc:
        st.markdown("### 🎬 **1. Kịch Bản ĐÃ Dựng**")
        for sc in comp_sc:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2.5, 1, 1])
                c1.markdown(f"**#{sc['id']}. {sc.get('title')}**")
                c1.caption(f"⚡ *{sc.get('hook')}*")
                if c2.button("👁 Xem lại", key=f"r_{sc['id']}", use_container_width=True):
                    st.session_state.active_script_id = int(sc['id']); st.rerun()
                if c3.button("🚀 Nhân bản", key=f"c_{sc['id']}", type="primary", use_container_width=True):
                    st.session_state.cloned_scripts.extend(clone_script(sc['id'])); st.rerun()

    if pend_sc:
        st.markdown("### ⏳ **2. Kịch Bản Chờ Dựng**")
        for sc in pend_sc:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1.2])
                c1.markdown(f"**#{sc['id']}. {sc.get('title')}** <span class=badge-pending>CHỜ DỰNG</span>", unsafe_allow_html=True)
                c1.caption(f"⚡ *{sc.get('hook')}*")
                if c2.button("✨ Tạo chi tiết ngay", key=f"cr_{sc['id']}", type="secondary", use_container_width=True):
                    with st.spinner("⏳ Đang dựng 4 cảnh chuẩn hóa..."):
                        create_scene_details(sc['id'], mode, style)
                        st.session_state.active_script_id = int(sc['id']); st.rerun()

    st.divider()
    st.markdown("### ➕ **Gọi Thêm 5 Kịch Bản Mới**")
    cg1, cg2 = st.columns([2, 1])
    c_ang = cg1.selectbox("🧭 Chiến lược mới:", ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến"], key=f"ea_{st.session_state.reset_key}")
    ex_note = cg2.text_input("Ghi chú bổ sung:")
    if st.button("🚀 Gọi Thêm 5 Kịch Bản", type="primary", use_container_width=True):
        st.session_state.expanded_scripts.extend(generate_more_scripts(c_ang, 1, [], "On-camera", "10s", st.session_state.character_profiles, ex_note, selected_presentation_format))
        st.toast("✅ Đã sinh thêm 5 kịch bản!"); st.rerun()
