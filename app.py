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
# 1. CẤU HÌNH GIAO DIỆN & KHỞI TẠO BIẾN STATE (FIX LỖI KEY ERROR TẠI ĐÂY)
# ==============================================================================
st.set_page_config(page_title="Đạo Diễn AI - Hệ Thống Kịch Bản Pro", page_icon="🎬", layout="wide")

# KHỞI TẠO STATE NGAY ĐẦU TIÊN ĐỂ CHỐNG LỖI ATTRIBUTE/KEY ERROR
if "session_id" not in st.session_state: st.session_state.session_id = str(uuid.uuid4())
for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", {}), # Đảm bảo mặc định là dictionary trống
    ("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []),
    ("generated_details", {}), ("content_analysis", None), ("active_script_id", None),
    ("current_input_context", ""), ("current_product_data_saved", None), ("current_product_data", None),
    ("reset_key", 0), ("scroll_to_top", False), ("scroll_to_detail", False),
    ("trigger_main_generation", False), ("trigger_more_generation", False),
    ("temp_main_args", {}), ("temp_more_args", {}),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"),
    ("last_mode", "🛒 TikTok Shop & Bán Hàng"), ("last_style", "Điện Ảnh Chân Thực"), ("last_narrator", "On-camera"),
    ("last_presentation_format", "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng"),
    ("target_duration_instruction", ""), ("character_profiles", []), ("current_project_id", None),
    ("saved_reference_images", []), ("show_all_projects", False), ("show_all_admin_accounts", False),
    ("current_processing_id", None), ("current_cloning_id", None), ("is_analyzed", False), ("last_autosave_time", "")
]:
    if key not in st.session_state: st.session_state[key] = default_val

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
# 2. KHỞI TẠO TỪ ĐIỂN, HẰNG SỐ CỐT LÕI
# ==============================================================================
ALL_MODULES = ["🛒 TikTok Shop & Bán Hàng", "🌟 Viral & Xây Kênh"]
ADMIN_EMAIL = "binhnguyenmedia.vn@gmail.com"

UNIFIED_STRATEGY_FORMAT_OPTS = [
    "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng",
    "📦 Review & Bóc Hộp Soi Chi Tiết (Freshly Unboxed)",
    "👶 Trải Nghiệm Thực Tế Đời Sống (Lifestyle POV)",
    "⚡ Flash Sale & Deal Hời (Bóc Hộp + Trải Nghiệm)",
    "🎭 Giải Quyết Nỗi Đau (PAS Thực Chiến)",
    "🔍 Review Thực Chiến & Test Công Năng",
    "💡 Chia Sẻ Mẹo Hay & Kiến Thức Hữu Ích",
    "😂 Tình Huống Hài Hước & Đời Thường"
]

COMPACT_CORE_RULES = """
🛑 QUY TẮC CỐT LÕI (BẮT BUỘC TUÂN THỦ 100%):
1. KOC 100% LÀ NGƯỜI VIỆT NAM & ĐÚNG ĐỘ TUỔI TÙY SẢN PHẨM: AI tự phân tích tệp khách hàng để gán KOC là Nam/Nữ, Trẻ em/Thanh niên/Người già. Tuyệt đối CẤM tạo người nước ngoài. Khóa chặt diện mạo, MÀU SẮC ĐÍCH DANH và CHẤT LIỆU xuyên suốt 4 cảnh.
2. HÀNH ĐỘNG HÌNH THỂ & VỊ TRÍ TƯƠNG TÁC (CRITICAL):
   - Cảnh 1 (Nêu nỗi đau): BẮT BUỘC có hành động hình thể chân thực (VD: ngứa thì gãi mạnh, hôi thì nhăn mặt bịt mũi, mỏi thì xoa bóp).
   - MỸ PHẨM: Công dụng ở đâu bôi CHÍNH XÁC ở đó! Son bôi môi, má hồng bôi má, lăn nách bôi nách. CẤM đưa các SP không phải dưỡng mặt lên mặt.
   - GIA DỤNG/THỜI TRANG: Cấm đưa lên mặt. Tương tác ngang ngực/eo hoặc dưới sàn. Cầm đúng tay cầm gốc, KHÔNG thả rơi.
   - 100% CÁC CẢNH KOC ĐỀU NÓI TRỰC TIẾP VÀO ỐNG KÍNH (No off-screen narrator). Giọng Hà Nội phải khớp độ tuổi/giới tính KOC.
3. LÕI THOẠI KOC THỰC CHIẾN & CHỐNG LẶP TỪ (CRITICAL):
   - NHẬP VAI 3 PHONG CÁCH: Kịch bản 1 (Năng động, dồn dập). Kịch bản 2 (Tâm sự, thủ thỉ, gần gũi). Kịch bản 3 (Chuyên gia, tập trung công năng).
   - CHỐNG LẶP TỪ TUYỆT ĐỐI: Không lặp từ trong cùng câu (Cấm "giá đang giảm giá", cấm "form hộp đứng form").
   - VĂN PHONG CHỐT SALE TỰ NHIÊN: Cấm "ngay tay". Chốt tự nhiên: "Deal hôm nay quá êm, mấy bà nhấp góc trái múc luôn nha".
4. VĂN NÓI HÀ NỘI THUẦN VIỆT:
   - CẤM sử dụng dấu chấm lửng (...), dấu gạch nối (-), ký hiệu ([ ]) trong thoại.
"""

INTIMATE_SAFE_ENGLISH_LEXICON = {
    r'\b(?:push-?up\s+|lace\s+|wireless\s+|seamless\s+)?bras?\b': 'seamless comfort fabric top',
    r'\bbrassieres?\b': 'seamless support garment',
    r'\b(?:lace\s+|cotton\s+|seamless\s+)?panties\b': 'seamless breathable fabric layer',
    r'\bunderwears?\b': 'soft stretchable fabric base',
    r'\bbriefs?\b': 'seamless textile base',
    r'\bthongs?\b': 'seamless stretch fabric',
    r'\blingerie\b': 'premium textile item',
    r'\bbikinis?\b': 'resort stretch wear',
    r'\bcleavage\b': 'modest neckline',
    r'\bsexy\b': 'elegant',
    r'\bcrotch\b': 'fabric gusset'
}

POLICY_REPLACEMENTS = {
    r'\ban\s*toàn\s*tuyệt\s*đối\b': 'cực kỳ an toàn', r'\byên\s*tâm\s*tuyệt\s*đối\b': 'cực kỳ yên tâm',
    r'\btuyệt\s*đối\s*an\s*toàn\b': 'cực kỳ an toàn', r'\btuyệt\s*đối\s*yên\s*tâm\b': 'cực kỳ yên tâm',
    r'\bhoàn\s*toàn\s*yên\s*tâm\b': 'cực kỳ yên tâm', r'\bhoàn\s*toàn\s*an\s*toàn\b': 'rất an toàn',
    r'\b100\s*%\s*an\s*toàn\b': 'rất an toàn', r'\ban\s*toàn\s*100\s*%\b': 'cực kỳ an toàn',
    r'(\b[a-zà-ỹ]+)\s+tuyệt\s*đối\b': r'cực kỳ \1',
    r'\bchữa\s*bệnh\b': 'hỗ trợ sức khỏe', r'\bchữa\s*khỏi\b': 'hỗ trợ cải thiện',
    r'\bđặc\s*trị\b': 'sản phẩm chuyên biệt', r'\bthuốc\s*đặc\s*trị\b': 'sản phẩm chuyên biệt',
    r'\btriệt\s*để\b': 'hiệu quả', r'\btrị\s*dứt\s*điểm\b': 'hỗ trợ cải thiện hiệu quả',
    r'\bdứt\s*điểm\b': 'cải thiện', r'\bthuốc\s*trị\b': 'sản phẩm hỗ trợ',
    r'\bđiều\s*trị\b': 'hỗ trợ quá trình', r'\bcam\s*kết\s*khỏi\b': 'giúp người dùng an tâm',
    r'\bbác\s*sĩ\s*khuyên\s*dùng\b': 'được nhiều người tin dùng',
    r'\btrắng\s*cấp\s*tốc\b': 'sáng khỏe tự nhiên', r'\bgiảm\s*béo\s*cấp\s*tốc\b': 'hỗ trợ vóc dáng thon gọn',
    r'\bxóa\s*sạch\s*nám\b': 'giúp mờ thâm sạm', r'\bkhỏi\s*hẳn\b': 'đỡ hẳn',
    r'\btrợ\s*giá\b': 'ưu đãi cực hời', r'\bphiên\s*live\b': 'đợt ưu đãi này', 
    r'\btrên\s*live\b': 'đợt này', r'\blivestream\b': 'chương trình ưu đãi'
}

