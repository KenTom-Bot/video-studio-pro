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
# 1. CẤU HÌNH GIAO DIỆN & KHỞI TẠO BIẾN STATE
# ==============================================================================
st.set_page_config(page_title="Đạo Diễn AI - Hệ Thống Kịch Bản Pro", page_icon="🎬", layout="wide")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

default_states = {
    "is_logged_in": False,
    "current_email": "",
    "licensed_accounts": {},
    "all_scripts": [],
    "cloned_scripts": [],
    "expanded_scripts": [],
    "generated_details": {},
    "content_analysis": None,
    "active_script_id": None,
    "current_input_context": "",
    "current_product_data_saved": None,
    "current_product_data": None,
    "reset_key": 0,
    "scroll_to_top": False,
    "scroll_to_detail": False,
    "trigger_main_generation": False,
    "trigger_more_generation": False,
    "temp_main_args": {},
    "temp_more_args": {},
    "active_project_title": f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}",
    "last_mode": "🛒 TikTok Shop & Bán Hàng",
    "last_style": "Điện Ảnh Chân Thực",
    "last_narrator": "On-camera",
    "last_presentation_format": "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng",
    "target_duration_instruction": "",
    "character_profiles": [],
    "current_project_id": None,
    "saved_reference_images": [],
    "show_all_projects": False,
    "show_all_admin_accounts": False,
    "current_processing_id": None,
    "current_cloning_id": None,
    "is_analyzed": False,
    "last_autosave_time": ""
}

