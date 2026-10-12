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
from datetime import datetime, timedelta

# ==============================================================================
# 1. CẤU HÌNH GIAO DIỆN & TÍCH HỢP GOOGLE ANALYTICS 4
# ==============================================================================
st.set_page_config(page_title="Universal AI Video Studio Pro", page_icon="🎬", layout="wide")

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
    div[data-testid="stButton"] > button[kind="secondary"]:hover, div[data-testid="stFormSubmitButton"] > button[kind="secondary"]:hover { transform: translateY(-1px) !important; box-shadow: 0 5px 14px rgba(255, 75, 75, 0.5) !important; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 3px 8px; border-radius: 4px; font-size: 11px; border: 1px solid #bbf7d0; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 3px 8px; border-radius: 4px; font-size: 11px; border: 1px solid #fde68a; }
    .custom-card { background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
    .support-box { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1.5px solid #86efac; border-radius: 12px; padding: 12px; text-align: center; margin-top: 15px; }
    .btn-zalo { background: #0068FF; color: white !important; font-weight: 900; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 15px; border: 1px solid #0056d6; }
    .btn-fb { background: #1877F2; color: white !important; font-weight: 900; padding: 8px 24px; border-radius: 8px; text-decoration: none; font-size: 16px; border: 1px solid #166fe5; font-family: serif; }
    .btn-tt { background: #000000; color: white !important; font-weight: 900; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 15px; border: 1px solid #333; }
    .social-icons-container { display: flex; gap: 12px; justify-content: center; margin-top: 10px; margin-bottom: 10px; }
    .detail-header-box { background: #eff6ff; border: 1.5px solid #bfdbfe; border-radius: 10px; padding: 15px; margin-bottom: 20px; color: #1e3a8a; }
    .voiceover-text { color: #15803d; background: #f0fdf4; padding: 6px 10px; border-radius: 6px; font-size: 15.5px; border: 1px solid #bbf7d0; display: inline-block; width: 100%; margin-top: 4px; }
    .scrollable-sidebar-container { max-height: 380px; overflow-y: auto; padding-right: 5px; margin-bottom: 10px; }
    div[data-testid="stFileUploader"] section { padding: 4px; min-height: 2rem; border: 1.5px dashed #cbd5e1 !important; background-color: #f8fafc !important; }
    div[data-testid="stFileUploader"] section > input { padding: 0px; }
    .streamlit-expanderHeader { font-weight: bold; color: #1e3a8a; background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div { background-color: #f8fafc !important; border: 1.5px solid #cbd5e1 !important; border-radius: 8px !important; transition: all 0.2s ease; }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within { border-color: #d90429 !important; box-shadow: 0 0 0 2px rgba(217, 4, 41, 0.15) !important; background-color: #ffffff !important; }
    input::placeholder, textarea::placeholder { color: #94a3b8 !important; opacity: 1 !important; }
</style>
""", unsafe_allow_html=True)

ALL_MODULES = ["🛒 TikTok Shop & Bán Hàng", "🌟 Viral & Xây Kênh"]
ADMIN_EMAIL = "binhnguyenmedia.vn@gmail.com"
HARDCODED_ASPECT = "9:16 (Dọc TikTok/Reels)"

@st.cache_resource
def init_supabase():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None
supabase = init_supabase()

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
client = genai.Client(api_key=api_key) if api_key else None

def is_valid_phone(phone):
    phone = phone.strip()
    return phone.isdigit() and phone.startswith('0') and 9 <= len(phone) <= 11

def compress_image_bytes(uploaded_file, max_dimension=1024, quality=80):
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        out_buffer = io.BytesIO()
        img.save(out_buffer, format="JPEG", quality=quality, optimize=True)
        return out_buffer.getvalue(), "image/jpeg"
    except Exception:
        return uploaded_file.getvalue(), (uploaded_file.type or "image/jpeg")

def load_licensed_accounts():
    accs = {ADMIN_EMAIL: {"roles": ALL_MODULES, "phone": "0968484369", "expires_at": "2099-12-31", "password": "admin", "plan_type": "VIP", "active_session_id": ""}}
    if not supabase: return accs
    try:
        res = supabase.table("licensed_accounts").select("*").execute()
        for row in res.data:
            accs[row["email"]] = {
                "roles": row.get("roles", ALL_MODULES),
                "phone": row.get("phone", ""),
                "password": row.get("password", ""),
                "expires_at": row.get("expires_at", "2099-12-31"),
                "plan_type": row.get("plan_type", "Trial"),
                "daily_usage_count": row.get("daily_usage_count", 0),
                "last_generation_date": row.get("last_generation_date", ""),
                "active_session_id": row.get("active_session_id", "")
            }
    except: pass
    return accs

def save_single_account(email, acc_data):
    if not supabase or email == ADMIN_EMAIL: return
    try:
        payload = {"email": email, **acc_data}
        supabase.table("licensed_accounts").upsert(payload).execute()
    except: pass

def delete_single_account(email):
    if not supabase or email == ADMIN_EMAIL: return
    try: supabase.table("licensed_accounts").delete().eq("email", email).execute()
    except: pass

def check_usage_limit(email, is_detailing=False):
    if email == ADMIN_EMAIL: return True, ""
    accs = st.session_state.licensed_accounts
    acc = accs.get(email)
    if not acc: return False, "Lỗi xác thực tài khoản."
    
    exp_date = datetime.strptime(acc.get("expires_at", "2099-12-31"), "%Y-%m-%d")
    if datetime.now() > exp_date:
        return False, "Tài khoản của bạn đã hết hạn. Vui lòng liên hệ Admin để gia hạn!"
        
    plan = acc.get("plan_type", "Trial")
    if plan == "VIP": return True, ""
        
    limit_map = {"Advanced": 20, "Basic": 10, "Trial": 3}
    limit = limit_map.get(plan, 3)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if acc.get("last_generation_date") != today:
        acc["daily_usage_count"] = 0
        acc["last_generation_date"] = today
        
    if is_detailing:
        if acc.get("daily_usage_count", 0) >= limit:
            return False, f"Bạn đã dùng hết {limit}/{limit} lượt tạo chi tiết kịch bản của hôm nay! Vui lòng nâng cấp gói cước để tạo thêm."
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

# Khởi tạo Session State
if "session_id" not in st.session_state: st.session_state.session_id = str(uuid.uuid4())

for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", load_licensed_accounts()),
    ("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []),
    ("generated_details", {}), ("content_analysis", None), ("active_script_id", None),
    ("current_input_context", ""), ("current_product_data_saved", None), ("current_product_data", None),
    ("reset_key", 0), ("scroll_to_top", False), ("scroll_to_detail", False), ("extra_num_chars", 1),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"),
    ("last_mode", ""), ("last_style", ""), ("last_narrator", ""),
    ("target_duration_instruction", ""), ("character_profiles", []), 
    ("editing_acc_email", None), ("current_project_id", None), ("load_more", False)
]:
    if key not in st.session_state: st.session_state[key] = default_val

# Khóa thiết bị đồng thời
if st.session_state.is_logged_in and st.session_state.current_email != ADMIN_EMAIL:
    current_acc_lock = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
    if current_acc_lock.get("active_session_id") != st.session_state.session_id:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.error("🚨 **CẢNH BÁO: TÀI KHOẢN ĐANG ĐƯỢC SỬ DỤNG Ở NƠI KHÁC**")
        st.info("Hệ thống phát hiện tài khoản của bạn đang được đăng nhập trên một thiết bị hoặc trình duyệt khác. Để bảo mật, mỗi tài khoản chỉ được phép sử dụng trên **1 thiết bị duy nhất** tại cùng một thời điểm.")
        if st.button("🔌 Sử dụng trên thiết bị này (Đăng xuất thiết bị kia)", type="primary"):
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
            var anchor = window.parent.document.getElementById('detailed-view-anchor');
            if (anchor) { anchor.scrollIntoView({behavior: 'smooth', block: 'start'}); } 
            else { window.parent.scrollTo({top: 0, behavior: 'smooth'}); }
        }, 500);
    </script>
    """, height=0)
    st.session_state.scroll_to_detail = False

# ==============================================================================
# 2. HÀM AI LÕI & LUẬT THÉP (CẬP NHẬT MODEL GEMINI-3.8-FLASH & JSON REPAIR)
# ==============================================================================
def repair_and_parse_json(text_content: str):
    cleaned = re.sub(r'```(?:json)?', '', text_content).strip()
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    if match: 
        candidate = match.group(0)
    else:
        candidate = cleaned

    def try_parse(s):
        try:
            p = json.loads(s, strict=False)
            return p[0] if isinstance(p, list) and len(p) > 0 else p
        except Exception:
            return None

    res = try_parse(candidate)
    if res is not None:
        return res

    fixed = candidate.rstrip(", \n\r\t")
    in_str = False
    escape = False
    stack = []
    
    for ch in fixed:
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if not in_str:
            if ch in ('{', '['):
                stack.append('}' if ch == '{' else ']')
            elif ch in ('}', ']'):
                if stack and stack[-1] == ch:
                    stack.pop()

    if in_str:
        fixed += '"'

    while stack:
        fixed += stack.pop()

    res = try_parse(fixed)
    if res is not None:
        return res

    try:
        py_str = candidate.replace('true', 'True').replace('false', 'False').replace('null', 'None')
        parsed = ast.literal_eval(py_str)
        return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else parsed
    except Exception:
        raise Exception("AI sinh JSON lỗi cấu trúc. Vui lòng thử lại.")

def call_gemini(contents, sys_inst="Bạn là AI hỗ trợ JSON.", max_tokens=4096):
    model_name = "gemini-3.8-flash"
    for attempt in range(2):
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
            err_msg = str(e).lower()
            if "not_found" in err_msg or "404" in err_msg:
                model_name = "gemini-3.8-flash-lite"
            if attempt == 1: 
                raise e
            time.sleep(1)

def generate_char_rules_string(profiles):
    if not profiles: return "CHAR_LOCK: AI tự tạo diện mạo KOC người Việt Nam chân thực, thần thái tự tin, ánh mắt sáng, nụ cười cuốn hút, khóa cố định Khuôn mặt, Kiểu tóc, Vóc dáng."
    rules = "KOC IMAGE EXTRACTION & BIO LOCK:\n"
    for p in profiles: rules += f" - Diễn viên {p['id']} ({p['role']}): TRÍCH XUẤT KHUÔN MẶT, KIỂU TÓC, VÓC DÁNG (Đảm bảo nét người Việt tự nhiên, dáng đứng/ngồi thẳng thanh lịch, thần thái cuốn hút). TỰ TẠO TRANG PHỤC. KHÓA CỐ ĐỊNH 100% DIỆN MẠO NÀY.\n"
    return rules

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, angle):
    if "Tự động mix" in angle:
        strat_cmd = "BẠN PHẢI MIX ĐA DẠNG 5 GÓC ĐỘ NỘI DUNG KHÁC NHAU."
    else:
        strat_cmd = f"🛑 LỆNH TẨY NÃO: BẠN BẮT BUỘC PHẢI VIẾT CẢ 5 KỊCH BẢN THEO ĐÚNG CHIẾN LƯỢC SAU: '{angle}'."
        
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL KÊNH TIKTOK SHOP TRIỆU VIEW. PHONG CÁCH: {style}
    {strat_cmd}
    
    🛑 QUY TẮC BỐI CẢNH VÀ CỐT TRUYỆN CHUẨN XÁC THEO SẢN PHẨM & KỊCH BẢN:
    1. PHÂN BIỆT BỐI CẢNH THỰC TẾ CHUẨN XÁC:
       - NẾU LÀ KỊCH BẢN FLASH SALE / XẢ KHO / GIÁ SỐC: BẮT BUỘC toàn bộ bối cảnh phải diễn ra tại KHO HÀNG, XƯỞNG SẢN XUẤT, HOẶC SHOWROOM TỔNG NGẬP TRÀN KIỆN HÀNG.
       - NẾU LÀ KỊCH BẢN REVIEW / ĐỜI SỐNG / NỖI ĐAU: BẮT BUỘC bối cảnh phải là KHÔNG GIAN SỬ DỤNG TỰ NHIÊN CỦA SẢN PHẨM ĐÓ. 
         + Gối ngủ, chăn ga, đệm: BẮT BUỘC ở PHÒNG NGỦ ẤM CÚNG, ĐẶT SẢN PHẨM NGAY TRÊN GIƯỜNG NGỦ. Tuyệt đối CẤM đặt trên bàn làm việc/bàn cạnh giường.
         + Đồ bếp, gia dụng: BẮT BUỘC ở PHÒNG BẾP / BÀN BẾP.
         + Đồ ăn/uống: Bàn ăn gia đình hoặc khu nấu bếp.
    2. KỊCH BẢN CHUẨN MÔ HÌNH AIDA:
       - Attention (3s đầu): Hook giật gân, tạo tò mò hoặc xúc động đánh đúng nỗi đau/mong muốn của tệp khách. CẤM giơ sản phẩm thô thiển.
       - Interest: Nêu rõ sản phẩm là gì, dành cho ai, giải quyết vấn đề gì trong không gian tự nhiên.
       - Desire: Nêu bật lý do nên mua, điểm độc bản (USP) so với thị trường.
       - Action: Kêu gọi hành động tự nhiên, chốt ưu đãi đúng lúc.
    3. CÔNG THỨC ĐÒN BẨY GIÁ TƯƠNG PHẢN (KHI NÓI GIÁ):
       - Neo giá gốc làm tròn (gần... nghìn / tận... nghìn).
       - Dùng mẫu tương phản: "Giá niêm yết gần [X] nghìn, nhưng hôm nay xả kho giảm cực sâu, bấm ngay giỏ hàng nhận deal hời, lưu ý giá có thể thay đổi tùy thời điểm nhé."
       - CẤM đọc số lẻ lê thê. CẤM đọc giá sale thực tế để dùng được đa kênh.
    4. BỘ LỌC CHÍNH SÁCH VĨNH VIỄN: CẤM "tuyệt đối", "hoàn toàn", "100%", "chắc chắn", "cam kết", "thuốc", "đặc trị", "trị dứt điểm".
    5. PERSONA HÀ NỘI CHUẨN: Dứt khoát (nhé, này, thế, dùng, không). CẤM từ miền Nam: "nha", "nè", "nghen", "vô", "xài".
    6. KHÔNG CHỮ/UI TẠO TỪ AI: CẤM chữ, subtitles, UI elements, icons. Khung hình sạch 100%.
    7. {char_rules}
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction):
    is_on_camera = "On-camera" in narrator_mode
    narrator_instruction = f"Nhân vật xuất hiện trực tiếp trước ống kính. Chèn lệnh `Audio:` vào `video_prompt`." if is_on_camera else "Lồng tiếng ngoài. KHÔNG chèn Audio vào `video_prompt`."
    
    if "TikTok Shop" in mode:
        voice_hint = "Giọng [Nam/Nữ tự phân tích] HÀ NỘI CHUẨN. Giọng ngực (chest voice) ĐẦY NỘI LỰC, ĐANH THÉP, BẮT ĐẦU NÓI NGAY TẠI GIÂY 0.00, TỐC ĐỘ ĐỀU METRONOME KHÔNG DỒN ĐUÔI CÂU (4.3 - 4.5 từ/s)."
    else:
        voice_hint = "Giọng [Nam/Nữ tự phân tích] HÀ NỘI CHUẨN. Hào hứng, tự nhiên, nhịp độ hoạt ngôn cuốn hút, nói ngay đầu cảnh."

    return f"""
    BẠN LÀ ĐẠO DIỄN VIRTUAL ĐỈNH CAO CHO VEO 3. PHONG CÁCH: {style}
    
    🛑 QUY TẮC ÂM THANH MÔI TRƯỜNG THỰC TẾ (DIEGETIC SOUND) & BẢO TOÀN VẬT THỂ:
    1. TỰ ĐỘNG SINH ÂM THANH MÔI TRƯỜNG VẬT LÝ THỰC TẾ (DIEGETIC & FOLEY SOUND FX):
       - Tùy theo tình huống của cảnh, BẮT BUỘC mô tả âm thanh tự nhiên đan xen với giọng đọc trong prompt `vid_p`:
         + Chiên xào / Nấu nướng: Chèn tiếng xèo xèo của dầu nóng, tiếng lách tách đáy chảo (`sizzling frying sound, gentle oil crackle in pan`).
         + Ăn uống: Tiếng cắn giòn rụm, nhai giòn tan (`crisp crunching bite sound, satisfying crunchy chewing sound`).
         + Gió thổi / Ngoài trời / Quạt: Tiếng gió thổi vi vu vù vù (`audible whooshing wind breeze sound, fluttering ambient air`).
         + Nồi cơm / Đồ điện tử: Tiếng chốt nắp bật cách cạch, tiếng hơi nước phì nhẹ (`mechanical latch click sound, steam hiss`).
         + Chăn ga / Gối nệm: Tiếng sột soạt êm ái của sợi vải và tiếng bọt nhớ đàn hồi (`soft fabric rustling, subtle foam compression sound`).
       - Trong lệnh âm thanh của `vid_p`, cấu trúc chuẩn:
         Audio: "[Lời thoại]", Layered SFX: [Âm thanh vật lý thực tế tương ứng], Ambient environment background sound.

    2. ĐẠO DIỄN BỐI CẢNH NATIVE CHUẨN XÁC 100%:
       - Với sản phẩm GỐI NGỦ / NỆM / CHĂN GA: Bối cảnh BẮT BUỘC là PHÒNG NGỦ HIỆN ĐẠI ẤM CÚNG (`cozy modern bedroom`). Gối BẮT BUỘC ĐẶT TRÊN GIƯỜNG NGỦ CÓ GA BỌC CHỈNH CHU (`resting on a neatly made bed`). Nhân vật ngồi mép giường hoặc đứng cạnh giường tương tác nhẹ nhàng (dùng lòng bàn tay ấn thử độ đàn hồi bọt nhớ của gối trên giường). TUYỆT ĐỐI CẤM đặt gối lên bàn!
       - Với kịch bản FLASH SALE / XẢ KHO: Bối cảnh BẮT BUỘC là KHO HÀNG / XƯỞNG SẢN XUẤT / SHOWROOM TỔNG ngập tràn kiện hàng và kệ pallet.
       - Với ĐỒ BẾP / GIA DỤNG: Đặt trên mặt bàn bếp/đảo bếp (`kitchen counter / island`).
    
    3. KHÓA BẢO TOÀN VẬT THỂ & CHỐNG DÍNH TAY, CHỐNG BIẾN MẤT (RIGID PERSISTENCE LOCK):
       - TUYỆT ĐỐI CẤM sản phẩm bị dính da tay, tự biến mất hoặc tự nhân bản thêm cái thứ hai.
       - Trong `vid_p`, BẮT BUỘC chèn lệnh:
         "Strict numerical object persistence: Exactly ONE single product item visible throughout the shot, resting stably in its designated environment, strictly NO extra duplicates, NO disappearing artifacts. Anatomically separate hands and fingers with crisp spatial boundary; skin never merges with fabric or casing. Product maintains 100% frozen geometry, identical fabric weave, fixed print patterns, and invariant colors without warping, fading, or pixel bleeding."
    
    4. LỆNH CƯỠNG CHẾ THOẠI TỨC THÌ TẠI GIÂY 0.00 (ZERO-LATENCY SPEECH TRIGGER):
       - Nhân vật mở miệng phát âm ngay frame đầu tiên: "Character begins speaking immediately at second 0.00 without any idle delay or hesitation."
    
    5. BẢNG KHỚP SỐ TỪ - THỜI GIAN ĐÃ TRỪ HAO NGHỈ & ĐỘ TRỄ (CHỐNG THIẾU VOICE TRIỆT ĐỂ):
       - Cảnh 4s & 6s: TỐI ĐA 1 DẤU PHẨY (,). Cảnh 8s & 10s: TỐI ĐA 2 DẤU PHẨY (,).
       - CÂN XỨNG VẾ CÂU: Số từ giữa 2 vế qua dấu phẩy phải tương đương nhau.
       - KHUNG SỐ TỪ THỰC TẾ CHUẨN XÁC:
         + Phân cảnh 4s ➔ BẮT BUỘC viết từ 12 đến 14 từ (Tối đa 1 dấu phẩy)
         + Phân cảnh 6s ➔ BẮT BUỘC viết từ 18 đến 20 từ (Tối đa 1 dấu phẩy)
         + Phân cảnh 8s ➔ BẮT BUỘC viết từ 26 đến 28 từ (Tối đa 2 dấu phẩy)
         + Phân cảnh 10s ➔ BẮT BUỘC viết từ 34 đến 36 từ (Tối đa 2 dấu phẩy)
         + CHỈ ĐƯỢC CHỌN CÁC MỐC THỜI LƯỢNG "4s", "6s", "8s", "10s".
       - TRẦN THỜI GIAN CỨNG 10S: Mọi phân cảnh <= 10s. Nếu vượt quá 36 từ, BẮT BUỘC TÁCH LÀM 2 PHÂN CẢNH NỐI TIẾP. Cảnh sau ghi 'trans': "Nối tiếp liền mạch từ cảnh trước".

    6. TƯ THẾ TỰ NHIÊN & GÓC MÁY NGANG TẦM MẮT:
       - TUYỆT ĐỐI CẤM NHÂN VẬT CÚI GẬP NGƯỜI, KHOM LƯNG XUỐNG BÀN (NO leaning forward, NO awkward crouching, NO hunching).
       - BẮT BUỘC tư thế thanh lịch, thẳng lưng, góc máy ngang tầm mắt.
    
    7. CÔNG THỨC THOẠI GIÁ TƯƠNG PHẢN (KHI NÓI GIÁ):
       - Neo giá gốc làm tròn. BẮT BUỘC dùng mẫu tương phản: "Giá niêm yết gần [X] nghìn, nhưng hôm nay xả kho giảm cực sâu, bấm ngay giỏ hàng nhận deal hời, lưu ý giá có thể thay đổi tùy thời điểm nhé."

    8. KHÓA MÀU SẮC ĐA BỘ PHẬN: Nhúng chết màu sắc, vân vải, hoa văn từ `product_color_lock` vào `prod_dna`.
    9. KHÔNG CHỮ VÀ KHÔNG UI/ICON (ANTI-UI/TEXT LOCK): Khung hình sạch 100%.
    10. {narrator_instruction}
    11. {char_rules}
    """

def create_scene_details(target_id, mode, style):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if sc["id"] == target_id), None)
    if not outline: return
    
    narrator_mode = outline.get("narrator_mode", st.session_state.get("last_narrator", "On-camera"))
    char_profiles = outline.get("character_profiles", st.session_state.get("character_profiles", []))
    char_rules = generate_char_rules_string(char_profiles)
    duration_instruction = outline.get("duration_instruction", st.session_state.get("target_duration_instruction", "Tự động phân bổ 15-30 giây"))
    
    is_on_camera = "On-camera" in narrator_mode
    prod_data_ctx = json.dumps(st.session_state.get('current_product_data_saved'), ensure_ascii=False)
    dna_data_ctx = json.dumps(st.session_state.get('content_analysis'), ensure_ascii=False)
    
    audio_instruction = 'TRONG TẤT CẢ vid_p BẮT BUỘC chèn lệnh: Audio: "[CHÉP LẠI TOÀN BỘ 100% CÂU THOẠI TRONG VOICEOVER, CẤM CẮT XÉN]", Layered SFX: [MÔ TẢ TIẾNG ĐỘNG THỰC TẾ CỦA TÌNH HUỐNG (VD tiếng xèo xèo rán đồ, vù vù gió thổi, rôm rốp khi ăn, cách cạch mở nắp...)]' if is_on_camera else 'KHÔNG chèn Audio thoại vào vid_p, chỉ chèn Layered SFX thực tế.'
    voice_hint = "Giọng [Nam/Nữ tự phân tích] HÀ NỘI CHUẨN 100% (CẤM TỪ MIỀN NAM). Giọng ngực ĐẦY NỘI LỰC, ĐANH THÉP, BẮT ĐẦU NÓI NGAY TẠI GIÂY 0.00, TỐC ĐỘ ĐỀU ĐẶN METRONOME KHÔNG DỒN ĐUÔI (4.3 - 4.5 từ/s)." if "TikTok Shop" in mode else "Giọng [Nam/Nữ tự phân tích] HÀ NỘI CHUẨN 100% (CẤM TỪ MIỀN NAM). Nhanh, Truyền cảm, Tự nhiên."

    prompt = f"""
    DỮ LIỆU ĐẦU VÀO: {prod_data_ctx} | PHÂN TÍCH DNA: {dna_data_ctx}
    Viết chi tiết kịch bản ID {target_id}: '{outline.get('title')}'. Hook: {outline.get('hook', outline.get('target_hook'))}. Bối cảnh: {outline.get('setting', outline.get('setting_style'))}.
    THUYẾT MINH: {audio_instruction} | LOẠI: {mode}
    
    LƯU Ý ĐẶC BIỆT (ÂM THANH MÔI TRƯỜNG THỰC TẾ & BỐI CẢNH NATIVE):
    - TỰ ĐỘNG CHÈN ÂM THANH MÔI TRƯỜNG THỰC TẾ (Layered SFX) trong 'vid_p' và 'director'.
    - ĐẠO DIỄN BỐI CẢNH NATIVE:
      + Nếu là GỐI NGỦ, ĐỆM, CHĂN GA: Bối cảnh BẮT BUỘC là PHÒNG NGỦ HIỆN ĐẠI (`cozy modern bedroom`), GỐI/ĐỆM ĐẶT NGAY TRÊN GIƯỜNG NGỦ CÓ GA BỌC CHỈNH CHU. Nhân vật ngồi ở mép giường hoặc đứng cạnh giường tương tác nhẹ nhàng (ấn thử độ đàn hồi bọt nhớ của gối trên giường). TUYỆT ĐỐI CẤM đặt trên bàn làm việc/bàn cạnh giường.
      + Nếu là KỊCH BẢN FLASH SALE / XẢ KHO: Bối cảnh BẮT BUỘC là KHO HÀNG / XƯỞNG / SHOWROOM NGẬP TRÀN KIỆN HÀNG.
      + Nếu là ĐỒ GIA DỤNG / BẾP: Đặt trên mặt bàn bếp/đảo bếp (`kitchen counter`).
    - NHÂN VẬT THOẠI NGAY TẠI GIÂY 0.00: Tuyệt đối không đứng im hay trễ 1s đầu cảnh.
    - CÔNG THỨC NÓI GIÁ TƯƠNG PHẢN (KHI NÓI VỀ GIÁ): 
      + Neo giá gốc làm tròn (gần... nghìn / tận... nghìn).
      + Ghép từ nối tương phản và tính từ giá đáy: "Giá niêm yết gần [X] nghìn, nhưng hôm nay xả kho giảm cực sâu, bấm ngay giỏ hàng nhận deal hời, lưu ý giá có thể thay đổi tùy thời điểm nhé."
    - BẢNG SỐ TỪ CHUẨN XÁC ĐÃ TRỪ HAO ĐỘ TRỄ:
      + Phân cảnh 4s ➔ BẮT BUỘC viết từ 12 đến 14 từ (Tối đa 1 dấu phẩy)
      + Phân cảnh 6s ➔ BẮT BUỘC viết từ 18 đến 20 từ (Tối đa 1 dấu phẩy)
      + Phân cảnh 8s ➔ BẮT BUỘC viết từ 26 đến 28 từ (Tối đa 2 dấu phẩy)
      + Phân cảnh 10s ➔ BẮT BUỘC viết từ 34 đến 36 từ (Tối đa 2 dấu phẩy)
      + CHỈ ĐƯỢC CHỌN THỜI LƯỢNG LÀ 4s, 6s, 8s, HOẶC 10s.
    - CÂN BẰNG VẾ CÂU: Số từ giữa 2 vế qua dấu phẩy phải tương đương nhau, ngắt nghỉ nhẹ nhàng, không viết vế sau dài hơn vế trước.
    - BẮT BUỘC PHÂN BỔ CÁC PHÂN CẢNH THEO AIDA:
      + Cảnh 1 (Attention): Hook 3s đầu đánh đúng nỗi đau/tò mò, KHÔNG quảng cáo thô thiển.
      + Cảnh 2 (Interest): Đưa sản phẩm vào như giải pháp cứu cánh trong bối cảnh chuẩn.
      + Cảnh 3 (Desire): Nêu rõ tại sao nên mua, chứng minh tính vượt trội và minh họa cách sử dụng nhanh gọn.
      + Cảnh 4 (Action): Kêu gọi hành động tự nhiên, chốt sale bằng công thức giá tương phản Omni-channel.
    - KHÓA KHÔNG GIAN BÀN TAY VÀ VẬT THỂ (vid_p & action_en):
      + BẮT BUỘC chèn lệnh: "Strict numerical object persistence: Exactly ONE single product item visible throughout the shot, resting stably in its designated environment, strictly NO extra duplicates, NO disappearing artifacts. Anatomically separate hands and fingers with crisp spatial boundary; skin never merges with fabric or casing. Product maintains 100% frozen geometry, identical fabric weave, fixed print patterns, and invariant colors without warping, fading, or pixel bleeding."
    - TƯ THẾ ĐỨNG THẲNG TỰ NHIÊN & GÓC NGANG TẦM MẮT (action_en): 
      + TUYỆT ĐỐI CẤM NHÂN VẬT CÚI GẬP NGƯỜI, CÚI MẶT XUỐNG BÀN (NO leaning forward, NO crouching, NO hunching).
    - TRẦN THỜI GIAN TỐI ĐA 10S: Mọi phân cảnh BẮT BUỘC có thời lượng <= 10s (chỉ chọn trong 4s, 6s, 8s, 10s).
    - TỰ ĐỘNG TÁCH CẢNH NỐI TIẾP: Nếu nội dung dài vượt quá 36 từ, BẮT BUỘC TÁCH THÀNH 2 PHÂN CẢNH NỐI TIẾP. Cảnh sau ghi 'trans': "Nối tiếp liền mạch từ cảnh trước"'.
    - CẤU TRÚC THOẠI HÀ NỘI: BẮT BUỘC NGẮT NGHỈ BẰNG DẤU PHẨY (,) CÂN BẰNG. Văn phong HÀ NỘI GỐC (Cấm: nha, nè, vô).
    - BỘ LỌC CHÍNH SÁCH: Cấm "tuyệt đối", "hoàn toàn", "100%", "chắc chắn", "thuốc".
    - ANTI-UI/TEXT LOCK: Khi KOC chỉ tay, KHÔNG nhắc đến "cart, button, icon". Chèn chuỗi cấm UI/Text vào cuối mọi ảnh/video.
    - PURE VOICEOVER & FULL AUDIO IN PROMPT: 'voiceover' KHÔNG chứa ngoặc đơn. Trong 'vid_p', PHẢI CHÉP LẠI TOÀN BỘ 100% lời thoại vào phần Audio, TUYỆT ĐỐI KHÔNG LÀM NGẮN.
    
    TRẢ VỀ JSON CHUẨN XÁC:
    {{
        "title": "{outline.get('title')}",
        "total_dur": "Tổng thời gian",
        "outfit_vi": "Tóm tắt trang phục và bối cảnh",
        "global_identity_en": "Exact English desc of Face, Hair, Body.",
        "global_outfit_en": "Exact English desc of the FULL multi-layered outfit. MUST BE LOCKED.",
        "global_setting_en": "Exact English desc of the unified native environment/setting (e.g. cozy modern bedroom with neatly made bed for pillows, or authentic warehouse/showroom for flash sale). MUST BE LOCKED.",
        "prod_dna": "Mô tả SP bằng Tiếng Anh. BẮT BUỘC CHỨA MÀU SẮC CHÍNH XÁC. Strict numerical persistence of exactly ONE item.",
        "voice": {{"gender": "Nam/Nữ", "tone": "{voice_hint}"}},
        "scenes": [
            {{
                "scene": 1, 
                "aida_stage": "Attention / Interest / Desire / Action",
                "word_count": "AI điền số nguyên. ĐẾM CHÍNH XÁC TỪNG TỪ.",
                "dur": "4s/6s/8s/10s (Bắt buộc khớp chuẩn an toàn: 12-14 từ -> 4s, 18-20 từ -> 6s, 26-28 từ -> 8s, 34-36 từ -> 10s)", 
                "trans": "Chuyển cảnh mới hoặc Nối tiếp liền mạch từ cảnh trước", 
                "setting": "Mô tả bối cảnh tiếng Việt chuẩn xác (Phòng ngủ đặt trên giường, hoặc Kho hàng xưởng xả kho)...",
                "action_en": "Direct eye-level shot. Character maintains upright natural elegant posture (NO crouching, NO leaning forward, NO awkward hunching). Interacts naturally with product resting in its native location. Hands show clear anatomical separation without merging into fabric. Expressive bright eyes, engaging authentic micro-smile, crisp natural mouth articulation starting immediately at 0.00s matching dialogue cadence.",
                "director": "Giai đoạn AIDA: Attention/Interest/Desire/Action | Bối cảnh: Native chuẩn xác | Âm thanh thực tế: [Mô tả chi tiết SFX thực tế] | Khởi động: THOẠI NGAY TẠI GIÂY 0.00 | Tông: Giọng ngực đầy nội lực (4.3 - 4.5 từ/s)", 
                "voiceover": "Thoại CÂU GHÉP CÓ DẤU PHẨY (,) CÂN BẰNG TỪ HAI VẾ, NGẮT NGHỈ RẤT NGẮN. TÔNG GIỌNG MẠNH MẼ KHÔNG ĐỀU ĐỀU. CẤM BỎ NGOẶC ĐƠN VÀO. THOẠI TỰ NHIÊN KHÔNG QUẢNG CÁO LỘ LIỄU. NẾU NÓI GIÁ PHẢI DÙNG ĐÒN BẨY TƯƠNG PHẢN. CẤM TỪ MIỀN NAM. LÁCH TỪ VI PHẠM.",
                "img_p": "Cinematic vertical 9:16 photo. Direct eye-level static shot. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en], positioned naturally with upright posture. Action: [action_en]. Product: [prod_dna] resting stably on designated surface. Maintain EXACT original product colors for all parts. Strict zero-mutation geometry. NO added handles, NO extra lifting loops, NO phantom fixtures. NO generated text, NO subtitles, NO typography, NO watermarks, NO UI elements, NO icons, NO logos, NO buttons, NO floating graphics. Clean frame.", 
                "vid_p": "Vertical 9:16 video. Direct eye-level static shot. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en], upright natural stance without hunching or awkward crouching. Action: [action_en]. Immediate speech start at second 0.00 without idle delay. Audio: \\"[ĐIỀN ĐẦY ĐỦ 100% NỘI DUNG VOICEOVER VÀO ĐÂY, KHÔNG CẮT BỚT]\\", Layered SFX: [Mô tả âm thanh tiếng Anh thực tế: sizzling frying sound, crunchy chewing sound, whooshing wind breeze, mechanical latch click...], ambient room tone. Product: [prod_dna]. Strict numerical object persistence: Exactly ONE single product item visible throughout the shot, strictly NO extra duplicates, NO disappearing artifacts. Anatomically separate hands and fingers with crisp spatial boundary; skin never merges with fabric or casing. Product maintains 100% frozen geometry, identical fabric weave, fixed print patterns, and invariant colors without warping, fading, or pixel bleeding. Strict zero-mutation geometry. NO added handles, NO extra lifting loops, NO phantom fixtures. NO morphing, NO warping, NO melting edges. NO generated text, NO subtitles, NO typography, NO watermarks, NO UI elements, NO icons, NO logos, NO buttons, NO floating graphics. Clean frame."
            }}
        ]
    }}
    """
    res = call_gemini([prompt], get_sys_inst_details(mode, style, narrator_mode, char_rules, f"TỔNG THỜI GIAN: {duration_instruction}"), max_tokens=4096)
    if not res or "scenes" not in res: raise Exception("AI JSON Error.")
    st.session_state.generated_details[target_id] = res

def generate_more_scripts(angle, num_chars, extra_char_inputs, narrator_mode_more, duration_inst, char_profiles):
    mode = st.session_state.get("last_mode", "Bán Hàng")
    style = st.session_state.get("last_style", "Điện ảnh")
    char_rules = generate_char_rules_string(char_profiles)
    cur_len = len(st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts)
    
    prod_ctx = f"INPUT: {st.session_state.current_input_context}"
    if mode == "Viral": db_ctx = f"DB: {json.dumps({'Kênh': st.session_state.get('viral_persona', ''), 'Chủ đề': st.session_state.get('viral_topic', '')}, ensure_ascii=False)}"
    else: db_ctx = f"DB: {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)}" if st.session_state.current_product_data_saved else ""
    dna_ctx = f"DNA: {json.dumps(st.session_state.content_analysis, ensure_ascii=False)}" if st.session_state.content_analysis else ""
    
    prompt = f"""
    {prod_ctx} | {db_ctx} | {dna_ctx}

    🛑 LỆNH TẨY NÃO: BẠN BẮT BUỘC PHẢI VIẾT CẢ 5 KỊCH BẢN MỚI THEO MÔ HÌNH AIDA VÀ CHIẾN LƯỢC: '{angle}'.
    - Phân biệt bối cảnh: Nếu Flash Sale thì là Kho hàng/Xưởng ngập kiện hàng; nếu Review sản phẩm phòng ngủ/gối/đệm thì BẮT BUỘC là Phòng ngủ đặt gối trên giường ngủ.
    - Hook 3 giây đầu đánh trúng nỗi đau/tò mò/xúc động, không quảng cáo lộ liễu.
    - Làm rõ: Sản phẩm là gì/có gì đặc biệt, Dành cho ai, Tại sao nên mua, Dùng ở đâu tiện ích ra sao, Cách dùng thực tế.
    - Áp dụng công thức giá tương phản Omni-channel (neo giá gốc làm tròn, khẳng định giảm cực sâu/chạm đáy, kêu gọi bấm xem deal hời, miễn trừ trách nhiệm thời gian).

    SỐ DIỄN VIÊN: {num_chars}.
    LUẬT: CÂU GHÉP DÀI CÂN BẰNG VẾ CÂU, TÔNG GIỌNG MẠNH MẼ, ĐANH THÉP, NHỊP ĐỘ ĐỀU METRONOME, THOẠI NGAY ĐẦU CẢNH. Giọng HÀ NỘI CHUẨN. CẤM DÙNG TỪ: tuyệt đối, hoàn toàn, 100%, thuốc, đặc trị. ĐỒNG NHẤT 1 BỐI CẢNH. Khung hình cấm UI/Icon.

    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{
                "id": {cur_len+1},
                "title": "Tên kịch bản 1",
                "setting": "Bối cảnh thực tế chuẩn xác (Phòng ngủ đặt trên giường ngủ nếu là gối đệm; Kho hàng xưởng nếu là Flash Sale)",
                "hook": "Hook 3 giây đầu AIDA: Xưng hô tự nhiên, đánh trúng nỗi đau hoặc gây tò mò cực độ, KHÔNG quảng cáo lộ liễu (CÓ CHỦ VỊ, CẤM TỪ VI PHẠM, TÔNG GIỌNG MẠNH MẼ ĐANH THÉP)",
                "actors": {num_chars}
            }}
        ]
    }}
    🛑 BẮT BUỘC ĐÚNG 5 KỊCH BẢN.
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, narrator_mode_more, char_rules, num_chars, angle), max_tokens=3000)
    if not res or ("outlines" not in res and "script_outlines" not in res): raise Exception("AI JSON Error.")
    more_scripts = res.get("outlines", res.get("script_outlines", []))
    for idx, sc in enumerate(more_scripts): 
        sc["id"] = cur_len + idx + 1
        sc["duration_instruction"] = duration_inst
        sc["narrator_mode"] = narrator_mode_more
        sc["character_profiles"] = char_profiles
    return more_scripts

def clone_script(script_id):
    mode = st.session_state.get("last_mode", "Bán Hàng")
    style = st.session_state.get("last_style", "Điện ảnh")
    
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if sc["id"] == script_id), None)
    cur_len = len(all_combined)
    num_chars = target.get("actors", target.get("actor_count", 1))
    
    target_dur = target.get("duration_instruction", st.session_state.get("target_duration_instruction", ""))
    target_narrator = target.get("narrator_mode", st.session_state.get("last_narrator", ""))
    target_chars = target.get("character_profiles", st.session_state.get("character_profiles", []))
    char_rules = generate_char_rules_string(target_chars)
    dna_str = json.dumps(st.session_state.content_analysis, ensure_ascii=False) if st.session_state.content_analysis else "N/A"
    
    prompt = f"""
    DỮ LIỆU GỐC: {dna_str}
    Nhân bản kịch bản gốc theo mô hình AIDA: {json.dumps(target, ensure_ascii=False)}. Tạo 5 biến thể mới.
    LUẬT: Thoại CÂU GHÉP DÀI CÂN BẰNG VẾ CÂU, TÔNG GIỌNG MẠNH MẼ ĐANH THÉP. Hook không lộ liễu. Bối cảnh chuẩn native (phòng ngủ trên giường nếu là gối nệm; kho hàng nếu là flash sale). Giọng HÀ NỘI GỐC. Cấm "tuyệt đối", "chữa bệnh". Đặt BỐI CẢNH ĐỒNG NHẤT. Nếu bán hàng, dùng công thức giá tương phản Omni-channel.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "...", "setting": "...", "hook": "...", "actors": {num_chars} }}
        ]
    }}
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, target_narrator, char_rules, num_chars, "Giữ nguyên chiến lược gốc"), max_tokens=3000)
    if not res or ("outlines" not in res and "script_outlines" not in res): raise Exception("AI JSON Error.")
    clones = res.get("outlines", res.get("script_outlines", []))
    for idx, cl in enumerate(clones): 
        cl["id"] = cur_len + idx + 1
        cl["duration_instruction"] = target_dur
        cl["narrator_mode"] = target_narrator
        cl["character_profiles"] = target_chars
    return clones

