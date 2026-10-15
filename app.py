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
    .detail-header-box { background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%); border: 1.5px solid #bfdbfe; border-radius: 12px; padding: 16px 20px; margin-bottom: 22px; color: #1e3a8a; line-height: 1.8; box-shadow: 0 3px 10px rgba(0,0,0,0.03); }
    .voiceover-text { color: #15803d; background: #f0fdf4; padding: 12px 14px; border-radius: 8px; font-size: 15.5px; border: 1px solid #bbf7d0; display: block; width: 100%; margin-top: 4px; line-height: 1.8; white-space: pre-line; }
    .timing-badge { font-size: 13.5px; font-weight: 700; color: #1e40af; background: #dbeafe; padding: 4px 10px; border-radius: 6px; border: 1px solid #bfdbfe; display: inline-block; margin-bottom: 6px; }
    div[data-testid="stFileUploader"] section { padding: 4px; min-height: 2rem; border: 1.5px dashed #cbd5e1 !important; background-color: #f8fafc !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div { background-color: #f8fafc !important; border: 1.5px solid #cbd5e1 !important; border-radius: 8px !important; }
    .dna-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 20px; margin-bottom: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.02); }
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
    rate = 5.0 if is_tiktok_shop else 4.2
    comma_pause = 0.08 if is_tiktok_shop else 0.12
    period_pause = 0.12 if is_tiktok_shop else 0.20
    duration = (words / rate) + (commas * comma_pause) + (periods * period_pause)
    return round(duration, 1)

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

# ==============================================================================
# BỘ LỌC BẢN QUYỀN BÊN THỨ BA (THIRD-PARTY IP RIGHTS SAFEGUARD)
# ==============================================================================
def sanitize_third_party_ip(text: str) -> str:
    if not text: return ""
    cleaned = text
    platforms = [r'\btiktok\s*(?:shop)?\b', r'\bshopee\b', r'\blazada\b', r'\bfacebook\b', r'\binstagram\b', r'\byoutube\b']
    for p in platforms:
        cleaned = re.sub(p, 'commercial marketplace', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:emoon|disney|marvel|spider-?man|spiderman|nike|apple|samsung|lego|barbie)\b', 'custom premium brand', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bin\s+logo\s+voi\s+con\s+màu\s+cam\s+emoon\b', 'featuring a minimalist cute stylized cartoon mascot graphic and clean brand typography', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\borange\s+elephant\s+emoon\s+logo\b', 'minimalist stylized cartoon mascot emblem with clean typography', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bspider-?man\s+(?:face|badge|figure)\b', 'stylized cute heroic cartoon mascot emblem', cleaned, flags=re.IGNORECASE)
    return cleaned

# ==============================================================================
# BỘ CHUẨN HÓA 100% TIẾNG HÀ NỘI CHUẨN (DIỆT TUYỆT ĐỐI TỪ 'NGÀN' & 'TRỢ GIÁ')
# ==============================================================================
POLICY_REPLACEMENTS = {
    r'\btuyệt\s*đối\b': 'rất', r'\bhoàn\s*toàn\b': 'thực sự', r'\b100\s*%\b': 'rất nhiều',
    r'\bchắc\s*chắn\b': 'rất có thể', r'\bcam\s*kết\b': 'an tâm', r'\bdứt\s*điểm\b': 'cải thiện',
    r'\bđặc\s*trị\b': 'hỗ trợ', r'\bkhỏi\s*hẳn\b': 'đỡ hẳn', r'\bvĩnh\s*viễn\b': 'lâu dài',
    r'\bchuẩn\s*đét\b': 'vừa vặn', r'\bchữa\s*khỏi\b': 'hỗ trợ', r'\bthần\s*dược\b': 'bí quyết',
    r'\btốt\s*nhất\b': 'rất tốt', r'\bsố\s*1\b': 'hàng đầu', r'\btrắng\s*cấp\s*tốc\b': 'sáng khỏe tự nhiên',
    r'\bgiảm\s*béo\s*cấp\s*tốc\b': 'vóc dáng thon gọn', r'\bxóa\s*sạch\s*nám\b': 'mờ thâm sạm',
    r'\bthuốc\s*trị\b': 'sản phẩm hỗ trợ', r'\bđiều\s*trị\b': 'hỗ trợ cải thiện', r'\btriệt\s*để\b': 'hiệu quả',
    r'\btrợ\s*giá\b': 'giảm giá sâu có hạn',
    r'\bphiên\s*live\b': 'đợt này',
    r'\btrên\s*live\b': 'đợt ưu đãi này',
    r'\blivestream\b': 'chương trình ưu đãi'
}

SOUTHERN_TO_HANOI = {
    r'\bngàn\b': 'nghìn',
    r'\bngàn\s+đồng\b': 'nghìn đồng',
    r'\bmấy\s+ngàn\b': 'mấy nghìn',
    r'\btrăm\s+ngàn\b': 'trăm nghìn',
    r'\bchục\s+ngàn\b': 'chục nghìn',
    r'\bvài\s+ngàn\b': 'vài nghìn',
    r'\bxài\b': 'dùng', r'\bbận\s+đồ\b': 'mặc đồ', r'\bbận\s+áo\b': 'mặc áo', r'\bbận\s+quần\b': 'mặc quần',
    r'\bbận\s+váy\b': 'mặc váy', r'\bly\s+nước\b': 'cốc nước', r'\bly\s+trà\b': 'cốc trà', r'\bly\s+đá\b': 'cốc đá',
    r'\bly\b(?=\s+(?:uống|nước|thủy tinh|nhựa))': 'cốc', r'\bmuỗng\b': 'thìa', r'\bgiùm\b': 'hộ', r'\bdùm\b': 'hộ',
    r'\btui\b': 'tôi', r'\bhén\b': 'nhỉ', r'\bnghen\b': 'nhé', r'\bhen\b': 'nhé', r'\brùi\b': 'rồi',
    r'\bmần\b': 'làm', r'\bkiếng\b': 'kính', r'\bđậu\s+phộng\b': 'lạc', r'\btrái\s+cây\b': 'hoa quả',
    r'\bhổng\b': 'không', r'\bthiệt\b': 'thật', r'\bmắc\s+cỡ\b': 'ngại', r'\bhết\s+sẩy\b': 'tuyệt cú mèo',
    r'\brẻ\s+bèo\b': 'rẻ thế', r'\bquá\s+trời\b': 'rất nhiều', r'\bquá\s+chừng\b': 'rất nhiều', r'\bnè\b': 'này', r'\bnha\b': 'nhé'
}

def normalize_hanoi_dialect(text: str) -> str:
    if not text: return ""
    cleaned = text
    for pattern, rep in SOUTHERN_TO_HANOI.items():
        cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    return cleaned

def sanitize_policy_text(text: str) -> str:
    if not text: return ""
    cleaned = normalize_hanoi_dialect(text)
    for pattern, rep in POLICY_REPLACEMENTS.items():
        cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bngàn\b', 'nghìn', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\btrợ\s*giá\b', 'giảm giá sâu có hạn', cleaned, flags=re.IGNORECASE)
    return cleaned

def sanitize_veo3_prompt(prompt_text: str) -> str:
    if not prompt_text: return ""
    p = re.sub(r'\bunzipping\s+(?:front\s+)?(?:zipper\s+)?(?:halfway\s+)?(?:on\s+)?chest\b', 'smoothly demonstrating the durable front zipper', prompt_text, flags=re.IGNORECASE)
    p = re.sub(r'\bparting\s+(?:front\s+)?lapel\b', 'displaying the jacket inner lining cleanly', p, flags=re.IGNORECASE)
    p = re.sub(r'\brevealing\b', 'showing', p, flags=re.IGNORECASE)
    p = re.sub(r'\bundressing\b', 'wearing outerwear', p, flags=re.IGNORECASE)
    p = re.sub(r'\btouching\s+(?:the\s+)?child\b', 'standing gently beside child', p, flags=re.IGNORECASE)
    p = re.sub(r'\bgesturing\s+(?:warmly\s+)?(?:downward\s+)?(?:toward\s+)?(?:lower\s+)?(?:left\s+)?corner\b', 'sharing recommendations warmly with a welcoming open-palm hand gesture', p, flags=re.IGNORECASE)
    p = re.sub(r'\bpointing\s+(?:downward\s+)?(?:to\s+)?(?:corner|cart)\b', 'speaking with gentle welcoming open hands', p, flags=re.IGNORECASE)
    return sanitize_third_party_ip(p)

def clean_analysis_text(text) -> str:
    if not text: return ""
    if isinstance(text, (dict, list)):
        return format_analysis_field(text)
    pattern = r'^(?:SẢN PHẨM LÀ GÌ\s*&?\s*(?:CÓ GÌ ĐẶC BIỆT)?|SẢN PHẨM DÀNH CHO AI|TẠI SAO NÊN MUA|DÙNG Ở ĐÂU\s*&?\s*(?:TIỆN LỢI LÀ GÌ)?|CÁCH SỬ DỤNG|THAO TÁC.*|MỤC ĐÍCH|ĐỐI TƯỢNG|LÝ DO MUA)\s*:\s*'
    res = re.sub(pattern, '', str(text).strip(), flags=re.IGNORECASE).strip()
    return sanitize_policy_text(res)

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict): 
        return "<br>".join([f"<span class='dna-label'>{str(k).replace('_', ' ').title()}:</span> <span class='dna-text'>{clean_analysis_text(v)}</span>" for k, v in field_val.items()])
    if isinstance(field_val, list): 
        return "<br>".join([f"<div class='dna-bullet'>• <span class='dna-text'>{clean_analysis_text(item)}</span></div>" for item in field_val])
    val_str = clean_analysis_text(str(field_val))
    return "".join([f"<div class='dna-bullet'>• <span class='dna-text'>{line.strip()}</span></div>" for line in val_str.split('<br>') if line.strip()])

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
    if datetime.now() > datetime.strptime(acc.get("expires_at", "2099-12-31"), "%Y-%m-%d"):
        return False, "Tài khoản đã hết hạn."
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

def safe_copy_button(text_to_copy: str, button_label: str = "📋 Sao Chép Prompt"):
    b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    html_id = f"btn_{int(time.time()*10000)}_{len(text_to_copy)}"
    html_code = f"""
    <button id="{html_id}" style="background:#16a34a; color:white; border:none; padding:8px 16px; font-size:13px; font-weight:700; border-radius:6px; cursor:pointer; width:100%; transition: 0.2s;">{button_label}</button>
    <script>
    document.getElementById("{html_id}").addEventListener("click", function() {{
        const text = decodeURIComponent(escape(atob("{b64}")));
        navigator.clipboard.writeText(text).then(() => {{
            document.getElementById("{html_id}").innerText = "✅ Đã sao chép!";
            setTimeout(() => {{ document.getElementById("{html_id}").innerText = "{button_label}"; }}, 2000);
        }}).catch(() => {{
            const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta); ta.select();
            document.execCommand('copy'); document.body.removeChild(ta);
            document.getElementById("{html_id}").innerText = "✅ Đã sao chép!";
        }});
    }});
    </script>
    """
    components.html(html_code, height=45)

# ==============================================================================
# KHỞI TẠO STATE & KIỂM SOÁT TIẾN TRÌNH TOÀN CỤC
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
    ("target_duration_instruction", ""), ("character_profiles", []), ("current_project_id", None),
    ("saved_reference_images", []), ("show_all_projects", False), ("show_all_admin_accounts", False),
    ("current_processing_id", None), ("current_cloning_id", None)
]:
    if key not in st.session_state: st.session_state[key] = default_val

is_system_busy = (
    st.session_state.get("current_processing_id") is not None or 
    st.session_state.get("current_cloning_id") is not None
)

if is_system_busy: lock_ui()

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
    components.html("""<script>setTimeout(() => { var el = window.parent.document.getElementById('detailed-view-anchor'); if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); } else { window.parent.scrollTo({top: 400, behavior: 'smooth'}); } }, 300);</script>""", height=0)
    st.session_state.scroll_to_detail = False

def repair_and_parse_json(text_content: str):
    if not text_content: raise Exception("AI không phản hồi nội dung. Vui lòng bấm tạo lại.")
    cleaned = re.sub(r'```(?:json)?', '', text_content).strip()
    try: return json.loads(cleaned, strict=False)
    except: pass

    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    if match:
        try: return json.loads(match.group(0), strict=False)
        except: pass

    candidate = cleaned
    fb = candidate.find('{')
    if fb != -1: candidate = candidate[fb:]
    if len(re.findall(r'(?<!\\)"', candidate)) % 2 != 0: candidate += '"'
    open_curly = candidate.count('{') - candidate.count('}')
    open_square = candidate.count('[') - candidate.count(']')
    candidate += (']' * max(0, open_square)) + ('}' * max(0, open_curly))
    try: return json.loads(candidate, strict=False)
    except: pass

    try:
        py_str = candidate.replace('true', 'True').replace('false', 'False').replace('null', 'None')
        parsed = ast.literal_eval(py_str)
        return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict) else parsed
    except: pass
    raise Exception("AI sinh JSON lỗi cấu trúc. Vui lòng bấm tạo lại.")

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
                err_str = str(e).lower()
                if "404" in err_str or "not_found" in err_str: break
                if "503" in err_str or "unavailable" in err_str or "429" in err_str or "resource_exhausted" in err_str:
                    time.sleep((attempt + 1) * 2.0); continue
                time.sleep(1.0)
    if last_exception:
        if "503" in str(last_exception) or "unavailable" in str(last_exception).lower():
            raise Exception("Máy chủ AI của Google đang bị quá tải tạm thời (503). Vui lòng đợi 5-10 giây rồi bấm tạo lại.")
        raise last_exception