SOUTHERN_TO_HANOI = {
    r'\blụa\s+premium\s+everyday\b': 'lụa cao cấp', r'\blụa\s+lustrous\s+satin(?:\s+silk)?\b': 'lụa cao cấp',
    r'\bpremium\s+everyday\b': 'cao cấp', r'\blustrous\s+satin(?:\s+silk)?\b': 'lụa cao cấp',
    r'\bmềm\s*rủ\b': 'mềm rũ', r'\bsiêu\s*rủ\b': 'siêu rũ', r'\bđộ\s*rủ\b': 'độ rũ', r'\brủ\s*xuống\b': 'rũ xuống',
    r'\báp\s*mã\b': 'nay giảm', r'\báp\s*voucher\b': 'nay giảm',
    r'\b1\s*trăm\s*(?:tư|tứ|bốn)?\s*mươi\b': 'một trăm bốn mươi', r'\b1\s*trăm\s*(?:tư|tứ)\b': 'một trăm bốn mươi',
    r'\bmột\s*trăm\s*(?:tư|tứ)\s*mươi\b': 'một trăm bốn mươi', r'\bmột\s*trăm\s*(?:tư|tứ)\b': 'một trăm bốn mươi',
    r'\btrăm\s*(?:tư|tứ)\s*mươi\b': 'trăm bốn mươi', r'\btrăm\s*(?:tư|tứ)\b': 'trăm bốn mươi',
    r'\b(?:tư|tứ)\s+mươi\b': 'bốn mươi', r'\bmười\s+(?:tư|tứ)\b': 'mười bốn', r'\bnghìn\s+(?:tư|tứ)\b': 'nghìn bốn trăm',
    r'\b1\s+trăm\b': 'một trăm', r'\b1\s+nghìn\b': 'một nghìn', r'\b1\s+triệu\b': 'một triệu',
    r'\b140\s*(?:k|nghìn|ngàn)\b': 'một trăm bốn mươi nghìn', r'\b140\b': 'một trăm bốn mươi',
    r'\b14\b': 'mười bốn', r'\b24\b': 'hai mươi bốn', r'\b34\b': 'ba mươi bốn',
    r'\b40\b': 'bốn mươi', r'\b44\b': 'bốn mươi bốn', r'\b4\b': 'bốn',
    r'\bmười\s+(?:tư|tứ)\b': 'mười bốn', r'\bhai\s+(?:tư|tứ)\b': 'hai mươi bốn',
    r'\bba\s+(?:tư|tứ)\b': 'ba mươi bốn', r'\b(?:tư|tứ)\s+mươi\b': 'bốn mươi',
    r'\b(\w+)\s+mươi\s+(?:tư|tứ)\b': r'\1 mươi bốn',
    r'\bnăm\s+(?:tư|tứ)\b': 'năm mươi bốn', r'\bsáu\s+(?:tư|tứ)\b': 'sáu mươi bốn',
    r'\bbảy\s+(?:tư|tứ)\b': 'bảy mươi bốn', r'\btám\s+(?:tư|tứ)\b': 'tám mươi bốn',
    r'\bchín\s+(?:tư|tứ)\b': 'chín mươi bốn', r'\bhai\s+(?:tư|tứ)\b': 'hai mươi bốn',
    r'\bba\s+(?:tư|tứ)\b': 'ba mươi bốn', r'\bhăm\s+(?:tư|tứ)\b': 'hai mươi bốn',
    r'\bba\s*rọi\b': 'ba chỉ', r'\bchiên\s*(?:giòn|phồng|ngập\s*dầu)?\b': 'rán giòn', r'\bchiên\b': 'rán',
    r'\báo\s*(?:đều|lớp\s*sốt|sốt)\b': 'ngấm đẫm sốt', r'\bcay\s*the\b': 'cay tê', r'\bthe\s*the\b': 'tê tê',
    r'\bsánh\s*dẻo\b': 'sền sệt', r'\bkẹo\s*lại\b': 'sệt lại', r'\bđậu\s*phộng\b': 'hạt lạc',
    r'\btrái\s*cây\s*dầm\b': 'hoa quả dầm', r'\btrái\s*cây\b': 'hoa quả', r'\brỗng\s*ruột\b': 'xốp tan',
    r'\bcực\s*kỳ\s*vừa\s*vặn\b': 'vừa miệng dã man', r'\bđã\s*cái\s*nư\b': 'đã miệng cực kỳ',
    r'\bxả\s*sơ(?:\s*qua)?\b': 'tráng qua', r'\bxả\s*nước\b': 'tráng nước',
    r'\brải\s+vào\b': 'xếp vào', r'\brải\b(?=\s+[a-zà-ỹ]+)': 'cho', r'\brửa\s*chén\b': 'rửa bát',
    r'\bnước\s*rửa\s*chén\b': 'nước rửa bát', r'\bly\s+nước\b': 'cốc nước', r'\bly\s+trà\b': 'cốc trà',
    r'\bly\s+đá\b': 'cốc đá', r'\bly\b(?=\s+(?:uống|nước|thủy tinh|nhựa))': 'cốc',
    r'\bmuỗng\b': 'thìa', r'\bbàn\s*ủi\b': 'bàn là', r'\bbao\s*rác\b': 'túi rác',
    r'\bchổi\s*lông\s*gà\b': 'chổi phất trần', r'\bkhít\s+tai\s+êm\s+ái\b': 'vừa khít mà êm ru',
    r'\bêm\s+ái\b': 'êm ru', r'\bvỏ\s*ngoài\b': 'bên ngoài', r'\bnét\s+căng\b': 'rõ mồn một',
    r'\bpin\s*trâu\b': 'pin dùng trâu bò', r'\bsạc\s*lẹ\b': 'sạc nhanh', r'\bthấm\s*lẹ\b': 'thấm nhanh',
    r'\bbết\s*rít\b': 'nhờn dính', r'\bxài\s*êm\b': 'dùng êm', r'\bmịn\s*mướt\b': 'căng mướt',
    r'\blột\s*mụn\b': 'hút mụn', r'\bbận\s+đồ\b': 'mặc đồ', r'\bbận\s+áo\b': 'mặc áo',
    r'\bbận\s+quần\b': 'mặc quần', r'\bbận\s+váy\b': 'mặc váy', r'\bbận\b(?=\s+[a-zà-ỹ]+)': 'mặc',
    r'\bđầm\b': 'váy', r'\báo\s*thun\b': 'áo phông', r'\bmang\s*giày\b': 'đi giày',
    r'\bmang\s*dép\b': 'đi dép', r'\bdây\s*nịt\b': 'thắt lưng', r'\bbóp\s*tiền\b': 'ví tiền',
    r'\bngàn\b': 'nghìn', r'\bxài\b': 'dùng', r'\bgiùm\b': 'hộ', r'\bdùm\b': 'hộ',
    r'\btui\b': 'tôi', r'\bhén\b': 'nhỉ', r'\bnghen\b': 'nhé', r'\bhen\b': 'nhé', r'\brùi\b': 'rồi',
    r'\bmần\b': 'làm', r'\bkiếng\b': 'kính', r'\bhổng\b': 'không', r'\bthiệt\b': 'thật',
    r'\bmắc\s+cỡ\b': 'ngại', r'\bhết\s+sẩy\b': 'tuyệt cú mèo', r'\brẻ\s+bèo\b': 'rẻ thế',
    r'\bquá\s+trời\b': 'rất nhiều', r'\bquá\s+chừng\b': 'rất nhiều', r'\bnè\b': 'này', r'\bnha\b': 'nhé',
    r'\bcưng\s+xỉu\b': 'yêu cực kỳ', r'\bcoi\b': 'xem', r'\bmua\s+liền\b': 'mua ngay'
}

# ==============================================================================
# 3. KẾT NỐI API & DB CƠ BẢN
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

# ==============================================================================
# 4. KHAI BÁO TOÀN BỘ HÀM TIỆN ÍCH, XỬ LÝ TEXT & JSON BÓC TÁCH SÂU
# ==============================================================================
def count_words(text: str) -> int: return len(re.findall(r'\b\w+\b', text)) if text else 0

def calculate_speech_duration(text: str, is_tiktok_shop: bool = True) -> float:
    words = count_words(text)
    commas, periods = text.count(',') + text.count(';'), text.count('.') + text.count('!') + text.count('?')
    return round((words / (4.8 if is_tiktok_shop else 4.0)) + (commas * (0.08 if is_tiktok_shop else 0.12)) + (periods * (0.12 if is_tiktok_shop else 0.20)), 1)

def is_valid_phone(phone): return phone.strip().isdigit() and phone.strip().startswith('0') and 9 <= len(phone.strip()) <= 11

def compress_image_bytes(uploaded_file, max_dimension=768, quality=75):
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        out_buffer = io.BytesIO()
        img.save(out_buffer, format="JPEG", quality=quality, optimize=True)
        return out_buffer.getvalue(), "image/jpeg"
    except Exception: return uploaded_file.getvalue(), (uploaded_file.type or "image/jpeg")

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
    raw = str(ca_data.get("what_and_unique", "")).strip() if isinstance(ca_data, dict) else ""
    if not raw and fallback_topic: raw = fallback_topic.strip()
    if not raw: return f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
    clean = re.sub(r'^(?:SẢN PHẨM LÀ GÌ\s*&?\s*(?:CÓ GÌ ĐẶC BIỆT)?|CHỦ ĐỀ|SẢN PHẨM)\s*:\s*', '', raw, flags=re.IGNORECASE).strip()
    if ":" in clean: prod_name = clean.split(":", 1)[0].strip()
    elif " - " in clean: prod_name = clean.split(" - ", 1)[0].strip()
    else: prod_name = clean
    prod_name = re.sub(r'[\[\]\*\"\'`]', '', prod_name).strip()
    if len(prod_name) > 55: prod_name = prod_name[:52].strip() + "..."
    return f"{prod_name} ({datetime.now().strftime('%d/%m')})" if prod_name else f"Chiến dịch ({datetime.now().strftime('%d/%m')})"

def normalize_hanoi_dialect(text: str) -> str:
    if not text: return ""
    cleaned = text
    for pattern, rep in SOUTHERN_TO_HANOI.items(): cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    return cleaned

