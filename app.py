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
from datetime import datetime, timedelta

# ==============================================================================
# 1. CẤU HÌNH GIAO DIỆN & KẾT NỐI
# ==============================================================================
st.set_page_config(page_title="Universal AI Video Studio Pro", page_icon="🎬", layout="wide")

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
    .voiceover-text { color: #15803d; background: #f0fdf4; padding: 4px 8px; border-radius: 6px; font-family: monospace; font-size: 15px; border: 1px solid #bbf7d0; }
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
ACCOUNTS_FILE = "accounts.json"
HARDCODED_ASPECT = "9:16 (Dọc TikTok/Reels)"

@st.cache_resource
def init_supabase():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None
supabase = init_supabase()

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
client = genai.Client(api_key=api_key) if api_key else None

def load_licensed_accounts():
    accs = {ADMIN_EMAIL: {"roles": ALL_MODULES, "phone": "0968484369", "expires_at": "2099-12-31", "password": "admin", "is_trial": False}}
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f: 
                data = json.load(f)
                for k, v in data.items():
                    if "password" not in v: v["password"] = v.get("phone", "123456")
                    if "is_trial" not in v: v["is_trial"] = False 
                    if "daily_usage_count" not in v: v["daily_usage_count"] = 0
                    if "last_generation_date" not in v: v["last_generation_date"] = ""
                    accs[k] = v
        except: pass
    return accs

def save_licensed_accounts(acc_dict):
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(acc_dict, f, ensure_ascii=False, indent=2)
    except: pass

def check_usage_limit(email):
    if email == ADMIN_EMAIL: return True, ""
    accs = st.session_state.licensed_accounts
    acc = accs.get(email)
    if not acc: return False, "Lỗi xác thực tài khoản."
    
    exp_date = datetime.strptime(acc.get("expires_at", "2099-12-31"), "%Y-%m-%d")
    if datetime.now() > exp_date:
        return False, "Tài khoản của bạn đã hết hạn. Vui lòng liên hệ Admin để gia hạn!"
        
    if acc.get("is_trial", False):
        today = datetime.now().strftime("%Y-%m-%d")
        if acc.get("last_generation_date") != today:
            acc["daily_usage_count"] = 0
            acc["last_generation_date"] = today
        
        if acc.get("daily_usage_count", 0) >= 5:
            return False, "Bạn đã dùng hết 5/5 lượt tạo kịch bản của hôm nay! Vui lòng quay lại vào ngày mai hoặc mua gói VIP để không giới hạn."
        
        acc["daily_usage_count"] += 1
        save_licensed_accounts(accs)
        
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
for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", load_licensed_accounts()),
    ("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []),
    ("generated_details", {}), ("content_analysis", None), ("active_script_id", None),
    ("current_input_context", ""), ("current_product_data_saved", None), ("current_product_data", None),
    ("reset_key", 0), ("scroll_to_top", False), ("scroll_to_detail", False), ("extra_num_chars", 1),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"),
    ("last_mode", ""), ("last_style", ""), ("last_narrator", ""),
    ("target_duration_instruction", ""), ("character_profiles", []), 
    ("editing_acc_email", None), ("current_project_id", None)
]:
    if key not in st.session_state: st.session_state[key] = default_val

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
# 2. HÀM AI LÕI & LUẬT THÉP (ĐÃ FIX LỖI FUNCTION NOT DEFINED)
# ==============================================================================
def get_dynamic_realtime_context(mode):
    now = datetime.now()
    month = now.month
    if month in [12, 1, 2]: season_desc = "thời tiết lạnh giá"
    elif month in [3, 4, 5]: season_desc = "thời tiết giao mùa, ấm áp"
    elif month in [6, 7, 8]: season_desc = "thời tiết nắng nóng"
    else: season_desc = "thời tiết mát mẻ, se lạnh"
    
    return f"BỐI CẢNH: {season_desc}. CẤM nhắc trực tiếp tên mùa một cách máy móc. Hãy dùng cảm giác thời tiết để chuyển ý tự nhiên."

def clean_and_parse_json(text_content: str):
    cleaned = re.sub(r'```(?:json)?', '', text_content).strip()
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    if match: cleaned = match.group(0)
    try:
        parsed = json.loads(cleaned, strict=False)
        return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else parsed
    except json.JSONDecodeError:
        try:
            py_str = cleaned.replace('true', 'True').replace('false', 'False').replace('null', 'None')
            parsed = ast.literal_eval(py_str)
            return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else parsed
        except Exception:
            raise Exception("AI sinh JSON lỗi cấu trúc. Vui lòng thử lại.")

def call_gemini(contents, sys_inst="Bạn là AI hỗ trợ JSON."):
    for attempt in range(3):
        try:
            res = client.models.generate_content(
                model="gemini-3.6-flash", contents=contents,
                config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.7)
            )
            return clean_and_parse_json(res.text)
        except Exception as e:
            if attempt == 2: raise e
            time.sleep(2)

def generate_char_rules_string(profiles):
    if not profiles: 
        return "CHAR_LOCK: AI creates face/hair/body and copies EXACTLY to all scenes. 100% consistent."
    rules = "MULTI-LAYER OUTFIT & BIO LOCK:\n"
    for p in profiles: 
        rules += f" - Actor {p['id']} ({p['role']}): Extract Face/Body/Hair from image. IGNORE original clothes. Design NEW multi-layer outfit (outer + inner) and LOCK exactly across all scenes.\n"
    return rules