for k, v in default_states.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.markdown("""
<style>
    .header-container { text-align: center; padding: 1.2rem; background: radial-gradient(circle, rgba(255,75,75,0.08) 0%, rgba(255,255,255,0) 70%); border-radius: 16px; margin-bottom: 1rem; }
    .main-title { font-size: 2.2rem !important; font-weight: 900 !important; background: linear-gradient(90deg, #ff0050 0%, #ff5252 50%, #ff7300 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    div[data-testid="stButton"] > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button[kind="primary"] { background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important; color: white !important; border-radius: 8px !important; font-weight: bold; width: 100%; }
    div[data-testid="stButton"] > button[kind="secondary"], div[data-testid="stFormSubmitButton"] > button[kind="secondary"] { background: linear-gradient(135deg, #ff4b4b 0%, #ff7300 100%) !important; color: #ffffff !important; box-shadow: 0 3px 8px rgba(255, 75, 75, 0.35) !important; padding: 0.55rem 1rem !important; font-weight: bold !important; border: none !important; width: 100%; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 3px 8px; border-radius: 4px; font-size: 11px; border: 1px solid #bbf7d0; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 3px 8px; border-radius: 4px; font-size: 11px; border: 1px solid #fde68a; }
    .autosave-badge { color: #0369a1; font-weight: 700; background: #e0f2fe; padding: 4px 10px; border-radius: 6px; font-size: 12px; border: 1px solid #bae6fd; display: inline-block; margin-top: 4px; }
    .detail-header-box { background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%); border: 1.5px solid #bfdbfe; border-radius: 12px; padding: 12px 16px; margin-bottom: 20px; color: #1e3a8a; line-height: 1.7; box-shadow: 0 2px 8px rgba(0,0,0,0.03); font-size: 14.5px; }
    .preview-script { background: #f8fafc; border-left: 4px solid #3b82f6; padding: 12px 16px; margin-top: 10px; margin-bottom: 10px; border-radius: 6px; font-size: 14.5px; color: #334155; font-style: italic; line-height: 1.7; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02); }
    .voiceover-text { color: #15803d; background: #f0fdf4; padding: 12px 14px; border-radius: 8px; font-size: 15.5px; border: 1px solid #bbf7d0; display: block; width: 100%; margin-top: 4px; line-height: 1.8; white-space: pre-line; }
    .timing-badge { font-size: 13.5px; font-weight: 700; color: #1e40af; background: #dbeafe; padding: 4px 10px; border-radius: 6px; border: 1px solid #bfdbfe; display: inline-block; margin-bottom: 6px; }
    div[data-testid="stFileUploader"] section { padding: 4px; min-height: 2rem; border: 1.5px dashed #cbd5e1 !important; background-color: #f8fafc !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div { background-color: #f8fafc !important; border: 1.5px solid #cbd5e1 !important; border-radius: 8px !important; }
    .dna-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 20px; margin-bottom: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.02); height: 100%; }
    .dna-card-title { font-size: 15.5px; font-weight: 800; color: #1e3a8a; margin-bottom: 12px; padding-bottom: 6px; border-bottom: 1.5px solid #f1f5f9; display: flex; align-items: center; gap: 6px; }
    .dna-row { margin-bottom: 9px; line-height: 1.65; }
    .dna-label { font-weight: 700; color: #0f172a; font-size: 14px; display: inline-block; margin-right: 5px; }
    .dna-text { font-weight: 400 !important; color: #334155 !important; font-size: 14px !important; line-height: 1.65 !important; }
    .no-product-warning { background: #fee2e2; border: 1px solid #fca5a5; padding: 10px; border-radius: 8px; color: #991b1b; font-weight: 700; font-size: 14px; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. TỪ ĐIỂN & QUY TẮC CỐT LÕI
# ==============================================================================
ALL_MODULES = ["🛒 TikTok Shop & Bán Hàng", "🌟 Viral & Xây Kênh"]
ADMIN_EMAIL = "binhnguyenmedia.vn@gmail.com"

UNIFIED_STRATEGY_FORMAT_OPTS = ["🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng", "📦 Review & Bóc Hộp Soi Chi Tiết", "👶 Trải Nghiệm Thực Tế Đời Sống", "⚡ Flash Sale & Deal Hời", "🎭 Giải Quyết Nỗi Đau (PAS)"]

COMPACT_CORE_RULES = """
🛑 QUY TẮC CỐT LÕI (BẮT BUỘC):
1. KOC 100% LÀ NGƯỜI VIỆT NAM & ĐÚNG ĐỘ TUỔI TÙY SẢN PHẨM: Cấm tạo người nước ngoài.
2. HÀNH ĐỘNG & TƯƠNG TÁC (CRITICAL):
   - Cảnh 1 (Nỗi đau): BẮT BUỘC biểu cảm/hành động chân thực (ngứa gãi, hôi bịt mũi).
   - MỸ PHẨM: Công dụng ở đâu bôi ĐÚNG ở đó! CẤM đưa lên mặt nếu ko phải kem mặt.
   - GIA DỤNG/THỜI TRANG: Cấm đưa lên mặt/tai. Tương tác ngang ngực/bàn. KHÔNG thả rơi.
   - 100% KOC nói TRỰC TIẾP vào ống kính.
3. LÕI THOẠI (CHỐNG LIVESTREAM & LÀM MỜ GIÁ):
   - Dồn dập, tự nhiên. Cấm lặp từ, cấm dịch word-by-word.
   - TUYỆT ĐỐI CẤM dùng từ "trên live", "phiên live". Dùng "trong video này", "hôm nay".
   - TUYỆT ĐỐI KHÔNG đọc giá cụ thể. CHỈ dùng khoảng ("hơn trăm cành", "đang sale cực sâu").
4. VĂN NÓI HÀ NỘI THUẦN VIỆT: CẤM dấu chấm lửng (...), ký hiệu ([ ]) trong thoại.
"""

INTIMATE_SAFE_ENGLISH_LEXICON = {r'\b(?:push-?up\s+|lace\s+|wireless\s+|seamless\s+)?bras?\b': 'seamless comfort fabric top', r'\bbrassieres?\b': 'seamless support garment', r'\b(?:lace\s+|cotton\s+|seamless\s+)?panties\b': 'seamless breathable fabric layer', r'\bunderwears?\b': 'soft stretchable fabric base', r'\bbriefs?\b': 'seamless textile base', r'\bthongs?\b': 'seamless stretch fabric', r'\blingerie\b': 'premium textile item', r'\bbikinis?\b': 'resort stretch wear', r'\bcleavage\b': 'modest neckline', r'\bsexy\b': 'elegant', r'\bcrotch\b': 'fabric gusset'}
POLICY_REPLACEMENTS = {r'\ban\s*toàn\s*tuyệt\s*đối\b': 'cực kỳ an toàn', r'\byên\s*tâm\s*tuyệt\s*đối\b': 'cực kỳ yên tâm', r'\btuyệt\s*đối\s*an\s*toàn\b': 'cực kỳ an toàn', r'\b100\s*%\s*an\s*toàn\b': 'rất an toàn', r'\bchữa\s*bệnh\b': 'hỗ trợ sức khỏe', r'\btrị\s*dứt\s*điểm\b': 'hỗ trợ cải thiện hiệu quả', r'\bđặc\s*trị\b': 'sản phẩm chuyên biệt', r'\btrắng\s*cấp\s*tốc\b': 'sáng khỏe tự nhiên', r'\btrợ\s*giá\b': 'ưu đãi cực hời', r'\bphiên\s*live\b': 'trong video này', r'\btrên\s*live\b': 'đợt này', r'\blivestream\b': 'video này', r'\bđang\s*live\b': 'đang sale'}
SOUTHERN_TO_HANOI = {r'\blụa\s+premium\s+everyday\b': 'lụa cao cấp', r'\blụa\s+lustrous\s+satin(?:\s+silk)?\b': 'lụa cao cấp', r'\bmềm\s*rủ\b': 'mềm rũ', r'\bsiêu\s*rủ\b': 'siêu rũ', r'\bđộ\s*rủ\b': 'độ rũ', r'\brủ\s*xuống\b': 'rũ xuống', r'\báp\s*mã\b': 'nay giảm', r'\báp\s*voucher\b': 'nay giảm', r'\b1\s*trăm\s*(?:tư|tứ|bốn)?\s*mươi\b': 'một trăm bốn mươi', r'\b1\s*trăm\s*(?:tư|tứ)\b': 'một trăm bốn mươi', r'\bmột\s*trăm\s*(?:tư|tứ)\s*mươi\b': 'một trăm bốn mươi', r'\bmột\s*trăm\s*(?:tư|tứ)\b': 'một trăm bốn mươi', r'\btrăm\s*(?:tư|tứ)\s*mươi\b': 'trăm bốn mươi', r'\btrăm\s*(?:tư|tứ)\b': 'trăm bốn mươi', r'\b(?:tư|tứ)\s+mươi\b': 'bốn mươi', r'\bmười\s+(?:tư|tứ)\b': 'mười bốn', r'\bnghìn\s+(?:tư|tứ)\b': 'nghìn bốn trăm', r'\b1\s+trăm\b': 'một trăm', r'\b1\s+nghìn\b': 'một nghìn', r'\b1\s+triệu\b': 'một triệu', r'\b140\s*(?:k|nghìn|ngàn)\b': 'một trăm bốn mươi nghìn', r'\b140\b': 'một trăm bốn mươi', r'\b14\b': 'mười bốn', r'\b24\b': 'hai mươi bốn', r'\b34\b': 'ba mươi bốn', r'\b40\b': 'bốn mươi', r'\b44\b': 'bốn mươi bốn', r'\b4\b': 'bốn', r'\bmười\s+(?:tư|tứ)\b': 'mười bốn', r'\bhai\s+(?:tư|tứ)\b': 'hai mươi bốn', r'\bba\s+(?:tư|tứ)\b': 'ba mươi bốn', r'\b(?:tư|tứ)\s+mươi\b': 'bốn mươi', r'\b(\w+)\s+mươi\s+(?:tư|tứ)\b': r'\1 mươi bốn', r'\bnăm\s+(?:tư|tứ)\b': 'năm mươi bốn', r'\bsáu\s+(?:tư|tứ)\b': 'sáu mươi bốn', r'\bbảy\s+(?:tư|tứ)\b': 'bảy mươi bốn', r'\btám\s+(?:tư|tứ)\b': 'tám mươi bốn', r'\bchín\s+(?:tư|tứ)\b': 'chín mươi bốn', r'\bhai\s+(?:tư|tứ)\b': 'hai mươi bốn', r'\bba\s+(?:tư|tứ)\b': 'ba mươi bốn', r'\bhăm\s+(?:tư|tứ)\b': 'hai mươi bốn', r'\bba\s*rọi\b': 'ba chỉ', r'\bchiên\s*(?:giòn|phồng|ngập\s*dầu)?\b': 'rán giòn', r'\bchiên\b': 'rán', r'\báo\s*(?:đều|lớp\s*sốt|sốt)\b': 'ngấm đẫm sốt', r'\bcay\s*the\b': 'cay tê', r'\bthe\s*the\b': 'tê tê', r'\bsánh\s*dẻo\b': 'sền sệt', r'\bkẹo\s*lại\b': 'sệt lại', r'\bđậu\s*phộng\b': 'hạt lạc', r'\btrái\s*cây\s*dầm\b': 'hoa quả dầm', r'\btrái\s*cây\b': 'hoa quả', r'\brỗng\s*ruột\b': 'xốp tan', r'\bcực\s*kỳ\s*vừa\s*vặn\b': 'vừa miệng dã man', r'\bđã\s*cái\s*nư\b': 'đã miệng cực kỳ', r'\bxả\s*sơ(?:\s*qua)?\b': 'tráng qua', r'\bxả\s*nước\b': 'tráng nước', r'\brải\s+vào\b': 'xếp vào', r'\brải\b(?=\s+[a-zà-ỹ]+)': 'cho', r'\brửa\s*chén\b': 'rửa bát', r'\bnước\s*rửa\s*chén\b': 'nước rửa bát', r'\bly\s+nước\b': 'cốc nước', r'\bly\s+trà\b': 'cốc trà', r'\bly\s+đá\b': 'cốc đá', r'\bly\b(?=\s+(?:uống|nước|thủy tinh|nhựa))': 'cốc', r'\bmuỗng\b': 'thìa', r'\bbàn\s*ủi\b': 'bàn là', r'\bbao\s*rác\b': 'túi rác', r'\bchổi\s*lông\s*gà\b': 'chổi phất trần', r'\bkhít\s+tai\s+êm\s+ái\b': 'vừa khít mà êm ru', r'\bêm\s+ái\b': 'êm ru', r'\bvỏ\s*ngoài\b': 'bên ngoài', r'\bnét\s+căng\b': 'rõ mồn một', r'\bpin\s*trâu\b': 'pin dùng trâu bò', r'\bsạc\s*lẹ\b': 'sạc nhanh', r'\bthấm\s*lẹ\b': 'thấm nhanh', r'\bbết\s*rít\b': 'nhờn dính', r'\bđầm\b': 'váy', r'\báo\s*thun\b': 'áo phông', r'\bmang\s*giày\b': 'đi giày', r'\bmang\s*dép\b': 'đi dép', r'\bdây\s*nịt\b': 'thắt lưng', r'\bbóp\s*tiền\b': 'ví tiền', r'\bngàn\b': 'nghìn', r'\bxài\b': 'dùng', r'\bgiùm\b': 'hộ', r'\bdùm\b': 'hộ', r'\btui\b': 'tôi', r'\bhén\b': 'nhỉ', r'\bnghen\b': 'nhé', r'\bhen\b': 'nhé', r'\brùi\b': 'rồi', r'\bmần\b': 'làm', r'\bkiếng\b': 'kính', r'\bhổng\b': 'không', r'\bthiệt\b': 'thật', r'\bmắc\s+cỡ\b': 'ngại', r'\bhết\s+sẩy\b': 'tuyệt cú mèo', r'\brẻ\s+bèo\b': 'rẻ thế', r'\bquá\s+trời\b': 'rất nhiều', r'\bquá\s+chừng\b': 'rất nhiều', r'\bnè\b': 'này', r'\bnha\b': 'nhé', r'\bcưng\s+xỉu\b': 'yêu cực kỳ', r'\bcoi\b': 'xem', r'\bmua\s+liền\b': 'mua ngay'}

# ==============================================================================
# 3. KẾT NỐI API & DB
# ==============================================================================
@st.cache_resource(show_spinner=False)
def init_supabase():
    try:
        url, key = st.secrets.get("SUPABASE_URL", ""), st.secrets.get("SUPABASE_KEY", "")
        if url and key: return create_client(url, key)
    except Exception: pass
    return None

@st.cache_resource(show_spinner=False)
def init_gemini_client():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if api_key: return genai.Client(api_key=api_key)
    except Exception: pass
    return None

supabase = init_supabase()
client = init_gemini_client()

def load_licensed_accounts():
    accs = {ADMIN_EMAIL: {"roles": ALL_MODULES, "phone": "0869628316", "expires_at": "2099-12-31", "password": "admin", "plan_type": "VIP", "active_session_id": ""}}
    if not supabase: return accs
    try:
        res = supabase.table("licensed_accounts").select("*").limit(200).execute()
        for row in (res.data or []):
            accs[row["email"]] = {
                "roles": row.get("roles", ALL_MODULES), "phone": row.get("phone", ""),
                "password": row.get("password", ""), "expires_at": row.get("expires_at", "2099-12-31"),
                "plan_type": row.get("plan_type", "Trial"), "daily_usage_count": row.get("daily_usage_count", 0),
                "last_generation_date": "", "active_session_id": ""
            }
    except Exception: pass
    return accs

if not st.session_state.get("licensed_accounts"):
    st.session_state.licensed_accounts = load_licensed_accounts()

is_system_busy = (
    st.session_state.get("current_processing_id") is not None or 
    st.session_state.get("current_cloning_id") is not None or
    st.session_state.get("trigger_main_generation") is True or
    st.session_state.get("trigger_more_generation") is True
)

# ==============================================================================
# 4. GỌI GEMINI API
# ==============================================================================
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
    open_curly, open_square = candidate.count('{') - candidate.count('}'), candidate.count('[') - candidate.count(']')
    candidate += (']' * max(0, open_square)) + ('}' * max(0, open_curly))
    try: return json.loads(candidate, strict=False)
    except: pass
    try:
        py_str = candidate.replace('true', 'True').replace('false', 'False').replace('null', 'None')
        parsed = ast.literal_eval(py_str)
        return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict) else parsed
    except: pass
    raise Exception("Lỗi khi đọc kết quả từ AI. Vui lòng thử lại.")

def call_gemini(contents, sys_inst="Bạn là AI hỗ trợ JSON.", max_tokens=4096):
    if not client: raise Exception("Chưa cấu hình GEMINI_API_KEY trong Streamlit Secrets.")
    models_to_try = ["gemini-3.8-flash", "gemini-3.8-flash-lite"]
    last_exception = None
    for model_name in models_to_try:
        for attempt in range(3):
            try:
                res = client.models.generate_content(
                    model=model_name, contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_inst, response_mime_type="application/json",
                        temperature=0.65, max_output_tokens=max_tokens
                    )
                )
                return repair_and_parse_json(res.text)
            except Exception as e:
                last_exception = e
                err_str = str(e).lower()
                if "404" in err_str or "not_found" in err_str: break
                if "503" in err_str or "unavailable" in err_str or "429" in err_str or "resource_exhausted" in err_str:
                    time.sleep((attempt + 1) * 1.2); continue
                time.sleep(0.6)
    if last_exception: raise last_exception

def get_sys_inst_outlines(mode, angle, custom_note=""):
    is_viral = ("Viral" in mode)
    goal = "VIRAL (Mẹo/kiến thức, KHÔNG bán hàng)" if is_viral else "TIKTOK SHOP (Bán hàng, chốt deal)"
    return f"ĐẠO DIỄN TIKTOK PRO | MỤC TIÊU: {goal} | CHIẾN LƯỢC: {angle}\n🛑 GHI CHÚ: {custom_note}\n{COMPACT_CORE_RULES}"

def get_sys_inst_details(mode, custom_note="", self_pronoun="em", audience_pronoun="các chị em", is_pas_story=False):
    pas_flow = "PAS Flow: Cảnh 1 tại nhà nêu nỗi đau (KHÔNG có SP) -> Cảnh 2,3,4 có SP." if is_pas_story else "Direct Flow: SP làm TRỌNG TÂM xuyên suốt 4 cảnh."
    return f"ĐẠO DIỄN TIKTOK PRO | Xưng '{self_pronoun}' - Gọi '{audience_pronoun}' | {pas_flow}\n🛑 GHI CHÚ: {custom_note}\n{COMPACT_CORE_RULES}"

# ==============================================================================
# 5. CÁC HÀM TIỆN ÍCH CHUNG
# ==============================================================================
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
    acc = st.session_state.get("licensed_accounts", {}).get(email)
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

def save_project_to_db(email, title, payload_data, project_id=None):
    if not supabase: return False, "Chưa kết nối DB."
    try:
        clean_content = json.loads(json.dumps(payload_data, default=str))
        if project_id:
            res = supabase.table("saved_projects").update({"project_title": title, "script_content": clean_content}).eq("id", project_id).execute()
            if res.data:
                st.session_state.last_autosave_time = datetime.now().strftime("%H:%M:%S")
                return True, f"Đã cập nhật '{title}'!"
        res = supabase.table("saved_projects").insert({"user_email": email, "project_title": title, "script_content": clean_content}).execute()
        if res.data:
            st.session_state.current_project_id = res.data[0]['id']
            st.session_state.last_autosave_time = datetime.now().strftime("%H:%M:%S")
            return True, f"Đã lưu '{title}'!"
        return False, "Không thể lưu dự án."
    except Exception as e: return False, str(e)

def auto_save_current_session():
    if not st.session_state.get("is_logged_in", False) or not supabase: return False, ""
    try:
        dedup_details = {str(k): v for k, v in st.session_state.get("generated_details", {}).items()}
        st.session_state.generated_details = dedup_details
        payload = {
            "content_analysis": st.session_state.get("content_analysis"),
            "all_scripts": st.session_state.get("all_scripts", []),
            "cloned_scripts": st.session_state.get("cloned_scripts", []),
            "expanded_scripts": st.session_state.get("expanded_scripts", []),
            "generated_details": dedup_details,
            "character_profiles": st.session_state.get("character_profiles", []),
            "current_input_context": st.session_state.get("current_input_context", ""),
            "is_analyzed": st.session_state.get("is_analyzed", False)
        }
        return save_project_to_db(st.session_state.get("current_email", ""), st.session_state.get("active_project_title", ""), payload, st.session_state.get("current_project_id"))
    except: return False, ""

def count_words(text: str) -> int: return len(re.findall(r'\b\w+\b', text)) if text else 0

def calculate_speech_duration(text: str, is_tiktok_shop: bool = True) -> float:
    words = count_words(text)
    commas, periods = text.count(',') + text.count(';'), text.count('.') + text.count('!') + text.count('?')
    return round((words / (4.8 if is_tiktok_shop else 4.0)) + (commas * (0.08 if is_tiktok_shop else 0.12)) + (periods * (0.12 if is_tiktok_shop else 0.20)), 1)

def compress_image_bytes(uploaded_file, max_dimension=768, quality=75):
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        out_buffer = io.BytesIO()
        img.save(out_buffer, format="JPEG", quality=quality, optimize=True)
        return out_buffer.getvalue(), "image/jpeg"
    except: return uploaded_file.getvalue(), (uploaded_file.type or "image/jpeg")

def clean_html(raw_html: str) -> str: return "\n".join(line.strip() for line in raw_html.strip().splitlines() if line.strip()) if raw_html else ""

def safe_copy_button(text_to_copy: str, button_label: str = "📋 Sao Chép Prompt", custom_color: str = "#16a34a"):
    b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    html_id = f"btn_{uuid.uuid4().hex[:8]}"
    html_code = f"""
    <button id="{html_id}" style="background:{custom_color}; color:white; border:none; padding:7px 14px; font-size:12.5px; font-weight:700; border-radius:6px; cursor:pointer; width:100%; transition: 0.2s;">{button_label}</button>
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
    components.html(html_code, height=42)

def extract_bold_product_title(ca_data: dict, fallback_topic: str = "") -> str:
    raw = str(ca_data.get("name", "")).strip()
    if not raw and fallback_topic: raw = fallback_topic.strip()
    if not raw: return f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
    return f"{re.sub(r'[\[\]\*\"\'`]', '', raw).strip()[:52]}... ({datetime.now().strftime('%d/%m')})"

def number_to_vietnamese_words(n: int) -> str:
    if n == 0: return "không đồng"
    digits = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    def read_block_3(num_str, is_highest=False):
        num_str = num_str.zfill(3)
        h, t, u = int(num_str[0]), int(num_str[1]), int(num_str[2])
        res = []
        if not is_highest or h > 0: res.append(digits[h] + " trăm")
        if t == 0 and u == 0: pass
        elif t == 0 and u != 0: res.append(("linh " if (not is_highest or h > 0) else "") + digits[u])
        elif t == 1:
            res.append("mười")
            if u == 1: res.append("một")
            elif u == 4: res.append("bốn")
            elif u == 5: res.append("lăm")
            elif u != 0: res.append(digits[u])
        else:
            res.append(digits[t] + " mươi")
            if u == 1: res.append("mốt")
            elif u == 4: res.append("bốn")
            elif u == 5: res.append("lăm")
            elif u != 0: res.append(digits[u])
        return " ".join(res)
    
    s = str(abs(n))
    groups = []
    while s: groups.append(s[-3:]); s = s[:-3]
    units = ["", "nghìn", "triệu", "tỷ"]
    result_parts = []
    for i in range(len(groups) - 1, -1, -1):
        val = int(groups[i])
        if val > 0:
            part = read_block_3(groups[i], is_highest=(i == len(groups) - 1))
            if units[i]: part += " " + units[i]
            result_parts.append(part)
    return re.sub(r'\s+', ' ', " ".join(result_parts).strip()).strip() + " đồng"

def extract_and_convert_prices_in_text(raw_text: str) -> str:
    if not raw_text: return ""
    def replace_k(match): return number_to_vietnamese_words(int(match.group(1)) * 1000).replace(" đồng", "")
    text = re.sub(r'\b(\d{1,4})\s*[kK]\b', replace_k, raw_text)
    def replace_num(match):
        try:
            val = int(match.group(1).replace('.', '').replace(',', ''))
            if val >= 1000: return number_to_vietnamese_words(val).replace(" đồng", "")
        except: pass
        return match.group(0)
    return re.sub(r'(\b\d{1,3}(?:[.,]\d{3})+\b)', replace_num, text)

def convert_to_soft_price_range(price_num: int, is_orig: bool = False) -> str:
    if not price_num: return "giá niêm yết" if is_orig else "deal cực hời"
    val = int(price_num)
    if is_orig:
        if 100000 <= val <= 125000: return "gần một trăm hai mươi nghìn"
        elif val > 1000000: return f"gần {number_to_vietnamese_words(math.ceil(val / 1000000) * 1000000).replace(' đồng', '')}"
        elif val > 100000:
            ceil_h = math.ceil(val / 100000) * 100000
            if val % 100000 > 70000: return f"gần {number_to_vietnamese_words(ceil_h).replace(' đồng', '')}"
            return f"gần {number_to_vietnamese_words(math.ceil(val / 10000) * 10000).replace(' đồng', '')}"
        else: return f"gần {number_to_vietnamese_words(math.ceil(val / 10000) * 10000).replace(' đồng', '')}"
    else:
        if val < 50000: return "mấy chục nghìn"
        elif val < 100000: return f"hơn {number_to_vietnamese_words(math.floor(val / 10000) * 10000).replace(' đồng', '')}"
        elif val < 1000000: return f"hơn {number_to_vietnamese_words(math.floor(val / 100000) * 100000).replace(' đồng', '')}"
        else: return f"hơn {number_to_vietnamese_words(math.floor(val / 1000000) * 1000000).replace(' đồng', '')}"

# ==============================================================================
# 6. KHỐI HÀM NLP (LÀM SẠCH VĂN BẢN VÀ CHỐNG VẤP THOẠI)
# ==============================================================================
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
    return cleaned

def sanitize_third_party_ip(text: str) -> str:
    if not text: return ""
    cleaned = text
    for p in [r'\btiktok\s*(?:shop)?\b', r'\bshopee\b', r'\blazada\b', r'\bfacebook\b', r'\binstagram\b', r'\byoutube\b']: 
        cleaned = re.sub(p, 'online store', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\blụa\s*titan\b', 'lustrous satin silk', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\btitan\b', 'lustrous satin', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:emoon|disney|marvel|spider-?man|spiderman|nike|adidas|gucci|chanel|dior|lv|louis\s+vuitton|zara|uniqlo|apple|samsung|xiaomi|dyson|philips|vaseline|lego|barbie)\b', 'premium everyday', cleaned, flags=re.IGNORECASE)
    for pattern, safe_term in INTIMATE_SAFE_ENGLISH_LEXICON.items(): 
        cleaned = re.sub(pattern, safe_term, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bwearing\s+wearing\b', 'wearing', cleaned, flags=re.IGNORECASE)
    return re.sub(r'\.\.+', '.', cleaned)

def clean_and_normalize_voiceover(text: str) -> str:
    if not text: return ""
    cleaned = sanitize_policy_text(text)
    cleaned = extract_and_convert_prices_in_text(cleaned)
    for pattern, rep in [
        (r'\bform\s*hộp\s*đứng\s*form\b', 'form hộp cứng cáp'), (r'\bform\s*dáng\s*đứng\s*form\b', 'lên dáng chuẩn xác'),
        (r'\bđứng\s*form\b', 'giữ form'), (r'\bchuẩn\s*form\b', 'lên dáng chuẩn'),
        (r'\bcực\s*nét\b', 'cực xịn'), (r'\bđang\s*giảm\s*giá\s*sâu\s*có\s*hạn\b', 'đang có deal cực hời'),
        (r'\bchốt\s*đơn\s*ngay\s*tay\b', 'chốt ngay kẻo lỡ'), (r'\bchốt\s*ngay\s*tay\b', 'chốt liền tay'),
        (r'\bliền\s*tay\b', 'ngay nhé'), (r'\bvừa\s*vặn\s*vừa\b', 'rất vừa vặn'),
        (r'\bsang\s*chảnh\s*sang\b', 'cực kỳ sang chảnh'), (r'\bđẹp\s*đẹp\b', 'tuyệt đẹp')
    ]: cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'[\(\)\[\]\{\}]', '', cleaned)
    cleaned = re.sub(r'\.{2,}', ',', cleaned)
    cleaned = re.sub(r'[-~*]', '', cleaned)
    
    cleaned = re.sub(r'\b(\w+(?:\s+\w+){1,3})\s+\1\b', r'\1', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(là|và|thì|mà|có|đang|đã|sẽ|giá|các|những|một|chiếc|cái|em|mình|tôi|bạn|mua|bấm|chốt|nhanh|này|kia|đó|đây|quá|rất|cực)\s+\1\b', r'\1', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\bgiá\s*đang\s*giá\b', 'giá đang', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bgiảm\s*giá\s*giảm\s*giá\b', 'giảm giá', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bđang\s*có\s*đang\s*có\b', 'đang có', cleaned, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', cleaned).strip()

def clean_analysis_text(text) -> str:
    if not text: return ""
    res = re.sub(r'^(?:SẢN PHẨM LÀ GÌ\s*&?\s*(?:CÓ GÌ ĐẶC BIỆT)?|SẢN PHẨM DÀNH CHO AI|TẠI SAO NÊN MUA|DÙNG Ở ĐÂU\s*&?\s*(?:TIỆN LỢI LÀ GÌ)?|CÁCH SỬ DỤNG|THAO TÁC.*|MỤC ĐÍCH|ĐỐI TƯỢNG|LÝ DO MUA)\s*:\s*', '', str(text).strip(), flags=re.IGNORECASE).strip()
    return clean_and_normalize_voiceover(res)

# 🌟 ĐÃ KHÔI PHỤC HÀM FORMAT TÊN SẢN PHẨM
def format_product_name_bold(text: str) -> str:
    if not text: return ""
    clean = clean_analysis_text(text)
    if ":" in clean: 
        parts = clean.split(":", 1)
        return f"<b style='color:#0f172a; font-weight:800; font-size:15px;'>{parts[0].strip()}</b>: {parts[1].strip()}"
    elif " - " in clean: 
        parts = clean.split(" - ", 1)
        return f"<b style='color:#0f172a; font-weight:800; font-size:15px;'>{parts[0].strip()}</b> - {parts[1].strip()}"
    return f"<b style='color:#0f172a; font-weight:800; font-size:15px;'>{clean}</b>"

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict): return "<br>".join([f"<span class='dna-label'>{str(k).replace('_', ' ').title()}:</span> <span class='dna-text'>{clean_analysis_text(v)}</span>" for k, v in field_val.items()])
    if isinstance(field_val, list): return "<br>".join([f"<div class='dna-bullet'>• <span class='dna-text'>{clean_analysis_text(item)}</span></div>" for item in field_val])
    val_str = clean_analysis_text(str(field_val))
    return "".join([f"<div class='dna-bullet'>• <span class='dna-text'>{line.strip()}</span></div>" for line in val_str.split('<br>') if line.strip()])

def extract_scenes(parsed_data):
    if isinstance(parsed_data, list): return parsed_data
    if isinstance(parsed_data, dict):
        for key in ["scenes", "scripts", "script", "outlines", "video_scenes", "data"]:
            if key in parsed_data and isinstance(parsed_data[key], list):
                return parsed_data[key]
        for k, v in parsed_data.items():
            if isinstance(v, dict):
                for key in ["scenes", "scripts", "script", "outlines"]:
                    if key in v and isinstance(v[key], list): return v[key]
    return []

# ==============================================================================
# 7. KHỐI HÀM VẬT LÝ, GÓC MÁY & MÀU SẮC ĐỘNG
# ==============================================================================
def detect_food(text_to_check: str) -> bool: return any(k in text_to_check.lower() for k in ["đồ ăn", "thức ăn", "bánh", "kẹo", "nước", "sữa", "trà", "cafe", "món ăn", "thực phẩm", "food", "snack"])
def detect_cosmetics(text_to_check: str) -> bool: return any(k in text_to_check.lower() for k in ["kem dưỡng", "son", "môi", "serum", "phấn", "tẩy trang", "mặt nạ", "sữa rửa mặt", "kem chống nắng", "toner", "lotion", "khử mùi", "nách", "má", "blush", "cheek"])
def detect_mom_baby(text_to_check: str) -> bool: return any(k in text_to_check.lower() for k in ["bỉm", "tã", "sữa bột", "đồ chơi trẻ em", "bình sữa", "ti giả", "xe đẩy", "nôi", "mẹ và bé"])
def detect_mom_baby_hard_props(text_to_check: str) -> bool: return any(k in text_to_check.lower() for k in ["bình sữa", "xe đẩy", "đồ chơi", "nôi"])
def detect_medicine(text_to_check: str) -> bool: return any(k in text_to_check.lower() for k in ["viên uống", "thuốc", "thực phẩm chức năng", "vitamin", "collagen", "giảm cân", "tpcn"])
def detect_single_tube_skirt(text_to_check: str) -> bool: return any(k in text_to_check.lower() for k in ["1 ống", "một ống", "quần váy", "váy 1 ống", "dạng váy", "quần giả váy", "single tube"])
def enforce_single_tube_skirt_syntax(text_en: str) -> str:
    cleaned = text_en
    for pat in [r'\bwide-?leg\s+(?:silk\s+)?(?:skirt-?pants|pants|trousers)\b', r'\bskirt-?pants\b', r'\bsilk\s+(?:pants|trousers)\b', r'\bflowing\s+(?:pants|trousers)\b', r'\bloose\s+(?:pants|trousers)\b', r'\bpants\b', r'\btrousers\b']: 
        cleaned = re.sub(pat, 'full-length A-line maxi skirt (single unified unsplit skirt tube, zero leg division)', cleaned, flags=re.IGNORECASE)
    return cleaned

def detect_strict_rigid_appliance(text_to_check: str) -> bool:
    return any(k in text_to_check.lower() for k in [
        "cốc", "ly", "bình", "tumbler", "cup", "bottle", "mug", "giỏ", "rổ", "kệ", "hộp", "thùng", "tủ", "móc", "chậu", "cây lau", "bàn chải", "máy giặt", "túi đựng", "khay", "nồi", "chảo", "dao", "thớt", "máy xay", "bếp", "ghế", "bàn", "đèn", "quạt", "máy sấy", "bàn là", "bàn ủi", "hút bụi", "tai nghe", "điện thoại", "loa", "sạc", "chuột", "bàn phím", "ví", "power bank", "sạc dự phòng"
    ])

def translate_and_lock_color_en(color_vi: str, ai_color_en: str = "") -> str:
    c = f"{color_vi} {ai_color_en}".lower().strip()
    if any(k in c for k in ["họa tiết", "hoa", "sọc", "pattern", "floral", "plaid", "stripe", "checkered", "print", "gradient"]):
        return f"exact reference-matching pattern and colors ({ai_color_en})"
    if ai_color_en and len(ai_color_en.strip()) > 2:
        return f"exact reference-matching {ai_color_en.strip()}"
    return "exact reference-matching color and pattern"

def sanitize_destructive_motion_verbs(action_text: str, is_fashion: bool = False, is_food: bool = False) -> str:
    cleaned = action_text
    if not is_fashion and not is_food:
        for pat, rep in [(r'\bunfolding\b', 'holding steadily'), (r'\bfolding\b', 'holding securely'), (r'\bcollapsing\b', 'presenting up close'), (r'\bflexing\b', 'pressing fingers gently on'), (r'\bbending\b', 'tilting slightly'), (r'\btwisting\b', 'holding firmly'), (r'\btransforming\b', 'showcasing'), (r'\bdeforming\b', 'presenting'), (r'\bstretching\b', 'tracing fingers along'), (r'\bsqueezing\b', 'gripping firmly'), (r'\bdropping\b', 'holding securely'), (r'\bfalling\b', 'staying firmly in hand'), (r'\bthrowing\b', 'holding firmly'), (r'\btossing\b', 'presenting carefully'), (r'\bletting\s+go\b', 'holding firmly'), (r'\b(?:turning|swaying|spinning|walking|stepping|dancing|moving around|tracking)\b', 'standing still')]:
            cleaned = re.sub(pat, rep, cleaned, flags=re.IGNORECASE)
    return cleaned

def extract_environmental_lighting_and_weather(vo_text: str, setting_text: str = ""):
    combined = f"{vo_text} {setting_text}".lower()
    is_indoor = not any(k in combined for k in ["ngoài trời", "sân vườn", "đường phố", "công viên", "vỉa hè", "ban công", "sân thượng", "dã ngoại", "bãi biển", "outdoor", "street", "garden"])
    if any(k in combined for k in ["đêm", "tối", "khuya", "tắt đèn", "mất điện", "đi ngủ", "night", "dark"]): return "dimly lit, cinematic low light, dark ambience", "quiet nighttime ambience (no reverb)"
    elif any(k in combined for k in ["mưa", "ẩm ướt", "nồm"]): return ("rain droplets on window, soft overcast indoor lighting" if is_indoor else "light rain, wet ground, overcast sky"), "subtle rain ambience (no reverb)"
    elif any(k in combined for k in ["nắng", "trưa hè"]): return ("warm sunbeams through window" if is_indoor else "sunny daylight, golden sunbeams"), "subtle breeze ambience (no reverb)"
    elif any(k in combined for k in ["sáng sớm", "buổi sáng", "bình minh"]): return "fresh morning sunlight", "subtle morning ambience (no reverb)"
    elif any(k in combined for k in ["hoàng hôn", "chiều tà", "buổi chiều"]): return "warm amber sunset glow", "subtle evening ambience (no reverb)"
    return ("clean natural daylight with soft warm fill light" if is_indoor else "bright commercial daylight"), ""

def sanitize_veo3_prompt(prompt_text: str) -> str:
    p = re.sub(r'\bgesturing\s+(?:warmly\s+)?(?:toward\s+)?corner\b', 'sharing recommendations with an open-palm gesture', prompt_text, flags=re.IGNORECASE)
    return sanitize_third_party_ip(re.sub(r'\bpointing\s+(?:downward\s+)?(?:to\s+)?(?:corner|cart)\b', 'speaking with welcoming open hands', p, flags=re.IGNORECASE))

def generate_char_rules_string(profiles):
    if not profiles: return "100% Vietnamese persona, natural black hair, consistent outfit across 3 scenes."
    return " | ".join([f"Actor {p['id']} ({p['role']}): 100% Vietnamese persona, consistent look across scenes" for p in profiles])

def is_pas_storytelling_strategy(strategy_str: str, title_str: str = "") -> bool:
    return any(k in f"{strategy_str} {title_str}".lower() for k in ["nỗi đau", "pas", "đời sống", "lifestyle", "pov", "tình huống", "hài hước", "đời thường"])

def detect_intimate_apparel(text_to_check: str) -> str:
    t = text_to_check.lower()
    if any(k in t for k in ["áo lót", "quần lót", "đồ lót", "nội y", "áo ngực", "su đúc", "quần chip", "quần sịp", "bikini", "đồ bơi", "váy ngủ", "đồ ngủ", "miếng dán ngực", "dung dịch vệ sinh", "bra", "panties", "underwear", "lingerie", "briefs", "thong"]): return "underwear_bra"
    if any(k in t for k in ["áo 2 dây", "áo hai dây", "áo ống", "áo quây", "camisole", "spaghetti strap"]): return "camisole"
    return "normal"

def detect_wearable_fashion(text_to_check: str) -> bool:
    t = text_to_check.lower()
    if any(k in t for k in ["giỏ", "kệ", "hộp", "thùng", "tủ", "móc", "chậu", "cây lau", "bàn chải", "máy giặt", "túi đựng", "rổ", "khay", "basket", "rack", "organizer", "bin", "box", "hamper"]): return False
    return any(k in t for k in ["áo", "quần", "váy", "đầm", "hoodie", "sweater", "blazer", "jacket", "shirt", "pants", "jeans", "shorts", "t-shirt", "set đồ", "bộ đồ", "cardigan", "polo", "chân váy", "pijama", "tất", "vớ", "socks", "tights", "stocking"])

def detect_footwear_or_accessory(text_to_check: str) -> bool:
    t = text_to_check.lower()
    if any(k in t for k in ["giỏ", "rổ", "thùng", "hộp", "kệ", "basket", "hamper", "organizer", "bin"]): return False
    return any(k in t for k in ["giày", "dép", "sneaker", "boot", "sandal", "heel", "túi xách", "ví", "balo", "mũ", "nón", "kính", "thắt lưng", "đồng hồ", "trang sức", "dây chuyền", "nhẫn", "khuyên tai", "shoe", "handbag", "backpack", "wallet", "watch", "glasses", "tất", "vớ", "socks"])

def detect_long_handle_tool(text_to_check: str) -> bool:
    return any(k in text_to_check.lower() for k in ["cây lau", "chổi", "cây chà", "bàn chải cán dài", "mop", "broom", "long-handled", "long handle"])

def get_cosmetic_target(product_name, check_str):
    p_cos = f"{product_name} {check_str}".lower()
    if any(k in p_cos for k in ["má", "blush", "cheek"]): return "cheeks", "instantly leaving a soft, natural, and radiant flush of color smoothly blended onto the skin"
    elif any(k in p_cos for k in ["môi", "lip", "son"]):
        if any(k in p_cos for k in ["dưỡng", "nẻ", "sáp", "balm", "chapstick", "mask", "vaseline", "treatment"]): return "lips", "instantly leaving a clear, highly glossy, deeply hydrated and plump finish without altering the natural lip color"
        else: return "lips", "instantly leaving a highly precise, rich and vibrant colored stroke exactly where applied"
    elif any(k in p_cos for k in ["tóc", "gội", "xả", "hair", "shampoo", "conditioner"]): return "hair", "instantly leaving the hair visibly smooth, silky and shiny"
    elif any(k in p_cos for k in ["nách", "khử mùi", "armpit", "deodorant"]): return "armpit", "instantly absorbing into the skin"
    elif any(k in p_cos for k in ["tay", "body", "cơ thể", "hand", "lotion", "toàn thân", "nail", "móng"]): return "hands/arms/body", "instantly absorbing and leaving a glowing, hydrated finish"
    else: return "facial skin", "instantly absorbing and disappearing, leaving a highly glossy, hydrated, glowing glass-skin finish"

def get_product_centric_camera_shot(scene_idx, is_fashion, is_footwear_acc, is_pas_scene1, clean_prod_en, is_strict_appliance, is_long_handle, is_food, is_cosmetics, is_mom_baby, is_medicine, intimate_type, check_str):
    if is_pas_scene1 and not is_fashion: return "Vertical 9:16 stable dynamic shot framing the character and the specific problem"
    
    if intimate_type != "normal":
        if scene_idx == 0: return f"Vertical 9:16 stable medium shot, character in a silk robe holding {clean_prod_en}"
        elif scene_idx == 1: return f"Vertical 9:16 stable tight macro close-up focused strictly on hands interacting with {clean_prod_en}"
        elif scene_idx == 2: return f"Vertical 9:16 stable macro close-up on the fabric details of {clean_prod_en}"
        else: return f"Vertical 9:16 stable balanced shot focusing on hands holding {clean_prod_en}"

    if is_footwear_acc:
        if scene_idx == 0: return f"Vertical 9:16 stable low-angle full-body shot focusing heavily on the legs and feet displaying {clean_prod_en}"
        elif scene_idx == 1: return f"Vertical 9:16 stable medium close-up focused on the hands holding {clean_prod_en} securely to show material details"
        elif scene_idx == 2: return f"Vertical 9:16 stable tight close-up focused on the hands forcefully bending and testing the flexibility of {clean_prod_en}"
        else: return f"Vertical 9:16 stable low-angle balanced shot highlighting the feet with {clean_prod_en}"

    if is_food or is_medicine:
        if scene_idx == 0: return f"Vertical 9:16 stable warm inviting medium shot, displaying {clean_prod_en}"
        elif scene_idx == 1: return f"Vertical 9:16 stable macro close-up shot focused deeply on the texture/details of {clean_prod_en}"
        elif scene_idx == 2: return f"Vertical 9:16 stable dynamic close-up action shot showing interaction with {clean_prod_en}"
        else: return f"Vertical 9:16 stable balanced eye-level medium shot showing {clean_prod_en}"
        
    elif is_cosmetics:
        target_part, _ = get_cosmetic_target(clean_prod_en, check_str)
        if scene_idx == 0: return f"Vertical 9:16 stable elegant medium shot holding {clean_prod_en} near the {target_part}"
        elif scene_idx == 1: return f"Vertical 9:16 stable smooth macro close-up focused precisely on the {target_part} demonstrating the texture of {clean_prod_en}"
        elif scene_idx == 2: return f"Vertical 9:16 stable tight close-up beauty shot showing direct application of {clean_prod_en} onto the {target_part}"
        else: return f"Vertical 9:16 stable radiant medium shot showing the final transformed {target_part} with {clean_prod_en}"

    elif is_mom_baby:
        if scene_idx == 0: return f"Vertical 9:16 stable soft warm medium shot holding {clean_prod_en}"
        elif scene_idx == 1: return f"Vertical 9:16 stable close-up shot showing the soft material/texture of {clean_prod_en}"
        elif scene_idx == 2: return f"Vertical 9:16 stable gentle close-up action shot testing or using {clean_prod_en}"
        else: return f"Vertical 9:16 stable balanced cozy medium shot with {clean_prod_en}"

    elif is_fashion:
        if scene_idx == 0: return "Vertical 9:16 eye-level three-quarter full-body shot showcasing the outfit worn on body"
        elif scene_idx == 1: return f"Vertical 9:16 stable close-up focused on the hands smoothing the fabric of {clean_prod_en} currently worn on body"
        elif scene_idx == 2: return f"Vertical 9:16 stable macro close-up focused on hands stretching the fabric of {clean_prod_en} currently worn on body"
        else: return "Vertical 9:16 warm eye-level medium-full shot modeling the outfit"
        
    elif is_long_handle:
        if scene_idx == 0: return f"Vertical 9:16 stable full-body wide shot, exact reference-matching {clean_prod_en} held at normal realistic scale"
        elif scene_idx == 1: return f"Vertical 9:16 stable medium-wide shot, keeping both human and {clean_prod_en} in frame to maintain normal true-to-life size (NO macro close-up)"
        elif scene_idx == 2: return f"Vertical 9:16 stable waist-down medium-wide shot showing the {clean_prod_en} working on the floor at normal realistic scale"
        else: return f"Vertical 9:16 stable full-body balanced shot, exact reference-matching {clean_prod_en} displayed at normal scale"
        
    elif is_strict_appliance:
        if scene_idx == 0: return f"Vertical 9:16 stable product-focused medium shot, exact reference-matching {clean_prod_en} held steadily, maintaining realistic scale"
        elif scene_idx == 1: return f"Vertical 9:16 stable close-up shot locked on {clean_prod_en}, maintaining 100% accurate true-to-life scale and identical proportions, tack-sharp focus"
        elif scene_idx == 2: return f"Vertical 9:16 stable tight close-up action shot centered directly on {clean_prod_en}, strictly maintaining accurate real-world scale during subtle interaction"
        else: return f"Vertical 9:16 stable balanced medium shot with exact reference-matching {clean_prod_en} displayed in realistic scale"
        
    else:
        if scene_idx == 0: return f"Vertical 9:16 stable product-focused medium shot, {clean_prod_en} held prominently, maintaining realistic human-to-product scale"
        elif scene_idx == 1: return f"Vertical 9:16 stable close-up shot (dolly-in) locked onto {clean_prod_en}, strictly maintaining true-to-life realistic scale, tack-sharp focus"
        elif scene_idx == 2: return f"Vertical 9:16 stable tight close-up action shot on {clean_prod_en} in real-time use, maintaining accurate real-world scale"
        else: return f"Vertical 9:16 stable balanced medium shot with {clean_prod_en} displayed with realistic scale"

def get_universal_physics_rules(product_name, vo_text, is_fashion, is_strict_appliance, is_long_handle, is_food, is_cosmetics, is_mom_baby, is_medicine, is_mom_baby_hard, intimate_type, is_aline_skirt):
    p = f"{product_name} {vo_text}".lower()
    if intimate_type != "normal": return "Soft breathable fabric physics: hands strictly stretching and releasing the elastic textile smoothly, showing its seamless texture. STRICTLY HAND INTERACTION ONLY. The product is NEVER worn on the body. Presenter is fully clothed."
    elif is_food: return "Mouth-watering visual physics; showing steam rising, juicy texture, melting, or smooth pulling/stretching if applicable. Presenter stands completely still; natural hand interaction only, NEVER dropping."
    elif is_cosmetics: 
        target_part, effect = get_cosmetic_target(product_name, vo_text)
        return f"Cosmetic physics: applying directly on the {target_part.upper()} ONLY (NEVER on other body parts). {effect}. Delicate hand interaction."
    elif is_mom_baby: 
        if is_mom_baby_hard: return "STRICT REFERENCE TRACKING for the baby product. 100% rigid non-deforming geometry, true-to-life scale. Safe and gentle interaction, holding securely, NEVER dropping. Hands kept strictly away from face."
        return "Ultra-soft fabric/material texture; showing gentle elasticity, high liquid absorption, or completely safe smooth surfaces. Holding securely. Hands kept strictly away from face."
    elif is_medicine: return "Clean, safe, solid capsule/pill geometry or smooth powder dissolving perfectly in clear water. Holding securely."
    elif is_fashion:
        if is_aline_skirt: return "Structured garment physics: the A-line skirt holds its firm, clean geometric shape without billowing, flaring, or pleating in motion. Subject models the garment WORN ON BODY. Fabric testing is done strictly WHILE WEARING IT. Hands kept strictly away from face."
        return "Natural fabric drape in motion; subject models the garment WORN ON BODY. Fabric testing (stretching/touching) is done strictly WHILE WEARING IT. Zero duplicate items in hands. Hands kept strictly away from face."
    elif any(k in p for k in ["hút bụi", "vacuum", "máy sấy", "máy thổi"]): return "CAMERA FOCUS LOCKED ON DEVICE HEAD/NOZZLE: 100% rigid non-deforming body lock, keeping its EXACT original nozzle/attachment (zero morphing to long sticks). The nozzle glides swiftly and firmly, visibly removing dirt or blowing air in real-time. Holding securely, never dropping. Hands kept strictly away from face."
    elif is_long_handle or any(k in p for k in ["chà sàn", "lau nhà", "bàn chải", "cọ", "tẩy", "rửa", "mop", "brush", "scrubber", "cleaner"]): return "Rigid tool body lock, true-to-life scale (NO giant sizes); product glides/scrubs rapidly and decisively across the floor/surface, visibly removing dirt/stains on the spot. Gripping firmly, never dropping. Hands kept strictly away from face."
    elif is_strict_appliance: return "STRICT REFERENCE TRACKING: The appliance maintains 100% exact shape, true-to-life scale, proportions, and surface details identical to the reference image. Zero morphing, zero hallucinated parts. The product stays completely rigid while presenter stands perfectly still; hands hold the product naturally (using its actual handle/strap if any), fast decisive interaction, NEVER dropping. CRITICAL: Product MUST remain at CHEST LEVEL or resting on a table. STRICTLY FORBIDDEN to lift product to face, cheek, or ear."
    else: return "CAMERA FOCUS LOCKED ON PRODUCT IN FOREGROUND: 100% rigid non-deforming 3D geometry, true-to-life scale (zero morphing); presenter stands completely still (zero body rotation); hands hold the product firmly at chest level (NEVER near the face) and trace surface decisively, never dropping. STRICTLY FORBIDDEN to lift product to face, cheek, or ear."

def get_action_templates_by_industry(clean_prod_en, check_str, is_fashion_wearable, is_strict_appliance, is_long_handle, is_food, is_cosmetics, is_mom_baby, is_medicine, intimate_type):
    p = f"{clean_prod_en} {check_str}".lower()
    if intimate_type != "normal": return (
        f"standing professionally in a modest oversized sweater, holding {clean_prod_en} securely in hands to show its premium texture",
        f"tight macro close-up focused strictly on hands pulling and stretching the highly elastic fabric of {clean_prod_en} to demonstrate extreme resilience",
        f"tight close-up of hands pressing into the breathable seamless surface of {clean_prod_en} resting flat on a wooden table",
        f"holding {clean_prod_en} neatly folded like a small towel in hands with a warm welcoming smile, fully dressed"
    )
    elif any(k in p for k in ["sock", "shoe", "boot", "sandal", "sneaker", "tights", "tất", "vớ", "giày", "dép"]): return ("stepping forward stylishly showcasing the footwear/socks on feet", "holding the product securely in hands, tracing fingers along the seams and material to show premium quality", "holding the product securely in hands, bending the sole or stretching the material firmly", "posing confidently with focus on the legs/feet")
    elif is_food: return (f"holding {clean_prod_en} securely while standing completely still and presenting it deliciously", f"taking a satisfying bite or showing the inside texture of {clean_prod_en}", f"pouring, dipping, or stretching {clean_prod_en} to show its mouth-watering details", f"holding {clean_prod_en} securely with a happy, satisfied expression")
    elif is_cosmetics:
        target_part, effect = get_cosmetic_target(clean_prod_en, check_str)
        return (f"elegantly holding {clean_prod_en} securely near the {target_part}", f"applying {clean_prod_en} DIRECTLY onto the {target_part} (strictly targeting the {target_part}), physically showing a clear visual transformation ({effect})", f"gently blending {clean_prod_en} directly into the {target_part}, the product texture visibly absorbs/changes to emphasize the stunning transformed finish", f"holding {clean_prod_en} securely with a radiant smile, showcasing the perfectly treated {target_part}")
    elif is_mom_baby: return (f"caring mother holding {clean_prod_en} securely next to her baby", f"gently touching or interacting with {clean_prod_en} to show its features", f"demonstrating the safe use of {clean_prod_en} with the baby", f"holding {clean_prod_en} securely with a caring smile next to the baby")
    elif is_medicine: return (f"holding {clean_prod_en} securely in hand", f"showing {clean_prod_en} up close next to a clear glass of water", f"dropping or demonstrating the use of {clean_prod_en}", f"holding {clean_prod_en} securely with a healthy, confident smile")
    elif is_fashion_wearable: return ("stepping forward confidently, modeling the outfit", "close-up on hands touching and smoothing the fabric of the outfit worn on body to show its premium texture", "close-up on hands gently stretching the fabric of the outfit worn on body to demonstrate elasticity and breathability", "posing elegantly (hands strictly kept away from face) and gesturing warmly while modeling the outfit")
    elif any(k in p for k in ["hút bụi", "vacuum"]): return (f"holding {clean_prod_en} with its EXACT original nozzle firmly, maintaining realistic scale", f"positioning the original nozzle of {clean_prod_en} on the surface to show its rigid structure", f"gliding {clean_prod_en} rapidly in focus using its original attachment, visibly sucking dirt straight into the dustbin", f"holding {clean_prod_en} securely with a warm open-palm gesture")
    elif is_long_handle: return (f"holding the exact reference-matching {clean_prod_en} firmly", f"demonstrating the exact reference-matching {clean_prod_en} swiftly on the floor without any added details or scale distortion", f"scrubbing/gliding the {clean_prod_en} rapidly and decisively across the floor keeping 100% fidelity and true realistic scale", f"holding {clean_prod_en} firmly with a confident gesture")
    elif is_strict_appliance: return (f"standing completely still while holding {clean_prod_en} firmly at realistic scale", f"presenting {clean_prod_en} swiftly", f"demonstrating {clean_prod_en} with fast, decisive hand interaction while keeping 100% fidelity. STRICTLY NO lifting to face/ear", f"holding {clean_prod_en} firmly with a confident open-palm gesture")
    else: return (f"standing perfectly still holding the rigid {clean_prod_en} firmly at CHEST LEVEL. STRICTLY NO lifting to face/ear", f"hands interacting directly with {clean_prod_en} strictly at chest or waist level, keeping it far away from the head", f"demonstrating {clean_prod_en} with fast decisive hand movements at chest level while preserving 100% rigid geometry. NEVER touch face", f"holding {clean_prod_en} securely at chest level with a confident gesture. Product remains strictly below shoulder level")

# ==============================================================================
# 8. LOGIC GỌI LÕI ĐỂ XỬ LÝ
# ==============================================================================
def create_scene_details(target_id, mode, style="Điện Ảnh Chân Thực"):
    all_combined = st.session_state.get("all_scripts", []) + st.session_state.get("cloned_scripts", []) + st.session_state.get("expanded_scripts", [])
    outline = next((sc for sc in all_combined if str(sc.get("id")) == str(target_id)), None)
    if not outline: raise Exception(f"Không tìm thấy kịch bản #{target_id} trong danh sách dự án.")
    
    char_profiles = outline.get("character_profiles", st.session_state.get("character_profiles", []))
    char_rules = generate_char_rules_string(char_profiles)
    current_active_mode = mode or st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    is_tiktok_shop = ("Viral" not in current_active_mode)
    is_viral = ("Viral" in current_active_mode)

    fixed_title = outline.get('title', 'Kịch bản chi tiết')
    full_vo_script = outline.get('vo', outline.get('full_voiceover_script', outline.get('hook', '')))
    fixed_setting_base = outline.get('set', outline.get('setting', 'Không gian thực tế phù hợp'))
    
    user_custom_note = outline.get("custom_note") or st.session_state.get("current_input_context", "").strip()
    presentation_format = outline.get("presentation_format") or st.session_state.get("last_presentation_format", "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng")
    is_pas_story = is_pas_storytelling_strategy(presentation_format, fixed_title)
    dna = st.session_state.get("content_analysis", {})
    
    p_orig, p_sale = dna.get("p_orig", 0), dna.get("p_sale", 0)
    
    self_pronoun = dna.get("pro_s", "em")
    audience_pronoun = dna.get("pro_a", "các chị em" if not is_viral else "mọi người")
    
    hero_color_str = dna.get("c_vi", "").strip()
    locked_color_en = translate_and_lock_color_en(hero_color_str, dna.get("c_en", "").strip())
    raw_prod_name = str(dna.get("name", "sản phẩm")).strip()
    ai_product_visual_en, dimensions_str = str(dna.get("vis_en", "")).strip(), str(dna.get("dim", "")).strip()

    check_str = f"{raw_prod_name} {fixed_title} {full_vo_script} {user_custom_note} {dna.get('usp', '')}"
    intimate_type = detect_intimate_apparel(check_str)
    is_footwear_accessory = detect_footwear_or_accessory(check_str)
    is_fashion_wearable = detect_wearable_fashion(check_str) and intimate_type == "normal" and not is_footwear_accessory
    
    is_single_skirt_mode = detect_single_tube_skirt(check_str)
    is_aline_skirt = any(k in check_str.lower() for k in ["chữ a", "a-line", "a line", "chân váy a"])
    
    is_strict_appliance = detect_strict_rigid_appliance(check_str) and not is_fashion_wearable
    is_long_handle = detect_long_handle_tool(check_str + " " + ai_product_visual_en)
    
    is_food = detect_food(check_str)
    is_cosmetics = detect_cosmetics(check_str)
    is_mom_baby = detect_mom_baby(check_str)
    is_mom_baby_hard = detect_mom_baby_hard_props(check_str)
    is_medicine = detect_medicine(check_str)
    
    koc_g = dna.get("koc_g", "female")
    koc_a = dna.get("koc_a", "adult")
    detected_gender, detected_demographic_en, voice_prompt = get_demographics_description(
        char_profiles, 
        f"Vietnamese {koc_a} {koc_g}", 
        "", 
        f"Native Hanoi Vietnamese {koc_a} {koc_g} voice",
        is_mom_baby
    )

    base_prod_en = f"{locked_color_en} seamless comfort fabric garment" if intimate_type == "underwear_bra" else (ai_product_visual_en if ai_product_visual_en else f"{raw_prod_name}")
    clean_prod_en = sanitize_third_party_ip(base_prod_en)
    if is_single_skirt_mode: clean_prod_en = enforce_single_tube_skirt_syntax(clean_prod_en)
    elif not is_fashion_wearable and not is_food and not is_cosmetics: clean_prod_en = re.sub(r'\b(?:foldable|collapsible|folding)\b', 'rigid structured', clean_prod_en, flags=re.IGNORECASE)

    dim_tag = f" ({dimensions_str})" if dimensions_str and len(dimensions_str) < 25 else ""
    color_lock_tag = f"[STRICT VISUAL LOCK: The product MUST strictly maintain {locked_color_en}, preserving exact original patterns/textures from reference, completely ignoring other colored variants]"
    
    if is_aline_skirt:
        color_lock_tag += " [GEOMETRY LOCK: STRICT STRUCTURED A-LINE SILHOUETTE, flat and smooth, zero pleats, zero flaring]"
    
    stylist_vibe_text = build_multi_industry_stylist_rules(clean_prod_en, hero_color_str, fixed_setting_base, detected_gender, intimate_type, is_fashion_wearable, check_str, is_food, is_cosmetics, is_mom_baby, is_medicine)
    footwear_match = re.search(r'Footwear:\s*([^|]+)', stylist_vibe_text)
    forced_footwear = footwear_match.group(1).strip() if footwear_match else "clean minimalist white sneakers"

    action_scene_1, action_scene_2, action_scene_3, action_scene_4 = get_action_templates_by_industry(clean_prod_en, check_str, is_fashion_wearable, is_strict_appliance, is_long_handle, is_food, is_cosmetics, is_mom_baby, is_medicine, intimate_type)
    
    is_pas_scn1_no_prod = (is_pas_story and not is_fashion_wearable)
    if is_pas_scn1_no_prod:
        scene_1_action_inst = "CRITICAL: Translate EXACT physical struggle/pain (e.g. scratching itchy skin, pinching nose) into explicit body language. EMPTY HANDS, ZERO PRODUCT IN FRAME."
    else:
        scene_1_action_inst = f"{action_scene_1} (under 18 words)"

    master_env_lighting_en, master_env_sfx_en = extract_environmental_lighting_and_weather(full_vo_script, fixed_setting_base)

    prompt_text = f"""
    TÊN SP: {raw_prod_name}
    MÔ TẢ EN: {clean_prod_en}. 
    Kịch bản: '{fixed_title}' | Bối cảnh gốc: '{fixed_setting_base}'
    KOC: {detected_demographic_en} | {stylist_vibe_text}
    
    THOẠI GỐC: "{full_vo_script}"
    
    NHIỆM VỤ ĐẠO DIỄN:
    1. Cắt thoại gốc thành 4 phần (vo).
    2. ĐỒNG BỘ BỐI CẢNH (CRITICAL): Bối cảnh chung (set_en) KHỚP với thoại. Nếu thoại rủ "đi cafe", bối cảnh là "coffee shop". CẤM set "bedroom".
    3. CẤM đưa sản phẩm lên mặt nếu không phải là mỹ phẩm mặt/đồ ăn.
    
    TRẢ VỀ DUY NHẤT ĐỊNH DẠNG JSON:
    {{
        "set_en": "Master setting EN (e.g., 'stylish coffee shop').",
        "wardrobe_vi": "Set đồ tiếng Việt chi tiết 4 cảnh",
        "wardrobe_en": "CRITICAL: EXACT outfit down to sleeve length and tucking.",
        "scenes": [
            {{ "set": "Bối cảnh VN...", "exp": "lively, engaging expression", "act": "{scene_1_action_inst} (under 25 words)", "sfx": "Foley", "dir": "Attention", "vo": "Trích phần đầu..." }},
            {{ "set": "Bối cảnh VN...", "exp": "confident", "act": "{action_scene_2} (under 20 words)", "sfx": "Foley", "dir": "Interest", "vo": "Trích đoạn tiếp theo..." }},
            {{ "set": "Bối cảnh VN...", "exp": "smiling", "act": "{action_scene_3} (under 20 words)", "sfx": "Foley", "dir": "Desire", "vo": "Trích đoạn tiếp theo..." }},
            {{ "set": "Bối cảnh VN...", "exp": "warm smile", "act": "{action_scene_4} (under 18 words)", "sfx": "Foley", "dir": "Action", "vo": "Trích đoạn chốt cuối..." }}
        ]
    }}
    """
    sys_inst = get_sys_inst_details(current_active_mode, "Điện Ảnh Chân Thực", "On-camera", char_rules, "Max 10s", 1, char_profiles, user_custom_note, presentation_format, self_pronoun, audience_pronoun, fixed_setting_base, True, is_pas_story, forced_footwear, target_id)
    
    scenes, w_lock_en, w_lock_vi, master_setting_en = [], "", "", "clean minimalist modern setting"
    max_retries = 2
    for attempt in range(max_retries):
        try:
            res = call_gemini([prompt_text], sys_inst, max_tokens=4096)
            scenes = extract_scenes(res)
            if scenes and isinstance(scenes, list) and len(scenes) > 0:
                master_setting_en = sanitize_third_party_ip(res.get("set_en", "clean minimalist modern setting")).strip().rstrip('.')
                w_lock_en = res.get("wardrobe_en", "")
                w_lock_vi = res.get("wardrobe_vi", "")
                break
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Lỗi khi gọi AI: {str(e)}")
            time.sleep(1.5)

    if not scenes: raise Exception("AI không tạo được danh sách phân cảnh. Vui lòng bấm tạo lại.")
    
    base_char_prompt = sanitize_third_party_ip(w_lock_en or f"{detected_demographic_en}, wearing high-fashion outfit").strip().rstrip('.')
    if is_single_skirt_mode: base_char_prompt = enforce_single_tube_skirt_syntax(base_char_prompt)
    if not is_fashion_wearable: base_char_prompt += ", standing completely still with zero body rotation"
    
    locked_character_prompt = f"[IDENTICAL CHARACTER LOCK: EXACT SAME face, body shape, hairstyle, hair color, and precise wardrobe outfit across all scenes. Presenter speaking directly to the lens] {base_char_prompt}"
    final_outfit_vi = w_lock_vi or "Trang phục Stylist đồng bộ 4 cảnh"

    anti_drop_neg = "dropping product, falling object, letting go of object, slipping, throwing, "
    anti_morph_neg = "extra handles, hallucinated handles, mismatched handle, changing straps, changing shape, deforming geometry, "
    skirt_neg_extra = "split-leg pants, bifurcated trousers, two separate pant legs, divided culottes, " if is_single_skirt_mode else ""
    
    if is_aline_skirt: 
        skirt_neg_extra += "flared skirt, pleated skirt, ruffled skirt, billowing fabric, bell-shaped skirt, circular skirt, flowy wide skirt, gathering, "
        
    appliance_neg_extra = "changing nozzle, adding extension stick, swapping brush head, mutating attachment, hallucinated parts, extra spouts, modified shape, changing proportions, warped structure, " if (is_strict_appliance and not is_food and not is_cosmetics) else ""
    color_neg_extra = "multiple product colors, mixed colors, wrong product color, different colored variants, solid flat color overriding pattern, missing original pattern, "
    
    dynamic_footwear_neg = ""
    vibe_lower = stylist_vibe_text.lower()
    if any(k in vibe_lower for k in ["barefoot", "slipper"]): dynamic_footwear_neg = "sneakers, sports shoes, running shoes, leather shoes, dress shoes, high heels, boots, outside shoes, "
    elif any(k in vibe_lower for k in ["sneaker", "running", "athletic"]): dynamic_footwear_neg = "barefoot, slippers, high heels, leather dress shoes, oxfords, sandals, "
    elif any(k in vibe_lower for k in ["heel", "loafer", "dress"]): dynamic_footwear_neg = "barefoot, slippers, running shoes, chunky sneakers, athletic shoes, "
    
    char_neg_extra = f"{dynamic_footwear_neg}changing top length, changing sleeve length, changing background, changing room, different room, changing clothes, changing shoes, changing hairstyle, changing hair color, changing shirt, changing pants, changing shirt styling, tucking in shirt, untucking shirt, different face, different hair, changing outfit, inconsistent wardrobe, adding clothing layers, removing clothing layers, morphing clothes, multiple characters, "
    
    face_touch_neg = "" if (is_cosmetics or is_food) else "holding like a phone, holding to ear, pressing against cheek, touching face, hand on face, hands near face, touching hair, covering face, product near face, bringing object to face, eating, smelling, "
    
    base_neg_prompt = f"{anti_morph_neg}{anti_drop_neg}{skirt_neg_extra}{appliance_neg_extra}{color_neg_extra}{char_neg_extra}{face_touch_neg}dark, moody, underexposed, poorly lit, heavy shadows, oversized product, giant product, massive brush, huge handle, product larger than human, out of scale, disproportionate scale, incorrect proportions, product out of focus, blurry product, tiny product in background, camera zooming on face instead of product, deforming geometry, melting plastic, folding/collapsing glitch, inconsistent product color, grey parts on white product, duplicate garment in hands, extra fingers, deformed hands, floating objects, nsfw, nudity, cleavage, text, watermark, subtitles, UI elements, background music, bgm, singing, fire, sparks, flames, smoke, plasma, glowing magic aura, visible wind lines, macro close up"
    if not is_fashion_wearable:
        base_neg_prompt += ", character turning, body swaying, walking, spinning, camera moving, camera panning"
    
    total_sec = 0.0
    for idx_scn, scn in enumerate(scenes):
        vo_text = clean_and_normalize_voiceover(scn.get("vo", scn.get("voiceover", "")))
        scn["voiceover"] = vo_text
        scn["director"] = sanitize_policy_text(scn.get("dir", scn.get("director", "")))
        
        raw_speech = calculate_speech_duration(vo_text, is_tiktok_shop)
        act_cushion = 1.0 if is_tiktok_shop else 1.3
        dynamic_sec = min(10, max(4, math.ceil(raw_speech + act_cushion)))
        actual_speech = round(dynamic_sec - 0.8, 1) if raw_speech >= dynamic_sec else raw_speech
        cushion_sec = round(max(0.5, dynamic_sec - actual_speech), 1)
        
        scn["dur"], scn["actual_speech_sec"] = f"{dynamic_sec}s", actual_speech
        total_sec += float(dynamic_sec)
        
        is_pas_scn1_no_prod = (idx_scn == 0 and is_pas_story and not is_fashion_wearable)
        
        cam_shot = get_product_centric_camera_shot(idx_scn, is_fashion_wearable, is_footwear_accessory, is_pas_scn1_no_prod, clean_prod_en, is_strict_appliance, is_long_handle, is_food, is_cosmetics, is_mom_baby, is_medicine, intimate_type, check_str)
        
        base_sfx = re.sub(r'\b(?:music|soundtrack|melody|song|bgm)\b', 'Foley', scn.get("sfx", "Natural Foley"), flags=re.IGNORECASE)
        scn["sfx"] = f"{base_sfx}, {master_env_sfx_en}" if master_env_sfx_en else base_sfx
        
        micro_expr = sanitize_third_party_ip(scn.get("exp", scn.get("expression_en", "natural engaging expression"))).strip().rstrip('.')
        clean_act = sanitize_destructive_motion_verbs(sanitize_third_party_ip(re.sub(r'^(?:Character\s+(?:is\s+)?|Subject\s+(?:is\s+)?)', '', scn.get("act", scn.get("action_en", action_scene_2)), flags=re.IGNORECASE).strip()).rstrip('.'), is_fashion=is_fashion_wearable, is_food=is_food)
        if is_single_skirt_mode: clean_act = enforce_single_tube_skirt_syntax(clean_act)
        
        if not is_fashion_wearable and not is_pas_scn1_no_prod:
            if not clean_act.lower().startswith("standing"):
                clean_act = f"standing completely still with zero body rotation, speaking directly to camera, {clean_act}"
        else:
            if not clean_act.lower().startswith("standing") and not clean_act.lower().startswith("stepping"):
                clean_act = f"speaking directly to camera, {clean_act}"

        scene_physics = get_universal_physics_rules(clean_prod_en, vo_text, is_fashion=is_fashion_wearable, is_strict_appliance=is_strict_appliance, is_long_handle=is_long_handle, is_food=is_food, is_cosmetics=is_cosmetics, is_mom_baby=is_mom_baby, is_medicine=is_medicine, is_mom_baby_hard=is_mom_baby_hard, intimate_type=intimate_type, is_aline_skirt=is_aline_skirt)

        color_lock_tag = f"[STRICT VISUAL LOCK: The product MUST strictly maintain {locked_color_en}, preserving exact original patterns/textures from reference, completely ignoring other colored variants]"
        
        if is_strict_appliance or is_mom_baby_hard: 
            locked_product_prompt_segment = f"STRICT REFERENCE APPLIANCE: {clean_prod_en}. {color_lock_tag}. Maintaining 100% identical shape, exact original nozzle/attachment, and surface details. Zero hallucinated parts."
        elif is_food or is_cosmetics or is_mom_baby or is_medicine: 
            locked_product_prompt_segment = f"PRODUCT FOCUS: {clean_prod_en}. {color_lock_tag} as the main subject."
        elif is_footwear_accessory and (idx_scn in [1, 2]):
            locked_product_prompt_segment = f"PRODUCT TESTING FOCUS: {clean_prod_en}. {color_lock_tag}. The product is held securely in hands for close-up physical demonstration (NOT worn on body)."
        elif is_fashion_wearable:
            if (idx_scn in [1, 2]):
                locked_product_prompt_segment = f"FASHION FABRIC TEST: wearing {clean_prod_en}. {color_lock_tag} directly on body. Hands are touching/stretching the fabric WHILE WEARING IT."
            else:
                locked_product_prompt_segment = f"FASHION SHOWCASE: wearing {clean_prod_en}. {color_lock_tag} directly on body."
        else:
            locked_product_prompt_segment = f"HERO PRODUCT CENTERPIECE: {clean_prod_en}{dim_tag} occupying foreground center focus. {color_lock_tag} (100% rigid non-deforming geometry)."

        if is_pas_scn1_no_prod:
            img_core = f"[IDENTICAL SETTING]: {cam_shot}, {master_setting_en}, {master_env_lighting_en}. Subject: {locked_character_prompt}, {micro_expr}, {clean_act} (EMPTY HANDS, ZERO PRODUCT, NO PRODUCT IN FRAME). [NOTE: DO NOT USE PRODUCT REFERENCE FOR THIS SCENE]"
        elif not is_fashion_wearable and idx_scn in [1, 2]:
            img_core = f"[IDENTICAL SETTING]: {cam_shot}, {master_setting_en}, {master_env_lighting_en}. [{locked_product_prompt_segment}]. Presenter in background: {locked_character_prompt}, {micro_expr}, {clean_act}"
        else:
            img_core = f"[IDENTICAL SETTING]: {cam_shot}, {master_setting_en}, {master_env_lighting_en}. [{locked_product_prompt_segment}]. Subject: {locked_character_prompt}, {micro_expr}, {clean_act}"

        scn["img_p"] = sanitize_third_party_ip(f"{img_core}, tack-sharp focus on product, photorealistic 8k --ar 9:16 --style raw --v 6.1")
        scn["img_neg"] = base_neg_prompt
        clean_vo_audio = clean_and_normalize_voiceover(re.sub(r'\.{2,}', '.', vo_text).strip())

        studio_audio_prompt = f"[AUDIO]: Studio-quality close-mic direct ON-CAMERA speech (Presenter's lips moving perfectly, KOC visibly talking directly to the camera, ZERO off-screen narrator, zero room reverb). {voice_prompt}: \"{clean_vo_audio}\". Foley only [{scn['sfx']}], zero BGM, no text overlays."

        if is_pas_scn1_no_prod:
            raw_vid = f"[CAMERA & SETTING]: {cam_shot}, gimbal live-action, {master_setting_en}, {master_env_lighting_en}. [SUBJECT]: {locked_character_prompt}, {micro_expr}, {clean_act}. [TIMING ({dynamic_sec}s)]: 0.0s-{actual_speech}s precise accurate Vietnamese lip-sync; final {cushion_sec}s natural breathing nod. {studio_audio_prompt}"
        elif not is_fashion_wearable or ((is_fashion_wearable or is_footwear_accessory) and (idx_scn in [1, 2])):
            raw_vid = f"[PRODUCT-CENTRIC CAMERA & SETTING]: {cam_shot}, stable camera, {master_setting_en}, {master_env_lighting_en}. [{locked_product_prompt_segment}]. [PRODUCT ACTION & PHYSICS]: {clean_act}. {scene_physics} [PRESENTER]: {locked_character_prompt}, {micro_expr}. [TIMING ({dynamic_sec}s)]: 0.0s-{actual_speech}s precise accurate Vietnamese lip-sync while demonstrating the product in foreground; final {cushion_sec}s warm smile & nod. {studio_audio_prompt}"
        else:
            raw_vid = f"[CAMERA & SETTING]: {cam_shot}, gimbal live-action, {master_setting_en}, {master_env_lighting_en}. [SUBJECT]: {locked_character_prompt}, {micro_expr}. [{locked_product_prompt_segment}]. [ACTION & PHYSICS]: {clean_act}. {scene_physics} [TIMING ({dynamic_sec}s)]: 0.0s-{actual_speech}s precise accurate Vietnamese lip-sync; final {cushion_sec}s warm smile & nod. {studio_audio_prompt}"

        vid_parts = raw_vid.split('[AUDIO]:')
        if len(vid_parts) == 2: scn["vid_p"] = sanitize_veo3_prompt(vid_parts[0]) + "[AUDIO]:" + vid_parts[1]
        else: scn["vid_p"] = sanitize_veo3_prompt(raw_vid)
        scn["vid_neg"] = base_neg_prompt
        scn["is_no_product_scene"] = is_pas_scn1_no_prod
        
    res["scenes"] = scenes
    res["total_dur"] = f"Khoảng {int(total_sec)} giây"
    res["full_voiceover_script"] = clean_and_normalize_voiceover(full_vo_script)
    
    summary_lines = [
        f"⏱ <b>Thời lượng:</b> Khoảng {int(total_sec)}s | 🎬 <b>Chiến lược:</b> {presentation_format}",
        f"🗣 <b>Xưng hô:</b> '{self_pronoun}' - '{audience_pronoun}' | 🏙 <b>Bối cảnh:</b> {fixed_setting_base}",
        f"👗 <b>Trang phục KOC:</b> {final_outfit_vi}"
    ]
    if user_custom_note and user_custom_note.lower() not in ["mặc định chuẩn", "không có"]:
        summary_lines.append(f"🎯 <b>Ghi chú:</b> {user_custom_note}")
        
    res["director_summary"] = "<br>".join(summary_lines)
    
    temp_dict = st.session_state.get("generated_details", {})
    temp_dict[str(target_id)] = res
    st.session_state.generated_details = temp_dict
    
    auto_save_current_session()

def clone_script(script_id):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    all_combined = st.session_state.get("all_scripts", []) + st.session_state.get("cloned_scripts", []) + st.session_state.get("expanded_scripts", [])
    target = next((sc for sc in all_combined if str(sc.get("id")) == str(script_id)), None)
    if not target: return []
    cur_len = len(all_combined)
    target_detail = st.session_state.get("generated_details", {}).get(str(script_id), {})
    user_custom_note = target.get("custom_note") or st.session_state.get("current_input_context", "").strip()
    presentation_format = target.get("presentation_format") or st.session_state.get("last_presentation_format", "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng")
    
    original_voices = [f"- Cảnh {s.get('scene')}: \"{s.get('voiceover')}\"" for s in target_detail.get("scenes", [])] if "scenes" in target_detail else []
    full_voice_text = "\n".join(original_voices) if original_voices else f"- Hook: \"{target.get('hook', '')}\""

    dna = st.session_state.get("content_analysis") or {}
    
    prompt = f"""
    SP: {dna.get('name', '')} | GỐC #{script_id}: '{target.get('title', '')}'
    THOẠI GỐC:\n{full_voice_text}
    NHIỆM VỤ: Nhân bản 3 biến thể giữ 90% cấu trúc, đổi bối cảnh đời thực khác nhau. Xưng '{dna.get("pro_s", "em")}' - Gọi '{dna.get("pro_a", "các chị em" if not ("Viral" in mode) else "mọi người")}'.
    TRẢ VỀ JSON DUY NHẤT (KHÔNG BỌC TRONG MARKDOWN):
    {{
        "scripts": [
            {{ "id": {cur_len+1}, "title": "Bản Năng Động", "set": "Bối cảnh khớp 100% với thoại", "vo": "Đoạn thoại dài 80-110 từ, liền mạch, TỰ NHIÊN..." }},
            {{ "id": {cur_len+2}, "title": "Bản Tâm Sự", "set": "Bối cảnh khớp 100% với thoại", "vo": "Đoạn thoại dài 80-110 từ, liền mạch, TỰ NHIÊN..." }},
            {{ "id": {cur_len+3}, "title": "Bản Chuyên Gia", "set": "Bối cảnh khớp 100% với thoại", "vo": "Đoạn thoại dài 80-110 từ, liền mạch, TỰ NHIÊN..." }}
        ]
    }}
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, "Điện Ảnh Chân Thực", "On-camera", "", 1, "Nhân bản", user_custom_note, presentation_format), max_tokens=2500)
    clones = extract_scenes(res)
    formatted_clones = []
    for idx, cl in enumerate(clones):
        formatted_clones.append({
            "id": cur_len + idx + 1, "title": cl.get("title", f"Biến thể #{cur_len + idx + 1}"),
            "setting": cl.get("set", cl.get("setting", f"Bối cảnh #{idx+1}")), 
            "full_voiceover_script": clean_and_normalize_voiceover(cl.get("vo", cl.get("full_voiceover_script", cl.get("hook", "")))),
            "actors": 1, "character_profiles": target.get("character_profiles", st.session_state.get("character_profiles", [])),
            "duration_instruction": "Max 10s", "narrator_mode": "On-camera",
            "custom_note": user_custom_note, "presentation_format": presentation_format
        })
    return formatted_clones

def generate_more_scripts(unified_strategy_format, char_profiles, extra_note=""):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    cur_len = len(st.session_state.get("all_scripts", []) + st.session_state.get("cloned_scripts", []) + st.session_state.get("expanded_scripts", []))
    active_note = extra_note.strip() if extra_note.strip() else st.session_state.get("current_input_context", "").strip()
    active_format = unified_strategy_format if unified_strategy_format else st.session_state.get("last_presentation_format", "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng")
    dna = st.session_state.get("content_analysis") or {}
    
    prompt = f"""
    SP: {dna.get('name', '')} | CHIẾN LƯỢC: '{active_format}' | Xưng '{dna.get("pro_s", "em")}' - Gọi '{dna.get("pro_a", "các chị em" if not ("Viral" in mode) else "mọi người")}'.
    TẠO 3 KỊCH BẢN Ở 3 BỐI CẢNH ĐỜI THỰC KHÁC NHAU. ĐẶC BIỆT LƯU Ý:
    - Kịch bản 1: Giọng điệu năng động, dồn dập.
    - Kịch bản 2: Giọng tâm sự, chia sẻ, gần gũi.
    - Kịch bản 3: Giọng chuyên gia, nhấn mạnh công năng.
    TRẢ VỀ JSON DUY NHẤT (KHÔNG BỌC TRONG MARKDOWN):
    {{
        "scripts": [
            {{ "id": {cur_len+1}, "title": "Bản Năng Động", "set": "Bối cảnh khớp 100% với thoại", "vo": "Đoạn thoại dài 80-110 từ, liền mạch, TỰ NHIÊN..." }},
            {{ "id": {cur_len+2}, "title": "Bản Tâm Sự", "set": "Bối cảnh khớp 100% với thoại", "vo": "Đoạn thoại dài 80-110 từ, liền mạch, TỰ NHIÊN..." }},
            {{ "id": {cur_len+3}, "title": "Bản Chuyên Gia", "set": "Bối cảnh khớp 100% với thoại", "vo": "Đoạn thoại dài 80-110 từ, liền mạch, TỰ NHIÊN..." }}
        ]
    }}
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, "Điện Ảnh Chân Thực", "On-camera", generate_char_rules_string(char_profiles), 1, active_format, active_note, active_format), max_tokens=2500)
    more_scripts = extract_scenes(res)
    for idx, sc in enumerate(more_scripts):
        sc.update({
            "id": cur_len + idx + 1, "duration_instruction": "Max 10s", 
            "full_voiceover_script": clean_and_normalize_voiceover(sc.get("vo", sc.get("full_voiceover_script", sc.get("hook", "")))),
            "setting": sc.get("set", sc.get("setting", "")),
            "narrator_mode": "On-camera", "character_profiles": char_profiles, "actors": 1,
            "custom_note": active_note, "presentation_format": active_format
        })
    return more_scripts