def sanitize_policy_text(text: str) -> str:
    if not text: return ""
    cleaned = normalize_hanoi_dialect(text)
    for pattern, rep in POLICY_REPLACEMENTS.items(): cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bngàn\b', 'nghìn', cleaned, flags=re.IGNORECASE)
    return cleaned

def sanitize_third_party_ip(text: str) -> str:
    if not text: return ""
    cleaned = text
    for p in [r'\btiktok\s*(?:shop)?\b', r'\bshopee\b', r'\blazada\b', r'\bfacebook\b', r'\binstagram\b', r'\byoutube\b']: cleaned = re.sub(p, 'online store', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\blụa\s*titan\b', 'lustrous satin silk', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\btitan\s*silk\b', 'lustrous satin silk', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\btitan\b', 'lustrous satin', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:emoon|disney|marvel|spider-?man|spiderman|nike|adidas|gucci|chanel|dior|lv|louis\s+vuitton|zara|uniqlo|apple|samsung|xiaomi|dyson|philips|vaseline|lego|barbie)\b', 'premium everyday', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:celebrity|celebrities|public\s+figure|famous\s+person|famous\s+model|supermodel|star|idol|influencer|koc|kol|deepfake|real\s+person|real\s+human|authentic\s+person)\b', 'fictional everyday character', cleaned, flags=re.IGNORECASE)
    for pattern, safe_term in INTIMATE_SAFE_ENGLISH_LEXICON.items(): cleaned = re.sub(pattern, safe_term, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bwearing\s+wearing\b', 'wearing', cleaned, flags=re.IGNORECASE)
    return re.sub(r'\.\.+', '.', cleaned)

def number_to_vietnamese_words(n: int) -> str:
    if n == 0: return "không đồng"
    digits = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    def read_block_3(num_str, is_highest=False):
        num_str = num_str.zfill(3)
        h, t, u = int(num_str[0]), int(num_str[1]), int(num_str[2])
        res = []
        if not is_highest or h > 0: res.append(digits[h] + " trăm")
        if t == 0 and u == 0: pass
        elif t == 0 and u != 0:
            if not is_highest or h > 0: res.append("linh " + digits[u])
            else: res.append(digits[u])
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

def convert_to_soft_price_range(price_text: str, is_orig: bool = False, exact_raw_str: str = "") -> str:
    combined = f"{exact_raw_str} {price_text}".lower().strip()
    num_matches = [int(n.replace('.', '').replace(',', '')) for n in re.findall(r'\b\d{1,3}(?:[.,]\d{3})+\b', combined)]
    if num_matches:
        val = num_matches[0]
        if is_orig:
            if 100000 <= val <= 125000: return "gần một trăm hai mươi nghìn"
            elif val > 1000000: return f"gần {number_to_vietnamese_words(math.ceil(val / 1000000) * 1000000).replace(' đồng', '')}"
            elif val > 100000:
                ceil_hundred = math.ceil(val / 100000) * 100000
                if val % 100000 > 70000: return f"gần {number_to_vietnamese_words(ceil_hundred).replace(' đồng', '')}"
                return f"gần {number_to_vietnamese_words(math.ceil(val / 10000) * 10000).replace(' đồng', '')}"
            else: return f"gần {number_to_vietnamese_words(math.ceil(val / 10000) * 10000).replace(' đồng', '')}"
        else:
            if val < 50000: return "mấy chục nghìn"
            elif val < 100000: return f"hơn {number_to_vietnamese_words(math.floor(val / 10000) * 10000).replace(' đồng', '')}"
            elif val < 1000000: return f"hơn {number_to_vietnamese_words(math.floor(val / 100000) * 100000).replace(' đồng', '')}"
            else: return f"hơn {number_to_vietnamese_words(math.floor(val / 1000000) * 1000000).replace(' đồng', '')}"
    p_lower = re.sub(r'^(?:khoảng\s+|hơn\s+|tầm\s+|gần\s+)+', '', str(price_text).lower().strip()).strip()
    return f"gần {p_lower}" if is_orig else f"hơn {p_lower}"

def clean_and_normalize_voiceover(text: str) -> str:
    """Lưới lọc ngôn ngữ tự nhiên: Chống lặp từ, chống vấp thoại, dịch word-by-word và dọn dẹp ký tự thừa."""
    if not text: return ""
    cleaned = sanitize_policy_text(text)
    cleaned = extract_and_convert_prices_in_text(cleaned)
    for pattern, rep in [
        (r'\blụa\s+premium\s+everyday\b', 'lụa cao cấp'), (r'\bpremium\s+everyday\b', 'cao cấp'),
        (r'\bmềm\s*rủ\b', 'mềm rũ'), (r'\bsiêu\s*rủ\b', 'siêu rũ'), (r'\bđộ\s*rủ\b', 'độ rũ'), (r'\brủ\s*xuống\b', 'rũ xuống'),
        (r'\báp\s*mã\b', 'nay giảm'), (r'\báp\s*voucher\b', 'nay giảm'),
        (r'\b1\s*trăm\s*(?:tư|tứ|bốn)?\s*mươi\b', 'một trăm bốn mươi'), (r'\b1\s*trăm\s*(?:tư|tứ)\b', 'một trăm bốn mươi'),
        (r'\bmột\s*trăm\s*(?:tư|tứ)\s*mươi\b', 'một trăm bốn mươi'), (r'\bmột\s*trăm\s*(?:tư|tứ)\b', 'một trăm bốn mươi'),
        (r'\btrăm\s*(?:tư|tứ)\s*mươi\b', 'trăm bốn mươi'), (r'\btrăm\s*(?:tư|tứ)\b', 'trăm bốn mươi'),
        (r'\b1\s*trăm\b', 'một trăm'), (r'\b1\s*nghìn\b', 'một nghìn'), (r'\b1\s*triệu\b', 'một triệu'),
        (r'\b140\s*(?:k|nghìn|ngàn)\b', 'một trăm bốn mươi nghìn'), (r'\b140\b', 'một trăm bốn mươi'),
        (r'\b14\b', 'mười bốn'), (r'\b24\b', 'hai mươi bốn'), (r'\b34\b', 'ba mươi bốn'),
        (r'\b40\b', 'bốn mươi'), (r'\b44\b', 'bốn mươi bốn'), (r'\b4\b', 'bốn'),
        (r'\bmười\s+(?:tư|tứ)\b', 'mười bốn'), (r'\bhai\s+(?:tư|tứ)\b', 'hai mươi bốn'),
        (r'\bba\s+(?:tư|tứ)\b', 'ba mươi bốn'), (r'\b(?:tư|tứ)\s+mươi\b', 'bốn mươi'), (r'\b(\w+)\s+mươi\s+(?:tư|tứ)\b', r'\1 mươi bốn'),
        
        # 🌟 BỘ TỪ ĐIỂN CHỐNG DỊCH WORD-BY-WORD (SƯỢNG TRÂN)
        (r'\bform\s*hộp\s*đứng\s*form\b', 'form hộp cứng cáp'),
        (r'\bform\s*dáng\s*đứng\s*form\b', 'lên dáng chuẩn xác'),
        (r'\bluồn\s*da\b', 'phối da'),
        (r'\bchần\s*chỉ\s*ô\s*trám\b', 'chần trám'),
        (r'\bchần\s*chỉ\s*hình\s*thoi\b', 'chần trám tinh tế'),
        (r'\bđứng\s*form\b', 'giữ form'),
        (r'\bchuẩn\s*form\b', 'lên dáng chuẩn'),
        (r'\bdáng\s*mảnh\s*chuẩn\s*phong\s*cách\b', 'thiết kế chuẩn style'),
        (r'\bcực\s*nét\b', 'cực xịn'),
        (r'\bđang\s*giảm\s*giá\s*sâu\s*có\s*hạn\b', 'đang có deal cực hời'),
        (r'\bchốt\s*đơn\s*ngay\s*tay\b', 'chốt ngay kẻo lỡ'),
        (r'\bchốt\s*ngay\s*tay\b', 'chốt liền tay'),
        (r'\bliền\s*tay\b', 'ngay nhé'),
        (r'\bvừa\s*vặn\s*vừa\b', 'rất vừa vặn'),
        (r'\bsang\s*chảnh\s*sang\b', 'cực kỳ sang chảnh'),
        (r'\bđẹp\s*đẹp\b', 'tuyệt đẹp')
    ]: cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'[\(\)\[\]\{\}]', '', cleaned)
    cleaned = re.sub(r'\.{2,}', ',', cleaned)
    cleaned = re.sub(r'[-~*]', '', cleaned)
    
    # 🌟 LÕI NLP CHỐNG VẤP THOẠI (STUTTER/ECHO FILTER)
    cleaned = re.sub(r'\b(\w+(?:\s+\w+){1,3})\s+\1\b', r'\1', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(là|và|thì|mà|có|đang|đã|sẽ|giá|các|những|một|chiếc|cái|em|mình|tôi|bạn|mua|bấm|chốt|nhanh|này|kia|đó|đây|quá|rất|cực)\s+\1\b', r'\1', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\bgiá\s*đang\s*giá\b', 'giá đang', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bgiảm\s*giá\s*giảm\s*giá\b', 'giảm giá', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bđang\s*có\s*đang\s*có\b', 'đang có', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def clean_analysis_text(text) -> str:
    if not text: return ""
    if isinstance(text, (dict, list)): return format_analysis_field(text)
    pattern = r'^(?:SẢN PHẨM LÀ GÌ\s*&?\s*(?:CÓ GÌ ĐẶC BIỆT)?|SẢN PHẨM DÀNH CHO AI|TẠI SAO NÊN MUA|DÙNG Ở ĐÂU\s*&?\s*(?:TIỆN LỢI LÀ GÌ)?|CÁCH SỬ DỤNG|THAO TÁC.*|MỤC ĐÍCH|ĐỐI TƯỢNG|LÝ DO MUA)\s*:\s*'
    res = re.sub(pattern, '', str(text).strip(), flags=re.IGNORECASE).strip()
    return clean_and_normalize_voiceover(res)

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict): return "<br>".join([f"<span class='dna-label'>{str(k).replace('_', ' ').title()}:</span> <span class='dna-text'>{clean_analysis_text(v)}</span>" for k, v in field_val.items()])
    if isinstance(field_val, list): return "<br>".join([f"<div class='dna-bullet'>• <span class='dna-text'>{clean_analysis_text(item)}</span></div>" for item in field_val])
    val_str = clean_analysis_text(str(field_val))
    return "".join([f"<div class='dna-bullet'>• <span class='dna-text'>{line.strip()}</span></div>" for line in val_str.split('<br>') if line.strip()])

