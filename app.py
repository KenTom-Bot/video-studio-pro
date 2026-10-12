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
    .detail-header-box { background: #eff6ff; border: 1.5px solid #bfdbfe; border-radius: 10px; padding: 15px; margin-bottom: 20px; color: #1e3a8a; }
    .voiceover-text { color: #15803d; background: #f0fdf4; padding: 6px 10px; border-radius: 6px; font-size: 15.5px; border: 1px solid #bbf7d0; display: inline-block; width: 100%; margin-top: 4px; }
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
        if acc.get("daily_usage_count", 0) >= limit: return False, f"Hết lượt tạo ({limit}/{limit})."
        acc["daily_usage_count"] += 1
        save_single_account(email, acc)
    return True, ""

def safe_copy_button(text_to_copy: str, button_label: str = "📋 Sao Chép Prompt"):
    b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    html_id = f"btn_{int(time.time()*10000)}_{len(text_to_copy)}"
    html_code = f"""
    <button id="{html_id}" style="background:#16a34a; color:white; border:none; padding:8px 16px; font-size:13px; font-weight:700; border-radius:6px; cursor:pointer; width:100%;">{button_label}</button>
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
    return "".join([f"<div style='margin-left: 10px;'>• {line.strip()}</div>" for line in text.split('<br>') if line.strip()])

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

# ==============================================================================
# 2. HÀM AI LÕI & LUẬT THÉP V60.0 (UNIFIED OUTFIT & FULL NARRATIVE AIDA)
# ==============================================================================
def repair_and_parse_json(text_content: str):
    cleaned = re.sub(r'```(?:json)?', '', text_content).strip()
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    candidate = match.group(0) if match else cleaned
    try:
        p = json.loads(candidate, strict=False)
        return p[0] if isinstance(p, list) and len(p) > 0 else p
    except Exception:
        fixed = candidate.rstrip(", \n\r\t")
        fixed += "}" if fixed.count("{") > fixed.count("}") else ""
        fixed += "]" if fixed.count("[") > fixed.count("]") else ""
        try:
            p = json.loads(fixed, strict=False)
            return p[0] if isinstance(p, list) and len(p) > 0 else p
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
    if not profiles: return "CHAR_LOCK: AI tự tạo diện mạo KOC Việt Nam tự nhiên, khóa cố định 100% Khuôn mặt, Kiểu tóc buộc/xõa và Vóc dáng xuyên suốt."
    rules = "KOC IDENTITY LOCK:\n"
    for p in profiles: rules += f" - Diễn viên {p['id']} ({p['role']}): Khóa chặt khuôn mặt người Việt tự nhiên, kiểu tóc cố định, vóc dáng chuẩn.\n"
    return rules

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, angle):
    strat = "MIX ĐA DẠNG 5 GÓC ĐỘ" if "Tự động mix" in angle else f"TUÂN THỦ CHIẾN LƯỢC: '{angle}'"
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL TIKTOK SHOP. {strat}. PHONG CÁCH: {style}
    
    🛑 QUY TẮC CỐT LÕI:
    1. ƯU TIÊN HERO SKU: Tự động quét nhãn bán chạy ('Đã bán 1K+', viền đỏ) từ ảnh để chọn màu/họa tiết chính.
    2. ĐỒNG NHẤT KHÔNG GIAN: Ga gối đệm bắt buộc trên giường phòng ngủ; đồ bếp ở mặt bàn bếp nấu nướng; xả kho ở kho hàng.
    3. CÔNG THỨC GIÁ TƯƠNG PHẢN: Neo giá gốc làm tròn, khẳng định giảm sâu/sập sàn, giấu giá sale, miễn trừ thời gian.
    4. {char_rules}
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction):
    is_on_camera = "On-camera" in narrator_mode
    audio_cmd = "Chèn lệnh `Audio:` vào `vid_p`." if is_on_camera else "KHÔNG chèn Audio vào `vid_p`."
    return f"""
    BẠN LÀ ĐẠO DIỄN VIRTUAL ĐỈNH CAO CHO VEO 3. PHONG CÁCH: {style}
    
    🛑 QUY TẮC BẮT BUỘC ĐỂ ĐẠT 100% CHẤT LƯỢNG:
    1. KHÓA ĐỒNG NHẤT TRANG PHỤC & DIỆN MẠO (UNIFIED OUTFIT & IDENTITY LOCK - CỰC KỲ QUAN TRỌNG):
       - Định nghĩa chi tiết duy nhất một bộ trang phục tại `global_outfit_en` (Ví dụ: áo thun/polo bên trong màu gì, tạp dề bên ngoài chính xác màu gì, chất liệu vải gì, quai đeo thế nào).
       - BẮT BUỘC tái sử dụng chính xác 100% chuỗi `global_outfit_en` này trong tất cả các `img_p` và `vid_p` của 4 phân cảnh. CẤM đổi màu tạp dề, cấm đổi kiểu áo giữa các cảnh.
       - Khuôn mặt, kiểu tóc (buộc gọn/xõa vai), màu tóc và hình thể phải được khóa đồng nhất qua `global_identity_en`.
    
    2. ĐẠO DIỄN HÀNH ĐỘNG SINH ĐỘNG NHƯ THỰC TẾ (REAL-LIFE STAGING):
       - CẤM nhân vật đứng đơ cầm sản phẩm giơ vào camera như chụp ảnh thẻ.
       - Phải có hành động thực tế theo sản phẩm: đang nấu nướng, bấm vòi xịt dầu ăn phun sương mịn màng lên đồ ăn/khay nướng, kiểm tra độ đàn hồi, thử nghiệm trực quan cuốn hút, khói bốc nhẹ, thức ăn giòn rụm.
    
    3. ĐỘ DÀI VÀ TÍNH LOGIC CỦA CÂU THOẠI (RICH & COMPLETE NARRATIVE):
       - Thoại phải có chiều sâu, tự nhiên, văn phong Hà Nội dứt khoát. Cả 4 phân cảnh ghép lại thành 1 câu chuyện hoàn chỉnh, logic, không chắp vá.
       - Bảng số từ chuẩn xác:
         + Cảnh 1 (Attention - 4s): 14 - 16 từ (Hook đánh trúng nỗi đau, bắt đầu thoại ngay 0.00s)
         + Cảnh 2 (Interest - 6s): 22 - 24 từ (Đưa sản phẩm vào giải quyết vấn đề, thao tác thực tế)
         + Cảnh 3 (Desire - 8s): 30 - 32 từ (Điểm độc bản USP, nêu bảng màu đa dạng, trải nghiệm thực tế)
         + Cảnh 4 (Action - 6s/8s): 22 - 28 từ (Đòn bẩy giá tương phản, kêu gọi hành động)
    
    4. KHÔNG CHỮ / SUBTITLES / ICONS (ANTI-UI LOCK):
       - Bắt buộc chèn vào cuối mọi prompt ảnh và video: "NO text, NO subtitles, NO floating icons, NO UI elements, NO watermarks. Clean camera frame."
    
    5. CƯỠNG CHẾ ĐỦ 4 CẢNH: Mảng 'scenes' bắt buộc sinh đủ 4 phân cảnh AIDA hoàn chỉnh.
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
    
    audio_instruction = 'Chèn: Audio: "[CHÉP ĐỦ 100% VOICEOVER, KHÔNG RÚT GỌN]", Layered SFX: [MÔ TẢ ÂM THANH MÔI TRƯỜNG THỰC TẾ: tiếng xịt dầu phun sương, tiếng xèo xèo chiên rán, sột soạt vải...]' if is_on_camera else 'Chỉ chèn Layered SFX thực tế, không chèn thoại.'
    voice_hint = "Giọng [Nam/Nữ] HÀ NỘI GỐC ĐẦY NỘI LỰC, ĐANH THÉP, BẮT ĐẦU THOẠI NGAY 0.00S, NHỊP ĐỘ ĐỀU METRONOME (4.3 - 4.5 từ/s)."

    prompt = f"""
    DỮ LIỆU ĐẦU VÀO: {prod_data_ctx} | DNA: {dna_data_ctx}
    Viết chi tiết kịch bản ID {target_id}: '{outline.get('title')}'. Hook: {outline.get('hook')}. Bối cảnh: {outline.get('setting')}.
    THUYẾT MINH: {audio_instruction} | LOẠI: {mode}
    
    🛑 BẮT BUỘC ĐỦ 4 PHÂN CẢNH THEO AIDA (MỖI CẢNH ĐẦY ĐỦ THOẠI VÀ HÀNH ĐỘNG THỰC TẾ):
    - Scene 1 (Attention): 4s (14-16 từ).
    - Scene 2 (Interest): 6s (22-24 từ).
    - Scene 3 (Desire): 8s (30-32 từ).
    - Scene 4 (Action): 6s hoặc 8s (22-28 từ).
    
    TRẢ VỀ JSON:
    {{
        "title": "{outline.get('title')}",
        "total_dur": "24s-30s",
        "outfit_vi": "Miêu tả cụ thể bộ trang phục và bối cảnh (sẽ dùng cố định cho mọi cảnh)",
        "global_identity_en": "Fixed English description of Face, Hair (specific style), Body.",
        "global_outfit_en": "Fixed English description of the EXACT outfit (e.g. beige cotton apron over plain white short-sleeve polo shirt). MUST BE REUSED 100% IN ALL SCENES.",
        "global_setting_en": "Fixed English description of the native environment/setting. MUST BE LOCKED.",
        "prod_dna": "English description of product with EXACT Hero SKU colors/patterns.",
        "voice": {{"gender": "Nam/Nữ", "tone": "{voice_hint}"}},
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention", "word_count": "14-16", "dur": "4s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh...",
                "action_en": "Real-life cooking/usage action. Character stands naturally wearing [global_outfit_en]. Mouth articulates immediately at 0.00s.",
                "director": "Attention | SFX thực tế | Khởi động: 0.00s | Tông đanh thép",
                "voiceover": "Thoại đầy đủ 14-16 từ gây chú ý...",
                "img_p": "Vertical 9:16 photo. Direct eye-level static shot. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Product: [prod_dna]. NO generated text, NO subtitles, NO floating icons, NO UI elements. Clean camera frame.",
                "vid_p": "Vertical 9:16 video. Direct eye-level static shot. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ VOICEOVER]\\", Layered SFX: [tiếng động thực tế], ambient tone. Product: [prod_dna]. Strict persistence, NO duplication, NO morphing. NO text, NO subtitles, NO icons, NO UI. Clean frame."
            }},
            {{
                "scene": 2, "aida_stage": "Interest", "word_count": "22-24", "dur": "6s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh...",
                "action_en": "Engaging real-life action demonstration. Wearing [global_outfit_en]. Mouth articulates immediately at 0.00s.",
                "director": "Interest | SFX thực tế | Khởi động: 0.00s | Tông tự nhiên",
                "voiceover": "Thoại đầy đủ 22-24 từ giải quyết vấn đề...",
                "img_p": "Vertical 9:16 photo. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Product: [prod_dna]. NO text, NO subtitles, NO UI. Clean frame.",
                "vid_p": "Vertical 9:16 video. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ VOICEOVER]\\", Layered SFX: [tiếng động thực tế]. Product: [prod_dna]. Clean frame."
            }},
            {{
                "scene": 3, "aida_stage": "Desire", "word_count": "30-32", "dur": "8s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh...",
                "action_en": "Dynamic product interaction demonstrating unique features. Wearing [global_outfit_en]. Mouth articulates at 0.00s.",
                "director": "Desire | SFX thực tế | Khởi động: 0.00s | Tông nội lực",
                "voiceover": "Thoại đầy đủ 30-32 từ nêu bật điểm độc bản và bảng màu combo...",
                "img_p": "Vertical 9:16 photo. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Product: [prod_dna]. NO text, NO subtitles, NO UI. Clean frame.",
                "vid_p": "Vertical 9:16 video. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ VOICEOVER]\\", Layered SFX: [tiếng động thực tế]. Product: [prod_dna]. Clean frame."
            }},
            {{
                "scene": 4, "aida_stage": "Action", "word_count": "22-28", "dur": "6s", "trans": "Chuyển cảnh mới",
                "setting": "Mô tả bối cảnh...",
                "action_en": "Confident posture, natural gesture toward action point. Wearing [global_outfit_en]. Mouth articulates at 0.00s.",
                "director": "Action | SFX thực tế | Khởi động: 0.00s | Tông chốt deal",
                "voiceover": "Thoại đòn bẩy giá tương phản 22-28 từ: Giá niêm yết gần [X] nghìn, nhưng hôm nay xả kho giảm cực sâu, bấm ngay giỏ hàng nhận deal hời nhé, lưu ý giá có thể thay đổi tùy thời điểm...",
                "img_p": "Vertical 9:16 photo. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Product: [prod_dna]. NO text, NO subtitles, NO UI. Clean frame.",
                "vid_p": "Vertical 9:16 video. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ VOICEOVER]\\", Layered SFX: [tiếng động thực tế]. Product: [prod_dna]. Clean frame."
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
    Số diễn viên: {num_chars}.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên kịch bản 1", "setting": "Bối cảnh chuẩn...", "hook": "Hook 3s đầu...", "actors": {num_chars} }}
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
    Nhân bản kịch bản gốc: {json.dumps(target, ensure_ascii=False)} thành 5 biến thể AIDA mới.
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
# 3. THANH BÊN (SIDEBAR) & TÀI KHOẢN
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        tabs = st.tabs(["🔐 Đăng Nhập", "🚀 Đăng Ký"])
        with tabs[0]:
            with st.form("login_form", border=False):
                email_input = st.text_input("Email:", autocomplete="new-password")
                pass_input = st.text_input("Mật khẩu:", type="password", autocomplete="new-password")
                if st.form_submit_button("🔑 Đăng Nhập", type="primary", use_container_width=True):
                    email_c, pass_c = email_input.strip(), pass_input.strip()
                    if email_c in st.session_state.licensed_accounts and st.session_state.licensed_accounts[email_c].get("password") == pass_c:
                        st.session_state.licensed_accounts[email_c]["active_session_id"] = st.session_state.session_id
                        save_single_account(email_c, st.session_state.licensed_accounts[email_c])
                        st.session_state.is_logged_in, st.session_state.current_email = True, email_c
                        st.toast("✅ Đăng nhập thành công!")
                        time.sleep(0.5); st.rerun()
                    else: st.error("Sai thông tin đăng nhập!")
        with tabs[1]:
            with st.form("register_form", border=False):
                r_email = st.text_input("Email đăng ký:", autocomplete="new-password")
                r_phone = st.text_input("Số điện thoại:", autocomplete="new-password")
                r_pass = st.text_input("Mật khẩu mới:", type="password", autocomplete="new-password")
                if st.form_submit_button("🚀 Đăng Ký", type="secondary", use_container_width=True):
                    if r_email and r_phone and r_pass and is_valid_phone(r_phone):
                        exp = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[r_email.strip()] = {"roles": ALL_MODULES, "phone": r_phone.strip(), "password": r_pass.strip(), "expires_at": exp, "plan_type": "Trial", "daily_usage_count": 0, "last_generation_date": "", "active_session_id": st.session_state.session_id}
                        save_single_account(r_email.strip(), st.session_state.licensed_accounts[r_email.strip()])
                        st.session_state.is_logged_in, st.session_state.current_email = True, r_email.strip()
                        st.toast("✅ Đăng ký thành công!")
                        time.sleep(0.5); st.rerun()
                    else: st.error("Vui lòng điền đúng thông tin!")
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
                st.toast("✅ Đã lưu!")
        
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

        if st.button("🚪 Đăng Xuất"): st.session_state.is_logged_in = False; st.rerun()

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
                
                prompt = f"""
                INPUT: {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)} | NOTE: {custom_note}
                BẮT BUỘC TRẢ VỀ JSON:
                {{
                    "content_analysis": {{
                        "target_audience": "Tệp khách mục tiêu",
                        "core_value": "Giá trị cốt lõi giải quyết vấn đề gì",
                        "pain_points": "Nỗi đau lớn nhất",
                        "hook_element": "Hook 3s đầu",
                        "hero_sku_color": "Mã màu/họa tiết bán chạy nhất nhận diện qua nhãn 'Đã bán 1K+' hoặc viền đỏ. Nếu không có thì chọn màu đẹp nhất.",
                        "color_palette": "Danh sách tất cả các màu có trong ảnh",
                        "what_and_unique": "Sản phẩm là gì & điểm độc bản",
                        "target_user": "Dành cho ai",
                        "why_buy": "Tại sao nên mua",
                        "where_and_convenience": "Dùng ở đâu tiện lợi",
                        "how_to_use": "Cách sử dụng thực tế",
                        "product_color_lock": "Khóa màu Hero SKU",
                        "detected_prices": "Giá niêm yết OCR",
                        "product_dimensions": "Kích thước thông số",
                        "prompt_dna_lock": "Visual DNA cho video"
                    }},
                    "outlines": [
                        {{ "id": 1, "title": "Tên 1", "setting": "Bối cảnh...", "hook": "Hook 3s đầu...", "actors": {num_chars} }},
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
                st.toast("✅ Đã phân tích xong!")
            except Exception as e: st.error(f"❌ Lỗi: {e}")

ca = st.session_state.content_analysis
if isinstance(ca, dict):
    st.divider()
    st.markdown("### 🔍 **Phân Tích DNA & Hero SKU Đã Khóa**")
    with st.container(border=True):
        col_dna1, col_dna2 = st.columns(2)
        col_dna1.markdown(f"##### 🎯 **1. Khách Hàng & Nỗi Đau:**<br>{format_analysis_field(ca.get('target_audience', ''))}<br>{format_analysis_field(ca.get('pain_points', ''))}", unsafe_allow_html=True)
        col_dna2.markdown(f"##### 🔥 **2. Mã Màu Bán Chạy (Hero SKU):**<br><b>⭐ Màu chính:</b> <span style='color:#d90429; font-size:16px; font-weight:bold;'>{ca.get('hero_sku_color', 'Tự động')}</span><br><b>🎨 Bảng màu:</b> {format_analysis_field(ca.get('color_palette', ''))}", unsafe_allow_html=True)

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
        st.markdown(f"<div class='detail-header-box'>⏱ Thời lượng: <b>{asc.get('total_dur')}</b> | 🎙 Giọng: <b>{vp.get('gender', 'Nữ')}</b> | 👔 <b>Trang phục khóa cố định:</b> {asc.get('outfit_vi')}</div>", unsafe_allow_html=True)
        
        for idx, scn in enumerate(asc.get("scenes", []), 1):
            st.markdown(f"#### 📍 Phân cảnh {idx} ({scn.get('dur')}) - Giai đoạn {scn.get('aida_stage')}")
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting')}*\n\n**🎙 Đạo diễn & SFX:** *{scn.get('director')}*\n\n**💬 Thoại:** <span class='voiceover-text'>{scn.get('voiceover')}</span>", unsafe_allow_html=True)
            if scn.get('img_p'): st.markdown("**🖼 Prompt Ảnh:**"); st.code(scn.get('img_p'), language="text"); safe_copy_button(scn.get('img_p'), f"📋 Sao Chép Ảnh Cảnh {idx}")
            if scn.get('vid_p'): st.markdown("**🎥 Prompt Video (Chứa Layered SFX):**"); st.code(scn.get('vid_p'), language="text"); safe_copy_button(scn.get('vid_p'), f"📋 Sao Chép Video Cảnh {idx}")
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
            if c3.button("🚀 Nhân bản", key=f"c_{sc_id}", type="primary", use_container_width=True):
                st.session_state.cloned_scripts.extend(clone_script(sc_id)); st.toast("✅ Đã clone!"); st.rerun()

    st.markdown("<br>### ⏳ **2. Kịch Bản Chờ Dựng**", unsafe_allow_html=True)
    for outline in pend_sc:
        sc_id = outline["id"]
        with st.container(border=True):
            c1, c2 = st.columns([3, 1.2])
            c1.markdown(f"**#{sc_id}. {outline.get('title')}** <span class=badge-pending>CHỜ DỰNG</span>", unsafe_allow_html=True)
            c1.caption(f"⚡ *{outline.get('hook')}*")
            if c2.button("✨ Tạo chi tiết ngay", key=f"cr_{sc_id}", type="secondary", use_container_width=True):
                can_run, msg = check_usage_limit(st.session_state.current_email, is_detailing=True)
                if can_run:
                    with st.spinner("⏳ Đang dựng 4 cảnh AIDA..."):
                        create_scene_details(sc_id, st.session_state.last_mode, st.session_state.last_style)
                        st.session_state.active_script_id = sc_id
                        st.rerun()
                else: st.error(msg)
