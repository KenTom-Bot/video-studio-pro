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

st.markdown("""
<style>
    .header-container { text-align: center; padding: 1.2rem; background: radial-gradient(circle, rgba(255,75,75,0.08) 0%, rgba(255,255,255,0) 70%); border-radius: 16px; margin-bottom: 1rem; }
    .main-title { font-size: 2.2rem !important; font-weight: 900 !important; background: linear-gradient(90deg, #ff0050 0%, #ff5252 50%, #ff7300 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important; color: white !important; border-radius: 8px !important; font-weight: bold; width: 100%; }
    div[data-testid="stButton"] > button[kind="secondary"] { background: linear-gradient(135deg, #ff4b4b 0%, #ff7300 100%) !important; color: #ffffff !important; box-shadow: 0 3px 8px rgba(255, 75, 75, 0.35) !important; padding: 0.55rem 1rem !important; font-weight: bold !important; border: none !important; }
    div[data-testid="stButton"] > button[kind="secondary"]:hover { transform: translateY(-1px) !important; box-shadow: 0 5px 14px rgba(255, 75, 75, 0.5) !important; }
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
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {ADMIN_EMAIL: {"roles": ALL_MODULES, "phone": "0968484369", "expires_at": "2099-12-31"}}

def save_licensed_accounts(acc_dict):
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(acc_dict, f, ensure_ascii=False, indent=2)
    except: pass

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
    ("editing_acc_email", None), ("current_project_id", None),
    ("action_trigger", None), ("action_param", None)
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
            if (anchor) {
                anchor.scrollIntoView({behavior: 'smooth', block: 'start'});
            } else {
                window.parent.scrollTo({top: 0, behavior: 'smooth'});
            }
        }, 500);
    </script>
    """, height=0)
    st.session_state.scroll_to_detail = False

# ==============================================================================
# 2. HÀM AI LÕI & LUẬT THÉP (KHÓA SINH TRẮC HỌC, ĐỒNG NHẤT KHÔNG ẢNH)
# ==============================================================================
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
        return "🔹 KHÓA ĐỒNG NHẤT NHÂN VẬT (KHÔNG CÓ ẢNH GỐC): AI BẮT BUỘC TỰ SÁNG TẠO diện mạo nhân vật (mô tả rõ độ tuổi, khuôn mặt, kiểu tóc, vóc dáng) VÀ GHI NHỚ MÔ TẢ NÀY. Bắt buộc dán nguyên văn mô tả này vào mọi prompt của tất cả các cảnh để giữ cho nhân vật đồng nhất 100%."
    rules = "🔹 KHÓA SINH TRẮC HỌC & GIẢI PHÓNG TRANG PHỤC:\n"
    for p in profiles: 
        rules += f"   + Nhân vật {p['id']} ({p['role']}): BẮT BUỘC trích xuất và khóa chặt KHUÔN MẶT, KIỂU TÓC, VÓC DÁNG từ ảnh tham chiếu. TUYỆT ĐỐI BỎ QUA trang phục trong ảnh. AI tự thiết kế trang phục mới phù hợp với bối cảnh kịch bản và ghim rắc-co trang phục đó xuyên suốt video.\n"
    return rules

def get_dynamic_realtime_context(mode):
    now = datetime.now()
    month = now.month
    year = now.year
    if month in [12, 1, 2]: season_desc = f"Mùa Đông / Tết Nguyên Đán ({month}/{year})."
    elif month in [3, 4, 5]: season_desc = f"Mùa Xuân / Giao mùa ({month}/{year})."
    elif month in [6, 7, 8]: season_desc = f"Mùa Hè / Nắng Nóng ({month}/{year})."
    else: season_desc = f"Mùa Thu / Se Lạnh ({month}/{year})."
    
    if "Viral" in mode:
        return f"THỜI GIAN HIỆN TẠI: {season_desc}. LƯU Ý QUAN TRỌNG: Chỉ áp dụng thời tiết vào hình ảnh bối cảnh. TUYỆT ĐỐI KHÔNG nhồi nhét từ ngữ miêu tả thời tiết/mùa màng vào lời thoại chia sẻ kiến thức, hãy giữ kịch bản tập trung 100% vào chuyên môn."
    else:
        return f"THỜI GIAN THỰC TẾ: {season_desc}. Bối cảnh, ánh sáng phải phản ánh chính xác thời điểm thực tế này."