def format_product_name_bold(text: str) -> str:
    if not text: return ""
    clean = clean_analysis_text(text)
    if ":" in clean: parts = clean.split(":", 1); return f"<b style='color:#0f172a; font-weight:800; font-size:15px;'>{parts[0].strip()}</b>: {parts[1].strip()}"
    elif " - " in clean: parts = clean.split(" - ", 1); return f"<b style='color:#0f172a; font-weight:800; font-size:15px;'>{parts[0].strip()}</b> - {parts[1].strip()}"
    return f"<b style='color:#0f172a; font-weight:800; font-size:15px;'>{clean}</b>"

def format_ocr_prices(ca_data: dict) -> str:
    if not isinstance(ca_data, dict): return "<span style='color:#dc2626; font-weight:700;'>Chưa xác định</span>"
    exact_orig, exact_sale, det = ca_data.get('exact_original_price_ocr', ''), ca_data.get('exact_sale_price_ocr', ''), ca_data.get('detected_prices', '')
    if exact_orig and exact_sale: return f"<b style='color:#475569;'>Giá gốc:</b> <span style='color:#64748b; text-decoration:line-through; font-weight:700; font-size:14px;'>{clean_analysis_text(exact_orig)}</span> &nbsp;|&nbsp; <b style='color:#dc2626;'>Giá giảm:</b> <span style='color:#dc2626; font-weight:800; font-size:15.5px;'>{clean_analysis_text(exact_sale)}</span>"
    elif det and ("-" in det or "|" in det or "đ" in det.lower()): return f"<span style='color:#dc2626; font-weight:800; font-size:14.5px;'>{clean_analysis_text(det)}</span>"
    orig, sale = ca_data.get('original_price_spoken', ''), ca_data.get('sale_price_spoken', '')
    if orig and sale: return f"<b style='color:#475569;'>Giá gốc:</b> <span style='color:#64748b; text-decoration:line-through; font-weight:700;'>{clean_analysis_text(orig)}</span> &nbsp;|&nbsp; <b style='color:#dc2626;'>Giá giảm:</b> <span style='color:#dc2626; font-weight:800; font-size:15px;'>{clean_analysis_text(sale)}</span>"
    return "<span style='color:#dc2626; font-weight:700;'>Chưa xác định</span>"

def extract_scenes(parsed_data):
    if isinstance(parsed_data, list): return parsed_data
    if isinstance(parsed_data, dict):
        for key in ["scenes", "script", "outlines", "video_scenes", "data"]:
            if key in parsed_data and isinstance(parsed_data[key], list):
                return parsed_data[key]
        for k, v in parsed_data.items():
            if isinstance(v, dict):
                for key in ["scenes", "script", "outlines", "video_scenes"]:
                    if key in v and isinstance(v[key], list):
                        return v[key]
    return []

# ==============================================================================
# 5. HỆ THỐNG ĐẠO DIỄN: GÓC MÁY, NHẬN DIỆN ĐA NGÀNH HÀNG & VẬT LÝ ĐỘNG LỰC
# ==============================================================================
def detect_food(text_to_check: str) -> bool:
    if not text_to_check: return False
    keywords = ["đồ ăn", "thức ăn", "bánh", "kẹo", "nước", "sữa", "trà", "cafe", "món ăn", "thực phẩm", "food", "snack", "drink", "cake", "noodle", "trái cây", "thịt", "hải sản", "cơm", "bún", "phở"]
    return any(k in text_to_check.lower() for k in keywords)

def detect_cosmetics(text_to_check: str) -> bool:
    if not text_to_check: return False
    keywords = ["kem dưỡng", "son", "môi", "serum", "phấn", "tẩy trang", "mặt nạ", "sữa rửa mặt", "kem chống nắng", "toner", "lotion", "cream", "lipstick", "lip", "makeup", "skincare", "cosmetic", "khử mùi", "nách", "sáp", "nẻ", "vaseline", "balm", "má", "blush", "cheek"]
    return any(k in text_to_check.lower() for k in keywords)

def detect_mom_baby(text_to_check: str) -> bool:
    if not text_to_check: return False
    keywords = ["bỉm", "tã", "sữa bột", "đồ chơi trẻ em", "bình sữa", "ti giả", "xe đẩy", "nôi", "mẹ và bé", "diaper", "baby", "formula", "pacifier", "stroller"]
    return any(k in text_to_check.lower() for k in keywords)

def detect_mom_baby_hard_props(text_to_check: str) -> bool:
    if not text_to_check: return False
    keywords = ["bình sữa", "xe đẩy", "đồ chơi", "nôi", "bottle", "stroller", "toy", "crib"]
    return any(k in text_to_check.lower() for k in keywords)

def detect_medicine(text_to_check: str) -> bool:
    if not text_to_check: return False
    keywords = ["viên uống", "thuốc", "thực phẩm chức năng", "vitamin", "collagen", "giảm cân", "tpcn", "pill", "capsule", "supplement", "medicine"]
    return any(k in text_to_check.lower() for k in keywords)

def detect_strict_rigid_appliance(text_to_check: str) -> bool:
    if not text_to_check: return False
    appliance_keywords = [
        "cốc", "ly", "bình", "tumbler", "cup", "bottle", "mug",
        "giỏ", "rổ", "kệ", "hộp", "thùng", "tủ", "móc", "chậu", "cây lau", "bàn chải", "máy giặt", "túi đựng", 
        "khay", "nồi", "chảo", "dao", "thớt", "máy xay", "bếp", "ghế", "bàn", "đèn", "quạt", 
        "máy sấy", "bàn là", "bàn ủi", "basket", "rack", "organizer", "bin", "box", "hamper", "shelf", "holder", 
        "pan", "pot", "tool", "vacuum", "dryer", "blower", "hút bụi",
        "tai nghe", "headphone", "earbud", "earphone", "bluetooth", "điện thoại", "phone", "loa", "speaker", 
        "sạc", "chuột", "bàn phím", "mic", "túi xách", "túi", "balo", "ví", "power bank", "sạc dự phòng"
    ]
    return any(k in text_to_check.lower() for k in appliance_keywords)

def detect_single_tube_skirt(text_to_check: str) -> bool:
    if not text_to_check: return False
    return any(k in text_to_check.lower() for k in ["1 ống", "một ống", "quần váy", "váy 1 ống", "dạng váy", "quần giả váy", "single tube", "skirt-pants", "culottes skirt", "unsplit skirt"])

def enforce_single_tube_skirt_syntax(text_en: str) -> str:
    if not text_en: return ""
    cleaned = text_en
    patterns = [r'\bwide-?leg\s+(?:silk\s+)?(?:skirt-?pants|pants|trousers)\b', r'\bskirt-?pants\b', r'\bsilk\s+(?:pants|trousers)\b', r'\bflowing\s+(?:pants|trousers)\b', r'\bloose\s+(?:pants|trousers)\b', r'\bpants\b', r'\btrousers\b']
    for pat in patterns: cleaned = re.sub(pat, 'full-length A-line maxi skirt (single unified unsplit skirt tube, zero leg division)', cleaned, flags=re.IGNORECASE)
    return cleaned

def translate_and_lock_color_en(color_vi: str, ai_color_en: str = "") -> str:
    c = f"{color_vi} {ai_color_en}".lower().strip()
    if any(k in c for k in ["họa tiết", "hoa", "sọc", "pattern", "floral", "plaid", "stripe", "checkered", "print", "gradient"]):
        return f"exact reference-matching pattern and colors ({ai_color_en})"
    if ai_color_en and len(ai_color_en.strip()) > 2:
        return f"exact reference-matching {ai_color_en.strip()}"
    return "exact reference-matching color and pattern"

def sanitize_destructive_motion_verbs(action_text: str, is_fashion: bool = False, is_food: bool = False) -> str:
    if not action_text: return ""
    cleaned = action_text
    if not is_fashion and not is_food:
        destructive_patterns = [
            (r'\bunfolding\b', 'holding steadily'), (r'\bfolding\b', 'holding securely'), 
            (r'\bcollapsing\b', 'presenting up close'), (r'\bflexing\b', 'pressing fingers gently on'), 
            (r'\bbending\b', 'tilting slightly'), (r'\btwisting\b', 'holding firmly'), 
            (r'\btransforming\b', 'showcasing'), (r'\bdeforming\b', 'presenting'), 
            (r'\bstretching\b', 'tracing fingers along'), (r'\bsqueezing\b', 'gripping firmly'), 
            (r'\bopening\s+and\s+closing\b', 'displaying clearly'),
            (r'\bdropping\b', 'holding securely'), (r'\bfalling\b', 'staying firmly in hand'),
            (r'\bthrowing\b', 'holding firmly'), (r'\btossing\b', 'presenting carefully'),
            (r'\bletting\s+go\b', 'holding firmly'),
            (r'\b(?:turning|swaying|spinning|walking|stepping|dancing|moving around|tracking)\b', 'standing still')
        ]
        for pat, rep in destructive_patterns: cleaned = re.sub(pat, rep, cleaned, flags=re.IGNORECASE)
    return cleaned