def get_mode_specific_rules(mode):
    if "Viral" in mode:
        return """
    🎯 ĐỊNH HƯỚNG: VIRAL & XÂY KÊNH (CHUYÊN GIA / KIẾN THỨC)
    - MỤC TIÊU LÕI: Chia sẻ kiến thức, mẹo hay hoặc kể chuyện logic để KÉO LƯỢT FOLLOW. CẤM CHỐT ĐƠN.
    - VĂN PHONG (TONE): Dân dã, tự nhiên, chuyên nghiệp. Không nói rườm rà.
        """
    else:
        return """
    🎯 ĐỊNH HƯỚNG: TIKTOK SHOP & BÁN HÀNG (AFFILIATE THỰC CHIẾN)
    - MỤC TIÊU LÕI: Đánh trúng Nỗi đau (Pain points), làm nổi bật USP để CHỐT ĐƠN.
    - CƠ CHẾ KÊU GỌI (CTA): Giục khách mua ngay, chớp deal hời. Nhưng CHỈ XUẤT HIỆN Ở CẢNH CUỐI.
        """

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars):
    time_ctx = get_dynamic_realtime_context(mode)
    mode_rules = get_mode_specific_rules(mode)
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL CHO VEO 3 VÀ IMAGEN 3. PHONG CÁCH: {style} | ĐỊNH DẠNG: {HARDCODED_ASPECT}
    {time_ctx}
    {mode_rules}
    🛑 CÁC QUY TẮC BỔ SUNG TUÂN THỦ 100%:
    1. SỐ LƯỢNG NHÂN VẬT: Đúng {num_chars} nhân vật tương tác với nhau.
    2. LÁCH LUẬT CẤM: TUYỆT ĐỐI CẤM dùng các từ: "Cam kết", "Chữa trị", "Đúng", "Chính xác 100%", "Trị dứt điểm". Dùng từ nói giảm nói tránh như "Khoảng...", "Hỗ trợ...", "Giúp cải thiện...". CẤM BÁO GIÁ CỤ THỂ BẰNG CON SỐ.
    3. CẤM NHẮC THỜI TIẾT: CẤM nhắc đến thời tiết hay mùa vụ (như mùa đông, mùa thu) vào kịch bản để tránh khiên cưỡng.
    4. ĐỒNG NHẤT 100%: Giữ nguyên trang phục ĐA LỚP, vóc dáng, kiểu tóc xuyên suốt video. Sản phẩm phải y hệt thực tế (KHÔNG đổi màu/kích thước).
    5. XƯNG HÔ THÔNG MINH: Phân tích tệp khách hàng. Nếu nữ -> xưng "chị em". Nam -> xưng "anh em". Chung -> xưng "anh chị". CẤM dùng "Hội", "Mấy bạn", "Dân nghiện...".
    6. QUY TẮC HOOK: Hook mở đầu KHÔNG ĐƯỢC chứa lời kêu gọi mua hàng/giỏ hàng. Cảnh 1 chỉ để đồng cảm.
    7. {char_rules}
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, num_chars, duration_instruction):
    time_ctx = get_dynamic_realtime_context(mode)
    mode_rules = get_mode_specific_rules(mode)
    is_on_camera = "On-camera" in narrator_mode
    narrator_instruction = f"Nhân vật xuất hiện trực tiếp nói chuyện trước ống kính. YÊU CẦU TỐI QUAN TRỌNG CHO VEO 3: BẮT BUỘC chèn lệnh `Audio: \"[Nguyên văn lời thoại tiếng Việt]\"` vào tất cả các `video_prompt`." if is_on_camera else "Lồng tiếng ngoài khung hình. KHÔNG đưa phần Audio vào `video_prompt`."
    
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL CHO VEO 3 VÀ IMAGEN 3. PHONG CÁCH: {style} | ĐỊNH DẠNG: {HARDCODED_ASPECT}
    {time_ctx}
    {mode_rules}
    🛑 CÁC QUY TẮC KỸ THUẬT QUAY DỰNG ĐỈNH CAO:
    1. ANTI-MORPHING: BẮT BUỘC chèn đoạn mã lệnh này vào đuôi của MỌI `video_prompt`: "Maintain EXACT product geometry, scale, color, and real-life details. NO morphing, NO distortion, NO hallucination of new parts. Keep the object rigid and consistent. NO generated text."
    2. CHÍNH SÁCH KIỂM DUYỆT: Cấm các từ "Cam kết", "Đúng", "Chữa trị". Thay bằng "Khoảng", "Hỗ trợ", "Giúp cải thiện". Cấm báo giá bằng số cụ thể.
    3. WPM (ĐẾM CỰC KỲ CHÍNH XÁC): {duration_instruction}. 
       - Cảnh 4s = Tối đa 16 âm tiết. 
       - Cảnh 6s = Tối đa 24 âm tiết. 
       - Cảnh 8s = Tối đa 32 âm tiết. (VIẾT LỐ SẼ GÂY LỖI ÂM THANH).
    4. NGÔN TỪ THỰC TẾ & XƯNG HÔ THÔNG MINH (CỰC KỲ QUAN TRỌNG): 
       - Dùng từ chuẩn xác: Hầm thịt thì dùng "chín mềm" (không dùng "mọng nước"), lau chùi thì dùng "dễ lau chùi" (không dùng "siêu khỏe"). 
       - TUYỆT ĐỐI CẤM nhồi nhét thời tiết, mùa vụ vào thoại.
       - Tự phân tích sản phẩm: Nữ -> "chị em", Nam -> "anh em", Chung -> "anh chị". CẤM dùng "Mấy bạn", "Hội", "Dân...". KHÔNG dùng "Cái nồi" -> chỉ dùng "Nồi".
    5. NGỮ PHÁP & SEAMLESS FLOW:
       - CÂU PHẢI CÓ ĐỦ CHỦ NGỮ - VỊ NGỮ. BẮT BUỘC dùng dấu phẩy (,) và dấu chấm (.) để tạo quãng nghỉ giúp giọng đọc AI có cảm xúc.
       - Các câu thoại từ Cảnh 1 đến Cảnh cuối BẮT BUỘC phải ghép lại thành 1 ĐOẠN VĂN DUY NHẤT mượt mà, dân dã, tự nhiên. KHÔNG hô khẩu hiệu cụt lủn.
    6. CẤU TRÚC HOOK & CTA:
       - Cảnh 1 (Hook): Chỉ dùng để đồng cảm vấn đề. CẤM kêu gọi bấm giỏ hàng/mua ngay ở Cảnh 1.
       - Cảnh cuối cùng: ĐÂY MỚI LÀ NƠI chốt đơn, gọi "bấm góc trái/mua ngay".
    7. LOGIC ĐỒNG BỘ CHUYỂN CẢNH:
       - CHỈ DÙNG "Cảnh nối tiếp (Dùng lại ảnh cuối)" KHI VÀ CHỈ KHI lời thoại ĐANG GIẢI THÍCH CHO Ý TRƯỚC ĐÓ và hành động đang diễn ra liên tục. (Bắt buộc chèn lệnh `holding the final frame steady as a reference anchor`).
       - NẾU LỜI THOẠI CHUYỂN Ý MỚI -> BẮT BUỘC dùng "Chuyển cảnh mới (Tạo ảnh mới)".
    8. {narrator_instruction}
    9. {char_rules}
    """

def create_scene_details(target_id, mode, style, narrator_mode, char_rules):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if sc["id"] == target_id), None)
    if not outline: return
    
    is_on_camera = "On-camera" in narrator_mode
    prod_data_ctx = json.dumps(st.session_state.get('current_product_data_saved'), ensure_ascii=False)
    dna_data_ctx = json.dumps(st.session_state.get('content_analysis'), ensure_ascii=False)
    duration_instruction = st.session_state.get("target_duration_instruction", "Tự động phân bổ 3-5 phân cảnh.")
    num_chars = outline.get("actor_count", st.session_state.get("extra_num_chars", 1))
    
    audio_instruction = 'Nhân vật xuất hiện trực tiếp. TRONG TẤT CẢ video_prompt BẮT BUỘC chèn lệnh: Audio: "[Điền nguyên văn lời thoại tiếng Việt]"' if is_on_camera else 'Lồng tiếng ngoài khung hình. KHÔNG chèn Audio vào video_prompt.'
    
    if "Viral" in mode:
        voice_hint = "Giọng đọc CẢM XÚC, CHÂN THẬT, GẦN GŨI để tạo sự đồng cảm và giữ chân người xem. Tốc độ vừa phải (1.8-2.2 từ/s)."
    else:
        voice_hint = "Giọng đọc MẠNH MẼ, NHANH, NĂNG LƯỢNG CAO để cuốn hút người xem và tạo chuyển đổi chốt sale dồn dập (3.5-4 từ/s)."

    video_prompt_example_1 = 'Vertical 9:16 video. Static shot... character talking directly to camera. Audio: \\"[Chèn nguyên văn lời thoại tiếng Việt vào đây]\\". Wearing EXACT SAME [Chèn tiếng Anh trang phục đa lớp]. [CHÈN NGUYÊN VĂN product_visual_dna_en VÀO ĐÂY]. Maintain EXACT product geometry, scale, and details. NO morphing, NO distortion, NO hallucination of new parts. Keep the object rigid and consistent. NO generated text.' if is_on_camera else 'Vertical 9:16 video. Slow pan... off-screen voiceover... [CHÈN NGUYÊN VĂN product_visual_dna_en VÀO ĐÂY]. Maintain EXACT product geometry, NO morphing. NO generated text.'
    video_prompt_example_2 = '<Nếu Start anchor as chèn: exactly final frame from holding hành image liên provided reference steady the tục,>. [CHÈN product_visual_dna_en]. Maintain EXACT product geometry, NO morphing. Audio: \\"[Chèn lời thoại tiếng Việt]\\"' if is_on_camera else '<Nếu Start anchor as chèn: exactly final frame from holding hành image liên provided reference steady the tục,>. [CHÈN product_visual_dna_en]. Maintain EXACT product geometry, NO morphing.'

    prompt = f"""
    DỮ LIỆU ĐẦU VÀO: {prod_data_ctx}
    PHÂN TÍCH DNA: {dna_data_ctx}
    
    Viết chi tiết kịch bản ID {target_id}: '{outline.get('title')}'. Hook: {outline.get('hook', outline.get('target_hook'))}. Bối cảnh: {outline.get('setting', outline.get('setting_style'))}.
    THUYẾT MINH: {audio_instruction}
    
    LƯU Ý ĐẶC BIỆT (PHẢI TUÂN THỦ TÙY TỪNG CHỮ):
    - ĐOẠN VĂN LIỀN KHỐI: Toàn bộ lời thoại của các cảnh phải ghép lại thành 1 đoạn văn DÂN DÃ, ĐỜI THƯỜNG duy nhất.
    - XƯNG HÔ THÔNG MINH: Dùng "chị em" hoặc "anh em" hoặc "anh chị". CẤM xưng "Hội", "Mấy bạn".
    - NGÔN TỪ THỰC TẾ: Không dùng từ cường điệu sai ngữ cảnh (VD không dùng "mọng nước" cho đồ hầm). CẤM nhắc mùa vụ/thời tiết.
    - HOOK & CTA: Cảnh 1 TUYỆT ĐỐI KHÔNG kêu gọi mua hàng. CTA mua hàng CHỈ NẰM Ở CẢNH CUỐI CÙNG.
    - ĐẾM ĐÚNG SỐ ÂM TIẾT WPM. 4s <= 16 âm tiết, 6s <= 24 âm tiết. KHÔNG DÙNG TỪ CẤM.
    
    TRẢ VỀ ĐÚNG 1 DICT JSON CẤU TRÚC SAU:
    {{
        "title": "{outline.get('title')}",
        "total_dur": "Tổng thời gian khớp",
        "outfit_vi": "BẮT BUỘC MÔ TẢ DIỆN MẠO VÀ TRANG PHỤC ĐA LỚP BẰNG TIẾNG VIỆT",
        "prod_dna": "Mô tả ngắn gọn hình dáng, chi tiết vật lý sản phẩm bằng TIẾNG ANH. NẾU KHÔNG CÓ SẢN PHẨM ĐỂ TRỐNG.",
        "voice": {{"gender": "Nam/Nữ", "tone": "{voice_hint}"}},
        "scenes": [
            {{
                "scene": 1, "dur": "4s", "trans": "Chuyển cảnh mới (Tạo ảnh mới)", 
                "setting": "Mô tả bối cảnh góc máy AN TOÀN (Static/Slow)...",
                "director": "Mô tả biểu cảm nhấn nhá cảm xúc...", 
                "voiceover": "GỌI TÊN KHÁCH (Anh chị/Chị em). Khơi gợi vấn đề. CÓ CHỦ VỊ, DẤU PHẨY NGẮT NGHỈ. CẤM CÓ CTA Ở ĐÂY. ĐÚNG WPM...",
                "img_p": "Cinematic vertical 9:16 photo. Static shot... [ENG OUTFIT]. [prod_dna]. Maintain EXACT facial identity, identical outer jacket and inner shirt. NO generated text.", 
                "vid_p": "Vertical 9:16 video. Static shot... character talking to camera. Audio: \\"[exact vi dialogue]\\". Wearing EXACT SAME [ENG OUTFIT]. [prod_dna]. Maintain EXACT product geometry, scale, color. NO morphing, NO distortion. Keep object rigid. NO generated text."
            }},
            {{
                "scene": 2, "dur": "6s", "trans": "<Cảnh Chuyển HOẶC cảnh mới nối tiếp>", 
                "setting": "...", "director": "...", 
                "voiceover": "<Nối 1. Câu Cảnh WPM chữ có dân dã, dấu mạch nghỉ. ngắt phẩy thường, từ ĐÚNG đời>",
                "img_p": "<Nếu KHÔNG MỚI TẠO nối thì tiếp>", 
                "vid_p": "<Nếu Audio: EXACT Maintain NO Start [prod_dna]. \\"[dialogue]\\" anchor. as exactly final frame from geometry, holding image, morphing. nối product provided reference steady tiếp:>"
            }}
        ]
    }}
    Lưu ý: Các "dur" CHỈ ĐƯỢC LÀ "4s", "6s", "8s". KHÔNG DÙNG DẤU NGOẶC KÉP CHƯA ESCAPE TRONG JSON. Cảnh cuối cùng mới được chốt đơn!
    """
    res = call_gemini([prompt], get_sys_inst_details(mode, style, narrator_mode, char_rules, num_chars, duration_instruction))
    if not res or "scenes" not in res: raise Exception("AI JSON Error.")
    st.session_state.generated_details[target_id] = res

def clone_script(script_id):
    mode = st.session_state.get("last_mode", "Bán Hàng")
    style = st.session_state.get("last_style", "Điện ảnh")
    narrator = st.session_state.get("last_narrator", "On-camera")
    char_rules = generate_char_rules_string(st.session_state.get("character_profiles", []))
    
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if sc["id"] == script_id), None)
    cur_len = len(all_combined)
    num_chars = target.get("actors", target.get("actor_count", 1))
    
    dna_str = json.dumps(st.session_state.content_analysis, ensure_ascii=False) if st.session_state.content_analysis else "N/A"
    
    prompt = f"""
    DỮ LIỆU GỐC: {dna_str}
    Nhân bản kịch bản gốc: {json.dumps(target, ensure_ascii=False)}. 
    Dựa BẮT BUỘC vào dữ liệu Gốc ở trên, tạo chính xác 5 biến thể mới. 
    YÊU CẦU ĐẶC BIỆT: Lời thoại tóm tắt phải CỰC KỲ dân dã, đời thường. Xưng "anh chị", "chị em", "anh em". KHÔNG nhắc thời tiết/mùa. KHÔNG xưng "Mấy bạn". LÁCH MỌI TỪ KHÓA BỊ CẤM.
    BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON GỒM CÁC KEY SAU:
    {{
        "outlines": [
            {{
                "id": {cur_len+1},
                "title": "Tên kịch bản",
                "setting": "Bối cảnh thực tế",
                "hook": "Gọi tên khách hàng tự nhiên & Hook dẫn dắt tâm lý đời thường (KHÔNG CTA, KHÔNG nói cụt lủn)",
                "actors": {num_chars}
            }}
        ]
    }}
    LƯU Ý: TRẢ VỀ ĐÚNG 5 PHẦN TỬ TRONG MẢNG `outlines`. KHÔNG DÙNG DẤU NGOẶC KÉP CHƯA ESCAPE.
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, narrator, char_rules, num_chars))
    if not res or ("outlines" not in res and "script_outlines" not in res): raise Exception("AI JSON Error.")
    clones = res.get("outlines", res.get("script_outlines", []))
    for idx, cl in enumerate(clones): cl["id"] = cur_len + idx + 1
    return clones

