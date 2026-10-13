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
    .voiceover-text { color: #15803d; background: #f0fdf4; padding: 8px 12px; border-radius: 6px; font-size: 15.5px; border: 1px solid #bbf7d0; display: inline-block; width: 100%; margin-top: 4px; line-height: 1.6; }
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
    words = re.findall(r'\b\w+\b', text)
    return len(words)

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
    accs = {ADMIN_EMAIL: {"roles": ALL_MODULES, "phone": "0968484369", "expires_at": "2099-12-31", "password": "admin", "plan_type": "VIP", "active_session_id": ""}}
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
        return False, "Tài khoản của bạn đã hết hạn. Vui lòng liên hệ Admin để gia hạn!"
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
    ("target_duration_instruction", ""), ("character_profiles", []), ("current_project_id", None), ("load_more", False)
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

# ==============================================================================
# 2. HÀM AI LÕI & LUẬT THÉP V67.0
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
    in_str = False
    escape = False
    stack = []
    
    for ch in fixed:
        if escape: escape = False; continue
        if ch == '\\': escape = True; continue
        if ch == '"': in_str = not in_str; continue
        if not in_str:
            if ch in ('{', '['): stack.append('}' if ch == '{' else ']')
            elif ch in ('}', ']'):
                if stack and stack[-1] == ch: stack.pop()

    if in_str: fixed += '"'
    while stack: fixed += stack.pop()

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
    if not profiles: return "CHAR_LOCK: AI tự tạo diện mạo KOC người Việt Nam chân thực, thần thái tự tin, ánh mắt sáng, nụ cười cuốn hút, khóa cố định Khuôn mặt, Kiểu tóc duy nhất, Vóc dáng."
    rules = "KOC IDENTITY LOCK:\n"
    for p in profiles: rules += f" - Diễn viên {p['id']} ({p['role']}): TRÍCH XUẤT KHUÔN MẶT, KIỂU TÓC, VÓC DÁNG (Đảm bảo nét người Việt tự nhiên, dáng đứng/ngồi thẳng thanh lịch). KHÓA CỐ ĐỊNH 100% DIỆN MẠO NÀY.\n"
    return rules

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, angle):
    strat_cmd = "BẠN PHẢI MIX ĐA DẠNG 5 GÓC ĐỘ NỘI DUNG KHÁC NHAU." if "Tự động mix" in angle else f"🛑 LỆNH TẨY NÃO: BẮT BUỘC VIẾT CẢ 5 KỊCH BẢN THEO CHIẾN LƯỢC: '{angle}'."
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL KÊNH TIKTOK SHOP TRIỆU VIEW. PHONG CÁCH: {style}
    {strat_cmd}
    
    🛑 BỘ LỌC CHÍNH SÁCH NỀN TẢNG TUYỆT ĐỐI KHÔNG VI PHẠM:
    1. CẤM TUYỆT ĐỐI CÁC TỪ CAM KẾT & QUẢNG CÁO LỐ:
       - CẤM: 'tuyệt đối', 'hoàn toàn', '100%', 'chắc chắn', 'cam kết', 'dứt điểm', 'đặc trị', 'khỏi hẳn', 'chuẩn đét', 'giảm cân giữ dáng'.
       - Thay bằng: 'hỗ trợ', 'cải thiện', 'bữa ăn thanh đạm nhẹ bụng', 'tiện ích hơn rất nhiều'.
    2. CHÍNH SÁCH AN TOÀN TRẺ EM (MẸ VÀ BÉ):
       - TUYỆT ĐỐI CẤM để trẻ nhỏ, trẻ sơ sinh ở một mình trong khung hình. Bắt buộc luôn có Mẹ bế bồng, âu yếm hoặc giám sát an toàn bên cạnh.
    3. ƯU TIÊN MÃ MÀU HERO SKU: Quét OCR nhận diện nhãn bán chạy ('Đã bán 1K+', viền đỏ) từ ảnh để làm màu chủ đạo xuyên suốt.
    4. BỐI CẢNH NATIVE CHUẨN XÁC:
       - Ga gối đệm: Bắt buộc ở phòng ngủ ấm cúng hiện đại, đặt sản phẩm trên giường ngủ. Cấm đặt trên bàn.
       - Đồ bếp: Ở mặt bàn bếp/đảo bếp nấu nướng thực tế.
       - Flash Sale/Xả kho: Ở kho hàng/xưởng ngập kiện hàng.
    5. CÔNG THỨC GIÁ TƯƠNG PHẢN (OMNI-CHANNEL PRICING):
       - Làm tròn giá gốc OCR (gần... nghìn), khẳng định giảm cực sâu/sập sàn, giấu giá sale, miễn trừ trách nhiệm thời gian.
    6. PERSONA HÀ NỘI CHUẨN: Dứt khoát (nhé, này, thế, dùng, không). CẤM từ miền Nam: nha, nè, vô, xài.
    7. KHÔNG CHỮ/UI TẠO TỪ AI: Khung hình sạch 100%.
    8. {char_rules}
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction):
    is_on_camera = "On-camera" in narrator_mode
    audio_cmd = "Chèn lệnh `Audio:` vào `vid_p`." if is_on_camera else "KHÔNG chèn Audio vào `vid_p`."
    voice_hint = "Giọng [Nam/Nữ tự phân tích] HÀ NỘI CHUẨN 100% (CẤM TỪ MIỀN NAM). Giọng ngực ĐẦY NỘI LỰC, ĐANH THÉP, BẮT ĐẦU NÓI NGAY TẠI GIÂY 0.00, TỐC ĐỘ ĐỀU METRONOME KHÔNG DỒN ĐUÔI CÂU (4.3 - 4.5 từ/s)."

    return f"""
    BẠN LÀ ĐẠO DIỄN VIRTUAL ĐỈNH CAO CHO VEO 3. PHONG CÁCH: {style}
    
    🛑 QUY TẮC BẮT BUỘC ĐỂ ĐẠT 100% CHẤT LƯỢNG VÀ KHÔNG LỖI:
    1. CƯỠNG CHẾ ĐỦ 4 PHÂN CẢNH THEO MÔ HÌNH AIDA TRONG MẢNG 'scenes':
       - Scene 1 (aida_stage: "Attention"): 4s (13-14 từ).
       - Scene 2 (aida_stage: "Interest"): 6s (20-22 từ).
       - Scene 3 (aida_stage: "Desire"): 8s (28-30 từ).
       - Scene 4 (aida_stage: "Action"): 6s hoặc 8s (20-26 từ).
       - TUYỆT ĐỐI CẤM dừng lại sau cảnh 1 hoặc cảnh 2.
    
    2. KHÓA ĐỒNG NHẤT KIỂU TÓC & HỌA TIẾT SẢN PHẨM (HAIRSTYLE & PATTERN LOCK):
       - Kiểu tóc: Khóa DUY NHẤT một kiểu tóc trong `global_identity_en` (chọn cố định: hoặc búi cao gọn gàng, hoặc xõa dài tự nhiên) và dùng cho cả 4 cảnh. CẤM cảnh xõa tóc cảnh búi tóc!
       - Họa tiết sản phẩm: Trích xuất và khóa chính xác mẫu họa tiết của sản phẩm tham chiếu trong `prod_dna` (VD: họa tiết da báo chuẩn màu nâu-đen, hoặc thỏ hoa). CẤM đổi họa tiết giữa các cảnh.
    
    3. HÌNH ẢNH CẢNH 1 BẮT BUỘC TRỰC QUAN HÓA THỰC TRẠNG / NỖI ĐAU (VISUAL PROBLEM MATCH):
       - Cảnh 1 (Attention): Hình ảnh (`img_p`) và video (`vid_p`) BẮT BUỘC quay cận cảnh THỰC TRẠNG KHÓ CHỊU mà lời thoại nhắc tới (VD: đồ ăn ngấy mỡ ngập dầu lem nhem; người nằm trằn trọc ôm cổ đau đệm co rúm xộc xệch; đáy nồi cháy dính). KOC thể hiện cảm xúc ngán ngẩm, không quảng cáo thô thiển.
       - Cảnh 2 & 3: Thao tác thực tế sinh động (xịt dầu phun sương mịn màng, khói bốc nhẹ, thức ăn chín vàng giòn rụm; nằm gối êm ái đàn hồi).
    
    4. KHÓA BẤT BIẾN KẾT CẤU KHI DI CHUYỂN (KINETIC INVARIANT LOCK):
       - Khi nhân vật bước đi hoặc thao tác: Cánh tay cầm sản phẩm di chuyển đồng bộ với thân người, giữ cự ly cố định trước ngực (fixed 30cm chest coordinate).
       - Thao tác ấn/xịt: Chỉ duy nhất ngón tay ấn thẳng đứng 1 chiều (vertical 1-DOF downward piston stroke) lên đầu nút bấm, toàn bộ thân chai và vòi không biến dạng.
       - Trong `vid_p`, BẮT BUỘC chèn lệnh:
         "Invariant product mechanical geometry throughout camera and character locomotion. Zero structural drift, zero functional mutation. Spray nozzle mechanism operates exclusively on a fixed 1-degree-of-freedom downward piston press without bending, stretching, or fusing into fingers. Solid transparent glass body and beige nozzle retain absolute static volume and rigid edges during all walking, turning, and spraying motions."

    5. KHÓA ĐỒNG NHẤT 100% TRANG PHỤC:
       - Định nghĩa chi tiết duy nhất một bộ trang phục tại `global_outfit_en`. BẮT BUỘC tái sử dụng chính xác 100% chuỗi này trong tất cả `img_p` và `vid_p` của 4 phân cảnh. CẤM đổi màu trang phục.

    6. AN TOÀN TRẺ EM: Mẹ và Bé luôn có mẹ bế hoặc kề cận chăm sóc an toàn. Cấm để bé một mình.
    7. TỰ ĐỘNG SINH ÂM THANH MÔI TRƯỜNG THỰC TẾ (DIEGETIC SFX):
       - Tiếng xịt dầu phun sương xì xì, tiếng dầu sôi xèo xèo, cắn giòn rụm, sột soạt vải mềm.
       - Trong `vid_p`: Audio: "[Lời thoại]", Layered SFX: [Âm thanh vật lý tương ứng], ambient room tone.

    8. THOẠI TỨC THÌ TẠI 0.00S & NGẮT NGHỈ CHUẨN XÁC:
       - Nhân vật mở miệng nói ngay từ frame đầu tiên. Không dùng ngoặc đơn trong thoại.
       - Hạn chế dấu phẩy (Cảnh 4s & 6s tối đa 1 dấu phẩy; Cảnh 8s tối đa 2 dấu phẩy). Cân bằng số từ 2 vế qua dấu phẩy.
       - Cả 4 phân cảnh ghép lại thành 1 câu chuyện hoàn chỉnh, có nghĩa, logic, văn phong Hà Nội dứt khoát.

    9. CÔNG THỨC GIÁ TƯƠNG PHẢN (KHI NÓI GIÁ Ở CẢNH 4):
       - "Giá niêm yết gần [X] nghìn, nhưng hôm nay xả kho giảm cực sâu, bấm ngay giỏ hàng nhận deal hời nhé, lưu ý giá có thể thay đổi tùy thời điểm..."
    
    10. KHÔNG CHỮ / SUBTITLES / ICONS: "NO generated text, NO subtitles, NO floating icons, NO UI elements, NO watermarks. Clean camera frame."
    11. {audio_cmd}
    12. {char_rules}
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
    
    audio_instruction = 'Chèn: Audio: "[CHÉP ĐỦ 100% VOICEOVER, KHÔNG RÚT GỌN]", Layered SFX: [MÔ TẢ ÂM THANH MÔI TRƯỜNG THỰC TẾ]' if is_on_camera else 'Chỉ chèn Layered SFX thực tế, không chèn thoại.'
    voice_hint = "Giọng [Nam/Nữ] HÀ NỘI GỐC ĐẦY NỘI LỰC, ĐANH THÉP, BẮT ĐẦU THOẠI NGAY 0.00S, NHỊP ĐỘ ĐỀU METRONOME (4.3 - 4.5 từ/s)."

    prompt = f"""
    DỮ LIỆU ĐẦU VÀO: {prod_data_ctx} | DNA: {dna_data_ctx}
    Viết chi tiết kịch bản ID {target_id}: '{outline.get('title')}'. Hook: {outline.get('hook')}. Bối cảnh: {outline.get('setting')}.
    THUYẾT MINH: {audio_instruction} | LOẠI: {mode}
    
    🛑 LỆNH CƯỠNG CHẾ BẢO TOÀN ĐỒNG NHẤT:
    1. BẮT BUỘC KHÓA DUY NHẤT 1 KIỂU TÓC TRONG `global_identity_en` (chọn cố định búi cao hoặc xõa dài) và TÁI SỬ DỤNG CHO CẢ 4 CẢNH.
    2. BẮT BUỘC KHÓA ĐÚNG HỌA TIẾT & MÀU SẮC CHÍNH XÁC CỦA SẢN PHẨM TRONG `prod_dna` (VD: họa tiết da báo hoặc thỏ hoa theo đúng ảnh tham chiếu).
    3. KHÓA KẾT CẤU KHI DI CHUYỂN: Tay cầm cố định cự ly với ngực; thao tác xịt là ấn piston 1 chiều thẳng đứng (1-DOF downward piston press), thân chai và vòi không biến dạng.
    4. CHÍNH SÁCH: Cấm từ cam kết (tuyệt đối, hoàn toàn, 100%, chuẩn đét, giảm cân giữ dáng). Nếu có trẻ em, luôn có mẹ bế/giám sát kề bên an toàn.
    5. CẢNH 1: Trực quan hóa đúng thực trạng khó chịu/nỗi đau trong câu hook.
    6. CẢNH 4: Đòn bẩy giá tương phản.
    
    BẮT BUỘC ĐỦ 4 CẢNH TRONG 'scenes':
    - Scene 1: Attention (4s, 13-14 từ).
    - Scene 2: Interest (6s, 20-22 từ).
    - Scene 3: Desire (8s, 28-30 từ).
    - Scene 4: Action (6s hoặc 8s, 20-26 từ).
    
    TRẢ VỀ JSON:
    {{
        "title": "{outline.get('title')}",
        "total_dur": "24s-30s",
        "outfit_vi": "Trang phục và kiểu tóc khóa cố định duy nhất cho cả 4 cảnh",
        "global_identity_en": "Fixed English description of Face, EXACT LOCKED HAIRSTYLE (choose strictly ONE invariant style across all scenes: neatly tied high bun OR loose hair), Body.",
        "global_outfit_en": "Fixed English description of the EXACT outfit. MUST BE REUSED 100% IN ALL SCENES.",
        "global_setting_en": "Fixed English description of native setting. MUST BE LOCKED.",
        "prod_dna": "English description of product with EXACT Hero SKU colors/patterns locked across all scenes.",
        "voice": {{"gender": "Nam/Nữ", "tone": "{voice_hint}"}},
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention", "dur": "4s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh và THỰC TRẠNG NỖI ĐAU khớp với câu hook...",
                "action_en": "Visual problem manifestation: Close-up realistic shot showing the direct pain point. (If baby product: mother is present holding baby safely). Character with same locked hairstyle wearing [global_outfit_en]. Mouth articulates immediately at 0.00s.",
                "director": "Attention | Trực quan hóa nỗi đau thực tế | SFX thực tế | Khởi động: 0.00s | Tông đanh thép",
                "voiceover": "Thoại đầy đủ 13-14 từ lách từ cấm, đánh trúng nỗi đau thực tế...",
                "img_p": "Vertical 9:16 photo. Realistic cinematic shot. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Product: [prod_dna]. Clean frame.",
                "vid_p": "Vertical 9:16 video. Realistic cinematic shot. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ VOICEOVER]\\", Layered SFX: [tiếng động thực tế], ambient room tone. Invariant product mechanical geometry throughout camera and character locomotion. Zero structural drift, zero functional mutation. Spray nozzle mechanism operates exclusively on a fixed 1-degree-of-freedom downward piston press without bending, stretching, or fusing into fingers. Solid transparent glass body and beige nozzle retain absolute static volume and rigid edges during all walking, turning, and spraying motions. Strict persistence. NO text, NO subtitles, NO UI. Clean frame."
            }},
            {{
                "scene": 2, "aida_stage": "Interest", "dur": "6s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh giải pháp xuất hiện...",
                "action_en": "Real-life practical rescue action: Smooth real usage action with fixed chest-hand coordination while stepping naturally. Same locked hairstyle and outfit. Mouth articulates at 0.00s.",
                "director": "Interest | Thao tác thực tế giải phóng nỗi đau | SFX thực tế | Khởi động: 0.00s | Tông tự nhiên",
                "voiceover": "Thoại đầy đủ 20-22 từ giải quyết vấn đề...",
                "img_p": "Vertical 9:16 photo. Dynamic real action. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Product: [prod_dna]. Clean frame.",
                "vid_p": "Vertical 9:16 video. Dynamic real action. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ VOICEOVER]\\", Layered SFX: [tiếng phun sương xì xì]. Product: [prod_dna]. Invariant product mechanical geometry throughout locomotion. Downward vertical piston press. Clean frame."
            }},
            {{
                "scene": 3, "aida_stage": "Desire", "dur": "8s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh trải nghiệm vượt trội...",
                "action_en": "Delightful sensory experience: Dynamic interaction highlighting unique features and multiple varieties neatly staged. Same locked hairstyle. Mouth articulates at 0.00s.",
                "director": "Desire | Trực quan hóa giá trị và bảng màu combo | SFX thực tế | Khởi động: 0.00s | Tông nội lực",
                "voiceover": "Thoại đầy đủ 28-30 từ nêu bật điểm độc bản và bảng màu combo...",
                "img_p": "Vertical 9:16 photo. Rich sensory display. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Product: [prod_dna]. Clean frame.",
                "vid_p": "Vertical 9:16 video. Rich real-life sensory experience. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ VOICEOVER]\\", Layered SFX: [tiếng dầu chiên giòn rụm / tiếng cắn rôm rốp]. Product: [prod_dna]. Invariant mechanical volume. Clean frame."
            }},
            {{
                "scene": 4, "aida_stage": "Action", "dur": "6s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh chốt deal...",
                "action_en": "Warm confident closing posture: Character gestures purposefully toward basket trigger. Same locked hairstyle. Mouth articulates at 0.00s.",
                "director": "Action | Đòn bẩy giá tương phản | SFX thực tế | Khởi động: 0.00s | Tông chốt deal",
                "voiceover": "Thoại đòn bẩy giá tương phản 20-26 từ: Giá niêm yết gần [X] nghìn, nhưng hôm nay xả kho giảm cực sâu, bấm ngay giỏ hàng nhận deal hời nhé, lưu ý giá có thể thay đổi tùy thời điểm...",
                "img_p": "Vertical 9:16 photo. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Product: [prod_dna]. Clean frame.",
                "vid_p": "Vertical 9:16 video. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ VOICEOVER]\\", Layered SFX: [tiếng động nhẹ nhàng]. Product: [prod_dna]. Clean frame."
            }}
        ]
    }}
    """
    res = call_gemini([prompt], get_sys_inst_details(mode, style, narrator_mode, char_rules, "24s-30s"), max_tokens=7000)
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
    Sinh 5 kịch bản mới chuẩn mô hình AIDA theo chiến lược: '{angle}'.
    Số diễn viên: {num_chars}. Tuân thủ tuyệt đối chính sách chống từ cam kết, an toàn trẻ em.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên kịch bản 1", "setting": "Bối cảnh chuẩn...", "hook": "Hook 3s đầu đánh trúng nỗi đau...", "actors": {num_chars} }}
        ]
    }}
    BẮT BUỘC ĐỦ 5 KỊCH BẢN.
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, narrator_mode_more, char_rules, num_chars, angle), max_tokens=3000)
    if not res or ("outlines" not in res and "script_outlines" not in res): raise Exception("AI JSON Error.")
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
    
    prompt = f"""
    Nhân bản kịch bản gốc: {json.dumps(target, ensure_ascii=False)} thành 5 biến thể AIDA mới tuân thủ chính sách nền tảng.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "...", "setting": "...", "hook": "...", "actors": {num_chars} }}
        ]
    }}
    """
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
# 3. THANH BÊN (SIDEBAR) & QUẢN TRỊ ADMIN ĐẦY ĐỦ
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
                            st.error("❌ Mật khẩu không chính xác! Vui lòng thử lại.")
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
        st.markdown("### 🗂 DỰ ÁN")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True):
            st.session_state.update({k: v for k, v in [("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []), ("generated_details", {}), ("content_analysis", None), ("active_script_id", None), ("current_input_context", ""), ("current_project_id", None)]})
            st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
            st.rerun()
            
        st.session_state.active_project_title = st.text_input("Tên dự án:", value=st.session_state.active_project_title)
        if st.button("💾 Lưu Dự Án", use_container_width=True):
            payload = {k: st.session_state[k] for k in ["content_analysis", "all_scripts", "cloned_scripts", "expanded_scripts", "generated_details", "character_profiles", "current_input_context"]}
            if save_project_to_db(st.session_state.current_email, st.session_state.active_project_title, payload, st.session_state.current_project_id):
                st.toast("✅ Đã lưu dự án!")
        
        st.markdown("---")
        st.markdown("### 📂 KHO DỰ ÁN")
        if supabase:
            res = supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
            for p in (res.data or []):
                with st.expander(f"🎬 {p['project_title']}"):
                    if st.button("📂 Mở", key=f"o_{p['id']}", use_container_width=True):
                        sd = p.get("script_content", {})
                        st.session_state.update({
                            "content_analysis": sd.get("content_analysis"), "all_scripts": sd.get("all_scripts", []),
                            "cloned_scripts": sd.get("cloned_scripts", []), "expanded_scripts": sd.get("expanded_scripts", []),
                            "generated_details": {int(k): v for k, v in sd.get("generated_details", {}).items()},
                            "character_profiles": sd.get("character_profiles", []), "current_project_id": p['id'], "active_project_title": p['project_title']
                        })
                        st.rerun()
                    if st.button("🗑 Xóa", key=f"d_{p['id']}", type="secondary", use_container_width=True):
                        supabase.table("saved_projects").delete().eq("id", p['id']).execute(); st.rerun()

        # Quản trị Admin
        if st.session_state.current_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙ QUẢN TRỊ ADMIN")
            with st.form("admin_grant"):
                st.markdown("##### ➕ Cấp Quyền Tài Khoản")
                adm_acc = st.text_input("Email:", autocomplete="new-password")
                adm_phone = st.text_input("SĐT:", autocomplete="new-password")
                adm_pass = st.text_input("Mật khẩu:", value="123456", autocomplete="new-password")
                adm_plan = st.radio("Gói cước:", ["Trial", "Basic", "Advanced", "VIP"])
                adm_dur = st.selectbox("Thời hạn:", ["3 Ngày", "7 Ngày", "1 Tháng", "Vĩnh viễn"])
                if st.form_submit_button("💾 Cấp Quyền"):
                    if adm_acc and adm_phone and adm_pass:
                        exp_str = "2099-12-31" if "Vĩnh" in adm_dur else (datetime.now() + timedelta(days={"3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30}[adm_dur])).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[adm_acc.strip()] = {"roles": ALL_MODULES, "phone": adm_phone.strip(), "password": adm_pass.strip(), "expires_at": exp_str, "plan_type": adm_plan, "daily_usage_count": 0, "last_generation_date": "", "active_session_id": ""}
                        save_single_account(adm_acc.strip(), st.session_state.licensed_accounts[adm_acc.strip()])
                        st.toast("✅ Đã cấp quyền thành công!")
                        time.sleep(0.4); st.rerun()

        st.markdown("---")
        u_info = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        u_plan = u_info.get("plan_type", "Trial")
        u_used = u_info.get("daily_usage_count", 0) if u_info.get("last_generation_date") == datetime.now().strftime("%Y-%m-%d") else 0
        u_lim = "Không giới hạn" if u_plan == "VIP" else (20 if u_plan == "Advanced" else (10 if u_plan == "Basic" else 3))
        st.info(f"**GÓI {u_plan.upper()}**\n\n• Email: {st.session_state.current_email}\n• Tạo chi tiết: **{u_used}/{u_lim}**\n• Hạn dùng: {u_info.get('expires_at')}")

        if st.button("🚪 Đăng Xuất"): st.session_state.is_logged_in = False; st.rerun()

        # Hỗ trợ Admin
        st.markdown("""
        <div class="support-box">
            <b>HỖ TRỢ & BẢO HÀNH</b>
            <div class="social-icons-container">
                <a href="[https://zalo.me/0968484369](https://zalo.me/0968484369)" target="_blank" class="btn-zalo">Zalo</a>
                <a href="[https://facebook.com](https://facebook.com)" target="_blank" class="btn-fb">f</a>
                <a href="[https://tiktok.com](https://tiktok.com)" target="_blank" class="btn-tt">TikTok</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
        with st.spinner("⏳ Đạo diễn AI đang quét OCR bảng màu, nhận diện Hero SKU và phân tích sâu DNA tuân thủ chính sách..."):
            try:
                st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
                char_rules = generate_char_rules_string(st.session_state.character_profiles)
                st.session_state.update({"last_mode": mode, "last_style": style, "last_narrator": narrator_mode, "current_input_context": custom_note})
                st.session_state.current_product_data_saved = st.session_state.get("current_product_data", {})
                
                prompt = f"""
                INPUT: {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)} | NOTE: {custom_note}
                BẮT BUỘC TRẢ VỀ JSON ĐẦY ĐỦ CÁC TRƯỜNG (TUÂN THỦ CHÍNH SÁCH CHỐNG TỪ CAM KẾT & AN TOÀN TRẺ EM):
                {{
                    "content_analysis": {{
                        "target_audience": "Nhận diện TỆP KHÁCH HÀNG MỤC TIÊU",
                        "core_value": "Giá trị cốt lõi giải quyết vấn đề gì",
                        "pain_points": "Nỗi đau / Rào cản lớn nhất của khách hàng (BẮT BUỘC TRỰC QUAN HÓA Ở CẢNH 1)",
                        "hook_element": "Yếu tố giật gân, tạo tò mò hoặc xúc động đánh đúng tâm lý trong 3 giây đầu",
                        "hero_sku_color": "MÃ MÀU BÁN CHẠY NHẤT (HERO SKU): Nhận diện mã màu/họa tiết có nhãn 'Đã bán 1K+', 'Đã bán...', 'Top bán chạy' hoặc ô viền đỏ. Nếu không có thì chọn màu đẹp nhất.",
                        "color_palette": "BẢNG MÀU TOÀN BỘ: Liệt kê danh sách tất cả các màu/họa tiết có trong ảnh",
                        "what_and_unique": "SẢN PHẨM LÀ GÌ & CÓ GÌ ĐẶC BIỆT: Định danh sản phẩm và điểm độc bản (USP) vượt trội",
                        "target_user": "SẢN PHẨM DÀNH CHO AI: Đối tượng cụ thể phù hợp nhất",
                        "why_buy": "TẠI SAO NÊN MUA: Lý do thuyết phục không thể chối từ",
                        "where_and_convenience": "DÙNG Ở ĐÂU & TIỆN LỢI LÀ GÌ: Hoàn cảnh ứng dụng thực tế và tính linh hoạt",
                        "how_to_use": "CÁCH SỬ DỤNG: Thao tác thực tế 1-2 bước trực quan, dễ dàng",
                        "product_size_class": "Phân loại kích thước SP. Tương tác vật lý không ảo giác.",
                        "product_color_lock": "KHÓA MÀU SẮC & HỌA TIẾT HERO SKU CHUẨN XÁC: Bóc tách chi tiết màu sắc, họa tiết in của mã bán chạy nhất để nhúng cứng vào prompt.",
                        "lid_mechanism": "CƠ CHẾ MỞ NẮP / VÒI XỊT: Vòi xịt phun sương hay rót, nắp liền bản lề hay nắp rời.",
                        "detected_prices": "QUÉT OCR GIÁ TIỀN: Đọc kĩ ảnh tìm Giá Gốc và Giá Sale (nếu có).",
                        "rounded_price_anchor": "LÀM TRÒN GIÁ NIÊM YẾT: Tự động đổi số tiền gốc thành cách đọc làm tròn tiếng Việt (VD: 486.000đ -> 'gần năm trăm nghìn', 298.000đ -> 'gần ba trăm nghìn'). CẤM dùng số lẻ.",
                        "product_dimensions": "QUÉT THÔNG SỐ: Kích thước, dung tích, độ dày.",
                        "prompt_dna_lock": "Khóa thị giác (Visual DNA) cho AI sinh video. Strict zero-mutation geometry. NO added handles, NO extra lifting loops, NO phantom fixtures."
                    }},
                    "outlines": [
                        {{ "id": 1, "title": "Tên 1", "setting": "Bối cảnh chuẩn...", "hook": "Hook 3s đầu...", "actors": {num_chars} }},
                        {{ "id": 2, "title": "Tên 2", "setting": "...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 3, "title": "Tên 3", "setting": "...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 4, "title": "Tên 4", "setting": "...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 5, "title": "Tên 5", "setting": "...", "hook": "...", "actors": {num_chars} }}
                    ]
                }}
                """
                payload = ["IMAGES:"]
                for f in up_files:
                    cb, cm = compress_image_bytes(f, 1024, 80)
                    payload.append(types.Part.from_bytes(data=cb, mime_type=cm))
                for c in char_inputs:
                    cb, cm = compress_image_bytes(c['file'], 768, 80)
                    payload.extend([f"ACTOR {c['id']}:", types.Part.from_bytes(data=cb, mime_type=cm)])
                payload.append(prompt)
                
                res = call_gemini(payload, get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, initial_angle))
                st.session_state.content_analysis = res.get("content_analysis")
                outlines = res.get("outlines", res.get("script_outlines", []))
                for o in outlines: o.update({"duration_instruction": "Khoảng 24-30 giây", "narrator_mode": narrator_mode, "character_profiles": st.session_state.character_profiles})
                st.session_state.update({"all_scripts": outlines, "cloned_scripts": [], "expanded_scripts": [], "generated_details": {}, "active_script_id": None})
                st.toast("✅ Đã phân tích xong đầy đủ DNA!")
            except Exception as e: st.error(f"❌ Lỗi: {e}")