def get_mode_specific_rules(mode):
    if "Viral" in mode:
        return """
    🎯 ĐỊNH HƯỚNG THỂ LOẠI: VIRAL & XÂY KÊNH (CHUYÊN GIA / KIẾN THỨC / GIẢI TRÍ)
    - MỤC TIÊU LÕI: Trao giá trị thực tế, chia sẻ kiến thức chuyên môn, mẹo hay hoặc kể chuyện logic để KÉO LƯỢT FOLLOW.
    - CƠ CHẾ KÊU GỌI (CTA): Tuyệt đối KHÔNG bán hàng, KHÔNG chốt đơn. Kết thúc bằng cái kết mở hoặc kêu gọi Follow/Bình luận.
    - VĂN PHONG & LOGIC: Giọng điệu phải CHÂN THẬT, CHUYÊN NGHIỆP. Đi thẳng vào vấn đề, mạch lạc.
        """
    else:
        return """
    🎯 ĐỊNH HƯỚNG THỂ LOẠI: TIKTOK SHOP & BÁN HÀNG (AFFILIATE THỰC CHIẾN)
    - MỤC TIÊU LÕI: Đánh trúng Nỗi đau (Pain points), làm nổi bật USP để CHỐT ĐƠN.
    - CƠ CHẾ KÊU GỌI (CTA): Giục khách mua ngay, chớp deal hời góc trái màn hình.
    - CHÍNH SÁCH: CẤM BÁO GIÁ cụ thể bằng con số. Mọi thông số kịch bản phải khớp 100% dữ liệu sản phẩm gốc.
        """

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars):
    time_ctx = get_dynamic_realtime_context(mode)
    mode_rules = get_mode_specific_rules(mode)
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL CHO VEO 3 VÀ IMAGEN 3. PHONG CÁCH: {style} | ĐỊNH DẠNG: {HARDCODED_ASPECT}
    {time_ctx}
    {mode_rules}
    🛑 CÁC QUY TẮC BỔ SUNG TUÂN THỦ 100%:
    1. SỐ LƯỢNG NHÂN VẬT CHUẨN XÁC: Kịch bản BẮT BUỘC thiết kế cho ĐÚNG {num_chars} nhân vật tương tác.
    2. {char_rules}
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, num_chars, duration_instruction):
    time_ctx = get_dynamic_realtime_context(mode)
    mode_rules = get_mode_specific_rules(mode)
    is_on_camera = "On-camera" in narrator_mode
    narrator_instruction = f"Nhân vật nói chuyện trực tiếp trước ống kính, lip-sync khớp lời thoại." if is_on_camera else "Lồng tiếng ngoài khung hình."
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL CHO VEO 3 VÀ IMAGEN 3. PHONG CÁCH: {style} | ĐỊNH DẠNG: {HARDCODED_ASPECT}
    {time_ctx}
    {mode_rules}
    🛑 CÁC QUY TẮC KỸ THUẬT QUAY DỰNG (BẮT BUỘC TUÂN THỦ 100%):
    1. BẢO VỆ MÀU SẮC, HÌNH ẢNH & CHỐNG TEXT RÁC:
       - Trong mọi `image_prompt` và `video_prompt`, BẮT BUỘC CHÈN LỆNH: "Maintain EXACT original product details. NO generated text, NO subtitles, NO floating logos, NO distortion."
    2. ĐỒNG NHẤT NHÂN VẬT & GIẢI PHÓNG TRANG PHỤC: 
       - {char_rules}
       - TỰ ĐỘNG THIẾT KẾ TRANG PHỤC: AI tự chọn quần áo phù hợp với bối cảnh kịch bản và GHIM chặt mô tả quần áo đó xuyên suốt tất cả các cảnh để giữ rắc-co (trừ khi có sự thay đổi thời gian/hoàn cảnh rõ rệt trong kịch bản).
    3. TÍNH TOÁN THỜI LƯỢNG VÀ SỐ PHÂN CẢNH CHÍNH XÁC:
       - {duration_instruction}
       - BẠN BẮT BUỘC PHẢI TẠO RA ĐỦ SỐ LƯỢNG PHÂN CẢNH (mỗi cảnh 4s, 6s, 8s) ĐỂ KHỚP 100% VỚI YÊU CẦU TRÊN.
    4. QUY CHUẨN TỐC ĐỘ NÓI (WPM PHYSICS):
       - Nhịp độ nhanh (Bán hàng): 3.5 - 4 từ/giây. Nhịp độ chậm (Kiến thức/Kể chuyện): 1.8 - 2.2 từ/giây.
    5. THOẠI MƯỢT MÀ VÀ LIỀN MẠCH: 
       - Lời thoại (`voiceover_vi`) TUYỆT ĐỐI không được lủng củng. Phải tự nhiên. Câu thoại giữa các cảnh phải KHỚP NỐI VÀ LIỀN MẠCH thành một luồng thông tin không đứt đoạn.
    6. LOGIC CHUYỂN CẢNH: Bắt buộc dùng "Cảnh nối tiếp (Dùng lại ảnh cuối)" kèm lệnh `holding the final frame steady as a reference anchor` khi hành động liên tục.
    7. HÌNH THỨC THUYẾT MINH: {narrator_instruction}
    """

def create_scene_details(target_id, mode, style, narrator_mode, char_rules):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if sc["id"] == target_id), None)
    if not outline: return
    
    time_ctx = get_dynamic_realtime_context(mode)
    is_on_camera = "On-camera" in narrator_mode
    prod_data_ctx = json.dumps(st.session_state.get('current_product_data_saved'), ensure_ascii=False)
    dna_data_ctx = json.dumps(st.session_state.get('content_analysis'), ensure_ascii=False)
    duration_instruction = st.session_state.get("target_duration_instruction", "Tự động phân bổ 3-5 phân cảnh.")
    num_chars = outline.get("actor_count", st.session_state.get("extra_num_chars", 1))
    
    prompt = f"""
    {time_ctx}
    DỮ LIỆU ĐẦU VÀO: {prod_data_ctx}
    PHÂN TÍCH DNA: {dna_data_ctx}
    
    Viết chi tiết kịch bản ID {target_id}: '{outline.get('title')}'. Hook: {outline.get('target_hook')}. Bối cảnh: {outline.get('setting_style')}.
    THUYẾT MINH: {'Nhân vật xuất hiện trực tiếp, lip-sync' if is_on_camera else 'Lồng tiếng ngoài khung hình'}.
    
    LƯU Ý VỀ DIỆN MẠO & TRANG PHỤC: AI phải tạo ra Cụm từ khóa mô tả Diện Mạo nhân vật (tóc, dáng mặt) và Trang Phục hợp bối cảnh, sau đó chèn y nguyên Cụm từ khóa này vào prompt của tất cả các cảnh. Nếu dùng ảnh tham chiếu, TUYỆT ĐỐI không lấy quần áo từ ảnh tham chiếu.
    
    TRẢ VỀ ĐÚNG 1 DICT JSON CẤU TRÚC SAU:
    {{
        "title": "{outline.get('title')}",
        "total_estimated_duration": "Tổng thời gian khớp với yêu cầu",
        "script_outfit_setup": "Mô tả DIỆN MẠO (nếu AI tự nghĩ ra) + TRANG PHỤC và BỐI CẢNH (BẮT BUỘC CHÈN NGUYÊN VĂN MÔ TẢ NÀY VÀO PROMPT TẤT CẢ CÁC CẢNH ĐỂ KHÓA RẮC-CO)",
        "voice_profile": {{"gender": "Nam/Nữ", "tone": "nhịp độ chuẩn theo thời lượng, giọng Miền Bắc (chuẩn)"}},
        "scenes": [
            {{
                "scene_number": 1, "duration": "4s", "transition_type": "Chuyển cảnh mới (Tạo ảnh mới)", 
                "scene_setting": "Mô tả bối cảnh góc máy...",
                "voice_director_vn": "Giọng Nam/Nữ Miền Bắc...", 
                "voiceover_vi": "Lời thoại tự nhiên, mượt mà, đúng số lượng từ WPM, KHÔNG nhồi nhét sáo rỗng...",
                "image_prompt": "Cinematic vertical 9:16 photo... [CHÈN MÔ TẢ DIỆN MẠO VÀ TRANG PHỤC Ở TRÊN VÀO ĐÂY ĐỂ ĐỒNG NHẤT]. DO NOT use clothing from reference image. NO generated text, NO floating logos.", 
                "video_prompt": "Vertical 9:16 video... {'character talking directly to camera, speaking the Vietnamese line: [Điền lời thoại] with perfect lip-sync...' if is_on_camera else 'off-screen voiceover...'} NO generated text."
            }},
            {{
                "scene_number": 2, "duration": "6s", "transition_type": "Cảnh nối tiếp (Dùng lại ảnh cuối)", 
                "scene_setting": "...",
                "voice_director_vn": "...", 
                "voiceover_vi": "<Câu chuyện câu liền mà mượt mạch nối tiếp trước,>",
                "image_prompt": "<Nếu Dùng chiếu... cuối ghi: tham thì ảnh>", 
                "video_prompt": "<Nếu a anchor as chèn: final frame holding nối reference steady the tiếp>"
            }}
        ]
    }}
    Lưu ý: Các "duration" CHỈ ĐƯỢC LÀ "4s", "6s", "8s". KHÔNG DÙNG DẤU NGOẶC KÉP CHƯA ESCAPE TRONG JSON.
    """
    res = call_gemini([prompt], get_sys_inst_details(mode, style, narrator_mode, char_rules, num_chars, duration_instruction))
    if not res or "scenes" not in res:
        raise Exception("AI không trả về đúng định dạng JSON, vui lòng thử lại.")
    st.session_state.generated_details[target_id] = res

def clone_script(script_id):
    mode = st.session_state.get("last_mode", "Bán Hàng")
    style = st.session_state.get("last_style", "Điện ảnh")
    narrator = st.session_state.get("last_narrator", "On-camera")
    char_rules = generate_char_rules_string(st.session_state.get("character_profiles", []))
    
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if sc["id"] == script_id), None)
    cur_len = len(all_combined)
    num_chars = target.get("actor_count", st.session_state.get("extra_num_chars", 1))
    
    time_ctx = get_dynamic_realtime_context(mode)
    dna_str = json.dumps(st.session_state.content_analysis, ensure_ascii=False) if st.session_state.content_analysis else "Chưa có dữ liệu"
    
    prompt = f"""
    {time_ctx}
    DỮ LIỆU GỐC: {dna_str}
    Nhân bản kịch bản gốc: {json.dumps(target, ensure_ascii=False)}. 
    Dựa BẮT BUỘC vào dữ liệu Gốc ở trên, tạo chính xác 5 biến thể mới tuân thủ tuyệt đối ĐỊNH HƯỚNG THỂ LOẠI. Lời thoại mượt mà tự nhiên, tương tác ĐÚNG {num_chars} nhân vật.
    BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON GỒM CÁC KEY SAU:
    {{
        "script_outlines": [
            {{
                "id": {cur_len+1},
                "title": "Tên kịch bản",
                "setting_style": "Bối cảnh thực tế",
                "target_hook": "Viết 2-3 câu tóm tắt diễn biến kịch bản và câu thoại Hook dẫn dắt tâm lý mượt mà (tuân thủ mục tiêu)",
                "actor_count": {num_chars}
            }}
        ]
    }}
    LƯU Ý: TRẢ VỀ ĐÚNG 5 PHẦN TỬ TRONG MẢNG `script_outlines`. KHÔNG DÙNG DẤU NGOẶC KÉP CHƯA ESCAPE.
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, narrator, char_rules, num_chars))
    if not res or "script_outlines" not in res:
        raise Exception("AI không trả về đúng định dạng JSON, vui lòng thử lại.")
    clones = res.get("script_outlines", [])
    for idx, cl in enumerate(clones): cl["id"] = cur_len + idx + 1
    return clones

