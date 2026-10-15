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
    rate = 5.0 if is_tiktok_shop else 4.0
    comma_pause = 0.08 if is_tiktok_shop else 0.15
    period_pause = 0.12 if is_tiktok_shop else 0.25
    return round((words / rate) + (commas * comma_pause) + (periods * period_pause), 1)

def snap_scene_bucket(dur_sec: float) -> str:
    if dur_sec <= 4.0: return "4s"
    elif dur_sec <= 6.0: return "6s"
    elif dur_sec <= 8.0: return "8s"
    else: return "10s"

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
# BỘ CHUẨN HÓA 100% GIỌNG HÀ NỘI & CHÍNH SÁCH ĐA NGÀNH HÀNG
# ==============================================================================
POLICY_REPLACEMENTS = {
    r'\btuyệt\s*đối\b': 'rất', r'\bhoàn\s*toàn\b': 'thực sự', r'\b100\s*%\b': 'rất nhiều',
    r'\bchắc\s*chắn\b': 'rất có thể', r'\bcam\s*kết\b': 'an tâm', r'\bdứt\s*điểm\b': 'cải thiện',
    r'\bđặc\s*trị\b': 'hỗ trợ', r'\bkhỏi\s*hẳn\b': 'đỡ hẳn', r'\bvĩnh\s*viễn\b': 'lâu dài',
    r'\bchuẩn\s*đét\b': 'vừa vặn', r'\bchữa\s*khỏi\b': 'hỗ trợ', r'\bthần\s*dược\b': 'bí quyết',
    r'\btốt\s*nhất\b': 'rất tốt', r'\bsố\s*1\b': 'hàng đầu', r'\btrắng\s*cấp\s*tốc\b': 'sáng khỏe tự nhiên',
    r'\bgiảm\s*béo\s*cấp\s*tốc\b': 'vóc dáng thon gọn', r'\bxóa\s*sạch\s*nám\b': 'mờ thâm sạm',
    r'\bthuốc\s*trị\b': 'sản phẩm hỗ trợ', r'\bđiều\s*trị\b': 'hỗ trợ cải thiện', r'\btriệt\s*để\b': 'hiệu quả'
}