def generate_more_scripts(angle, num_chars, extra_char_inputs, narrator_mode_more):
    mode = st.session_state.get("last_mode", "Bán Hàng")
    style = st.session_state.get("last_style", "Điện ảnh")
    char_rules = generate_char_rules_string(st.session_state.get("character_profiles", []))
    cur_len = len(st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts)
    
    prod_ctx = f"INPUT: {st.session_state.current_input_context}"
    db_ctx = f"DB: {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)}" if st.session_state.current_product_data_saved else ""
    dna_ctx = f"DNA: {json.dumps(st.session_state.content_analysis, ensure_ascii=False)}" if st.session_state.content_analysis else ""
    
    prompt = f"""
    {prod_ctx} | {db_ctx} | {dna_ctx}

    🛑 CRITICAL STRATEGY OVERRIDE: '{angle}'. 
    Bạn PHẢI viết 5 kịch bản mới TUÂN THỦ TUYỆT ĐỐI chiến lược này. Bẻ giọng điệu sao cho phù hợp với '{angle}'.

    SỐ DIỄN VIÊN: CHÍNH XÁC {num_chars}.
    LUẬT: Lách từ cấm 100%. Lời thoại DÂN DÃ, ĐỜI THƯỜNG, ĐẦY ĐỦ CHỦ VỊ. Xưng "anh chị", "chị em", "anh em". Không nói cụt lủn hô khẩu hiệu. CẤM NHẮC THỜI TIẾT MÁY MÓC.

    STRICT JSON:
    {{
        "outlines": [
            {{
                "id": {cur_len+1},
                "title": "...",
                "setting": "...",
                "hook": "Gọi tên KH & Hook tâm lý mượt mà (Không có CTA ở cảnh 1), CHUẨN XÁC CHIẾN LƯỢC",
                "actors": {num_chars}
            }}
        ]
    }}
    """
    payload = []
    if extra_char_inputs:
        for c in extra_char_inputs:
            payload.append(f"ACTOR {c['id']} ({c['role']}):")
            payload.append(types.Part.from_bytes(data=c["bytes"], mime_type=c["mime_type"]))
    payload.append(prompt)
    
    res = call_gemini(payload, get_sys_inst_outlines(mode, style, narrator_mode_more, char_rules, num_chars))
    if not res or ("outlines" not in res and "script_outlines" not in res): raise Exception("AI JSON Error.")
    more_scripts = res.get("outlines", res.get("script_outlines", []))
    for idx, sc in enumerate(more_scripts): sc["id"] = cur_len + idx + 1
    return more_scripts

def save_project_to_db(email, title, payload_data, project_id=None):
    if not supabase: return "Chưa kết nối Database Supabase."
    try:
        clean_content = json.loads(json.dumps(payload_data, default=str)) 
        if project_id:
            supabase.table("saved_projects").update({
                "project_title": title,
                "script_content": clean_content
            }).eq("id", project_id).execute()
        else:
            data = {"user_email": email, "project_title": title, "script_content": clean_content}
            res = supabase.table("saved_projects").insert(data).execute()
            if res.data and len(res.data) > 0:
                st.session_state.current_project_id = res.data[0]['id']
        return True
    except Exception as e:
        err_msg = str(e)
        if "Name or service not known" in err_msg or "Errno -2" in err_msg:
            return "Sai link Supabase (thiếu https://) trong Secrets."
        return err_msg