def generate_more_scripts(angle, num_chars, extra_char_inputs):
    mode = st.session_state.get("last_mode", "Bán Hàng")
    style = st.session_state.get("last_style", "Điện ảnh")
    narrator = st.session_state.get("last_narrator", "On-camera")
    char_rules = generate_char_rules_string(st.session_state.get("character_profiles", []))
    
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    cur_len = len(all_combined)
    
    time_ctx = get_dynamic_realtime_context(mode)
    prod_ctx = f"THÔNG TIN NGƯỜI DÙNG NHẬP: {st.session_state.current_input_context}"
    db_ctx = f"DỮ LIỆU (DB): {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)}" if st.session_state.current_product_data_saved else ""
    dna_ctx = f"DNA GỐC: {json.dumps(st.session_state.content_analysis, ensure_ascii=False)}" if st.session_state.content_analysis else ""
    
    prompt = f"""
    {time_ctx}
    {prod_ctx}
    {db_ctx}
    {dna_ctx}
    
    🛑 YÊU CẦU MỞ RỘNG (BẮT BUỘC TUÂN THỦ CHÍNH SÁCH VÀ THỂ LOẠI):
    1. ĐỊNH HƯỚNG CHIẾN LƯỢC: '{angle}'. Đánh mạnh tâm lý học.
    2. THỜI GIAN THỰC & CẢM XÚC: Văn phong nói mượt mà, chuyên sâu, tự nhiên mạng xã hội.
    3. SỐ LƯỢNG DIỄN VIÊN BẮT BUỘC: Thiết kế thoại tương tác cho đúng {num_chars} nhân vật. 
    4. BẮT BUỘC TẠO CHÍNH XÁC 5 KỊCH BẢN MỚI TRONG MẢNG `script_outlines`.
    
    BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON GỒM CÁC KEY SAU:
    {{
        "script_outlines": [
            {{
                "id": {cur_len+1},
                "title": "Tên kịch bản chuẩn chiến lược",
                "setting_style": "Bối cảnh thực tế",
                "target_hook": "Viết 2-3 câu tóm tắt diễn biến kịch bản theo đúng chiến lược '{angle}' kèm câu thoại Hook mở đầu sắc bén, mượt mà đánh đúng nỗi đau/khao khát, tuân thủ mục tiêu của Thể loại",
                "actor_count": {num_chars}
            }}
        ]
    }}
    LƯU Ý: TRẢ VỀ ĐÚNG 5 PHẦN TỬ.
    """
    
    payload = []
    if extra_char_inputs:
        for c in extra_char_inputs:
            payload.append(f"ẢNH NHÂN VẬT THAM CHIẾU {c['id']} - VAI TRÒ: {c['role']}:")
            payload.append(types.Part.from_bytes(data=c['file'].getvalue(), mime_type=c['file'].type if c['file'].type else "image/jpeg"))
    payload.append(prompt)
    
    res = call_gemini(payload, get_sys_inst_outlines(mode, style, narrator, char_rules, num_chars))
    if not res or "script_outlines" not in res:
        raise Exception("AI không trả về đúng định dạng JSON, vui lòng thử lại.")
    more_scripts = res.get("script_outlines", [])
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
            return "Sai đường link Supabase (Thiếu https:// hoặc bị lỗi đánh máy) trong cài đặt Secrets."
        return err_msg