# Hiển thị DNA đầy đủ 4 khối chuẩn
ca = st.session_state.content_analysis
if isinstance(ca, dict):
    st.divider()
    st.markdown("### 🔍 **Phân Tích DNA Chi Tiết Theo Mô Hình AIDA & Hero SKU**")
    with st.container(border=True):
        col_dna1, col_dna2 = st.columns(2)
        col_dna1.markdown(f"##### 🎯 **1. Chân dung Khách hàng & Hook 3s (Attention):**<br><div style='line-height: 1.8;'>{format_analysis_field(ca.get('target_audience', ''))}<br>{format_analysis_field(ca.get('pain_points', ''))}<br><b>⚡ Yếu tố Hook 3s đầu:</b> <span style='color:#d90429; font-weight:bold;'>{ca.get('hook_element', '')}</span></div>", unsafe_allow_html=True)
        col_dna2.markdown(f"##### 🔥 **2. Mã Màu Bán Chạy Nhất (Hero SKU):**<br><div style='line-height: 1.8;'><b>⭐ Màu ưu tiên làm video:</b> <span style='color:#d90429; font-size:16px; font-weight:bold;'>{ca.get('hero_sku_color', 'Tự động chọn màu đẹp nhất')}</span><br><b>🎨 Toàn bộ bảng màu phát hiện:</b> <span style='color:#0284c7;'>{format_analysis_field(ca.get('color_palette', 'Đang cập nhật'))}</span></div>", unsafe_allow_html=True)
        st.markdown(f"--- \n##### 💎 **3. Giải phẫu Sản phẩm Không Lộ Liễu (Interest & Desire):**<br><div style='line-height: 1.8;'><b>📦 Sản phẩm là gì & Điểm đặc biệt:</b> {ca.get('what_and_unique', '')}<br><b>👥 Sản phẩm dành cho ai:</b> {ca.get('target_user', '')}<br><b>🔥 Tại sao nên mua:</b> {ca.get('why_buy', '')}<br><b>📍 Dùng ở đâu & Tiện lợi:</b> {ca.get('where_and_convenience', '')}<br><b>🛠 Cách sử dụng:</b> {ca.get('how_to_use', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"--- \n##### 🏭 **4. Vật lý, Cơ chế & Mức Giá OCR:**<br><div style='line-height: 1.8;'><b>📐 Thông số (Đã lọc vi phạm):</b> <span style='color:#059669; font-weight:bold;'>{ca.get('product_dimensions', 'Chưa lấy được kích thước')}</span><br><b>🎨 Khóa màu chi tiết:</b> <span style='color:#0284c7; font-weight:bold;'>{ca.get('product_color_lock', 'Không xác định')}</span><br><b>⚙ Cơ chế hoạt động/mở nắp:</b> <span style='color:#8b5cf6; font-weight:bold;'>{ca.get('lid_mechanism', 'Bình thường')}</span><br><b>💰 Mức giá (OCR):</b> <span style='color:#d90429; font-weight:bold;'>{ca.get('detected_prices', 'Không tìm thấy')}</span> (Làm tròn: <b>{ca.get('rounded_price_anchor', 'gần mốc gốc')}</b>)</div>", unsafe_allow_html=True)
    if ca.get('prompt_dna_lock'):
        st.markdown("##### 📌 **Visual DNA Lock:**")
        st.code(ca.get('prompt_dna_lock'), language="text")

# DANH SÁCH KỊCH BẢN
all_sc = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
if all_sc:
    st.divider()
    comp_sc = [sc for sc in all_sc if sc["id"] in st.session_state.generated_details]
    pend_sc = [sc for sc in all_sc if sc["id"] not in st.session_state.generated_details]

    if st.session_state.active_script_id is not None:
        if st.button("⬅ Thu gọn danh sách"): st.session_state.active_script_id = None; st.rerun()
        asc = st.session_state.generated_details.get(st.session_state.active_script_id, {})
        vp = asc.get("voice", {})
        
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT (CHUẨN 4 PHÂN CẢNH AIDA): {str(asc.get('title')).upper()}**")
        st.markdown(f"<div class='detail-header-box'>⏱ Thời lượng: <b>{asc.get('total_dur')}</b> | 🎙 Giọng: <b>{vp.get('gender', 'Nữ')} ({vp.get('tone', '')})</b> | 👔 <b>Khóa diện mạo & kiểu tóc cố định:</b> {asc.get('outfit_vi')}</div>", unsafe_allow_html=True)
        
        for idx, scn in enumerate(asc.get("scenes", []), 1):
            vo_text = scn.get('voiceover', '')
            actual_words = count_words(vo_text)
            comma_count = vo_text.count(',')
            
            st.markdown(f"#### 📍 Phân cảnh {idx} ({scn.get('dur')}) - Giai đoạn {scn.get('aida_stage')}")
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting')}*\n\n**🎙 Đạo diễn & SFX Thực Tế:** *{scn.get('director')}*\n\n**💬 Thoại (Đếm Python chuẩn xác: {actual_words} từ | {comma_count} dấu phẩy):** <span class='voiceover-text'>{vo_text}</span>", unsafe_allow_html=True)
            if scn.get('img_p'): st.markdown("**🖼 Prompt Ảnh:**"); st.code(img_p := scn.get('img_p'), language="text"); safe_copy_button(img_p, f"📋 Sao Chép Ảnh Cảnh {idx}")
            if scn.get('vid_p'): st.markdown("**🎥 Prompt Video (Khóa kiểu tóc, kết cấu & SFX thực tế):**"); st.code(vid_p := scn.get('vid_p'), language="text"); safe_copy_button(vid_p, f"📋 Sao Chép Video Cảnh {idx}")
            st.markdown("---")

    st.markdown("### 🎬 **1. Kịch Bản Đã Dựng Chi Tiết**")
    for outline in comp_sc:
        sc_id = outline["id"]
        with st.container(border=True):
            c1, c2, c3 = st.columns([2.5, 1, 1])
            c1.markdown(f"**#{sc_id}. {outline.get('title')}**")
            c1.caption(f"⚡ *{outline.get('hook')}*")
            if sc_id != st.session_state.active_script_id:
                if c2.button("👁 Xem", key=f"r_{sc_id}", use_container_width=True): st.session_state.active_script_id = sc_id; st.rerun()
            
            btn_clone_ph = c3.empty()
            if st.session_state.get(f"loading_clone_{sc_id}", False):
                btn_clone_ph.empty()
                st.markdown("<div style='background: #fef2f2; color: #dc2626; border-radius: 6px; padding: 6px; text-align: center; font-size: 13px; font-weight: bold;'>⏳ Đang nhân bản 5 biến thể...</div>", unsafe_allow_html=True)
                lock_ui()
                try:
                    st.session_state.cloned_scripts.extend(clone_script(sc_id))
                    st.toast("✅ Đã nhân bản 5 kịch bản mới!")
                except Exception as e:
                    st.error(f"❌ Lỗi: {e}")
                finally:
                    st.session_state[f"loading_clone_{sc_id}"] = False
                    time.sleep(0.4)
                    st.rerun()
            else:
                if btn_clone_ph.button("🚀 Nhân bản", key=f"c_{sc_id}", type="primary", use_container_width=True):
                    can_run, msg = check_usage_limit(st.session_state.current_email)
                    if can_run:
                        st.session_state[f"loading_clone_{sc_id}"] = True
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
            if st.session_state.get(f"loading_detail_{sc_id}", False):
                btn_detail_ph.empty()
                st.markdown("<div style='background: #fffbeb; color: #d97706; border-radius: 6px; padding: 6px; text-align: center; font-size: 13px; font-weight: bold;'>⏳ Đang dựng đủ 4 cảnh AIDA...</div>", unsafe_allow_html=True)
                lock_ui()
                try:
                    create_scene_details(sc_id, st.session_state.last_mode, st.session_state.last_style)
                    st.session_state.active_script_id = sc_id
                    st.toast("✅ Đã hoàn tất dựng 4 phân cảnh!")
                except Exception as e:
                    st.error(f"❌ Lỗi: {e}")
                finally:
                    st.session_state[f"loading_detail_{sc_id}"] = False
                    time.sleep(0.4)
                    st.rerun()
            else:
                if btn_detail_ph.button("✨ Tạo chi tiết ngay", key=f"cr_{sc_id}", type="secondary", use_container_width=True):
                    can_run, msg = check_usage_limit(st.session_state.current_email, is_detailing=True)
                    if can_run:
                        st.session_state[f"loading_detail_{sc_id}"] = True
                        st.rerun()
                    else: st.error(msg)

    # KHỐI GỌI THÊM 5 KỊCH BẢN MỚI
    st.markdown("--- \n##### ➕ **Gọi Thêm 5 Kịch Bản Mới**")
    cg1, cg2, cg3, cg4 = st.columns([1.5, 0.8, 1.2, 1.5])
    a_opts = ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Chia sẻ", "😂 Hài hước"]
    c_ang = cg1.selectbox("🧭 Chiến lược mới:", a_opts, key=f"ea_{st.session_state.reset_key}")
    c_num = cg2.number_input("Số diễn viên:", 1, 8, 1, key=f"en_{st.session_state.reset_key}")
    c_dur_choice = cg3.selectbox("⏳ Thời lượng:", ["Tự động (~24-30s)", "Tùy chỉnh (s)"], key=f"ed_{st.session_state.reset_key}")
    c_dur_str = f"Chính xác {cg3.number_input('Số giây:', 10, 300, 60, key=f'eds_{st.session_state.reset_key}')} giây." if "Tùy" in c_dur_choice else "Khoảng 24-30 giây."
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
            st.toast("✅ Đã sinh thêm 5 kịch bản mới!")
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
        finally:
            st.session_state.load_more = False
            time.sleep(0.4)
            st.rerun()
    else:
        if btn_more_ph.button("🚀 Gọi Thêm 5 Kịch Bản Mới", type="primary", use_container_width=True):
            can_run, msg = check_usage_limit(st.session_state.current_email)
            if can_run:
                st.session_state.load_more = True
                st.rerun()
            else:
                st.error(msg)