def save_project_to_db(email, title, payload_data, project_id=None):
    if not supabase: return "Chưa kết nối Database Supabase."
    try:
        clean_content = json.loads(json.dumps(payload_data, default=str)) 
        if project_id: supabase.table("saved_projects").update({"project_title": title, "script_content": clean_content}).eq("id", project_id).execute()
        else:
            res = supabase.table("saved_projects").insert({"user_email": email, "project_title": title, "script_content": clean_content}).execute()
            if res.data: st.session_state.current_project_id = res.data[0]['id']
        return True
    except Exception as e: return str(e)

# ==============================================================================
# 3. THANH BÊN (SIDEBAR) & TÀI KHOẢN (AUTH & LEAD GEN)
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        tabs = st.tabs(["🔐 Đăng Nhập", "🚀 Đăng Ký"])
        with tabs[0]:
            with st.form("login_form", border=False):
                email_input = st.text_input("Email:", placeholder="Nhập email của bạn...", key="login_email_input", autocomplete="new-password")
                pass_input = st.text_input("Mật khẩu:", type="password", placeholder="Nhập mật khẩu...", key="login_pass_input", autocomplete="new-password")
                
                btn_login_ph = st.empty()
                if st.session_state.get("loading_login", False):
                    btn_login_ph.empty()
                    st.markdown("<div style='background: #eff6ff; border: 1px solid #93c5fd; padding: 8px; border-radius: 8px; color: #1e3a8a; text-align: center; font-weight: bold;'>⏳ Đang xác thực...</div>", unsafe_allow_html=True)
                    
                    email_check, pass_check = email_input.strip(), pass_input.strip()
                    if email_check in st.session_state.licensed_accounts:
                        acc_info = st.session_state.licensed_accounts[email_check]
                        if acc_info.get("password") == pass_check:
                            exp_date_str = acc_info.get("expires_at", "2099-12-31")
                            try:
                                if datetime.now() > datetime.strptime(exp_date_str, "%Y-%m-%d"):
                                    st.error("❌ Tài khoản đã hết hạn!"); st.session_state.loading_login = False; st.stop()
                            except: pass
                            st.session_state.licensed_accounts[email_check]["active_session_id"] = st.session_state.session_id
                            save_single_account(email_check, st.session_state.licensed_accounts[email_check])
                            st.session_state.is_logged_in, st.session_state.current_email = True, email_check
                            st.toast("✅ Đăng nhập thành công!")
                            st.session_state.loading_login = False
                            time.sleep(0.5); st.rerun()
                        else: st.error("Sai mật khẩu!"); st.session_state.loading_login = False
                    else: st.error("Tài khoản chưa được cấp quyền!"); st.session_state.loading_login = False
                else:
                    if btn_login_ph.form_submit_button("🔑 Đăng Nhập", type="primary", use_container_width=True):
                        st.session_state.loading_login = True
                        st.rerun()

        with tabs[1]:
            st.markdown("<p style='font-size: 13px; color: #475569;'>Đăng ký nhận ngay 3 lượt trải nghiệm/ngày.</p>", unsafe_allow_html=True)
            with st.form("register_form", border=False):
                reg_email = st.text_input("Email đăng ký:", autocomplete="new-password")
                reg_phone = st.text_input("Số điện thoại:", autocomplete="new-password")
                reg_pass = st.text_input("Mật khẩu mới:", type="password", autocomplete="new-password")
                
                btn_reg_ph = st.empty()
                if st.session_state.get("loading_reg", False):
                    btn_reg_ph.empty()
                    st.markdown("<div style='background: #eff6ff; border: 1px solid #93c5fd; padding: 8px; border-radius: 8px; color: #1e3a8a; text-align: center; font-weight: bold;'>⏳ Đang đăng ký...</div>", unsafe_allow_html=True)
                    
                    email_check, phone_check = reg_email.strip(), reg_phone.strip()
                    if not email_check or not phone_check or not reg_pass.strip(): st.error("Điền đủ thông tin!"); st.session_state.loading_reg = False
                    elif not is_valid_phone(phone_check): st.error("SĐT không hợp lệ!"); st.session_state.loading_reg = False
                    elif email_check in st.session_state.licensed_accounts: st.error("Email đã tồn tại!"); st.session_state.loading_reg = False
                    else:
                        exp_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[email_check] = {
                            "roles": ALL_MODULES, "phone": phone_check, "password": reg_pass.strip(),
                            "expires_at": exp_date, "plan_type": "Trial", "daily_usage_count": 0,
                            "last_generation_date": "", "active_session_id": st.session_state.session_id
                        }
                        save_single_account(email_check, st.session_state.licensed_accounts[email_check])
                        st.session_state.is_logged_in, st.session_state.current_email = True, email_check
                        st.toast("✅ Đăng ký thành công!")
                        st.session_state.loading_reg = False
                        time.sleep(0.5); st.rerun()
                else:
                    if btn_reg_ph.form_submit_button("🚀 Đăng Ký Tài Khoản", type="secondary", use_container_width=True):
                        st.session_state.loading_reg = True
                        st.rerun()
    else:
        current_acc = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        if current_acc and st.session_state.current_email != ADMIN_EMAIL and current_acc.get("plan_type", "Trial") != "Trial":
            try:
                days_left = (datetime.strptime(current_acc.get("expires_at", "2099-12-31"), "%Y-%m-%d") - datetime.now()).days
                if 0 <= days_left <= 7: st.warning(f"⚠️ Tài khoản hết hạn sau **{days_left} ngày nữa**.")
            except: pass

        st.markdown("### 🗂 LÀM VIỆC")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True):
            with st.spinner("⏳ Đang khởi tạo..."):
                st.session_state.update({k: v for k, v in [("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []), ("generated_details", {}), ("content_analysis", None), ("active_script_id", None), ("current_input_context", ""), ("current_product_data_saved", None), ("character_profiles", []), ("current_project_id", None)]})
                st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
                st.session_state.reset_key += 1
                st.toast("✅ Đã tạo mới!")
                time.sleep(0.5)
                st.rerun()
            
        st.session_state.active_project_title = st.text_input("Tên dự án hiện tại:", value=st.session_state.active_project_title)
        
        if st.button("💾 Lưu Dự Án Này", use_container_width=True):
            with st.spinner("⏳ Đang lưu dữ liệu lên Cloud..."):
                if not (st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts): st.warning("⚠️ Chưa có kịch bản!")
                else:
                    payload = {k: st.session_state[k] for k in ["content_analysis", "all_scripts", "cloned_scripts", "expanded_scripts", "generated_details", "character_profiles", "current_input_context", "target_duration_instruction"]}
                    save_result = save_project_to_db(st.session_state.current_email, st.session_state.active_project_title, payload, st.session_state.current_project_id)
                    if save_result is True: st.toast("✅ Đã lưu thành công!")
                    else: st.error(f"❌ {save_result}")
        
        st.markdown("---")
        st.markdown("### 📂 KHO LƯU TRỮ")
        if not supabase: st.error("Chưa kết nối Database.")
        else:
            try:
                res = supabase.table("saved_projects").select("*").order("created_at", desc=True).execute() if st.session_state.current_email == ADMIN_EMAIL else supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
                projects = res.data
            except: projects = []

            search_proj = st.text_input("🔍 Tìm kiếm dự án:", placeholder="Nhập tên hoặc ngày...")
            if search_proj: projects = [p for p in projects if search_proj.lower() in p['project_title'].lower() or search_proj in p['created_at']]

            if not projects: st.info("Không có dự án.")
            else:
                st.markdown("<div class='scrollable-sidebar-container'>", unsafe_allow_html=True)
                for p in projects:
                    with st.expander(f"🎬 {p['project_title']}"):
                        st.caption(f"📅 {p['created_at'][:10]}")
                        if st.session_state.current_email == ADMIN_EMAIL: st.caption(f"👤 Tạo bởi: {p['user_email']}")
                        col_open, col_del = st.columns(2)
                        
                        if col_open.button("📂 Mở", key=f"btn_o_{p['id']}", use_container_width=True):
                            with st.spinner("⏳ Đang khôi phục..."):
                                sd = p.get("script_content", {})
                                if isinstance(sd, dict):
                                    st.session_state.update({
                                        "content_analysis": sd.get("content_analysis"), "all_scripts": sd.get("all_scripts", []), "cloned_scripts": sd.get("cloned_scripts", []),
                                        "expanded_scripts": sd.get("expanded_scripts", []), "generated_details": {int(k): v for k, v in sd.get("generated_details", {}).items()},
                                        "character_profiles": sd.get("character_profiles", []), "current_input_context": sd.get("current_input_context", ""), "target_duration_instruction": sd.get("target_duration_instruction", "")
                                    })
                                st.session_state.update({"current_project_id": p['id'], "active_project_title": p['project_title'], "active_script_id": None, "scroll_to_top": True})
                                st.session_state.reset_key += 1
                                st.toast("✅ Đã khôi phục!")
                                time.sleep(0.5)
                                st.rerun()
                            
                        if col_del.button("🗑️ Xóa", key=f"btn_d_{p['id']}", type="secondary", use_container_width=True):
                            with st.spinner("⏳ Đang xóa..."):
                                supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                                st.toast("✅ Đã xóa!")
                                time.sleep(0.5)
                                st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.current_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙ QUẢN TRỊ ADMIN")
            with st.form("add_license"):
                st.markdown("##### ➕ Cấp Quyền Khách Hàng Mới")
                n_acc, n_phone, n_pass = st.text_input("Email:", autocomplete="new-password"), st.text_input("SĐT:", autocomplete="new-password"), st.text_input("Mật khẩu:", value="123456", autocomplete="new-password")
                acc_type = st.radio("Loại:", ["Trial", "Basic", "Advanced", "VIP"])
                roles = st.multiselect("Phân quyền:", ALL_MODULES, default=ALL_MODULES)
                dur = st.selectbox("Thời hạn:", ["3 Ngày", "7 Ngày", "1 Tháng", "Vĩnh viễn"])
                if st.form_submit_button("💾 Cấp Quyền"):
                    if n_acc and n_phone and n_pass:
                        exp = "2099-12-31" if "Vĩnh" in dur else (datetime.now() + timedelta(days={"3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30}[dur])).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[n_acc] = {"roles": roles, "phone": n_phone, "password": n_pass, "expires_at": exp, "plan_type": acc_type, "daily_usage_count": 0, "last_generation_date": "", "active_session_id": ""}
                        save_single_account(n_acc, st.session_state.licensed_accounts[n_acc])
                        st.toast("✅ Đã cấp quyền!")
                        time.sleep(0.5)
                        st.rerun()

            for acc, info in list(st.session_state.licensed_accounts.items()):
                if acc == ADMIN_EMAIL: continue
                with st.expander(f"👤 {acc} ({info.get('plan_type')})"):
                    st.caption(f"Phone: {info.get('phone')} | Exp: {info.get('expires_at')}")
                    if st.button("🗑 Xóa", key=f"d_adm_{acc}"): 
                        del st.session_state.licensed_accounts[acc]; delete_single_account(acc)
                        st.rerun()

        st.markdown("---")
        user_info = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        plan = user_info.get("plan_type", "Trial")
        used = user_info.get("daily_usage_count", 0) if user_info.get("last_generation_date") == datetime.now().strftime("%Y-%m-%d") else 0
        limit = "Không giới hạn" if plan == "VIP" else (20 if plan == "Advanced" else (10 if plan == "Basic" else 3))
        st.info(f"**GÓI {plan.upper()}**\n\n• Email: {st.session_state.current_email}\n• Tạo chi tiết: **{used}/{limit}**\n• Hết hạn: {user_info.get('expires_at', '')}")

        if st.button("🚪 Đăng Xuất"): 
            with st.spinner("⏳ Đang thoát..."):
                st.session_state.is_logged_in = False
                st.toast("✅ Đăng xuất!")
                time.sleep(0.5)
                st.rerun()

if not st.session_state.is_logged_in: st.info("👈 Vui lòng đăng nhập ở thanh bên."); st.stop()

# ==============================================================================
# 5. KHÔNG GIAN SÁNG TẠO CHÍNH
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div></div>""", unsafe_allow_html=True)
allowed_categories = st.session_state.licensed_accounts.get(st.session_state.current_email, {}).get("roles", ALL_MODULES) or ALL_MODULES
mode = st.selectbox("🎯 Thể loại:", allowed_categories, key=f"mode_sel_{st.session_state.reset_key}")
is_viral_mode = "Viral" in mode

up_files, custom_note = [], ""
if is_viral_mode:
    st.markdown("#### 🌟 Thông tin Kênh & Chủ đề")
    col_v1, col_v2 = st.columns(2)
    viral_persona = col_v1.text_input("👤 Định vị Kênh:", key=f"vp_{st.session_state.reset_key}")
    viral_topic = col_v2.text_area("💡 Chủ đề / Mẹo:", height=68, key=f"vt_{st.session_state.reset_key}")
    with st.expander("📎 Dữ liệu bổ sung (Tùy chọn)"):
        up_files = st.file_uploader("📦 Upload Ảnh:", type=["jpg", "png"], accept_multiple_files=True, key=f"uv_{st.session_state.reset_key}")
        custom_note = st.text_area("✍ Ghi chú:", key=f"nv_{st.session_state.reset_key}")
else:
    st.markdown("#### 🛒 Nhập thông tin sản phẩm")
    products_data = supabase.table("products").select("*").execute().data if supabase else []
    if products_data:
        selected_name = st.selectbox("📌 Chọn sản phẩm:", [p["product_name"] for p in products_data], key=f"sp_{st.session_state.reset_key}")
        st.session_state.current_product_data = next(p for p in products_data if p["product_name"] == selected_name)
        prod = st.session_state.current_product_data
        with st.container(border=True):
            col_a, col_b = st.columns(2)
            col_a.markdown(f"**💰 Hoa hồng:** <span style='color:#15803d; font-weight:900;'>{prod.get('commission_percent', 0)}%</span><br>**🎯 Tệp:** {prod.get('target_audience', '')}", unsafe_allow_html=True)
            col_b.markdown(f"**🧠 Insight:** {prod.get('product_insight', '')}<br>**💔 Nỗi đau:** {prod.get('pain_points', '')}", unsafe_allow_html=True)
    up_files = st.file_uploader("📦 Upload Ảnh SP (Tự động nén tối ưu Token - Đọc Giá & Cơ chế mở nắp):", type=["jpg", "png"], accept_multiple_files=True, key=f"us_{st.session_state.reset_key}")
    custom_note = st.text_area("✍ Ghi chú AI:", key=f"ns_{st.session_state.reset_key}")

st.markdown("---")
st.markdown("### 🎥 Đạo Diễn, Góc Quay & Thời Lượng")
col_opt1, col_opt2 = st.columns(2)

style = col_opt1.selectbox("🎨 Phong cách hình ảnh:", ["Điện Ảnh Chân Thực", "Hoạt Hình 3D", "Hoạt Hình 2D", "Studio Tối Giản"], key=f"sty_{st.session_state.reset_key}")
angle_options = ["🌟 Tự động mix", "🧠 Chuyên gia", "💡 Mẹo hay", "🎭 Drama", "📖 Storytelling", "😂 Hài hước"] if is_viral_mode else ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Chia sẻ", "😂 Hài hước (Chốt sale)"]
initial_angle = col_opt1.selectbox("🧭 Chiến lược:", angle_options, key=f"ang_{st.session_state.reset_key}")

duration_choice = col_opt2.selectbox("⏳ Thời lượng video:", ["Tự động (AI Tối ưu ~20-30s)", "Tùy chỉnh (Nhập số giây)"], key=f"dur_{st.session_state.reset_key}")
if duration_choice.startswith("Tùy"): st.session_state.target_duration_instruction = f"Chính xác {col_opt2.number_input('Số giây:', min_value=10, max_value=300, value=60)} giây."
else: st.session_state.target_duration_instruction = "Khoảng 15-30 giây."

narrator_mode = col_opt2.selectbox("🎙 Thuyết minh:", ["Nhân vật xuất hiện (On-camera)", "🎙 Lồng tiếng ngoài (Off-screen)"], key=f"nar_{st.session_state.reset_key}")
num_chars = st.number_input("👤 Số lượng Diễn viên:", min_value=1, max_value=8, value=1, key=f"num_{st.session_state.reset_key}")

char_inputs = []
if num_chars > 0:
    for i in range(num_chars):
        c_r, c_i = st.columns([2, 1])
        role = c_r.text_input(f"Vai trò NV {i+1}:", key=f"r_{i}_{st.session_state.reset_key}")
        c_file = c_i.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"f_{i}_{st.session_state.reset_key}", label_visibility="collapsed")
        if c_file: char_inputs.append({"id": i+1, "role": role or "AI tự phân tích", "file": c_file})

if st.button("🚀 PHÂN TÍCH DNA & SINH 5 KỊCH BẢN ĐA VŨ TRỤ", type="primary", use_container_width=True):
    can_run, msg = check_usage_limit(st.session_state.current_email, is_detailing=False)
    if not can_run: st.error(f"❌ {msg}")
    else:
        with st.spinner("⏳ Đạo diễn AI đang nén ảnh tối ưu token và phân tích DNA sản phẩm... Vui lòng đợi!"):
            try:
                st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
                char_rules = generate_char_rules_string(st.session_state.character_profiles)
                st.session_state.update({"last_mode": mode, "last_style": style, "last_narrator": narrator_mode, "current_input_context": custom_note, "current_project_id": None})
                st.session_state.current_product_data_saved = {"Định vị Kênh": viral_persona, "Chủ đề": viral_topic} if is_viral_mode else st.session_state.get("current_product_data")
                
                prompt = f"""
                INPUT DATA: {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)} | NOTES: {custom_note}
                BẮT BUỘC TRẢ VỀ JSON HỢP LỆ VỚI CẤU TRÚC:
                {{
                    "content_analysis": {{
                        "target_audience": "Nhận diện TỆP KHÁCH HÀNG MỤC TIÊU",
                        "core_value": "Giá trị cốt lõi giải quyết vấn đề gì", 
                        "pain_points": "Nỗi đau / Rào cản lớn nhất của khách hàng", 
                        "hook_element": "Yếu tố giật gân, tạo tò mò hoặc xúc động đánh đúng tâm lý trong 3 giây đầu",
                        "what_and_unique": "SẢN PHẨM LÀ GÌ & CÓ GÌ ĐẶC BIỆT: Định danh sản phẩm và điểm độc bản (USP) vượt trội",
                        "target_user": "SẢN PHẨM DÀNH CHO AI: Đối tượng cụ thể phù hợp nhất",
                        "why_buy": "TẠI SAO NÊN MUA: Lý do thuyết phục không thể chối từ",
                        "where_and_convenience": "DÙNG Ở ĐÂU & TIỆN LỢI LÀ GÌ: Hoàn cảnh ứng dụng thực tế và tính linh hoạt",
                        "how_to_use": "CÁCH SỬ DỤNG: Thao tác thực tế 1-2 bước trực quan, dễ dàng",
                        "product_size_class": "Phân loại kích thước SP. Tương tác vật lý không ảo giác.",
                        "product_color_lock": "QUÉT THỊ GIÁC TUYỆT ĐỐI CHÍNH XÁC: Bóc tách màu sắc chi tiết của TỪNG BỘ PHẬN sản phẩm từ ảnh tải lên. CẤM bịa màu.",
                        "lid_mechanism": "QUÉT CƠ CHẾ MỞ NẮP TỪ ẢNH: Phân tích xem nắp là nắp liền bản lề hay nắp rời. Vị trí nút bấm/chốt mở nằm ở đâu. Khóa cố định không vẽ thêm quai xách.",
                        "detected_prices": "QUÉT OCR TUYỆT ĐỐI CHÍNH XÁC: Đọc kĩ ảnh tải lên để tìm Giá Gốc và Giá Sale (nếu có). Trích xuất nguyên bản text.",
                        "product_dimensions": "QUÉT OCR TUYỆT ĐỐI CHÍNH XÁC: Quét ảnh tìm thông số kích thước thực tế. Nệm/Thảm BẮT BUỘC dùng từ 'Độ dày' kèm ước lượng (khoảng).",
                        "voice_gender": "Phân tích xem sản phẩm này hợp giọng Nam hay Nữ để đọc thoại",
                        "prompt_dna_lock": "Khóa thị giác (Visual DNA) cho AI sinh video. Strict zero-mutation geometry. NO added handles, NO extra lifting loops, NO phantom fixtures."
                    }},
                    "outlines": [ 
                        {{
                            "id": 1, "title": "Tên", "setting": "Bối cảnh thực tế chuẩn xác (Phòng ngủ đặt trên giường ngủ nếu là gối đệm; Kho hàng xưởng nếu là Flash Sale)", 
                            "hook": "HOOK 3 GIÂY ĐẦU AIDA: Xưng hô dân dã, đánh trúng nỗi đau hoặc tò mò xúc động, KHÔNG quảng cáo lộ liễu. TÔNG GIỌNG MẠNH MẼ, ĐANH THÉP, DỒN DẬP.",
                            "actors": {num_chars}
                        }},
                        {{ "id": 2, "title": "...", "setting": "...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 3, "title": "...", "setting": "...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 4, "title": "...", "setting": "...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 5, "title": "...", "setting": "...", "hook": "...", "actors": {num_chars} }}
                    ]
                }}
                🛑 NẾU CHIẾN LƯỢC LÀ TỰ ĐỘNG MIX THÌ BẠN HÃY MIX. CÒN NẾU CHIẾN LƯỢC LÀ '{initial_angle}', BẠN BẮT BUỘC PHẢI TRẢ VỀ CẢ 5 KỊCH BẢN THEO ĐÚNG CHIẾN LƯỢC NÀY. KHÔNG ĐƯỢC MIX! CẤM XUẤT HIỆN CHỮ/SUBTITLES Ở HÌNH VÀ VIDEO. BẮT BUỘC TUÂN THỦ CHÍNH SÁCH MỌI NỀN TẢNG (Cấm "tuyệt đối", cấm "chữa bệnh").
                """
                payload = ["REFERENCE IMAGES:"]
                if up_files:
                    for f in up_files:
                        c_bytes, c_mime = compress_image_bytes(f, max_dimension=1024, quality=80)
                        payload.append(types.Part.from_bytes(data=c_bytes, mime_type=c_mime))
                        
                for c in char_inputs:
                    c_bytes, c_mime = compress_image_bytes(c['file'], max_dimension=768, quality=80)
                    payload.extend([f"ACTOR {c['id']}:", types.Part.from_bytes(data=c_bytes, mime_type=c_mime)])
                payload.append(prompt)
                
                res = call_gemini(payload, get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, initial_angle), max_tokens=4096)
                if not res or ("outlines" not in res and "script_outlines" not in res): st.error("❌ AI lỗi định dạng.")
                else:
                    st.session_state.content_analysis = res.get("content_analysis")
                    outlines = res.get("outlines", res.get("script_outlines", []))
                    for o in outlines: o.update({"duration_instruction": st.session_state.target_duration_instruction, "narrator_mode": narrator_mode, "character_profiles": st.session_state.character_profiles})
                    st.session_state.update({"all_scripts": outlines, "cloned_scripts": [], "expanded_scripts": [], "generated_details": {}, "active_script_id": None, "scroll_to_top": True})
                    st.toast("✅ Đã phân tích xong (Đã tối ưu token ảnh)!")
            except Exception as e: st.error(f"❌ Lỗi: {e}")

# Hiển thị DNA
ca = st.session_state.content_analysis
if isinstance(ca, dict):
    st.divider()
    st.markdown(f"### 🔍 **Phân Tích DNA Chi Tiết Theo Mô Hình AIDA**")
    with st.container(border=True):
        st.markdown(f"##### 🎯 **1. Chân dung Khách hàng & Hook 3s (Attention):**<br><div style='line-height: 1.8;'>{format_analysis_field(ca.get('target_audience', ''))}<br>{format_analysis_field(ca.get('pain_points', ''))}<br><b>⚡ Yếu tố Hook 3s đầu:</b> <span style='color:#d90429; font-weight:bold;'>{ca.get('hook_element', '')}</span></div>", unsafe_allow_html=True)
        st.markdown(f"--- \n##### 💎 **2. Giải phẫu Sản phẩm Không Lộ Liễu (Interest & Desire):**<br><div style='line-height: 1.8;'><b>📦 Sản phẩm là gì & Điểm đặc biệt:</b> {ca.get('what_and_unique', '')}<br><b>👥 Sản phẩm dành cho ai:</b> {ca.get('target_user', '')}<br><b>🔥 Tại sao nên mua:</b> {ca.get('why_buy', '')}<br><b>📍 Dùng ở đâu & Tiện lợi:</b> {ca.get('where_and_convenience', '')}<br><b>🛠 Cách sử dụng:</b> {ca.get('how_to_use', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"--- \n##### 🏭 **3. Vật lý, Cơ chế & Màu sắc Đa Chi Tiết:**<br><div style='line-height: 1.8;'><b>📐 Thông số (Đã lọc vi phạm):</b> <span style='color:#059669; font-weight:bold;'>{ca.get('product_dimensions', 'Chưa lấy được kích thước')}</span><br><b>🎨 Màu chi tiết (Đã khóa):</b> <span style='color:#0284c7; font-weight:bold;'>{ca.get('product_color_lock', 'Không xác định')}</span><br><b>⚙ Cơ chế mở nắp thực tế:</b> <span style='color:#8b5cf6; font-weight:bold;'>{ca.get('lid_mechanism', 'Bản lề thông thường')}</span><br><b>💰 Mức giá (OCR):</b> <span style='color:#d90429; font-weight:bold;'>{ca.get('detected_prices', 'Không tìm thấy')}</span></div>", unsafe_allow_html=True)
    if ca.get('prompt_dna_lock'): st.markdown("##### 📌 **Visual DNA Lock:**"); st.code(ca.get('prompt_dna_lock'), language="text")

# DANH SÁCH KỊCH BẢN
all_sc = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
if all_sc:
    st.divider()
    comp_sc = [sc for sc in all_sc if sc["id"] in st.session_state.generated_details]
    pend_sc = [sc for sc in all_sc if sc["id"] not in st.session_state.generated_details]

    if st.session_state.active_script_id is not None:
        if st.button("⬅ Thu gọn danh sách"): st.session_state.active_script_id = None; st.session_state.scroll_to_top = True; st.rerun()
        
        asc = st.session_state.generated_details.get(st.session_state.active_script_id, {})
        vp = asc.get("voice", {})
        if isinstance(vp, str): vp = {"gender": "Nữ", "tone": vp}
        
        st.markdown("<div id='detailed-view-anchor'></div>", unsafe_allow_html=True)
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT (CHUẨN AIDA & DIEGETIC AUDIO): {str(asc.get('title')).upper()}**")
        st.markdown(f"<div class='detail-header-box'>⏱ Thời lượng: <b>{asc.get('total_dur')}</b> | 🎙 Giọng: <b>{vp.get('gender', 'Nữ')} ({vp.get('tone', '')})</b> | 👔 Bối cảnh chung: <b>{asc.get('outfit_vi')}</b></div>", unsafe_allow_html=True)
        
        scenes = asc.get("scenes", [])
        if isinstance(scenes, dict): scenes = [scenes]
        for idx, scn in enumerate(scenes, 1):
            aida_badge = f"<span style='background:#dbeafe; color:#1e40af; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:12px; margin-left:8px;'>{scn.get('aida_stage', 'AIDA')}</span>"
            st.markdown(f"#### 📍 Phân cảnh {idx} ({scn.get('dur', '8s')}) {aida_badge} — [ {scn.get('trans', 'Chuyển cảnh')} ]", unsafe_allow_html=True)
            st.markdown(f"🏛 **Bối cảnh & Miêu tả:** *{scn.get('setting')}*\n\n**🎙 Đạo diễn & SFX Thực Tế:** *{scn.get('director')}*\n\n**💬 Thoại (Số từ thực tế: {scn.get('word_count', 'Không đếm')}):** <span class='voiceover-text'>{scn.get('voiceover')}</span>", unsafe_allow_html=True)
            
            img_p, vid_p = scn.get('img_p', ''), scn.get('vid_p', '')
            if "nối tiếp" in scn.get('trans', '').lower() or "dùng lại" in img_p.lower():
                st.info("🔗 **Cảnh nối tiếp:** Dùng khung hình cuối của cảnh trước làm ảnh tham chiếu Video-to-Video.")
            else:
                if img_p: st.markdown("**🖼 Prompt Ảnh:**"); st.code(img_p, language="text"); safe_copy_button(img_p, f"📋 Sao Chép Ảnh Cảnh {idx}")
            if vid_p: st.markdown("**🎥 Prompt Video (Chứa Lệnh Layered SFX):**"); st.code(vid_p, language="text"); safe_copy_button(vid_p, f"📋 Sao Chép Video Cảnh {idx}")
            st.markdown("---")

    st.markdown("### 🎬 **1. Kịch Bản Đã Hoàn Thiện Chi Tiết**")
    if not comp_sc: st.info("💡 Chưa có kịch bản chi tiết.")
    else:
        for outline in comp_sc:
            sc_id = outline["id"]
            with st.container(border=True):
                c1, c2, c3 = st.columns([2.5, 1, 1])
                c1.markdown(f"**#{sc_id}. {outline.get('title')}**{' <span class=badge-ready>ĐANG XEM</span>' if sc_id == st.session_state.active_script_id else ''}", unsafe_allow_html=True)
                c1.caption(f"⚡ *{outline.get('hook', 'Kịch bản review trọng tâm')}*")
                if sc_id != st.session_state.active_script_id:
                    if c2.button("👁 Xem lại", key=f"r_{sc_id}", use_container_width=True): st.session_state.active_script_id = sc_id; st.session_state.scroll_to_detail = True; st.rerun()
                
                ck = f"load_clone_{sc_id}"
                btn_clone_ph = c3.empty()
                if st.session_state.get(ck, False):
                    btn_clone_ph.empty()
                    st.markdown("<div style='background: #fef2f2; color: #dc2626; border-radius: 6px; padding: 6px; text-align: center; font-size: 13px; font-weight: bold;'>⏳ Đang nhân bản...</div>", unsafe_allow_html=True)
                    lock_ui()
                    try: 
                        st.session_state.cloned_scripts.extend(clone_script(sc_id))
                        st.toast("✅ Đã clone!")
                    except Exception as e: 
                        st.error(f"❌ Lỗi: {e}")
                    finally:
                        st.session_state[ck] = False
                        st.rerun()
                else:
                    if btn_clone_ph.button("🚀 Nhân bản", key=f"c_{sc_id}", type="primary", use_container_width=True):
                        can_run, msg = check_usage_limit(st.session_state.current_email)
                        if can_run: 
                            st.session_state[ck] = True
                            st.rerun()
                        else: 
                            st.error(msg)

    st.markdown("<br>### ⏳ **2. Kịch Bản Đang Chờ Dựng**", unsafe_allow_html=True)
    if not pend_sc: st.success("🎉 Đã hoàn thiện toàn bộ danh sách.")
    else:
        for outline in pend_sc:
            sc_id = outline["id"]
            with st.container(border=True):
                c1, c2 = st.columns([3, 1.2])
                c1.markdown(f"**#{sc_id}. {outline.get('title')}** <span class=badge-pending>CHỜ DỰNG</span>", unsafe_allow_html=True)
                c1.caption(f"⚡ *{outline.get('hook', 'Nội dung cốt lõi')}*")
                
                ck = f"load_cre_{sc_id}"
                btn_cre_ph = c2.empty()
                if st.session_state.get(ck, False):
                    btn_cre_ph.empty()
                    st.markdown("<div style='background: #fffbeb; color: #d97706; border-radius: 6px; padding: 6px; text-align: center; font-size: 13px; font-weight: bold;'>⏳ Đang dựng...</div>", unsafe_allow_html=True)
                    lock_ui()
                    try:
                        create_scene_details(sc_id, st.session_state.last_mode, st.session_state.last_style)
                        st.session_state.active_script_id = sc_id
                        st.session_state.scroll_to_detail = True
                        st.toast("✅ Hoàn tất dựng!")
                    except Exception as e: 
                        st.error(f"❌ Lỗi: {e}")
                    finally:
                        st.session_state[ck] = False
                        time.sleep(0.5)
                        st.rerun()
                else:
                    if btn_cre_ph.button("✨ Tạo chi tiết ngay", key=f"cr_{sc_id}", type="secondary", use_container_width=True):
                        can_run, msg = check_usage_limit(st.session_state.current_email, is_detailing=True)
                        if can_run: 
                            st.session_state[ck] = True
                            st.rerun()
                        else: 
                            st.error(msg)

    st.markdown("--- \n##### ➕ **Gọi Thêm 5 Kịch Bản Mới**")
    cg1, cg2, cg3, cg4 = st.columns([1.5, 0.8, 1.2, 1.5])
    a_opts = ["🌟 Tự động mix", "🧠 Chuyên gia", "💡 Mẹo hay", "🎭 Drama", "📖 Storytelling", "😂 Hài hước"] if is_viral_mode else ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Chia sẻ", "😂 Hài hước (Chốt sale)"]
    c_ang = cg1.selectbox("🧭 Chiến lược:", a_opts, key=f"ea_{st.session_state.reset_key}")
    c_num = cg2.number_input("Số diễn viên:", 1, 8, 1, key=f"en_{st.session_state.reset_key}")
    c_dur_choice = cg3.selectbox("⏳ Thời lượng:", ["Tự động (~20-30s)", "Tùy chỉnh (s)"], key=f"ed_{st.session_state.reset_key}")
    c_dur_str = f"Chính xác {cg3.number_input('Số giây:', 10, 300, 60, key=f'eds_{st.session_state.reset_key}')} giây." if "Tùy" in c_dur_choice else "Khoảng 15-30 giây."
    c_nar = cg4.selectbox("🎙 Thuyết minh:", ["Nhân vật xuất hiện (On-camera)", "🎙 Lồng tiếng ngoài (Off-screen)"], key=f"ena_{st.session_state.reset_key}")

    e_chars = []
    if c_num > 0:
        for i in range(c_num):
            c_r, c_i = st.columns([2, 1])
            e_role = c_r.text_input(f"Vai trò NV {i+1} mới:", key=f"er_{i}_{st.session_state.reset_key}")
            e_file = c_i.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"ef_{i}_{st.session_state.reset_key}", label_visibility="collapsed")
            if e_file: e_chars.append({"id": i+1, "role": e_role or "AI tự phân", "file": e_file})

    btn_more_ph = st.columns([1, 2, 1])[1].empty()
    if st.session_state.get("load_more", False):
        btn_more_ph.empty()
        st.markdown("<div style='background: #fff0f2; border: 1.5px solid #ffa4b4; padding: 12px; border-radius: 8px; color: #d90429; text-align: center; font-weight: bold;'>⏳ Đang sáng tạo thêm 5 kịch bản theo mô hình AIDA...</div>", unsafe_allow_html=True)
        lock_ui()
        try:
            p_chars = [{"id": c["id"], "role": c["role"]} for c in e_chars] if e_chars else st.session_state.character_profiles
            new_sc = generate_more_scripts(c_ang, c_num, e_chars, c_nar, c_dur_str, p_chars)
            st.session_state.expanded_scripts.extend(new_sc)
            st.session_state.scroll_to_top = True
            st.toast("✅ Đã sinh thêm 5 kịch bản!")
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
        finally:
            st.session_state.load_more = False
            time.sleep(0.5)
            st.rerun()
    else:
        if btn_more_ph.button("🚀 Gọi Thêm 5 Kịch Bản Mới", type="primary", use_container_width=True):
            can_run, msg = check_usage_limit(st.session_state.current_email)
            if can_run:
                st.session_state.load_more = True
                st.rerun()
            else:
                st.error(msg)