def extract_environmental_lighting_and_weather(vo_text: str, setting_text: str = ""):
    combined_text = f"{vo_text} {setting_text}".lower()
    outdoor_keywords = ["ngoài trời", "sân vườn", "đường phố", "công viên", "vỉa hè", "ban công", "sân thượng", "dã ngoại", "bãi biển", "outdoor", "street", "garden", "park", "balcony"]
    is_indoor = not any(k in combined_text for k in outdoor_keywords)
    
    if any(k in combined_text for k in ["đêm", "tối", "khuya", "tắt đèn", "mất điện", "đi ngủ", "night", "dark"]): 
        return "dimly lit, cinematic low light, dark ambience", "quiet nighttime ambience (no reverb)"
    elif any(k in combined_text for k in ["mưa", "ẩm ướt", "nồm"]): 
        return ("rain droplets on window, soft overcast indoor lighting" if is_indoor else "light rain, wet ground, overcast sky"), "subtle rain ambience (no reverb)"
    elif any(k in combined_text for k in ["nắng", "trưa hè"]): 
        return ("warm sunbeams through window" if is_indoor else "sunny daylight, golden sunbeams"), "subtle breeze ambience (no reverb)"
    elif any(k in combined_text for k in ["sáng sớm", "buổi sáng", "bình minh"]): 
        return "fresh morning sunlight", "subtle morning ambience (no reverb)"
    elif any(k in combined_text for k in ["hoàng hôn", "chiều tà", "buổi chiều"]): 
        return "warm amber sunset glow", "subtle evening ambience (no reverb)"
        
    return ("clean natural daylight with soft warm fill light" if is_indoor else "bright commercial daylight"), ""

def sanitize_veo3_prompt(prompt_text: str) -> str:
    if not prompt_text: return ""
    p = re.sub(r'\bgesturing\s+(?:warmly\s+)?(?:toward\s+)?corner\b', 'sharing recommendations with an open-palm gesture', prompt_text, flags=re.IGNORECASE)
    return sanitize_third_party_ip(re.sub(r'\bpointing\s+(?:downward\s+)?(?:to\s+)?(?:corner|cart)\b', 'speaking with welcoming open hands', p, flags=re.IGNORECASE))

def generate_char_rules_string(profiles):
    if not profiles: return "100% Vietnamese persona, natural black hair, consistent outfit across 3 scenes."
    return " | ".join([f"Actor {p['id']} ({p['role']}): 100% Vietnamese persona, consistent look across scenes" for p in profiles])

def get_demographics_description(char_profiles, ai_persona_en="", ai_body_and_hair_en="", ai_voice_prompt="", is_mom_baby=False):
    user_roles = [str(p.get("role", "")).strip() for p in (char_profiles or []) if str(p.get("role", "")).strip()]
    asian_features = "authentic Vietnamese Southeast Asian facial features, natural jet-black hair"
    
    if is_mom_baby: 
        return "female", f"A caring Vietnamese mother ({asian_features}) safely holding/interacting with her baby", "Native Hanoi Vietnamese warm young adult female voice"
    
    if user_roles:
        role_lower = user_roles[0].lower()
        if any(k in role_lower for k in ["trẻ em", "bé", "kid", "child", "boy", "girl"]):
            gender = "male" if any(k in role_lower for k in ["trai", "boy"]) else "female"
            return gender, f"Vietnamese child, {user_roles[0]}, {asian_features}", f"Native Hanoi Vietnamese child {gender} voice"
        elif any(k in role_lower for k in ["ông", "già", "bác già", "bà", "senior", "old"]):
            gender = "male" if any(k in role_lower for k in ["ông", "nam", "bác trai"]) else "female"
            return gender, f"Vietnamese senior, {user_roles[0]}, {asian_features}", f"Native Hanoi Vietnamese senior {gender} voice"
        elif any(k in role_lower for k in ["bố", "ba", "chồng", "nam", "anh", "trai", "man", "male"]):
            return "male", f"Vietnamese man, {user_roles[0]}, {asian_features}", "Native Hanoi Vietnamese adult male voice"
        else:
            return "female", f"Vietnamese woman, {user_roles[0]}, {asian_features}", "Native Hanoi Vietnamese adult female voice"
            
    ai_p_lower = ai_persona_en.lower()
    gender = "male" if any(k in ai_p_lower for k in ["man", "male", "boy", "father", "gentleman", "anh", "nam"]) else "female"
    clean_p = re.sub(r'\b(?:authentic|real|famous|celebrity|popular|influencer|koc|model|fictional|everyday|western|caucasian)\b', '', ai_persona_en, flags=re.IGNORECASE).strip()
    if "vietnamese" not in clean_p.lower(): clean_p = f"Vietnamese {clean_p}"
    physique = f", {ai_body_and_hair_en}" if ai_body_and_hair_en else f", {asian_features}"
    voice = ai_voice_prompt if ai_voice_prompt else f"Native Hanoi Vietnamese adult {gender} voice"
    
    return gender, f"{clean_p}{physique}", voice

def is_pas_storytelling_strategy(strategy_str: str, title_str: str = "") -> bool:
    return any(k in f"{strategy_str} {title_str}".lower() for k in ["nỗi đau", "pas", "đời sống", "lifestyle", "pov", "tình huống", "hài hước", "đời thường"])

def detect_intimate_apparel(text_to_check: str) -> str:
    if not text_to_check: return "normal"
    t = text_to_check.lower()
    if any(k in t for k in ["áo lót", "quần lót", "đồ lót", "nội y", "áo ngực", "su đúc", "quần chip", "quần sịp", "bikini", "đồ bơi", "váy ngủ", "đồ ngủ", "miếng dán ngực", "dung dịch vệ sinh", "bra", "panties", "underwear", "lingerie", "briefs", "thong"]): return "underwear_bra"
    if any(k in t for k in ["áo 2 dây", "áo hai dây", "áo ống", "áo quây", "camisole", "spaghetti strap"]): return "camisole"
    return "normal"

def detect_wearable_fashion(text_to_check: str) -> bool:
    if not text_to_check: return False
    t = text_to_check.lower()
    if any(k in t for k in ["giỏ", "kệ", "hộp", "thùng", "tủ", "móc", "chậu", "cây lau", "bàn chải", "máy giặt", "túi đựng", "rổ", "khay", "basket", "rack", "organizer", "bin", "box", "hamper"]): return False
    fashion_keywords = ["áo", "quần", "váy", "đầm", "hoodie", "sweater", "blazer", "jacket", "shirt", "pants", "jeans", "shorts", "t-shirt", "set đồ", "bộ đồ", "cardigan", "polo", "chân váy", "pijama", "tất", "vớ", "socks", "tights", "stocking"]
    return any(k in t for k in fashion_keywords)

def detect_footwear_or_accessory(text_to_check: str) -> bool:
    if not text_to_check: return False
    t = text_to_check.lower()
    if any(k in t for k in ["giỏ", "rổ", "thùng", "hộp", "kệ", "basket", "hamper", "organizer", "bin"]): return False
    return any(k in t for k in [
        "giày", "dép", "sneaker", "boot", "sandal", "heel", "túi xách", "ví", "balo", 
        "mũ", "nón", "kính", "thắt lưng", "đồng hồ", "trang sức", "dây chuyền", "nhẫn", "khuyên tai", 
        "shoe", "handbag", "backpack", "wallet", "watch", "glasses", "tất", "vớ", "socks"
    ])

def detect_long_handle_tool(text_to_check: str) -> bool:
    if not text_to_check: return False
    return any(k in text_to_check.lower() for k in ["cây lau", "chổi", "cây chà", "bàn chải cán dài", "mop", "broom", "long-handled", "long handle"])

def get_cosmetic_target(product_name, check_str):
    p_cos = f"{product_name} {check_str}".lower()
    if any(k in p_cos for k in ["má", "blush", "cheek"]):
        return "cheeks", "instantly leaving a soft, natural, and radiant flush of color smoothly blended onto the skin"
    elif any(k in p_cos for k in ["môi", "lip", "son"]):
        if any(k in p_cos for k in ["dưỡng", "nẻ", "sáp", "balm", "chapstick", "mask", "vaseline", "treatment"]):
            return "lips", "instantly leaving a clear, highly glossy, deeply hydrated and plump finish without altering the natural lip color"
        else:
            return "lips", "instantly leaving a highly precise, rich and vibrant colored stroke exactly where applied"
    elif any(k in p_cos for k in ["tóc", "gội", "xả", "hair", "shampoo", "conditioner"]): return "hair", "instantly leaving the hair visibly smooth, silky and shiny"
    elif any(k in p_cos for k in ["nách", "khử mùi", "armpit", "deodorant"]): return "armpit", "instantly absorbing into the skin"
    elif any(k in p_cos for k in ["tay", "body", "cơ thể", "hand", "lotion", "toàn thân", "nail", "móng"]): return "hands/arms/body", "instantly absorbing and leaving a glowing, hydrated finish"
    else: return "facial skin", "instantly absorbing and disappearing, leaving a highly glossy, hydrated, glowing glass-skin finish"

