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
    
    /* KHỐI HỖ TRỢ */
    .support-box { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1.5px solid #86efac; border-radius: 14px; padding: 14px 12px; text-align: center; margin-top: 15px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
    .hotline-tag { font-size: 14.5px; font-weight: 800; color: #166534; margin-bottom: 8px; }
    .hotline-tag a { color: #dc2626 !important; text-decoration: none; font-size: 16px; font-weight: 900; }
    .btn-zalo { background: linear-gradient(135deg, #0068FF 0%, #004ecc 100%); color: white !important; font-weight: 800; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-size: 14px; box-shadow: 0 2px 6px rgba(0,104,255,0.3); display: inline-flex; align-items: center; justify-content: center; min-width: 65px; }
    .btn-fb { background: linear-gradient(135deg, #1877F2 0%, #0d65d9 100%); color: white !important; font-weight: 800; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 15px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; box-shadow: 0 2px 6px rgba(24,119,242,0.3); display: inline-flex; align-items: center; justify-content: center; min-width: 65px; }
    .btn-tt { background: linear-gradient(135deg, #111111 0%, #000000 100%); color: white !important; font-weight: 800; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-size: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.3); border: 1px solid #333; display: inline-flex; align-items: center; justify-content: center; min-width: 65px; }
    .social-icons-container { display: flex; gap: 8px; justify-content: center; margin-top: 8px; }

    /* DETAIL HEADER BOX CHUYÊN NGHIỆP */
    .detail-header-box { background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%); border: 1.5px solid #bfdbfe; border-radius: 12px; padding: 16px 20px; margin-bottom: 22px; color: #1e3a8a; line-height: 1.8; box-shadow: 0 3px 10px rgba(0,0,0,0.03); }
    .voiceover-text { color: #15803d; background: #f0fdf4; padding: 10px 14px; border-radius: 8px; font-size: 15.5px; border: 1px solid #bbf7d0; display: inline-block; width: 100%; margin-top: 4px; line-height: 1.7; }
    .scrollable-sidebar-container { max-height: 380px; overflow-y: auto; padding-right: 5px; margin-bottom: 10px; }
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
    if not text: return 0
    return len(re.findall(r'\b\w+\b', text))

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
        return False, "Tài khoản của bạn đã hết hạn. Vui lòng liên hệ Hotline/Zalo 0869 628 316 để gia hạn!"
    plan = acc.get("plan_type", "Trial")
    if plan == "VIP": return True, ""
    limit = {"Advanced": 20, "Basic": 10, "Trial": 3}.get(plan, 3)
    today = datetime.now().strftime("%Y-%m-%d")
    if acc.get("last_generation_date") != today:
        acc["daily_usage_count"] = 0
        acc["last_generation_date"] = today
    if is_detailing:
        if acc.get("daily_usage_count", 0) >= limit: return False, f"Hết lượt tạo chi tiết kịch bản ({limit}/{limit}) hôm nay! Vui lòng nâng cấp gói."
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

# Khởi tạo state
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

# Khóa thiết bị đồng thời
if st.session_state.is_logged_in and st.session_state.current_email != ADMIN_EMAIL:
    current_acc_lock = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
    if current_acc_lock.get("active_session_id") != st.session_state.session_id:
        st.error("🚨 TÀI KHOẢN ĐANG ĐĂNG NHẬP Ở THIẾT BỊ KHÁC. Mỗi tài khoản chỉ dùng trên 1 thiết bị duy nhất.")
        if st.button("🔌 Sử dụng trên thiết bị này (Đăng xuất thiết bị kia)", type="primary"):
            st.session_state.licensed_accounts[st.session_state.current_email]["active_session_id"] = st.session_state.session_id
            save_single_account(st.session_state.current_email, st.session_state.licensed_accounts[st.session_state.current_email])
            st.rerun()
        st.stop()

# Xử lý cuộn trang mượt mà
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

# ==============================================================================
# 2. HÀM AI LÕI & LUẬT THÉP V78.0 (KHÓA CHẶT HOOK GỐC & FULL HEADER BOX)
# ==============================================================================
def repair_and_parse_json(text_content: str):
    cleaned = re.sub(r'```(?:json)?', '', text_content).strip()
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    candidate = match.group(0) if match else cleaned

    def try_parse(s):
        try:
            p = json.loads(s, strict=False)
            return p[0] if isinstance(p, list) and len(p) > 0 else p
        except Exception:
            return None

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

def generate_char_rules_string(profiles):
    if not profiles: return "KOC_IDENTITY: KOC người Việt tự nhiên, duyên dáng. KHÓA DUY NHẤT 1 kiểu tóc (búi cao hoặc xõa) cố định cho tất cả các cảnh."
    rules = "KOC_IDENTITY:\n"
    for p in profiles: rules += f" - Diễn viên {p['id']} ({p['role']}): Trích xuất mặt người Việt. Khóa 1 kiểu tóc duy nhất cố định xuyên suốt.\n"
    return rules

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, angle):
    strat_cmd = "BẠN PHẢI MIX ĐA DẠNG 5 GÓC ĐỘ NỘI DUNG." if "Tự động mix" in angle else f"VIẾT CẢ 5 KỊCH BẢN THEO: '{angle}'."
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL TIKTOK SHOP VIỆT NAM. PHONG CÁCH: {style}
    {strat_cmd}
    
    🛑 BỘ LỌC CHÍNH SÁCH BÁN HÀNG VIỆT NAM (TUÂN THỦ 100%):
    1. CẤM TỪ CAM KẾT VÀ TỪ CẤM: 'tuyệt đối', 'hoàn toàn', '100%', 'chắc chắn', 'cam kết', 'dứt điểm', 'đặc trị', 'khỏi hẳn', 'chuẩn đét', 'giảm cân giữ dáng'.
       - Dùng từ ngữ tự nhiên, đời thường: 'hỗ trợ', 'cải thiện', 'nhẹ bụng hơn', 'tiện ích', 'đáng thử', 'ưng ý'.
    2. AN TOÀN TRẺ EM: Nếu là sản phẩm Mẹ & Bé, luôn có mẹ bế hoặc kề bên chăm sóc, TUYỆT ĐỐI CẤM để bé một mình trong phòng/trên giường.
    3. ƯU TIÊN MÃ BÁN CHẠY (HERO SKU): Soi kỹ ảnh tham chiếu (ví dụ họa tiết da báo hoặc thỏ hoa có nhãn Đã bán 1K+) để làm sản phẩm chủ đạo.
    4. BỐI CẢNH NATIVE: Ga gối đệm trên giường phòng ngủ; đồ bếp ở bàn bếp; xả kho ở kho hàng.
    5. ĐÒN BẨY GIÁ TƯƠNG PHẢN: Neo giá gốc làm tròn (gần... nghìn), khẳng định giảm sâu, giấu giá sale, miễn trừ thời gian.
    6. PERSONA HÀ NỘI CHUẨN: Dứt khoát (nhé, này, thế, dùng, không). CẤM từ miền Nam: nha, nè, vô, xài.
    7. {char_rules}
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction):
    is_on_camera = "On-camera" in narrator_mode
    audio_cmd = "Chèn `Audio:` vào `vid_p`." if is_on_camera else "Không chèn thoại vào `vid_p`."
    voice_hint = "Giọng [Nam/Nữ] HÀ NỘI GỐC ĐẦY NỘI LỰC, ĐANH THÉP, TRUYỀN CẢM, BẮT ĐẦU THOẠI NGAY TẠI 0.00S, TỐC ĐỘ ĐỀU METRONOME (4.3 - 4.5 từ/s)."

    return f"""
    BẠN LÀ BẬC THẦY KỊCH BẢN VIRTUAL VIDEO TIKTOK SHOP TẠI VIỆT NAM. PHONG CÁCH: {style}
    
    🛑 QUY TẮC CỐT LÕI: KHÓA CHẶT TIÊU ĐỀ & CÂU HOOK GỐC, KHÔNG ĐƯỢC TỰ BỊA NỘI DUNG MỚI:
    1. BẮT BUỘC BÁM SÁT TIÊU ĐỀ VÀ HOOK ĐƯỢC GIAO:
       - TIÊU ĐỀ: Giữ nguyên 100% tiêu đề kịch bản được truyền vào trong prompt, TUYỆT ĐỐI KHÔNG ĐỔI TÊN KỊCH BẢN.
       - CẢNH 1 (ATTENTION): Lời thoại BẮT BUỘC phải lấy trực tiếp câu Hook gốc đã có trong danh sách làm nòng cốt! Bạn chỉ được phép trau chuốt, thêm thắt từ ngữ xưng hô dẫn dắt để câu thoại đạt đủ độ dài 22 - 25 từ. TUYỆT ĐỐI CẤM đổi sang một ý tưởng hay câu hook hoàn toàn khác!
    
    2. CẢ 4 PHÂN CẢNH GHÉP LẠI PHẢI THÀNH 1 ĐOẠN VĂN KỂ CHUYỆN CÓ HỒN, LOGIC CHẶT CHẼ:
       - CẤM VIẾT CÂU THOẠI CỘT LỐC, RỜI RẠC.
       - Dẫn dắt liền mạch: Cảnh 1 (Attention - 6s, 22-25 từ) -> Cảnh 2 (Interest - 8s, 30-34 từ) -> Cảnh 3 (Desire - 10s, 38-42 từ) -> Cảnh 4 (Action - 6s/8s, 24-28 từ).
    
    3. TRIỆT TIÊU TOÀN BỘ ICON GIỎ HÀNG, NÚT BẤM & SUB NỔI:
       - Scene 4 chỉ mở lòng bàn tay hướng nhẹ xuống ("Character gestures warmly downward with an open hand").
       - Cuối mọi img_p & vid_p: "Strictly pure live-action footage: NO yellow shopping cart icons, NO floating buttons, NO simulated UI, NO overlays, NO text, NO subtitles. Clean frame."

    4. KHÓA 100% MẪU MÃ TỪ ẢNH GỐC & KHÓA 1 KIỂU TÓC DUY NHẤT:
       - `prod_dna` mô tả chính xác mẫu mã ảnh tham chiếu (VD: da báo nâu đen chuẩn ảnh). Cấm đổi mẫu giữa các cảnh.
       - Khóa DUY NHẤT một kiểu tóc trong `global_identity_en` và 1 bộ trang phục `global_outfit_en`.
       - Cảnh 1 quay cận cảnh THỰC TRẠNG NỖI ĐAU khớp trực tiếp với câu Hook gốc.
    
    5. ÂM THANH THỰC TẾ (Layered SFX): Tiếng dầu sôi xèo xèo, phun sương xì xì, cắn giòn rụm, sột soạt vải mềm.
    6. {audio_cmd}
    7. {char_rules}
    """

def create_scene_details(target_id, mode, style):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if sc["id"] == target_id), None)
    if not outline: return
    
    narrator_mode = outline.get("narrator_mode", st.session_state.get("last_narrator", "On-camera"))
    char_profiles = outline.get("character_profiles", st.session_state.get("character_profiles", []))
    char_rules = generate_char_rules_string(char_profiles)
    
    is_on_camera = "On-camera" in narrator_mode
    prod_data_ctx = json.dumps(st.session_state.get('current_product_data_saved'), ensure_ascii=False)
    dna_data_ctx = json.dumps(st.session_state.get('content_analysis'), ensure_ascii=False)
    
    audio_instruction = 'Chèn: Audio: "[CHÉP ĐỦ 100% VOICEOVER]", Layered SFX: [MÔ TẢ SFX THỰC TẾ]' if is_on_camera else 'Chỉ chèn Layered SFX thực tế, không chèn thoại.'
    voice_hint = "Giọng [Nam/Nữ] HÀ NỘI CHUẨN 100%, ĐẦY NỘI LỰC, ĐANH THÉP, TRUYỀN CẢM, THOẠI NGAY 0.00S, NHỊP ĐỘ ĐỀU METRONOME (4.3 - 4.5 từ/s)."

    fixed_title = outline.get('title', 'Kịch bản chi tiết')
    fixed_hook = outline.get('hook', '')

    prompt_text = f"""
    DỮ LIỆU ĐẦU VÀO: {prod_data_ctx} | DNA: {dna_data_ctx}
    THÔNG TIN KỊCH BẢN ĐÃ CHỌN:
    - ID: #{target_id}
    - TIÊU ĐỀ BẮT BUỘC GIỮ NGUYÊN: '{fixed_title}'
    - CÂU HOOK GỐC BẮT BUỘC DÙNG CHO CẢNH 1: '{fixed_hook}'
    - Bối cảnh chỉ đạo: {outline.get('setting', 'Phòng ngủ')}
    THUYẾT MINH: {audio_instruction} | LOẠI: {mode}
    
    🛑 LỆNH CƯỠNG CHẾ TUYỆT ĐỐI (KHÔNG ĐƯỢC PHÉP SAI LỆCH):
    1. TIÊU ĐỀ: Trường "title" trong JSON BẮT BUỘC ĐIỀN ĐÚNG NGUYÊN VĂN: '{fixed_title}'. CẤM TỰ NGHĨ RA TÊN MỚI!
    2. CẢNH 1 (ATTENTION): Lời thoại 'voiceover' BẮT BUỘC PHẢI DỰA TRÊN CÂU HOOK GỐC: '{fixed_hook}'. Hãy mở rộng và trau chuốt câu này để đạt đủ từ 22 đến 25 từ tự nhiên, đúng giọng Hà Nội. CẤM BỎ CÂU HOOK NÀY ĐI ĐỂ TỰ BỊA CÂU KHÁC!
    3. CẢNH 2 (Interest - 30-34 từ), CẢNH 3 (Desire - 38-42 từ), CẢNH 4 (Action - 24-28 từ): Viết tiếp nối mạch truyện liền mạch từ Cảnh 1, ghép lại thành một bài nói chuyện hoàn chỉnh, có nghĩa.
    4. KHUNG HEADER ĐẦY ĐỦ: Trường "director_summary" phải chứa phân tích chi tiết đầy đủ (Thời lượng, giọng đọc, góc máy, đồng nhất kiểu tóc và bối cảnh).
    5. CẤM ICON GIỎ HÀNG: Scene 4 chỉ mở lòng bàn tay hướng nhẹ xuống. Cuối img_p & vid_p cấm icons, text, subs.
    6. ĐỐI CHIẾU ẢNH GỐC: prod_dna khớp 100% mẫu mã/họa tiết ảnh tham chiếu. Khóa 1 kiểu tóc duy nhất trong global_identity_en.
    
    TRẢ VỀ JSON:
    {{
        "title": "{fixed_title}",
        "total_dur": "Khoảng 30 giây",
        "voice": {{"gender": "Nam/Nữ", "tone": "{voice_hint}"}},
        "outfit_vi": "Trang phục cụ thể và kiểu tóc duy nhất được khóa cố định suốt 4 cảnh",
        "director_summary": "⏱ <b>Thời lượng:</b> Khoảng 30 giây (Chuẩn 4 phân cảnh AIDA) | 🎙 <b>Giọng đọc:</b> [Nam/Nữ] HÀ NỘI GỐC ĐẦY NỘI LỰC, ĐANH THÉP, TRUYỀN CẢM (4.3-4.5 từ/s)<br>👔 <b>Đồng nhất nhân vật & kiểu tóc:</b> [Mô tả trang phục và 1 kiểu tóc duy nhất]<br>🎯 <b>Sản phẩm Hero SKU:</b> [Mô tả mẫu mã chuẩn từ ảnh tham chiếu]",
        "global_identity_en": "Vietnamese KOC, pleasant natural face, EXACT LOCKED HAIRSTYLE (choose strictly ONE: neatly tied high bun OR straight loose hair), Body.",
        "global_outfit_en": "Exact locked outfit description, invariant across all scenes.",
        "global_setting_en": "Exact native room setting, invariant across all scenes.",
        "prod_dna": "Photorealistic description matching the exact reference image product, including exact pattern and colors, locked across all scenes.",
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention", "dur": "6s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh cảnh 1 trực quan hóa đúng thực trạng nỗi đau của câu hook...",
                "action_en": "Realistic shot demonstrating the exact pain point mentioned in hook. Character with locked hairstyle and outfit. Speaking naturally starting immediately at 0.00s.",
                "director": "Attention | Trực quan hóa nỗi đau | SFX thực tế | Khởi động: 0.00s | Tông đanh thép",
                "voiceover": "Mở rộng từ câu hook gốc '{fixed_hook}' đạt độ dài từ 22 đến 25 từ, nói ngay 0.00s...",
                "img_p": "Vertical 9:16 photo. Cinematic eye-level shot. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Product: [prod_dna]. Strictly pure camera footage: NO yellow shopping cart icons, NO floating buttons, NO text, NO subtitles, NO UI overlays. Clean pristine frame.",
                "vid_p": "Vertical 9:16 video. Eye-level shot. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ 100% VOICEOVER CẢNH 1]\\", Layered SFX: [tiếng động thực tế]. Product: [prod_dna]. Stable geometry, persistent pattern. Strictly pure live-action footage: NO yellow shopping cart icons, NO floating animated buttons, NO simulated UI, NO overlays, NO text, NO subtitles. 100% clean pristine cinematic frame."
            }},
            {{
                "scene": 2, "aida_stage": "Interest", "dur": "8s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh giải pháp xuất hiện...",
                "action_en": "Practical demonstration action smoothly transitioning from scene 1. Same locked hairstyle and outfit. Interacting naturally with product.",
                "director": "Interest | Thao tác thực tế | SFX | Khởi động: 0.00s | Tông tự nhiên",
                "voiceover": "Thoại nối tiếp liền mạch dài từ 30 đến 34 từ, giải thích giải pháp chân thật...",
                "img_p": "Vertical 9:16 photo. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Strictly pure camera footage: NO icons, NO text, NO subtitles, NO UI. Clean frame.",
                "vid_p": "Vertical 9:16 video. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ 100% VOICEOVER CẢNH 2]\\", Layered SFX: [tiếng phun sương/thao tác]. Product: [prod_dna]. Strictly pure live-action footage: NO icons, NO UI overlays, NO text, NO subtitles. Clean frame."
            }},
            {{
                "scene": 3, "aida_stage": "Desire", "dur": "10s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh trải nghiệm vượt trội...",
                "action_en": "Sensory experience action showing practical benefits and multiple varieties. Same locked hairstyle.",
                "director": "Desire | Trải nghiệm & Bảng màu | SFX | Khởi động: 0.00s | Tông nội lực",
                "voiceover": "Thoại sâu sắc dài từ 38 đến 42 từ, nêu bật điểm độc bản và nhắc bảng màu đa dạng...",
                "img_p": "Vertical 9:16 photo. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Clean frame.",
                "vid_p": "Vertical 9:16 video. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ 100% VOICEOVER CẢNH 3]\\", Layered SFX: [tiếng động thực tế]. Product: [prod_dna]. Strictly pure live-action footage: NO icons, NO UI overlays, NO text, NO subtitles. Clean frame."
            }},
            {{
                "scene": 4, "aida_stage": "Action", "dur": "6s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh chốt deal...",
                "action_en": "Warm confident closing gesture: Character gestures warmly and naturally downward with an open hand, maintaining friendly eye contact. Same locked hairstyle and outfit.",
                "director": "Action | Đòn bẩy giá | SFX | Khởi động: 0.00s | Tông chốt deal",
                "voiceover": "Thoại chốt deal tự nhiên dài từ 24 đến 28 từ theo đòn bẩy giá tương phản...",
                "img_p": "Vertical 9:16 photo. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Clean frame.",
                "vid_p": "Vertical 9:16 video. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ 100% VOICEOVER CẢNH 4]\\", Layered SFX: [tiếng động nhẹ]. Product: [prod_dna]. Strictly pure live-action footage: NO yellow shopping cart icons, NO floating buttons, NO UI overlays, NO text, NO subtitles. Clean frame."
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

    res = call_gemini(payload, get_sys_inst_details(mode, style, narrator_mode, char_rules, "Khoảng 30 giây"), max_tokens=7000)
    if not res or "scenes" not in res: raise Exception("AI JSON Error.")
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
    Sinh 5 kịch bản mới chuẩn AIDA theo chiến lược: '{angle}'. Diễn viên: {num_chars}.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên kịch bản mới", "setting": "Bối cảnh...", "hook": "Câu hook 3s đầu ngắn gọn ấn tượng...", "actors": {num_chars} }}
        ]
    }}
    BẮT BUỘC ĐỦ 5 KỊCH BẢN.
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, narrator_mode_more, char_rules, num_chars, angle), max_tokens=3000)
    more_scripts = res.get("outlines", res.get("script_outlines", []))
    for idx, sc in enumerate(more_scripts): 
        sc.update({"id": cur_len + idx + 1, "duration_instruction": duration_inst, "narrator_mode": narrator_mode_more, "character_profiles": char_profiles})
    return more_scripts

def clone_script(script_id):
    mode = st.session_state.get("last_mode", "Bán Hàng")
    style = st.session_state.get("last_style", "Điện ảnh")
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if sc["id"] == script_id), None)
    cur_len = len(all_combined)
    num_chars = target.get("actors", target.get("actor_count", 1))
    
    prompt = f"Nhân bản kịch bản #{script_id}: {json.dumps(target, ensure_ascii=False)} thành 5 biến thể AIDA mới tuân thủ chính sách."
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, target.get("narrator_mode", ""), "", num_chars, "Gốc"), max_tokens=3000)
    clones = res.get("outlines", res.get("script_outlines", []))
    for idx, cl in enumerate(clones): 
        cl.update({"id": cur_len + idx + 1, "duration_instruction": target.get("duration_instruction", ""), "narrator_mode": target.get("narrator_mode", ""), "character_profiles": target.get("character_profiles", [])})
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

# ==============================================================================
# 3. THANH BÊN (SIDEBAR) & QUẢN TRỊ ADMIN (CÓ CHỈNH SỬA & GIA HẠN TÀI KHOẢN)
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
                            st.error("❌ Mật khẩu không chính xác! Hãy nhập lại.")
                    else:
                        st.error("❌ Email chưa được cấp quyền sử dụng!")
                        
        with tabs[1]:
            with st.form("register_form", border=False):
                r_email = st.text_input("Email đăng ký:", key="f_reg_email", autocomplete="new-password")
                r_phone = st.text_input("Số điện thoại:", key="f_reg_phone", autocomplete="new-password")
                r_pass = st.text_input("Mật khẩu mới:", type="password", key="f_reg_pass", autocomplete="new-password")
                submit_reg = st.form_submit_button("🚀 Đăng Ký", type="secondary", use_container_width=True)
                
                if submit_reg:
                    email_r, phone_r, pass_r = r_email.strip(), r_phone.strip(), r_pass.strip()
                    if not email_r or not phone_r or not pass_r:
                        st.error("⚠️ Vui lòng điền đủ tất cả các trường!")
                    elif not is_valid_phone(phone_r):
                        st.error("⚠️ Số điện thoại không hợp lệ (9-11 số, bắt đầu bằng 0)!")
                    elif email_r in st.session_state.licensed_accounts:
                        st.error("⚠️ Email này đã tồn tại trên hệ thống!")
                    else:
                        exp = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[email_r] = {
                            "roles": ALL_MODULES, "phone": phone_r, "password": pass_r,
                            "expires_at": exp, "plan_type": "Trial", "daily_usage_count": 0,
                            "last_generation_date": "", "active_session_id": st.session_state.session_id
                        }
                        save_single_account(email_r, st.session_state.licensed_accounts[email_r])
                        st.session_state.is_logged_in = True
                        st.session_state.current_email = email_r
                        st.toast("✅ Đăng ký thành công! Nhận 3 lượt dùng thử/ngày.")
                        time.sleep(0.4)
                        st.rerun()
    else:
        # KHỐI 1: LÀM VIỆC DỰ ÁN
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
        
        # KHỐI 2: KHO DỰ ÁN (HIỂN THỊ 3 DỰ ÁN + TÌM KIẾM)
        st.markdown("### 📂 KHO DỰ ÁN")
        if supabase:
            try:
                res = supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
                all_projects = res.data or []
            except: all_projects = []

            search_proj = st.text_input("🔍 Tìm kiếm dự án:", placeholder="Nhập tên dự án...", key="search_proj_input")
            if search_proj.strip():
                display_projects = [p for p in all_projects if search_proj.strip().lower() in p['project_title'].lower()]
            else:
                display_projects = all_projects if st.session_state.show_all_projects else all_projects[:3]

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

        # KHỐI 3: QUẢN TRỊ ADMIN (CÓ CHỨC NĂNG SỬA HẠN & GIA HẠN TÀI KHOẢN)
        if st.session_state.current_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙ QUẢN TRỊ ADMIN")
            
            with st.expander("➕ Cấp Quyền Tài Khoản Mới", expanded=False):
                adm_acc = st.text_input("Email:", autocomplete="new-password", key="adm_in_acc")
                adm_phone = st.text_input("SĐT:", autocomplete="new-password", key="adm_in_phone")
                adm_pass = st.text_input("Mật khẩu:", value="123456", autocomplete="new-password", key="adm_in_pass")
                adm_plan = st.radio("Gói cước:", ["Trial (3 kịch bản)", "Basic (10 kịch bản)", "Advanced (20 kịch bản)", "VIP (không giới hạn)"], horizontal=True, key="adm_in_plan")
                
                dur_options = [
                    "3 Ngày", "7 Ngày", "1 Tháng", "3 Tháng", "6 Tháng", 
                    "1 Năm", "2 Năm", "Vĩnh viễn", 
                    "Tùy chỉnh (Số ngày)", "Tùy chỉnh (Chọn ngày)"
                ]
                adm_dur = st.selectbox("Thời hạn:", dur_options, key="adm_in_dur")
                
                calculated_exp_str = "2099-12-31"
                if adm_dur == "Tùy chỉnh (Số ngày)":
                    custom_num_days = st.number_input("👉 Nhập số ngày sử dụng:", min_value=1, max_value=3650, value=30, step=1, key="custom_num_days_input")
                    calculated_exp_str = (datetime.now() + timedelta(days=int(custom_num_days))).strftime("%Y-%m-%d")
                    st.caption(f"📅 Dự tính hết hạn ngày: **{calculated_exp_str}**")
                elif adm_dur == "Tùy chỉnh (Chọn ngày)":
                    custom_chosen_date = st.date_input("👉 Chọn ngày hết hạn cụ thể trên lịch:", value=date.today() + timedelta(days=30), min_value=date.today(), key="custom_date_input")
                    calculated_exp_str = custom_chosen_date.strftime("%Y-%m-%d")
                    st.caption(f"📅 Hết hạn vào ngày: **{calculated_exp_str}**")
                elif adm_dur == "Vĩnh viễn":
                    calculated_exp_str = "2099-12-31"
                    st.caption("📅 Thời hạn vĩnh viễn (2099-12-31)")
                else:
                    dur_days_map = {
                        "3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30, 
                        "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730
                    }
                    calculated_exp_str = (datetime.now() + timedelta(days=dur_days_map.get(adm_dur, 30))).strftime("%Y-%m-%d")
                    st.caption(f"📅 Hết hạn vào ngày: **{calculated_exp_str}**")

                if st.button("💾 Cấp Quyền Tài Khoản", type="primary", use_container_width=True, key="btn_submit_grant_admin"):
                    if adm_acc.strip() and adm_phone.strip() and adm_pass.strip():
                        st.session_state.licensed_accounts[adm_acc.strip()] = {
                            "roles": ALL_MODULES, "phone": adm_phone.strip(), "password": adm_pass.strip(),
                            "expires_at": calculated_exp_str, "plan_type": adm_plan, "daily_usage_count": 0,
                            "last_generation_date": "", "active_session_id": ""
                        }
                        save_single_account(adm_acc.strip(), st.session_state.licensed_accounts[adm_acc.strip()])
                        st.toast(f"✅ Đã cấp quyền thành công đến {calculated_exp_str}!")
                        time.sleep(0.4)
                        st.rerun()
                    else:
                        st.error("⚠️ Vui lòng nhập đầy đủ Email, SĐT và Mật khẩu!")

            st.markdown("##### 👥 Danh Sách Tài Khoản & Gia Hạn")
            search_acc = st.text_input("🔍 Tìm tài khoản (Email/SĐT):", placeholder="Nhập email hoặc SĐT...", key="search_acc_input")
            other_accs = [item for item in st.session_state.licensed_accounts.items() if item[0] != ADMIN_EMAIL]
            
            if search_acc.strip():
                filt_accs = [item for item in other_accs if search_acc.strip().lower() in item[0].lower() or search_acc.strip() in item[1].get('phone', '')]
            else:
                filt_accs = other_accs if st.session_state.show_all_admin_accounts else other_accs[:3]

            for acc_mail, info in filt_accs:
                with st.expander(f"👤 {acc_mail} ({info.get('plan_type')})"):
                    st.write(f"📞 **SĐT:** `{info.get('phone', 'N/A')}`")
                    st.write(f"⏳ **Hạn hiện tại:** `{info.get('expires_at')}`")
                    
                    st.markdown("---")
                    st.markdown("**⚙ Chỉnh sửa / Gia hạn:**")
                    
                    # 1. Chọn đổi gói cước
                    cur_plan = info.get("plan_type", "Trial")
                    plan_idx = ["Trial (3 kịch bản)", "Basic (10 kịch bản)", "Advanced (20 kịch bản)", "VIP (không giới hạn)"].index(cur_plan) if cur_plan in ["Trial", "Basic", "Advanced", "VIP"] else 0
                    new_plan = st.selectbox("Đổi gói cước:", ["Trial", "Basic", "Advanced", "VIP"], index=plan_idx, key=f"plan_sel_{acc_mail}")
                    
                    # 2. Chọn mốc thời hạn gia hạn
                    renew_opts = [
                        "Giữ nguyên hạn hiện tại", "3 Ngày", "7 Ngày", "1 Tháng", "3 Tháng", 
                        "6 Tháng", "1 Năm", "2 Năm", "Vĩnh viễn", 
                        "Tùy chỉnh (Số ngày)", "Tùy chỉnh (Chọn ngày)"
                    ]
                    renew_choice = st.selectbox("Gia hạn / Đổi thời hạn:", renew_opts, key=f"renew_opt_{acc_mail}")
                    
                    target_exp_str = info.get("expires_at", "2099-12-31")
                    if renew_choice == "Tùy chỉnh (Số ngày)":
                        r_days = st.number_input("Số ngày gia hạn thêm:", min_value=1, max_value=3650, value=30, key=f"rdays_{acc_mail}")
                        target_exp_str = (datetime.now() + timedelta(days=int(r_days))).strftime("%Y-%m-%d")
                        st.caption(f"📅 Hạn mới: **{target_exp_str}**")
                    elif renew_choice == "Tùy chỉnh (Chọn ngày)":
                        try:
                            cur_d = datetime.strptime(info.get("expires_at", ""), "%Y-%m-%d").date()
                        except:
                            cur_d = date.today() + timedelta(days=30)
                        r_date = st.date_input("Chọn ngày hết hạn mới:", value=cur_d, key=f"rdate_{acc_mail}")
                        target_exp_str = r_date.strftime("%Y-%m-%d")
                        st.caption(f"📅 Hạn mới: **{target_exp_str}**")
                    elif renew_choice == "Vĩnh viễn":
                        target_exp_str = "2099-12-31"
                        st.caption("📅 Hạn mới: **Vĩnh viễn (2099-12-31)**")
                    elif renew_choice != "Giữ nguyên hạn hiện tại":
                        dur_map = {"3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730}
                        target_exp_str = (datetime.now() + timedelta(days=dur_map.get(renew_choice, 30))).strftime("%Y-%m-%d")
                        st.caption(f"📅 Hạn mới: **{target_exp_str}**")

                    c_act1, c_act2 = st.columns(2)
                    if c_act1.button("🔄 Cập Nhật & Gia Hạn", key=f"save_renew_{acc_mail}", use_container_width=True):
                        st.session_state.licensed_accounts[acc_mail]["plan_type"] = new_plan
                        st.session_state.licensed_accounts[acc_mail]["expires_at"] = target_exp_str
                        save_single_account(acc_mail, st.session_state.licensed_accounts[acc_mail])
                        st.toast(f"✅ Đã cập nhật {acc_mail} thành công!")
                        time.sleep(0.4); st.rerun()

                    if c_act2.button("🗑 Xóa tài khoản", key=f"del_acc_{acc_mail}", type="secondary", use_container_width=True):
                        delete_single_account(acc_mail)
                        if acc_mail in st.session_state.licensed_accounts:
                            del st.session_state.licensed_accounts[acc_mail]
                        st.toast(f"✅ Đã xóa {acc_mail}!")
                        time.sleep(0.3); st.rerun()

            if not search_acc.strip() and len(other_accs) > 3:
                if st.session_state.show_all_admin_accounts:
                    if st.button("🔼 Thu gọn danh sách tài khoản", use_container_width=True):
                        st.session_state.show_all_admin_accounts = False
                        st.rerun()
                else:
                    if st.button(f"🔽 Xem thêm {len(other_accs)-3} tài khoản", use_container_width=True):
                        st.session_state.show_all_admin_accounts = True
                        st.rerun()

        st.markdown("---")
        
        # KHỐI 4: HỖ TRỢ (NẰM TRÊN THÔNG TIN TÀI KHOẢN, CÓ HOTLINE BẤM GỌI & ICON MỚI)
        st.markdown("""
        <div class="support-box">
            <div style="font-weight:900; font-size:16px; color:#15803d; margin-bottom:4px;">🎧 HỖ TRỢ</div>
            <div class="hotline-tag">Hotline: <a href="tel:0869628316">0869 628 316</a></div>
            <div class="social-icons-container">
                <a href="[https://zalo.me/0869628316](https://zalo.me/0869628316)" target="_blank" class="btn-zalo">Zalo</a>
                <a href="[https://www.facebook.com/profile.php?id=61594877491617](https://www.facebook.com/profile.php?id=61594877491617)" target="_blank" class="btn-fb">Facebook</a>
                <a href="[https://www.tiktok.com/@binhnguyenai.studio](https://www.tiktok.com/@binhnguyenai.studio)" target="_blank" class="btn-tt">TikTok</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # KHỐI 5: THÔNG TIN TÀI KHOẢN & ĐĂNG XUẤT (NẰM DƯỚI CÙNG BẢO ĐẢM THỨ TỰ)
        u_info = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        u_plan = u_info.get("plan_type", "Trial")
        u_used = u_info.get("daily_usage_count", 0) if u_info.get("last_generation_date") == datetime.now().strftime("%Y-%m-%d") else 0
        u_lim = "Không giới hạn" if u_plan == "VIP" else (20 if u_plan == "Advanced" else (10 if u_plan == "Basic" else 3))
        st.info(f"**GÓI {u_plan.upper()}**\n\n• Email: {st.session_state.current_email}\n• Tạo chi tiết: **{u_used}/{u_lim}**\n• Hạn dùng: {u_info.get('expires_at')}")

        if st.button("🚪 Đăng Xuất"): 
            st.session_state.is_logged_in = False
            st.rerun()

if not st.session_state.is_logged_in: st.info("👈 Vui lòng đăng nhập ở thanh bên."); st.stop()

# ==============================================================================
# 5. KHÔNG GIAN SÁNG TẠO CHÍNH
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div></div>""", unsafe_allow_html=True)
mode = st.selectbox("🎯 Thể loại:", ALL_MODULES, key=f"mode_sel_{st.session_state.reset_key}")
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
num_chars = col_opt2.number_input("👤 Số Diễn viên:", 1, 8, 1)

char_inputs = []
for i in range(num_chars):
    c_r, c_i = st.columns([2, 1])
    role = c_r.text_input(f"Vai trò NV {i+1}:", key=f"r_{i}")
    c_file = c_i.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"f_{i}", label_visibility="collapsed")
    if c_file: char_inputs.append({"id": i+1, "role": role or "AI phân tích", "file": c_file})

if st.button("🚀 PHÂN TÍCH DNA & SINH 5 KỊCH BẢN ĐA VŨ TRỤ", type="primary", use_container_width=True):
    can_run, msg = check_usage_limit(st.session_state.current_email)
    if not can_run: st.error(msg)
    else:
        with st.spinner("⏳ Đạo diễn AI đang quét OCR bảng màu, nhận diện Hero SKU và phân tích DNA..."):
            try:
                st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
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
                BẮT BUỘC TRẢ VỀ JSON:
                {{
                    "content_analysis": {{
                        "target_audience": "Nhận diện TỆP KHÁCH HÀNG MỤC TIÊU",
                        "core_value": "Giá trị cốt lõi giải quyết vấn đề gì",
                        "pain_points": "Nỗi đau / Rào cản lớn nhất của khách hàng (BẮT BUỘC TRỰC QUAN HÓA Ở CẢNH 1)",
                        "hook_element": "Yếu tố giật gân, tạo tò mò hoặc xúc động đánh đúng tâm lý trong 3 giây đầu",
                        "hero_sku_color": "MÃ MÀU BÁN CHẠY NHẤT (HERO SKU): Nhận diện mẫu mã/họa tiết nổi bật nhất trên ảnh tham chiếu (VD: họa tiết da báo hoặc thỏ hoa có nhãn Đã bán 1K+).",
                        "color_palette": "BẢNG MÀU TOÀN BỘ: Liệt kê danh sách tất cả các màu/họa tiết có trong ảnh",
                        "what_and_unique": "SẢN PHẨM LÀ GÌ & CÓ GÌ ĐẶC BIỆT: Định danh sản phẩm và điểm độc bản (USP) vượt trội",
                        "target_user": "SẢN PHẨM DÀNH CHO AI: Đối tượng cụ thể phù hợp nhất",
                        "why_buy": "TẠI SAO NÊN MUA: Lý do thuyết phục không thể chối từ",
                        "where_and_convenience": "DÙNG Ở ĐÂU & TIỆN LỢI LÀ GÌ: Hoàn cảnh ứng dụng thực tế",
                        "how_to_use": "CÁCH SỬ DỤNG: Thao tác thực tế 1-2 bước trực quan",
                        "product_size_class": "Phân loại kích thước",
                        "product_color_lock": "KHÓA MÀU SẮC & HỌA TIẾT HERO SKU CHUẨN XÁC THEO ẢNH",
                        "lid_mechanism": "Cơ chế mở nắp / vòi xịt",
                        "detected_prices": "QUÉT OCR GIÁ TIỀN: Giá gốc và giá sale",
                        "rounded_price_anchor": "LÀM TRÒN GIÁ NIÊM YẾT: Tự động đổi giá gốc thành cách đọc làm tròn (VD: 'gần năm trăm nghìn')",
                        "product_dimensions": "Thông số kích thước",
                        "prompt_dna_lock": "Visual DNA cho video"
                    }},
                    "outlines": [
                        {{ "id": 1, "title": "Tên kịch bản 1", "setting": "Bối cảnh chuẩn...", "hook": "Câu hook 3s đầu ngắn gọn ấn tượng...", "actors": {num_chars} }},
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
                for o in outlines: o.update({"duration_instruction": "Khoảng 30 giây", "narrator_mode": narrator_mode, "character_profiles": st.session_state.character_profiles})
                st.session_state.update({"all_scripts": outlines, "cloned_scripts": [], "expanded_scripts": [], "generated_details": {}, "active_script_id": None})
                st.toast("✅ Đã phân tích xong đầy đủ DNA!")
            except Exception as e: st.error(f"❌ Lỗi: {e}")

# Hiển thị DNA 4 khối
ca = st.session_state.content_analysis
if isinstance(ca, dict):
    st.divider()
    st.markdown("### 🔍 **Phân Tích DNA Chi Tiết Theo Mô Hình AIDA & Hero SKU**")
    with st.container(border=True):
        col_dna1, col_dna2 = st.columns(2)
        col_dna1.markdown(f"##### 🎯 **1. Chân dung Khách hàng & Hook 3s (Attention):**<br><div style='line-height: 1.8;'>{format_analysis_field(ca.get('target_audience', ''))}<br>{format_analysis_field(ca.get('pain_points', ''))}<br><b>⚡ Yếu tố Hook 3s đầu:</b> <span style='color:#d90429; font-weight:bold;'>{ca.get('hook_element', '')}</span></div>", unsafe_allow_html=True)
        col_dna2.markdown(f"##### 🔥 **2. Mã Màu Bán Chạy Nhất (Hero SKU):**<br><div style='line-height: 1.8;'><b>⭐ Mẫu ưu tiên làm video:</b> <span style='color:#d90429; font-size:16px; font-weight:bold;'>{ca.get('hero_sku_color', 'Tự động')}</span><br><b>🎨 Toàn bộ bảng màu:</b> <span style='color:#0284c7;'>{format_analysis_field(ca.get('color_palette', ''))}</span></div>", unsafe_allow_html=True)
        st.markdown(f"--- \n##### 💎 **3. Giải phẫu Sản phẩm Không Lộ Liễu (Interest & Desire):**<br><div style='line-height: 1.8;'><b>📦 Sản phẩm là gì & Điểm đặc biệt:</b> {ca.get('what_and_unique', '')}<br><b>👥 Sản phẩm dành cho ai:</b> {ca.get('target_user', '')}<br><b>🔥 Tại sao nên mua:</b> {ca.get('why_buy', '')}<br><b>📍 Dùng ở đâu & Tiện lợi:</b> {ca.get('where_and_convenience', '')}<br><b>🛠 Cách sử dụng:</b> {ca.get('how_to_use', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"--- \n##### 🏭 **4. Vật lý, Cơ chế & Mức Giá OCR:**<br><div style='line-height: 1.8;'><b>📐 Thông số:</b> {ca.get('product_dimensions', '')}<br><b>🎨 Khóa màu chi tiết:</b> {ca.get('product_color_lock', '')}<br><b>⚙ Cơ chế hoạt động/mở nắp:</b> {ca.get('lid_mechanism', 'Bình thường')}</div><br><b>💰 Mức giá (OCR):</b> {ca.get('detected_prices', '')} (Làm tròn: <b>{ca.get('rounded_price_anchor', '')}</b>)", unsafe_allow_html=True)
    if ca.get('prompt_dna_lock'):
        st.markdown("##### 📌 **Visual DNA Lock:**")
        st.code(ca.get('prompt_dna_lock'), language="text")

# DANH SÁCH KỊCH BẢN
all_sc = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
if all_sc:
    st.divider()
    comp_sc = [sc for sc in all_sc if sc["id"] in st.session_state.generated_details]
    pend_sc = [sc for sc in all_sc if sc["id"] not in st.session_state.generated_details]

    # KHUNG HIỂN THỊ CHI TIẾT (ĐƯỢC GẮN THẺ NEO ĐỂ TỰ ĐỘNG CUỘN ĐẾN ĐÂY)
    if st.session_state.active_script_id is not None:
        st.markdown("<div id='detailed-view-anchor'></div>", unsafe_allow_html=True)
        if st.button("⬅ Thu gọn danh sách kịch bản"):
            st.session_state.active_script_id = None
            st.session_state.scroll_to_top = True
            st.rerun()
            
        asc = st.session_state.generated_details.get(st.session_state.active_script_id, {})
        vp = asc.get("voice", {})
        
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(asc.get('title')).upper()}**")
        
        # HIỂN THỊ KHUNG HEADER ĐẦY ĐỦ VÀ SÂU SẮC NHƯ CÁC BẢN GỐC
        director_summary_html = asc.get('director_summary', '')
        if not director_summary_html:
            gender_txt = vp.get('gender', 'Nữ')
            tone_txt = vp.get('tone', 'Giọng HÀ NỘI GỐC ĐẦY NỘI LỰC, ĐANH THÉP, TRUYỀN CẢM')
            outfit_txt = asc.get('outfit_vi', 'Khóa cố định 1 bộ trang phục và 1 kiểu tóc duy nhất')
            hero_sku_txt = ca.get('hero_sku_color', 'Mẫu mã chuẩn từ ảnh gốc') if isinstance(ca, dict) else 'Mẫu mã chuẩn từ ảnh gốc'
            director_summary_html = f"⏱ <b>Thời lượng:</b> Khoảng 30 giây (Chuẩn 4 phân cảnh AIDA) | 🎙 <b>Giọng đọc:</b> {gender_txt} ({tone_txt})<br>👔 <b>Đồng nhất nhân vật & kiểu tóc:</b> {outfit_txt}<br>🎯 <b>Sản phẩm Hero SKU:</b> {hero_sku_txt}"
            
        st.markdown(f"<div class='detail-header-box'>{director_summary_html}</div>", unsafe_allow_html=True)
        
        for idx, scn in enumerate(asc.get("scenes", []), 1):
            vo_text = scn.get('voiceover', '')
            actual_words = count_words(vo_text)
            comma_count = vo_text.count(',')
            
            st.markdown(f"#### 📍 Phân cảnh {idx} ({scn.get('dur')}) - Giai đoạn {scn.get('aida_stage')}")
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting')}*\n\n**🎙 Đạo diễn & SFX:** *{scn.get('director')}*\n\n**💬 Thoại (Đếm thực tế: {actual_words} từ | {comma_count} dấu phẩy):** <span class='voiceover-text'>{vo_text}</span>", unsafe_allow_html=True)
            if scn.get('img_p'): st.markdown("**🖼 Prompt Ảnh:**"); st.code(img_p := scn.get('img_p'), language="text"); safe_copy_button(img_p, f"📋 Sao Chép Ảnh Cảnh {idx}")
            if scn.get('vid_p'): st.markdown("**🎥 Prompt Video (Khóa kiểu tóc, họa tiết, triệt tiêu icon giỏ hàng & SFX):**"); st.code(vid_p := scn.get('vid_p'), language="text"); safe_copy_button(vid_p, f"📋 Sao Chép Video Cảnh {idx}")
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
                        time.sleep(0.4)
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
                btn_detail_ph.markdown("<div style='background: #fffbeb; color: #d97706; border-radius: 8px; padding: 8px; text-align: center; font-size: 13px; font-weight: bold; border: 1px solid #fde68a;'>⏳ Đang dựng 4 cảnh AIDA...</div>", unsafe_allow_html=True)
            else:
                is_another_busy = (st.session_state.current_processing_id is not None)
                if btn_detail_ph.button("✨ Tạo chi tiết ngay", key=f"cr_{sc_id}", type="secondary", use_container_width=True, disabled=is_another_busy):
                    can_run, msg = check_usage_limit(st.session_state.current_email, is_detailing=True)
                    if can_run:
                        st.session_state.current_processing_id = sc_id
                        st.rerun()
                    else: st.error(msg)

    # XỬ LÝ GENERATION TẠI KỊCH BẢN ĐƯỢC CHỌN VÀ TỰ ĐỘNG MỞ KHÓA
    if st.session_state.current_processing_id is not None:
        target_id_to_run = st.session_state.current_processing_id
        lock_ui()
        try:
            with st.spinner(f"⏳ Đang bám sát câu Hook gốc và dựng 4 phân cảnh kịch bản #{target_id_to_run}..."):
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

    # KHỐI GỌI THÊM 5 KỊCH BẢN MỚI
    st.markdown("--- \n##### ➕ **Gọi Thêm 5 Kịch Bản Mới**")
    cg1, cg2, cg3, cg4 = st.columns([1.5, 0.8, 1.2, 1.5])
    a_opts = ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Chia sẻ", "😂 Hài hước"]
    c_ang = cg1.selectbox("🧭 Chiến lược mới:", a_opts, key=f"ea_{st.session_state.reset_key}")
    c_num = cg2.number_input("Số diễn viên:", 1, 8, 1, key=f"en_{st.session_state.reset_key}")
    c_dur_choice = cg3.selectbox("⏳ Thời lượng:", ["Tự động (~30s)", "Tùy chỉnh (s)"], key=f"ed_{st.session_state.reset_key}")
    c_dur_str = f"Chính xác {cg3.number_input('Số giây:', 10, 300, 60, key=f'eds_{st.session_state.reset_key}')} giây." if "Tùy" in c_dur_choice else "Khoảng 30 giây."
    c_nar = cg4.selectbox("🎙 Thuyết minh:", ["Nhân vật xuất hiện (On-camera)", "🎙 Lồng tiếng ngoài (Off-screen)"], key=f"ena_{st.session_state.reset_key}")

    e_chars = []
    for i in range(c_num):
        c_r, c_i = st.columns([2, 1])
        e_role = c_r.text_input(f"Vai trò NV {i+1} mới:", key=f"er_{i}_{st.session_state.reset_key}")
        e_file = c_i.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"ef_{i}_{st.session_state.reset_key}", label_visibility="collapsed")
        if e_file: e_chars.append({"id": i+1, "role": e_role or "AI phân tích", "file": e_file})

    btn_more_disabled = (st.session_state.current_processing_id is not None)
    if st.button("🚀 Gọi Thêm 5 Kịch Bản Mới", type="primary", use_container_width=True, disabled=btn_more_disabled):
        can_run, msg = check_usage_limit(st.session_state.current_email)
        if can_run:
            with st.spinner("⏳ Đang sáng tạo thêm 5 kịch bản theo mô hình AIDA..."):
                p_chars = [{"id": c["id"], "role": c["role"]} for c in e_chars] if e_chars else st.session_state.character_profiles
                new_sc = generate_more_scripts(c_ang, c_num, e_chars, c_nar, c_dur_str, p_chars)
                st.session_state.expanded_scripts.extend(new_sc)
                st.toast("✅ Đã sinh thêm 5 kịch bản mới!")
                time.sleep(0.4)
                st.rerun()
        else: st.error(msg)