def build_voice_direction(mode, num_chars, character_profiles):
    is_tiktok_shop = ("Viral" not in mode)
    speed_txt = "tốc độ BẮN TỈA DỒN DẬP (4.8 - 5.2 từ/s), rướn người, cử chỉ tay chém nhịp dứt khoát" if is_tiktok_shop else "tốc độ tự nhiên, biến thiên cảm xúc linh hoạt"
    if num_chars <= 1:
        return f"Nhân vật nói trực tiếp (On-camera): 100% Giọng [Nam/Nữ] HÀ NỘI CHUẨN bản địa đúng độ tuổi, phát âm tròn vành rõ chữ, {speed_txt}. Giữ nguyên duy nhất một phong thái giọng Hà Nội nhất quán suốt 4 cảnh."
    dirs = []
    for p in character_profiles:
        r = str(p.get('role', '')).lower()
        if any(k in r for k in ["bé", "con", "trẻ", "nhỏ", "gái", "trai", "thiếu nhi"]):
            dirs.append(f"• NV {p['id']} ({p['role']}): 100% Giọng THIẾU NHI HÀ NỘI CHUẨN đúng độ tuổi, trong trẻo, líu lo, ngây thơ, xưng con/cháu, nhất quán suốt video.")
        elif any(k in r for k in ["ông", "bà", "già", "cao tuổi"]):
            dirs.append(f"• NV {p['id']} ({p['role']}): 100% Giọng NGƯỜI CAO TUỔI HÀ NỘI CHUẨN đúng độ tuổi, từ tốn, đôn hậu, trầm ấm, phúc hậu, nhất quán suốt video.")
        elif any(k in r for k in ["bố", "ba", "chồng", "nam", "anh", "bác trai"]):
            dirs.append(f"• NV {p['id']} ({p['role']}): 100% Giọng NAM HÀ NỘI CHUẨN đúng độ tuổi, trầm ấm, chững chạc, nội lực, đĩnh đạc, nhất quán suốt video.")
        else:
            dirs.append(f"• NV {p['id']} ({p['role']}): 100% Giọng NỮ HÀ NỘI CHUẨN đúng độ tuổi, thanh lịch, ngọt ngào, dịu dàng, âm sắc trong sáng, nhất quán suốt video.")
    return " | ".join(dirs)