def get_product_centric_camera_shot(scene_idx: int, is_fashion: bool, is_footwear_acc: bool, is_pas_scene1: bool, clean_prod_en: str, is_strict_appliance: bool, is_long_handle: bool, is_food: bool, is_cosmetics: bool, is_mom_baby: bool, is_medicine: bool, intimate_type: str, check_str: str = "") -> str:
    if is_pas_scene1 and not is_fashion: return "Vertical 9:16 stable dynamic shot framing the character and the specific problem"
    
    if intimate_type != "normal":
        if scene_idx == 0: return f"Vertical 9:16 stable medium shot, character in a silk robe holding {clean_prod_en}"
        elif scene_idx == 1: return f"Vertical 9:16 stable tight macro close-up focused strictly on hands interacting with {clean_prod_en}"
        elif scene_idx == 2: return f"Vertical 9:16 stable macro close-up on the fabric details of {clean_prod_en}"
        else: return f"Vertical 9:16 stable balanced shot focusing on hands holding {clean_prod_en}"

    if is_footwear_acc and any(k in clean_prod_en.lower() for k in ["sock", "shoe", "boot", "sandal", "sneaker", "tights", "footwear", "tất", "vớ"]):
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

def get_universal_physics_rules(product_name: str, vo_text: str = "", is_fashion: bool = False, is_strict_appliance: bool = False, is_long_handle: bool = False, is_food: bool = False, is_cosmetics: bool = False, is_mom_baby: bool = False, is_medicine: bool = False, is_mom_baby_hard: bool = False, intimate_type: str = "normal", is_aline_skirt: bool = False) -> str:
    p = f"{product_name} {vo_text}".lower()
    
    if intimate_type != "normal":
        return "Soft breathable fabric physics: hands strictly stretching and releasing the elastic material smoothly, showing its seamless texture and high resilience. strictly hand interaction, NEVER worn on the body directly."
    
    elif is_food: return "Mouth-watering visual physics; showing steam rising, juicy texture, melting, or smooth pulling/stretching if applicable. Presenter stands completely still; natural hand interaction only, NEVER dropping."
    elif is_cosmetics: 
        target_part, effect = get_cosmetic_target(product_name, vo_text)
        return f"Cosmetic physics: applying directly on the {target_part.upper()} ONLY (NEVER on other body parts). {effect}. Delicate hand interaction."
    elif is_mom_baby: 
        if is_mom_baby_hard: return "STRICT REFERENCE TRACKING for the baby product. 100% rigid non-deforming geometry, true-to-life scale. Safe and gentle interaction, holding securely, NEVER dropping. Hands kept strictly away from face."
        return "Ultra-soft fabric/material texture; showing gentle elasticity, high liquid absorption, or completely safe smooth surfaces. Holding securely. Hands kept strictly away from face."
    elif is_medicine: return "Clean, safe, solid capsule/pill geometry or smooth powder dissolving perfectly in clear water. Holding securely."
    
    elif is_fashion:
        if is_aline_skirt:
            return "Structured garment physics: the A-line skirt holds its firm, clean geometric shape without billowing, flaring, or pleating in motion. Subject models the garment WORN ON BODY. Fabric testing is done strictly WHILE WEARING IT. Hands kept strictly away from face."
        return "Natural fabric drape in motion; subject models the garment WORN ON BODY. Fabric testing (stretching/touching) is done strictly WHILE WEARING IT. Zero duplicate items in hands. Hands kept strictly away from face."
    
    elif any(k in p for k in ["hút bụi", "vacuum", "máy sấy", "máy thổi"]): return "CAMERA FOCUS LOCKED ON DEVICE HEAD/NOZZLE: 100% rigid non-deforming body lock, keeping its EXACT original nozzle/attachment (zero morphing to long sticks). The nozzle glides swiftly and firmly, visibly removing dirt or blowing air in real-time. Holding securely, never dropping. Hands kept strictly away from face."
    elif is_long_handle or any(k in p for k in ["chà sàn", "lau nhà", "bàn chải", "cọ", "tẩy", "rửa", "mop", "brush", "scrubber", "cleaner"]): return "Rigid tool body lock, true-to-life scale (NO giant sizes); product glides/scrubs rapidly and decisively across the floor/surface, visibly removing dirt/stains on the spot. Gripping firmly, never dropping. Hands kept strictly away from face."
    
    elif is_strict_appliance: return "STRICT REFERENCE TRACKING: The appliance maintains 100% exact shape, true-to-life scale, proportions, and surface details identical to the reference image. Zero morphing, zero hallucinated parts. The product stays completely rigid while presenter stands perfectly still; hands hold the product naturally (using its actual handle/strap if any), fast decisive interaction, NEVER dropping. CRITICAL: Product MUST remain at CHEST LEVEL or resting on a table. STRICTLY FORBIDDEN to lift product to face, cheek, or ear."
    else: return "CAMERA FOCUS LOCKED ON PRODUCT IN FOREGROUND: 100% rigid non-deforming 3D geometry, true-to-life scale (zero morphing); presenter stands completely still (zero body rotation); hands hold the product firmly at chest level (NEVER near the face) and trace surface decisively, never dropping. STRICTLY FORBIDDEN to lift product to face, cheek, or ear."

def get_action_templates_by_industry(clean_prod_en: str, check_str: str, is_fashion_wearable: bool, is_strict_appliance: bool, is_long_handle: bool, is_food: bool, is_cosmetics: bool, is_mom_baby: bool, is_medicine: bool, intimate_type: str = "normal"):
    p = f"{clean_prod_en} {check_str}".lower()
    
    if intimate_type != "normal":
        return (
            f"standing elegantly in a silk robe, holding {clean_prod_en} securely in hands to show its premium texture",
            f"close-up on hands gently stretching the highly elastic fabric of {clean_prod_en} to demonstrate extreme resilience",
            f"macro shot of hands touching the breathable seamless surface of {clean_prod_en}",
            f"holding {clean_prod_en} neatly folded in hands with a warm welcoming smile"
        )

    elif any(k in p for k in ["sock", "shoe", "boot", "sandal", "sneaker", "tights", "tất", "vớ", "giày", "dép"]):
        return ("stepping forward stylishly showcasing the footwear/socks on feet", "holding the product securely in hands, tracing fingers along the seams and material to show premium quality", "holding the product securely in hands, bending the sole or stretching the material firmly to demonstrate extreme flexibility and durability", "posing confidently with focus on the legs/feet")

    if is_food: return (f"holding {clean_prod_en} securely while standing completely still and presenting it deliciously", f"taking a satisfying bite or showing the inside texture of {clean_prod_en}", f"pouring, dipping, or stretching {clean_prod_en} to show its mouth-watering details", f"holding {clean_prod_en} securely with a happy, satisfied expression")
    elif is_cosmetics:
        target_part, effect = get_cosmetic_target(clean_prod_en, check_str)
        return (
            f"elegantly holding {clean_prod_en} securely near the {target_part}",
            f"applying {clean_prod_en} DIRECTLY onto the {target_part} (strictly targeting the {target_part}), physically showing a clear visual transformation ({effect})",
            f"gently blending {clean_prod_en} directly into the {target_part}, the product texture visibly absorbs/changes to emphasize the stunning transformed finish",
            f"holding {clean_prod_en} securely with a radiant smile, showcasing the perfectly treated {target_part}"
        )
    elif is_mom_baby: return (f"caring mother holding {clean_prod_en} securely next to her baby", f"gently touching or interacting with {clean_prod_en} to show its features", f"demonstrating the safe use of {clean_prod_en} with the baby", f"holding {clean_prod_en} securely with a caring smile next to the baby")
    elif is_medicine: return (f"holding {clean_prod_en} securely in hand", f"showing {clean_prod_en} up close next to a clear glass of water", f"dropping or demonstrating the use of {clean_prod_en}", f"holding {clean_prod_en} securely with a healthy, confident smile")

    elif is_fashion_wearable: return (
        "stepping forward confidently, modeling the outfit", 
        "close-up on hands touching and smoothing the fabric of the outfit worn on body to show its premium texture", 
        "close-up on hands gently stretching the fabric of the outfit worn on body to demonstrate elasticity and breathability", 
        "posing elegantly (hands strictly kept away from face) and gesturing warmly while modeling the outfit"
    )
    
    elif any(k in p for k in ["hút bụi", "vacuum"]): return (f"holding {clean_prod_en} with its EXACT original nozzle firmly, maintaining realistic scale", f"positioning the original nozzle of {clean_prod_en} on the surface to show its rigid structure", f"gliding {clean_prod_en} rapidly in focus using its original attachment, visibly sucking dirt straight into the dustbin", f"holding {clean_prod_en} securely with a warm open-palm gesture")
    elif is_long_handle: return (f"holding the exact reference-matching {clean_prod_en} firmly", f"demonstrating the exact reference-matching {clean_prod_en} swiftly on the floor without any added details or scale distortion", f"scrubbing/gliding the {clean_prod_en} rapidly and decisively across the floor keeping 100% fidelity and true realistic scale", f"holding {clean_prod_en} firmly with a confident gesture")
    elif is_strict_appliance: return (f"standing completely still while holding {clean_prod_en} firmly at realistic scale", f"presenting {clean_prod_en} swiftly", f"demonstrating {clean_prod_en} with fast, decisive hand interaction while keeping 100% fidelity. STRICTLY NO lifting to face/ear", f"holding {clean_prod_en} firmly with a confident open-palm gesture")
    
    else: return (
        f"standing perfectly still holding the rigid {clean_prod_en} firmly at CHEST LEVEL. STRICTLY NO lifting to face/ear", 
        f"hands interacting directly with {clean_prod_en} strictly at chest or waist level, keeping it far away from the head", 
        f"demonstrating {clean_prod_en} with fast decisive hand movements at chest level while preserving 100% rigid geometry. NEVER touch face", 
        f"holding {clean_prod_en} securely at chest level with a confident open-palm gesture. Product remains strictly below shoulder level"
    )