SOUTHERN_TO_HANOI = {
    r'\bxài\b': 'dùng', r'\bbận\s+đồ\b': 'mặc đồ', r'\bbận\s+áo\b': 'mặc áo', r'\bbận\s+quần\b': 'mặc quần',
    r'\bbận\s+váy\b': 'mặc váy', r'\bly\s+nước\b': 'cốc nước', r'\bly\s+trà\b': 'cốc trà', r'\bly\s+đá\b': 'cốc đá',
    r'\bly\b(?=\s+(?:uống|nước|thủy tinh|nhựa))': 'cốc', r'\bmuỗng\b': 'thìa', r'\bgiùm\b': 'hộ', r'\bdùm\b': 'hộ',
    r'\btui\b': 'tôi', r'\bhén\b': 'nhỉ', r'\bnghen\b': 'nhé', r'\bhen\b': 'nhé', r'\brùi\b': 'rồi',
    r'\bmần\b': 'làm', r'\bkiếng\b': 'kính', r'\bđậu\s+phộng\b': 'lạc', r'\btrái\s+cây\b': 'hoa quả',
    r'\bhổng\b': 'không', r'\bthiệt\b': 'thật', r'\bmắc\s+cỡ\b': 'ngại', r'\bhết\s+sẩy\b': 'tuyệt cú mèo',
    r'\bquá\s+trời\b': 'rất nhiều', r'\bquá\s+chừng\b': 'rất nhiều', r'\bnè\b': 'này', r'\bnha\b': 'nhé'
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
    return p

def clean_analysis_text(text) -> str:
    if not text: return ""
    if isinstance(text, (dict, list)):
        return format_analysis_field(text)
    pattern = r'^(?:SẢN PHẨM LÀ GÌ\s*&?\s*(?:CÓ GÌ ĐẶC BIỆT)?|SẢN PHẨM DÀNH CHO AI|TẠI SAO NÊN MUA|DÙNG Ở ĐÂU\s*&?\s*(?:TIỆN LỢI LÀ GÌ)?|CÁCH SỬ DỤNG|THAO TÁC.*|MỤC ĐÍCH|ĐỐI TƯỢNG|LÝ DO MUA)\s*:\s*'
    return re.sub(pattern, '', str(text).strip(), flags=re.IGNORECASE).strip()

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
        return f"Nhân vật nói trực tiếp (On-camera): 100% Giọng [Nam/Nữ] HÀ NỘI CHUẨN bản địa đúng độ tuổi, phát âm chuẩn tròn vành rõ chữ, {speed_txt}."
    dirs = []
    for p in character_profiles:
        r = str(p.get('role', '')).lower()
        if any(k in r for k in ["bé", "con", "trẻ", "nhỏ", "gái", "trai", "thiếu nhi"]):
            dirs.append(f"• NV {p['id']} ({p['role']}): 100% Giọng THIẾU NHI HÀ NỘI CHUẨN đúng độ tuổi, trong trẻo, líu lo, ngây thơ, xưng con/cháu.")
        elif any(k in r for k in ["ông", "bà", "già", "cao tuổi"]):
            dirs.append(f"• NV {p['id']} ({p['role']}): 100% Giọng NGƯỜI CAO TUỔI HÀ NỘI CHUẨN đúng độ tuổi, từ tốn, đôn hậu, trầm ấm, phúc hậu.")
        elif any(k in r for k in ["bố", "ba", "chồng", "nam", "anh", "bác trai"]):
            dirs.append(f"• NV {p['id']} ({p['role']}): 100% Giọng NAM HÀ NỘI CHUẨN đúng độ tuổi, trầm ấm, chững chạc, nội lực, đĩnh đạc.")
        else:
            dirs.append(f"• NV {p['id']} ({p['role']}): 100% Giọng NỮ HÀ NỘI CHUẨN đúng độ tuổi, thanh lịch, ngọt ngào, dịu dàng, âm sắc trong sáng.")
    return " | ".join(dirs)

def generate_char_rules_string(profiles):
    if not profiles: return "100% người Việt Nam bản địa, tóc đen tự nhiên, khóa duy nhất 1 kiểu tóc và 1 bộ trang phục cụ thể suốt 4 cảnh."
    rules = "DANH SÁCH DIỄN VIÊN (KHÓA 100% NGƯỜI VIỆT & TRANG PHỤC CỐ ĐỊNH SUỐT 4 CẢNH):\n"
    for p in profiles: 
        rules += f" - Diễn viên {p['id']} ({p['role']}): 100% thuần Việt, tóc đen tự nhiên. KHÓA DUY NHẤT 1 BỘ TRANG PHỤC CỤ THỂ VÀ 1 KIỂU TÓC XUYÊN SUỐT 4 CẢNH.\n"
    return rules

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, angle):
    is_multi = (num_chars >= 2)
    format_direction = f"ĐỊNH DẠNG: TIỂU PHẨM ĐỐI THOẠI {num_chars} NHÂN VẬT THUẦN VIỆT NÓI TRỰC TIẾP." if is_multi else "ĐỊNH DẠNG: ĐỘC THOẠI KOC THUẦN VIỆT NÓI TRỰC TIẾP."
    strat_cmd = "BẠN PHẢI MIX ĐA DẠNG 5 GÓC ĐỘ NỘI DUNG." if "Tự động mix" in angle else f"VIẾT CẢ 5 KỊCH BẢN THEO: '{angle}'."
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL TIKTOK SHOP & VIRAL TRIỆU VIEW. PHONG CÁCH: {style}
    {strat_cmd} | {format_direction}
    🛑 CƯỠNG CHẾ 100% GIỌNG HÀ NỘI CHUẨN ĐÚNG ĐỘ TUỔI NÓI TRỰC TIẾP (ON-CAMERA LIP-SYNC DIALOGUE):
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
    
    🛑 CƠ CHẾ THỜI LƯỢNG ĐỘNG (FLEXIBLE DURATION BUCKETS - 4s, 6s, 8s, 10s):
    - KHÔNG BÓ CỨNG MẶC ĐỊNH MỖI CẢNH PHẢI CỐ ĐỊNH MẤY GIÂY. AI tự phân tích độ sâu của nội dung để tự do gán thời lượng '4s', '6s', '8s' hoặc '10s' cho từng phân cảnh.
    - Hoàn toàn có thể cả 4 cảnh đều 10s (tổng 40s), hoặc Cảnh 1 (8s), Cảnh 2-3-4 (10s), hoặc bất kỳ sự kết hợp nào logic nhất với câu chuyện.
    - Khống chế số từ tương thích chính xác với mốc thời lượng mà AI đã chọn:
      • Khung 4s: ~16 - 20 từ (tốc độ 4.8 - 5.2 từ/s)
      • Khung 6s: ~24 - 28 từ
      • Khung 8s: ~34 - 38 từ
      • Khung 10s: ~44 - 50 từ (TUYỆT ĐỐI CẤM vượt quá 50 từ/cảnh để tránh tràn sang 12s).

    🛑 KỸ THUẬT KỂ CHUYỆN LIỀN MẠCH & ĐÀO SÂU CÔNG NĂNG THỰC TẾ (SEAMLESS STORYTELLING & DEEP UTILITY):
    - CẢ 4 CẢNH KHI GHÉP LẠI PHẢI TẠO THÀNH 1 ĐOẠN VĂN LIỀN KHÚC, TỰ NHIÊN, ĐỜI THƯỜNG, CÓ SỢI CHỈ ĐỎ DẪN DẮT CẢM XÚC:
      • Cảnh 1: Mở màn nêu bật nỗi đau/tình huống đời thực chân thật bằng văn phong gần gũi.
      • Cảnh 2: Mở đầu bằng từ nối tự nhiên ('Đấy, bí quyết là ở chỗ...', 'Điểm ăn tiền nhất của em này là...'). Đi sâu vào cấu tạo, cơ chế và thao tác thực tế.
      • Cảnh 3: Mở đầu bằng từ nối trải nghiệm ('Mà thích nhất cái đoạn...', 'Công nhận từ lúc có em này...'). Đào sâu cảm giác xúc giác, sự sung sướng và giá trị vượt trội khi dùng hàng ngày.
      • Cảnh 4: Chuyển nhịp mượt mà sang chốt deal ('Thế nên đợt này bác nào/mẹ nào đang cần thì...'). Đủ 3 vế: Đòn bẩy giá tương phản + Câu miễn trừ giá có hạn theo khung giờ + Lời kêu gọi ấm áp.
    - CẤM văn phong quảng cáo vô hồn; dùng văn phong tâm sự, chia sẻ chân thành của người dùng thực tế.

    🛑 CƯỠNG CHẾ 100% GIỌNG HÀ NỘI CHUẨN ĐÚNG ĐỘ TUỔI NÓI TRỰC TIẾP (ON-CAMERA LIP-SYNC DIALOGUE):
    - CẤM TUYỆT ĐỐI GIỌNG THUYẾT MINH NGOÀI. CẤM TRIỆT ĐỂ KHẨU NGỮ MIỀN NAM (xài, nè, nha, nghen, hén, tui, bận đồ, ly nước, muỗng, dùm, rùi, mần, thiệt, hổng...). Khẩu hình khớp từng từ với lời thoại.

    🛑 TÌNH HUỐNG TRẢI NGHIỆM ĐỜI THỰC & CHÍNH SÁCH ĐA NGÀNH:
    - Nếu là Mẹ & Bé: Bé trực tiếp trải nghiệm/sử dụng sản phẩm sinh động, người lớn LUÔN KỀ BÊN chăm sóc 100% khung hình.
    - Nếu là Dược / TPCN: Không khẳng định chữa bệnh, chỉ dùng 'hỗ trợ cải thiện', 'bổ sung'.
    - KHÓA CỨNG KẾT CẤU & BẢO TỒN TEM NHÃN IN: Giữ nguyên hình khối, kích thước, tem nhãn gốc và chữ in sắc nét. Không morphing.
    - BÀN TAY 5 NGÓN CHUẨN XÁC: Điểm tiếp xúc rõ ràng, ranh giới vật lý rành mạch giữa ngón tay và sản phẩm.

    🛑 ÂM THANH SFX & FOLEY ĐA TẦNG:
    - Cảnh 1: Tiếng whoosh nhẹ + tiếng thở dài/lạo xạo mô tả nỗi đau.
    - Cảnh 2: Tiếng cơ học thực tế: gõ cộc cộc, xoay vặn khục, vuốt vải ASMR...
    - Cảnh 3: Tiếng kích thích thèm muốn: rót nước đá róc rách, búng vải nẩy tưng tưng...
    - Cảnh 4: Tiếng chuông ting chốt đơn vui tai.

    🛑 TRIỆT TIÊU TOÀN BỘ ICON GIỎ HÀNG, NÚT BẤM VÀ SUB NỔI:
    - CẤM cử chỉ chỉ tay xuống góc trái. Hai bàn tay mở tự nhiên chân thành.
    - BẮT BUỘC định nghĩa 'character_matrix': (Face, Hair, Top, Bottom, Setting).
    - {char_rules}
    """

# ==============================================================================
# HÀM TẠO CHI TIẾT KỊCH BẢN - THỜI LƯỢNG ĐỘNG & THOẠI LIỀN MẠCH
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
    
    dna = st.session_state.get("content_analysis") or {}
    condensed_dna = {
        "product": dna.get("what_and_unique", ""),
        "hero_sku": dna.get("hero_sku_color", ""),
        "color_lock": dna.get("product_color_lock", ""),
        "dimensions": dna.get("product_dimensions", ""),
        "mechanism": dna.get("lid_mechanism", "Kết cấu cơ học chuẩn xác theo đời thực"),
        "how_to_use": dna.get("how_to_use", "Thao tác sử dụng thực tế chuẩn công thái học"),
        "price_anchor": dna.get("rounded_price_anchor", ""),
        "visual_dna": dna.get("prompt_dna_lock", "")
    }

    prompt_text = f"""
    THÔNG TIN SẢN PHẨM: {json.dumps(condensed_dna, ensure_ascii=False)}
    KỊCH BẢN #{target_id}: TIÊU ĐỀ: '{fixed_title}' | HOOK GỐC: '{fixed_hook}' | BỐI CẢNH: {outline.get('setting', 'Không gian thực tế phù hợp')}
    HÌNH THỨC: 100% Lời thoại nhân vật nói trực tiếp trên hình bằng Giọng Hà Nội chuẩn đúng độ tuổi, tốc độ 4.8 - 5.2 từ/s. TUYỆT ĐỐI CẤM TỪ NGỮ MIỀN NAM.
    
    🛑 CHỈ THỊ THỜI LƯỢNG ĐỘNG & NỘI DUNG LIỀN MẠCH:
    1. TỰ DO GÁN THỜI LƯỢNG (4s, 6s, 8s, 10s): AI tự chọn thời lượng 'dur' ('4s', '6s', '8s', '10s') cho từng cảnh tùy theo lượng thông tin. Cả 4 cảnh đều 10s hoặc kết hợp linh hoạt đều được!
    2. SỐ TỪ TƯƠNG ỨNG MỐC ĐÃ CHỌN: 4s (~16-20 từ), 6s (~24-28 từ), 8s (~34-38 từ), 10s (~44-50 từ). Tuyệt đối không quá 50 từ/cảnh.
    3. MẠCH NỘI DUNG LIỀN KHÚC: Ghép 4 cảnh lại phải thành 1 đoạn văn tâm sự, chia sẻ hoàn chỉnh, tự nhiên, cuốn hút.
    4. CẢNH 4 BẮT BUỘC ĐỦ 3 VẾ: Đòn bẩy giá tương phản + Câu miễn trừ giá có hạn theo khung giờ + Lời chào ấm áp.
    5. Trả về 'clean_product_name_en': Tên/mô tả sản phẩm tiếng Anh ngắn gọn dưới 15 từ.
    
    ĐỊNH DẠNG JSON TRẢ VỀ:
    {{
        "title": "{fixed_title}",
        "voice": {{"tone": "{voice_guidance}"}},
        "outfit_vi": "Mô tả chi tiết: Áo trên cụ thể + Quần/Váy cụ thể + Kiểu tóc cụ thể khóa cứng 4 cảnh",
        "clean_product_name_en": "Concise photorealistic English description of the hero product under 15 words",
        "character_matrix": {{
            "full_characters_appearance": "Authentic native Vietnamese character(s), natural Vietnamese facial features, warm skin tone",
            "locked_hairstyles": "Mô tả 1 kiểu tóc cố định phù hợp bối cảnh bằng tiếng Anh",
            "locked_tops": "Mô tả 1 mẫu áo trên cụ thể phù hợp bối cảnh bằng tiếng Anh",
            "locked_bottoms": "Mô tả 1 mẫu quần hoặc váy bằng tiếng Anh",
            "locked_setting": "Mô tả 1 góc bối cảnh cố định phù hợp sản phẩm bằng tiếng Anh",
            "locked_negative": "Caucasian, white, blonde hair, blue eyes, yellow cart icon, shopping bag graphic, animated button, simulated UI overlay, subtitles, on-screen text, typography, watermark, wrinkles, deformed hands, extra fingers, product morphing, shape shifting, disappearing label, fading text, blurred sticker"
        }},
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention",
                "dur": "6s",
                "setting": "Mô tả bối cảnh...",
                "camera_shot": "Vertical 9:16 eye-level medium shot",
                "expression": "Ánh mắt đồng cảm chân thành, hơi nhíu mày trăn trở nỗi đau",
                "sfx": "Tiếng whoosh vút nhẹ mở màn 3s đầu kết hợp tiếng thở dài nhẹ thực tế",
                "action_en": "Authentic situational storytelling. Character interacting naturally in a real-life context with expressive lip movements.",
                "director": "Attention | Tình huống đời thực mở màn | Nhân vật nói trực tiếp giọng Hà Nội chuẩn | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại mở màn tự nhiên bằng tiếng Hà Nội chuẩn..."
            }},
            {{
                "scene": 2, "aida_stage": "Interest",
                "dur": "8s",
                "setting": "Mô tả bối cảnh...",
                "camera_shot": "Cinematic tight macro close-up with 85mm lens, shallow depth of field, razor-sharp focus on product details and hand ergonomics",
                "expression": "Ánh mắt bừng sáng, chân mày giãn ra, thần thái tự tin",
                "sfx": "Tiếng gõ cộc cộc đanh chắc hoặc tiếng xoay nắp ren khục chắc nịch / tiếng vuốt vải sột soạt ASMR",
                "action_en": "Lively situational demonstration: Character actively interacting with the product in a real-world scenario with steady natural five-finger hands.",
                "director": "Interest | Cận cảnh Macro 85mm thao tác công năng chuẩn đời thực | SFX thực tế ASMR | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại đào sâu công năng nối tiếp mượt mà từ cảnh 1 bằng tiếng Hà Nội chuẩn..."
            }},
            {{
                "scene": 3, "aida_stage": "Desire",
                "dur": "10s",
                "setting": "Mô tả bối cảnh...",
                "camera_shot": "Cinematic tight macro shot showcasing sensory tactile satisfaction and premium quality",
                "expression": "Nụ cười mãn nguyện, ánh mắt ánh lên sự thỏa mãn giác quan, gật đầu khẳng định",
                "sfx": "Tiếng rót nước róc rách đá lạnh lách cách vang giòn / tiếng búng vải nẩy tưng tưng / tiếng ASMR giác quan",
                "action_en": "Genuine lifestyle experience. Character enjoying the practical sensory benefits of the product. Joyful satisfied micro-expression.",
                "director": "Desire | Thể hiện độ hài lòng và trải nghiệm giác quan thực tế | SFX sống động | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại đặc tả trải nghiệm thực tế sâu sắc nối tiếp tự nhiên từ cảnh 2 bằng tiếng Hà Nội chuẩn..."
            }},
            {{
                "scene": 4, "aida_stage": "Action",
                "dur": "8s",
                "setting": "Mô tả bối cảnh...",
                "camera_shot": "Vertical 9:16 warm eye-level medium closing shot",
                "expression": "Nụ cười rạng rỡ, ánh mắt chân thành ấm áp, hai bàn tay mở tự nhiên hướng về camera",
                "sfx": "Tiếng chuông ting trong trẻo vui tai kích thích hành động",
                "action_en": "Warm confident closing shot. Character smiling warmly into camera, speaking directly with sincere welcoming open-palm gestures. Pure cinematic frame.",
                "director": "Action | Nhân vật nói trực tiếp chốt deal đòn bẩy giá tương phản kèm câu miễn trừ giá hợp quy | SFX chuông ting vui tai | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại chốt deal gồm giá sốc + câu rào miễn trừ giá có hạn theo khung giờ + lời chào ấm áp kết nối trọn vẹn toàn bộ kịch bản..."
            }}
        ]
    }}
    """
    res = call_gemini([prompt_text], get_sys_inst_details(current_active_mode, style, "On-camera", char_rules, "Thời lượng động linh hoạt", num_chars, char_profiles), max_tokens=6500)
    if not res: raise Exception("AI không phản hồi hoặc trả về dữ liệu rỗng. Vui lòng bấm tạo lại.")
    
    scenes = res.get("scenes") or res.get("script") or []
    if not scenes: raise Exception("AI không tạo được danh sách phân cảnh. Vui lòng bấm tạo lại.")
    
    c_mat = res.get("character_matrix") or {}
    full_char = c_mat.get("full_characters_appearance") or "Authentic native Vietnamese character(s), natural Vietnamese facial features, warm skin tone"
    locked_hair = c_mat.get("locked_hairstyles") or "natural dark hair worn loose over shoulders"
    locked_tops = c_mat.get("locked_tops") or "neat casual shirt"
    locked_bottoms = c_mat.get("locked_bottoms") or "straight trousers"
    locked_setting = c_mat.get("locked_setting") or (outline.get("setting") or "warm cozy realistic setting")
    locked_negative = c_mat.get("locked_negative") or "Caucasian, blonde, deformed hands, extra fingers, text, watermark, typography, subtitles, floating cart icon, distorted geometry"
    clean_prod_en = res.get("clean_product_name_en") or f"authentic {condensed_dna.get('hero_sku', '')} {condensed_dna.get('product', 'product')}".strip()
    
    unified_subject = f"{full_char}, strictly with {locked_hair}. Invariant Wardrobe: wearing {locked_tops} and {locked_bottoms}"
    
    dur_map = {"4s": 4, "6s": 6, "8s": 8, "10s": 10}
    total_sec = 0.0
    for scn in scenes:
        if "voiceover" in scn: scn["voiceover"] = sanitize_policy_text(scn["voiceover"])
        if "director" in scn: scn["director"] = sanitize_policy_text(scn["director"])
        
        actual_speech_time = calculate_speech_duration(scn.get("voiceover", ""), is_tiktok_shop)
        
        # PHÂN BỔ THỜI LƯỢNG ĐỘNG: Lấy mốc AI chọn, đối soát với thời gian đọc thực tế để khung hình luôn >= thời gian đọc
        ai_dur = scn.get("dur", "")
        ai_sec = dur_map.get(ai_dur, 0)
        calc_bucket = snap_scene_bucket(actual_speech_time)
        calc_sec = dur_map.get(calc_bucket, 6)
        
        final_sec = max(ai_sec, calc_sec) if ai_sec > 0 else calc_sec
        final_bucket = f"{final_sec}s"
        
        scn["dur"] = final_bucket
        scn["actual_speech_sec"] = actual_speech_time
        total_sec += float(final_sec)
        
        clean_action = re.sub(r'\[.*?\]', '', scn.get("action_en", "")).strip()
        camera_shot = scn.get("camera_shot", "Vertical 9:16 cinematic shot")
        sfx_sound = scn.get("sfx", "Layered realistic ambient sensory Foley sounds")
        micro_expr = scn.get("expression", "Natural expressive facial micro-emotions")
        
        # PROMPT ẢNH TINH GỌN (FLUX / MIDJOURNEY)
        scn["img_p"] = (
            f"{camera_shot}. {unified_subject}. "
            f"Setting: {locked_setting}. "
            f"Action: Holding and interacting naturally with {clean_prod_en}, looking directly at camera with {micro_expr}. "
            f"Product Details: {clean_prod_en}, rigid non-deformable form, original intact label and clear textures. "
            f"Quality: Anatomically correct five-finger hands with realistic grip, photorealistic commercial lifestyle photography, natural lighting. "
            f"Negative prompt: {locked_negative}."
        )
        
        # PROMPT VIDEO VEO 3 SAFE / KLING AI
        speaker_line = scn.get("voiceover", "")
        audio_part = f' Direct on-camera spoken dialogue at 0.00s. Character visibly speaking with natural lip-sync mouth movement. Audio: "{speaker_line}", Layered Foley SFX: [{sfx_sound}].'
        raw_vid = (
            f"{camera_shot}. Wholesome live-action commercial footage. {unified_subject}. "
            f"Setting: {locked_setting}. "
            f"Action: {clean_action}. Micro-expression: {micro_expr}.{audio_part} "
            f"Product Invariance: Authentic {clean_prod_en}, strictly rigid geometry, intact original manufacturer label, zero morphing. "
            f"Anatomy: Anatomically correct hands with strictly five fingers per hand, natural smooth hand gestures, zero limb morphing. "
            f"Strictly pure footage: ABSOLUTELY NO yellow cart icons, NO animated buttons, NO UI stickers, NO on-screen subtitles, NO text. "
            f"Negative prompt: {locked_negative}."
        )
        scn["vid_p"] = sanitize_veo3_prompt(raw_vid)
        
    res["scenes"] = scenes
    res["total_dur"] = f"Khoảng {int(total_sec)} giây"
    res["director_summary"] = f"⏱ <b>Thời lượng kịch bản:</b> Khoảng {int(total_sec)} giây (Thời lượng động 4s/6s/8s/10s theo độ sâu nội dung | Khung cảnh luôn ≥ thời gian đọc) | 🎙 <b>Chỉ đạo giọng:</b> 100% nhân vật nói trực tiếp trên hình (100% Giọng Hà Nội chuẩn đúng độ tuổi | Tốc độ 4.8 - 5.2 từ/s)<br>👗 <b>Ma trận khóa diện mạo 5 lớp:</b> {res.get('outfit_vi', 'Khóa chết áo, quần/váy, kiểu tóc và bối cảnh suốt 4 cảnh')}<br>📖 <b>Mạch truyện liền khúc:</b> 4 cảnh gắn kết logic thành 1 câu chuyện hoàn chỉnh | 🛡 <b>Tuân thủ chính sách:</b> Câu miễn trừ giá có hạn theo khung giờ<br>🔒 <b>Bảo tồn sản phẩm:</b> Khóa cứng kết cấu hình học bất biến, bảo tồn 100% tem nhãn và chữ in nguyên bản<br>🎵 <b>Hệ thống đa giác quan:</b> Âm thanh SFX & Foley đa tầng | 😊 <b>Vi biểu cảm & hình thể KOC:</b> Biến thiên tự nhiên theo tâm lý AIDA<br>📍 <b>Bối cảnh logic cố định:</b> {locked_setting}<br>🚫 <b>Bộ lọc thị giác:</b> Triệt tiêu hoàn toàn icon giỏ hàng, nút bấm ảo và chữ phụ đề nổi"
    
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
    NHIỆM VỤ: Giữ nguyên 100% công năng và đòn bẩy neo giá kèm câu miễn trừ giá hợp quy chuẩn, nhân bản thành 5 biến thể kịch bản thoại mới theo 5 góc kể chuyện liền mạch, hấp dẫn. 100% nhân vật nói trực tiếp bằng Giọng Hà Nội chuẩn đúng độ tuổi, tốc độ 4.8 - 5.2 từ/s. TUYỆT ĐỐI CẤM TỪ NGỮ MIỀN NAM.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên biến thể 1", "setting": "Bối cảnh mới...", "hook": "Câu hook ngắn gọn do nhân vật nói trực tiếp bằng tiếng Hà Nội chuẩn...", "actors": 1, "character_roles": ["Nữ KOC Hà Nội"] }},
            {{ "id": {cur_len+2}, "title": "Tên biến thể 2", "setting": "...", "hook": "...", "actors": 1, "character_roles": ["Cô nàng công sở"] }},
            {{ "id": {cur_len+3}, "title": "Tên biến thể 3", "setting": "...", "hook": "...", "actors": 2, "character_roles": ["Mẹ trẻ", "Bé gái"] }},
            {{ "id": {cur_len+4}, "title": "Tên biến thể 4", "setting": "...", "hook": "...", "actors": 1, "character_roles": ["KOC trẻ trung"] }},
            {{ "id": {cur_len+5}, "title": "Tên biến thể 5", "setting": "...", "hook": "...", "actors": 2, "character_roles": ["Đôi bạn thân"] }}
        ]
    }}
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, "On-camera", "", target.get("actors", 1), "Nhân bản thoại"), max_tokens=2200)
    clones = res.get("outlines", res.get("script_outlines", []))
    formatted_clones = []
    for idx, cl in enumerate(clones):
        new_actors_count = cl.get("actors", 1)
        raw_roles = cl.get("character_roles", [f"Diễn viên {i+1}" for i in range(new_actors_count)])
        new_profiles = [{"id": i+1, "role": r} for i, r in enumerate(raw_roles)]
        formatted_clones.append({
            "id": cur_len + idx + 1, "title": cl.get("title", f"Biến thể kịch bản #{cur_len + idx + 1}"),
            "setting": cl.get("setting", "Không gian phù hợp"), "hook": sanitize_policy_text(cl.get("hook", "")),
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
    100% LỜI THOẠI LÀ DO NHÂN VẬT NÓI TRỰC TIẾP BẰNG GIỌNG HÀ NỘI CHUẨN ĐÚNG ĐỘ TUỔI (4.8 - 5.2 từ/s). TUYỆT ĐỐI CẤM TỪ NGỮ MIỀN NAM.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên kịch bản mới", "setting": "Bối cảnh chuẩn...", "hook": "Câu hook ngắn gọn nhân vật nói trực tiếp bằng tiếng Hà Nội chuẩn...", "actors": {num_chars} }}
        ]
    }}
    BẮT BUỘC ĐỦ 5 KỊCH BẢN.
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, "On-camera", char_rules, num_chars, angle), max_tokens=2200)
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
        tabs = st.tabs(["🔐 Đăng Nhập", "🚀 Đăng Ký Dùng Thử"])
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
                submit_reg = st.form_submit_button("🚀 Đăng Ký Dùng Thử", type="secondary", use_container_width=True)
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
                100% LỜI THOẠI LÀ DO CHÍNH NHÂN VẬT MỞ MIỆNG NÓI TRỰC TIẾP TRƯỚC ỐNG KÍNH BẰNG GIỌNG HÀ NỘI CHUẨN ĐÚNG ĐỘ TUỔI, TỐC ĐỘ 4.8 - 5.2 TỪ/S.
                🛑 CẤM TUYỆT ĐỐI KHẨU NGỮ MIỀN NAM. 100% dùng từ ngữ Hà Nội chuẩn.
                CHỈ ĐẠO HERO SKU: {override_instruction}
                
                BẮT BUỘC TRẢ VỀ JSON:
                {{
                    "content_analysis": {{
                        "target_audience": "Tệp khách hàng mục tiêu",
                        "core_value": "Giá trị cốt lõi",
                        "pain_points": "Nỗi đau thực tế",
                        "hook_element": "Yếu tố giật gân 3 giây đầu",
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
                        "detected_prices": "Quét OCR giá tiền (giá gốc và giá sale)",
                        "rounded_price_anchor": "TÂM LÝ HỌC NEO GIÁ TƯƠNG PHẢN: Làm tròn giá gốc TIẾN LÊN mốc số chẵn lớn gần nhất và làm mềm giá sale. Định dạng: 'Giá gốc gần [X] -> Nay giảm sốc chỉ còn [Y]'",
                        "product_dimensions": "Thông số kích thước",
                        "prompt_dna_lock": "Visual DNA cho video"
                    }},
                    "outlines": [
                        {{ "id": 1, "title": "Tên kịch bản 1", "setting": "Bối cảnh chuẩn...", "hook": "Câu hook ngắn gọn nhân vật nói trực tiếp bằng tiếng Hà Nội chuẩn...", "actors": {num_chars} }},
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
                    cb, cm = compress_image_bytes(c['file'], 768, 75)
                    payload.extend([f"ACTOR {c['id']}:", types.Part.from_bytes(data=cb, mime_type=cm)])
                payload.append(prompt)
                
                res = call_gemini(payload, get_sys_inst_outlines(mode, style, "On-camera", char_rules, num_chars, initial_angle), max_tokens=2500)
                st.session_state.content_analysis = res.get("content_analysis")
                outlines = res.get("outlines", res.get("script_outlines", []))
                for o in outlines: 
                    if "hook" in o: o["hook"] = sanitize_policy_text(o["hook"])
                    o.update({"duration_instruction": "Thời lượng động linh hoạt", "narrator_mode": "Nhân vật xuất hiện (On-camera)", "character_profiles": st.session_state.character_profiles, "actors": num_chars})
                st.session_state.update({"all_scripts": outlines, "cloned_scripts": [], "expanded_scripts": [], "generated_details": {}, "active_script_id": None})
                st.toast("✅ Đã phân tích xong đầy đủ DNA!"); time.sleep(0.3); st.rerun()
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
        <div class="dna-card-title">⚙ 4. Vật lý, Cơ chế & Mức giá</div>
        <div class="dna-row"><span class="dna-label">📐 Thông số kích thước:</span><span class="dna-text">{clean_analysis_text(ca.get('product_dimensions', ''))}</span></div>
        <div class="dna-row"><span class="dna-label">🎨 Khóa màu chi tiết:</span><span class="dna-text">{clean_analysis_text(ca.get('product_color_lock', ''))}</span></div>
        <div class="dna-row"><span class="dna-label">⚙ Cấu tạo cơ học thực tế:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{clean_analysis_text(ca.get('lid_mechanism', 'Bình thường'))}</span></div>
        <div class="dna-row"><span class="dna-label">💰 Mức giá (OCR):</span><span class="dna-text">{clean_analysis_text(ca.get('detected_prices', ''))}</span></div>
        <div class="dna-row"><span class="dna-label" style="color:#dc2626;">🎯 Đòn bẩy giá tương phản:</span><span class="dna-text" style="color:#dc2626; font-weight:700;">{clean_analysis_text(ca.get('rounded_price_anchor', ''))}</span></div>
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
            
            st.markdown(f"#### 📍 Phân cảnh {idx} - Giai đoạn {scn.get('aida_stage')}")
            st.markdown(f"<span class='timing-badge'>⏱ Khung phân cảnh chuẩn: {scn.get('dur')} | Khớp nhịp đọc thực tế: ~{speech_sec}s ({actual_words} từ, {comma_count} dấu phẩy, {period_count} dấu ngắt câu | ~{round(actual_words/max(1.0, speech_sec), 1)} từ/s)</span>", unsafe_allow_html=True)
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting')}*\n\n**😊 Vi biểu cảm & Cử chỉ:** *{scn.get('expression', 'Tự nhiên, rạng rỡ')}*\n\n**🎵 Hiệu ứng âm thanh (SFX & Foley):** *{scn.get('sfx', 'Âm thanh thực tế sống động')}*\n\n**🎙 Đạo diễn KOC:** *{scn.get('director')}*\n\n**💬 Thoại nhân vật nói trực tiếp (100% Giọng Hà Nội chuẩn đúng độ tuổi):** <div class='voiceover-text'>{vo_text}</div>", unsafe_allow_html=True)
            if scn.get('img_p'): st.markdown("**🖼 Prompt Ảnh (Midjourney / Flux - Tinh Gọn & Chuẩn Thực Tế):**"); st.code(img_p := scn.get('img_p'), language="text"); safe_copy_button(img_p, f"📋 Sao Chép Ảnh Cảnh {idx}")
            if scn.get('vid_p'): st.markdown("**🎥 Prompt Video (Veo 3 Safe / Kling AI / Hedra - Bảo Tồn Tem Nhãn & Trải Nghiệm Sống Động):**"); st.code(vid_p := scn.get('vid_p'), language="text"); safe_copy_button(vid_p, f"📋 Sao Chép Video Cảnh {idx}")
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
            with st.spinner(f"⏳ Đang áp dụng thời lượng động và dựng kịch bản #{target_id_to_run}..."):
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
            with st.spinner("⏳ Đang sáng tạo thêm 5 kịch bản theo mô hình AIDA..."):
                p_chars = [{"id": c["id"], "role": c["role"]} for c in e_chars] if e_chars else st.session_state.character_profiles
                new_sc = generate_more_scripts(c_ang, c_num, e_chars, c_nar, c_dur_str, p_chars)
                st.session_state.expanded_scripts.extend(new_sc)
                st.toast("✅ Đã sinh thêm 5 kịch bản mới!"); time.sleep(0.4); st.rerun()
        else: st.error(msg)
