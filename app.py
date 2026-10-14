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

# LỚP KHÓA CỨNG GIAO DIỆN CHỐNG CLICK ĐÈ KHI AI ĐANG CHẠY
def lock_ui():
    st.markdown("""
    <style>
        div[data-testid="stAppViewContainer"], div[data-testid="stSidebar"] {
            pointer-events: none !important;
            user-select: none !important;
        }
        button, div[data-testid="stButton"] button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"] {
            pointer-events: none !important;
            opacity: 0.35 !important;
            cursor: not-allowed !important;
            filter: grayscale(60%) !important;
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

# TÍNH TOÁN THỜI LƯỢNG THOẠI CHUẨN XÁC: TỪ + DẤU NGẮT NGHỈ
def calculate_speech_duration(text: str, is_tiktok_shop: bool = True) -> float:
    words = count_words(text)
    commas = text.count(',') + text.count(';')
    periods = text.count('.') + text.count('!') + text.count('?')
    rate = 4.6 if is_tiktok_shop else 3.8
    comma_pause = 0.20
    period_pause = 0.35
    duration = (words / rate) + (commas * comma_pause) + (periods * period_pause)
    return round(duration, 1)

# KHÓA TRẦN THỜI LƯỢNG THEO TỪNG GIAI ĐOẠN AIDA (CHỐNG LỖI CẢNH 1 DÀI 10S)
def snap_scene_bucket(stage: str, dur_sec: float) -> str:
    stage_str = str(stage).lower()
    if any(k in stage_str for k in ["attention", "action", "hook", "chốt"]):
        # Cảnh 1 và Cảnh 4: Chỉ cho phép mốc 4s hoặc 6s
        return "4s" if dur_sec <= 4.8 else "6s"
    elif "interest" in stage_str:
        # Cảnh 2: Cho phép mốc 6s hoặc 8s
        return "6s" if dur_sec <= 6.8 else "8s"
    else:
        # Cảnh 3 (Desire): Cho phép mốc 8s hoặc 10s
        return "8s" if dur_sec <= 8.8 else "10s"

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

# ==============================================================================
# BỘ LỌC CHÍNH SÁCH ĐA NGÀNH NGHỀ & VEO 3 SAFE FILTER
# ==============================================================================
POLICY_REPLACEMENTS = {
    r'\btuyệt\s*đối\b': 'rất', r'\bhoàn\s*toàn\b': 'thực sự', r'\b100\s*%\b': 'rất nhiều',
    r'\bchắc\s*chắn\b': 'rất có thể', r'\bcam\s*kết\b': 'an tâm', r'\bdứt\s*điểm\b': 'cải thiện',
    r'\bđặc\s*trị\b': 'hỗ trợ', r'\bkhỏi\s*hẳn\b': 'đỡ hẳn', r'\bvĩnh\s*viễn\b': 'lâu dài',
    r'\bchuẩn\s*đét\b': 'vừa vặn', r'\bchữa\s*khỏi\b': 'hỗ trợ', r'\bthần\s*dược\b': 'bí quyết',
    r'\btốt\s*nhất\b': 'rất tốt', r'\bsố\s*1\b': 'hàng đầu', r'\btrắng\s*cấp\s*tốc\b': 'sáng khỏe tự nhiên',
    r'\bgiảm\s*béo\s*cấp\s*tốc\b': 'vóc dáng thon gọn', r'\bxóa\s*sạch\s*nám\b': 'mờ thâm sạm'
}

def sanitize_policy_text(text: str) -> str:
    if not text: return ""
    cleaned = text
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
    return p

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
                "last_generation_date": "", "active_session_id": row.get("active_session_id", "")
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

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict): return "<br>".join([f"• <b>{str(k).replace('_', ' ').title()}:</b> {str(v)}" for k, v in field_val.items()])
    if isinstance(field_val, list): return "<br>".join([f"• {str(item)}" for item in field_val])
    return "".join([f"<div style='margin-left: 10px; margin-top: 3px;'>• {line.strip()}</div>" for line in str(field_val).split('<br>') if line.strip()])

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
    ("last_mode", ""), ("last_style", ""), ("last_narrator", ""),
    ("target_duration_instruction", ""), ("character_profiles", []), ("current_project_id", None),
    ("saved_reference_images", []), ("show_all_projects", False), ("show_all_admin_accounts", False),
    ("current_processing_id", None), ("current_cloning_id", None)
]:
    if key not in st.session_state: st.session_state[key] = default_val

is_system_busy = (
    st.session_state.get("current_processing_id") is not None or 
    st.session_state.get("current_cloning_id") is not None
)

if is_system_busy:
    lock_ui()

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
    candidate += "}" if candidate.count("{") > candidate.count("}") else ""
    candidate += "]" if candidate.count("[") > candidate.count("]") else ""
    res = try_parse(candidate)
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
        return "Giọng [Nam/Nữ] HÀ NỘI GỐC, tốc độ BẮN TỈA DỒN DẬP (4.5 - 4.8 từ/s), hình thể KOC rướn người, chém nhịp dứt khoát." if is_tiktok_shop else "Giọng [Nam/Nữ] HÀ NỘI GỐC, biến thiên cảm xúc linh hoạt."
    else:
        dirs = []
        for p in character_profiles:
            r = str(p.get('role', '')).lower()
            if any(k in r for k in ["bé", "con", "trẻ", "nhỏ", "gái", "trai"]):
                dirs.append(f"NV {p['id']} ({p['role']}): Giọng thiếu nhi miền Bắc líu lo, ngây thơ, lém lỉnh.")
            elif any(k in r for k in ["bố", "ba", "chồng", "nam"]):
                dirs.append(f"NV {p['id']} ({p['role']}): Giọng nam miền Bắc trầm ấm, đĩnh đạc.")
            elif any(k in r for k in ["ông", "bà"]):
                dirs.append(f"NV {p['id']} ({p['role']}): Giọng người lớn tuổi miền Bắc từ tốn, ấm áp.")
            else:
                dirs.append(f"NV {p['id']} ({p['role']}): Giọng nữ Hà Nội chuẩn dịu dàng, năng lượng cao.")
        return " | ".join(dirs)

def generate_char_rules_string(profiles):
    if not profiles: return "100% người Việt Nam bản địa, tóc đen tự nhiên, khóa duy nhất 1 kiểu tóc và 1 bộ trang phục cụ thể suốt 4 cảnh."
    rules = "DANH SÁCH DIỄN VIÊN (KHÓA 100% NGƯỜI VIỆT & TRANG PHỤC CỐ ĐỊNH SUỐT 4 CẢNH):\n"
    for p in profiles: 
        rules += f" - Diễn viên {p['id']} ({p['role']}): 100% thuần Việt, tóc đen tự nhiên. KHÓA DUY NHẤT 1 BỘ TRANG PHỤC CỤ THỂ VÀ 1 KIỂU TÓC XUYÊN SUỐT 4 CẢNH.\n"
    return rules

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, angle):
    is_multi = (num_chars >= 2)
    format_direction = f"ĐỊNH DẠNG: TIỂU PHẨM ĐỐI THOẠI {num_chars} NHÂN VẬT THUẦN VIỆT." if is_multi else "ĐỊNH DẠNG: ĐỘC THOẠI KOC THUẦN VIỆT."
    strat_cmd = "BẠN PHẢI MIX ĐA DẠNG 5 GÓC ĐỘ NỘI DUNG." if "Tự động mix" in angle else f"VIẾT CẢ 5 KỊCH BẢN THEO: '{angle}'."
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL TIKTOK SHOP & VIRAL TRIỆU VIEW. PHONG CÁCH: {style}
    {strat_cmd} | {format_direction}
    🛑 BỘ LỌC CHÍNH SÁCH BÁN HÀNG ĐA NGÀNH NGHỀ:
    - CẤM: 'tuyệt đối', 'hoàn toàn', '100%', 'cam kết', 'dứt điểm', 'đặc trị', 'khỏi hẳn', 'vĩnh viễn'.
    - AN TOÀN TRẺ EM (MINOR SAFETY): Trẻ em LUÔN CÓ NGƯỜI LỚN KỀ BÊN trong mọi cảnh, TUYỆT ĐỐI CẤM để bé một mình trong khung hình.
    - DƯỢC / TPCN: Không nhận là thuốc điều trị, chỉ dùng từ 'hỗ trợ', 'bổ sung'.
    🛑 100% NGƯỜI VIỆT THUẦN TÚY: Tuyệt đối cấm mặt ngoại quốc.
    🛑 {char_rules}
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction, num_chars, character_profiles):
    is_on_camera = "On-camera" in narrator_mode
    is_multi = (num_chars >= 2)
    voice_guidance = build_voice_direction(mode, num_chars, character_profiles)

    dialogue_type_rule = f"🛑 ĐỐI THOẠI {num_chars} NHÂN VẬT: Tách từng câu thoại (Mẹ: '...' | Bé: '...'). Giọng thiếu nhi ngây thơ, mẹ dịu dàng." if is_multi else "🛑 ĐỘC THOẠI KOC: Lời thoại liền mạch 1 giọng đọc KOC Hà Nội chuẩn, tốc độ 4.5 - 4.8 từ/s."
    outro_instruction = "🛑 CẢNH 4 (VIRAL): Cả nhà cười tươi vẫy tay chào camera, kêu gọi follow." if "Viral" in mode else "🛑 CẢNH 4 (TIKTOK SHOP): Kêu gọi mua hàng tinh tế hướng về góc trái."
    audio_cmd = "Chèn `Audio:` vào `vid_p`." if is_on_camera else "Không chèn thoại vào `vid_p`."

    return f"""
    BẠN LÀ BẬC THẦY BIÊN KỊCH TIKTOK THỰC CHIẾN VIỆT NAM. PHONG CÁCH: {style}
    CHỈ ĐẠO GIỌNG: {voice_guidance}
    {dialogue_type_rule}
    {outro_instruction}
    
    🛑 LUẬT KHỐNG CHẾ SỐ TỪ VÀ DẤU NGẮT NGHỈ CHUẨN XÁC THEO MỐC THỜI LƯỢNG (4s, 6s, 8s, 10s):
    - Tốc độ đọc: 4.6 từ/giây. Dấu phẩy nghỉ 0.20s; Dấu chấm/than/hỏi nghỉ 0.35s.
    - CẢNH 1 (ATTENTION - HOOK): BẮT BUỘC CHỌN 4s (14-17 từ) HOẶC 6s (22-26 từ). TUYỆT ĐỐI CẤM vượt quá 26 từ! (Lỗi 47 từ là vi phạm nghiêm trọng).
    - CẢNH 2 (INTEREST): BẮT BUỘC CHỌN 6s (22-26 từ) HOẶC 8s (30-35 từ).
    - CẢNH 3 (DESIRE): BẮT BUỘC CHỌN 8s (30-35 từ) HOẶC 10s (38-44 từ).
    - CẢNH 4 (ACTION - CTA): BẮT BUỘC CHỌN 4s (14-17 từ) HOẶC 6s (22-26 từ). TUYỆT ĐỐI CẤM vượt quá 26 từ!

    🛑 MA TRẬN KHÓA CỨNG 5 LỚP THỰC THỂ (STRICT 5-LAYER IDENTITY LOCK) - CHỐNG ĐỔI ĐỒ VÀ ĐỔI TÓC 100%:
    1. LỚP 1 (FACE): Khuôn mặt người Việt tự nhiên, độ tuổi cụ thể, lớp trang điểm nhẹ nhàng không đổi.
    2. LỚP 2 (HAIR): KHÓA DUY NHẤT 1 KIỂU TÓC BẤT BIẾN (Ví dụ: Tóc xõa dài uốn nhẹ tự nhiên. TUYỆT ĐỐI CẤM cảnh sau búi tóc, buộc tóc hay cắt ngắn).
    3. LỚP 3 (TOP / OUTERWEAR): KHÓA CỤ THỂ 1 LOẠI ÁO (Ví dụ: Áo len dệt kim màu be kem cổ tròn dài tay. TUYỆT ĐỐI CẤM cảnh sau đổi sang áo phông cộc tay, áo hoa hay cardigan).
    4. LỚP 4 (BOTTOM): KHÓA CỤ THỂ 1 LOẠI QUẦN/VÁY (Ví dụ: Chân váy midi xếp ly màu nâu cà phê. TUYỆT ĐỐI CẤM cảnh sau đổi sang quần jean hay váy khác).
    5. LỚP 5 (SETTING): KHÓA CỤ THỂ 1 BỐI CẢNH DUY NHẤT (Ví dụ: Góc phòng khách Japandi ấm áp bên sofa vải be và bàn trà gỗ. CẤM đổi sang phòng khác).
    -> TẤT CẢ các cảnh phải mang đúng bộ quần áo, kiểu tóc và bối cảnh này!

    🛑 BỘ LỌC CHÍNH SÁCH VÀ AN TOÀN TRẺ EM / VEO 3:
    - Nếu có trẻ em: Người lớn BẮT BUỘC luôn có mặt bên cạnh trong 100% các cảnh. CẤM trẻ đứng một mình!
    - Veo 3: Cấm các từ nhạy cảm về động chạm cơ thể trẻ em (thay 'unzip chest' bằng 'smoothly showing zipper').
    - Bán hàng: Cấm từ cam kết tuyệt đối ('tuyệt đối', '100%', 'cam kết', 'dứt điểm', 'đặc trị', 'khỏi hẳn').
    - Neo giá tương phản ở Cảnh 4: Giá gốc làm tròn tiến lên mốc cao, giá sale hạ sốc.
    - {audio_cmd}
    - {char_rules}
    """

def create_scene_details(target_id, mode, style):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if sc["id"] == target_id), None)
    if not outline: return
    
    narrator_mode = outline.get("narrator_mode", st.session_state.get("last_narrator", "On-camera"))
    char_profiles = outline.get("character_profiles", st.session_state.get("character_profiles", []))
    char_rules = generate_char_rules_string(char_profiles)
    num_chars = outline.get("actors", outline.get("actor_count", len(char_profiles) if char_profiles else 1))
    voice_guidance = build_voice_direction(mode, num_chars, char_profiles)
    is_tiktok_shop = "TikTok Shop" in mode
    audio_instruction = 'Chèn: Audio: "[CHÉP ĐỦ 100% LỜI THOẠI]", Layered SFX: [SFX thực tế]' if "On-camera" in narrator_mode else 'Chỉ chèn Layered SFX thực tế, không chèn thoại.'
    
    fixed_title = outline.get('title', 'Kịch bản chi tiết')
    fixed_hook = sanitize_policy_text(outline.get('hook', ''))
    prod_data_ctx = json.dumps(st.session_state.get('current_product_data_saved'), ensure_ascii=False)
    dna_data_ctx = json.dumps(st.session_state.get('content_analysis'), ensure_ascii=False)

    prompt_text = f"""
    DỮ LIỆU SẢN PHẨM: {prod_data_ctx}
    DNA SẢN PHẨM: {dna_data_ctx}
    KỊCH BẢN #{target_id}: TIÊU ĐỀ: '{fixed_title}' | HOOK CẢNH 1: '{fixed_hook}' | BỐI CẢNH GỐC: {outline.get('setting', 'Không gian thực tế phù hợp')}
    THUYẾT MINH: {audio_instruction} | LOẠI: {mode} | CHỈ ĐẠO GIỌNG: {voice_guidance}
    
    🛑 LỆNH CƯỠNG CHẾ KHỐNG CHẾ SỐ TỪ & KHÓA MA TRẬN 5 LỚP BẤT BIẾN:
    1. KHỐNG CHẾ THỜI LƯỢNG MỖI CẢNH VÀO CÁC MỐC: 4s, 6s, 8s, HOẶC 10s:
       - Cảnh 1 (Attention): BẮT BUỘC 4s (14-17 từ) HOẶC 6s (22-26 từ). TUYỆT ĐỐI CẤM vượt quá 26 từ!
       - Cảnh 2 (Interest): BẮT BUỘC 6s (22-26 từ) HOẶC 8s (30-35 từ).
       - Cảnh 3 (Desire): BẮT BUỘC 8s (30-35 từ) HOẶC 10s (38-44 từ).
       - Cảnh 4 (Action): BẮT BUỘC 4s (14-17 từ) HOẶC 6s (22-26 từ). TUYỆT ĐỐI CẤM vượt quá 26 từ!
    2. MA TRẬN KHÓA 5 LỚP (BẮT BUỘC ĐỊNH DANH CỤ THỂ):
       - Áo trên: Định danh cụ thể 1 mẫu áo (chất vải, màu sắc, kiểu cổ, kiểu tay). CẤM ĐỔI ÁO!
       - Quần/Váy: Định danh cụ thể 1 mẫu quần/váy. CẤM ĐỔI!
       - Kiểu tóc: Định danh duy nhất 1 kiểu (ví dụ tóc xõa tự nhiên). CẤM đổi sang búi tóc hay buộc tóc!
       - Bối cảnh: Duy nhất 1 góc quay cố định xuyên suốt 4 cảnh.
    3. AN TOÀN TRẺ EM: Nếu có trẻ em, người lớn luôn ở cạnh trong 100% các cảnh.
    4. ĐÒN BẨY GIÁ Ở CẢNH 4: Neo giá gốc làm tròn tiến lên mốc cao, giá sale hạ sốc.
    
    TRẢ VỀ JSON:
    {{
        "title": "{fixed_title}",
        "voice": {{"tone": "{voice_guidance}"}},
        "outfit_vi": "Mô tả chi tiết: Áo trên cụ thể + Quần/Váy cụ thể + Kiểu tóc cụ thể được khóa chết 100% suốt 4 cảnh",
        "global_identity_en": "Authentic native Vietnamese character(s), natural Vietnamese facial features, warm skin tone. EXACT LOCKED HAIRSTYLE AND DETAILS invariant across all 4 scenes.",
        "global_outfit_en": "STRICTLY LOCKED SINGLE OUTFIT: [Mô tả chi tiết áo trên, màu sắc, kiểu dáng, chất liệu] paired with [mô tả chi tiết quần/váy, màu sắc]. 100% invariant across all 4 scenes.",
        "global_setting_en": "Consistent single realistic room/space corner, invariant across all 4 scenes.",
        "prod_dna": "Photorealistic description matching the exact reference product, single instance.",
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention", "dur": "6s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh cảnh 1 tại vị trí cố định...",
                "action_en": "Vertical 9:16 eye-level shot. Authentic native Vietnamese character. Wearing [global_outfit_en], with [locked hairstyle]. Natural engaging action manifesting the hook.",
                "director": "Attention | Hook ngắn gọn dồn dập (tối đa 26 từ) | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại mở đầu phát triển từ câu hook gốc '{fixed_hook}' TUÂN THỦ TỐI ĐA 22-26 từ...",
                "img_p": "Vertical 9:16 photo. Authentic native Vietnamese person. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Strictly pure camera footage: NO yellow shopping cart icons, NO floating buttons, NO text. Negative prompt: Caucasian, white, European, blonde hair, blue eyes, t-shirt, short sleeves, hair bun, ponytail, tied hair, outfit change, wardrobe jump, clothes change, extra limbs.",
                "vid_p": "Vertical 9:16 video. Authentic native Vietnamese person. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ 100% LỜI THOẠI CẢNH 1]\\", Layered SFX: [tiếng động thực tế]. Product: [prod_dna]. Strictly pure live-action footage: NO yellow shopping cart icons, NO floating buttons, NO text. Negative prompt: Caucasian, white, European, t-shirt, short sleeves, hair bun, ponytail, outfit change, clothes change."
            }},
            {{
                "scene": 2, "aida_stage": "Interest", "dur": "8s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh cảnh 2 tại cùng vị trí cố định...",
                "action_en": "Medium close-up shot showing practical ergonomic demonstration of product. Same [global_outfit_en], same locked hairstyle. Physically grounded handling.",
                "director": "Interest | Thao tác giải phóng nỗi đau (tối đa 35 từ) | SFX thực tế | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại giải thích tính năng vượt trội TUÂN THỦ TỐI ĐA 30-35 từ...",
                "img_p": "Vertical 9:16 photo. Authentic native Vietnamese person. Demonstrating product with realistic handling. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Negative prompt: Caucasian, white, European, blonde hair, blue eyes, t-shirt, short sleeves, hair bun, ponytail, outfit change, clothes change.",
                "vid_p": "Vertical 9:16 video. Authentic native Vietnamese person smoothly interacting with product. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ 100% LỜI THOẠI CẢNH 2]\\", Layered SFX: [tiếng động thực tế]. Product: [prod_dna]. Negative prompt: Caucasian, white, European, t-shirt, short sleeves, hair bun, ponytail, outfit change."
            }},
            {{
                "scene": 3, "aida_stage": "Desire", "dur": "10s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh cảnh 3 tại cùng vị trí cố định...",
                "action_en": "Sensory visual showcasing genuine comfort and tactile delight. Same [global_outfit_en], same locked hairstyle. Product presented attractively.",
                "director": "Desire | Trực quan hóa giá trị giác quan (tối đa 44 từ) | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại nêu bật cảm giác thỏa mãn và chất lượng TUÂN THỦ TỐI ĐA 38-44 từ...",
                "img_p": "Vertical 9:16 photo. Authentic native Vietnamese person enjoying product tactile benefits. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Negative prompt: Caucasian, white, European, blonde hair, blue eyes, t-shirt, short sleeves, hair bun, ponytail, outfit change, clothes change.",
                "vid_p": "Vertical 9:16 video. Authentic native Vietnamese person showcasing sensory satisfaction. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ 100% LỜI THOẠI CẢNH 3]\\", Layered SFX: [tiếng động thực tế]. Product: [prod_dna]. Negative prompt: Caucasian, white, European, t-shirt, short sleeves, hair bun, ponytail, outfit change."
            }},
            {{
                "scene": 4, "aida_stage": "Action", "dur": "6s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh cảnh 4 tại cùng vị trí cố định...",
                "action_en": "Warm confident closing gesture: Smiling warmly at camera, open hand gesturing downward toward lower corner. Same [global_outfit_en], same locked hairstyle.",
                "director": "Action | Chốt deal đòn bẩy giá tương phản (tối đa 26 từ) | SFX chuông vui tai | Khởi động: 0.00s",
                "voiceover": "Đoạn thoại kết bài chốt deal đòn bẩy giá TUÂN THỦ TỐI ĐA 22-26 từ...",
                "img_p": "Vertical 9:16 photo. Authentic native Vietnamese person smiling warmly at camera with downward open hand gesture. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Negative prompt: Caucasian, white, European, blonde hair, blue eyes, t-shirt, short sleeves, hair bun, ponytail, outfit change, clothes change.",
                "vid_p": "Vertical 9:16 video. Commercial CTA shot. Authentic native Vietnamese person smiling warmly with decisive CTA gesture. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ 100% LỜI THOẠI CẢNH 4]\\", Layered SFX: [tiếng chuông ting vui tai]. Product: [prod_dna]. Negative prompt: Caucasian, white, European, t-shirt, short sleeves, hair bun, ponytail, outfit change."
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
    
    # KHẮC PHỤC TRIỆT ĐỂ: TỰ ĐỘNG THAY THẾ BIẾN THÀNH MÔ TẢ MA TRẬN 5 LỚP
    g_id = res.get("global_identity_en", "Authentic native Vietnamese person")
    g_outfit = res.get("global_outfit_en", "Specific locked outfit")
    g_setting = res.get("global_setting_en", "Consistent single realistic room corner")
    g_prod = res.get("prod_dna", "Realistic product matching reference")
    
    total_sec = 0.0
    for scn in res.get("scenes", []):
        if "voiceover" in scn: scn["voiceover"] = sanitize_policy_text(scn["voiceover"])
        if "director" in scn: scn["director"] = sanitize_policy_text(scn["director"])
        
        # Xử lý img_p: Triệt tiêu ngoặc vuông và nhúng ma trận khóa
        if "img_p" in scn and scn["img_p"]:
            ip = scn["img_p"]
            ip = ip.replace("[global_setting_en]", g_setting)
            ip = ip.replace("[global_identity_en]", g_id)
            ip = ip.replace("[global_outfit_en]", g_outfit)
            ip = ip.replace("[prod_dna]", g_prod)
            ip = re.sub(r'\[.*?\]', '', ip).strip()
            scn["img_p"] = ip
            
        # Xử lý vid_p: Triệt tiêu ngoặc vuông, nhúng ma trận khóa và khử từ nhạy cảm Veo 3
        if "vid_p" in scn and scn["vid_p"]:
            vp = scn["vid_p"]
            vp = vp.replace("[global_setting_en]", g_setting)
            vp = vp.replace("[global_identity_en]", g_id)
            vp = vp.replace("[global_outfit_en]", g_outfit)
            vp = vp.replace("[prod_dna]", g_prod)
            vp = vp.replace(f"[ĐIỀN ĐỦ 100% LỜI THOẠI CẢNH {scn.get('scene', '')}]", scn.get('voiceover', ''))
            vp = vp.replace("[ĐIỀN ĐỦ 100% LỜI THOẠI]", scn.get('voiceover', ''))
            vp = re.sub(r'\[.*?\]', '', vp).strip()
            scn["vid_p"] = sanitize_veo3_prompt(vp)
        
        # TÍNH TOÁN THỜI LƯỢNG THỰC TẾ & KHÓA TRẦN THEO GIAI ĐOẠN AIDA (4s, 6s, 8s, 10s)
        actual_speech_time = calculate_speech_duration(scn.get("voiceover", ""), is_tiktok_shop)
        standard_dur = snap_scene_bucket(scn.get("aida_stage", ""), actual_speech_time)
        scn["dur"] = standard_dur
        scn["actual_speech_sec"] = actual_speech_time
        total_sec += float(standard_dur.replace("s", ""))
        
    res["total_dur"] = f"Khoảng {int(total_sec)} giây"
    res["director_summary"] = f"⏱ <b>Thời lượng thực tế:</b> Khoảng {int(total_sec)} giây (Khóa trần AIDA: 4s/6s/8s/10s | Nhịp đọc 4.6 từ/s kèm ngắt câu) | 🎙 <b>Chỉ đạo giọng:</b> {voice_guidance}<br>👗 <b>Ma trận khóa diện mạo 5 lớp:</b> {res.get('outfit_vi', 'Khóa chết áo, quần, kiểu tóc và bối cảnh suốt 4 cảnh')}<br>📍 <b>Bối cảnh logic cố định:</b> {res.get('global_setting_en', 'Duy nhất 1 không gian xác định xuyên suốt 4 cảnh')}"
    
    st.session_state.generated_details[target_id] = res

# ==============================================================================
# HÀM NHÂN BẢN KỊCH BẢN (BIẾN ĐỔI VOICE, GIỮ SẢN PHẨM, LINH HOẠT DIỄN VIÊN/BỐI CẢNH)
# ==============================================================================
def clone_script(script_id):
    mode = st.session_state.get("last_mode", "Bán Hàng")
    style = st.session_state.get("last_style", "Điện ảnh")
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if sc["id"] == script_id), None)
    if not target: return []
    
    cur_len = len(all_combined)
    target_detail = st.session_state.generated_details.get(script_id, {})
    
    original_voices = []
    if target_detail and "scenes" in target_detail:
        for s in target_detail["scenes"]:
            original_voices.append(f"- Cảnh {s.get('scene')} ({s.get('aida_stage')}): \"{s.get('voiceover')}\"")
        full_voice_text = "\n".join(original_voices)
    else:
        full_voice_text = f"- Hook 3s đầu: \"{target.get('hook', '')}\""

    prod_ctx = f"INPUT SẢN PHẨM: {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)}"
    dna_ctx = f"DNA SẢN PHẨM: {json.dumps(st.session_state.content_analysis, ensure_ascii=False)}" if st.session_state.content_analysis else ""
    
    prompt = f"""
    {prod_ctx}
    {dna_ctx}
    
    KỊCH BẢN VOICE GỐC CẦN NHÂN BẢN (ID #{script_id}):
    Tiêu đề: {target.get('title', '')}
    Bối cảnh gốc: {target.get('setting', '')}
    Nội dung lời thoại (Voice) gốc:
    {full_voice_text}
    
    🛑 NHIỆM VỤ NHÂN BẢN NỘI DUNG VOICE & LINH HOẠT DIỄN VIÊN / BỐI CẢNH:
    1. BẢO TỒN 100% THÔNG SỐ SẢN PHẨM: USP, công năng, cơ chế, Hero SKU và đòn bẩy neo giá tương phản (giá gốc làm tròn cao, giá sale sốc).
    2. BIẾN HÓA LỜI THOẠI (VOICE VARIATION): Viết 5 biến thể kịch bản thoại mới truyền tải cùng thông điệp giá trị nhưng bằng 5 phong cách kể chuyện khác nhau:
       - Biến thể 1: Góc tình huống đời thường dở khóc dở cười.
       - Biến thể 2: Góc chia sẻ chân thành, giải quyết nỗi đau thầm kín.
       - Biến thể 3: Góc so sánh tương phản trước và sau khi dùng.
       - Biến thể 4: Góc trải nghiệm cảm giác giác quan cực đã.
       - Biến thể 5: Góc deal hời / xả kho chốt đơn khẩn cấp.
    3. LINH HOẠT DIỄN VIÊN & BỐI CẢNH: Tự do sáng tạo nhân vật và bối cảnh ăn khớp nhất với câu chuyện thoại mới!
    4. TUÂN THỦ CHÍNH SÁCH BÁN HÀNG ĐA NGÀNH: CẤM 'tuyệt đối', 'hoàn toàn', '100%', 'cam kết', 'dứt điểm', 'đặc trị', 'khỏi hẳn', 'vĩnh viễn'. Nếu có trẻ em luôn có người lớn đồng hành.
    
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{
                "id": {cur_len+1},
                "title": "Tên biến thể kịch bản thoại mới 1",
                "setting": "Bối cảnh mới phù hợp với câu chuyện...",
                "hook": "Câu hook ngắn gọn cuốn hút...",
                "actors": 1,
                "character_roles": ["Nữ KOC Hà Nội"]
            }},
            {{
                "id": {cur_len+2},
                "title": "Tên biến thể kịch bản thoại mới 2",
                "setting": "Bối cảnh mới...",
                "hook": "...",
                "actors": 1,
                "character_roles": ["Cô nàng công sở"]
            }},
            {{
                "id": {cur_len+3},
                "title": "Tên biến thể kịch bản thoại mới 3",
                "setting": "...",
                "hook": "...",
                "actors": 2,
                "character_roles": ["Mẹ trẻ", "Bé gái"]
            }},
            {{
                "id": {cur_len+4},
                "title": "Tên biến thể kịch bản thoại mới 4",
                "setting": "...",
                "hook": "...",
                "actors": 1,
                "character_roles": ["KOC trẻ trung"]
            }},
            {{
                "id": {cur_len+5},
                "title": "Tên biến thể kịch bản thoại mới 5",
                "setting": "...",
                "hook": "...",
                "actors": 2,
                "character_roles": ["Đôi bạn thân"]
            }}
        ]
    }}
    BẮT BUỘC ĐỦ 5 BIẾN THỂ KỊCH BẢN.
    """
    
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, target.get("narrator_mode", ""), "", target.get("actors", 1), "Nhân bản thoại"), max_tokens=3000)
    clones = res.get("outlines", res.get("script_outlines", []))
    
    formatted_clones = []
    for idx, cl in enumerate(clones):
        new_actors_count = cl.get("actors", 1)
        raw_roles = cl.get("character_roles", [f"Diễn viên {i+1}" for i in range(new_actors_count)])
        new_profiles = [{"id": i+1, "role": r} for i, r in enumerate(raw_roles)]
        
        hook_clean = sanitize_policy_text(cl.get("hook", ""))
        formatted_clones.append({
            "id": cur_len + idx + 1,
            "title": cl.get("title", f"Biến thể kịch bản #{cur_len + idx + 1}"),
            "setting": cl.get("setting", "Không gian phù hợp"),
            "hook": hook_clean,
            "actors": new_actors_count,
            "character_profiles": new_profiles,
            "duration_instruction": target.get("duration_instruction", "Khoảng 30 giây"),
            "narrator_mode": target.get("narrator_mode", "Nhân vật xuất hiện (On-camera)")
        })
    return formatted_clones

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
    TUÂN THỦ CHÍNH SÁCH: CẤM 'tuyệt đối', 'hoàn toàn', '100%', 'cam kết', 'dứt điểm', 'đặc trị', 'khỏi hẳn'. Trẻ em luôn có người lớn bên cạnh.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên kịch bản mới", "setting": "Bối cảnh chuẩn...", "hook": "Câu hook ngắn gọn...", "actors": {num_chars} }}
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
                            "last_generation_date": "", "active_session_id": st.session_state.session_id
                        }
                        save_single_account(email_r, st.session_state.licensed_accounts[email_r])
                        st.session_state.is_logged_in = True
                        st.session_state.current_email = email_r
                        st.toast("✅ Đăng ký thành công!"); time.sleep(0.4); st.rerun()
                    else: st.error("⚠️ Thông tin không hợp lệ hoặc tài khoản đã tồn tại!")
    else:
        st.markdown("### 🗂 DỰ ÁN")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True, disabled=is_system_busy):
            st.session_state.update({k: v for k, v in [("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []), ("generated_details", {}), ("content_analysis", None), ("active_script_id", None), ("current_input_context", ""), ("current_project_id", None), ("saved_reference_images", []), ("current_processing_id", None), ("current_cloning_id", None)]})
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
                            st.session_state.update({
                                "content_analysis": sd.get("content_analysis"), "all_scripts": sd.get("all_scripts", []),
                                "cloned_scripts": sd.get("cloned_scripts", []), "expanded_scripts": sd.get("expanded_scripts", []),
                                "generated_details": {int(k): v for k, v in sd.get("generated_details", {}).items()},
                                "character_profiles": sd.get("character_profiles", []), "current_project_id": p['id'], "active_project_title": p['project_title'],
                                "scroll_to_detail": True
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

        # QUẢN TRỊ ADMIN
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
                elif adm_dur == "Vĩnh viễn":
                    calculated_exp_str = "2099-12-31"
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
                    st.write(f"📞 SĐT: `{info.get('phone', 'N/A')}`")
                    st.write(f"⏳ Hạn hiện tại: `{info.get('expires_at')}`")
                    
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
                        st.caption(f"📅 Hạn mới: **{target_exp_str}**")
                    elif renew_choice == "Vĩnh viễn":
                        target_exp_str = "2099-12-31"
                    elif renew_choice != "Giữ nguyên hạn hiện tại":
                        dur_map = {"3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730}
                        target_exp_str = (datetime.now() + timedelta(days=dur_map.get(renew_choice, 30))).strftime("%Y-%m-%d")

                    c_act1, c_act2 = st.columns(2)
                    if c_act1.button("🔄 Cập Nhật", key=f"save_renew_{acc_mail}", use_container_width=True, disabled=is_system_busy):
                        st.session_state.licensed_accounts[acc_mail]["roles"] = new_roles
                        st.session_state.licensed_accounts[acc_mail]["plan_type"] = new_plan
                        st.session_state.licensed_accounts[acc_mail]["expires_at"] = target_exp_str
                        save_single_account(acc_mail, st.session_state.licensed_accounts[acc_mail])
                        st.toast("✅ Đã cập nhật thành công!"); time.sleep(0.4); st.rerun()
                    if c_act2.button("🗑 Xóa tài khoản", key=f"del_acc_{acc_mail}", type="secondary", use_container_width=True, disabled=is_system_busy):
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
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
                body { background: transparent; padding: 2px; }
                .support-container { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1.5px solid #86efac; border-radius: 14px; padding: 12px 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
                .support-title { font-size: 14px; font-weight: 800; color: #15803d; margin-bottom: 7px; display: flex; align-items: center; justify-content: center; gap: 6px; }
                .hotline-card { background: linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%); border-radius: 10px; padding: 8px 6px; box-shadow: 0 3px 8px rgba(153, 27, 27, 0.25); text-align: center; }
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

        if st.button("🚪 Đăng Xuất", disabled=is_system_busy): 
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

if st.button("🚀 PHÂN TÍCH DNA & SINH 5 KỊCH BẢN ĐA VŨ TRỤ", type="primary", use_container_width=True, disabled=is_system_busy):
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
                        "lid_mechanism": "Cơ chế hoạt động",
                        "detected_prices": "Quét OCR giá tiền (giá gốc và giá sale)",
                        "rounded_price_anchor": "TÂM LÝ HỌC NEO GIÁ TƯƠNG PHẢN: Làm tròn giá gốc TIẾN LÊN mốc số chẵn lớn gần nhất (VD: 169.000đ -> 'gần 200 nghìn đồng') và làm mềm giá sale (VD: 98.000đ -> 'chưa đến 100 nghìn'). Định dạng: 'Giá gốc gần [X] -> Nay giảm sốc chỉ còn [Y]'",
                        "product_dimensions": "Thông số kích thước",
                        "prompt_dna_lock": "Visual DNA cho video"
                    }},
                    "outlines": [
                        {{ "id": 1, "title": "Tên kịch bản 1", "setting": "Bối cảnh chuẩn...", "hook": "Câu hook ngắn gọn...", "actors": {num_chars} }},
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
        st.markdown(f"--- \n##### 🏭 **4. Vật lý, Cơ chế & Mức Giá OCR:**<br><div style='line-height: 1.8;'><b>📐 Thông số:</b> {ca.get('product_dimensions', '')}<br><b>🎨 Khóa màu chi tiết:</b> {ca.get('product_color_lock', '')}<br><b>⚙ Cơ chế hoạt động:</b> {ca.get('lid_mechanism', 'Bình thường')}</div><br><b>💰 Mức giá (OCR):</b> {ca.get('detected_prices', '')} <br><b>🎯 Đòn bẩy giá tương phản:</b> <span style='color:#dc2626; font-size:15px; font-weight:900;'>{ca.get('rounded_price_anchor', '')}</span>", unsafe_allow_html=True)
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
        if st.button("⬅ Thu gọn danh sách kịch bản", disabled=is_system_busy):
            st.session_state.active_script_id = None
            st.session_state.scroll_to_top = True
            st.rerun()
            
        asc = st.session_state.generated_details.get(st.session_state.active_script_id, {})
        vp = asc.get("voice", {})
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(asc.get('title')).upper()}**")
        
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
            speech_sec = scn.get('actual_speech_sec', calculate_speech_duration(vo_text, "TikTok Shop" in st.session_state.get("last_mode", "")))
            
            st.markdown(f"#### 📍 Phân cảnh {idx} - Giai đoạn {scn.get('aida_stage')}")
            st.markdown(f"<span class='timing-badge'>⏱ Khung phân cảnh chuẩn: {scn.get('dur')} | Khớp nhịp đọc thực tế: ~{speech_sec}s ({actual_words} từ, {comma_count} dấu phẩy, {period_count} dấu ngắt câu | ~{round(actual_words/max(1.0, speech_sec), 1)} từ/s)</span>", unsafe_allow_html=True)
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting')}*\n\n**🎙 Đạo diễn & Ngôn ngữ hình thể KOC:** *{scn.get('director')}*\n\n**💬 Thoại kịch bản:** <div class='voiceover-text'>{vo_text}</div>", unsafe_allow_html=True)
            if scn.get('img_p'): st.markdown("**🖼 Prompt Ảnh (Midjourney / Flux - Khóa Ma Trận 5 Lớp & 100% Người Việt):**"); st.code(img_p := scn.get('img_p'), language="text"); safe_copy_button(img_p, f"📋 Sao Chép Ảnh Cảnh {idx}")
            if scn.get('vid_p'): st.markdown("**🎥 Prompt Video (Veo 3 Safe / Kling AI / Hedra - Cử Chỉ Hình Thể KOC & SFX):**"); st.code(vid_p := scn.get('vid_p'), language="text"); safe_copy_button(vid_p, f"📋 Sao Chép Video Cảnh {idx}")
            st.markdown("---")

    st.markdown("### 🎬 **1. Kịch Bản Đã Dựng Chi Tiết**")
    for outline in comp_sc:
        sc_id = outline["id"]
        with st.container(border=True):
            c1, c2, c3 = st.columns([2.5, 1, 1])
            c1.markdown(f"**#{sc_id}. {outline.get('title')}**")
            c1.caption(f"⚡ *{outline.get('hook')}*")
            
            if sc_id != st.session_state.active_script_id:
                if c2.button("👁 Xem lại", key=f"r_{sc_id}", use_container_width=True, disabled=is_system_busy):
                    st.session_state.active_script_id = sc_id
                    st.session_state.scroll_to_detail = True
                    st.rerun()
            
            btn_clone_ph = c3.empty()
            if st.session_state.current_cloning_id == sc_id:
                btn_clone_ph.markdown("<div style='background: #fffbeb; color: #dc2626; border-radius: 8px; padding: 8px; text-align: center; font-size: 13px; font-weight: bold; border: 1px solid #fca5a5;'>⏳ Đang nhân bản...</div>", unsafe_allow_html=True)
            else:
                if btn_clone_ph.button("🚀 Nhân bản", key=f"c_{sc_id}", type="primary", use_container_width=True, disabled=is_system_busy):
                    can_run, msg = check_usage_limit(st.session_state.current_email)
                    if can_run:
                        st.session_state.current_cloning_id = sc_id
                        st.rerun()
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
                btn_detail_ph.markdown("<div style='background: #fffbeb; color: #d97706; border-radius: 8px; padding: 8px; text-align: center; font-size: 13px; font-weight: bold; border: 1px solid #fde68a;'>⏳ Đang dựng 4 cảnh...</div>", unsafe_allow_html=True)
            else:
                if btn_detail_ph.button("✨ Tạo chi tiết ngay", key=f"cr_{sc_id}", type="secondary", use_container_width=True, disabled=is_system_busy):
                    can_run, msg = check_usage_limit(st.session_state.current_email, is_detailing=True)
                    if can_run:
                        st.session_state.current_processing_id = sc_id
                        st.rerun()
                    else: st.error(msg)

    # ==============================================================================
    # KHỐI XỬ LÝ GENERATION TẠI KỊCH BẢN ĐƯỢC CHỌN (TẠO CHI TIẾT)
    # ==============================================================================
    if st.session_state.current_processing_id is not None:
        target_id_to_run = st.session_state.current_processing_id
        try:
            with st.spinner(f"⏳ Đang áp dụng ma trận khóa 5 lớp, khống chế số từ và dựng kịch bản #{target_id_to_run}..."):
                create_scene_details(target_id_to_run, st.session_state.last_mode, st.session_state.last_style)
                st.session_state.active_script_id = target_id_to_run
                st.session_state.scroll_to_detail = True
                st.toast(f"✅ Đã hoàn tất dựng kịch bản #{target_id_to_run}!")
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
        finally:
            st.session_state.current_processing_id = None
            time.sleep(0.3)
            st.rerun()

    # ==============================================================================
    # KHỐI XỬ LÝ NHÂN BẢN KỊCH BẢN ĐƯỢC CHỌN (BIẾN HÓA LỜI THOẠI)
    # ==============================================================================
    if st.session_state.current_cloning_id is not None:
        clone_id_to_run = st.session_state.current_cloning_id
        try:
            with st.spinner(f"⏳ Đang biến hóa nội dung voice và nhân bản 5 biến thể cho kịch bản #{clone_id_to_run}..."):
                new_clones = clone_script(clone_id_to_run)
                st.session_state.cloned_scripts.extend(new_clones)
                st.toast("✅ Đã nhân bản thành công 5 kịch bản voice mới!")
        except Exception as e:
            st.error(f"❌ Lỗi nhân bản: {e}")
        finally:
            st.session_state.current_cloning_id = None
            time.sleep(0.3)
            st.rerun()

    st.markdown("--- \n##### ➕ **Gọi Thêm 5 Kịch Bản Mới**")
    cg1, cg2, cg3, cg4 = st.columns([1.5, 0.8, 1.2, 1.5])
    a_opts = ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Chia sẻ", "😂 Hài hước"]
    c_ang = cg1.selectbox("🧭 Chiến lược mới:", a_opts, key=f"ea_{st.session_state.reset_key}")
    c_num = cg2.number_input("Số diễn viên:", 1, 8, num_chars, key=f"en_{st.session_state.reset_key}")
    c_dur_choice = cg3.selectbox("⏳ Thời lượng:", ["Tự động đồng bộ thoại", "Tùy chỉnh (s)"], key=f"ed_{st.session_state.reset_key}")
    c_dur_str = f"Chính xác {cg3.number_input('Số giây:', 10, 300, 60, key=f'eds_{st.session_state.reset_key}')} giây." if "Tùy" in c_dur_choice else "Khoảng 30 giây."
    c_nar = cg4.selectbox("🎙 Thuyết minh:", ["Nhân vật xuất hiện (On-camera)", "🎙 Lồng tiếng ngoài (Off-screen)"], key=f"ena_{st.session_state.reset_key}")

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