def build_multi_industry_stylist_rules(product_en: str, hero_color: str, setting_vi: str, gender: str, intimate_type: str, is_fashion: bool, raw_vi_info: str = "", is_food: bool = False, is_cosmetics: bool = False, is_mom_baby: bool = False, is_medicine: bool = False) -> str:
    s_lower, h_lower = f"{product_en} {setting_vi} {raw_vi_info}".lower(), hero_color.lower()
    setting_lower = setting_vi.lower()
    
    is_bedroom = any(k in setting_lower for k in ["phòng ngủ", "giường", "bedroom", "pijama", "đồ ngủ", "ngủ", "thức dậy"])
    is_bathroom = any(k in setting_lower for k in ["phòng tắm", "nhà vệ sinh", "toilet", "bathroom", "nhà tắm"])
    is_kitchen = any(k in setting_lower for k in ["bếp", "nấu", "kitchen", "cooking", "ăn"])
    is_chore = any(k in setting_lower for k in ["dọn dẹp", "lau nhà", "vệ sinh", "chà sàn", "phòng giặt", "máy giặt", "laundry", "góc giặt", "ban công"])
    is_living_room = any(k in setting_lower for k in ["phòng khách", "sofa", "nhà", "ở nhà", "living room", "home"]) and not (is_bedroom or is_kitchen or is_chore or is_bathroom)
    
    is_office = any(k in setting_lower for k in ["văn phòng", "công sở", "công ty", "họp", "office", "workplace"])
    is_gym_sport = any(k in setting_lower for k in ["thể thao", "chạy bộ", "gym", "tập luyện", "yoga", "workout", "sport"])
    is_event_party = any(k in setting_lower for k in ["tiệc", "sự kiện", "đám cưới", "party", "event"])
    is_beach_resort = any(k in setting_lower for k in ["biển", "resort", "du lịch", "beach", "vacation"])
    
    is_single_skirt = detect_single_tube_skirt(s_lower)
    is_evening_fashion = any(k in s_lower for k in ["váy", "đầm", "dự tiệc", "đi tiệc", "công sở", "thanh lịch", "áo dài", "dress", "gown"])
    
    if intimate_type == "underwear_bra":
        vibe = "Intimate Apparel Review (Wearing a premium soft silk robe, cozy bathrobe, or comfortable loose homewear, UNTUCKED, barefoot or fluffy slippers)"
    elif intimate_type == "camisole":
        vibe = "Casual Loungewear (Wearing a stylish oversized cardigan layered over the product, comfy shorts, UNTUCKED, barefoot or indoor slippers)"
    
    elif is_fashion:
        if any(k in s_lower for k in ["chân váy", "quần", "skirt", "pants", "jeans", "shorts"]):
            if is_beach_resort: vibe = "Beach/Resort (Wearing the product perfectly fitted on the lower body. Top: fitted sleeveless silk camisole or halter top, fully TUCKED IN. Footwear: strappy flat beach sandals)"
            elif is_office: vibe = "Professional Office (Wearing the product perfectly fitted on the lower body. Top: tailored long-sleeve silk blouse, fully TUCKED IN. Footwear: pointed-toe leather high heels)"
            else: vibe = "Trendy Streetwear (Wearing the product perfectly fitted on the lower body. Top: fitted short-sleeve knit top or chic cropped tee. Footwear: clean minimalist white sneakers or leather loafers)"
        elif any(k in s_lower for k in ["áo", "shirt", "top", "jacket", "sweater", "hoodie"]):
            if is_beach_resort: vibe = "Beach/Resort (Wearing the product perfectly fitted on the upper body. Bottom: breezy wide-leg linen pants or denim shorts. Footwear: woven sandals)"
            elif is_office: vibe = "Professional Office (Wearing the product perfectly fitted on the upper body. Bottom: tailored wide-leg trousers or straight pencil skirt. Footwear: pointed-toe heels)"
            else: vibe = "Trendy Streetwear (Wearing the product perfectly fitted on the upper body. Bottom: fashionable high-waisted straight jeans or pleated midi skirt. Footwear: clean white sneakers)"
        else:
            if is_event_party or is_evening_fashion: vibe = "Elegant Evening (Wearing the full product perfectly fitted. Top layer: structured blazer draped over shoulders. Footwear: stiletto heels)"
            elif is_beach_resort: vibe = "Beach/Resort (Wearing the full product perfectly fitted, wide-brim woven hat, woven beach sandals)"
            else: vibe = "High-Fashion Lookbook (Wearing the full product perfectly fitted, elegant makeup, premium matching footwear)"
            
    elif is_bedroom:
        vibe = "Cozy Bedroom (Soft silk/cotton sleepwear or loose pajamas, UNTUCKED, barefoot or fluffy indoor slippers)"
    elif is_bathroom:
        vibe = "Bathroom/Washroom (Bathrobe or comfortable home wear, UNTUCKED, barefoot or plastic anti-slip slippers)"
    elif is_kitchen or is_chore:
        vibe = "Active Home/Chores (Neat comfy loungewear, rolled-up sleeves, UNTUCKED, casual indoor slippers)"
    elif is_living_room:
        vibe = "Relaxed Living Room (Smart-casual loungewear or comfy chic sweater/t-shirt, UNTUCKED, minimalist indoor slippers)"
    elif is_gym_sport:
        vibe = "Athletic/Gym (Form-fitting activewear, leggings/joggers, UNTUCKED, athletic running shoes)"
    elif is_office:
        if gender == "female": vibe = "Professional Office (Elegant blouse, tailored trousers or pencil skirt, neatly TUCKED IN, pointed-toe heels or smart loafers)"
        else: vibe = "Professional Office (Crisp button-down shirt, tailored trousers, neatly TUCKED IN, leather dress shoes or smart loafers)"
    elif is_event_party or is_evening_fashion:
        if gender == "female": vibe = "Elegant Evening (Glamorous evening dress or chic formal outfit, strappy heeled sandals or stilettos)"
        else: vibe = "Elegant Evening (Tailored suit or sharp blazer, polished dress shoes)"
    else: 
        if gender == "female": vibe = "Trendy Streetwear/Cafe (Stylish layered outfit, fashionable jeans or skirt, UNTUCKED or French tuck, clean white sneakers or ankle boots)"
        else: vibe = "Trendy Streetwear/Cafe (Smart-casual layered outfit, overshirt or stylish tee, clean denim or chinos, UNTUCKED, minimalist white sneakers)"

    contrast_note = "Trang phục màu Beige/Mocha/Xanh pastel làm nổi bật SP trắng/sáng" if any(k in h_lower for k in ["trắng", "white", "kem"]) else "Trang phục thanh lịch, màu sắc nhã nhặn tôn lên SP"
    if is_cosmetics: contrast_note = "Trang điểm tinh tế, tóc tai gọn gàng, trang phục tôn da (clean elegant makeup, neat hair)"
    elif is_mom_baby: contrast_note = "Trang phục màu pastel ấm áp, chất liệu thân thiện (cozy soft pastel clothes)"
    elif is_medicine: contrast_note = "Trang phục tạo cảm giác chuyên gia an toàn, uy tín (smart, neat)"
        
    skirt_rule = " | ĐẶC BIỆT: Phần dưới là VÁY 1 ỐNG RỘNG (full-length A-line maxi skirt, single unified unsplit skirt tube, zero leg division - CẤM viết từ pants/trousers)!" if is_single_skirt else ""
    return f"HOLISTIC STYLIST LOCK: Fashion Vibe must be [{vibe}]. {contrast_note}{skirt_rule}"