def generate_char_rules_string(profiles):
    if not profiles: return "100% người Việt Nam bản địa, tóc đen tuyền tự nhiên, khóa duy nhất 1 kiểu tóc suốt 4 cảnh."
    rules = "DANH SÁCH DIỄN VIÊN (KHÓA 100% NGƯỜI VIỆT & DIỆN MẠO BẤT BIẾN SUỐT 4 CẢNH):\n"
    for p in profiles: 
        rules += f" - Diễn viên {p['id']} ({p['role']}): 100% thuần Việt, tóc đen tuyền tự nhiên. KHÓA DUY NHẤT 1 MÀU TÓC ĐEN TUYỀN, 1 KIỂU TÓC VÀ 1 KHUÔN MẶT XUYÊN SUỐT 4 CẢNH.\n"
    return rules

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, angle):
    is_multi = (num_chars >= 2)
    format_direction = f"ĐỊNH DẠNG: TIỂU PHẨM ĐỐI THOẠI {num_chars} NHÂN VẬT THUẦN VIỆT NÓI TRỰC TIẾP." if is_multi else "ĐỊNH DẠNG: ĐỘC THOẠI KOC THUẦN VIỆT NÓI TRỰC TIẾP."
    strat_cmd = "BẠN PHẢI MIX ĐA DẠNG 5 GÓC ĐỘ NỘI DUNG." if "Tự động mix" in angle else f"VIẾT CẢ 5 KỊCH BẢN THEO: '{angle}'."
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL TIKTOK SHOP & VIRAL TRIỆU VIEW. PHONG CÁCH: {style}
    {strat_cmd} | {format_direction}
    
    🛑 YÊU CẦU ĐA DẠNG HÓA 5 BỐI CẢNH HOÀN TOÀN KHÁC NHAU:
    - BẮT BUỘC mỗi kịch bản trong 5 kịch bản phải diễn ra ở 1 BỐI CẢNH ĐỜI THỰC KHÁC NHAU (tuyệt đối không trùng lặp bối cảnh giữa 5 kịch bản).
    - Phân tích linh hoạt theo đúng thực tế sản phẩm và góc độ kịch bản:
      • Kịch bản 1: Không gian phòng ngủ gia đình (nỗi đau đêm khuya, giấc ngủ, con quấy khóc...).
      • Kịch bản 2: Góc bếp hoặc bàn ăn gia đình lúc chuẩn bị đồ dùng / ăn uống.
      • Kịch bản 3: Bàn làm việc công sở / văn phòng tranh thủ giờ giải lao.
      • Kịch bản 4: Phòng khách ấm cúng hoặc ban công thoáng đãng.
      • Kịch bản 5: Không gian chuẩn bị ra ngoài dạo phố hoặc kho hàng TMĐT đóng gói tấp nập (nếu là Flash Sale).
    - TUYỆT ĐỐI KHÔNG KHÓA CỨNG vào bất kỳ bối cảnh đơn lẻ nào!

    🛑 CƯỠNG CHẾ 100% GIỌNG HÀ NỘI CHUẨN ĐÚNG ĐỘ TUỔI NÓI TRỰC TIẾP (ON-CAMERA LIP-SYNC DIALOGUE):
    - CẤM TUYỆT ĐỐI TỪ 'NGÀN'. 100% BẮT BUỘC DÙNG TỪ 'NGHÌN' (ví dụ: 'mấy chục nghìn', 'trăm nghìn').
    - CẤM TUYỆT ĐỐI TỪ 'TRỢ GIÁ', 'PHIÊN LIVE', 'TRÊN LIVE' (tránh bị AI nền tảng phạt hiểu nhầm là livestream).
    - CẤM TUYỆT ĐỐI TỪ NGỮ VÀ KHẨU NGỮ MIỀN NAM: CẤM 'xài', 'nè', 'nha', 'nghen', 'hén', 'tui', 'bận đồ', 'ly nước', 'muỗng', 'dùm', 'giùm', 'rùi', 'mần', 'thiệt', 'hổng'.
    - BẮT BUỘC 100% khẩu ngữ Hà Nội chuẩn: 'dùng', 'này', 'nhé', 'nhỉ', 'tôi/mình', 'mặc đồ', 'cốc nước', 'thìa', 'hộ/giúp', 'rồi', 'thật', 'không'.
    - TUYỆT ĐỐI KHÔNG CÓ GIỌNG THUYẾT MINH NGOÀI (NO OFF-SCREEN NARRATOR).
    🛑 BỘ LỌC CHÍNH SÁCH ĐA NGÀNH HÀNG:
    - CẤM: 'tuyệt đối', 'hoàn toàn', '100%', 'cam kết', 'dứt điểm', 'đặc trị', 'khỏi hẳn', 'vĩnh viễn'.
    - AN TOÀN TRẺ EM: Trẻ em LUÔN CÓ NGƯỜI LỚN KỀ BÊN trong mọi cảnh, TUYỆT ĐỐI CẤM để bé một mình trong khung hình.
    - DƯỢC / TPCN: Không nhận là thuốc điều trị, chỉ dùng từ 'hỗ trợ', 'bổ sung'.
    🛑 100% NGƯỜI VIỆT THUẦN TÚY: Tuyệt đối cấm mặt ngoại quốc.
    🛑 {char_rules}
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction, num_chars, character_profiles):
    is_multi = (num_chars >= 2)
    voice_guidance = build_voice_direction(mode, num_chars, character_profiles)
    dialogue_type_rule = f"🛑 ĐỐI THOẠI {num_chars} NHÂN VẬT: Tách từng câu thoại nói trực tiếp (Mẹ: '...' | Bé: '...'). Giọng thiếu nhi Hà Nội ngây thơ, mẹ dịu dàng đúng độ tuổi." if is_multi else "🛑 ĐỘC THOẠI KOC: Lời thoại liền mạch do chính KOC mở miệng nói trực tiếp trước ống kính, tốc độ bắn tỉa 4.8 - 5.2 từ/s."
    outro_instruction = "🛑 CẢNH 4 (VIRAL): Cả nhà cười tươi vẫy tay chào camera, mời follow." if "Viral" in mode else "🛑 CẢNH 4 (TIKTOK SHOP): Kêu gọi mua hàng ấm áp, chốt deal giá sốc kèm câu rào miễn trừ giá có hạn."

    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL TIKTOK SHOP ĐA GIÁC QUAN (AUDIO-VISUAL MASTER). PHONG CÁCH: {style}
    CHỈ ĐẠO GIỌNG: {voice_guidance}
    {dialogue_type_rule}
    {outro_instruction}
    
    🛑 CƯỠNG CHẾ 100% CẢ 4 CẢNH (CẢNH 1, 2, 3, 4) LÀ NHÂN VẬT MỞ MIỆNG NÓI TRỰC TIẾP TRƯỚC CAMERA (ON-CAMERA LIP-SYNC DIALOGUE):
    - TUYỆT ĐỐI CẤM VĂN PHONG THUYẾT MINH / LỒNG TIẾNG NGOÀI (NO OFF-SCREEN NARRATION / NO VOICE-OVER) Ở CẢNH 2 VÀ MỌI CẢNH!
    - ĐẶC BIỆT Ở CẢNH 2 (INTEREST): 
      • CẤM viết câu thoại mô tả tính năng kiểu người thứ ba hay đọc sách hướng dẫn sử dụng ("Sản phẩm này được thiết kế...", "Với cơ chế...").
      • BẮT BUỘC KOC trực tiếp xưng hô (mình/tôi/em/mẹ), nói chuyện tâm sự tự nhiên với người xem: "Đấy, mọi người nhìn kỹ hộ em chỗ này này...", "Điểm ăn tiền nhất mà mình thấy chính là...".
      • GÓC MÁY CẢNH 2: Phải là Trung cận cảnh (Medium Close-up), thấy rõ cả KHUÔN MẶT ĐANG NÓI CÓ KHẨU HÌNH KHỚP LỜI THOẠI lẫn ĐÔI BÀN TAY đang cầm thao tác sản phẩm ngang ngực. CẤM chỉ quay mỗi bàn tay tách rời mặt!
    - ĐỒNG NHẤT 100% CHẤT GIỌNG, TÔNG GIỌNG, ĐỘ TUỔI VÀ KIỂU THOẠI XUYÊN SUỐT CẢ 4 CẢNH (Cùng 1 người nói, cùng 1 cao độ, cùng 1 nhịp điệu 4.8 - 5.2 từ/s giọng Hà Nội chuẩn).

    🛑 BỘ ĐÔI HOOK HOÀN HẢO Ở CẢNH 1: VISUAL HOOK (MẮT NHÌN) + AUDIO HOOK (TAI NGHE):
    - CẢNH 1 THIẾT KẾ THEO KỸ THUẬT 2 NHỊP:
      • Nhịp 1 (0.0s - 1.5s) - Visual Hook Impact: Máy quay góc hẹp kéo nhanh (Fast push-in). Thực hiện ngay một hành động thị giác giật gân (Visual Stress Test / Tactile Flex / Tái hiện nỗi đau) đi kèm âm thanh SFX whoosh mở màn + âm thanh va chạm thực tế.
      • Nhịp 2 (1.5s - 6.0s) - Voice Hook & Lip-sync: Chuyển sang góc trung cảnh ấm áp, nhân vật nhìn thẳng vào camera, mở miệng nói câu thoại Giọng Hà Nội chuẩn kết nối trực tiếp với hành động vừa diễn ra ở Nhịp 1.

    🛑 PHÂN BIỆT RÕ RÀNG: SẢN PHẨM PHỐI ĐỒ THỜI TRANG (FASHION STYLING) VS SẢN PHẨM THƯỜNG:
    1. NẾU LÀ SẢN PHẨM THỜI TRANG & NỘI DUNG LÀ PHỐI ĐỒ (LOOKBOOK, GỢI Ý CÁCH MẶC THEO HOÀN CẢNH):
       - 'is_fashion_styling' = true.
       - KHUÔN MẶT, MÀU TÓC ĐEN TUYỀN, KIỂU TÓC, TUỔI TÁC: KHÓA BẤT BIẾN 100% (cùng 1 người mẫu duy nhất).
       - TRANG PHỤC ('scene_outfit_en'): CHO PHÉP VÀ BẮT BUỘC THAY ĐỔI THEO TỪNG CẢNH ĂN KHỚP VỚI CÂU THOẠI (Ví dụ: Cảnh 1 áo phối quần âu đi làm, Cảnh 3 phối chân váy đi dạo phố).
    2. NẾU LÀ CÁC SẢN PHẨM KHÁC (GIA DỤNG, MẸ VÀ BÉ, CÔNG NGHỆ, MỸ PHẨM...) HOẶC THỜI TRANG MẶC 1 BỘ:
       - 'is_fashion_styling' = false.
       - TRANG PHỤC KHÓA BẤT BIẾN 100% CẢ 4 CẢNH dựa trên hoàn cảnh thực tế (ở nhà thì mặc đồ ở nhà đồng nhất, đi làm thì mặc đồ công sở đồng nhất suốt 4 cảnh).

    🛑 BỐI CẢNH THỰC TẾ LINH HOẠT THEO LOGIC TỪNG KỊCH BẢN:
    - Bối cảnh phải tự nhiên, ăn khớp với nỗi đau và câu chuyện đời thực.
    - CẢ 4 CẢNH TRONG CÙNG 1 KỊCH BẢN PHẢI GẮN KẾT LOGIC VỚI NHAU.

    🛑 CƠ CHẾ THỜI LƯỢNG ĐỘNG & ĐỆM AN TOÀN TRÁNH CỤT TIẾNG:
    - Tự do gán thời lượng '4s', '6s', '8s' hoặc '10s'.
    - Trần số từ: Khung 4s (tối đa 15-16 từ), Khung 6s (tối đa 22-24 từ), Khung 8s (tối đa 32-34 từ), Khung 10s (tối đa 40-42 từ).

    🛑 KỸ THUẬT KỂ CHUYỆN LIỀN MẠCH, ĐỜI THƯỜNG & ĐÀO SÂU CÔNG NĂNG:
    - 4 cảnh ghép lại thành 1 đoạn văn tâm sự tự nhiên bằng khẩu ngữ Hà Nội chuẩn.
    - Cảnh 4 đủ 3 vế: 
      1. Đòn bẩy giá tương phản linh hoạt: cho phép nói 'khoảng...', 'gần...', 'chưa tới...', 'tầm...' (ví dụ: 'giá gốc gần 200 nghìn, nay giảm chỉ còn khoảng chín mươi mấy nghìn' hoặc 'chưa tới một trăm nghìn').
      2. Câu miễn trừ giá có hạn: CẤM dùng 'trợ giá', dùng 'chương trình giảm giá sâu có hạn theo khung giờ'.
      3. Lời chào ấm áp, thân thiện.

    🛑 CƯỠNG CHẾ 100% GIỌNG HÀ NỘI CHUẨN ĐỒNG NHẤT:
    - 100% dùng từ 'nghìn' (CẤM TUYỆT ĐỐI TỪ 'NGÀN').
    - CẤM TUYỆT ĐỐI TỪ 'TRỢ GIÁ', 'PHIÊN LIVE'.
    - CẤM giọng thuyết minh ngoài. Khẩu hình khớp từng từ với lời thoại.

    🛑 TRIỆT TIÊU TOÀN BỘ ICON GIỎ HÀNG, NÚT BẤM VÀ SUB NỔI.
    - {char_rules}
    """

# ==============================================================================
# HÀM TẠO CHI TIẾT KỊCH BẢN - 100% ON-CAMERA LIP-SYNC & GÓC MÁY CẢNH 2 CHUẨN
# ==============================================================================
def create_scene_details(target_id, mode, style):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if str(sc.get("id")) == str(target_id)), None)
    if not outline: raise Exception(f"Không tìm thấy kịch bản #{target_id} trong danh sách dự án.")
    
    char_profiles = outline.get("character_profiles", st.session_state.get("character_profiles", []))
    char_rules = generate_char_rules_string(char_profiles)
    num_chars = outline.get("actors", outline.get("actor_count", len(char_profiles) if char_profiles else 1))
    
    current_active_mode = mode or st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    is_tiktok_shop = ("Viral" not in current_active_mode)
    voice_guidance = build_voice_direction(current_active_mode, num_chars, char_profiles)
    
    fixed_title = outline.get('title', 'Kịch bản chi tiết')
    fixed_hook = sanitize_policy_text(outline.get('hook', ''))
    fixed_setting_base = outline.get('setting', 'Không gian thực tế phù hợp')
    
    dna = st.session_state.get("content_analysis") or {}
    condensed_dna = {
        "product": dna.get("what_and_unique", ""),
        "hero_sku": dna.get("hero_sku_color", ""),
        "color_lock": dna.get("product_color_lock", ""),
        "dimensions": dna.get("product_dimensions", ""),
        "mechanism": dna.get("lid_mechanism", "Kết cấu cơ học chuẩn xác theo đời thực"),
        "how_to_use": dna.get("how_to_use", "Thao tác sử dụng thực tế chuẩn công thái học"),
        "price_anchor": dna.get("rounded_price_anchor", ""),
        "visual_hook_archetype": dna.get("visual_hook_archetype", "Thử thách thị giác / Tái hiện nỗi đau"),
        "connector_specs": dna.get("flexible_connector_specs", "Không có dây nối"),
        "assembly_structure": dna.get("product_assembly_structure", "Nguyên khối thực tế"),
        "anti_morph_targets": dna.get("strict_anti_morph_targets", "ống tiêm y tế xylanh, que nhựa đơn chiếc"),
        "visual_dna": dna.get("prompt_dna_lock", "")
    }

    prompt_text = f"""
    THÔNG TIN SẢN PHẨM: {json.dumps(condensed_dna, ensure_ascii=False)}
    KỊCH BẢN #{target_id}: TIÊU ĐỀ: '{fixed_title}' | HOOK GỐC: '{fixed_hook}' | BỐI CẢNH KỊCH BẢN NÀY: {fixed_setting_base}
    HÌNH THỨC: 100% Lời thoại do CHÍNH NHÂN VẬT MỞ MIỆNG NÓI TRỰC TIẾP TRƯỚC ỐNG KÍNH (ON-CAMERA LIP-SYNC) TRONG CẢ 4 CẢNH (CẢNH 1, 2, 3, 4). TUYỆT ĐỐI CẤM THUYẾT MINH NGOÀI. TUYỆT ĐỐI CẤM TỪ 'NGÀN' (PHẢI DÙNG TỪ 'NGHÌN'). TUYỆT ĐỐI CẤM TỪ 'TRỢ GIÁ'.
    
    🛑 CHỈ THỊ TRIỆT TIÊU THUYẾT MINH Ở CẢNH 2:
    1. CẢNH 2 PHẢI LÀ KOC TỰ NÓI TRỰC TIẾP: Lời thoại Cảnh 2 là KOC xưng tôi/mình/em, tâm sự chỉ cho người xem thấy chi tiết thực tế ('Đấy, mọi người nhìn kỹ hộ em chỗ này này...', 'Điểm ăn tiền nhất mà mình thấy chính là...'). CẤM viết lời thuyết minh vô hồn!
    2. GÓC MÁY CẢNH 2: Vertical 9:16 Medium Close-up, THẤY RÕ KHUÔN MẶT KOC ĐANG NÓI CÓ KHẨU HÌNH VÀ ĐÔI TAY ĐANG CẦM SẢN PHẨM. CẤM chỉ quay mỗi bàn tay tách rời mặt!
    3. ĐỒNG NHẤT 100% GIỌNG HÀ NỘI CHUẨN XUYÊN SUỐT 4 CẢNH: Cùng 1 người nói, cùng 1 cao độ, cùng 1 nhịp đọc 4.8 - 5.2 từ/s.
    4. CẢNH 1 THIẾT KẾ 2 NHỊP: Visual Hook giật gân (0.0s - 1.5s) + Voice Hook (1.5s - 6.0s). Cảnh 2, 3, 4 thoại bắt đầu ngay từ 0.00s.
    5. NEO GIÁ LINH HOẠT Ở CẢNH 4: Dùng các từ 'khoảng...', 'gần...', 'chưa tới...', 'tầm...'. CẤM TUYỆT ĐỐI từ 'ngàn' và 'trợ giá'.
    6. BỐI CẢNH THỰC TẾ: Bám sát đúng '{fixed_setting_base}' (chiều sâu không gian sinh động, ấm cúng).
    7. ĐÁNH GIÁ CHẾ ĐỘ PHỐI ĐỒ:
       - Nếu là THỜI TRANG PHỐI ĐỒ: 'is_fashion_styling' = true (khuôn mặt & tóc đen tuyền giữ nguyên, outfit 'scene_outfit_en' đổi theo thoại).
       - Nếu là CÁC SẢN PHẨM KHÁC: 'is_fashion_styling' = false (trang phục khóa cứng 1 bộ suốt 4 cảnh).
    8. KHÓA BẤT BIẾN MÀU TÓC & KHUÔN MẶT: 100% tóc đen tuyền tự nhiên ('locked_hair_color'), cùng 1 kiểu tóc, cùng 1 khuôn mặt người Việt.
    9. TRẦN SỐ TỪ AN TOÀN: Cảnh 1 (dưới 24 từ), Cảnh 2 (dưới 34 từ), Cảnh 3 (dưới 42 từ), Cảnh 4 (dưới 32 từ).
    
    ĐỊNH DẠNG JSON TRẢ VỀ:
    {{
        "title": "{fixed_title}",
        "is_fashion_styling": true/false,
        "voice": {{"tone": "{voice_guidance}"}},
        "outfit_vi": "Mô tả chi tiết trang phục phù hợp với bối cảnh {fixed_setting_base}",
        "clean_product_name_en": "Concise photorealistic English description of the hero product under 15 words without proprietary brand names",
        "connector_physics_en": "Detailed English description of flexible tube/cord dimensions, length, diameter, and gravitational droop (if any)",
        "character_matrix": {{
            "full_characters_appearance": "Authentic native Vietnamese character(s), natural Vietnamese facial features, warm skin tone, identical facial bone structure and exact same age across all frames",
            "locked_hairstyles": "Mô tả 1 kiểu tóc cố định chi tiết bằng tiếng Anh",
            "locked_hair_color": "strictly uniform deep natural jet-black hair pigment, completely unaffected by ambient lighting color bleed, zero hair highlights, zero brown tint",
            "locked_tops": "Mô tả mẫu áo chính phù hợp hoàn cảnh {fixed_setting_base}",
            "locked_outer_or_apron": "Mô tả áo khoác/tạp dề nếu có (hoặc 'none')",
            "locked_bottoms": "Mô tả mẫu quần hoặc váy phù hợp",
            "locked_setting": "Mô tả bối cảnh {fixed_setting_base} bằng tiếng Anh với chiều sâu không gian chân thực",
            "locked_negative": "Caucasian, white, blonde hair, blue eyes, yellow cart icon, shopping bag graphic, animated button, simulated UI overlay, subtitles, on-screen text, typography, watermark, wrinkles, deformed hands, extra fingers, product morphing, shape shifting, disappearing label, fading text, blurred sticker, changing hairstyle, different haircut, different hair length, different hair parting, changing face, face morphing, different person, inconsistent actor, inconsistent character, different facial features, altering hairstyle, changing hair color, brown hair, light brown hair, auburn hair, chestnut hair, blonde hair, dyed hair, bleached hair, hair highlights, reddish hair tint, inconsistent hair color"
        }},
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention",
                "dur": "6s",
                "setting": "Mô tả bối cảnh mở màn bám sát {fixed_setting_base}...",
                "setting_en": "Detailed realistic setting description in English based on {fixed_setting_base}",
                "scene_outfit_en": "Mô tả trang phục cho cảnh 1 nếu is_fashion_styling = true",
                "camera_shot": "Vertical 9:16 dynamic two-beat opening: 0.0s-1.5s fast kinetic push-in macro, 1.5s-6.0s warm eye-level medium shot",
                "expression": "0.0s-1.5s biểu cảm kịch tính/bất ngờ, 1.5s-6.0s ánh mắt đồng cảm chân thành nhìn thẳng camera",
                "sfx": "Tiếng whoosh vút mạnh mở màn ở 0.0s kết hợp âm thanh va chạm thực tế (nước sủi bọt/búng nẩy/tiếng gõ) + tiếng thở phào nhẹ nhõm",
                "visual_hook_action": "Mô tả hành động thị giác giật gân ở 0.0s - 1.5s bằng tiếng Việt",
                "action_en": "Two-beat hook action: At 0.00s-1.50s, camera pushes in fast capturing an immediate visual impact (kinetic stress test / tactile demonstration / visceral struggle). At 1.50s-6.00s, character smoothly establishes warm direct eye contact with camera, speaking with natural expressive lip movements.",
                "director": "Attention | Dual-Layer Hook: Nhịp 1 Visual Hook giật gân (0.0s-1.5s) + Nhịp 2 Voice Hook Hà Nội chuẩn (1.5s-6.0s) | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại mở màn tự nhiên dưới 24 từ bằng tiếng Hà Nội chuẩn, dùng từ 'nghìn', khớp với Visual Hook..."
            }},
            {{
                "scene": 2, "aida_stage": "Interest",
                "dur": "8s",
                "setting": "Mô tả bối cảnh góc quay ngang tầm mắt thấy rõ người và bàn thao tác...",
                "setting_en": "Detailed setting description in English for medium close-up",
                "scene_outfit_en": "Mô tả trang phục cho cảnh 2 nếu is_fashion_styling = true",
                "camera_shot": "Vertical 9:16 eye-level medium close-up, clearly framing character's speaking face with moving lips and hands demonstrating the product at chest level",
                "expression": "Ánh mắt bừng sáng, chân mày giãn ra, thần thái hào hứng chia sẻ trực tiếp với người xem",
                "sfx": "Tiếng gõ cộc cộc đanh chắc hoặc tiếng xoay nắp ren khục chắc nịch / tiếng vuốt vải sột soạt ASMR",
                "action_en": "Direct on-camera interaction: Character visibly looks into the camera lens and speaks directly with natural lip-sync mouth movements starting at 0.00s, holding the product at chest level and demonstrating its mechanism with steady five-finger hands.",
                "director": "Interest | Nhân vật nói trực tiếp on-camera lip-sync khớp từ 0.00s (CẤM thuyết minh) | SFX thực tế ASMR | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại KOC nói trực tiếp bằng tiếng Hà Nội chuẩn xưng hô thân mật (ví dụ: 'Đấy, mọi người nhìn kỹ hộ em chỗ này này...') dưới 34 từ..."
            }},
            {{
                "scene": 3, "aida_stage": "Desire",
                "dur": "10s",
                "setting": "Mô tả bối cảnh trải nghiệm thực tế sinh động bám sát {fixed_setting_base}...",
                "setting_en": "Vivid contextual setting in English matching {fixed_setting_base} with realistic depth of field",
                "scene_outfit_en": "Mô tả trang phục phối đồ phong cách mới cho cảnh 3 nếu is_fashion_styling = true",
                "camera_shot": "Vertical 9:16 medium close-up lifestyle experience shot, framing character visibly speaking on camera",
                "expression": "Nụ cười mãn nguyện, ánh mắt ánh lên sự thỏa mãn giác quan, gật đầu khẳng định",
                "sfx": "Tiếng rót nước róc rách đá lạnh lách cách vang giòn / tiếng búng vải nẩy tưng tưng / tiếng ASMR giác quan",
                "action_en": "Direct on-camera lifestyle experience: Character happily speaks directly to the camera with natural lip-sync starting at 0.00s while demonstrating practical benefits in daily routine within {fixed_setting_base}, with identical face and identical deep black hair.",
                "director": "Desire | Nhân vật nói trực tiếp on-camera lip-sync trải nghiệm đời thực sâu sắc | SFX sống động | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại KOC nói trực tiếp đặc tả trải nghiệm thực tế dưới 42 từ nối tiếp tự nhiên từ cảnh 2 bằng tiếng Hà Nội chuẩn..."
            }},
            {{
                "scene": 4, "aida_stage": "Action",
                "dur": "8s",
                "setting": "Mô tả bối cảnh chốt deal ấm áp bám sát {fixed_setting_base}...",
                "setting_en": "Warm commercial setting in English with clean appealing lighting",
                "scene_outfit_en": "Mô tả trang phục chốt deal cho cảnh 4 nếu is_fashion_styling = true",
                "camera_shot": "Vertical 9:16 warm commercial eye-level medium closing shot",
                "expression": "Nụ cười rạng rỡ, ánh mắt chân thành ấm áp, hai bàn tay mở tự nhiên hướng về camera",
                "sfx": "Tiếng chuông ting trong trẻo vui tai kích thích hành động",
                "action_en": "Warm commercial closing shot: Character smiling warmly into camera, speaking directly with sincere welcoming open-palm gestures and clear lip-sync starting at 0.00s.",
                "director": "Action | Nhân vật nói trực tiếp on-camera chốt deal đòn bẩy giá tương phản linh hoạt kèm câu miễn trừ giá hợp quy | SFX chuông ting vui tai | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại chốt deal dưới 32 từ gồm neo giá linh hoạt (dùng 'khoảng...', 'gần...', 'chưa tới...', từ 'nghìn') + câu rào chương trình giảm giá sâu có hạn theo khung giờ (CẤM dùng 'trợ giá') + lời chào ấm áp..."
            }}
        ]
    }}
    """
    res = call_gemini([prompt_text], get_sys_inst_details(current_active_mode, style, "On-camera", char_rules, "Thời lượng động linh hoạt", num_chars, char_profiles), max_tokens=6500)
    if not res: raise Exception("AI không phản hồi hoặc trả về dữ liệu rỗng. Vui lòng bấm tạo lại.")
    
    scenes = res.get("scenes") or res.get("script") or []
    if not scenes: raise Exception("AI không tạo được danh sách phân cảnh. Vui lòng bấm tạo lại.")
    
    c_mat = res.get("character_matrix") or {}
    full_char = c_mat.get("full_characters_appearance") or "Authentic native Vietnamese character(s), natural Vietnamese facial features, warm skin tone, identical facial bone structure and exact same age across all frames"
    locked_hair = c_mat.get("locked_hairstyles") or "natural dark hair styled in a neat tidy hairstyle, strictly invariant"
    locked_hair_color = c_mat.get("locked_hair_color") or "strictly uniform deep natural jet-black hair pigment, completely unaffected by ambient lighting color bleed, zero hair highlights, zero brown tint"
    locked_tops = c_mat.get("locked_tops") or "neat cozy casual top"
    locked_outer = c_mat.get("locked_outer_or_apron") or "none"
    locked_bottoms = c_mat.get("locked_bottoms") or "comfortable trousers"
    default_setting = c_mat.get("locked_setting") or (outline.get("setting") or "warm realistic indoor setting with natural depth of field")
    base_negative = c_mat.get("locked_negative") or "Caucasian, white, blonde hair, blue eyes, yellow cart icon, shopping bag graphic, animated button, simulated UI overlay, subtitles, on-screen text, typography, watermark, wrinkles, deformed hands, extra fingers, product morphing, shape shifting, disappearing label, fading text, blurred sticker, medical syringe, injection needle, single handheld tube without hose, detached hose, vanishing tube, morphed product, changing hairstyle, different haircut, different hair length, different hair parting, changing face, face morphing, different person, inconsistent actor, inconsistent character, different facial features, altering hairstyle, changing hair color, brown hair, light brown hair, auburn hair, chestnut hair, blonde hair, dyed hair, bleached hair, hair highlights, reddish hair tint, inconsistent hair color"
    
    is_fashion_styling = res.get("is_fashion_styling", False)
    clean_prod_en = sanitize_third_party_ip(res.get("clean_product_name_en") or f"authentic {condensed_dna.get('hero_sku', '')} {condensed_dna.get('product', 'product')}".strip())
    connector_physics_en = res.get("connector_physics_en") or "translucent flexible silicone tube approx 20-25cm length, 6-8mm diameter, hanging with a natural loose U-shaped curved droop between hands"
    
    character_base_identity = (
        f"Character Identity Lock: {full_char}. "
        f"Invariant Hair & Color Lock: strictly identical {locked_hair} with {locked_hair_color}, zero color shift across different scenes. "
        f"Continuity: Strictly identical person, same facial bone structure, same skin tone, same age, same haircut, exactly the same deep black hair color."
    )
    
    wardrobe_str = f"strictly wearing {locked_tops} and {locked_bottoms}"
    if locked_outer and locked_outer.lower() != "none":
        wardrobe_str += f" paired with {locked_outer}"
    
    dur_map = {"4s": 4, "6s": 6, "8s": 8, "10s": 10}
    total_sec = 0.0
    for scn in scenes:
        if "voiceover" in scn: scn["voiceover"] = sanitize_policy_text(scn["voiceover"])
        if "director" in scn: scn["director"] = sanitize_policy_text(scn["director"])
        
        raw_speech_time = calculate_speech_duration(scn.get("voiceover", ""), is_tiktok_shop)
        
        if raw_speech_time <= 3.2: calc_sec = 4
        elif raw_speech_time <= 5.2: calc_sec = 6
        elif raw_speech_time <= 7.2: calc_sec = 8
        else: calc_sec = 10
            
        ai_dur = scn.get("dur", "")
        ai_sec = dur_map.get(ai_dur, 0)
        final_sec = max(ai_sec, calc_sec)
        
        if raw_speech_time >= final_sec:
            actual_speech_time = round(final_sec - 0.6, 1)
        else:
            actual_speech_time = raw_speech_time
            
        final_bucket = f"{final_sec}s"
        scn["dur"] = final_bucket
        scn["actual_speech_sec"] = actual_speech_time
        total_sec += float(final_sec)
        
        clean_action = re.sub(r'\[.*?\]', '', scn.get("action_en", "")).strip()
        camera_shot = scn.get("camera_shot", "Vertical 9:16 cinematic shot")
        sfx_sound = scn.get("sfx", "Layered realistic ambient sensory Foley sounds")
        micro_expr = scn.get("expression", "Natural expressive facial micro-emotions")
        scene_num = scn.get("scene", 1)
        scene_setting_en = scn.get("setting_en") or scn.get("setting") or default_setting
        
        if is_fashion_styling:
            scene_outfit = scn.get("scene_outfit_en") or wardrobe_str
            active_wardrobe_desc = f"Fashion Outfit Styling Look: expertly styled wearing {scene_outfit} highlighting {clean_prod_en}"
            active_negative = base_negative
        else:
            active_wardrobe_desc = f"Invariant Locked Wardrobe: {wardrobe_str} with exact same color, texture and fabric across all scenes"
            active_negative = base_negative + ", changing clothes, different shirt, different colored shirt, costume change, wardrobe change, changing outfit, different colored top, removing jacket, taking off apron, different pants, inconsistent wardrobe, inconsistent clothes"
            
        full_identity_anchor = f"{character_base_identity} {active_wardrobe_desc}."
        
        # CẤU TRÚC PROMPT ẢNH: ĐỒNG NHẤT KHUÔN MẶT, MÀU TÓC ĐEN & NHÂN VẬT TRỰC TIẾP
        if scene_num == 1:
            scene_focus = (
                f"Attention stage with Dual-Layer Hook: Two-beat opening. "
                f"Beat 1 (0.0s-1.5s): High-impact visual kinetic hook capturing {clean_prod_en} in action. "
                f"Beat 2 (1.5s-6.0s): Medium shot capturing {full_identity_anchor} facing camera with {micro_expr}, introducing {clean_prod_en} in {scene_setting_en}."
            )
        elif scene_num == 2:
            scene_focus = (
                f"Interest stage: Vertical 9:16 eye-level medium close-up in {scene_setting_en}. "
                f"{full_identity_anchor} "
                f"Character visibly facing camera and speaking directly with moving lips, holding {clean_prod_en} at chest level, demonstrating its mechanism with steady five-finger hands. Close-up clarity on {clean_prod_en} and hand ergonomics. Connector physics: {connector_physics_en}. Hair color strictly deep black without ambient color shifts."
            )
        elif scene_num == 3:
            scene_focus = (
                f"Desire stage: Medium close-up lifestyle action shot in {scene_setting_en}. "
                f"{full_identity_anchor} "
                f"Action: {clean_action}. Character enjoying the real-life practical benefits and tactile satisfaction of {clean_prod_en} with {micro_expr}, strictly maintaining identical facial features and deep black hair."
            )
        else:
            scene_focus = f"Action stage: Warm commercial closing shot in {scene_setting_en}. {full_identity_anchor} Character smiling with confident direct eye contact, holding {clean_prod_en} with welcoming open-palm gestures."
            
        raw_img = (
            f"{camera_shot}. {scene_focus} "
            f"Product Integrity: Authentic {clean_prod_en}, strictly rigid non-deformable structure, neutral clean typography. "
            f"Quality: Photorealistic commercial photography, clean lighting, sharp focus, natural realistic environment. "
            f"Negative prompt: {active_negative}."
        )
        scn["img_p"] = sanitize_third_party_ip(raw_img)
        
        # PROMPT VIDEO VEO 3 SAFE / KLING AI: CƯỠNG CHẾ KHẨU HÌNH ON-CAMERA 100%
        speaker_line = scn.get("voiceover", "")
        # SỬA LỖI TIMING: Cảnh 1 nói lúc 1.50s (sau cú visual hook), Cảnh 2,3,4 BẮT BUỘC nói ngay lúc 0.00s!
        audio_start_sec = "1.50s" if scene_num == 1 else "0.00s"
        audio_part = f' Direct on-camera spoken dialogue at {audio_start_sec}. Character visibly facing camera with mouth and lips clearly moving in continuous natural lip-sync. Spoken audio: "{speaker_line}", Layered Foley SFX: [{sfx_sound}].'
        continuity_note = "Identity Continuity: Invariant actor face, strictly uniform deep jet-black hair pigment across all scenes without ambient discoloration, matching styling looks." if is_fashion_styling else "Identity & Wardrobe Continuity: Invariant actor face, strictly uniform deep jet-black hair pigment across all scenes, invariant clothing across all frames, zero costume change."
        
        raw_vid = (
            f"{camera_shot}. Wholesome live-action commercial footage. {full_identity_anchor} "
            f"Setting: {scene_setting_en}. "
            f"Action: {clean_action}. Micro-expression: {micro_expr}.{audio_part} "
            f"Product Assembly & Invariance: Authentic {clean_prod_en}. Multi-component assembly strictly maintained: {connector_physics_en}. The connecting hose remains continuously visible bridging both hands without vanishing or morphing. "
            f"{continuity_note} "
            f"Anatomy & Kinetics: Invariant two-hand operation, anatomically correct hands with strictly five fingers per hand, zero limb morphing, ZERO syringe transformation. "
            f"Strictly pure footage: ABSOLUTELY NO off-screen voiceover, ABSOLUTELY NO yellow cart icons, NO animated buttons, NO UI stickers, NO on-screen subtitles, NO text. "
            f"Negative prompt: {active_negative}."
        )
        scn["vid_p"] = sanitize_veo3_prompt(raw_vid)
        
    res["scenes"] = scenes
    res["total_dur"] = f"Khoảng {int(total_sec)} giây"
    wardrobe_summary_text = "👗 <b>Chế độ Thời trang Phối đồ:</b> Thay đổi outfit linh hoạt theo từng cảnh & câu thoại (Khuôn mặt, dáng người & màu tóc đen tuyền khóa bất biến 100%)" if is_fashion_styling else f"👗 <b>Khóa bất biến trang phục:</b> {res.get('outfit_vi', 'Khóa chết áo chính, áo trong/khoác/tạp dề, quần/váy 100%')}"
    
    res["director_summary"] = f"⏱ <b>Thời lượng kịch bản:</b> Khoảng {int(total_sec)} giây (Khung hình luôn dài hơn thời gian đọc, có đệm an toàn chống cụt tiếng) | 🎙 <b>Chỉ đạo giọng:</b> 100% nhân vật nói trực tiếp on-camera lip-sync (CẢ 4 CẢNH ĐỀU LÀ NHÂN VẬT NÓI, TRIỆT TIÊU THUYẾT MINH | 100% Giọng Hà Nội chuẩn, dùng 'nghìn', neo giá linh hoạt 'khoảng/gần/chưa tới', không dùng 'trợ giá')<br>⚡ <b>Cảnh 1 Dual-Layer Hook:</b> Nhịp 1 Visual Hook giật gân (0.0s-1.5s) + Nhịp 2 Voice Hook Hà Nội chuẩn (1.5s-6.0s)<br>👤 <b>Khóa bất biến nhân vật:</b> Màu tóc đen tuyền tự nhiên không biến đổi theo ánh sáng, khuôn mặt đồng nhất 100%<br>{wardrobe_summary_text}<br>🏙 <b>Bối cảnh bám sát kịch bản:</b> {fixed_setting_base} (chiều sâu không gian sinh động đời thực)<br>📸 <b>Đa dạng hóa 4 góc máy on-camera:</b> Cảnh 1 (Dual-Layer Hook) &rarr; Cảnh 2 (Medium close-up người nói + tay thao tác) &rarr; Cảnh 3 (Trung cận đời sống) &rarr; Cảnh 4 (Thương mại chốt deal)<br>🔗 <b>Động lực học dây nối:</b> {connector_physics_en} | 🚫 <b>Khóa đa linh kiện:</b> Triệt tiêu hoàn toàn lỗi biến thành ống tiêm xylanh<br>📖 <b>Mạch truyện liền khúc:</b> 4 cảnh gắn kết logic thành 1 câu chuyện hoàn chỉnh | 🛡 <b>Tuân thủ chính sách:</b> Câu miễn trừ chương trình giảm giá sâu có hạn theo khung giờ"
    
    st.session_state.generated_details[int(target_id)] = res
    st.session_state.generated_details[str(target_id)] = res

def clone_script(script_id):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    style = st.session_state.get("last_style", "Điện Ảnh Chân Thực")
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if str(sc.get("id")) == str(script_id)), None)
    if not target: return []
    
    cur_len = len(all_combined)
    target_detail = st.session_state.generated_details.get(int(script_id), st.session_state.generated_details.get(str(script_id), {}))
    
    original_voices = []
    if target_detail and "scenes" in target_detail:
        for s in target_detail["scenes"]:
            original_voices.append(f"- Cảnh {s.get('scene')} ({s.get('aida_stage')}): \"{s.get('voiceover')}\"")
        full_voice_text = "\n".join(original_voices)
    else:
        full_voice_text = f"- Hook 3s đầu: \"{target.get('hook', '')}\""

    dna = st.session_state.get("content_analysis") or {}
    condensed_dna = {
        "product": dna.get("what_and_unique", ""),
        "hero_sku": dna.get("hero_sku_color", ""),
        "price_anchor": dna.get("rounded_price_anchor", "")
    }
    
    prompt = f"""
    SẢN PHẨM: {json.dumps(condensed_dna, ensure_ascii=False)} | KỊCH BẢN GỐC #{script_id}: TIÊU ĐỀ: '{target.get('title', '')}'
    THOẠI GỐC:\n{full_voice_text}
    NHIỆM VỤ: Giữ nguyên 100% công năng và đòn bẩy neo giá kèm câu miễn trừ giá hợp quy chuẩn, nhân bản thành 5 biến thể kịch bản thoại mới theo 5 góc kể chuyện và 5 BỐI CẢNH ĐỜI THỰC KHÁC NHAU. 100% CẢ 4 PHÂN CẢNH ĐỀU LÀ NHÂN VẬT MỞ MIỆNG NÓI TRỰC TIẾP ON-CAMERA BẰNG GIỌNG HÀ NỘI CHUẨN ĐÚNG ĐỘ TUỔI, TỐC ĐỘ 4.8 - 5.2 TỪ/S (CẤM TUYỆT ĐỐI THUYẾT MINH). TUYỆT ĐỐI CẤM TỪ 'NGÀN' (BẮT BUỘC DÙNG 'NGHÌN'). TUYỆT ĐỐI CẤM TỪ 'TRỢ GIÁ'. NEO GIÁ LINH HOẠT ('KHOẢNG...', 'GẦN...', 'CHƯA TỚI...').
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên biến thể 1", "setting": "Bối cảnh đời thực 1...", "hook": "Câu hook ngắn gọn do nhân vật nói trực tiếp bằng tiếng Hà Nội chuẩn...", "actors": 1, "character_roles": ["Nữ KOC Hà Nội"] }},
            {{ "id": {cur_len+2}, "title": "Tên biến thể 2", "setting": "Bối cảnh đời thực 2...", "hook": "...", "actors": 1, "character_roles": ["Cô nàng công sở"] }},
            {{ "id": {cur_len+3}, "title": "Tên biến thể 3", "setting": "Bối cảnh đời thực 3...", "hook": "...", "actors": 2, "character_roles": ["Mẹ trẻ", "Bé gái"] }},
            {{ "id": {cur_len+4}, "title": "Tên biến thể 4", "setting": "Bối cảnh đời thực 4...", "hook": "...", "actors": 1, "character_roles": ["KOC trẻ trung"] }},
            {{ "id": {cur_len+5}, "title": "Tên biến thể 5", "setting": "Bối cảnh đời thực 5...", "hook": "...", "actors": 2, "character_roles": ["Đôi bạn thân"] }}
        ]
    }}
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, "On-camera", "", target.get("actors", 1), "Nhân bản thoại"), max_tokens=2500)
    clones = res.get("outlines", res.get("script_outlines", []))
    formatted_clones = []
    for idx, cl in enumerate(clones):
        new_actors_count = cl.get("actors", 1)
        raw_roles = cl.get("character_roles", [f"Diễn viên {i+1}" for i in range(new_actors_count)])
        new_profiles = [{"id": i+1, "role": r} for i, r in enumerate(raw_roles)]
        formatted_clones.append({
            "id": cur_len + idx + 1, "title": cl.get("title", f"Biến thể kịch bản #{cur_len + idx + 1}"),
            "setting": cl.get("setting", f"Bối cảnh sinh hoạt #{idx+1}"), "hook": sanitize_policy_text(cl.get("hook", "")),
            "actors": new_actors_count, "character_profiles": new_profiles,
            "duration_instruction": target.get("duration_instruction", "Thời lượng động"), "narrator_mode": "Nhân vật xuất hiện (On-camera)"
        })
    return formatted_clones