# ==============================================================================
# 9. GIAO DIỆN THANH BÊN (SIDEBAR) & QUẢN TRỊ ADMIN
# ==============================================================================
with st.sidebar:
    if not st.session_state.get("is_logged_in", False):
        tabs = st.tabs(["🔐 Đăng Nhập", "🚀 Đăng Ký"])
        with tabs[0]:
            with st.form("login_form", border=False):
                email_input = st.text_input("Email:", key="f_login_email")
                pass_input = st.text_input("Mật khẩu:", type="password", key="f_login_pass")
                submit_login = st.form_submit_button("🔑 Đăng Nhập", type="primary", use_container_width=True)
                if submit_login:
                    email_c, pass_c = email_input.strip(), pass_input.strip()
                    if email_c in st.session_state.get("licensed_accounts", {}) and st.session_state.get("licensed_accounts", {})[email_c].get("password") == pass_c:
                        st.session_state.licensed_accounts[email_c]["active_session_id"] = st.session_state.get("session_id", "")
                        save_single_account(email_c, st.session_state.licensed_accounts[email_c])
                        st.session_state.is_logged_in = True
                        st.session_state.current_email = email_c
                        st.rerun()
                    else: st.error("❌ Email hoặc mật khẩu không đúng!")
            with st.expander("❓ Quên mật khẩu?"):
                st.info("💡 Liên hệ Zalo Admin: **0869 628 316** để được hỗ trợ.")
        with tabs[1]:
            with st.form("register_form", border=False):
                r_email = st.text_input("Email đăng ký:", key="f_reg_email")
                r_phone = st.text_input("Số điện thoại:", key="f_reg_phone")
                r_pass = st.text_input("Mật khẩu mới:", type="password", key="f_reg_pass")
                r_purpose = st.selectbox("🎯 Mục đích:", ["🛒 TikTok Shop", "🌟 Viral & Xây Kênh", "⚡ Cả hai"], key="f_reg_purpose")
                submit_reg = st.form_submit_button("🚀 Đăng Ký", type="secondary", use_container_width=True)
                if submit_reg:
                    email_r, phone_r, pass_r = r_email.strip(), r_phone.strip(), r_pass.strip()
                    if email_r and phone_r and pass_r and is_valid_phone(phone_r) and email_r not in st.session_state.get("licensed_accounts", {}):
                        exp = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[email_r] = {
                            "roles": ALL_MODULES, "phone": phone_r, "password": pass_r, "expires_at": exp,
                            "plan_type": "Trial", "daily_usage_count": 0, "last_generation_date": "", "active_session_id": ""
                        }
                        save_single_account(email_r, st.session_state.licensed_accounts[email_r])
                        st.session_state.is_logged_in = True
                        st.session_state.current_email = email_r
                        st.rerun()
                    else: st.error("⚠️ Thông tin không hợp lệ hoặc tài khoản đã tồn tại!")
    else:
        if is_system_busy:
            if st.button("🛑 HỦY KẸT & MỞ KHÓA NGAY", type="secondary", use_container_width=True, key="sidebar_unhang_btn"):
                st.session_state.current_processing_id = None
                st.session_state.current_cloning_id = None
                st.session_state.trigger_main_generation = False
                st.session_state.trigger_more_generation = False
                st.rerun()

        st.markdown("### 🗂 DỰ ÁN")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True, disabled=is_system_busy):
            st.session_state.reset_key += 1
            st.session_state.update({
                "all_scripts": [], "cloned_scripts": [], "expanded_scripts": [],
                "generated_details": {}, "content_analysis": None, "active_script_id": None,
                "current_input_context": "", "current_product_data_saved": None, "current_product_data": None,
                "current_project_id": None, "saved_reference_images": [], "character_profiles": [],
                "current_processing_id": None, "current_cloning_id": None, "is_analyzed": False,
                "last_autosave_time": ""
            })
            st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
            st.rerun()
            
        st.session_state.active_project_title = st.text_input("Tên dự án hiện tại:", value=st.session_state.get("active_project_title", ""), disabled=is_system_busy)
        if st.session_state.get("last_autosave_time"):
            st.markdown(f"<div class='autosave-badge'>☁️ Đã tự động lưu lúc {st.session_state.get('last_autosave_time')}</div>", unsafe_allow_html=True)

        c_save1, c_save2 = st.columns(2)
        if c_save1.button("💾 Lưu Dự Án", use_container_width=True, disabled=is_system_busy):
            success, msg = auto_save_current_session()
            if success: st.toast(f"✅ {msg}"); st.rerun()
            else: st.error(f"❌ {msg}")
            
        if c_save2.button("📑 Lưu Bản Mới", use_container_width=True, disabled=is_system_busy):
            dedup_details = {str(k): v for k, v in st.session_state.get("generated_details", {}).items()}
            payload = {
                "content_analysis": st.session_state.get("content_analysis"),
                "all_scripts": st.session_state.get("all_scripts", []),
                "cloned_scripts": st.session_state.get("cloned_scripts", []),
                "expanded_scripts": st.session_state.get("expanded_scripts", []),
                "generated_details": dedup_details,
                "character_profiles": st.session_state.get("character_profiles", []),
                "current_input_context": st.session_state.get("current_input_context", ""),
                "is_analyzed": st.session_state.get("is_analyzed", False)
            }
            new_title = f"{st.session_state.get('active_project_title', '')} (Bản sao)"
            success, msg = save_project_to_db(st.session_state.get("current_email", ""), new_title, payload, project_id=None)
            if success: 
                st.session_state.active_project_title = new_title
                st.toast("✅ Đã lưu thành dự án mới độc lập!"); st.rerun()
            else: st.error(f"❌ {msg}")
        
        st.markdown("---")
        st.markdown("### 📂 KHO DỰ ÁN")
        is_admin_user = (st.session_state.get("current_email", "") == ADMIN_EMAIL)
        
        if supabase:
            try:
                if is_admin_user:
                    res = supabase.table("saved_projects").select("id, project_title, user_email, created_at").order("created_at", desc=True).limit(500).execute()
                else:
                    res = supabase.table("saved_projects").select("id, project_title, user_email, created_at").eq("user_email", st.session_state.get("current_email", "")).order("created_at", desc=True).limit(300).execute()
                all_projects = res.data or []
            except: all_projects = []

            if is_admin_user and all_projects:
                creator_emails = sorted(list(set(p.get("user_email", "") for p in all_projects if p.get("user_email"))))
                sel_creator = st.selectbox("👤 Lọc theo thành viên:", ["Tất cả thành viên"] + creator_emails, key="admin_sel_creator", disabled=is_system_busy)
                if sel_creator != "Tất cả thành viên": all_projects = [p for p in all_projects if p.get("user_email") == sel_creator]

            search_proj = st.text_input("🔍 Tìm kiếm dự án:", placeholder="Nhập tên dự án...", key="search_proj_input", disabled=is_system_busy)
            display_projects = [p for p in all_projects if search_proj.strip().lower() in p['project_title'].lower()] if search_proj.strip() else (all_projects if st.session_state.get("show_all_projects", False) else all_projects[:3])

            if not display_projects: st.info("Chưa có dự án nào.")
            else:
                for p in display_projects:
                    proj_creator = p.get("user_email", "N/A")
                    is_current_open = (str(st.session_state.get("current_project_id")) == str(p['id']))
                    exp_label = f"🟢 {p['project_title']}" if is_current_open else f"🎬 {p['project_title']}"
                    with st.expander(exp_label):
                        if is_admin_user:
                            st.markdown(f"<span style='font-size:12px; color:#1e40af; background:#dbeafe; padding:2px 8px; border-radius:4px; font-weight:600;'>👤 Tạo bởi: {proj_creator}</span>", unsafe_allow_html=True)
                            st.caption(f"📅 Ngày tạo: {p.get('created_at', '')[:10]}")
                        
                        new_p_name = st.text_input("Đổi tên dự án:", value=p['project_title'], key=f"ren_txt_{p['id']}", disabled=is_system_busy)
                        if st.button("✏️ Cập Nhật Tên", key=f"ren_btn_{p['id']}", use_container_width=True, disabled=is_system_busy):
                            if new_p_name.strip() and new_p_name.strip() != p['project_title']:
                                supabase.table("saved_projects").update({"project_title": new_p_name.strip()}).eq("id", p['id']).execute()
                                if is_current_open: st.session_state.active_project_title = new_p_name.strip()
                                st.toast("✅ Đã đổi tên dự án thành công!"); st.rerun()
                        
                        col_o, col_d = st.columns(2)
                        if col_o.button("📂 Mở", key=f"o_{p['id']}", use_container_width=True, disabled=is_system_busy):
                            full_row = supabase.table("saved_projects").select("script_content").eq("id", p['id']).single().execute()
                            sd = (full_row.data or {}).get("script_content", {})
                            loaded_details = {str(k): v for k, v in sd.get("generated_details", {}).items()}
                            st.session_state.update({
                                "content_analysis": sd.get("content_analysis"), "all_scripts": sd.get("all_scripts", []),
                                "cloned_scripts": sd.get("cloned_scripts", []), "expanded_scripts": sd.get("expanded_scripts", []),
                                "generated_details": loaded_details, "character_profiles": sd.get("character_profiles", []),
                                "current_input_context": sd.get("current_input_context", ""), "current_project_id": p['id'], 
                                "active_project_title": p['project_title'], "is_analyzed": sd.get("is_analyzed", True)
                            })
                            st.rerun()
                        if col_d.button("🗑 Xóa", key=f"d_{p['id']}", type="secondary", use_container_width=True, disabled=is_system_busy):
                            supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                            if is_current_open: st.session_state.current_project_id = None
                            st.toast("✅ Đã xóa dự án!"); st.rerun()

                if not search_proj.strip() and len(all_projects) > 3:
                    if st.session_state.get("show_all_projects", False):
                        if st.button("🔼 Thu gọn kho dự án", use_container_width=True, disabled=is_system_busy):
                            st.session_state.show_all_projects = False; st.rerun()
                    else:
                        if st.button(f"🔽 Xem thêm {len(all_projects)-3} dự án", use_container_width=True, disabled=is_system_busy):
                            st.session_state.show_all_projects = True; st.rerun()

        if is_admin_user:
            st.markdown("---")
            st.markdown("### ⚙ QUẢN TRỊ ADMIN")
            with st.expander("➕ Cấp Quyền Mới", expanded=False):
                adm_acc = st.text_input("Email:", key="adm_in_acc")
                adm_phone = st.text_input("SĐT:", key="adm_in_phone")
                adm_pass = st.text_input("Mật khẩu:", value="123456", key="adm_in_pass")
                adm_roles_choice = st.multiselect("🎯 Thể loại:", ALL_MODULES, default=ALL_MODULES, key="adm_in_roles")
                adm_plan = st.radio("Gói cước:", ["Trial", "Basic", "Advanced", "VIP"], horizontal=True, key="adm_in_plan")
                adm_dur = st.selectbox("Thời hạn:", ["3 Ngày", "7 Ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "Vĩnh viễn", "Tùy chỉnh (Chọn ngày)"], key="adm_in_dur")
                
                calculated_exp_str = "2099-12-31"
                if adm_dur == "Tùy chỉnh (Chọn ngày)":
                    calculated_exp_str = st.date_input("Chọn ngày hết hạn:", value=date.today() + timedelta(days=30), min_value=date.today(), key="adm_custom_date").strftime("%Y-%m-%d")
                    st.caption(f"📅 Hạn mới: **{calculated_exp_str}**")
                elif adm_dur != "Vĩnh viễn":
                    dur_days_map = {"3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730}
                    calculated_exp_str = (datetime.now() + timedelta(days=dur_days_map.get(adm_dur, 30))).strftime("%Y-%m-%d")

                if st.button("💾 Cấp Quyền Tài Khoản", type="primary", use_container_width=True, key="btn_submit_grant_admin", disabled=is_system_busy):
                    if adm_acc.strip() and adm_phone.strip() and adm_pass.strip() and adm_roles_choice:
                        st.session_state.licensed_accounts[adm_acc.strip()] = {
                            "roles": ALL_MODULES, "phone": adm_phone.strip(), "password": adm_pass.strip(),
                            "expires_at": calculated_exp_str, "plan_type": adm_plan, "daily_usage_count": 0, "last_generation_date": "", "active_session_id": ""
                        }
                        save_single_account(adm_acc.strip(), st.session_state.licensed_accounts[adm_acc.strip()])
                        st.toast(f"✅ Đã cấp quyền đến {calculated_exp_str}!"); st.rerun()
                    else: st.error("⚠️ Vui lòng nhập đầy đủ thông tin!")

            st.markdown("##### 👥 Danh Sách Tài Khoản & Mật Khẩu")
            search_acc = st.text_input("🔍 Tìm tài khoản:", placeholder="Nhập Email hoặc SĐT...", key="search_acc_input", disabled=is_system_busy)
            other_accs = [item for item in st.session_state.get("licensed_accounts", {}).items() if item[0] != ADMIN_EMAIL]
            filt_accs = [item for item in other_accs if search_acc.strip().lower() in item[0].lower() or search_acc.strip() in item[1].get('phone', '')] if search_acc.strip() else (other_accs if st.session_state.get("show_all_admin_accounts", False) else other_accs[:3])

            for acc_mail, info in filt_accs:
                with st.expander(f"👤 {acc_mail} ({info.get('plan_type')})"):
                    st.write(f"📞 SĐT: `{info.get('phone', 'N/A')}` | ⏳ Hạn: `{info.get('expires_at')}`")
                    new_user_pass = st.text_input("🔑 Đổi mật khẩu:", value=info.get("password", ""), key=f"pass_edit_{acc_mail}", disabled=is_system_busy)
                    if st.button("⚡ Đặt 123456", key=f"btn_quick_reset_{acc_mail}", use_container_width=True, disabled=is_system_busy):
                        st.session_state.licensed_accounts[acc_mail]["password"] = "123456"
                        save_single_account(acc_mail, st.session_state.licensed_accounts[acc_mail])
                        st.toast(f"✅ Đã reset mật khẩu của {acc_mail} về '123456'!"); st.rerun()

                    new_roles = st.multiselect("Đổi thể loại:", ALL_MODULES, default=info.get("roles", ALL_MODULES), key=f"roles_sel_{acc_mail}", disabled=is_system_busy)
                    new_plan = st.selectbox("Đổi gói:", ["Trial", "Basic", "Advanced", "VIP"], index=["Trial", "Basic", "Advanced", "VIP"].index(info.get("plan_type", "Trial")), key=f"plan_sel_{acc_mail}", disabled=is_system_busy)
                    renew_choice = st.selectbox("Gia hạn:", ["Giữ nguyên hạn hiện tại", "3 Ngày", "7 Ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "Vĩnh viễn", "Tùy chỉnh (Chọn ngày)"], key=f"renew_opt_{acc_mail}", disabled=is_system_busy)
                    target_exp_str = info.get("expires_at", "2099-12-31")
                    if renew_choice == "Tùy chỉnh (Chọn ngày)":
                        try: cur_d = datetime.strptime(info.get("expires_at", ""), "%Y-%m-%d").date()
                        except: cur_d = date.today() + timedelta(days=30)
                        target_exp_str = st.date_input("Chọn ngày hết hạn mới:", value=cur_d, min_value=date.today(), key=f"rdate_{acc_mail}", disabled=is_system_busy).strftime("%Y-%m-%d")
                    elif renew_choice == "Vĩnh viễn": target_exp_str = "2099-12-31"
                    elif renew_choice != "Giữ nguyên hạn hiện tại":
                        dur_map_v = {"3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730}
                        target_exp_str = (datetime.now() + timedelta(days=dur_map_v.get(renew_choice, 30))).strftime("%Y-%m-%d")

                    c_act1, c_act2 = st.columns(2)
                    if c_act1.button("🔄 Cập Nhật", key=f"save_renew_{acc_mail}", use_container_width=True, disabled=is_system_busy):
                        st.session_state.licensed_accounts[acc_mail].update({"password": new_user_pass.strip(), "roles": new_roles, "plan_type": new_plan, "expires_at": target_exp_str})
                        save_single_account(acc_mail, st.session_state.licensed_accounts[acc_mail])
                        st.toast("✅ Đã cập nhật!"); st.rerun()
                    if c_act2.button("🗑 Xóa", key=f"del_acc_{acc_mail}", type="secondary", use_container_width=True, disabled=is_system_busy):
                        delete_single_account(acc_mail)
                        if acc_mail in st.session_state.licensed_accounts: del st.session_state.licensed_accounts[acc_mail]
                        st.toast("✅ Đã xóa!"); st.rerun()

            if not search_acc.strip() and len(other_accs) > 3:
                if st.session_state.get("show_all_admin_accounts", False):
                    if st.button("🔼 Thu gọn danh sách tài khoản", use_container_width=True, disabled=is_system_busy):
                        st.session_state.show_all_admin_accounts = False; st.rerun()
                else:
                    if st.button(f"🔽 Xem thêm {len(other_accs)-3} tài khoản", use_container_width=True, disabled=is_system_busy):
                        st.session_state.show_all_admin_accounts = True; st.rerun()

        st.markdown("---")
        st.markdown("""<div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:1.5px solid #86efac;border-radius:12px;padding:10px;text-align:center;margin-bottom:10px;"><div style="font-size:13px;font-weight:800;color:#15803d;">🎧 HỖ TRỢ TRỰC TIẾP (ZALO/HOTLINE)</div><div style="font-size:18px;font-weight:900;color:#991b1b;margin-top:4px;">0869 628 316</div></div>""", unsafe_allow_html=True)
        u_info = st.session_state.get("licensed_accounts", {}).get(st.session_state.get("current_email", ""), {})
        u_plan = u_info.get("plan_type", "Trial")
        u_used = u_info.get("daily_usage_count", 0) if u_info.get("last_generation_date") == datetime.now().strftime("%Y-%m-%d") else 0
        u_lim = "Không giới hạn" if u_plan == "VIP" else (20 if u_plan == "Advanced" else (10 if u_plan == "Basic" else 3))
        st.info(f"**GÓI {u_plan.upper()}**\n\n• Email: {st.session_state.get('current_email', '')}\n• Đã tạo: **{u_used}/{u_lim}**\n• Hạn dùng: {u_info.get('expires_at')}")
        if st.button("🚪 Đăng Xuất", disabled=is_system_busy): 
            st.session_state.is_logged_in = False; st.rerun()

if not st.session_state.get("is_logged_in", False): 
    st.info("👈 Vui lòng đăng nhập ở thanh bên.")
    st.stop()

# ==============================================================================
# 10. KHÔNG GIAN SÁNG TẠO CHÍNH (MAIN APP UI)
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Đạo Diễn AI - Hệ Thống Kịch Bản Pro</div></div>""", unsafe_allow_html=True)

user_allowed_modules = st.session_state.get("licensed_accounts", {}).get(st.session_state.get("current_email", ""), {}).get("roles", ALL_MODULES) or ALL_MODULES
mode = st.selectbox("🎯 Thể loại:", user_allowed_modules, key=f"mode_sel_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)
is_viral_mode = "Viral" in mode

up_files, custom_note = [], ""
viral_persona, viral_topic = "", ""

if not st.session_state.get("is_analyzed", False):
    if is_viral_mode:
        col_v1, col_v2 = st.columns(2)
        viral_persona = col_v1.text_input("👤 Định vị Kênh:", placeholder="Ví dụ: Mẹ bỉm sữa thông thái...", key=f"viral_persona_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)
        viral_topic = col_v2.text_area("💡 Chủ đề / Mẹo:", height=68, placeholder="Ví dụ: 3 mẹo setup góc làm việc gọn gàng...", key=f"viral_topic_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)
        up_files = st.file_uploader("📦 Upload Ảnh:", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_viral_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)
        if up_files:
            with st.expander(f"👁 Xem lại {len(up_files)} ảnh đã tải lên", expanded=False):
                n_cols = min(len(up_files), 4)
                cols = st.columns(n_cols)
                for idx, f in enumerate(up_files): cols[idx % n_cols].image(f, caption=f"Ảnh {idx + 1}", use_container_width=True)
        custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất - ví dụ: quần là dạng váy 1 ống rộng):", key=f"custom_note_viral_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)
        hero_sku_override = ""
    else:
        products_data = supabase.table("products").select("*").execute().data if supabase else []
        if products_data:
            selected_name = st.selectbox("📌 Chọn sản phẩm:", [p["product_name"] for p in products_data], key=f"prod_select_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)
            st.session_state.current_product_data = next(p for p in products_data if p["product_name"] == selected_name)
        col_f1, col_f2 = st.columns([2, 1])
        up_files = col_f1.file_uploader("📦 Upload Ảnh SP (Quét OCR Giá, Hero SKU & Bảng màu):", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_prod_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)
        hero_sku_override = col_f2.text_input("🎯 Màu / SKU ưu tiên (Tùy chọn):", placeholder="Ví dụ: Trắng tinh...", key=f"hero_override_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)
        if up_files:
            with st.expander(f"👁 Xem lại {len(up_files)} ảnh sản phẩm đã tải lên", expanded=False):
                n_cols = min(len(up_files), 4)
                cols = st.columns(n_cols)
                for idx, f in enumerate(up_files): cols[idx % n_cols].image(f, caption=f"Ảnh {idx + 1}", use_container_width=True)
        custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất - ví dụ: quần là dạng váy 1 ống rộng):", key=f"custom_note_prod_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)

    style = "Điện Ảnh Chân Thực"
    col_strat, col_role, col_actor_img = st.columns([1.4, 1.6, 1.0])
    unified_strategy_format = col_strat.selectbox("🧭 Chiến lược & Hình thức Video:", UNIFIED_STRATEGY_FORMAT_OPTS, index=0, key=f"unified_strat_format_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)
    role_input = col_role.text_input("👤 Vai trò NV (Để trống = AI tự phân tích):", value="", placeholder="Ví dụ: Nam 25t...", key=f"r_0_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)
    c_file = col_actor_img.file_uploader("📸 Ảnh mẫu NV (Tùy chọn):", type=["jpg", "png"], key=f"f_0_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)

    char_inputs = [{"id": 1, "role": role_input.strip(), "file": c_file}] if (c_file or role_input.strip()) else []

    if st.button("🚀 Phân Tích Sản Phẩm Và Tạo Lời Thoại", type="primary", use_container_width=True, disabled=is_system_busy):
        can_run, msg = check_usage_limit(st.session_state.get("current_email", ""))
        if not can_run: 
            st.error(msg)
        else:
            temp_images = []
            if up_files:
                for f in up_files:
                    cb, cm = compress_image_bytes(f, 768, 75)
                    temp_images.append((cb, cm))
            
            avatar_file = None
            if c_file:
                cb, cm = compress_image_bytes(c_file, 768, 75)
                avatar_file = {"data": cb, "mime": cm}
            
            st.session_state.temp_main_args = {
                "viral_persona": viral_persona.strip() if is_viral_mode else "",
                "viral_topic": viral_topic.strip() if is_viral_mode else "",
                "custom_note": custom_note.strip(),
                "hero_sku_override": hero_sku_override.strip() if not is_viral_mode else "",
                "unified_strategy_format": unified_strategy_format,
                "role_input": role_input.strip(),
                "avatar_file": avatar_file,
                "temp_images": temp_images
            }
            st.session_state.trigger_main_generation = True
            st.rerun()

if st.session_state.get("trigger_main_generation"):
    st.session_state.trigger_main_generation = False
    args = st.session_state.get("temp_main_args", {})
    with st.spinner("⏳ Đạo diễn AI đang phân tích sản phẩm (Super Lite Token) ..."):
        try:
            char_inputs = []
            if args.get("avatar_file") or args.get("role_input"):
                char_inputs.append({"id": 1, "role": args.get("role_input", ""), "file_bytes": args.get("avatar_file")})
            
            st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs] if char_inputs else [{"id": 1, "role": ""}]
            char_rules = generate_char_rules_string(st.session_state.get("character_profiles", []))
            st.session_state.update({
                "last_mode": mode, "last_style": "Điện Ảnh Chân Thực", "last_narrator": "On-camera", 
                "last_presentation_format": args.get("unified_strategy_format", ""),
                "current_input_context": args.get("custom_note", "")
            })
            
            if is_viral_mode:
                st.session_state.current_product_data_saved = {"channel_persona": args.get("viral_persona", ""), "topic_or_tips": args.get("viral_topic", "")}
                input_context_str = f"KÊNH: '{args.get('viral_persona', '')}' | CHỦ ĐỀ: '{args.get('viral_topic', '')}' | NOTE: '{args.get('custom_note', '')}'"
            else:
                st.session_state.current_product_data_saved = st.session_state.get("current_product_data", {})
                input_context_str = f"SP: {json.dumps(st.session_state.get('current_product_data_saved', {}), ensure_ascii=False)} | NOTE: '{args.get('custom_note', '')}'"
            
            st.session_state["saved_reference_images"] = args.get("temp_images", [])

            override_instruction = f"Khóa màu Hero SKU: '{args.get('hero_sku_override', '')}'" if args.get('hero_sku_override') else "Ưu tiên SKU icon 🔥/Hot. Chỉ chọn 1 MÀU DUY NHẤT để khóa!"
            skirt_note_rule = "ĐẶC BIỆT: Nếu quần dạng váy 1 ống/quần váy, BẮT BUỘC 'vis_en' là 'full-length A-line maxi skirt (single unified unsplit skirt tube, zero leg division)'!" if detect_single_tube_skirt(args.get("custom_note", "")) else ""

            prompt = f"""
            INPUT: {input_context_str} | THỂ LOẠI: '{mode}' | CHIẾN LƯỢC: '{args.get("unified_strategy_format", "")}'
            HERO SKU: {override_instruction}
            {skirt_note_rule}
            - Tách biệt 100% SP khỏi người mẫu gốc trong ảnh.
            - KOC 100% LÀ NGƯỜI VIỆT NAM (Vietnamese). Phân tích đúng đối tượng sử dụng SP để chọn koc_g (male/female) và koc_a (child/teen/adult/senior).
            
            TRẢ VỀ DUY NHẤT ĐỊNH DẠNG JSON SIÊU NÉN:
            {{
                "ca": {{
                    "pro_s": "Đại từ xưng (VD: em)",
                    "pro_a": "Đại từ gọi (VD: các chị em)",
                    "koc_g": "male hoặc female",
                    "koc_a": "child / teen / adult / senior",
                    "p_orig": <Giá 250000 CHỮ, INT, KHÔNG VD: dạng gốc số>,
                    "p_sale": <Giá 150000 CHỮ, INT, KHÔNG VD: dạng giảm số>,
                    "c_vi": "Màu/Họa tiết tiếng Việt",
                    "c_en": "Exact English color pattern",
                    "vis_en": "Mô tả SP tiếng Anh max 20 words. CRITICAL GEOMETRY LOCK: Mô tả rõ quai/tay cầm gốc.",
                    "name": "[Tên SP]: [Điểm độc bản USP]",
                    "dim": "Kích thước"
                }},
                "scripts": [
                    {{ "id": 1, "title": "Bản Năng Động", "set": "Bối cảnh khớp 100% thoại", "vo": "Đoạn thoại dài 80-110 từ, liền mạch..." }},
                    {{ "id": 2, "title": "Bản Tâm Sự", "set": "Bối cảnh khớp 100% thoại", "vo": "Đoạn thoại dài 80-110 từ, liền mạch..." }},
                    {{ "id": 3, "title": "Bản Chuyên Gia", "set": "Bối cảnh khớp 100% thoại", "vo": "Đoạn thoại dài 80-110 từ, liền mạch..." }}
                ]
            }}
            """
            payload = ["PRODUCT IMAGES (EXTRACT RIGID 3D STRUCTURE, EXACT HANDLES/STRAPS, TRUE COLOR, AND OCR PRICES - IGNORE HUMAN MODELS):"]
            for cb, cm in args.get("temp_images", []):
                payload.append(types.Part.from_bytes(data=cb, mime_type=cm))
            for c in char_inputs:
                if c.get("file_bytes"):
                    payload.extend([f"ACTOR {c['id']} (EXTRACT AGE, GENDER, HAIR ONLY):", types.Part.from_bytes(data=c["file_bytes"]["data"], mime_type=c["file_bytes"]["mime"])])
            payload.append(prompt)
            
            ca_result, outlines = {}, []
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    res = call_gemini(payload, get_sys_inst_outlines(mode, "Điện Ảnh Chân Thực", "On-camera", char_rules, 1, args.get("unified_strategy_format", ""), args.get("custom_note", ""), args.get("unified_strategy_format", "")), max_tokens=4096)
                    ca_result = res.get("ca", res.get("content_analysis", {}))
                    outlines = extract_scenes(res)
                    if ca_result and outlines: break
                except Exception as e:
                    if attempt == max_retries - 1: raise Exception(f"Lỗi khi gọi AI: {str(e)}")
                    time.sleep(1.5)
            
            if not outlines: raise Exception("AI không tạo được danh sách kịch bản. Vui lòng bấm tạo lại.")
            
            st.session_state.content_analysis = ca_result
            
            for o in outlines:
                vo_script = o.get("vo", o.get("full_voiceover_script", ""))
                o["full_voiceover_script"] = clean_and_normalize_voiceover(vo_script)
                o["setting"] = o.get("set", o.get("setting", ""))
                o.update({
                    "duration_instruction": "Max 10s", 
                    "narrator_mode": "On-camera", 
                    "character_profiles": st.session_state.get("character_profiles", []), 
                    "actors": 1,
                    "custom_note": args.get("custom_note", ""),
                    "presentation_format": args.get("unified_strategy_format", "")
                })
            
            auto_proj_title = extract_bold_product_title(ca_result, fallback_topic=args.get("viral_topic", ""))
            st.session_state.update({
                "active_project_title": auto_proj_title, "current_project_id": None,
                "all_scripts": outlines, "cloned_scripts": [], "expanded_scripts": [],
                "generated_details": {}, "active_script_id": None, "is_analyzed": True
            })
            auto_save_current_session()
            st.toast(f"✅ Đã phân tích & tự động lưu dự án: {auto_proj_title}!")
            st.session_state.scroll_to_top = True
            st.rerun()
        except Exception as e: 
            st.error(f"❌ Lỗi: {e}")

ca = st.session_state.get("content_analysis")
if isinstance(ca, dict):
    st.divider()
    col_hdr1, col_hdr2 = st.columns([2.5, 1.5])
    col_hdr1.markdown("### 🔍 **Phân Tích Thông Số Kỹ Thuật (Ultra Lite Mode)**")
    if st.session_state.get("last_autosave_time"):
        col_hdr2.markdown(f"<div style='text-align:right;'><span class='autosave-badge'>☁️ Dự án: <b>{st.session_state.get('active_project_title', '')}</b> (Đã tự động lưu {st.session_state.get('last_autosave_time', '')})</span></div>", unsafe_allow_html=True)
    
    col_row1_left, col_row1_right = st.columns(2)
    with col_row1_left:
        koc_g = ca.get('koc_g', 'female')
        koc_a = ca.get('koc_a', 'adult')
        age_map = {"child": "Trẻ em", "teen": "Thiếu niên", "adult": "Thanh niên", "senior": "Người cao tuổi"}
        gender_map = {"male": "Nam", "female": "Nữ"}
        
        user_specified_actors = [p['role'] for p in st.session_state.get('character_profiles', []) if str(p.get('role', '')).strip()]
        koc_display_str = f"👤 <b>KOC:</b> {', '.join(user_specified_actors)} (Người dùng chỉ định)" if user_specified_actors else f"🤖 <b>KOC thuần Việt:</b> {gender_map.get(koc_g, 'Nữ')} {age_map.get(koc_a, 'Thanh niên')} (Tự động)"
        
        pronoun_badge = f"🗣 <b>Nhân xưng:</b> KOC xưng <b>'{ca.get('pro_s', 'em')}'</b> - Gọi người xem là <b>'{ca.get('pro_a', 'mọi người')}'</b>"
        
        st.markdown(clean_html(f"""
        <div class="dna-card">
            <div class="dna-card-title">🎭 1. Định Vị KOC, Stylist & Giọng Đọc</div>
            <div class="dna-row"><span class="dna-label">👤 Chân dung KOC:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{koc_display_str}</span></div>
            <div class="dna-row"><span class="dna-label">👗 Stylist Phối đồ:</span><span class="dna-text" style="color:#7c3aed; font-weight:600;">Tự động phối đồ bám sát bối cảnh, bảo toàn form dáng xuyên suốt 4 cảnh.</span></div>
            <div class="dna-row"><span class="dna-label">🗣 Nhân xưng & Giọng đọc:</span><span class="dna-text" style="color:#15803d; font-weight:700;">{pronoun_badge}</span></div>
        </div>"""), unsafe_allow_html=True)

    with col_row1_right:
        dim_txt_display = ca.get('dim', 'Chuẩn đời thực')
        locked_color_preview = translate_and_lock_color_en(ca.get('c_vi', ''), ca.get('c_en', ''))
        
        p_orig = ca.get('p_orig', 0)
        p_sale = ca.get('p_sale', 0)
        
        try: p_orig_int = int(p_orig)
        except: p_orig_int = 0
        try: p_sale_int = int(p_sale)
        except: p_sale_int = 0
        
        soft_orig = convert_to_soft_price_range(p_orig_int, True) if p_orig_int else "giá niêm yết"
        soft_sale = convert_to_soft_price_range(p_sale_int, False) if p_sale_int else "deal cực hời"
        
        st.markdown(clean_html(f"""
        <div class="dna-card">
            <div class="dna-card-title">💎 2. Thông số Sản phẩm & Hình học 3D</div>
            <div class="dna-row"><span class="dna-label">📦 SP & Điểm đặc biệt:</span><span class="dna-text">{format_product_name_bold(ca.get('name', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">🧱 Khóa Hình Học 3D:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{ca.get('vis_en', 'Chuẩn ảnh gốc')}</span></div>
            <div class="dna-row"><span class="dna-label">⭐ Khóa màu/Họa tiết:</span><span class="dna-text" style="color:#dc2626; font-weight:700;">{clean_analysis_text(ca.get('c_vi', 'Tự động'))} ({locked_color_preview})</span></div>
            <div class="dna-row"><span class="dna-label" style="color:#dc2626;">🎯 Mức giá (Nay giảm):</span><span class="dna-text" style="color:#dc2626; font-weight:700;">Bình thường {soft_orig}, nay giảm {soft_sale}</span></div>
        </div>"""), unsafe_allow_html=True)

all_sc = st.session_state.get("all_scripts", []) + st.session_state.get("cloned_scripts", []) + st.session_state.get("expanded_scripts", [])
if all_sc:
    st.divider()
    
    ui_action_ph = st.empty()

    def is_generated(sc_id): return (str(sc_id) in st.session_state.get("generated_details", {}) or sc_id in st.session_state.get("generated_details", {}))
    comp_sc = [sc for sc in all_sc if is_generated(sc.get("id"))]
    pend_sc = [sc for sc in all_sc if not is_generated(sc.get("id"))]

    if st.session_state.get("active_script_id") is not None:
        if st.button("🔼 Thu gọn kịch bản chi tiết", disabled=is_system_busy):
            st.session_state.active_script_id = None; st.rerun()
            
        active_id = st.session_state.get("active_script_id")
        asc = st.session_state.get("generated_details", {}).get(str(active_id), st.session_state.get("generated_details", {}).get(active_id, {}))
        
        st.markdown("<div id='detailed-view-anchor'></div>", unsafe_allow_html=True)
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(asc.get('title', '')).upper()}**")
        
        director_summary_html = asc.get('director_summary', '')
        if not director_summary_html:
            total_sec = 0.0
            for s in asc.get("scenes", []):
                d_str = str(s.get('dur', '8s')).replace('s', '').strip()
                try: total_sec += float(d_str)
                except: total_sec += 8.0
            
            summary_lines = [
                f"⏱ <b>Thời lượng:</b> Khoảng {int(total_sec)}s",
                f"🏙 <b>Bối cảnh Master:</b> Khớp chuẩn sự kiện"
            ]
            director_summary_html = "<br>".join(summary_lines)
        st.markdown(f"<div class='detail-header-box'>{director_summary_html}</div>", unsafe_allow_html=True)
        
        for idx, scn in enumerate(asc.get("scenes", []), 1):
            vo_text = clean_and_normalize_voiceover(scn.get('voiceover', scn.get('vo', '')))
            actual_words = count_words(vo_text)
            comma_count, period_count = vo_text.count(',') + vo_text.count(';'), vo_text.count('.') + vo_text.count('!') + vo_text.count('?')
            curr_mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
            is_tts = ("Viral" not in curr_mode)
            speech_sec = scn.get('actual_speech_sec', calculate_speech_duration(vo_text, is_tts))
            
            dur_str = str(scn.get('dur', '8s')).replace('s', '').strip()
            try: dur_int = int(float(dur_str))
            except: dur_int = 8
            
            safe_cushion = round(max(0.0, dur_int - speech_sec), 1)
            
            st.markdown(f"#### 📍 Phân cảnh {idx} - Giai đoạn {scn.get('aida_stage', scn.get('dir', ''))}")
            st.markdown(f"<span class='timing-badge'>⏱ Khung phân cảnh chuẩn: {scn.get('dur', '8s')} (Max 10s Veo 3) | Khớp nhịp đọc thực tế: ~{speech_sec}s ({actual_words} từ, {comma_count} phẩy, {period_count} ngắt | ~{round(actual_words/max(1.0, speech_sec), 1)} từ/s) | 🛡 Đệm diễn xuất tự nhiên: +{safe_cushion}s</span>", unsafe_allow_html=True)
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting', scn.get('set', ''))}*\n\n**😊 Vi biểu cảm & Cử chỉ:** *{scn.get('expression_en', scn.get('exp', 'Tự nhiên, rạng rỡ'))}*\n\n**🎵 Hiệu ứng âm thanh:** *{scn.get('sfx', 'Âm thanh thực tế sống động')}*\n\n**🎙 Đạo diễn KOC:** *{scn.get('director', scn.get('dir', ''))}*\n\n**💬 Đoạn thoại cắt tương ứng:** <div class='voiceover-text'>{vo_text}</div>", unsafe_allow_html=True)
            
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                is_no_prod = scn.get("is_no_product_scene", False)
                if is_no_prod:
                    st.markdown("<div class='no-product-warning'>🚨 LƯU Ý: Phân cảnh này KHÔNG CÓ SẢN PHẨM. Bạn KHÔNG CẦN dùng ảnh tham chiếu sản phẩm khi tạo ảnh!</div>", unsafe_allow_html=True)
                    st.markdown("**🖼 Prompt Ảnh Tinh Gọn (KHÔNG SẢN PHẨM):**")
                else:
                    st.markdown("**🖼 Prompt Ảnh Tinh Gọn (Midjourney / Flux):**")
                st.code(img_p := scn.get('img_p', ''), language="text")
                safe_copy_button(img_p, f"📋 Sao Chép Prompt Ảnh Cảnh {idx}")
                if not is_no_prod:
                    st.caption("💡 *Mẹo giữ nhân vật & màu sản phẩm đồng nhất:* Sau khi tạo ảnh Cảnh 1 ưng ý, copy link ảnh và gắn vào đuôi prompt Cảnh 2, 3, 4: `--cref [URL_ẢNH_CẢNH_1] --cw 100`")
                
            with c_p2:
                st.markdown("**🎥 Prompt Video Tinh Gọn (Veo 3 Pro - Âm thanh Studio, Chống Vấp Thoại):**")
                st.code(vid_p := scn.get('vid_p', ''), language="text")
                safe_copy_button(vid_p, f"📋 Sao Chép Prompt Video Cảnh {idx}")
            
            with st.expander(f"🛡 Negative Prompt Chuyên Biệt Cảnh {idx}", expanded=False):
                neg_val = scn.get('vid_neg', 'extra fingers, text, watermark, background music')
                st.code(neg_val, language="text")
                safe_copy_button(neg_val, f"📋 Sao Chép Negative Prompt Cảnh {idx}", custom_color="#475569")
            st.markdown("---")
            
        if st.session_state.get("scroll_to_detail", False): 
            components.html("""
            <script>
                setTimeout(() => { 
                    const el = window.parent.document.getElementById('detailed-view-anchor'); 
                    if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); } 
                    else { window.parent.scrollTo({top: 500, behavior: 'smooth'}); } 
                }, 400);
            </script>""", height=0)
            st.session_state.scroll_to_detail = False

    if comp_sc:
        st.markdown("### 🎬 **1. Kịch Bản ĐÃ Dựng Chi Tiết**")
        for outline in comp_sc:
            sc_id = outline["id"]
            with st.container(border=True):
                c1, c2, c3 = st.columns([2.5, 1, 1])
                c1.markdown(f"**#{sc_id}. {outline.get('title')}** <span class=badge-ready>ĐÃ LƯU</span>", unsafe_allow_html=True)
                vo_preview = outline.get("full_voiceover_script", outline.get("vo", outline.get("hook", "")))
                c1.markdown(f"<div class='preview-script'>💬 {clean_and_normalize_voiceover(vo_preview)}</div>", unsafe_allow_html=True)
                
                if str(sc_id) != str(st.session_state.get("active_script_id", "")):
                    if c2.button("👁 Xem lại", key=f"r_{sc_id}", use_container_width=True, disabled=is_system_busy):
                        st.session_state.active_script_id = int(sc_id)
                        st.session_state.scroll_to_detail = True
                        st.rerun()
                btn_clone_ph = c3.empty()
                if str(st.session_state.get("current_cloning_id", "")) == str(sc_id):
                    if btn_clone_ph.button("🛑 Đang nhân bản...", key=f"unhang_c_{sc_id}", type="secondary", use_container_width=True):
                        st.session_state.current_cloning_id = None; st.rerun()
                else:
                    if btn_clone_ph.button("🚀 Nhân bản", key=f"c_{sc_id}", type="primary", use_container_width=True, disabled=is_system_busy):
                        can_run, msg = check_usage_limit(st.session_state.get("current_email", ""))
                        if can_run: st.session_state.current_cloning_id = sc_id; st.rerun()
                        else: st.error(msg)

    if pend_sc:
        st.markdown("### ⏳ **2. Kịch Bản Chờ Dựng**")
        for outline in pend_sc:
            sc_id = outline["id"]
            with st.container(border=True):
                c1, c2 = st.columns([3, 1.2])
                c1.markdown(f"**#{sc_id}. {outline.get('title')}** <span class=badge-pending>CHỜ DỰNG</span>", unsafe_allow_html=True)
                vo_preview = outline.get("full_voiceover_script", outline.get("vo", outline.get("hook", "")))
                c1.markdown(f"<div class='preview-script'>💬 {clean_and_normalize_voiceover(vo_preview)}</div>", unsafe_allow_html=True)
                
                btn_detail_ph = c2.empty()
                if str(st.session_state.get("current_processing_id", "")) == str(sc_id):
                    if btn_detail_ph.button("🛑 Đang dựng...", key=f"unhang_p_{sc_id}", type="secondary", use_container_width=True):
                        st.session_state.current_processing_id = None; st.rerun()
                else:
                    if btn_detail_ph.button("✨ Tạo chi tiết ngay", key=f"cr_{sc_id}", type="secondary", use_container_width=True, disabled=is_system_busy):
                        can_run, msg = check_usage_limit(st.session_state.get("current_email", ""), is_detailing=True)
                        if can_run: st.session_state.current_processing_id = sc_id; st.rerun()
                        else: st.error(msg)

    if st.session_state.get("current_processing_id") is not None:
        target_id_to_run = st.session_state.get("current_processing_id")
        success, error_msg = False, ""
        with ui_action_ph.container():
            try:
                with st.spinner(f"⏳ Đang cắt cảnh & dựng prompt chi tiết cho kịch bản #{target_id_to_run}..."):
                    create_scene_details(target_id_to_run, st.session_state.get("last_mode", ""), "Điện Ảnh Chân Thực")
                    st.session_state.active_script_id = int(target_id_to_run)
                    success = True
            except Exception as e: error_msg = str(e)
            
        st.session_state.current_processing_id = None
        if success: 
            st.toast(f"✅ Đã dựng xong phân cảnh chi tiết kịch bản #{target_id_to_run}!")
            st.session_state.scroll_to_detail = True
            st.rerun()
        else: st.error(f"❌ Lỗi khi dựng kịch bản: {error_msg}")

    if st.session_state.get("current_cloning_id") is not None:
        clone_id_to_run = st.session_state.get("current_cloning_id")
        success, error_msg = False, ""
        with ui_action_ph.container():
            try:
                with st.spinner(f"⏳ Đang nhân bản 3 biến thể cho kịch bản #{clone_id_to_run} & tự động lưu cập nhật..."):
                    st.session_state.cloned_scripts.extend(clone_script(clone_id_to_run))
                    auto_save_current_session()
                    success = True
            except Exception as e: error_msg = str(e)
            
        st.session_state.current_cloning_id = None
        if success: 
            st.toast("✅ Đã nhân bản thành công 3 kịch bản voice bám sát gốc!")
            st.session_state.scroll_to_top = True
            st.rerun()
        else: st.error(f"❌ Lỗi khi nhân bản kịch bản: {error_msg}")

    # ==========================================================================
    # 12. KHU VỰC GỌI THÊM 3 KỊCH BẢN MỚI
    # ==========================================================================
    st.divider()
    st.markdown("### ➕ **Gọi Thêm 3 Kịch Bản Mới**")
    
    cy1, cy2, cy3 = st.columns([1.4, 1.6, 1.0])
    c_unified_more = cy1.selectbox("🧭 Chiến lược & Hình thức Video mới:", UNIFIED_STRATEGY_FORMAT_OPTS, index=0, key=f"more_unified_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)
    e_role = cy2.text_input("👤 Vai trò NV mới (Để trống = AI tự phân tích):", value="", placeholder="Để trống = Giữ nguyên hoặc AI tự phân tích...", key=f"er_0_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)
    e_file = cy3.file_uploader("📸 Ảnh mẫu NV mới (Tùy chọn):", type=["jpg", "png"], key=f"ef_0_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)
    extra_custom_note = st.text_area("✍ Ghi chú AI cho kịch bản thêm (Ưu tiên cao nhất):", placeholder="Ví dụ: Quần là dạng váy 1 ống rộng...", key=f"extra_custom_note_{st.session_state.get('reset_key', 0)}", disabled=is_system_busy)

    if st.button("🚀 Gọi Thêm 3 Kịch Bản Mới", type="primary", use_container_width=True, disabled=is_system_busy):
        can_run, msg = check_usage_limit(st.session_state.get("current_email", ""))
        if can_run:
            st.session_state.temp_more_args = {
                "format": c_unified_more,
                "role": e_role.strip(),
                "note": extra_custom_note
            }
            st.session_state.trigger_more_generation = True
            st.rerun()
        else: st.error(msg)
        
if st.session_state.get("trigger_more_generation"):
    st.session_state.trigger_more_generation = False
    args = st.session_state.get("temp_more_args", {})
    with st.spinner("⏳ Đang sáng tạo thêm 3 kịch bản & tự động lưu cập nhật vào dự án..."):
        try:
            p_chars = [{"id": 1, "role": args["role"]}] if args["role"] else st.session_state.get("character_profiles", [])
            new_sc = generate_more_scripts(args.get("format", ""), p_chars, args.get("note", ""))
            st.session_state.expanded_scripts.extend(new_sc)
            auto_save_current_session()
            st.toast("✅ Đã sinh thêm 3 kịch bản mới & tự động lưu cập nhật vào dự án!")
            st.session_state.scroll_to_top = True
            st.rerun()
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