# ==============================================================================
# 3. THANH BÊN (SIDEBAR) & TÀI KHOẢN (AUTH & LEAD GEN)
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        tabs = st.tabs(["🔐 Đăng Nhập", "🚀 Đăng Ký"])
        
        with tabs[0]:
            with st.form("login_form", border=False):
                email_input = st.text_input("Email:", placeholder="Nhập email của bạn...", key="login_email_input")
                pass_input = st.text_input("Mật khẩu:", type="password", placeholder="Nhập mật khẩu...", key="login_pass_input")
                submitted = st.form_submit_button("🔑 Đăng Nhập", type="primary", use_container_width=True)
            
            if submitted:
                ph = st.empty()
                ph.markdown("<div style='background: #eff6ff; border: 1px solid #93c5fd; padding: 8px; border-radius: 8px; color: #1e3a8a; text-align: center; font-weight: bold;'>⏳ Đang xác thực...</div>", unsafe_allow_html=True)
                email_check = email_input.strip()
                pass_check = pass_input.strip()
                
                if email_check in st.session_state.licensed_accounts:
                    acc_info = st.session_state.licensed_accounts[email_check]
                    
                    if acc_info.get("password") == pass_check or email_check == ADMIN_EMAIL:
                        exp_date_str = acc_info.get("expires_at", "2099-12-31")
                        try:
                            exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
                            if datetime.now() > exp_date:
                                ph.empty()
                                st.error(f"❌ Tài khoản đã hết hạn vào ngày {exp_date_str}! Vui lòng liên hệ Admin để gia hạn.")
                                st.stop()
                        except: pass
                        st.session_state.is_logged_in = True
                        st.session_state.current_email = email_check
                        st.toast("✅ Đăng nhập thành công!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        ph.empty()
                        st.error("Sai mật khẩu!")
                else: 
                    ph.empty()
                    st.error("Tài khoản chưa được cấp quyền!")
                    
        with tabs[1]:
            st.markdown("<p style='font-size: 13px; color: #475569;'>Đăng ký tài khoản để trải nghiệm toàn bộ sức mạnh của Đạo diễn AI (Tặng 3 ngày trải nghiệm, 5 lượt/ngày).</p>", unsafe_allow_html=True)
            with st.form("register_form", border=False):
                reg_email = st.text_input("Email đăng ký:", placeholder="Nhập email...")
                reg_phone = st.text_input("Số điện thoại (Bắt buộc):", placeholder="Nhập SĐT có Zalo...")
                reg_pass = st.text_input("Mật khẩu mới:", type="password", placeholder="Tạo mật khẩu...")
                reg_submitted = st.form_submit_button("🚀 Đăng Ký Tài Khoản", type="secondary", use_container_width=True)
            
            if reg_submitted:
                ph_reg = st.empty()
                ph_reg.markdown("<div style='background: #eff6ff; border: 1px solid #93c5fd; padding: 8px; border-radius: 8px; color: #1e3a8a; text-align: center; font-weight: bold;'>⏳ Đang khởi tạo tài khoản...</div>", unsafe_allow_html=True)
                email_check = reg_email.strip()
                if email_check in st.session_state.licensed_accounts:
                    ph_reg.empty()
                    st.error("Email này đã tồn tại trong hệ thống!")
                elif not email_check or not reg_phone.strip() or not reg_pass.strip():
                    ph_reg.empty()
                    st.error("Vui lòng điền đầy đủ thông tin!")
                else:
                    exp_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                    st.session_state.licensed_accounts[email_check] = {
                        "roles": ALL_MODULES,
                        "phone": reg_phone.strip(),
                        "password": reg_pass.strip(),
                        "expires_at": exp_date,
                        "is_trial": True,
                        "daily_usage_count": 0,
                        "last_generation_date": ""
                    }
                    save_licensed_accounts(st.session_state.licensed_accounts)
                    st.session_state.is_logged_in = True
                    st.session_state.current_email = email_check
                    st.toast("✅ Đăng ký tài khoản thành công!")
                    time.sleep(0.5)
                    st.rerun()
    else:
        current_acc = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        exp_date_str = current_acc.get("expires_at", "2099-12-31")
        is_trial = current_acc.get("is_trial", False)
        
        # Chỉ hiện cảnh báo sắp hết hạn cho KHÁCH VIP
        if current_acc and st.session_state.current_email != ADMIN_EMAIL and not is_trial:
            try:
                exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
                days_left = (exp_date - datetime.now()).days
                if 0 <= days_left <= 7:
                    st.warning(f"⚠️ **CẢNH BÁO:** Tài khoản của bạn sẽ hết hạn sau **{days_left} ngày nữa** ({exp_date_str}). Liên hệ hotline để gia hạn!")
            except: pass

        st.markdown("### 🗂 LÀM VIỆC")
        btn_new_proj_ph = st.empty()
        new_proj_key = "loading_new_proj"
        if new_proj_key not in st.session_state: st.session_state[new_proj_key] = False
        
        if st.session_state[new_proj_key]:
            st.markdown("<div style='background: #eff6ff; border: 1px solid #93c5fd; padding: 8px; border-radius: 8px; color: #1e3a8a; text-align: center; font-weight: bold;'>⏳ Đang khởi tạo dự án mới...</div>", unsafe_allow_html=True)
            lock_ui()
            st.session_state.all_scripts, st.session_state.cloned_scripts, st.session_state.expanded_scripts = [], [], []
            st.session_state.generated_details, st.session_state.content_analysis = {}, None
            st.session_state.active_script_id = None
            st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
            st.session_state.current_input_context = ""
            st.session_state.current_product_data_saved = None
            st.session_state.character_profiles = []
            st.session_state.current_project_id = None
            st.session_state.reset_key += 1 
            st.session_state[new_proj_key] = False
            st.toast("✅ Đã dọn dẹp và mở dự án mới sạch sẽ!")
            time.sleep(0.5)
            st.rerun()
        else:
            if btn_new_proj_ph.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True):
                st.session_state[new_proj_key] = True
                st.rerun()
            
        st.session_state.active_project_title = st.text_input("Tên dự án hiện tại:", placeholder="VD: Chiến dịch Tháng 10...", value=st.session_state.active_project_title)
        
        btn_save_proj_ph = st.empty()
        save_proj_key = "loading_save_proj"
        if save_proj_key not in st.session_state: st.session_state[save_proj_key] = False
        
        if st.session_state[save_proj_key]:
            st.markdown("<div style='background: #eff6ff; border: 1px solid #93c5fd; padding: 8px; border-radius: 8px; color: #1e3a8a; text-align: center; font-weight: bold;'>⏳ Đang lưu dữ liệu lên Cloud...</div>", unsafe_allow_html=True)
            lock_ui()
            all_com = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
            if not all_com: st.warning("⚠️ Chưa có kịch bản nào để lưu!")
            else:
                payload = {
                    "content_analysis": st.session_state.content_analysis,
                    "all_scripts": st.session_state.all_scripts,
                    "cloned_scripts": st.session_state.cloned_scripts,
                    "expanded_scripts": st.session_state.expanded_scripts,
                    "generated_details": st.session_state.generated_details,
                    "character_profiles": st.session_state.character_profiles,
                    "current_input_context": st.session_state.current_input_context,
                    "target_duration_instruction": st.session_state.target_duration_instruction
                }
                save_result = save_project_to_db(st.session_state.current_email, st.session_state.active_project_title, payload, st.session_state.current_project_id)
                if save_result is True: st.toast("✅ Đã cập nhật và lưu dự án thành công!")
                else: st.error(f"❌ {save_result}")
            st.session_state[save_proj_key] = False
            time.sleep(0.5)
            st.rerun()
        else:
            if btn_save_proj_ph.button("💾 Lưu Dự Án Này", use_container_width=True):
                st.session_state[save_proj_key] = True
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📂 KHO LƯU TRỮ")
        if not supabase: st.error("Chưa kết nối Database.")
        else:
            try:
                if st.session_state.current_email == ADMIN_EMAIL: res = supabase.table("saved_projects").select("*").order("created_at", desc=True).execute()
                else: res = supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
                projects = res.data
            except: projects = []

            search_proj = st.text_input("🔍 Tìm kiếm dự án:", placeholder="Nhập tên hoặc ngày...", key="search_proj_input")
            if search_proj:
                projects = [p for p in projects if search_proj.lower() in p['project_title'].lower() or search_proj in p['created_at']]

            if not projects: st.info("Không tìm thấy dự án phù hợp.")
            else:
                st.markdown("<div class='scrollable-sidebar-container'>", unsafe_allow_html=True)
                for p in projects:
                    with st.expander(f"🎬 {p['project_title']}"):
                        st.caption(f"📅 {p['created_at'][:10]}")
                        if st.session_state.current_email == ADMIN_EMAIL: st.caption(f"👤 Tạo bởi: {p['user_email']}")
                        
                        col_open, col_del = st.columns(2)
                        with col_open:
                            btn_open_ph = st.empty()
                            open_state_key = f"open_loading_{p['id']}"
                            if open_state_key not in st.session_state: st.session_state[open_state_key] = False
                            
                            if st.session_state[open_state_key]:
                                st.markdown("<div style='background: #eff6ff; border: 1px solid #93c5fd; padding: 4px; border-radius: 4px; color: #1e3a8a; text-align: center; font-size: 12px; font-weight: bold;'>⏳ Khôi phục...</div>", unsafe_allow_html=True)
                                lock_ui()
                                saved_data = p.get("script_content", {})
                                if isinstance(saved_data, dict) and "all_scripts" in saved_data:
                                    st.session_state.content_analysis = saved_data.get("content_analysis")
                                    st.session_state.all_scripts = saved_data.get("all_scripts", [])
                                    st.session_state.cloned_scripts = saved_data.get("cloned_scripts", [])
                                    st.session_state.expanded_scripts = saved_data.get("expanded_scripts", [])
                                    raw_details = saved_data.get("generated_details", {})
                                    st.session_state.generated_details = {int(k): v for k, v in raw_details.items()} if raw_details else {}
                                    st.session_state.character_profiles = saved_data.get("character_profiles", [])
                                    st.session_state.current_input_context = saved_data.get("current_input_context", "")
                                    st.session_state.target_duration_instruction = saved_data.get("target_duration_instruction", "")
                                elif isinstance(saved_data, list):
                                    st.session_state.all_scripts = saved_data
                                    st.session_state.content_analysis = None
                                    st.session_state.cloned_scripts = []
                                    st.session_state.expanded_scripts = []
                                    st.session_state.generated_details = {}
                                
                                st.session_state.current_project_id = p['id']
                                st.session_state.active_project_title = p['project_title']
                                st.session_state.active_script_id = None
                                st.session_state.reset_key += 1
                                st.session_state.scroll_to_top = True
                                st.session_state[open_state_key] = False
                                st.toast("✅ Đã khôi phục dự án!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                if btn_open_ph.button("📂 Mở", key=f"open_{p['id']}", use_container_width=True):
                                    st.session_state[open_state_key] = True
                                    st.rerun()
                                    
                        with col_del:
                            btn_del_ph = st.empty()
                            del_state_key = f"del_loading_{p['id']}"
                            if del_state_key not in st.session_state: st.session_state[del_state_key] = False
                            
                            if st.session_state[del_state_key]:
                                st.markdown("<div style='background: #fef2f2; border: 1px solid #f87171; padding: 4px; border-radius: 4px; color: #991b1b; text-align: center; font-size: 12px; font-weight: bold;'>⏳ Đang xóa...</div>", unsafe_allow_html=True)
                                lock_ui()
                                supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                                st.session_state[del_state_key] = False
                                st.toast("✅ Đã xóa dự án!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                if btn_del_ph.button("🗑️ Xóa", key=f"del_{p['id']}", type="secondary", use_container_width=True):
                                    st.session_state[del_state_key] = True
                                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.current_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙ QUẢN TRỊ ADMIN")
            
            st.markdown("##### 🚨 Thông Báo & Cảnh Báo")
            expired_or_soon = []
            for acc, info in st.session_state.licensed_accounts.items():
                if acc == ADMIN_EMAIL: continue
                exp_str = info.get("expires_at", "2099-12-31")
                is_trial_user = info.get("is_trial", False)
                today_str = datetime.now().strftime("%Y-%m-%d")
                usage = info.get("daily_usage_count", 0) if info.get("last_generation_date") == today_str else 0
                
                try:
                    exp_dt = datetime.strptime(exp_str, "%Y-%m-%d")
                    d_left = (exp_dt - datetime.now()).days
                    if d_left <= 7 or (is_trial_user and usage >= 5): 
                        expired_or_soon.append((acc, info, d_left, exp_str, usage))
                except: pass
            
            if expired_or_soon:
                for cust, info, d_left, exp_str, usage in expired_or_soon:
                    is_trial_user = info.get("is_trial", False)
                    phone = info.get('phone', '')
                    
                    if d_left < 0: status_text = f"Đã quá hạn {abs(d_left)} ngày"
                    elif d_left == 0: status_text = "Hết hạn hôm nay!"
                    else: status_text = f"Còn {d_left} ngày"
                    
                    alert_reason = "⚠️ " + status_text
                    if is_trial_user and usage >= 5:
                        alert_reason += " | 🔥 ĐÃ DÙNG HẾT LƯỢT TRONG NGÀY"
                    
                    with st.container(border=True):
                        st.markdown(f"**👤 {cust}** <span style='font-size: 11px; padding: 2px 6px; background: {'#fde047' if is_trial_user else '#86efac'}; border-radius: 4px; font-weight: bold;'>{'TRIAL' if is_trial_user else 'VIP'}</span>", unsafe_allow_html=True)
                        st.caption(f"📞 SĐT: {phone or 'Chưa có'} | 🔑 Pass: `{info.get('password', 'N/A')}`<br><b style='color:#d90429;'>{alert_reason}</b>", unsafe_allow_html=True)
                        if phone:
                            clean_phone = re.sub(r'\D', '', phone)
                            st.markdown(f"<a href='[https://zalo.me/](https://zalo.me/){clean_phone}' target='_blank' style='background:#0068ff; color:white; padding:5px 12px; border-radius:6px; text-decoration:none; font-size:12px; font-weight:700; display:inline-block; margin-top:5px;'>💬 Nhắn Zalo Chốt Sale</a>", unsafe_allow_html=True)
            else: st.caption("✅ Không có cảnh báo nào.")
            
            st.markdown("---")
            with st.form("add_license"):
                st.markdown("##### ➕ Cấp Quyền Khách Hàng Mới")
                new_acc = st.text_input("Email khách hàng:")
                new_phone = st.text_input("Số điện thoại (SĐT):")
                new_pass = st.text_input("Mật khẩu:", value="123456")
                acc_type = st.radio("Loại Tài Khoản:", ["Gói VIP (Không giới hạn)", "Dùng thử (Giới hạn 5 lần/ngày)"], index=0)
                assigned_modules = st.multiselect("Phân quyền thể loại:", options=ALL_MODULES, default=ALL_MODULES)
                duration_opt = st.selectbox("Thời hạn:", ["1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "3 Ngày (Dùng thử)", "Vĩnh viễn (Trọn đời)"])
                btn_add_lic = st.form_submit_button("💾 Cấp Quyền & Lưu")
                if btn_add_lic:
                    with st.spinner("⏳ Đang cấp quyền..."):
                        is_trial = "Dùng thử" in acc_type
                        days_add = 3 if is_trial else {"1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "Vĩnh viễn (Trọn đời)": 3650}.get(duration_opt, 30)
                        exp_date = "2099-12-31" if "Vĩnh viễn" in duration_opt else (datetime.now() + timedelta(days=days_add)).strftime("%Y-%m-%d")
                        
                        st.session_state.licensed_accounts[new_acc.strip()] = {
                            "roles": assigned_modules, "phone": new_phone.strip(), "password": new_pass.strip(), 
                            "expires_at": exp_date, "is_trial": is_trial, "daily_usage_count": 0, "last_generation_date": ""
                        }
                        save_licensed_accounts(st.session_state.licensed_accounts)
                        st.toast(f"✅ Đã lưu thông tin cho {new_acc}!")
                        time.sleep(0.5)
                        st.rerun()
            
            search_cust = st.text_input("🔍 Tìm kiếm khách hàng:", placeholder="Nhập Email hoặc SĐT", key="search_cust_input")
            filtered_accs = list(st.session_state.licensed_accounts.items())
            if search_cust: filtered_accs = [(acc, info) for acc, info in filtered_accs if search_cust.lower() in acc.lower() or search_cust in str(info.get('phone', ''))]

            if filtered_accs:
                st.markdown(f"##### 📋 Danh sách Khách hàng ({len(filtered_accs)})")
                st.markdown("<div class='scrollable-sidebar-container'>", unsafe_allow_html=True)
                for acc, info in filtered_accs:
                    with st.container(border=True):
                        is_trial = info.get("is_trial", False)
                        st.markdown(f"**👤 {acc}** <span style='font-size: 11px; padding: 2px 6px; background: {'#fde047' if is_trial else '#86efac'}; border-radius: 4px; font-weight: bold;'>{'TRIAL' if is_trial else 'VIP'}</span>", unsafe_allow_html=True)
                        phone_val = info.get('phone', '')
                        pass_val = info.get('password', '')
                        roles_val = info.get('roles', ALL_MODULES)
                        exp_val = info.get('expires_at', '2099-12-31')
                        today_str = datetime.now().strftime("%Y-%m-%d")
                        usage = info.get("daily_usage_count", 0) if info.get("last_generation_date") == today_str else 0
                        
                        st.caption(f"📞 SĐT: {phone_val or 'Chưa có'} | 🔑 Pass: `{pass_val}`<br>• Quyền: {', '.join(roles_val)}<br>• Hết hạn: {exp_val} <br>• Lượt dùng hôm nay: {usage}/5", unsafe_allow_html=True)
                        
                        col_up, col_del = st.columns(2)
                        with col_up:
                            if st.button("✏️ Sửa", key=f"edit_acc_{acc}", use_container_width=True):
                                st.session_state.editing_acc_email = acc
                                st.rerun()
                        with col_del:
                            if st.button("🗑 Xóa", key=f"del_acc_{acc}", type="secondary", use_container_width=True):
                                lock_ui()
                                del st.session_state.licensed_accounts[acc]
                                save_licensed_accounts(st.session_state.licensed_accounts)
                                st.toast("✅ Đã xóa tài khoản!")
                                time.sleep(0.5)
                                st.rerun()
                        
                        if st.session_state.get("editing_acc_email") == acc:
                            with st.form(f"update_form_{acc}" ):
                                st.markdown(f"**Cập nhật cho: {acc}**")
                                upd_phone = st.text_input("SĐT mới:", value=phone_val)
                                upd_pass = st.text_input("Mật khẩu:", value=pass_val)
                                upd_trial = st.checkbox("Là tài khoản Dùng thử (Giới hạn 5 lượt/ngày)", value=is_trial)
                                upd_roles = st.multiselect("Phân quyền thể loại:", options=ALL_MODULES, default=roles_val)
                                upd_exp = st.text_input("Ngày hết hạn (YYYY-MM-DD):", value=exp_val)
                                btn_save_upd = st.form_submit_button("💾 Lưu Cập Nhật")
                                if btn_save_upd:
                                    with st.spinner("⏳ Đang lưu..."):
                                        st.session_state.licensed_accounts[acc].update({
                                            "roles": upd_roles, "phone": upd_phone.strip(), "password": upd_pass.strip(), 
                                            "expires_at": upd_exp.strip(), "is_trial": upd_trial
                                        })
                                        save_licensed_accounts(st.session_state.licensed_accounts)
                                        st.session_state.editing_acc_email = None
                                        st.toast("✅ Đã cập nhật tài khoản thành công!")
                                        time.sleep(0.5)
                                        st.rerun()
                    st.markdown("---")
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div class="support-box">
            <b style="color: #166534; font-size: 0.95rem;">💬 Cần Hỗ Trợ / Mua Gói?</b><br>
            <p style="font-size: 0.85rem; color: #15803d; margin: 6px 0 8px 0;">Kết nối ngay với chúng tôi:</p>
            <div class="social-icons-container">
                <a href="[https://zalo.me/0968484369](https://zalo.me/0968484369)" target="_blank" class="btn-zalo">Zalo</a>
                <a href="[https://facebook.com/](https://facebook.com/)" target="_blank" class="btn-fb">f</a>
                <a href="[https://tiktok.com/](https://tiktok.com/)" target="_blank" class="btn-tt">♪</a>
            </div>
            <div style="font-weight: 700; color: #166534; font-size: 12px; margin-top: 8px;">📞 Hotline: 0968.484.369</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🔐 Thông Tin Tài Khoản")
        
        user_info = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        if st.session_state.current_email == ADMIN_EMAIL:
            st.success("Tài khoản: ADMIN (Không giới hạn)")
        elif user_info.get("is_trial", False):
            today_str = datetime.now().strftime("%Y-%m-%d")
            used = user_info.get("daily_usage_count", 0) if user_info.get("last_generation_date") == today_str else 0
            st.info(f"**GÓI TRẢI NGHIỆM TÂN THỦ**\n\n• Email: {st.session_state.current_email}\n• Đã dùng: **{used}/5** lượt hôm nay\n• Hết hạn: {user_info.get('expires_at')}")
        else:
            st.success(f"**GÓI VIP** (Không giới hạn)\n\n• Email: {st.session_state.current_email}\n• Hết hạn: {user_info.get('expires_at')}")

        btn_logout_ph = st.empty()
        logout_key = "loading_logout"
        if logout_key not in st.session_state: st.session_state[logout_key] = False
        
        if st.session_state[logout_key]:
            st.markdown("<div style='background: #eff6ff; border: 1px solid #93c5fd; padding: 8px; border-radius: 8px; color: #1e3a8a; text-align: center; font-weight: bold;'>⏳ Đang thoát...</div>", unsafe_allow_html=True)
            lock_ui()
            st.session_state.is_logged_in = False
            st.session_state[logout_key] = False
            st.toast("✅ Đăng xuất!")
            time.sleep(0.5)
            st.rerun()
        else:
            if btn_logout_ph.button("🚪 Đăng Xuất"):
                st.session_state[logout_key] = True
                st.rerun()

if not st.session_state.is_logged_in:
    st.info("👈 Vui lòng đăng nhập hoặc đăng ký ở thanh công cụ bên trái.")
    st.stop()

# ==============================================================================
# 5. KHÔNG GIAN SÁNG TẠO CHÍNH
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div></div>""", unsafe_allow_html=True)

current_acc_info = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
allowed_categories = [m for m in ALL_MODULES if m in current_acc_info.get("roles", ALL_MODULES)]
if not allowed_categories: allowed_categories = ALL_MODULES

st.markdown("### ⚙ THIẾT LẬP THỂ LOẠI & DỮ LIỆU ĐẦU VÀO")
mode = st.selectbox("🎯 Thể loại (Đã được phân quyền):", allowed_categories, key=f"mode_sel_{st.session_state.reset_key}")
is_viral_mode = "Viral" in mode

up_files = []
custom_note = ""

if is_viral_mode:
    st.markdown("#### 🌟 Thông tin Kênh & Chủ đề")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        viral_persona = st.text_input("👤 Định vị Kênh / Người nói (Tùy chọn):", placeholder="Nhập định vị (VD: Bác sĩ da liễu, Mẹ bỉm sữa 3 con, Góc nhìn GenZ...)", key=f"viral_persona_{st.session_state.reset_key}")
    with col_v2:
        viral_topic = st.text_area("💡 Chủ đề Video / Mẹo muốn chia sẻ:", placeholder="Nhập thông tin, yêu cầu chi tiết, hoặc ý tưởng cụ thể của bạn vào đây...", height=68, key=f"viral_topic_{st.session_state.reset_key}")
    
    with st.expander("📎 Dữ liệu bổ sung (Upload Ảnh Tham chiếu / Ghi chú đặc biệt) - KHÔNG BẮT BUỘC"):
        up_files = st.file_uploader("📦 Upload Ảnh Tham chiếu (Bối cảnh/Đồ vật - Tùy chọn):", type=["jpg", "png"], accept_multiple_files=True, key=f"up_main_files_v_{st.session_state.reset_key}")
        custom_note = st.text_area("✍ Ghi chú kịch bản / Ý tưởng cụ thể (Tùy chọn):", placeholder="Nhập thông tin, yêu cầu chi tiết, hoặc ý tưởng cụ thể của bạn vào đây...", key=f"note_main_v_{st.session_state.reset_key}")
else:
    st.markdown("#### 🛒 Nhập thông tin sản phẩm")
    if supabase:
        try: products_data = supabase.table("products").select("*").execute().data
        except: products_data = []
        
        if products_data:
            prod_names = [p["product_name"] for p in products_data]
            selected_name = st.selectbox("📌 Chọn sản phẩm từ Database:", options=prod_names, key=f"select_prod_main_{st.session_state.reset_key}")
            st.session_state.current_product_data = next(p for p in products_data if p["product_name"] == selected_name)
            prod = st.session_state.current_product_data
            
            with st.container(border=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**💰 Hoa hồng:** <span style='color:#15803d; font-weight:900;'>{prod.get('commission_percent', 0)}%</span>", unsafe_allow_html=True)
                    st.markdown(f"**🎯 Tệp khách hàng:** {prod.get('target_audience', '')}")
                with col_b:
                    st.markdown(f"**🧠 Insight:** {prod.get('product_insight', '')}")
                    st.markdown(f"**💔 Nỗi đau:** {prod.get('pain_points', '')}")

    st.markdown("<br>", unsafe_allow_html=True)
    up_files = st.file_uploader("📦 Upload Ảnh SP / Bối cảnh (Sẽ được AI giữ nguyên màu/thiết kế 100%):", type=["jpg", "png"], accept_multiple_files=True, key=f"up_main_files_s_{st.session_state.reset_key}")
    custom_note = st.text_area("✍ Ghi chú đặc biệt cho AI (Tùy chọn):", placeholder="Nhập yêu cầu nhấn mạnh tính năng, kịch bản mẫu, hoặc ý tưởng cụ thể của bạn vào đây...", key=f"note_main_s_{st.session_state.reset_key}")

st.markdown("---")
st.markdown("### 🎥 Đạo Diễn, Góc Quay & Thời Lượng")
col_opt1, col_opt2 = st.columns(2)

with col_opt1:
    style = st.selectbox("🎨 Phong cách hình ảnh:", ["Điện Ảnh Chân Thực", "Hoạt Hình 3D", "Hoạt Hình 2D / Anime", "Studio Tối Giản"], key=f"style_sel_{st.session_state.reset_key}")
    
    if is_viral_mode:
        angle_options = [
            "🌟 Tự động (AI tự phân tích và mix đa dạng nội dung viral)", 
            "🧠 Chia sẻ kiến thức / Chuyên gia", 
            "💡 Mẹo hay / Life hack", 
            "🎭 Tình huống Drama / Gây tranh cãi", 
            "📖 Kể chuyện (Storytelling) / Truyền cảm hứng",
            "😂 Tình huống hài hước / Giải trí"
        ]
    else:
        angle_options = [
            "🌟 Tự động (AI tự phân tích và mix 5 góc độ đa dạng, tối ưu nhất)", 
            "⚡ Flash Sale & Deal hời (Tập trung chốt đơn)", 
            "🎭 Tình huống đời sống / Nỗi đau (PAS)", 
            "🔍 Review thực chiến", 
            "💡 Mẹo vặt / Chia sẻ (Lồng ghép sản phẩm)", 
            "😂 Tình huống hài hước (Chốt sale bất ngờ)"
        ]
        
    initial_angle = st.selectbox("🧭 Định hướng chiến lược (Ban đầu):", angle_options, key=f"init_angle_{st.session_state.reset_key}")

with col_opt2:
    duration_choice = st.selectbox("⏳ Thời lượng video:", ["Tự động (AI Tối ưu ~20-30s)", "Tùy chỉnh (Nhập số giây)"], key=f"dur_choice_{st.session_state.reset_key}")
    if duration_choice.startswith("Tùy chỉnh"):
        custom_seconds = st.number_input("Nhập số giây mong muốn:", min_value=10, max_value=300, value=60, step=5, key=f"dur_sec_{st.session_state.reset_key}")
        st.session_state.target_duration_instruction = f"TỔNG THỜI LƯỢNG YÊU CẦU: Chính xác {custom_seconds} giây. Bạn PHẢI tạo ra số lượng phân cảnh đủ nhiều (mỗi cảnh 4s, 6s, 8s) sao cho tổng thời gian cộng lại bằng ĐÚNG {custom_seconds} giây."
    else:
        st.session_state.target_duration_instruction = "TỔNG THỜI LƯỢNG YÊU CẦU: Tự động (Khoảng 3 đến 5 phân cảnh, tổng 15-30 giây)."

    narrator_mode = st.selectbox("🎙 Thuyết minh & Nhân vật:", ["Nhân vật xuất hiện nói chuyện (On-camera, Lip-sync)", "🎙 Lồng tiếng ngoài (Off-screen, Show sản phẩm)"], key=f"narrator_sel_{st.session_state.reset_key}")

num_chars = st.number_input("👤 Số lượng Diễn viên (Tối đa 8):", min_value=1, max_value=8, value=1, step=1, key=f"num_chars_main_{st.session_state.reset_key}")

st.markdown("<br>", unsafe_allow_html=True)

# THÔNG TIN DIỄN VIÊN
char_inputs = []
if num_chars > 0:
    st.markdown("#### 👤 Thông tin Diễn viên (Avatar/Khuôn mặt)")
    for i in range(num_chars):
        col_role, col_img = st.columns([2, 1])
        with col_role:
            c_role = st.text_input(f"Vai trò NV {i+1} (Tùy chọn):", key=f"role_{i}_{st.session_state.reset_key}", placeholder="Nhập vai trò (VD: Bác sĩ, Khách hàng...) Hoặc để trống để AI tự phân tích")
        with col_img:
            c_file = st.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"file_{i}_{st.session_state.reset_key}", label_visibility="collapsed")
        
        if c_file:
            role_val = c_role.strip() if c_role.strip() else "AI tự phân tích dựa theo ngữ cảnh và ảnh"
            char_inputs.append({"id": i+1, "role": role_val, "file": c_file})
    st.markdown("<br>", unsafe_allow_html=True)

# ==================== NÚT TẠO KỊCH BẢN CHÍNH ====================
btn_gen_main_ph = st.empty()
gen_main_key = "loading_gen_main"
if gen_main_key not in st.session_state: st.session_state[gen_main_key] = False

if st.session_state[gen_main_key]:
    st.markdown("<div style='background: #fff0f2; border: 1.5px solid #ffa4b4; padding: 14px; border-radius: 8px; color: #d90429; text-align: center; font-size: 16px; font-weight: bold;'>⏳ Đạo diễn AI đang phân tích dữ liệu, tâm lý và sinh kịch bản... Vui lòng đợi!</div>", unsafe_allow_html=True)
    lock_ui()
    try:
        st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
        char_rules = generate_char_rules_string(st.session_state.character_profiles)
        
        st.session_state.last_mode = mode
        st.session_state.last_style = style
        st.session_state.last_narrator = narrator_mode
        st.session_state.current_input_context = custom_note
        
        if is_viral_mode:
            st.session_state.current_product_data_saved = {
                "Định vị Kênh / Người nói": viral_persona,
                "Chủ đề Video": viral_topic
            }
        else:
            st.session_state.current_product_data_saved = st.session_state.get("current_product_data")
            
        st.session_state.current_project_id = None
        
        time_ctx = get_dynamic_realtime_context(mode)
        prod_ctx = f"INPUT DATA: {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)}" if st.session_state.current_product_data_saved else ""
        
        angle_str = initial_angle
        num_c = num_chars
        
        prompt = f"""
        {time_ctx}
        {prod_ctx}
        NOTES: {custom_note}
        
        STRICT JSON REQUIRED:
        {{
            "content_analysis": {{
                "target_audience": "Nhận diện TỆP KHÁN GIẢ/KHÁCH HÀNG (VD: Nữ -> chị em, Nam -> anh em)",
                "core_value": "Giá trị cốt lõi / mechanical specs",
                "pain_points": "Nỗi đau khách hàng",
                "hook_element": "Yếu tố giữ chân / Mong muốn cốt lõi",
                "visual_rules": "Quy chuẩn vật lý & Bối cảnh",
                "prompt_dna_lock": "Khóa thị giác"
            }},
            "outlines": [ 
                {{
                    "id": 1, 
                    "title": "Tên kịch bản", 
                    "setting": "Bối cảnh thực tế", 
                    "hook": "HOOK BẮT BUỘC: Phân tích tệp KH để xưng hô (anh chị/chị em/anh em). Khơi gợi vấn đề tự nhiên. KHÔNG nhắc mua hàng/giỏ hàng ở đây. KHÔNG dùng 'Hội', 'Mấy bạn'.",
                    "actors": {num_c}
                }} 
            ]
        }}
        CREATE EXACTLY 5 SCRIPTS. STRATEGY: '{angle_str}'. INTERACTION FOR {num_c} ACTORS.
        """
        
        payload = []
        if up_files:
            payload.append("REFERENCE IMAGES:")
            for f in up_files: payload.append(types.Part.from_bytes(data=f.getvalue(), mime_type=f.type if f.type else "image/jpeg"))
        if char_inputs:
            for c in char_inputs:
                payload.append(f"ACTOR {c['id']} ({c['role']}):")
                payload.append(types.Part.from_bytes(data=c['file'].getvalue(), mime_type=c['file'].type if c['file'].type else "image/jpeg"))
        payload.append(prompt)
        
        res = call_gemini(payload, get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_c))
        
        if not res or ("outlines" not in res and "script_outlines" not in res):
            st.error("❌ AI không trả về đúng định dạng JSON. Vui lòng thử lại!")
        else:
            st.session_state.content_analysis = res.get("content_analysis")
            st.session_state.all_scripts = res.get("outlines", res.get("script_outlines", []))
            st.session_state.cloned_scripts = []
            st.session_state.expanded_scripts = []
            st.session_state.generated_details = {}
            st.session_state.active_script_id = None
            st.session_state.scroll_to_top = True
            st.toast("✅ Đã sinh xong 5 kịch bản và phân tích DNA!")
    except Exception as e:
        st.error(f"❌ Lỗi xử lý AI: {str(e)}")
        time.sleep(2)
    st.session_state[gen_main_key] = False
    st.rerun()
else:
    if btn_gen_main_ph.button("🚀 PHÂN TÍCH DNA & SINH 5 KỊCH BẢN ĐA VŨ TRỤ", type="primary", use_container_width=True):
        can_run, msg = check_usage_limit(st.session_state.current_email)
        if not can_run: st.error(f"❌ {msg}")
        else:
            st.session_state[gen_main_key] = True
            st.rerun()

# ==================== HIỂN THỊ PHÂN TÍCH DNA ====================
if st.session_state.content_analysis and isinstance(st.session_state.content_analysis, dict):
    st.divider()
    st.markdown(f"### 🔍 **Phân Tích DNA Chi Tiết Đa Tầng**")
    ca = st.session_state.content_analysis
    
    ca_target = ca.get('target_audience', ca.get('primary_target_audience', 'N/A'))
    ca_pain = ca.get('pain_points', ca.get('customer_pain_points', ca.get('audience_pain_points', 'N/A')))
    ca_core = ca.get('core_value', ca.get('mechanical_and_accessories', ca.get('core_value_or_message', 'N/A')))
    ca_visual = ca.get('visual_rules', ca.get('visual_physics_rules', 'N/A'))
    ca_hook = ca.get('hook_element', ca.get('core_desires', ca.get('viral_hook_element', 'N/A')))
    ca_usp = ca.get('usp', ca.get('emotional_or_usp_hook', 'N/A'))
    
    with st.container(border=True):
        st.markdown("##### 🎯 **1. Chân dung Khán giả & Vấn đề:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Tệp khán giả / khách hàng:</b> {format_analysis_field(ca_target)}<br>{format_analysis_field(ca_pain)}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 🏭 **2. Yếu tố Cốt lõi & Vật lý:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Giá trị / Thông số:</b> {format_analysis_field(ca_core)}<br>• <b>Vật lý & Bối cảnh:</b> {format_analysis_field(ca_visual)}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 💡 **3. Điểm thu hút & USP:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Mong muốn / Sự đồng cảm:</b> {format_analysis_field(ca_hook)}<br>• <b>USP / Hook:</b> {format_analysis_field(ca_usp)}</div>", unsafe_allow_html=True)
    st.markdown("##### 📌 **Chuỗi khóa thị giác (Visual DNA Lock):**")
    st.code(str(ca.get('prompt_dna_lock', 'N/A')), language="text")

# ==============================================================================
# 6. DANH SÁCH KỊCH BẢN & XEM CHI TIẾT
# ==============================================================================
all_combined_scripts_list = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts

if all_combined_scripts_list:
    st.divider()
    
    completed_scripts = [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) in st.session_state.generated_details]
    pending_scripts = [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) not in st.session_state.generated_details]

    if st.session_state.active_script_id is not None:
        btn_collapse_ph = st.empty()
        if btn_collapse_ph.button("⬅ Thu gọn và Quay lại danh sách tổng"):
            btn_collapse_ph.empty()
            st.session_state.active_script_id = None
            st.session_state.scroll_to_top = True
            st.rerun()
        
        active_sc = st.session_state.generated_details.get(st.session_state.active_script_id, {})
        if isinstance(active_sc, list): active_sc = active_sc[0] if active_sc else {}
        vp = active_sc.get("voice", active_sc.get("voice_profile", {}))
        if isinstance(vp, str): vp = {"gender": "Nữ", "tone": vp}
        
        # ĐÂY LÀ ĐIỂM NEO KHI AUTO-SCROLL
        st.markdown("<div id='detailed-view-anchor'></div>", unsafe_allow_html=True)
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(active_sc.get('title', 'KỊCH BẢN')).upper()}**")
        st.markdown(f"""
        <div class='detail-header-box'>
            ⏱ Thời lượng: <b>{active_sc.get('total_dur', active_sc.get('total_estimated_duration', '24s'))}</b> | 
            🎙 Giọng: <b>{vp.get('gender', 'Nữ')} ({vp.get('tone', 'nhịp độ chuẩn')})</b> | 
            👔 Trang phục & Bối cảnh: <b>{active_sc.get('outfit_vi', active_sc.get('script_outfit_setup', 'Mặc định'))}</b> | 
            📐 Khung hình: <b>{HARDCODED_ASPECT}</b>
        </div>
        """, unsafe_allow_html=True)
        
        scenes = active_sc.get("scenes", [])
        if isinstance(scenes, dict): scenes = [scenes]
        for idx, scene in enumerate(scenes, 1):
            trans_type = scene.get('trans', scene.get('transition_type', 'Chuyển cảnh mới'))
            dur = scene.get('dur', scene.get('duration', '8s'))
            st.markdown(f"#### 📍 Phân cảnh {idx} ({dur}) — [ {trans_type} ]")
            st.markdown(f"🏛 **Bối cảnh & Miêu tả:** *{scene.get('setting', scene.get('scene_setting', ''))}*")
            st.markdown(f"**🎙 Đạo diễn ngữ điệu & SFX:** *{scene.get('director', scene.get('voice_director_vn', ''))}*")
            st.markdown(f"**💬 Thoại & Âm thanh (Chuẩn chính tả):** <span class='voiceover-text'>{scene.get('voiceover', scene.get('voiceover_vi', ''))}</span>", unsafe_allow_html=True)
            
            img_p = scene.get('img_p', scene.get('image_prompt', ''))
            is_linked_scene = "nối tiếp" in trans_type.lower() or "dùng lại ảnh cuối" in img_p.lower() or "tham chiếu" in img_p.lower() or "không cần" in img_p.lower()
            
            if is_linked_scene:
                st.info("🔗 **Cảnh nối tiếp:** Không cần tạo ảnh mới. Hãy sử dụng khung hình cuối của Cảnh trước làm ảnh tham chiếu (Image-to-Video) cho cảnh này.")
            else:
                if img_p: 
                    st.markdown(f"**🖼 Prompt Ảnh (Imagen 3):**")
                    st.code(img_p, language="text")
                    safe_copy_button(img_p, f"📋 Sao Chép Prompt Ảnh Cảnh {idx}")
            
            vid_p = scene.get('vid_p', scene.get('video_prompt', ''))
            if vid_p: 
                st.markdown(f"**🎥 Prompt Video (Veo 3):**")
                st.code(vid_p, language="text")
                safe_copy_button(vid_p, f"📋 Sao Chép Prompt Video Cảnh {idx}")
            st.markdown("---")

    st.markdown("### 🎬 **1. Kịch Bản Đã Hoàn Thiện Chi Tiết (Sẵn Sàng Sản Xuất & Nhân Bản)**")
    if not completed_scripts:
        st.info("💡 Chưa có kịch bản nào được tạo chi tiết.")
    else:
        for outline in completed_scripts:
            sc_id = int(outline.get("id", 0))
            is_current = (sc_id == st.session_state.active_script_id)
            with st.container(border=True):
                col_i1, col_btn1, col_btn2 = st.columns([2.5, 1, 1])
                with col_i1:
                    badge = " <span class='badge-ready'>ĐANG XEM</span>" if is_current else ""
                    st.markdown(f"**#{sc_id}. {outline.get('title')}**{badge}", unsafe_allow_html=True)
                    hook_val = outline.get('hook', outline.get('target_hook', ''))
                    if not hook_val or str(hook_val).strip().lower() in ['none', 'null', '']: hook_val = "Kịch bản tập trung làm nổi bật nội dung cốt lõi."
                    st.caption(f"⚡ **Tóm tắt & Hook:** *{hook_val}*")
                with col_btn1:
                    if not is_current:
                        if st.button("👁 Xem lại", key=f"btn_rev_{sc_id}", use_container_width=True):
                            st.session_state.active_script_id = sc_id
                            st.session_state.scroll_to_detail = True
                            st.rerun()
                with col_btn2:
                    clone_key = f"loading_clone_{sc_id}"
                    if clone_key not in st.session_state: st.session_state[clone_key] = False
                    
                    if st.session_state[clone_key]:
                        st.markdown("<div style='background: #fff0f2; border: 1px solid #ffa4b4; padding: 8px; border-radius: 8px; color: #d90429; text-align: center; font-weight: bold;'>⏳ Đang nhân bản...</div>", unsafe_allow_html=True)
                        lock_ui()
                        try:
                            new_clones = clone_script(sc_id)
                            st.session_state.cloned_scripts.extend(new_clones)
                            st.toast("✅ Đã nhân bản kịch bản thành công!")
                        except Exception as e:
                            st.error(f"❌ Lỗi: {e}")
                            time.sleep(2)
                        st.session_state[clone_key] = False
                        st.rerun()
                    else:
                        if st.button("🚀 Nhân bản (Clone)", key=f"btn_clone_{sc_id}", type="primary", use_container_width=True):
                            can_run, msg = check_usage_limit(st.session_state.current_email)
                            if not can_run: st.error(f"❌ {msg}")
                            else:
                                st.session_state[clone_key] = True
                                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ⏳ **2. Kịch Bản Đang Chờ Tạo Chi Tiết**")
    if not pending_scripts:
        st.success("🎉 Tất cả các kịch bản trong danh sách đã được tạo chi tiết thành công.")
    else:
        for outline in pending_scripts:
            sc_id = int(outline.get("id", 0))
            with st.container(border=True):
                col_i2, col_a2 = st.columns([3, 1.2])
                with col_i2:
                    st.markdown(f"**#{sc_id}. {outline.get('title')}** — <span class='badge-pending'>ĐANG CHỜ</span>", unsafe_allow_html=True)
                    hook_val = outline.get('hook', outline.get('target_hook', ''))
                    if not hook_val or str(hook_val).strip().lower() in ['none', 'null', '']: hook_val = "Kịch bản tập trung làm nổi bật nội dung cốt lõi."
                    st.caption(f"⚡ **Tóm tắt & Hook:** *{hook_val}*")
                with col_a2:
                    cre_key = f"loading_cre_{sc_id}"
                    if cre_key not in st.session_state: st.session_state[cre_key] = False
                    
                    if st.session_state[cre_key]:
                        st.markdown("<div style='background: #eff6ff; border: 1px solid #93c5fd; padding: 8px; border-radius: 8px; color: #1e3a8a; text-align: center; font-weight: bold;'>⏳ Đang dựng kịch bản...</div>", unsafe_allow_html=True)
                        lock_ui()
                        try:
                            char_rules = generate_char_rules_string(st.session_state.get("character_profiles", []))
                            create_scene_details(sc_id, st.session_state.get("last_mode", ""), st.session_state.get("last_style", ""), st.session_state.get("last_narrator", ""), char_rules)
                            st.session_state.active_script_id = sc_id
                            st.session_state.scroll_to_detail = True
                            st.toast("✅ Đã tạo kịch bản chi tiết thành công!")
                        except Exception as e:
                            st.error(f"❌ Lỗi: {e}")
                            time.sleep(2)
                        st.session_state[cre_key] = False
                        st.rerun()
                    else:
                        if st.button("✨ Tạo chi tiết ngay", key=f"btn_cre_{sc_id}", type="secondary", use_container_width=True):
                            can_run, msg = check_usage_limit(st.session_state.current_email)
                            if not can_run: st.error(f"❌ {msg}")
                            else:
                                st.session_state[cre_key] = True
                                st.rerun()

    st.markdown("---")
    st.markdown("##### ➕ **Tùy Chỉnh & Gọi Thêm Kịch Bản Mới**")
    
    col_g1, col_g2, col_g3, col_g4 = st.columns([1.5, 0.8, 1.2, 1.5])
    with col_g1:
        if "Viral" in st.session_state.get("last_mode", "Bán Hàng"):
            angle_opts = [
                "🌟 Tự động (AI tự phân tích và mix đa dạng nội dung viral)", 
                "🧠 Chia sẻ kiến thức / Chuyên gia", 
                "💡 Mẹo hay / Life hack", 
                "🎭 Tình huống Drama / Gây tranh cãi", 
                "📖 Kể chuyện (Storytelling) / Truyền cảm hứng",
                "😂 Tình huống hài hước / Giải trí"
            ]
        else:
            angle_opts = [
                "🌟 Tự động (AI tự phân tích và mix 5 góc độ đa dạng, tối ưu nhất)", 
                "⚡ Flash Sale & Deal hời (Tập trung chốt đơn)", 
                "🎭 Tình huống đời sống / Nỗi đau (PAS)", 
                "🔍 Review thực chiến", 
                "💡 Mẹo vặt / Chia sẻ (Lồng ghép sản phẩm)", 
                "😂 Tình huống hài hước (Chốt sale bất ngờ)"
            ]
        chosen_angle = st.selectbox("🧭 Chọn Định hướng chiến lược mới:", angle_opts, key=f"extra_angle_selectbox_{st.session_state.reset_key}")
    with col_g2:
        chosen_chars = st.number_input("Số diễn viên:", min_value=1, max_value=8, value=1, step=1, key=f"extra_num_chars_callmore_{st.session_state.reset_key}")
    with col_g3:
        duration_choice_more = st.selectbox("⏳ Thời lượng video mới:", ["Tự động (AI Tối ưu ~20-30s)", "Tùy chỉnh (Nhập số giây)"], key=f"dur_choice_more_{st.session_state.reset_key}")
        if duration_choice_more.startswith("Tùy chỉnh"):
            custom_sec_more = st.number_input("Nhập số giây:", min_value=10, max_value=300, value=60, step=5, key=f"dur_sec_more_{st.session_state.reset_key}")
    with col_g4:
        idx_narrator = 0 if st.session_state.get("last_narrator") == "Nhân vật xuất hiện nói chuyện (On-camera, Lip-sync)" else 1
        narrator_mode_more = st.selectbox("🎙 Thuyết minh & Nhân vật:", ["Nhân vật xuất hiện nói chuyện (On-camera, Lip-sync)", "🎙 Lồng tiếng ngoài (Off-screen, Show sản phẩm)"], index=idx_narrator, key=f"narrator_more_{st.session_state.reset_key}")

    extra_char_inputs = []
    if chosen_chars > 0:
        st.markdown("###### 👤 Diễn viên cho kịch bản mới (Tùy chọn thay đổi)")
        for i in range(chosen_chars):
            col_role, col_img = st.columns([2, 1])
            with col_role:
                c_role = st.text_input(f"Vai trò NV {i+1} (mới):", key=f"extra_role_{i}_{st.session_state.reset_key}", placeholder="Nhập vai trò (VD: Bác sĩ, Người bệnh...) Hoặc để trống")
            with col_img:
                c_file = st.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"extra_file_{i}_{st.session_state.reset_key}", label_visibility="collapsed")
            
            if c_file:
                role_val = c_role.strip() if c_role.strip() else "AI tự phân tích dựa theo ngữ cảnh và ảnh"
                extra_char_inputs.append({"id": i+1, "role": role_val, "file": c_file})

    st.markdown("<br>", unsafe_allow_html=True)
    c_l, c_btn, c_r = st.columns([1, 2, 1])
    
    with c_btn:
        btn_more_ph = st.empty()
        more_key = "loading_generate_more"
        if more_key not in st.session_state: st.session_state[more_key] = False
        
        if st.session_state[more_key]:
            st.markdown("<div style='background: #fff0f2; border: 1.5px solid #ffa4b4; padding: 12px; border-radius: 8px; color: #d90429; text-align: center; font-size: 16px; font-weight: bold;'>⏳ Đang sáng tạo 5 kịch bản mới... Vui lòng đợi!</div>", unsafe_allow_html=True)
            lock_ui()
            try:
                if duration_choice_more.startswith("Tùy chỉnh"):
                    st.session_state.target_duration_instruction = f"TỔNG THỜI LƯỢNG YÊU CẦU: Chính xác {custom_sec_more} giây. Bạn PHẢI tạo ra số lượng phân cảnh đủ nhiều (mỗi cảnh 4s, 6s, 8s) sao cho tổng thời gian cộng lại bằng ĐÚNG {custom_sec_more} giây."
                else:
                    st.session_state.target_duration_instruction = "TỔNG THỜI LƯỢNG YÊU CẦU: Tự động (Khoảng 3 đến 5 phân cảnh, tổng 15-30 giây)."

                if extra_char_inputs:
                    st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in extra_char_inputs]
                
                st.session_state.last_narrator = narrator_mode_more
                
                new_scripts = generate_more_scripts(chosen_angle, chosen_chars, extra_char_inputs, narrator_mode_more)
                st.session_state.expanded_scripts.extend(new_scripts)
                st.session_state.scroll_to_top = True
                st.toast("✅ Đã sinh thêm 5 kịch bản mới thành công!")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                time.sleep(2)
            st.session_state[more_key] = False
            st.rerun()
        else:
            if btn_more_ph.button("🚀 Gọi Thêm 5 Kịch Bản Mới", key="btn_execute_more_scripts", type="primary", use_container_width=True):
                can_run, msg = check_usage_limit(st.session_state.current_email)
                if not can_run: st.error(f"❌ {msg}")
                else:
                    st.session_state[more_key] = True
                    st.rerun()