def generate_more_scripts(angle, num_chars, extra_char_inputs, narrator_mode_more, duration_inst, char_profiles):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    style = st.session_state.get("last_style", "Điện Ảnh Chân Thực")
    char_rules = generate_char_rules_string(char_profiles)
    cur_len = len(st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts)
    dna = st.session_state.get("content_analysis") or {}
    condensed_dna = {
        "product": dna.get("what_and_unique", ""), "hero_sku": dna.get("hero_sku_color", ""), "price_anchor": dna.get("rounded_price_anchor", "")
    }
    prompt = f"""
    SẢN PHẨM: {json.dumps(condensed_dna, ensure_ascii=False)} | CHIẾN LƯỢC: '{angle}' | DIỄN VIÊN: {num_chars} người Việt.
    BẮT BUỘC TẠO RA 5 KỊCH BẢN Ở 5 BỐI CẢNH ĐỜI THỰC HOÀN TOÀN KHÁC NHAU (tuyệt đối không trùng lặp bối cảnh giữa 5 kịch bản).
    100% CẢ 4 PHÂN CẢNH ĐỀU LÀ NHÂN VẬT MỞ MIỆNG NÓI TRỰC TIẾP ON-CAMERA BẰNG GIỌNG HÀ NỘI CHUẨN ĐÚNG ĐỘ TUỔI (4.8 - 5.2 từ/s), TUYỆT ĐỐI CẤM THUYẾT MINH. TUYỆT ĐỐI CẤM TỪ 'NGÀN' (PHẢI DÙNG TỪ 'NGHÌN'). TUYỆT ĐỐI CẤM TỪ 'TRỢ GIÁ'. NEO GIÁ LINH HOẠT ('KHOẢNG...', 'GẦN...', 'CHƯA TỚI...').
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên kịch bản 1", "setting": "Bối cảnh đời thực 1...", "hook": "Câu hook ngắn gọn nhân vật nói trực tiếp bằng tiếng Hà Nội chuẩn...", "actors": {num_chars} }},
            {{ "id": {cur_len+2}, "title": "Tên kịch bản 2", "setting": "Bối cảnh đời thực 2...", "hook": "...", "actors": {num_chars} }},
            {{ "id": {cur_len+3}, "title": "Tên kịch bản 3", "setting": "Bối cảnh đời thực 3...", "hook": "...", "actors": {num_chars} }},
            {{ "id": {cur_len+4}, "title": "Tên kịch bản 4", "setting": "Bối cảnh đời thực 4...", "hook": "...", "actors": {num_chars} }},
            {{ "id": {cur_len+5}, "title": "Tên kịch bản 5", "setting": "Bối cảnh đời thực 5...", "hook": "...", "actors": {num_chars} }}
        ]
    }}
    BẮT BUỘC ĐỦ 5 KỊCH BẢN.
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, "On-camera", char_rules, num_chars, angle), max_tokens=2500)
    more_scripts = res.get("outlines", res.get("script_outlines", []))
    for idx, sc in enumerate(more_scripts):
        if "hook" in sc: sc["hook"] = sanitize_policy_text(sc["hook"])
        sc.update({"id": cur_len + idx + 1, "duration_instruction": duration_inst, "narrator_mode": "Nhân vật xuất hiện (On-camera)", "character_profiles": char_profiles, "actors": num_chars})
    return more_scripts

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

# ==============================================================================
# 3. THANH BÊN (SIDEBAR) & QUẢN TRỊ ADMIN (LỊCH CHỌN NGÀY)
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        tabs = st.tabs(["🔐 Đăng Nhập", "🚀 Đăng Ký"])
        with tabs[0]:
            with st.form("login_form", border=False):
                email_input = st.text_input("Email:", key="f_login_email", autocomplete="new-password")
                pass_input = st.text_input("Mật khẩu:", type="password", key="f_login_pass", autocomplete="new-password")
                submit_login = st.form_submit_button("🔑 Đăng Nhập", type="primary", use_container_width=True)
                if submit_login:
                    email_c, pass_c = email_input.strip(), pass_input.strip()
                    if email_c in st.session_state.licensed_accounts and st.session_state.licensed_accounts[email_c].get("password") == pass_c:
                        st.session_state.licensed_accounts[email_c]["active_session_id"] = st.session_state.session_id
                        save_single_account(email_c, st.session_state.licensed_accounts[email_c])
                        st.session_state.is_logged_in = True
                        st.session_state.current_email = email_c
                        st.toast("✅ Đăng nhập thành công!"); time.sleep(0.4); st.rerun()
                    else: st.error("❌ Email hoặc mật khẩu không đúng!")
                        
        with tabs[1]:
            with st.form("register_form", border=False):
                r_email = st.text_input("Email đăng ký:", key="f_reg_email", autocomplete="new-password")
                r_phone = st.text_input("Số điện thoại:", key="f_reg_phone", autocomplete="new-password")
                r_pass = st.text_input("Mật khẩu mới:", type="password", key="f_reg_pass", autocomplete="new-password")
                r_purpose = st.selectbox("🎯 Mục đích:", ["🛒 TikTok Shop", "🌟 Viral & Xây Kênh", "⚡ Cả hai"], key="f_reg_purpose")
                submit_reg = st.form_submit_button("🚀 Đăng Ký", type="secondary", use_container_width=True)
                if submit_reg:
                    email_r, phone_r, pass_r = r_email.strip(), r_phone.strip(), r_pass.strip()
                    if email_r and phone_r and pass_r and is_valid_phone(phone_r) and email_r not in st.session_state.licensed_accounts:
                        exp = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[email_r] = {
                            "roles": ALL_MODULES, "phone": phone_r, "password": pass_r,
                            "expires_at": exp, "plan_type": "Trial", "daily_usage_count": 0,
                            "last_generation_date": "", "active_session_id": ""
                        }
                        save_single_account(email_r, st.session_state.licensed_accounts[email_r])
                        st.session_state.is_logged_in = True
                        st.session_state.current_email = email_r
                        st.toast("✅ Đăng ký thành công!"); time.sleep(0.4); st.rerun()
                    else: st.error("⚠️ Thông tin không hợp lệ hoặc tài khoản đã tồn tại!")
    else:
        st.markdown("### 🗂 DỰ ÁN")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True, disabled=is_system_busy):
            st.session_state.reset_key += 1
            st.session_state.update({
                "all_scripts": [], "cloned_scripts": [], "expanded_scripts": [],
                "generated_details": {}, "content_analysis": None, "active_script_id": None,
                "current_input_context": "", "current_product_data_saved": None, "current_product_data": None,
                "current_project_id": None, "saved_reference_images": [], "character_profiles": [],
                "current_processing_id": None, "current_cloning_id": None
            })
            st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
            st.rerun()
            
        st.session_state.active_project_title = st.text_input("Tên dự án:", value=st.session_state.active_project_title)
        if st.button("💾 Lưu Dự Án", use_container_width=True, disabled=is_system_busy):
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

            if not display_projects: st.info("Chưa có dự án nào.")
            else:
                for p in display_projects:
                    with st.expander(f"🎬 {p['project_title']}"):
                        col_o, col_d = st.columns(2)
                        if col_o.button("📂 Mở", key=f"o_{p['id']}", use_container_width=True, disabled=is_system_busy):
                            sd = p.get("script_content", {})
                            loaded_details = {}
                            for k, v in sd.get("generated_details", {}).items():
                                try: loaded_details[int(k)] = v
                                except: pass
                                loaded_details[str(k)] = v
                            st.session_state.update({
                                "content_analysis": sd.get("content_analysis"), "all_scripts": sd.get("all_scripts", []),
                                "cloned_scripts": sd.get("cloned_scripts", []), "expanded_scripts": sd.get("expanded_scripts", []),
                                "generated_details": loaded_details, "character_profiles": sd.get("character_profiles", []),
                                "current_project_id": p['id'], "active_project_title": p['project_title'], "scroll_to_detail": True
                            })
                            st.rerun()
                        if col_d.button("🗑 Xóa", key=f"d_{p['id']}", type="secondary", use_container_width=True, disabled=is_system_busy):
                            supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                            st.toast("✅ Đã xóa!"); time.sleep(0.3); st.rerun()

                if not search_proj.strip() and len(all_projects) > 3:
                    if st.session_state.show_all_projects:
                        if st.button("🔼 Thu gọn kho dự án", use_container_width=True, disabled=is_system_busy):
                            st.session_state.show_all_projects = False; st.rerun()
                    else:
                        if st.button(f"🔽 Xem thêm {len(all_projects)-3} dự án", use_container_width=True, disabled=is_system_busy):
                            st.session_state.show_all_projects = True; st.rerun()

        if st.session_state.current_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙ QUẢN TRỊ ADMIN")
            with st.expander("➕ Cấp Quyền Mới", expanded=False):
                adm_acc = st.text_input("Email:", autocomplete="new-password", key="adm_in_acc")
                adm_phone = st.text_input("SĐT:", autocomplete="new-password", key="adm_in_phone")
                adm_pass = st.text_input("Mật khẩu:", value="123456", autocomplete="new-password", key="adm_in_pass")
                adm_roles_choice = st.multiselect("🎯 Thể loại:", ALL_MODULES, default=ALL_MODULES, key="adm_in_roles")
                adm_plan = st.radio("Gói cước:", ["Trial", "Basic", "Advanced", "VIP"], horizontal=True, key="adm_in_plan")
                adm_dur = st.selectbox("Thời hạn:", ["3 Ngày", "7 Ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "Vĩnh viễn", "Tùy chỉnh (Chọn ngày)"], key="adm_in_dur")
                
                calculated_exp_str = "2099-12-31"
                if adm_dur == "Tùy chỉnh (Chọn ngày)":
                    custom_date = st.date_input("Chọn ngày hết hạn:", value=date.today() + timedelta(days=30), min_value=date.today(), key="adm_custom_date")
                    calculated_exp_str = custom_date.strftime("%Y-%m-%d")
                    st.caption(f"📅 Hạn mới: **{calculated_exp_str}**")
                elif adm_dur == "Vĩnh viễn": calculated_exp_str = "2099-12-31"
                else:
                    dur_days_map = {"3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730}
                    calculated_exp_str = (datetime.now() + timedelta(days=dur_days_map.get(adm_dur, 30))).strftime("%Y-%m-%d")

                if st.button("💾 Cấp Quyền Tài Khoản", type="primary", use_container_width=True, key="btn_submit_grant_admin", disabled=is_system_busy):
                    if adm_acc.strip() and adm_phone.strip() and adm_pass.strip() and adm_roles_choice:
                        st.session_state.licensed_accounts[adm_acc.strip()] = {
                            "roles": ALL_MODULES, "phone": adm_phone.strip(), "password": adm_pass.strip(),
                            "expires_at": calculated_exp_str, "plan_type": adm_plan, "daily_usage_count": 0,
                            "last_generation_date": "", "active_session_id": ""
                        }
                        save_single_account(adm_acc.strip(), st.session_state.licensed_accounts[adm_acc.strip()])
                        st.toast(f"✅ Đã cấp quyền đến {calculated_exp_str}!"); time.sleep(0.4); st.rerun()
                    else: st.error("⚠️ Vui lòng nhập đầy đủ thông tin!")

            st.markdown("##### 👥 Danh Sách Tài Khoản & Gia Hạn")
            search_acc = st.text_input("🔍 Tìm tài khoản:", placeholder="Nhập Email hoặc SĐT...", key="search_acc_input")
            other_accs = [item for item in st.session_state.licensed_accounts.items() if item[0] != ADMIN_EMAIL]
            filt_accs = [item for item in other_accs if search_acc.strip().lower() in item[0].lower() or search_acc.strip() in item[1].get('phone', '')] if search_acc.strip() else (other_accs if st.session_state.show_all_admin_accounts else other_accs[:3])

            for acc_mail, info in filt_accs:
                with st.expander(f"👤 {acc_mail} ({info.get('plan_type')})"):
                    st.write(f"📞 SĐT: `{info.get('phone', 'N/A')}` | ⏳ Hạn: `{info.get('expires_at')}`")
                    cur_roles = info.get("roles", ALL_MODULES)
                    new_roles = st.multiselect("Đổi thể loại:", ALL_MODULES, default=cur_roles, key=f"roles_sel_{acc_mail}")
                    new_plan = st.selectbox("Đổi gói:", ["Trial", "Basic", "Advanced", "VIP"], index=["Trial", "Basic", "Advanced", "VIP"].index(info.get("plan_type", "Trial")), key=f"plan_sel_{acc_mail}")
                    renew_opts = ["Giữ nguyên hạn hiện tại", "3 Ngày", "7 Ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "Vĩnh viễn", "Tùy chỉnh (Chọn ngày)"]
                    renew_choice = st.selectbox("Gia hạn:", renew_opts, key=f"renew_opt_{acc_mail}")
                    target_exp_str = info.get("expires_at", "2099-12-31")
                    if renew_choice == "Tùy chỉnh (Chọn ngày)":
                        try: cur_d = datetime.strptime(info.get("expires_at", ""), "%Y-%m-%d").date()
                        except: cur_d = date.today() + timedelta(days=30)
                        r_date = st.date_input("Chọn ngày hết hạn mới:", value=cur_d, min_value=date.today(), key=f"rdate_{acc_mail}")
                        target_exp_str = r_date.strftime("%Y-%m-%d")
                    elif renew_choice == "Vĩnh viễn": target_exp_str = "2099-12-31"
                    elif renew_choice != "Giữ nguyên hạn hiện tại":
                        dur_map_v = {"3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730}
                        target_exp_str = (datetime.now() + timedelta(days=dur_map_v.get(renew_choice, 30))).strftime("%Y-%m-%d")

                    c_act1, c_act2 = st.columns(2)
                    if c_act1.button("🔄 Cập Nhật", key=f"save_renew_{acc_mail}", use_container_width=True, disabled=is_system_busy):
                        st.session_state.licensed_accounts[acc_mail]["roles"] = new_roles
                        st.session_state.licensed_accounts[acc_mail]["plan_type"] = new_plan
                        st.session_state.licensed_accounts[acc_mail]["expires_at"] = target_exp_str
                        save_single_account(acc_mail, st.session_state.licensed_accounts[acc_mail])
                        st.toast("✅ Đã cập nhật thành công!"); time.sleep(0.4); st.rerun()
                    if c_act2.button("🗑 Xóa", key=f"del_acc_{acc_mail}", type="secondary", use_container_width=True, disabled=is_system_busy):
                        delete_single_account(acc_mail)
                        if acc_mail in st.session_state.licensed_accounts: del st.session_state.licensed_accounts[acc_mail]
                        st.toast("✅ Đã xóa!"); time.sleep(0.3); st.rerun()

            if not search_acc.strip() and len(other_accs) > 3:
                if st.session_state.show_all_admin_accounts:
                    if st.button("🔼 Thu gọn danh sách tài khoản", use_container_width=True, disabled=is_system_busy):
                        st.session_state.show_all_admin_accounts = False; st.rerun()
                else:
                    if st.button(f"🔽 Xem thêm {len(other_accs)-3} tài khoản", use_container_width=True, disabled=is_system_busy):
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
            st.session_state.is_logged_in = False; st.rerun()

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
    viral_persona = col_v1.text_input("👤 Định vị Kênh:", key=f"viral_persona_{st.session_state.reset_key}")
    viral_topic = col_v2.text_area("💡 Chủ đề / Mẹo:", height=68, key=f"viral_topic_{st.session_state.reset_key}")
    up_files = st.file_uploader("📦 Upload Ảnh:", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_viral_{st.session_state.reset_key}")
    custom_note = st.text_area("✍ Ghi chú AI:", key=f"custom_note_viral_{st.session_state.reset_key}")
    hero_sku_override = ""
else:
    products_data = supabase.table("products").select("*").execute().data if supabase else []
    if products_data:
        selected_name = st.selectbox("📌 Chọn sản phẩm:", [p["product_name"] for p in products_data], key=f"prod_select_{st.session_state.reset_key}")
        st.session_state.current_product_data = next(p for p in products_data if p["product_name"] == selected_name)
    
    col_f1, col_f2 = st.columns([2, 1])
    up_files = col_f1.file_uploader("📦 Upload Ảnh SP (Quét OCR Giá, Hero SKU & Bảng màu):", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_prod_{st.session_state.reset_key}")
    hero_sku_override = col_f2.text_input("🎯 Màu / SKU ưu tiên (Tùy chọn):", placeholder="Ví dụ: Đỏ, Be, Size L...", key=f"hero_override_{st.session_state.reset_key}")
    custom_note = st.text_area("✍ Ghi chú AI:", key=f"custom_note_prod_{st.session_state.reset_key}")

col_opt1, col_opt2 = st.columns(2)
style = col_opt1.selectbox("🎨 Phong cách:", ["Điện Ảnh Chân Thực", "Hoạt Hình 3D", "Studio Tối Giản"], key=f"style_sel_{st.session_state.reset_key}")
angle_options = ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Chia sẻ", "😂 Hài hước"]
initial_angle = col_opt1.selectbox("🧭 Chiến lược:", angle_options, key=f"angle_sel_{st.session_state.reset_key}")
narrator_mode = col_opt2.selectbox("🎙 Thuyết minh:", ["Nhân vật xuất hiện (On-camera)"], key=f"narrator_sel_{st.session_state.reset_key}")
num_chars = col_opt2.number_input("👤 Số Diễn viên (1 = Độc thoại KOC, ≥2 = Tiểu phẩm đối thoại):", 1, 8, 1, key=f"num_chars_{st.session_state.reset_key}")

char_inputs = []
for i in range(num_chars):
    c_r, c_i = st.columns([2, 1])
    role_default = "Mẹ trẻ 26 tuổi người Việt" if (num_chars >= 2 and i == 0) else ("Bé trai 4 tuổi người Việt" if (num_chars >= 2 and i == 1) else ("Bé gái 1 tuổi người Việt" if (num_chars >= 2 and i == 2) else ""))
    role = c_r.text_input(f"Vai trò NV {i+1}:", value=role_default, key=f"r_{i}_{st.session_state.reset_key}")
    c_file = c_i.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"f_{i}_{st.session_state.reset_key}", label_visibility="collapsed")
    if c_file: char_inputs.append({"id": i+1, "role": role or f"Diễn viên {i+1}", "file": c_file})

if st.button("🚀 PHÂN TÍCH DNA & SINH 5 KỊCH BẢN ĐA VŨ TRỤ", type="primary", use_container_width=True, disabled=is_system_busy):
    can_run, msg = check_usage_limit(st.session_state.current_email)
    if not can_run: st.error(msg)
    else:
        with st.spinner("⏳ Đạo diễn AI đang quét OCR bảng màu, nhận diện Hero SKU và phân tích DNA..."):
            try:
                st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs] if char_inputs else [{"id": i+1, "role": f"Diễn viên {i+1}"} for i in range(num_chars)]
                char_rules = generate_char_rules_string(st.session_state.character_profiles)
                st.session_state.update({"last_mode": mode, "last_style": style, "last_narrator": "On-camera", "current_input_context": custom_note})
                st.session_state.current_product_data_saved = st.session_state.get("current_product_data", {})
                
                st.session_state["saved_reference_images"] = []
                if up_files:
                    for f in up_files:
                        cb, cm = compress_image_bytes(f, 768, 75)
                        st.session_state["saved_reference_images"].append((cb, cm))

                override_instruction = f"BẮT BUỘC KHÓA HERO SKU LÀ: '{hero_sku_override.strip()}' theo yêu cầu trực tiếp của người dùng." if hero_sku_override.strip() else "QUÉT OCR ƯU TIÊN TUYỆT ĐỐI Ô PHÂN LOẠI CÓ GẮN ICON NGỌN LỬA '🔥', 'Hot', 'Bán chạy', 'Top 1'. Nếu ô có tag này, BẮT BUỘC 100% chọn ô đó là Hero SKU! Không chọn màu khác khi đã có tag Hot/Bán chạy."

                prompt = f"""
                INPUT: {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)} | NOTE: {custom_note}
                DIỄN VIÊN: {num_chars} nhân vật 100% người Việt bản địa ({', '.join([p['role'] for p in st.session_state.character_profiles])}).
                100% CẢ 4 PHÂN CẢNH ĐỀU LÀ DO CHÍNH NHÂN VẬT MỞ MIỆNG NÓI TRỰC TIẾP TRƯỚC ỐNG KÍNH (ON-CAMERA LIP-SYNC) BẰNG GIỌNG HÀ NỘI CHUẨN ĐÚNG ĐỘ TUỔI, TỐC ĐỘ 4.8 - 5.2 TỪ/S (TUYỆT ĐỐI CẤM THUYẾT MINH).
                🛑 CẤM TUYỆT ĐỐI TỪ 'NGÀN'. 100% BẮT BUỘC DÙNG TỪ 'NGHÌN'.
                🛑 CẤM TUYỆT ĐỐI TỪ 'TRỢ GIÁ', 'PHIÊN LIVE', 'TRÊN LIVE'.
                🛑 CẤM TUYỆT ĐỐI KHẨU NGỮ MIỀN NAM. 100% dùng từ ngữ Hà Nội chuẩn.
                🛑 BẮT BUỘC TẠO RA 5 KỊCH BẢN Ở 5 BỐI CẢNH ĐỜI THỰC KHÁC NHAU (tuyệt đối không trùng lặp bối cảnh giữa 5 kịch bản).
                CHỈ ĐẠO HERO SKU: {override_instruction}
                
                BẮT BUỘC TRẢ VỀ JSON:
                {{
                    "content_analysis": {{
                        "target_audience": "Tệp khách hàng mục tiêu",
                        "core_value": "Giá trị cốt lõi",
                        "pain_points": "Nỗi đau thực tế",
                        "hook_element": "Yếu tố giật gân 3 giây đầu",
                        "visual_hook_archetype": "Dạng thức Visual Hook phù hợp nhất (Visual Stress Test / Visceral Pain / ASMR Tactile / Instant Contrast / Pattern Interrupt)",
                        "hero_sku_color": "Mã màu bán chạy nhất (Hero SKU - Ưu tiên tuyệt đối ô có tag '🔥 Hot' / 'Bán chạy')",
                        "color_palette": "Bảng màu toàn bộ",
                        "what_and_unique": "Định danh sản phẩm và điểm độc bản (USP) vượt trội (chỉ viết nội dung)",
                        "target_user": "Đối tượng cụ thể phù hợp nhất (chỉ viết nội dung)",
                        "why_buy": "Lý do thuyết phục không thể chối từ (chỉ viết nội dung)",
                        "where_and_convenience": "Hoàn cảnh ứng dụng thực tế và sự tiện lợi (chỉ viết nội dung)",
                        "how_to_use": "Mô tả thao tác đời thực chuẩn xác theo loại sản phẩm (chỉ viết nội dung)",
                        "product_size_class": "Phân loại kích thước",
                        "product_color_lock": "Khóa màu sắc và họa tiết Hero SKU",
                        "lid_mechanism": "Cơ chế cơ học/kết cấu thực tế: Nắp vặn kín, cúc áo, khóa kéo, bo chun... TUYỆT ĐỐI KHÔNG BỊA RA CHI TIẾT DỊ THƯỜNG",
                        "product_assembly_structure": "Bóc tách cấu trúc đa linh kiện: (1) Thân máy/ống pít-tông, (2) Dây dẫn/ống nối mềm (nếu có), (3) Đầu hút/vòi thao tác rời. Nếu nguyên khối thì ghi rõ nguyên khối.",
                        "flexible_connector_specs": "Nếu có dây nối/ống silicone: Ghi rõ độ dài ước tính (20-25cm), đường kính ngoài (6-8mm), chất liệu silicone mờ dẻo, độ võng cong chữ U tự nhiên theo trọng lực nối giữa 2 tay. Nếu không có dây thì ghi 'Không có dây nối'.",
                        "strict_anti_morph_targets": "Các vật thể AI dễ vẽ nhầm/hallucination (ví dụ: ống tiêm y tế xylanh, kim tiêm, que nhựa) để cấm tiệt.",
                        "detected_prices": "Quét OCR giá tiền (giá gốc và giá sale)",
                        "rounded_price_anchor": "TÂM LÝ HỌC NEO GIÁ TƯƠNG PHẢN LINH HOẠT (100% DÙNG TỪ 'NGHÌN', CẤM 'NGÀN', CẤM 'TRỢ GIÁ'): Làm tròn giá gốc TIẾN LÊN mốc chẵn cao hơn, giá sale linh hoạt dùng các từ 'khoảng...', 'gần...', 'chưa tới...', 'tầm...'. Ví dụ: 'Giá gốc gần [X] nghìn -> Nay giảm chỉ còn khoảng [Y] nghìn' hoặc 'gần [Y] nghìn', 'chưa tới [Y] nghìn'",
                        "product_dimensions": "Thông số kích thước",
                        "prompt_dna_lock": "Visual DNA cho video"
                    }},
                    "outlines": [
                        {{ "id": 1, "title": "Tên kịch bản 1", "setting": "Bối cảnh đời thực 1 (ví dụ: Phòng ngủ gia đình nửa đêm)...", "hook": "Câu hook ngắn gọn nhân vật nói trực tiếp bằng tiếng Hà Nội chuẩn...", "actors": {num_chars} }},
                        {{ "id": 2, "title": "Tên kịch bản 2", "setting": "Bối cảnh đời thực 2 (ví dụ: Góc bếp / bàn ăn lúc chuẩn bị)...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 3, "title": "Tên kịch bản 3", "setting": "Bối cảnh đời thực 3 (ví dụ: Bàn làm việc văn phòng giờ nghỉ)...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 4, "title": "Tên kịch bản 4", "setting": "Bối cảnh đời thực 4 (ví dụ: Phòng khách ấm cúng bên sofa)...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 5, "title": "Tên kịch bản 5", "setting": "Bối cảnh đời thực 5 (ví dụ: Góc chuẩn bị ra ngoài dạo phố hoặc kho TMĐT)...", "hook": "...", "actors": {num_chars} }}
                    ]
                }}
                """
                payload = ["IMAGES:"]
                for cb, cm in st.session_state["saved_reference_images"]:
                    payload.append(types.Part.from_bytes(data=cb, mime_type=cm))
                for c in char_inputs:
                    cb, cm = compress_image_bytes(c['file'], 768, 75)
                    payload.extend([f"ACTOR {c['id']}:", types.Part.from_bytes(data=cb, mime_type=cm)])
                payload.append(prompt)
                
                res = call_gemini(payload, get_sys_inst_outlines(mode, style, "On-camera", char_rules, num_chars, initial_angle), max_tokens=6000)
                st.session_state.content_analysis = res.get("content_analysis")
                outlines = res.get("outlines", res.get("script_outlines", []))
                
                if not outlines:
                    raise Exception("AI bị ngắt quãng do kết nối mạng trong lúc sinh kịch bản. Vui lòng bấm tạo lại.")
                
                for o in outlines: 
                    if "hook" in o: o["hook"] = sanitize_policy_text(o["hook"])
                    o.update({"duration_instruction": "Thời lượng động linh hoạt", "narrator_mode": "Nhân vật xuất hiện (On-camera)", "character_profiles": st.session_state.character_profiles, "actors": num_chars})
                st.session_state.update({"all_scripts": outlines, "cloned_scripts": [], "expanded_scripts": [], "generated_details": {}, "active_script_id": None})
                st.toast("✅ Đã phân tích xong đầy đủ DNA & 5 Kịch bản đa bối cảnh!"); time.sleep(0.3); st.rerun()
            except Exception as e: st.error(f"❌ Lỗi: {e}")

ca = st.session_state.content_analysis
if isinstance(ca, dict):
    st.divider()
    st.markdown("### 🔍 **Phân Tích Chi Tiết**")
    col_dna1, col_dna2 = st.columns(2)
    with col_dna1:
        st.markdown(f"""
        <div class="dna-card">
            <div class="dna-card-title">🎯 1. Chân dung Khách hàng & Hook 3s (Attention)</div>
            <div class="dna-row"><span class="dna-label">👥 Tệp khách hàng:</span><span class="dna-text">{clean_analysis_text(ca.get('target_audience', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">💔 Nỗi đau thực tế:</span><span class="dna-text">{clean_analysis_text(ca.get('pain_points', ''))}</span></div>
            <div class="dna-row"><span class="dna-label" style="color:#d90429;">⚡ Yếu tố Hook 3s đầu:</span><span class="dna-text" style="color:#d90429; font-weight:600;">{clean_analysis_text(ca.get('hook_element', ''))}</span></div>
            <div class="dna-row"><span class="dna-label" style="color:#2563eb;">🎬 Dạng thức Visual Hook:</span><span class="dna-text" style="color:#2563eb; font-weight:600;">{clean_analysis_text(ca.get('visual_hook_archetype', ''))}</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col_dna2:
        st.markdown(f"""
        <div class="dna-card">
            <div class="dna-card-title">🔥 2. Mã Màu Bán Chạy Nhất (Hero SKU)</div>
            <div class="dna-row"><span class="dna-label">⭐ Mẫu ưu tiên làm video:</span><span class="dna-text" style="color:#dc2626; font-weight:700;">{clean_analysis_text(ca.get('hero_sku_color', 'Tự động'))}</span></div>
            <div class="dna-row"><span class="dna-label">🎨 Toàn bộ bảng màu:</span><span class="dna-text">{clean_analysis_text(ca.get('color_palette', ''))}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="dna-card">
        <div class="dna-card-title">💎 3. Giải phẫu Sản phẩm (Interest & Desire)</div>
        <div class="dna-row"><span class="dna-label">📦 Sản phẩm là gì & Điểm đặc biệt:</span><span class="dna-text">{clean_analysis_text(ca.get('what_and_unique', ''))}</span></div>
        <div class="dna-row"><span class="dna-label">👥 Sản phẩm dành cho ai:</span><span class="dna-text">{clean_analysis_text(ca.get('target_user', ''))}</span></div>
        <div class="dna-row"><span class="dna-label">🔥 Tại sao nên mua:</span><span class="dna-text">{clean_analysis_text(ca.get('why_buy', ''))}</span></div>
        <div class="dna-row"><span class="dna-label">📍 Hoàn cảnh sử dụng & Tiện lợi:</span><span class="dna-text">{clean_analysis_text(ca.get('where_and_convenience', ''))}</span></div>
        <div class="dna-row"><span class="dna-label">🛠 Thao tác & Cách dùng chuẩn thực tế:</span><span class="dna-text">{clean_analysis_text(ca.get('how_to_use', ''))}</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="dna-card">
        <div class="dna-card-title">⚙ 4. Vật lý, Cơ chế, Động lực học Dây nối & Mức giá</div>
        <div class="dna-row"><span class="dna-label">📐 Thông số kích thước:</span><span class="dna-text">{clean_analysis_text(ca.get('product_dimensions', ''))}</span></div>
        <div class="dna-row"><span class="dna-label">🧩 Bóc tách cấu trúc linh kiện:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{clean_analysis_text(ca.get('product_assembly_structure', 'Nguyên khối'))}</span></div>
        <div class="dna-row"><span class="dna-label">🔗 Động lực học dây nối/ống dẫn:</span><span class="dna-text" style="color:#d97706; font-weight:600;">{clean_analysis_text(ca.get('flexible_connector_specs', 'Không có dây nối'))}</span></div>
        <div class="dna-row"><span class="dna-label">🎨 Khóa màu chi tiết:</span><span class="dna-text">{clean_analysis_text(ca.get('product_color_lock', ''))}</span></div>
        <div class="dna-row"><span class="dna-label">⚙ Cấu tạo cơ học thực tế:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{clean_analysis_text(ca.get('lid_mechanism', 'Bình thường'))}</span></div>
        <div class="dna-row"><span class="dna-label">💰 Mức giá (OCR):</span><span class="dna-text">{clean_analysis_text(ca.get('detected_prices', ''))}</span></div>
        <div class="dna-row"><span class="dna-label" style="color:#dc2626;">🎯 Đòn bẩy giá tương phản linh hoạt:</span><span class="dna-text" style="color:#dc2626; font-weight:700;">{clean_analysis_text(ca.get('rounded_price_anchor', ''))}</span></div>
    </div>
    """, unsafe_allow_html=True)

    if ca.get('prompt_dna_lock'):
        st.markdown("##### 📌 **Visual DNA Lock:**")
        st.code(ca.get('prompt_dna_lock'), language="text")

all_sc = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
if all_sc:
    st.divider()
    def is_generated(sc_id):
        return (sc_id in st.session_state.generated_details or 
                str(sc_id) in st.session_state.generated_details or 
                int(sc_id) in st.session_state.generated_details)

    comp_sc = [sc for sc in all_sc if is_generated(sc.get("id"))]
    pend_sc = [sc for sc in all_sc if not is_generated(sc.get("id"))]

    if st.session_state.active_script_id is not None:
        st.markdown("<div id='detailed-view-anchor'></div>", unsafe_allow_html=True)
        if st.button("🔼 Thu gọn kịch bản chi tiết", disabled=is_system_busy):
            st.session_state.active_script_id = None
            st.session_state.scroll_to_top = True
            st.rerun()
            
        active_id = st.session_state.active_script_id
        asc = st.session_state.generated_details.get(int(active_id), st.session_state.generated_details.get(str(active_id), {}))
        vp = asc.get("voice", {})
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(asc.get('title', '')).upper()}**")
        
        director_summary_html = asc.get('director_summary', '')
        if not director_summary_html:
            tone_txt = vp.get('tone', 'Hội thoại tự nhiên')
            director_summary_html = f"🎙 <b>Chỉ đạo giọng:</b> {tone_txt}<br>👨‍👩‍👧 <b>Đồng nhất diện mạo:</b> 100% người Việt thuần túy, khóa chết 1 bộ trang phục và 1 kiểu tóc suốt 4 cảnh"
        st.markdown(f"<div class='detail-header-box'>{director_summary_html}</div>", unsafe_allow_html=True)
        
        for idx, scn in enumerate(asc.get("scenes", []), 1):
            vo_text = scn.get('voiceover', '')
            actual_words = count_words(vo_text)
            comma_count = vo_text.count(',') + vo_text.count(';')
            period_count = vo_text.count('.') + vo_text.count('!') + vo_text.count('?')
            curr_mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
            is_tts = ("Viral" not in curr_mode)
            speech_sec = scn.get('actual_speech_sec', calculate_speech_duration(vo_text, is_tts))
            
            dur_int = int(str(scn.get('dur', '6s')).replace('s', ''))
            safe_cushion = round(max(0.0, dur_int - speech_sec), 1)
            
            st.markdown(f"#### 📍 Phân cảnh {idx} - Giai đoạn {scn.get('aida_stage')}")
            st.markdown(f"<span class='timing-badge'>⏱ Khung phân cảnh chuẩn: {scn.get('dur')} | Khớp nhịp đọc thực tế: ~{speech_sec}s ({actual_words} từ, {comma_count} phẩy, {period_count} ngắt | ~{round(actual_words/max(1.0, speech_sec), 1)} từ/s) | 🛡 Đệm an toàn chống cụt: +{safe_cushion}s</span>", unsafe_allow_html=True)
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting')}*\n\n**😊 Vi biểu cảm & Cử chỉ:** *{scn.get('expression', 'Tự nhiên, rạng rỡ')}*\n\n**🎵 Hiệu ứng âm thanh (SFX & Foley):** *{scn.get('sfx', 'Âm thanh thực tế sống động')}*\n\n**🎙 Đạo diễn KOC:** *{scn.get('director')}*\n\n**💬 Thoại nhân vật nói trực tiếp on-camera (100% Giọng Hà Nội chuẩn, dùng 'nghìn', neo giá linh hoạt 'khoảng/gần/chưa tới'):** <div class='voiceover-text'>{vo_text}</div>", unsafe_allow_html=True)
            if scn.get('img_p'): st.markdown("**🖼 Prompt Ảnh (Midjourney / Flux - Tinh Gọn, Khóa Cứng Mặt, Tóc Đen Tuyền & On-Camera Lip-sync):**"); st.code(img_p := scn.get('img_p'), language="text"); safe_copy_button(img_p, f"📋 Sao Chép Ảnh Cảnh {idx}")
            if scn.get('vid_p'): st.markdown("**🎥 Prompt Video (Veo 3 Safe / Kling AI / Hedra - Bảo Tồn Dây Nối, Khóa Cứng Mặt & 100% On-Camera):**"); st.code(vid_p := scn.get('vid_p'), language="text"); safe_copy_button(vid_p, f"📋 Sao Chép Video Cảnh {idx}")
            st.markdown("---")

    st.markdown("### 🎬 **1. Kịch Bản ĐÃ Dựng Chi Tiết**")
    for outline in comp_sc:
        sc_id = outline["id"]
        with st.container(border=True):
            c1, c2, c3 = st.columns([2.5, 1, 1])
            c1.markdown(f"**#{sc_id}. {outline.get('title')}**")
            c1.caption(f"⚡ *{outline.get('hook')}*")
            if str(sc_id) != str(st.session_state.active_script_id):
                if c2.button("👁 Xem lại", key=f"r_{sc_id}", use_container_width=True, disabled=is_system_busy):
                    st.session_state.active_script_id = int(sc_id); st.session_state.scroll_to_detail = True; st.rerun()
            btn_clone_ph = c3.empty()
            if str(st.session_state.current_cloning_id) == str(sc_id):
                btn_clone_ph.markdown("<div style='background: #fffbeb; color: #dc2626; border-radius: 8px; padding: 8px; text-align: center; font-size: 13px; font-weight: bold; border: 1px solid #fca5a5;'>⏳ Đang nhân bản...</div>", unsafe_allow_html=True)
            else:
                if btn_clone_ph.button("🚀 Nhân bản", key=f"c_{sc_id}", type="primary", use_container_width=True, disabled=is_system_busy):
                    can_run, msg = check_usage_limit(st.session_state.current_email)
                    if can_run: st.session_state.current_cloning_id = sc_id; st.rerun()
                    else: st.error(msg)

    st.markdown("<br>### ⏳ **2. Kịch Bản Chờ Dựng**", unsafe_allow_html=True)
    for outline in pend_sc:
        sc_id = outline["id"]
        with st.container(border=True):
            c1, c2 = st.columns([3, 1.2])
            c1.markdown(f"**#{sc_id}. {outline.get('title')}** <span class=badge-pending>CHỜ DỰNG</span>", unsafe_allow_html=True)
            c1.caption(f"⚡ *{outline.get('hook')}*")
            btn_detail_ph = c2.empty()
            if str(st.session_state.current_processing_id) == str(sc_id):
                btn_detail_ph.markdown("<div style='background: #fffbeb; color: #d97706; border-radius: 8px; padding: 8px; text-align: center; font-size: 13px; font-weight: bold; border: 1px solid #fde68a;'>⏳ Đang dựng 4 cảnh...</div>", unsafe_allow_html=True)
            else:
                if btn_detail_ph.button("✨ Tạo chi tiết ngay", key=f"cr_{sc_id}", type="secondary", use_container_width=True, disabled=is_system_busy):
                    can_run, msg = check_usage_limit(st.session_state.current_email, is_detailing=True)
                    if can_run: st.session_state.current_processing_id = sc_id; st.rerun()
                    else: st.error(msg)

    if st.session_state.current_processing_id is not None:
        target_id_to_run = st.session_state.current_processing_id
        success = False
        error_msg = ""
        try:
            with st.spinner(f"⏳ Đang áp dụng cơ chế 100% On-camera Lip-sync, triệt tiêu thuyết minh và dựng kịch bản #{target_id_to_run}..."):
                create_scene_details(target_id_to_run, st.session_state.last_mode, st.session_state.last_style)
                st.session_state.active_script_id = int(target_id_to_run); st.session_state.scroll_to_detail = True; success = True
        except Exception as e: error_msg = str(e)
            
        st.session_state.current_processing_id = None
        if success: st.toast(f"✅ Đã hoàn tất dựng kịch bản #{target_id_to_run}!"); time.sleep(0.3); st.rerun()
        else: st.error(f"❌ Lỗi khi dựng kịch bản: {error_msg}")

    if st.session_state.current_cloning_id is not None:
        clone_id_to_run = st.session_state.current_cloning_id
        success = False
        error_msg = ""
        try:
            with st.spinner(f"⏳ Đang nhân bản 5 biến thể cho kịch bản #{clone_id_to_run}..."):
                new_clones = clone_script(clone_id_to_run)
                st.session_state.cloned_scripts.extend(new_clones); success = True
        except Exception as e: error_msg = str(e)
            
        st.session_state.current_cloning_id = None
        if success: st.toast("✅ Đã nhân bản thành công 5 kịch bản voice mới!"); time.sleep(0.3); st.rerun()
        else: st.error(f"❌ Lỗi khi nhân bản kịch bản: {error_msg}")

    st.markdown("--- \n##### ➕ **Gọi Thêm 5 Kịch Bản Mới**")
    cg1, cg2, cg3, cg4 = st.columns([1.5, 0.8, 1.2, 1.5])
    a_opts = ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Chia sẻ", "😂 Hài hước"]
    c_ang = cg1.selectbox("🧭 Chiến lược mới:", a_opts, key=f"ea_{st.session_state.reset_key}")
    c_num = cg2.number_input("Số diễn viên:", 1, 8, num_chars, key=f"en_{st.session_state.reset_key}")
    c_dur_choice = cg3.selectbox("⏳ Thời lượng:", ["Thời lượng động linh hoạt", "Tùy chỉnh (s)"], key=f"ed_{st.session_state.reset_key}")
    c_dur_str = f"Chính xác {cg3.number_input('Số giây:', 10, 300, 60, key=f'eds_{st.session_state.reset_key}')} giây." if "Tùy" in c_dur_choice else "Thời lượng động linh hoạt"
    c_nar = cg4.selectbox("🎙 Thuyết minh:", ["Nhân vật xuất hiện (On-camera)"], key=f"ena_{st.session_state.reset_key}")

    e_chars = []
    for i in range(c_num):
        c_r, c_i = st.columns([2, 1])
        e_role = c_r.text_input(f"Vai trò NV {i+1} mới:", key=f"er_{i}_{st.session_state.reset_key}")
        e_file = c_i.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"ef_{i}_{st.session_state.reset_key}", label_visibility="collapsed")
        if e_file: e_chars.append({"id": i+1, "role": e_role or f"Diễn viên {i+1}", "file": e_file})

    if st.button("🚀 Gọi Thêm 5 Kịch Bản Mới", type="primary", use_container_width=True, disabled=is_system_busy):
        can_run, msg = check_usage_limit(st.session_state.current_email)
        if can_run:
            with st.spinner("⏳ Đang sáng tạo thêm 5 kịch bản theo 5 bối cảnh đời thực khác nhau..."):
                p_chars = [{"id": c["id"], "role": c["role"]} for c in e_chars] if e_chars else st.session_state.character_profiles
                new_sc = generate_more_scripts(c_ang, c_num, e_chars, c_nar, c_dur_str, p_chars)
                st.session_state.expanded_scripts.extend(new_sc)
                st.toast("✅ Đã sinh thêm 5 kịch bản mới đa bối cảnh!"); time.sleep(0.4); st.rerun()
        else: st.error(msg)