# ==============================================================================
# 11. TỐI ƯU HÓA PROMPT LITE CHẾ ĐỘ TIẾT KIỆM TOKEN
# ==============================================================================
def create_scene_details(target_id, mode, style="Điện Ảnh Chân Thực"):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if str(sc.get("id")) == str(target_id)), None)
    if not outline: raise Exception(f"Không tìm thấy kịch bản #{target_id} trong danh sách dự án.")
    
    char_profiles = outline.get("character_profiles", st.session_state.get("character_profiles", []))
    char_rules = generate_char_rules_string(char_profiles)
    current_active_mode = mode or st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    is_tiktok_shop = ("Viral" not in current_active_mode)
    is_viral = ("Viral" in current_active_mode)

    fixed_title = outline.get('title', 'Kịch bản chi tiết')
    fixed_setting_base = outline.get('setting', 'Không gian thực tế phù hợp')
    full_vo_script = outline.get('full_voiceover_script', outline.get('hook', ''))
    
    user_custom_note = outline.get("custom_note") or st.session_state.get("current_input_context", "").strip()
    presentation_format = outline.get("presentation_format") or st.session_state.get("last_presentation_format", "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng")
    is_pas_story = is_pas_storytelling_strategy(presentation_format, fixed_title)
    dna = st.session_state.get("content_analysis") or {}
    
    raw_orig_price, raw_sale_price = dna.get("original_price_spoken", ""), dna.get("sale_price_spoken", "")
    if not raw_orig_price or not raw_sale_price:
        num_matches = [int(n.replace('.', '').replace(',', '')) for n in re.findall(r'\b\d{1,3}(?:[.,]\d{3})+\b', str(dna.get("detected_prices", "")))]
        if len(num_matches) >= 2: num_matches.sort(); raw_orig_price, raw_sale_price = number_to_vietnamese_words(num_matches[-1]).replace(" đồng", ""), number_to_vietnamese_words(num_matches[0]).replace(" đồng", "")
        elif len(num_matches) == 1: raw_orig_price, raw_sale_price = number_to_vietnamese_words(int(num_matches[0] * 1.25)).replace(" đồng", ""), number_to_vietnamese_words(num_matches[0]).replace(" đồng", "")
        else: raw_orig_price, raw_sale_price = "ba trăm năm mươi nghìn", "hai trăm chín mươi nghìn"

    orig_price_spoken, sale_price_spoken = clean_and_normalize_voiceover(raw_orig_price), clean_and_normalize_voiceover(raw_sale_price)
    soft_orig_price = dna.get("rounded_soft_original_spoken") or convert_to_soft_price_range(orig_price_spoken, is_orig=True, exact_raw_str=str(dna.get("exact_original_price_ocr", "")))
    soft_sale_price = dna.get("rounded_soft_sale_spoken") or convert_to_soft_price_range(sale_price_spoken, is_orig=False, exact_raw_str=str(dna.get("exact_sale_price_ocr", "")))

    self_pronoun, audience_pronoun = dna.get("self_pronoun") or "em", dna.get("audience_pronoun") or ("các chị em" if not is_viral else "mọi người")
    hero_color_str = dna.get("hero_sku_color", "").strip()
    locked_color_en = translate_and_lock_color_en(hero_color_str, dna.get("hero_sku_color_en", "").strip())
    raw_prod_name = str(dna.get("what_and_unique", "sản phẩm")).split(":", 1)[0].strip() if ":" in str(dna.get("what_and_unique", "sản phẩm")) else str(dna.get("what_and_unique", "sản phẩm")).strip()
    ai_product_visual_en, dimensions_str = str(dna.get("product_visual_en", "")).strip(), str(dna.get("product_dimensions", "")).strip()

    check_str = f"{raw_prod_name} {fixed_title} {full_vo_script} {user_custom_note} {dna.get('what_and_unique', '')}"
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
    
    ai_koc_data = dna.get("koc_demographic_analysis", {})
    detected_gender, detected_demographic_en, voice_prompt = get_demographics_description(
        char_profiles, 
        ai_koc_data.get("persona_en", "") if isinstance(ai_koc_data, dict) else "", 
        ai_koc_data.get("body_and_hair_en", "") if isinstance(ai_koc_data, dict) else "", 
        ai_koc_data.get("voice_prompt", "") if isinstance(ai_koc_data, dict) else "",
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
        scene_1_action_inst = "CRITICAL: Translate the EXACT physical struggle/pain mentioned in the voiceover (e.g., vigorously scratching itchy skin, pinching nose/wincing for bad smell, rubbing sore neck) into vivid explicit body language. EMPTY HANDS, ZERO PRODUCT IN FRAME."
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
    1. Cắt thoại gốc thành 4 phần.
    2. ĐỒNG BỘ BỐI CẢNH (CRITICAL): Bối cảnh chung (master_setting_en) PHẢI KHỚP với thoại. Nếu thoại rủ "đi cafe", bối cảnh là "coffee shop". CẤM set "bedroom".
    3. VỊ TRÍ TƯƠNG TÁC (CRITICAL): Tôn trọng công năng sản phẩm. CẤM đưa sản phẩm lên mặt nếu không phải là mỹ phẩm bôi mặt/đồ ăn.
    4. HÀNH ĐỘNG HÌNH THỂ (Cảnh 1): Biểu cảm cơ thể chân thực khớp với nỗi đau (gãi ngứa, bịt mũi vì hôi...).

    TRẢ VỀ DUY NHẤT ĐỊNH DẠNG JSON:
    {{
        "title": "{fixed_title}",
        "master_setting_en": "Mô tả không gian tiếng Anh (VD: 'stylish coffee shop'). CẤM dùng 'bedroom' nếu thoại ra ngoài.",
        "wardrobe_lock": {{
            "outfit_vi": "Thiết kế 1 set đồ ĐỘC BẢN, cực kỳ thời trang. (Ghi rõ: loại áo, độ dài tay áo, có sơ vin không, kết hợp giày gì).",
            "master_character_en": "CRITICAL: Define the EXACT outfit down to the sleeve length and tucking. MUST NOT contain 'or', 'maybe'. This EXACT string locks the outfit across 4 scenes."
        }},
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention",
                "setting": "Bối cảnh mở màn tiếng Việt...",
                "expression_en": "{'wincing, vigorously scratching skin, or showing physical discomfort' if is_pas_story else 'lively, engaging expression'}",
                "action_en": "{scene_1_action_inst} (under 25 words)",
                "sfx": "Foley thực tế (không nhạc)",
                "director": "Attention | {'Trực tiếp mô tả HÀNH ĐỘNG CƠ THỂ BỊ NỖI ĐAU (TUYỆT ĐỐI KHÔNG CÓ SẢN PHẨM)' if is_pas_scn1_no_prod else 'Đưa sản phẩm ra tiền cảnh'}",
                "voiceover": "Trích phần đầu của kịch bản thoại gốc..."
            }},
            {{
                "scene": 2, "aida_stage": "Interest",
                "setting": "Bối cảnh thực tế...",
                "expression_en": "relieved, confident and enthusiastic",
                "action_en": "{action_scene_2} (under 20 words)",
                "sfx": "Tiếng thao tác thực tế",
                "director": "Interest | Thao tác sản phẩm",
                "voiceover": "Trích đoạn tiếp theo..."
            }},
            {{
                "scene": 3, "aida_stage": "Desire",
                "setting": "Bối cảnh đồng bộ...",
                "expression_en": "smiling contentedly with approving nod",
                "action_en": "{action_scene_3} (under 20 words)",
                "sfx": "Tiếng trải nghiệm thực tế",
                "director": "Desire | Thao tác cận cảnh",
                "voiceover": "Trích đoạn tiếp theo..."
            }},
            {{
                "scene": 4, "aida_stage": "Action",
                "setting": "Bối cảnh kết thúc...",
                "expression_en": "smiling warmly with open-palm gesture",
                "action_en": "{action_scene_4} (under 18 words)",
                "sfx": "Tiếng chuông ting nhẹ",
                "director": "Action | Chốt deal",
                "voiceover": "Trích đoạn chốt cuối..."
            }}
        ]
    }}
    """
    sys_inst = get_sys_inst_details(current_active_mode, "Điện Ảnh Chân Thực", "On-camera", char_rules, "Max 10s", 1, char_profiles, user_custom_note, presentation_format, self_pronoun, audience_pronoun, fixed_setting_base, True, is_pas_story, forced_footwear, target_id)
    
    scenes, w_lock, master_setting_en = [], {}, "clean minimalist modern setting"
    max_retries = 2
    for attempt in range(max_retries):
        try:
            res = call_gemini([prompt_text], sys_inst, max_tokens=4096)
            scenes = extract_scenes(res)
            if scenes and isinstance(scenes, list) and len(scenes) > 0:
                master_setting_en = sanitize_third_party_ip(res.get("master_setting_en", "clean minimalist modern setting")).strip().rstrip('.')
                w_lock = res.get("wardrobe_lock", {})
                break
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Lỗi khi gọi AI: {str(e)}")
            time.sleep(1.5)

    if not scenes: raise Exception("AI không tạo được danh sách phân cảnh. Vui lòng bấm tạo lại.")
    
    base_char_prompt = sanitize_third_party_ip(w_lock.get("master_character_en") or f"{detected_demographic_en}, wearing high-fashion outfit").strip().rstrip('.')
    if is_single_skirt_mode: base_char_prompt = enforce_single_tube_skirt_syntax(base_char_prompt)
    if not is_fashion_wearable: base_char_prompt += ", standing completely still with zero body rotation"
    
    locked_character_prompt = f"[IDENTICAL CHARACTER LOCK: EXACT SAME face, body shape, hairstyle, hair color, and precise wardrobe outfit across all scenes. Presenter speaking directly to the lens] {base_char_prompt}"
    final_outfit_vi = w_lock.get("outfit_vi") or "Trang phục Stylist đồng bộ 4 cảnh"

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
        vo_text = clean_and_normalize_voiceover(scn.get("voiceover", ""))
        scn["voiceover"] = vo_text
        scn["director"] = sanitize_policy_text(scn.get("director", ""))
        
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
        
        micro_expr = sanitize_third_party_ip(scn.get("expression_en", "natural engaging expression")).strip().rstrip('.')
        clean_act = sanitize_destructive_motion_verbs(sanitize_third_party_ip(re.sub(r'^(?:Character\s+(?:is\s+)?|Subject\s+(?:is\s+)?)', '', scn.get("action_en") or action_scene_2, flags=re.IGNORECASE).strip()).rstrip('.'), is_fashion=is_fashion_wearable, is_food=is_food)
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
    
    st.session_state.generated_details[str(target_id)] = res
    auto_save_current_session()

# ==============================================================================
# HÀM clone_script và generate_more_scripts ĐÃ ĐƯỢC CẬP NHẬT Ở DƯỚI
# ==============================================================================