# ==============================================================================
# 3. THANH BÊN (SIDEBAR) & TÀI KHOẢN
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        st.markdown("### 🔐 ĐĂNG NHẬP")
        email_input = st.text_input("Nhập Email:", placeholder="Nhập email tài khoản của bạn...", key="login_email_input")
        btn_login_ph = st.empty()
        if btn_login_ph.button("🔑 Đăng Nhập", type="primary"):
            with btn_login_ph.container():
                with st.spinner("⏳ Đang xác thực..."):
                    email_check = email_input.strip()
                    if email_check in st.session_state.licensed_accounts:
                        acc_info = st.session_state.licensed_accounts[email_check]
                        exp_date_str = acc_info.get("expires_at", "2099-12-31")
                        try:
                            exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
                            if datetime.now() > exp_date:
                                st.error(f"❌ Tài khoản đã hết hạn vào ngày {exp_date_str}! Vui lòng liên hệ Admin để gia hạn.")
                                st.stop()
                        except: pass
                        st.session_state.is_logged_in = True
                        st.session_state.current_email = email_check
                        st.toast("✅ Đăng nhập thành công!")
                        time.sleep(0.5)
                        st.rerun()
                    else: st.error("Tài khoản chưa được cấp quyền!")
    else:
        current_acc = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        exp_date_str = current_acc.get("expires_at", "2099-12-31")
        if current_acc and st.session_state.current_email != ADMIN_EMAIL:
            try:
                exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
                days_left = (exp_date - datetime.now()).days
                if 0 <= days_left <= 7:
                    st.warning(f"⚠️ **CẢNH BÁO:** Tài khoản của bạn sẽ hết hạn sau **{days_left} ngày nữa** ({exp_date_str}). Liên hệ hotline để gia hạn!")
            except: pass

        st.markdown("### 🗂 LÀM VIỆC")
        btn_new_proj_ph = st.empty()
        if btn_new_proj_ph.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True):
            with btn_new_proj_ph.container():
                with st.spinner("⏳ Đang khởi tạo..."):
                    st.session_state.all_scripts, st.session_state.cloned_scripts, st.session_state.expanded_scripts = [], [], []
                    st.session_state.generated_details, st.session_state.content_analysis = {}, None
                    st.session_state.active_script_id = None
                    st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
                    st.session_state.current_input_context = ""
                    st.session_state.current_product_data_saved = None
                    st.session_state.character_profiles = []
                    st.session_state.current_project_id = None
                    st.session_state.reset_key += 1 
                    st.toast("✅ Đã dọn dẹp và mở dự án mới sạch sẽ!")
                    time.sleep(0.5)
                    st.rerun()
            
        st.session_state.active_project_title = st.text_input("Tên dự án hiện tại:", placeholder="VD: Chiến dịch Tháng 10...", value=st.session_state.active_project_title)
        
        btn_save_proj_ph = st.empty()
        if btn_save_proj_ph.button("💾 Lưu Dự Án Này", use_container_width=True):
            with btn_save_proj_ph.container():
                with st.spinner("⏳ Đang lưu dữ liệu..."):
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
                            if btn_open_ph.button("📂 Mở", key=f"open_{p['id']}", use_container_width=True):
                                with btn_open_ph.container():
                                    with st.spinner("⏳ Khôi phục..."):
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
                                        st.toast("✅ Đã khôi phục dự án!")
                                        time.sleep(0.5)
                                        st.rerun()
                        with col_del:
                            btn_del_ph = st.empty()
                            if btn_del_ph.button("🗑️ Xóa", key=f"del_{p['id']}", type="secondary", use_container_width=True):
                                with btn_del_ph.container():
                                    supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                                    st.toast("✅ Đã xóa dự án!")
                                    time.sleep(0.5)
                                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.current_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙ QUẢN TRỊ ADMIN")
            expired_or_soon = []
            for acc, info in st.session_state.licensed_accounts.items():
                if acc == ADMIN_EMAIL: continue
                exp_str = info.get("expires_at", "2099-12-31")
                try:
                    exp_dt = datetime.strptime(exp_str, "%Y-%m-%d")
                    d_left = (exp_dt - datetime.now()).days
                    if d_left <= 7: expired_or_soon.append((acc, info.get('phone', ''), d_left, exp_str))
                except: pass
            
            if expired_or_soon:
                for cust, phone, d_left, exp_str in expired_or_soon:
                    status_text = f"Đã quá hạn {abs(d_left)} ngày" if d_left < 0 else (f"Hết hạn hôm nay!" if d_left == 0 else f"Còn {d_left} ngày")
                    with st.container(border=True):
                        st.markdown(f"**👤 {cust}**")
                        st.caption(f"📞 SĐT: {phone or 'Chưa có'}<br>⚠️ Trạng thái: <b>{status_text}</b> ({exp_str})", unsafe_allow_html=True)
                        if phone:
                            clean_phone = re.sub(r'\D', '', phone)
                            st.markdown(f"<a href='[https://zalo.me/](https://zalo.me/){clean_phone}' target='_blank' style='background:#0068ff; color:white; padding:5px 12px; border-radius:6px; text-decoration:none; font-size:12px; font-weight:700; display:inline-block; margin-top:5px;'>💬 Nhắn Zalo nhắc hạn</a>", unsafe_allow_html=True)
            else: st.caption("✅ Không có khách nào sắp hết hạn trong 7 ngày tới.")
            
            st.markdown("---")
            with st.form("add_license"):
                st.markdown("##### ➕ Cấp Quyền Khách Hàng Mới")
                new_acc = st.text_input("Email khách hàng:", placeholder="Nhập email khách hàng cần cấp quyền...")
                new_phone = st.text_input("Số điện thoại (SĐT):", placeholder="Vd: 0968484369")
                assigned_modules = st.multiselect("Phân quyền thể loại:", options=ALL_MODULES, default=ALL_MODULES)
                duration_opt = st.selectbox("Thời hạn:", ["Dùng thử 3 ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "3 Năm", "5 Năm", "10 Năm", "Vĩnh viễn (Trọn đời)"])
                btn_add_lic = st.form_submit_button("💾 Cấp Quyền & Lưu SĐT")
                if btn_add_lic:
                    with st.spinner("⏳ Đang cấp quyền..."):
                        exp_date = "2099-12-31" if "Vĩnh viễn" in duration_opt else (datetime.now() + timedelta(days=3 if "Dùng thử" in duration_opt else {"1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730, "3 Năm": 1095, "5 Năm": 1825, "10 Năm": 3650}.get(duration_opt, 30))).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[new_acc.strip()] = {
                            "roles": assigned_modules, "phone": new_phone.strip(), "expires_at": exp_date
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
                        st.markdown(f"**👤 {acc}**")
                        phone_val = info.get('phone', '')
                        roles_val = info.get('roles', ALL_MODULES)
                        exp_val = info.get('expires_at', '2099-12-31')
                        st.caption(f"📞 SĐT: {phone_val or 'Chưa có'}<br>• Quyền: {', '.join(roles_val)}<br>• Hết hạn: {exp_val}", unsafe_allow_html=True)
                        if phone_val:
                            clean_p = re.sub(r'\D', '', phone_val)
                            st.markdown(f"<a href='[https://zalo.me/](https://zalo.me/){clean_p}' target='_blank' style='background:#0068ff; color:white; padding:4px 10px; border-radius:4px; text-decoration:none; font-size:11px; font-weight:700; display:inline-block; margin-bottom:5px;'>💬 Nhắn Zalo</a>", unsafe_allow_html=True)
                        
                        col_up, col_del = st.columns(2)
                        with col_up:
                            btn_edit_ph = st.empty()
                            if btn_edit_ph.button("✏️ Sửa", key=f"edit_acc_{acc}", use_container_width=True):
                                st.session_state.editing_acc_email = acc
                                st.rerun()
                        with col_del:
                            btn_del_acc_ph = st.empty()
                            if btn_del_acc_ph.button(f"🗑 Xóa", key=f"del_acc_{acc}", type="secondary", use_container_width=True):
                                with btn_del_acc_ph.container():
                                    del st.session_state.licensed_accounts[acc]
                                    save_licensed_accounts(st.session_state.licensed_accounts)
                                    st.toast("✅ Đã xóa tài khoản!")
                                    time.sleep(0.5)
                                    st.rerun()
                        
                        if st.session_state.get("editing_acc_email") == acc:
                            with st.form(f"update_form_{acc}" ):
                                st.markdown(f"**Cập nhật cho: {acc}**")
                                upd_phone = st.text_input("SĐT mới:", value=phone_val, placeholder="Cập nhật số điện thoại...", key=f"upd_p_{acc}")
                                upd_roles = st.multiselect("Phân quyền thể loại:", options=ALL_MODULES, default=roles_val, key=f"upd_r_{acc}")
                                upd_exp = st.text_input("Ngày hết hạn (YYYY-MM-DD):", value=exp_val, placeholder="YYYY-MM-DD", key=f"upd_e_{acc}")
                                btn_save_upd = st.form_submit_button("💾 Lưu Cập Nhật")
                                if btn_save_upd:
                                    with st.spinner("⏳ Đang lưu..."):
                                        st.session_state.licensed_accounts[acc] = {"roles": upd_roles, "phone": upd_phone.strip(), "expires_at": upd_exp.strip()}
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
        st.markdown("### 🔐 TÀI KHOẢN")
        st.success(f"Đang dùng: {st.session_state.current_email}")
        btn_logout_ph = st.empty()
        if btn_logout_ph.button("🚪 Đăng Xuất"):
            with btn_logout_ph.container():
                st.session_state.is_logged_in = False
                st.toast("✅ Đăng xuất!")
                time.sleep(0.5)
                st.rerun()

if not st.session_state.is_logged_in:
    st.info("👈 Vui lòng đăng nhập ở thanh công cụ bên trái.")
    st.stop()

# ==============================================================================
# 4. HỆ THỐNG KIỂM SOÁT SỰ KIỆN TOÀN CẦU (GLOBAL LOCK - ANTI GHOST UI)
# ==============================================================================
if st.session_state.get("action_trigger"):
    action = st.session_state.action_trigger
    param = st.session_state.action_param
    st.session_state.action_trigger = None 
    
    st.markdown("<h2 style='text-align:center; color:#d90429;'>🚀 HỆ THỐNG ĐANG XỬ LÝ... VUI LÒNG ĐỢI</h2>", unsafe_allow_html=True)
    
    if action == "generate_main":
        with st.spinner("⏳ Đạo diễn AI đang phân tích dữ liệu, tâm lý và sinh kịch bản..."):
            try:
                char_inputs_temp = st.session_state.get("temp_char_inputs", [])
                up_files_temp = st.session_state.get("temp_up_files", [])
                
                st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs_temp]
                char_rules = generate_char_rules_string(st.session_state.character_profiles)
                
                st.session_state.last_mode = param["mode"]
                st.session_state.last_style = param["style"]
                st.session_state.last_narrator = param["narrator_mode"]
                st.session_state.current_input_context = param["custom_note"]
                
                if param.get("is_viral"):
                    st.session_state.current_product_data_saved = {
                        "Định vị Kênh / Người nói": param.get("channel_persona"),
                        "Chủ đề Video": param.get("video_topic")
                    }
                else:
                    st.session_state.current_product_data_saved = st.session_state.get("current_product_data")
                    
                st.session_state.current_project_id = None
                
                time_ctx = get_dynamic_realtime_context(param["mode"])
                prod_ctx = f"DỮ LIỆU ĐẦU VÀO: {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)}" if st.session_state.current_product_data_saved else ""
                
                angle_str = param["initial_angle"]
                num_c = param["num_chars"]
                
                if param.get("is_viral"):
                    angle_instruction = "CHIẾN LƯỢC VIRAL: AI TỰ ĐỘNG PHÂN TÍCH VÀ ĐƯA RA 5 KỊCH BẢN ĐA DẠNG." if "Tự động" in angle_str else f"CHIẾN LƯỢC BẮT BUỘC: '{angle_str}'"
                    dna_instruction = """
                    "content_analysis": {
                        "primary_target_audience": "Nhận diện TỆP KHÁN GIẢ MỤC TIÊU",
                        "core_value_or_message": "Giá trị cốt lõi / Thông điệp truyền tải",
                        "audience_pain_points": "Nỗi đau / Vấn đề của khán giả",
                        "viral_hook_element": "Yếu tố giữ chân / Gây tranh cãi / Đồng cảm",
                        "visual_physics_rules": "Quy chuẩn vật lý & Bối cảnh",
                        "prompt_dna_lock": "Khóa thị giác"
                    }
                    """
                else:
                    angle_instruction = "CHIẾN LƯỢC BÁN HÀNG: AI TỰ ĐỘNG MIX 5 KỊCH BẢN TỐI ƯU NHẤT." if "Tự động" in angle_str else f"CHIẾN LƯỢC BẮT BUỘC: '{angle_str}'"
                    dna_instruction = """
                    "content_analysis": {
                        "primary_target_audience": "Nhận diện TỆP KHÁCH HÀNG",
                        "mechanical_and_accessories": "Kiểu dáng, chất liệu",
                        "customer_pain_points": "Nỗi đau khách hàng",
                        "core_desires": "Mong muốn cốt lõi",
                        "emotional_or_usp_hook": "USP độc quyền",
                        "visual_physics_rules": "Quy chuẩn vật lý",
                        "prompt_dna_lock": "Khóa thị giác"
                    }
                    """

                prompt = f"""
                {time_ctx}
                {prod_ctx}
                GHI CHÚ DỰ ÁN: {param["custom_note"]}
                
                BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON CHUẨN GỒM CÁC KEY SAU:
                {{
                    {dna_instruction},
                    "script_outlines": [ 
                        {{
                            "id": 1, 
                            "title": "Tên kịch bản", 
                            "setting_style": "Bối cảnh thực tế", 
                            "target_hook": "Viết 2-3 câu tóm tắt diễn biến kịch bản và câu thoại Hook mở đầu mượt mà, tự nhiên",
                            "actor_count": {num_c}
                        }} 
                    ]
                }}
                YÊU CẦU: Tạo chính xác 5 kịch bản khác nhau.
                ĐỊNH HƯỚNG TÂM LÝ: {angle_instruction}
                LƯU Ý CỰC KỲ QUAN TRỌNG: Kịch bản BẮT BUỘC thiết kế tương tác qua lại cho ĐÚNG {num_c} nhân vật (nếu >1). KHÔNG DÙNG DẤU NGOẶC KÉP CHƯA ESCAPE BÊN TRONG JSON.
                """
                
                payload = []
                if up_files_temp:
                    payload.append("ẢNH THAM CHIẾU:")
                    for f in up_files_temp: payload.append(types.Part.from_bytes(data=f.getvalue(), mime_type=f.type if f.type else "image/jpeg"))
                if char_inputs_temp:
                    for c in char_inputs_temp:
                        payload.append(f"ẢNH NHÂN VẬT THAM CHIẾU {c['id']} - VAI TRÒ: {c['role']}:")
                        payload.append(types.Part.from_bytes(data=c['file'].getvalue(), mime_type=c['file'].type if c['file'].type else "image/jpeg"))
                payload.append(prompt)
                
                res = call_gemini(payload, get_sys_inst_outlines(param["mode"], param["style"], param["narrator_mode"], char_rules, num_c))
                
                if not res or "script_outlines" not in res:
                    st.error("❌ AI không trả về đúng định dạng JSON. Vui lòng thử lại!")
                else:
                    st.session_state.content_analysis = res.get("content_analysis")
                    st.session_state.all_scripts = res.get("script_outlines", [])
                    st.session_state.cloned_scripts = []
                    st.session_state.expanded_scripts = []
                    st.session_state.generated_details = {}
                    st.session_state.active_script_id = None
                    st.session_state.scroll_to_top = True
                    st.toast("✅ Đã sinh xong 5 kịch bản và phân tích DNA!")
            except Exception as e:
                st.error(f"❌ Lỗi xử lý AI: {str(e)}")
                time.sleep(2)
            st.rerun()

    elif action == "create_detail":
        with st.spinner(f"⏳ Đang dựng kịch bản #{param}, khớp nối thoại mượt mà, WPM và Thông số Sản phẩm..."):
            try:
                char_rules = generate_char_rules_string(st.session_state.get("character_profiles", []))
                create_scene_details(param, st.session_state.get("last_mode", ""), st.session_state.get("last_style", ""), st.session_state.get("last_narrator", ""), char_rules)
                st.session_state.active_script_id = param
                st.session_state.scroll_to_detail = True
                st.toast("✅ Đã tạo kịch bản chi tiết thành công!")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                time.sleep(2)
            time.sleep(0.5)
            st.rerun()
            
    elif action == "clone_script":
        with st.spinner(f"⏳ Đang phân tích và nhân bản biến thể từ Kịch bản #{param}... Vui lòng đợi..."):
            try:
                new_clones = clone_script(param)
                st.session_state.cloned_scripts.extend(new_clones)
                st.session_state.scroll_to_top = True
                st.toast("✅ Đã nhân bản kịch bản thành công!")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                time.sleep(2)
            time.sleep(0.5)
            st.rerun()
            
    elif action == "generate_more":
        angle = param.get("angle")
        chars = param.get("chars")
        with st.spinner(f"⏳ Đang sáng tạo và gọi thêm 5 kịch bản mới theo chiến lược '{angle}'... Vui lòng đợi..."):
            try:
                extra_char_inputs_temp = st.session_state.get("temp_extra_char_inputs", [])
                if extra_char_inputs_temp:
                    st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in extra_char_inputs_temp]
                
                new_scripts = generate_more_scripts(angle, chars, extra_char_inputs_temp)
                st.session_state.expanded_scripts.extend(new_scripts)
                st.session_state.scroll_to_top = True
                st.toast("✅ Đã sinh thêm 5 kịch bản mới thành công!")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                time.sleep(2)
            time.sleep(0.5)
            st.rerun()

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
        viral_topic = st.text_area("💡 Chủ đề Video / Mẹo muốn chia sẻ:", placeholder="Nhập chủ đề (VD: 3 sai lầm khi rửa mặt, Tại sao không nên nghỉ việc ngang...)", height=68, key=f"viral_topic_{st.session_state.reset_key}")
    
    with st.expander("📎 Dữ liệu bổ sung (Upload Ảnh Tham chiếu / Ghi chú đặc biệt) - KHÔNG BẮT BUỘC"):
        up_files = st.file_uploader("📦 Upload Ảnh Tham chiếu (Bối cảnh/Đồ vật - Tùy chọn):", type=["jpg", "png"], accept_multiple_files=True, key=f"up_main_files_v_{st.session_state.reset_key}")
        custom_note = st.text_area("✍️️ Ghi chú kịch bản / Ý tưởng cụ thể (Tùy chọn):", placeholder="Nhập thông tin, yêu cầu chi tiết, hoặc ý tưởng cụ thể của bạn vào đây...", key=f"note_main_v_{st.session_state.reset_key}")
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
    custom_note = st.text_area("✍️ Ghi chú đặc biệt cho AI (Tùy chọn):", placeholder="Nhập yêu cầu nhấn mạnh tính năng, kịch bản mẫu, hoặc ý tưởng cụ thể của bạn vào đây...", key=f"note_main_s_{st.session_state.reset_key}")


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

    narrator_mode = st.selectbox("🎙 Thuyết minh & Nhân vật:", ["Nhân vật xuất hiện nói chuyện (On-camera, Lip-sync)", "🎙️ Lồng tiếng ngoài (Off-screen, Show sản phẩm)"], key=f"narrator_sel_{st.session_state.reset_key}")

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

btn_gen_main_ph = st.empty()
spin_gen_main_ph = st.empty()
if btn_gen_main_ph.button("🚀 PHÂN TÍCH DNA & SINH 5 KỊCH BẢN ĐA VŨ TRỤ", type="primary", use_container_width=True):
    btn_gen_main_ph.empty()
    with spin_gen_main_ph.container():
        st.session_state.action_trigger = "generate_main"
        st.session_state.action_param = {
            "mode": mode, "style": style, "narrator_mode": narrator_mode, 
            "initial_angle": initial_angle, "custom_note": custom_note, "num_chars": num_chars,
            "is_viral": is_viral_mode,
            "channel_persona": viral_persona if is_viral_mode else "",
            "video_topic": viral_topic if is_viral_mode else ""
        }
        st.session_state.temp_char_inputs = char_inputs
        st.session_state.temp_up_files = up_files
        st.rerun()

# ==================== HIỂN THỊ PHÂN TÍCH DNA ====================
if st.session_state.content_analysis and isinstance(st.session_state.content_analysis, dict):
    st.divider()
    st.markdown(f"### 🔍 **Phân Tích DNA Chi Tiết Đa Tầng**")
    ca = st.session_state.content_analysis
    with st.container(border=True):
        st.markdown("##### 🎯 **1. Chân dung Khán giả & Vấn đề:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Tệp khán giả / khách hàng:</b> {format_analysis_field(ca.get('primary_target_audience', 'N/A'))}<br>{format_analysis_field(ca.get('customer_pain_points', ca.get('audience_pain_points', 'N/A')))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 🏭 **2. Yếu tố Cốt lõi & Vật lý:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Giá trị / Thông số:</b> {format_analysis_field(ca.get('mechanical_and_accessories', ca.get('core_value_or_message', 'N/A')))}<br>• <b>Vật lý & Bối cảnh:</b> {format_analysis_field(ca.get('visual_physics_rules', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 💡 **3. Điểm thu hút & USP:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Mong muốn / Sự đồng cảm:</b> {format_analysis_field(ca.get('core_desires', ca.get('viral_hook_element', 'N/A')))}<br>• <b>USP / Hook:</b> {format_analysis_field(ca.get('emotional_or_usp_hook', 'N/A'))}</div>", unsafe_allow_html=True)
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
        vp = active_sc.get("voice_profile", {})
        if isinstance(vp, str): vp = {"gender": "Nữ", "tone": vp}
        
        # ĐÂY LÀ ĐIỂM NEO KHI AUTO-SCROLL
        st.markdown("<div id='detailed-view-anchor'></div>", unsafe_allow_html=True)
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(active_sc.get('title', 'KỊCH BẢN')).upper()}**")
        st.markdown(f"""
        <div class='detail-header-box'>
            ⏱️ Thời lượng: <b>{active_sc.get('total_estimated_duration', '24s (0.4 phút)')}</b> | 
            🎙 Giọng: <b>{vp.get('gender', 'Nữ')} ({vp.get('tone', 'nhịp độ chuẩn')})</b> | 
            👔 Trang phục & Bối cảnh: <b>{active_sc.get('script_outfit_setup', 'Mặc định theo kịch bản')}</b> | 
            📐 Khung hình: <b>{HARDCODED_ASPECT}</b>
        </div>
        """, unsafe_allow_html=True)
        
        scenes = active_sc.get("scenes", [])
        if isinstance(scenes, dict): scenes = [scenes]
        for idx, scene in enumerate(scenes, 1):
            trans_type = scene.get('transition_type', 'Chuyển cảnh mới (Tạo ảnh mới)')
            st.markdown(f"#### 📍 Phân cảnh {idx} ({scene.get('duration', '8s')}) — [ {trans_type} ]")
            st.markdown(f"🏛 **Bối cảnh & Miêu tả:** *{scene.get('scene_setting', '')}*")
            st.markdown(f"**🎙️ Đạo diễn ngữ điệu & SFX:** *{scene.get('voice_director_vn', '')}*")
            st.markdown(f"**💬 Thoại & Âm thanh (Chuẩn chính tả):** <span class='voiceover-text'>{scene.get('voiceover_vi', '')}</span>", unsafe_allow_html=True)
            
            img_p = scene.get('image_prompt', '')
            is_linked_scene = "nối tiếp" in trans_type.lower() or "dùng lại ảnh cuối" in img_p.lower() or "tham chiếu" in img_p.lower() or "không cần" in img_p.lower()
            
            if is_linked_scene:
                st.info("🔗 **Cảnh nối tiếp:** Không cần tạo ảnh mới. Hãy sử dụng khung hình cuối của Cảnh trước làm ảnh tham chiếu (Image-to-Video) cho cảnh này.")
            else:
                if img_p: 
                    st.markdown(f"**🖼️ Prompt Ảnh (Imagen 3):**")
                    st.code(img_p, language="text")
                    safe_copy_button(img_p, f"📋 Sao Chép Prompt Ảnh Cảnh {idx}")
            
            vid_p = scene.get('video_prompt', '')
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
                    hook_val = outline.get('target_hook', '')
                    if not hook_val or str(hook_val).strip().lower() in ['none', 'null', '']: hook_val = "Kịch bản tập trung làm nổi bật nội dung cốt lõi."
                    st.caption(f"⚡ **Tóm tắt & Hook:** *{hook_val}*")
                with col_btn1:
                    if not is_current:
                        btn_rev_ph = st.empty()
                        if btn_rev_ph.button("👁 Xem lại", key=f"btn_rev_{sc_id}", use_container_width=True):
                            btn_rev_ph.empty()
                            st.session_state.active_script_id = sc_id
                            st.session_state.scroll_to_detail = True
                            st.rerun()
                with col_btn2:
                    btn_clone_ph = st.empty()
                    spin_clone_ph = st.empty()
                    if btn_clone_ph.button("🚀 Nhân bản (Clone)", key=f"btn_clone_{sc_id}", type="primary", use_container_width=True):
                        btn_clone_ph.empty()
                        with spin_clone_ph.container():
                            st.session_state.action_trigger = "clone_script"
                            st.session_state.action_param = sc_id
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
                    hook_val = outline.get('target_hook', '')
                    if not hook_val or str(hook_val).strip().lower() in ['none', 'null', '']: hook_val = "Kịch bản tập trung làm nổi bật nội dung cốt lõi."
                    st.caption(f"⚡ **Tóm tắt & Hook:** *{hook_val}*")
                with col_a2:
                    btn_cre_ph = st.empty()
                    spin_cre_ph = st.empty()
                    if btn_cre_ph.button("✨ Tạo chi tiết ngay", key=f"btn_cre_{sc_id}", type="secondary", use_container_width=True):
                        btn_cre_ph.empty()
                        with spin_cre_ph.container():
                            st.session_state.action_trigger = "create_detail"
                            st.session_state.action_param = sc_id
                            st.rerun()

    st.markdown("---")
    st.markdown("##### ➕ **Tùy Chỉnh & Gọi Thêm Kịch Bản Mới**")
    
    col_g1, col_g2, col_g3 = st.columns([2, 1, 1.5])
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
        chosen_chars = st.number_input("Số diễn viên cho kịch bản mới:", min_value=1, max_value=8, value=1, step=1, key=f"extra_num_chars_callmore_{st.session_state.reset_key}")
    with col_g3:
        duration_choice_more = st.selectbox("⏳ Thời lượng video mới:", ["Tự động (AI Tối ưu ~20-30s)", "Tùy chỉnh (Nhập số giây)"], key=f"dur_choice_more_{st.session_state.reset_key}")
        if duration_choice_more.startswith("Tùy chỉnh"):
            custom_sec_more = st.number_input("Nhập số giây:", min_value=10, max_value=300, value=60, step=5, key=f"dur_sec_more_{st.session_state.reset_key}")
    
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
        spin_more_ph = st.empty()
        if btn_more_ph.button("🚀 Gọi Thêm 5 Kịch Bản Mới", key="btn_execute_more_scripts", type="primary", use_container_width=True):
            btn_more_ph.empty()
            with spin_more_ph.container():
                st.session_state.action_trigger = "generate_more"
                st.session_state.action_param = {"angle": chosen_angle, "chars": chosen_chars}
                st.session_state.temp_extra_char_inputs = extra_char_inputs
                
                if duration_choice_more.startswith("Tùy chỉnh"):
                    st.session_state.target_duration_instruction = f"TỔNG THỜI LƯỢNG YÊU CẦU: Chính xác {custom_sec_more} giây. Bạn PHẢI tạo ra số lượng phân cảnh đủ nhiều (mỗi cảnh 4s, 6s, 8s) sao cho tổng thời gian cộng lại bằng ĐÚNG {custom_sec_more} giây."
                else:
                    st.session_state.target_duration_instruction = "TỔNG THỜI LƯỢNG YÊU CẦU: Tự động (Khoảng 3 đến 5 phân cảnh, tổng 15-30 giây)."
                    
                st.rerun()
