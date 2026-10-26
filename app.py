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
# 1. CẤU HÌNH GIAO DIỆN & CSS TOÀN CỤC
# ==============================================================================
st.set_page_config(page_title="Đạo Diễn AI - Hệ Thống Kịch Bản Pro", page_icon="🎬", layout="wide")

st.markdown("""
<style>
    .header-container { text-align: center; padding: 1.2rem; background: radial-gradient(circle, rgba(255,75,75,0.08) 0%, rgba(255,255,255,0) 70%); border-radius: 16px; margin-bottom: 1rem; }
    .main-title { font-size: 2.2rem !important; font-weight: 900 !important; background: linear-gradient(90deg, #ff0050 0%, #ff5252 50%, #ff7300 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    div[data-testid="stButton"] > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button[kind="primary"] { background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important; color: white !important; border-radius: 8px !important; font-weight: bold; width: 100%; }
    div[data-testid="stButton"] > button[kind="secondary"], div[data-testid="stFormSubmitButton"] > button[kind="secondary"] { background: linear-gradient(135deg, #ff4b4b 0%, #ff7300 100%) !important; color: #ffffff !important; box-shadow: 0 3px 8px rgba(255, 75, 75, 0.35) !important; padding: 0.55rem 1rem !important; font-weight: bold !important; border: none !important; width: 100%; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 3px 8px; border-radius: 4px; font-size: 11px; border: 1px solid #bbf7d0; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 3px 8px; border-radius: 4px; font-size: 11px; border: 1px solid #fde68a; }
    .autosave-badge { color: #0369a1; font-weight: 700; background: #e0f2fe; padding: 4px 10px; border-radius: 6px; font-size: 12px; border: 1px solid #bae6fd; display: inline-block; margin-top: 4px; }
    .detail-header-box { background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%); border: 1.5px solid #bfdbfe; border-radius: 12px; padding: 14px 18px; margin-bottom: 20px; color: #1e3a8a; line-height: 1.7; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
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
1. ĐỒNG NHẤT BỐI CẢNH & NHÂN VẬT (MASTER LOCK):
   - Sinh 1 'master_setting_en' và dùng cho CẢ 4 CẢNH (không được đổi phòng, đổi cảnh).
   - Sinh 1 'master_character_en' duy nhất miêu tả từ tóc, mặt, quần áo, đến giày dép. KHÔNG THAY ĐỔI TRANG PHỤC trong suốt video.
2. PRODUCT SCALE, CAMERA & TEST RULES:
   - CẦM NẮM TUYỆT ĐỐI (ANTI-DROP): KOC phải cầm thật chắc sản phẩm bằng cách ôm vào phần Thân Chính (Main Body), TUYỆT ĐỐI KHÔNG ĐƯỢC thả rơi hay ném. Chống mọc tay cầm thừa.
   - Nếu là Thời trang/Giày Tất: Cảnh 1 & Cảnh 4 mặc trên người. RIÊNG CẢNH 2 & 3 PHẢI CẦM TRÊN TAY ĐỂ SOI CHI TIẾT VÀ TEST LỰC (vò, kéo, bẻ).
   - NẾU KHÔNG PHẢI THỜI TRANG: Tuyệt đối CẤM nhân vật xoay người. Phải ĐỨNG IM (zero body rotation).
3. THỰC TRẠNG NỖI ĐAU CẢNH 1 (VISUAL PAIN POINT):
   - Ở Cảnh 1 (không có SP), BẮT BUỘC miêu tả HÀNH ĐỘNG VẬT LÝ thực tế của nỗi đau (VD: đang gãi mạnh mảng da mẩn đỏ, lúi húi kéo tất tuột gót) kết hợp thoại từ 0.0s.
4. VĂN NÓI HÀ NỘI THUẦN VIỆT & CHỐNG VẤP THOẠI LẮP TỪ:
   - CẤM sử dụng dấu chấm lửng (...), dấu gạch nối (-), hoặc ký hiệu ([ ]) trong thoại để AI đọc mượt.
   - NẾU LÀ TPCN/THUỐC: Cấm dùng "chữa bệnh, đặc trị". Chỉ dùng "hỗ trợ, bảo vệ, bổ sung".
5. LUẬT MẸ VÀ BÉ:
   - Tuyệt đối không để em bé một mình.
"""

INTIMATE_SAFE_ENGLISH_LEXICON = {
    r'\b(?:push-?up\s+|lace\s+|wireless\s+|seamless\s+)?bras?\b': 'seamless comfort top garment',
    r'\bbrassieres?\b': 'seamless support garment',
    r'\b(?:lace\s+|cotton\s+|seamless\s+)?panties\b': 'seamless breathable base-layer garment',
    r'\bunderwears?\b': 'soft cotton comfort apparel',
    r'\bbriefs?\b': 'seamless base-layer garment',
    r'\bthongs?\b': 'seamless fabric garment',
    r'\blingerie\b': 'pastel loungewear apparel',
    r'\bbikinis?\b': 'resort activewear',
    r'\bcleavage\b': 'modest neckline',
    r'\bsexy\b': 'elegant modern'
}

POLICY_REPLACEMENTS = {
    r'\ban\s*toàn\s*tuyệt\s*đối\b': 'cực kỳ an toàn', r'\byên\s*tâm\s*tuyệt\s*đối\b': 'cực kỳ yên tâm',
    r'\btuyệt\s*đối\s*an\s*toàn\b': 'cực kỳ an toàn', r'\btuyệt\s*đối\s*yên\s*tâm\b': 'cực kỳ yên tâm',
    r'\bhoàn\s*toàn\s*yên\s*tâm\b': 'cực kỳ yên tâm', r'\bhoàn\s*toàn\s*an\s*toàn\b': 'rất an toàn',
    r'\b100\s*%\s*an\s*toàn\b': 'rất an toàn', r'\ban\s*toàn\s*100\s*%\b': 'cực kỳ an toàn',
    r'(\b[a-zà-ỹ]+)\s+tuyệt\s*đối\b': r'cực kỳ \1', r'\btuyệt\s*đối\b': 'rất', r'\bhoàn\s*toàn\b': 'thực sự',
    r'\b100\s*%\b': 'rất nhiều', r'\bchắc\s*chắn\b': 'rất có thể', r'\bcam\s*kết\b': 'an tâm',
    r'\bvĩnh\s*viễn\b': 'lâu dài', r'\bchuẩn\s*đét\b': 'vừa vặn', r'\bsố\s*1\b': 'hàng đầu',
    r'\bthần\s*dược\b': 'bí quyết', r'\btốt\s*nhất\b': 'rất tốt',
    r'\bchữa\s*bệnh\b': 'hỗ trợ sức khỏe', r'\bchữa\s*khỏi\b': 'hỗ trợ cải thiện',
    r'\bđặc\s*trị\b': 'sản phẩm chuyên biệt', r'\bthuốc\s*đặc\s*trị\b': 'sản phẩm chuyên biệt',
    r'\btriệt\s*để\b': 'hiệu quả', r'\btrị\s*dứt\s*điểm\b': 'hỗ trợ cải thiện hiệu quả',
    r'\bdứt\s*điểm\b': 'cải thiện', r'\bthuốc\s*trị\b': 'sản phẩm hỗ trợ',
    r'\bđiều\s*trị\b': 'hỗ trợ quá trình', r'\bcam\s*kết\s*khỏi\b': 'giúp người dùng an tâm',
    r'\bbác\s*sĩ\s*khuyên\s*dùng\b': 'được nhiều người tin dùng',
    r'\btrắng\s*cấp\s*tốc\b': 'sáng khỏe tự nhiên', r'\bgiảm\s*béo\s*cấp\s*tốc\b': 'hỗ trợ vóc dáng thon gọn',
    r'\bxóa\s*sạch\s*nám\b': 'giúp mờ thâm sạm', r'\bkhỏi\s*hẳn\b': 'đỡ hẳn',
    r'\btrợ\s*giá\b': 'giảm giá sâu có hạn', r'\bphiên\s*live\b': 'đợt ưu đãi này', 
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
    r'\b(\w+)\s+mươi\s+(?:tư|tứ)\b': r'\1 mươi bốn', r'\bbốn\s+(?:tư|tứ)\b': 'bốn mươi bốn',
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
    r'\bcưng\s+xỉu\b': 'yêu cực kỳ', r'\bcoi\b': 'xem', r'\bmua\s+liền\b': 'mua ngay',
    r'\bliền\s+tay\b': 'ngay tay', r'\bbữa\s+nay\b': 'hôm nay', r'\bbữa\s+hổm\b': 'hôm trước',
    r'\bhổm\s+rày\b': 'dạo này', r'\bmấy\s+chế\b': 'các chị em', r'\bmấy\s+bà\b': 'các chị em',
    r'\bmấy\s+bồ\b': 'các bạn', r'\bưng\s+bụng\b': 'vừa ý'
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
# 4. KHAI BÁO TOÀN BỘ HÀM TIỆN ÍCH, XỬ LÝ TEXT (ĐẦY ĐỦ 100%)
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
        (r'\bba\s+(?:tư|tứ)\b', 'ba mươi bốn'), (r'\b(?:tư|tứ)\s+mươi\b', 'bốn mươi'), (r'\b(\w+)\s+mươi\s+(?:tư|tứ)\b', r'\1 mươi bốn')
    ]: cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\ban\s*toàn\s*rất\s*luôn\b', 'cực kỳ an toàn luôn', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\ban\s*toàn\s*rất\b', 'rất an toàn', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b([a-zà-ỹ]+)\s+rất\s+luôn\b', r'cực kỳ \1 luôn', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'[\(\)\[\]\{\}]', '', cleaned)
    cleaned = re.sub(r'\.{2,}', ',', cleaned)
    cleaned = re.sub(r'[-~*]', '', cleaned)
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

# ==============================================================================
# 5. HỆ THỐNG ĐẠO DIỄN: GÓC MÁY, NHẬN DIỆN ĐA NGÀNH HÀNG & VẬT LÝ ĐỘNG LỰC
# ==============================================================================
def detect_food(text_to_check: str) -> bool:
    if not text_to_check: return False
    keywords = ["đồ ăn", "thức ăn", "bánh", "kẹo", "nước", "sữa", "trà", "cafe", "món ăn", "thực phẩm", "food", "snack", "drink", "cake", "noodle", "trái cây", "thịt", "hải sản", "cơm", "bún", "phở"]
    return any(k in text_to_check.lower() for k in keywords)

def detect_cosmetics(text_to_check: str) -> bool:
    if not text_to_check: return False
    keywords = ["kem dưỡng", "son", "môi", "serum", "phấn", "tẩy trang", "mặt nạ", "sữa rửa mặt", "kem chống nắng", "toner", "lotion", "cream", "lipstick", "lip", "makeup", "skincare", "cosmetic"]
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
        "giỏ", "rổ", "kệ", "hộp", "thùng", "tủ", "móc", "chậu", "cây lau", "bàn chải", "máy giặt", "túi đựng", 
        "khay", "nồi", "chảo", "dao", "thớt", "máy xay", "bếp", "bình", "cốc", "ly", "ghế", "bàn", "đèn", "quạt", 
        "máy sấy", "bàn là", "bàn ủi", "basket", "rack", "organizer", "bin", "box", "hamper", "shelf", "holder", 
        "pan", "pot", "tool", "vacuum", "dryer", "blower",
        "tai nghe", "headphone", "earbud", "earphone", "bluetooth", "điện thoại", "phone", "loa", "speaker", 
        "sạc", "chuột", "bàn phím", "mic"
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
    if any(k in combined_text for k in ["mưa", "ẩm ướt", "nồm"]): return ("rain droplets on window, soft overcast indoor lighting" if is_indoor else "light rain, wet ground, overcast sky"), "subtle rain ambience (no reverb)"
    elif any(k in combined_text for k in ["nắng", "trưa hè"]): return ("warm sunbeams through window" if is_indoor else "sunny daylight, golden sunbeams"), "subtle breeze ambience (no reverb)"
    elif any(k in combined_text for k in ["sáng sớm", "buổi sáng", "bình minh"]): return "fresh morning sunlight", "subtle morning ambience (no reverb)"
    elif any(k in combined_text for k in ["hoàng hôn", "chiều tà", "buổi chiều"]): return "warm amber sunset glow", "subtle evening ambience (no reverb)"
    elif any(k in combined_text for k in ["ban đêm", "tối muộn", "buổi tối", "đi ngủ"]): return "cozy warm tungsten lamp lighting", "quiet nighttime ambience (no reverb)"
    return ("clean natural daylight with soft warm fill light" if is_indoor else "bright commercial daylight"), ""

def sanitize_veo3_prompt(prompt_text: str) -> str:
    if not prompt_text: return ""
    p = re.sub(r'\bgesturing\s+(?:warmly\s+)?(?:toward\s+)?corner\b', 'sharing recommendations with an open-palm gesture', prompt_text, flags=re.IGNORECASE)
    return sanitize_third_party_ip(re.sub(r'\bpointing\s+(?:downward\s+)?(?:to\s+)?(?:corner|cart)\b', 'speaking with welcoming open hands', p, flags=re.IGNORECASE))

def generate_char_rules_string(profiles):
    if not profiles: return "100% fictional Vietnamese persona, natural black hair, consistent outfit across 4 scenes."
    return " | ".join([f"Actor {p['id']} ({p['role']}): fictional Vietnamese persona, consistent look across 4 scenes" for p in profiles])

def get_demographics_description(char_profiles, ai_persona_en="", ai_body_and_hair_en="", is_mom_baby=False):
    if is_mom_baby: return "female", "A caring Vietnamese mother safely holding/interacting with her baby"
    
    user_roles = [str(p.get("role", "")).strip() for p in (char_profiles or []) if str(p.get("role", "")).strip()]
    extra_physique = f", {ai_body_and_hair_en.strip()}" if ai_body_and_hair_en and len(ai_body_and_hair_en.strip()) > 5 else ", slender figure, jet-black hair, natural fair-warm skin"
    if not user_roles and ai_persona_en and len(ai_persona_en.strip()) > 6:
        ai_p_lower = ai_persona_en.lower()
        gender = "male" if any(k in ai_p_lower for k in ["man", "male", "boy", "father", "gentleman", "anh", "nam"]) else "female"
        clean_p = re.sub(r'\b(?:authentic|real|famous|celebrity|popular|influencer|koc|model|fictional|everyday)\b', '', ai_persona_en, flags=re.IGNORECASE).strip()
        return gender, f"{re.sub(r'^a\s+', '', clean_p, flags=re.IGNORECASE).strip()}{extra_physique}"
    if not char_profiles or not user_roles: return "female", f"25yo Vietnamese woman{extra_physique}"
    role_lower = str(char_profiles[0].get("role", "")).lower()
    if any(k in role_lower for k in ["bố", "ba", "chồng", "bác trai", "nam", "anh", "trai"]): return "male", f"26yo Vietnamese man{extra_physique}"
    elif any(k in role_lower for k in ["ông", "già", "bác già"]): return "male", "65yo Vietnamese senior man"
    elif any(k in role_lower for k in ["bà", "bà nội", "bà ngoại"]): return "female", "65yo Vietnamese senior woman"
    return "female", f"25yo Vietnamese woman{extra_physique}"

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

def get_product_centric_camera_shot(scene_idx: int, is_fashion: bool, is_footwear_acc: bool, is_pas_scene1: bool, clean_prod_en: str, is_appliance: bool, is_long_handle: bool, is_food: bool, is_cosmetics: bool, is_mom_baby: bool, is_medicine: bool) -> str:
    if is_pas_scene1 and not is_fashion: return "Vertical 9:16 stable dynamic shot framing the character and the specific problem"
    
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
        if scene_idx == 0: return f"Vertical 9:16 stable elegant medium shot holding {clean_prod_en}"
        elif scene_idx == 1: return f"Vertical 9:16 stable smooth macro close-up swatching or focusing on the texture of {clean_prod_en}"
        elif scene_idx == 2: return f"Vertical 9:16 stable close-up beauty shot showing application of {clean_prod_en}"
        else: return f"Vertical 9:16 stable radiant medium shot with {clean_prod_en}"

    elif is_mom_baby:
        if scene_idx == 0: return f"Vertical 9:16 stable soft warm medium shot holding {clean_prod_en}"
        elif scene_idx == 1: return f"Vertical 9:16 stable close-up shot showing the soft material/texture of {clean_prod_en}"
        elif scene_idx == 2: return f"Vertical 9:16 stable gentle close-up action shot testing or using {clean_prod_en}"
        else: return f"Vertical 9:16 stable balanced cozy medium shot with {clean_prod_en}"

    elif is_fashion:
        if scene_idx == 0: return "Vertical 9:16 eye-level three-quarter full-body shot showcasing the outfit"
        elif scene_idx == 1: return f"Vertical 9:16 stable close-up focused on the hands holding and physically demonstrating the texture of {clean_prod_en}"
        elif scene_idx == 2: return f"Vertical 9:16 stable macro close-up focused on the hands physically testing and stretching the fabric of {clean_prod_en}"
        else: return "Vertical 9:16 warm eye-level medium shot"
        
    elif is_long_handle:
        if scene_idx == 0: return f"Vertical 9:16 stable full-body wide shot, exact reference-matching {clean_prod_en} held at normal realistic scale"
        elif scene_idx == 1: return f"Vertical 9:16 stable medium-wide shot, keeping both human and {clean_prod_en} in frame to maintain normal true-to-life size (NO macro close-up)"
        elif scene_idx == 2: return f"Vertical 9:16 stable waist-down medium-wide shot showing the {clean_prod_en} working on the floor at normal realistic scale"
        else: return f"Vertical 9:16 stable full-body balanced shot, exact reference-matching {clean_prod_en} displayed at normal scale"
        
    elif is_appliance:
        if scene_idx == 0: return f"Vertical 9:16 stable product-focused medium shot, exact reference-matching {clean_prod_en} held steadily, maintaining realistic scale"
        elif scene_idx == 1: return f"Vertical 9:16 stable close-up shot locked on {clean_prod_en}, maintaining 100% accurate true-to-life scale and identical proportions, tack-sharp focus"
        elif scene_idx == 2: return f"Vertical 9:16 stable tight close-up action shot centered directly on {clean_prod_en}, strictly maintaining accurate real-world scale during subtle interaction"
        else: return f"Vertical 9:16 stable balanced medium shot with exact reference-matching {clean_prod_en} displayed in realistic scale"
        
    else:
        if scene_idx == 0: return f"Vertical 9:16 stable product-focused medium shot, {clean_prod_en} held prominently, maintaining realistic human-to-product scale"
        elif scene_idx == 1: return f"Vertical 9:16 stable close-up shot (dolly-in) locked onto {clean_prod_en}, strictly maintaining true-to-life realistic scale, tack-sharp focus"
        elif scene_idx == 2: return f"Vertical 9:16 stable tight close-up action shot on {clean_prod_en} in real-time use, maintaining accurate real-world scale"
        else: return f"Vertical 9:16 stable balanced medium shot with {clean_prod_en} displayed with realistic scale"

def get_universal_physics_rules(product_name: str, vo_text: str = "", is_fashion: bool = False, is_appliance: bool = False, is_long_handle: bool = False, is_food: bool = False, is_cosmetics: bool = False, is_mom_baby: bool = False, is_medicine: bool = False, is_mom_baby_hard: bool = False) -> str:
    p = f"{product_name} {vo_text}".lower()
    
    if is_food: return "Mouth-watering visual physics; showing steam rising, juicy texture, melting, or smooth pulling/stretching if applicable. Presenter stands completely still; natural hand interaction only, NEVER dropping."
    elif is_cosmetics: 
        if any(k in p for k in ["son", "môi", "lip"]): return "Smooth creamy/pigmented texture; visibly leaving a rich color stroke or flawless texture on the skin/lips. Delicate hand interaction only, gripping firmly; body remains perfectly still."
        return "Smooth creamy or watery texture physics; visibly absorbing into the skin with a glowing, flawless finish. Delicate hand interaction only, holding securely; body remains perfectly still."
    elif is_mom_baby: 
        if is_mom_baby_hard: return "STRICT REFERENCE TRACKING for the baby product. 100% rigid non-deforming geometry, true-to-life scale. Safe and gentle interaction, holding securely, NEVER dropping."
        return "Ultra-soft fabric/material texture; showing gentle elasticity, high liquid absorption, or completely safe smooth surfaces. Holding securely."
    elif is_medicine: return "Clean, safe, solid capsule/pill geometry or smooth powder dissolving perfectly in clear water. Holding securely."
    
    elif is_fashion: return "Natural fabric drape in motion; subject steps smoothly, turns 45 degrees, and touches fabric softly (worn on body, zero duplicate item in hands)."
    elif any(k in p for k in ["máy sấy", "máy thổi", "quạt", "dryer", "blower", "fan"]): return "CAMERA FOCUS LOCKED ON PRODUCT AND AIRFLOW TARGET: 100% rigid non-deforming body lock, true-to-life scale. Creates a powerful, completely invisible and transparent airflow (ZERO fire, ZERO sparks, ZERO smoke, ZERO plasma). The invisible breeze realistically blows away dust, leaves, or softly blows hair. Gripping firmly, never dropping."
    elif any(k in p for k in ["hút bụi", "vacuum"]): return "CAMERA FOCUS LOCKED ON VACUUM HEAD AND DUSTBIN: 100% rigid non-deforming body lock, true-to-life scale. The nozzle glides swiftly and firmly, visibly sucking dirt, crumbs, or debris off the surface directly into the transparent dustbin in real-time. Holding securely, never dropping."
    elif is_long_handle or any(k in p for k in ["chà sàn", "lau nhà", "bàn chải", "cọ", "tẩy", "rửa", "mop", "brush", "scrubber", "cleaner"]): return "Rigid tool body lock, true-to-life scale (NO giant sizes); product glides/scrubs rapidly and decisively across the floor/surface, visibly removing dirt/stains on the spot. Gripping firmly, never dropping."
    # BỔ SUNG LỆNH ÔM VÀO THÂN SẢN PHẨM (MAIN BODY) ĐỂ CHỐNG MỌC TAY CẦM ẢO GIÁC
    elif is_appliance: return "STRICT REFERENCE TRACKING: The appliance maintains 100% exact shape, true-to-life scale, proportions, and surface details identical to the reference image. Zero morphing, zero hallucinated parts, zero extra handles. The product stays completely rigid while presenter stands perfectly still; hands hold the MAIN BODY of the product firmly, fast decisive interaction, NEVER dropping."
    else: return "CAMERA FOCUS LOCKED ON PRODUCT IN FOREGROUND: 100% rigid non-deforming 3D geometry, true-to-life scale (zero morphing); presenter stands completely still (zero body rotation); hands hold the MAIN BODY of the product firmly and trace surface decisively, zero extra handles, never dropping."

def get_action_templates_by_industry(clean_prod_en: str, check_str: str, is_fashion_wearable: bool, is_appliance: bool, is_long_handle: bool, is_food: bool, is_cosmetics: bool, is_mom_baby: bool, is_medicine: bool):
    p = f"{clean_prod_en} {check_str}".lower()
    
    if any(k in p for k in ["sock", "shoe", "boot", "sandal", "sneaker", "tights", "tất", "vớ", "giày", "dép"]):
        return ("stepping forward stylishly showcasing the footwear/socks on feet", "holding the product securely in hands, tracing fingers along the seams and material to show premium quality", "holding the product securely in hands, bending the sole or stretching the material firmly to demonstrate extreme flexibility and durability", "posing confidently with focus on the legs/feet")

    if is_food: return (f"holding {clean_prod_en} securely while standing completely still and presenting it deliciously", f"taking a satisfying bite or showing the inside texture of {clean_prod_en}", f"pouring, dipping, or stretching {clean_prod_en} to show its mouth-watering details", f"holding {clean_prod_en} securely with a happy, satisfied expression")
    elif is_cosmetics: return (f"elegantly holding {clean_prod_en} securely next to the face", f"swatching or applying a small amount of {clean_prod_en} smoothly on the skin, visibly leaving a rich stroke", f"gently tapping {clean_prod_en} into the skin to show the glowing finish", f"holding {clean_prod_en} securely with a radiant smile")
    elif is_mom_baby: return (f"caring mother holding {clean_prod_en} securely next to her baby", f"gently touching or interacting with {clean_prod_en} to show its features", f"demonstrating the safe use of {clean_prod_en} with the baby", f"holding {clean_prod_en} securely with a caring smile next to the baby")
    elif is_medicine: return (f"holding {clean_prod_en} securely in hand", f"showing {clean_prod_en} up close next to a clear glass of water", f"dropping or demonstrating the use of {clean_prod_en}", f"holding {clean_prod_en} securely with a healthy, confident smile")

    elif is_fashion_wearable: return ("stepping forward confidently and gesturing expressively while speaking", "holding the product securely in hands, rubbing and stretching the fabric to show its anti-wrinkle or premium texture", "holding the product securely in hands, stretching the fabric firmly or demonstrating its breathable texture up close", "posing confidently with a warm open-palm gesture")
    elif any(k in p for k in ["máy sấy", "máy thổi", "quạt", "dryer", "blower", "fan"]): return (f"holding the rigid {clean_prod_en} firmly maintaining realistic scale", f"turning on {clean_prod_en} swiftly up close, showing completely transparent and invisible airflow (no sparks)", f"aiming {clean_prod_en} to forcefully blow away dust or leaves with invisible breeze", f"holding {clean_prod_en} securely with a warm open-palm gesture")
    elif any(k in p for k in ["hút bụi", "vacuum"]): return (f"holding the rigid {clean_prod_en} firmly maintaining realistic scale", f"positioning {clean_prod_en} on the surface to show its rigid structure", f"gliding {clean_prod_en} rapidly in focus, visibly sucking dirt straight into the dustbin", f"holding {clean_prod_en} securely with a warm open-palm gesture")
    elif is_long_handle: return (f"holding the exact reference-matching {clean_prod_en} firmly", f"demonstrating the exact reference-matching {clean_prod_en} swiftly on the floor without any added details or scale distortion", f"scrubbing/gliding the {clean_prod_en} rapidly and decisively across the floor keeping 100% fidelity and true realistic scale", f"holding {clean_prod_en} firmly with a confident gesture")
    
    # BỔ SUNG LỆNH ÔM VÀO THÂN SẢN PHẨM (MAIN BODY) ĐỂ CHỐNG MỌC TAY CẦM ẢO GIÁC
    elif is_appliance: return (f"standing completely still while holding the main body of {clean_prod_en} firmly at realistic scale", f"presenting the main body of {clean_prod_en} swiftly without any added details or side handles", f"demonstrating {clean_prod_en} with fast, decisive hand interaction on the main body while keeping 100% fidelity", f"holding the main body of {clean_prod_en} firmly with a confident open-palm gesture")
    else: return (f"standing perfectly still holding the main body of {clean_prod_en} firmly at realistic scale toward the lens", f"positioning {clean_prod_en} right in front of the lens, tracing fingers swiftly and decisively along its solid main body without distorting scale", f"demonstrating {clean_prod_en} with fast decisive hand movements on the main body while preserving 100% rigid geometry", f"holding the main body of {clean_prod_en} securely with a confident open-palm gesture")

def build_multi_industry_stylist_rules(product_en: str, hero_color: str, setting_vi: str, gender: str, intimate_type: str, is_fashion: bool, raw_vi_info: str = "", is_food: bool = False, is_cosmetics: bool = False, is_mom_baby: bool = False, is_medicine: bool = False) -> str:
    s_lower, h_lower = f"{product_en} {setting_vi} {raw_vi_info}".lower(), hero_color.lower()
    setting_lower = setting_vi.lower()
    
    is_professional_outdoor = any(k in setting_lower or k in raw_vi_info.lower() for k in ["văn phòng", "công sở", "công ty", "ngoài trời", "đường phố", "sự kiện", "quán", "cửa hàng", "office", "street"])
    is_wet_room = any(k in setting_lower for k in ["phòng tắm", "nhà vệ sinh", "toilet", "bathroom", "nhà tắm"])
    is_home_cozy = any(k in setting_lower for k in ["phòng ngủ", "phòng khách", "nhà bếp", "bedroom", "living room", "kitchen", "pijama", "đồ ngủ"])
    
    is_evening = any(k in s_lower for k in ["váy", "đầm", "dự tiệc", "đi tiệc", "công sở", "thanh lịch", "áo dài", "dress", "gown"])
    is_single_skirt = detect_single_tube_skirt(s_lower)
    
    if is_professional_outdoor:
        if gender == "female" and is_evening: footwear = "elegant pointed-toe high heels or smart-casual loafers"
        else: footwear = "clean minimalist white sneakers or smart-casual loafers"
    elif is_wet_room:
        footwear = "barefoot or wearing waterproof plastic slippers"
    elif is_home_cozy and not is_fashion:
        footwear = "clean minimalist pastel indoor slippers"
    else:
        if is_fashion and is_evening and gender == "female": footwear = "elegant pointed-toe high heels or strappy heeled sandals"
        else: footwear = "clean minimalist white sneakers or smart-casual loafers"
    
    contrast = "Áo KOC màu Beige/Mocha/Xanh pastel tương phản làm nổi bật SP màu sáng" if any(k in h_lower for k in ["trắng", "white", "kem"]) else "Trang phục tông sáng/trung tính thanh lịch tôn SP"
    
    if is_cosmetics:
        contrast = "Trang phục thanh lịch, tóc tai gọn gàng, trang điểm nhẹ nhàng (clean elegant makeup, neat hair) tôn da KOC"
    elif is_mom_baby:
        contrast = "Trang phục mặc nhà chất liệu cotton/linen mềm mại, tông màu pastel ấm áp (cozy soft pastel home wear)"
    elif is_medicine:
        contrast = "Trang phục smart-casual thanh lịch, gọn gàng, tạo cảm giác chuyên gia an toàn"
        
    jewelry = "dainty necklace, pearl stud earrings, and thin bracelet/watch" if gender == "female" else "minimalist wristwatch"
    skirt_rule = " | ĐẶC BIỆT: Phần dưới là VÁY 1 ỐNG RỘNG (full-length A-line maxi skirt, single unified unsplit skirt tube, zero leg division - CẤM viết từ pants/trousers)!" if is_single_skirt else ""
    return f"STYLIST LOCK: {contrast} | Footwear: {footwear} | Phụ kiện cố định 4 cảnh: {jewelry}{skirt_rule}."


# ==============================================================================
# 6. QUẢN LÝ DB (SUPABASE) VÀ LƯU TRỮ
# ==============================================================================
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

def save_single_account(email, acc_data):
    if not supabase or email == ADMIN_EMAIL: return
    try: supabase.table("licensed_accounts").upsert({"email": email, **acc_data}).execute()
    except Exception: pass

def delete_single_account(email):
    if not supabase or email == ADMIN_EMAIL: return
    try: supabase.table("licensed_accounts").delete().eq("email", email).execute()
    except Exception: pass

def check_usage_limit(email, is_detailing=False):
    if email == ADMIN_EMAIL: return True, ""
    acc = st.session_state.licensed_accounts.get(email)
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
    if not supabase: return False, "Chưa kết nối cơ sở dữ liệu."
    try:
        clean_content = json.loads(json.dumps(payload_data, default=str))
        if project_id:
            res = supabase.table("saved_projects").update({"project_title": title, "script_content": clean_content}).eq("id", project_id).execute()
            if res.data and len(res.data) > 0:
                st.session_state.last_autosave_time = datetime.now().strftime("%H:%M:%S")
                return True, f"Đã tự động cập nhật vào dự án '{title}'!"
        
        res = supabase.table("saved_projects").insert({"user_email": email, "project_title": title, "script_content": clean_content}).execute()
        if res.data and len(res.data) > 0:
            st.session_state.current_project_id = res.data[0]['id']
            st.session_state.last_autosave_time = datetime.now().strftime("%H:%M:%S")
            return True, f"Đã tự động tạo & lưu dự án '{title}'!"
        return False, "Không thể lưu dữ liệu dự án."
    except Exception as e:
        return False, str(e)

def auto_save_current_session():
    if not st.session_state.get("is_logged_in") or not supabase: return False, ""
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
        return save_project_to_db(st.session_state.current_email, st.session_state.active_project_title, payload, st.session_state.current_project_id)
    except Exception as e:
        return False, str(e)

# ==============================================================================
# 7. KHỞI TẠO SESSION STATE TOÀN CỤC CHUẨN XÁC NHẤT 
# ==============================================================================
if "session_id" not in st.session_state: st.session_state.session_id = str(uuid.uuid4())
for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", None),
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

if st.session_state.licensed_accounts is None: st.session_state.licensed_accounts = load_licensed_accounts()
is_system_busy = (
    st.session_state.get("current_processing_id") is not None or 
    st.session_state.get("current_cloning_id") is not None or
    st.session_state.get("trigger_main_generation") is True or
    st.session_state.get("trigger_more_generation") is True
)

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
    components.html("""<script>setTimeout(() => { var el = window.parent.document.getElementById('detailed-view-anchor'); if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); } else { window.parent.scrollTo({top: 400, behavior: 'smooth'}); } }, 250);</script>""", height=0)
    st.session_state.scroll_to_detail = False

# ==============================================================================
# 8. HỆ THỐNG GỌI GEMINI API: KHÓA CỨNG GEMINI-3.8-FLASH & LITE
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
    raise Exception("AI sinh JSON lỗi cấu trúc. Vui lòng bấm tạo lại.")

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
    if last_exception:
        if "503" in str(last_exception) or "unavailable" in str(last_exception).lower(): raise Exception("Google API bận tạm thời (503). Vui lòng đợi 5s rồi bấm lại.")
        raise last_exception

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, angle, custom_note="", presentation_format=""):
    is_viral = ("Viral" in mode)
    goal = "VIRAL (Chia sẻ mẹo/kiến thức/câu chuyện, KHÔNG bán hàng, KHÔNG giá)" if is_viral else "TIKTOK SHOP (Chuyển đổi bán hàng, giải quyết nỗi đau, chốt deal)"
    return f"ĐẠO DIỄN TIKTOK PRO | MỤC TIÊU: {goal} | CHIẾN LƯỢC: {presentation_format or angle}\n{f'🛑 CHỈ THỊ ƯU TIÊN SỐ 1 TỪ NGƯỜI DÙNG: {custom_note}' if custom_note else ''}\n{COMPACT_CORE_RULES}\n- 5 kịch bản = 5 bối cảnh đời thực khác nhau khớp sản phẩm & sự kiện.\n- Diễn viên: {char_rules}"

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction, num_chars, character_profiles, custom_note="", presentation_format="", self_pronoun="em", audience_pronoun="các chị em", setting_archetype="", is_fixed_location=True, is_pas_story=False, forced_footwear="sneakers"):
    is_viral = ("Viral" in mode)
    pas_flow = "PAS Flow: Cảnh 1 tại nhà nêu nỗi đau (KHÔNG có SP) -> Cảnh 2,3,4 có SP làm TRỌNG TÂM TIỀN CẢNH giải quyết vấn đề." if is_pas_story else "Direct Flow: SP làm TRỌNG TÂM TIỀN CẢNH xuyên suốt 4 cảnh, Cảnh 2 nối mượt từ Cảnh 1."
    return f"ĐẠO DIỄN TIKTOK PRO | Xưng '{self_pronoun}' - Gọi '{audience_pronoun}' | {pas_flow}\n{f'🛑 CHỈ THỊ ƯU TIÊN SỐ 1 TỪ NGƯỜI DÙNG (BẮT BUỘC TUÂN THỦ TUYỆT ĐỐI): {custom_note}' if custom_note else ''}\n{COMPACT_CORE_RULES}\n- FOOTWEAR LOCK: Bắt buộc yêu cầu AI đi giày dép theo định hướng: {forced_footwear}.\n- Cảnh 4: {'Kêu gọi thảo luận & follow (không bán hàng)' if is_viral else 'Chốt deal chuẩn quy tắc'}."

# ==============================================================================
# 9. LOGIC KỊCH BẢN CHÍNH (CREATE DETAILS, CLONE, EXPAND)
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

    fixed_title, fixed_hook = outline.get('title', 'Kịch bản chi tiết'), clean_and_normalize_voiceover(outline.get('hook', ''))
    fixed_setting_base = outline.get('setting', 'Không gian thực tế phù hợp')
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

    check_str = f"{raw_prod_name} {fixed_title} {fixed_hook} {user_custom_note} {dna.get('what_and_unique', '')}"
    intimate_type = detect_intimate_apparel(check_str)
    is_footwear_accessory = detect_footwear_or_accessory(check_str)
    is_fashion_wearable = detect_wearable_fashion(check_str) and intimate_type == "normal" and not is_footwear_accessory
    is_single_skirt_mode = detect_single_tube_skirt(check_str)
    is_strict_appliance = detect_strict_rigid_appliance(check_str) and not is_fashion_wearable
    is_long_handle = detect_long_handle_tool(check_str + " " + ai_product_visual_en)
    
    is_food = detect_food(check_str)
    is_cosmetics = detect_cosmetics(check_str)
    is_mom_baby = detect_mom_baby(check_str)
    is_mom_baby_hard = detect_mom_baby_hard_props(check_str)
    is_medicine = detect_medicine(check_str)
    
    is_flashsale_script = any(k in f"{fixed_title} {fixed_hook} {presentation_format}".lower() for k in ["flash sale", "săn deal", "deal hời", "giảm sốc", "ưu đãi sốc"])
    
    ai_koc_data = dna.get("koc_demographic_analysis", {})
    detected_gender, detected_demographic_en = get_demographics_description(char_profiles, ai_koc_data.get("persona_en", "") if isinstance(ai_koc_data, dict) else "", ai_koc_data.get("body_and_hair_en", "") if isinstance(ai_koc_data, dict) else "", is_mom_baby)

    base_prod_en = f"{locked_color_en} seamless comfort fabric garment" if intimate_type == "underwear_bra" else (ai_product_visual_en if ai_product_visual_en else f"{raw_prod_name}")
    clean_prod_en = sanitize_third_party_ip(base_prod_en)
    if is_single_skirt_mode: clean_prod_en = enforce_single_tube_skirt_syntax(clean_prod_en)
    elif not is_fashion_wearable and not is_food and not is_cosmetics: clean_prod_en = re.sub(r'\b(?:foldable|collapsible|folding)\b', 'rigid structured', clean_prod_en, flags=re.IGNORECASE)

    dim_tag = f" ({dimensions_str})" if dimensions_str and len(dimensions_str) < 25 else ""
    
    color_lock_tag = f"[STRICT VISUAL LOCK: The product MUST strictly maintain {locked_color_en}, preserving exact original patterns/textures from reference, completely ignoring other colored variants]"
    
    stylist_rules_text = build_multi_industry_stylist_rules(clean_prod_en, hero_color_str, fixed_setting_base, detected_gender, intimate_type, is_fashion_wearable, check_str, is_food, is_cosmetics, is_mom_baby, is_medicine)
    footwear_match = re.search(r'Footwear:\s*([^|]+)', stylist_rules_text)
    forced_footwear = footwear_match.group(1).strip() if footwear_match else "clean minimalist white sneakers"

    action_scene_1, action_scene_2, action_scene_3, action_scene_4 = get_action_templates_by_industry(clean_prod_en, check_str, is_fashion_wearable, is_strict_appliance, is_long_handle, is_food, is_cosmetics, is_mom_baby, is_medicine)
    scene_4_vo_guide = f"Bình thường khoảng {soft_orig_price}, nay giảm chỉ còn khoảng {soft_sale_price} thôi, nhưng giá từng thời điểm có thể khác nhau tùy đợt ưu đãi, {audience_pronoun} cứ bấm góc trái kiểm tra tài khoản mình xem nhé!" if is_flashsale_script else f"Nay hãng đang có giá ưu đãi cực sâu, {audience_pronoun} nào mà đang gặp tình trạng khó chịu như trên thì rinh ngay em nó ở giỏ hàng góc trái nhé!"
    scene_1_action_inst = "speaking actively from 0.0s while physically demonstrating the SPECIFIC physical problem mentioned in the hook (e.g., vigorously scratching a red itchy rash on skin, struggling to pull up slipping socks from shoes, looking into a filthy washing machine drum) - EMPTY HANDS, ZERO PRODUCT" if is_pas_story else f"{action_scene_1} (under 18 words)"

    prompt_text = f"""
    TÊN SẢN PHẨM TIẾNG VIỆT (DÙNG CHO 'voiceover'): {raw_prod_name} (Màu/Họa tiết gốc: {hero_color_str})
    MÔ TẢ TIẾNG ANH (CHỈ DÙNG CHO 'action_en'): {clean_prod_en}. (LƯU Ý: Phải mô tả chính xác kết cấu quai xách/dây đeo nếu có. Ép buộc KHÔNG CÓ tay cầm phụ bên hông 'NO side handles' để chống AI tự vẽ thêm).
    Nỗi đau: {dna.get('pain_points', '')} | Công năng: {dna.get('how_to_use', '')}
    Kịch bản #{target_id}: '{fixed_title}' | Hook: '{fixed_hook}' | Bối cảnh gốc: '{fixed_setting_base}'
    GHI CHÚ BẮT BUỘC: '{user_custom_note if user_custom_note else 'none'}'
    KOC: {detected_demographic_en} | {stylist_rules_text}

    TRẢ VỀ JSON GỌN (LƯU Ý: 'voiceover' 100% Tiếng Việt thuần túy, CẤM chèn dấu chấm lửng (...), dấu gạch ngang (-), ngoặc vuông/tròn vào lời thoại để chống vấp máy đọc):
    {{
        "title": "{fixed_title}",
        "master_setting_en": "Mô tả tiếng Anh chi tiết chung cho CẢ 4 CẢNH (VD: 'messy bathroom with wet tile floor' hoặc 'clean modern kitchen'). Bắt buộc chỉ trả 1 mô tả duy nhất để dùng chung.",
        "wardrobe_lock": {{
            "outfit_vi": "Set đồ Stylist tiếng Việt",
            "master_character_en": "Detailed English lock MUST INCLUDE: {detected_demographic_en}, [hair style], [top], [bottom], wearing {forced_footwear}, [jewelry]. MUST BE EXACTLY THE SAME FOR ALL 4 SCENES."
        }},
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention",
                "setting": "Bối cảnh mở màn tiếng Việt...",
                "expression_en": "{'frustrated and troubled expression' if is_pas_story else 'lively, engaging expression'}",
                "action_en": "{scene_1_action_inst} (under 25 words)",
                "sfx": "Foley thực tế (không nhạc)",
                "director": "Attention | {'Trực tiếp mô tả hình ảnh nỗi đau vật lý' if is_pas_story else 'Đưa sản phẩm ra tiền cảnh'}",
                "voiceover": "Thoại mở màn 100% tiếng Việt tự nhiên (18-30 từ)..."
            }},
            {{
                "scene": 2, "aida_stage": "Interest",
                "setting": "Bối cảnh thực tế...",
                "expression_en": "relieved, confident and enthusiastic",
                "action_en": "{action_scene_2} (under 20 words)",
                "sfx": "Tiếng thao tác thực tế",
                "director": "Interest | Giữ đúng tỷ lệ sản phẩm + Cầu nối 3 nhánh",
                "voiceover": "Thoại Cảnh 2 100% tiếng Việt (22-34 từ)..."
            }},
            {{
                "scene": 3, "aida_stage": "Desire",
                "setting": "Bối cảnh đồng bộ...",
                "expression_en": "smiling contentedly with approving nod",
                "action_en": "{action_scene_3} (under 20 words)",
                "sfx": "Tiếng trải nghiệm thực tế",
                "director": "Desire | Thao tác cận cảnh không biến dạng sản phẩm",
                "voiceover": "Thoại Cảnh 3 100% tiếng Việt (20-34 từ)..."
            }},
            {{
                "scene": 4, "aida_stage": "Action",
                "setting": "Bối cảnh kết thúc...",
                "expression_en": "smiling warmly with open-palm gesture",
                "action_en": "{action_scene_4} (under 18 words)",
                "sfx": "Tiếng chuông ting nhẹ",
                "director": "Action | Giữ sản phẩm nổi bật ở tiền cảnh & Chốt deal",
                "voiceover": "{scene_4_vo_guide}"
            }}
        ]
    }}
    """
    sys_inst = get_sys_inst_details(current_active_mode, "Điện Ảnh Chân Thực", "On-camera", char_rules, "Max 10s", 1, char_profiles, user_custom_note, presentation_format, self_pronoun, audience_pronoun, fixed_setting_base, True, is_pas_story, forced_footwear)
    res = call_gemini([prompt_text], sys_inst, max_tokens=4096)
    scenes = res.get("scenes") or res.get("script") or []
    if not scenes: raise Exception("AI không tạo được danh sách phân cảnh. Vui lòng bấm tạo lại.")
    
    master_setting_en = sanitize_third_party_ip(res.get("master_setting_en", "clean minimalist modern setting")).strip().rstrip('.')
    
    w_lock = res.get("wardrobe_lock", {})
    locked_character_prompt = sanitize_third_party_ip(w_lock.get("master_character_en") or f"Fictional everyday {detected_demographic_en} (synthetic AI persona), wearing smart-casual coordinated outfit, wearing {forced_footwear}").strip().rstrip('.')
    if is_single_skirt_mode: locked_character_prompt = enforce_single_tube_skirt_syntax(locked_character_prompt)
    if not is_fashion_wearable: locked_character_prompt += ", standing completely still with zero body rotation"
    
    final_outfit_vi = w_lock.get("outfit_vi") or "Trang phục Stylist đồng bộ 4 cảnh"

    anti_drop_neg = "dropping product, falling object, letting go of object, slipping, throwing, "
    skirt_neg_extra = "split-leg pants, bifurcated trousers, two separate pant legs, divided culottes, " if is_single_skirt_mode else ""
    
    # 🌟 CẬP NHẬT: Lớp Khiên Chống Mọc Tay Cầm / Biến Dạng Cấu Trúc
    anti_morph_neg = "extra handles, hallucinated side handle, mug handle, changing straps, changing shape, deforming geometry, "
    appliance_neg_extra = "hallucinated parts, extra handles, extra spouts, modified shape, changing proportions, warped structure, " if (is_strict_appliance and not is_food and not is_cosmetics) else ""
    color_neg_extra = "multiple product colors, mixed colors, wrong product color, different colored variants, solid flat color overriding pattern, missing original pattern, "
    
    base_neg_prompt = f"{anti_morph_neg}{anti_drop_neg}{skirt_neg_extra}{appliance_neg_extra}{color_neg_extra}changing background, changing room, different room, changing clothes, changing shoes, different face, different hair, changing outfit, inconsistent wardrobe, oversized product, giant product, massive brush, huge handle, product larger than human, out of scale, disproportionate scale, incorrect proportions, product out of focus, blurry product, tiny product in background, camera zooming on face instead of product, morphing product, deforming geometry, melting plastic, folding/collapsing glitch, inconsistent product color, grey parts on white product, duplicate garment in hands, extra fingers, deformed hands, floating objects, nsfw, nudity, cleavage, text, watermark, subtitles, UI elements, background music, bgm, singing, fire, sparks, flames, smoke, plasma, glowing magic aura, visible wind lines, macro close up"
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
        
        env_lighting_en, env_sfx_en = extract_environmental_lighting_and_weather(vo_text, scn.get("setting", fixed_setting_base))
        is_pas_scn1_no_prod = (idx_scn == 0 and is_pas_story and not is_fashion_wearable)
        cam_shot = get_product_centric_camera_shot(idx_scn, is_fashion_wearable, is_footwear_accessory, is_pas_scn1_no_prod, clean_prod_en, is_strict_appliance, is_long_handle, is_food, is_cosmetics, is_mom_baby, is_medicine)
        
        base_sfx = re.sub(r'\b(?:music|soundtrack|melody|song|bgm)\b', 'Foley', scn.get("sfx", "Natural Foley"), flags=re.IGNORECASE)
        scn["sfx"] = f"{base_sfx}, {env_sfx_en}" if env_sfx_en else base_sfx
        
        micro_expr = sanitize_third_party_ip(scn.get("expression_en", "natural engaging expression")).strip().rstrip('.')
        clean_act = sanitize_destructive_motion_verbs(sanitize_third_party_ip(re.sub(r'^(?:Character\s+(?:is\s+)?|Subject\s+(?:is\s+)?)', '', scn.get("action_en") or action_scene_2, flags=re.IGNORECASE).strip()).rstrip('.'), is_fashion=is_fashion_wearable, is_food=is_food)
        if is_single_skirt_mode: clean_act = enforce_single_tube_skirt_syntax(clean_act)
        
        is_testing_scene = (idx_scn in [1, 2])
        if (is_fashion_wearable or is_footwear_accessory) and is_testing_scene:
            if not clean_act.lower().startswith("standing"):
                clean_act = f"standing completely still, {clean_act}"
        elif not is_fashion_wearable and not is_pas_scn1_no_prod:
            if not clean_act.lower().startswith("standing"):
                clean_act = f"standing completely still with zero body rotation, {clean_act}"

        if (is_fashion_wearable or is_footwear_accessory) and is_testing_scene:
            scene_physics = "Physical demonstration physics: hands firmly gripping the product, showing material details up close, applying force to stretch or bend without deforming its core structure. NEVER dropping."
        else:
            scene_physics = get_universal_physics_rules(clean_prod_en, vo_text, is_fashion=is_fashion_wearable, is_appliance=is_strict_appliance, is_long_handle=is_long_handle, is_food=is_food, is_cosmetics=is_cosmetics, is_mom_baby=is_mom_baby, is_medicine=is_medicine, is_mom_baby_hard=is_mom_baby_hard)

        color_lock_tag = f"[STRICT VISUAL LOCK: The product MUST strictly maintain {locked_color_en}, preserving exact original patterns/textures from reference, completely ignoring other colored variants]"
        
        if is_strict_appliance or is_mom_baby_hard: 
            locked_product_prompt_segment = f"STRICT REFERENCE APPLIANCE: {clean_prod_en}. {color_lock_tag}. Maintaining 100% identical shape, proportions, and surface details. Zero hallucinated parts."
        elif is_food or is_cosmetics or is_mom_baby or is_medicine: 
            locked_product_prompt_segment = f"PRODUCT FOCUS: {clean_prod_en}. {color_lock_tag} as the main subject."
        elif (is_fashion_wearable or is_footwear_accessory) and is_testing_scene:
            locked_product_prompt_segment = f"PRODUCT TESTING FOCUS: {clean_prod_en}. {color_lock_tag}. The product is held securely in hands for close-up physical demonstration (NOT worn on body)."
        else: 
            if is_fashion_wearable:
                locked_product_prompt_segment = f"Garment Lock: wearing {clean_prod_en}. {color_lock_tag} directly on body."
            elif is_footwear_accessory and any(k in clean_prod_en.lower() for k in ["sock", "shoe", "boot", "sandal", "sneaker", "tights", "footwear", "tất", "vớ"]):
                locked_product_prompt_segment = f"Footwear Lock: wearing {clean_prod_en}. {color_lock_tag} directly on feet."
            else:
                locked_product_prompt_segment = f"HERO PRODUCT CENTERPIECE: {clean_prod_en}{dim_tag} occupying foreground center focus. {color_lock_tag} (100% rigid non-deforming geometry)."

        if is_pas_scn1_no_prod:
            img_core = f"[IDENTICAL SETTING]: {cam_shot}, {master_setting_en}, {env_lighting_en}. Subject: {locked_character_prompt}, {micro_expr}, {clean_act} (EMPTY HANDS, ZERO PRODUCT). [NOTE: DO NOT USE PRODUCT REFERENCE FOR THIS SCENE]"
        elif not is_fashion_wearable and idx_scn in [1, 2]:
            img_core = f"[IDENTICAL SETTING]: {cam_shot}, {master_setting_en}, {env_lighting_en}. [{locked_product_prompt_segment}]. Presenter in background: {locked_character_prompt}, {micro_expr}, {clean_act}"
        else:
            img_core = f"[IDENTICAL SETTING]: {cam_shot}, {master_setting_en}, {env_lighting_en}. [{locked_product_prompt_segment}]. Subject: {locked_character_prompt}, {micro_expr}, {clean_act}"

        scn["img_p"] = sanitize_third_party_ip(f"{img_core}, tack-sharp focus on product, photorealistic 8k --ar 9:16 --style raw --v 6.1")
        scn["img_neg"] = base_neg_prompt
        clean_vo_audio = clean_and_normalize_voiceover(re.sub(r'\.{2,}', '.', vo_text).strip())

        studio_audio_prompt = f"[AUDIO]: Studio-quality close-mic direct on-camera speech (zero room reverb, zero echo, NO off-screen narrator). Native Hanoi Vietnamese voice: \"{clean_vo_audio}\". Foley only [{scn['sfx']}], zero BGM, no text overlays."

        if is_pas_scn1_no_prod:
            raw_vid = f"[CAMERA & SETTING]: {cam_shot}, gimbal live-action, {master_setting_en}, {env_lighting_en}. [SUBJECT]: {locked_character_prompt}, {micro_expr}, {clean_act}. [TIMING ({dynamic_sec}s)]: 0.0s-{actual_speech}s accurate Vietnamese lip-sync; final {cushion_sec}s natural breathing nod. {studio_audio_prompt}"
        elif not is_fashion_wearable or ((is_fashion_wearable or is_footwear_accessory) and is_testing_scene):
            raw_vid = f"[PRODUCT-CENTRIC CAMERA & SETTING]: {cam_shot}, stable camera, {master_setting_en}, {env_lighting_en}. [{locked_product_prompt_segment}]. [PRODUCT ACTION & PHYSICS]: {clean_act}. {scene_physics} [PRESENTER]: {locked_character_prompt}, {micro_expr}. [TIMING ({dynamic_sec}s)]: 0.0s-{actual_speech}s accurate Vietnamese lip-sync while demonstrating the product in foreground; final {cushion_sec}s warm smile & nod. {studio_audio_prompt}"
        else:
            raw_vid = f"[CAMERA & SETTING]: {cam_shot}, gimbal live-action, {master_setting_en}, {env_lighting_en}. [SUBJECT]: {locked_character_prompt}, {micro_expr}. [{locked_product_prompt_segment}]. [ACTION & PHYSICS]: {clean_act}. {scene_physics} [TIMING ({dynamic_sec}s)]: 0.0s-{actual_speech}s accurate Vietnamese lip-sync; final {cushion_sec}s warm smile & nod. {studio_audio_prompt}"

        vid_parts = raw_vid.split('[AUDIO]:')
        if len(vid_parts) == 2: scn["vid_p"] = sanitize_veo3_prompt(vid_parts[0]) + "[AUDIO]:" + vid_parts[1]
        else: scn["vid_p"] = sanitize_veo3_prompt(raw_vid)
        scn["vid_neg"] = base_neg_prompt
        scn["is_no_product_scene"] = is_pas_scn1_no_prod
        
    res["scenes"] = scenes
    res["total_dur"] = f"Khoảng {int(total_sec)} giây"
    
    goal_badge = "🌟 <b>Định hướng:</b> Xây Kênh & Follow" if is_viral else "🛒 <b>Định hướng:</b> Chốt đơn TikTok Shop an toàn"
    cam_mode_badge = "👗 <b>Chế độ Quay (Wearable Fashion):</b> Lấy phom dáng và đường rũ vải làm trung tâm." if is_fashion_wearable else "🎯 <b>Chế độ Quay (Product-Hero Centerpiece):</b> Khóa camera tĩnh (stable shot), ép KOC đứng im (zero rotation), sản phẩm là trọng tâm tuyệt đối."
    
    industry_badges = []
    if is_pas_story: industry_badges.append("🎭 <b>Động lực học Nỗi đau (PAS):</b> Cảnh 1 tự động hiển thị trực quan thực trạng vật lý của nỗi đau (ngứa ngáy, lồng giặt bẩn, tuột tất...) kết hợp thoại từ 0.0s.")
    if is_fashion_wearable or is_footwear_accessory: industry_badges.append("🔥 <b>Cơ chế Khóa Lai Cải Tiến (Expanded Hybrid Engine):</b> Tự động lột/cởi sản phẩm ở <b>CẢ CẢNH 2 VÀ CẢNH 3</b> để chuyển sang chế độ cầm trên tay soi cận cảnh & test lực (kéo giãn, bẻ cong) chống ảo giác AI.")
    if is_footwear_accessory and any(k in clean_prod_en.lower() for k in ["sock", "shoe", "boot", "sandal", "sneaker", "tights", "footwear"]): industry_badges.append("🧦 <b>Động lực học Giày/Tất:</b> Máy quay chúi xuống (low-angle) soi trực tiếp bàn chân/cổ chân, KOC tự động xỏ tất/giày vào chân.")
    if is_food: industry_badges.append("🍔 <b>Động lực học F&B:</b> Khóa kết cấu mọng nước, hơi nóng, cấm ép khối cứng.")
    if is_cosmetics: industry_badges.append("💄 <b>Động lực học Mỹ phẩm:</b> Đã kích hoạt hiệu ứng bắt sáng, ép sản phẩm để lại vệt màu trên da/môi chân thực.")
    if is_mom_baby: industry_badges.append("👶 <b>Động lực học Mẹ & Bé (Bảo vệ TikTok):</b> Bắt buộc phải có NGƯỜI LỚN tương tác cùng em bé, tuyệt đối không để bé 1 mình.")
    if is_medicine: industry_badges.append("💊 <b>Động lực học Y tế (Chính sách):</b> Tự động gọt sạch các từ vi phạm ('chữa bệnh', 'cam kết'). Góc quay viên uống rõ nét, an toàn.")
    
    summary_lines = [
        f"⏱ <b>Thời lượng:</b> Khoảng {int(total_sec)}s (Tối đa 10s/cảnh) | 🎬 <b>Chiến lược:</b> {presentation_format}",
        f"🗣 <b>Nhân xưng:</b> '{self_pronoun}' - '{audience_pronoun}' | 🏙 <b>Bối cảnh Master (Đồng nhất 4 cảnh):</b> {fixed_setting_base} | {goal_badge}",
        f"{cam_mode_badge}",
        f"👗 <b>Khóa Diện mạo & Stylist Tối Ưu (Contextual Footwear Lock):</b> {final_outfit_vi} (Đã chốt chính xác giày dép khớp ngữ cảnh: Cấm đi dép lên văn phòng, tự động dùng Sneaker/Heel cho môi trường chuyên nghiệp).",
        f"🎨 <b>Khóa Họa tiết & Màu sắc (Pattern/Color Lock):</b> Ép loại bỏ hoàn toàn các màu tạp trong ảnh gốc, bảo tồn 100% họa tiết/màu của: {hero_color_str if hero_color_str else 'Chuẩn ảnh'} -> <code>{clean_prod_en} | {locked_color_en}</code>",
        f"✊ <b>Cơ Chế Chống Biến Dạng Cấu Trúc (Anti-Morphing Engine):</b> Đã khóa ép buộc KOC cầm sát vào thân gốc của sản phẩm. Tiêu diệt triệt để lỗi tự mọc tay cầm hông, tự làm méo quai xách.",
        f"🎙 <b>Lõi m thanh Studio (Studio-Quality Close-Mic):</b> Khử 100% tiếng vang phòng (Zero Reverb), cấm tuyệt đối giọng thuyết minh lồng tiếng (No narrator), dọn sạch ký tự đặc biệt chống vấp chữ.",
    ]
    if industry_badges: summary_lines.extend(industry_badges)
    if is_single_skirt_mode: summary_lines.append("👗 <b>Khóa Váy 1 Ống Rộng (Single Unsplit Skirt Tube Lock):</b> Đã chuyển đổi thành Maxi Skirt, chặn quần 2 ống trong Negative Prompt.")
    if is_long_handle: summary_lines.append("🧹 <b>Chống Sản Phẩm Khổng Lồ (Long-Handle Scale Lock):</b> Tự động phát hiện dụng cụ cán dài, chặn Macro Close-up, ép góc quay eo trở xuống để bảo toàn 100% tỷ lệ thực tế.")
    elif is_strict_appliance and not is_food and not is_cosmetics: summary_lines.append("🏠 <b>Khóa Tham Chiếu Đồ Gia Dụng (Strict Reference Appliance):</b> Bám sát 100% hình mẫu tham chiếu, khóa cứng hình học 3D, cấm làm to sản phẩm khổng lồ.")
    if any(k in f"{raw_prod_name} {user_custom_note}".lower() for k in ["máy sấy", "máy thổi", "quạt", "hút bụi"]): summary_lines.append("💨 <b>Cơ chế Vật lý Gió/Hút Bụi Tàng hình:</b> Kích hoạt hiệu ứng gió/hút rác thực tế, cấm tia lửa (sparks) và khói (smoke) trong Negative Prompt.")
    if user_custom_note and user_custom_note.lower() not in ["mặc định chuẩn", "không có"]: summary_lines.append(f"🎯 <b>Ghi chú riêng của người dùng:</b> {user_custom_note}")
    res["director_summary"] = "<br>".join(summary_lines)
    
    st.session_state.generated_details[str(target_id)] = res
    auto_save_current_session()

def clone_script(script_id):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if str(sc.get("id")) == str(script_id)), None)
    if not target: return []
    cur_len = len(all_combined)
    target_detail = st.session_state.generated_details.get(str(script_id), {})
    user_custom_note = target.get("custom_note") or st.session_state.get("current_input_context", "").strip()
    presentation_format = target.get("presentation_format") or st.session_state.get("last_presentation_format", "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng")
    
    original_voices = [f"- Cảnh {s.get('scene')}: \"{s.get('voiceover')}\"" for s in target_detail.get("scenes", [])] if "scenes" in target_detail else []
    full_voice_text = "\n".join(original_voices) if original_voices else f"- Hook: \"{target.get('hook', '')}\""

    dna = st.session_state.get("content_analysis") or {}
    prompt = f"""
    SP: {dna.get('what_and_unique', '')} | GỐC #{script_id}: '{target.get('title', '')}'
    THOẠI GỐC:\n{full_voice_text}
    NHIỆM VỤ: Nhân bản 5 biến thể giữ 90% cấu trúc, đổi 5 bối cảnh đời thực khác nhau. Xưng '{dna.get("self_pronoun", "em")}' - Gọi '{dna.get("audience_pronoun", "các chị em" if not ("Viral" in mode) else "mọi người")}'.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên biến thể 1", "setting": "Bối cảnh 1...", "hook": "Hook 1...", "actors": 1 }},
            {{ "id": {cur_len+2}, "title": "Tên biến thể 2", "setting": "Bối cảnh 2...", "hook": "Hook 2...", "actors": 1 }},
            {{ "id": {cur_len+3}, "title": "Tên biến thể 3", "setting": "Bối cảnh 3...", "hook": "Hook 3...", "actors": 1 }},
            {{ "id": {cur_len+4}, "title": "Tên biến thể 4", "setting": "Bối cảnh 4...", "hook": "Hook 4...", "actors": 1 }},
            {{ "id": {cur_len+5}, "title": "Tên biến thể 5", "setting": "Bối cảnh 5...", "hook": "Hook 5...", "actors": 1 }}
        ]
    }}
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, "Điện Ảnh Chân Thực", "On-camera", "", 1, "Nhân bản", user_custom_note, presentation_format), max_tokens=2500)
    clones = res.get("outlines", res.get("script_outlines", []))
    formatted_clones = []
    for idx, cl in enumerate(clones):
        formatted_clones.append({
            "id": cur_len + idx + 1, "title": cl.get("title", f"Biến thể #{cur_len + idx + 1}"),
            "setting": cl.get("setting", f"Bối cảnh #{idx+1}"), "hook": clean_and_normalize_voiceover(cl.get("hook", "")),
            "actors": 1, "character_profiles": target.get("character_profiles", st.session_state.get("character_profiles", [])),
            "duration_instruction": "Max 10s", "narrator_mode": "On-camera",
            "custom_note": user_custom_note, "presentation_format": presentation_format
        })
    return formatted_clones

def generate_more_scripts(unified_strategy_format, char_profiles, extra_note=""):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    cur_len = len(st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts)
    active_note = extra_note.strip() if extra_note.strip() else st.session_state.get("current_input_context", "").strip()
    active_format = unified_strategy_format if unified_strategy_format else st.session_state.get("last_presentation_format", "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng")
    dna = st.session_state.get("content_analysis") or {}
    
    prompt = f"""
    SP: {dna.get('what_and_unique', '')} | CHIẾN LƯỢC: '{active_format}' | Xưng '{dna.get("self_pronoun", "em")}' - Gọi '{dna.get("audience_pronoun", "các chị em" if not ("Viral" in mode) else "mọi người")}'.
    GHI CHÚ: '{active_note if active_note else "none"}'
    TẠO 5 KỊCH BẢN Ở 5 BỐI CẢNH ĐỜI THỰC KHÁC NHAU.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên kịch bản 1", "setting": "Bối cảnh 1...", "hook": "Hook 1...", "actors": 1 }},
            {{ "id": {cur_len+2}, "title": "Tên kịch bản 2", "setting": "Bối cảnh 2...", "hook": "Hook 2...", "actors": 1 }},
            {{ "id": {cur_len+3}, "title": "Tên kịch bản 3", "setting": "Bối cảnh 3...", "hook": "Hook 3...", "actors": 1 }},
            {{ "id": {cur_len+4}, "title": "Tên kịch bản 4", "setting": "Bối cảnh 4...", "hook": "Hook 4...", "actors": 1 }},
            {{ "id": {cur_len+5}, "title": "Tên kịch bản 5", "setting": "Bối cảnh 5...", "hook": "Hook 5...", "actors": 1 }}
        ]
    }}
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, "Điện Ảnh Chân Thực", "On-camera", generate_char_rules_string(char_profiles), 1, active_format, active_note, active_format), max_tokens=2500)
    more_scripts = res.get("outlines", res.get("script_outlines", []))
    for idx, sc in enumerate(more_scripts):
        if "hook" in sc: sc["hook"] = clean_and_normalize_voiceover(sc["hook"])
        sc.update({
            "id": cur_len + idx + 1, "duration_instruction": "Max 10s", 
            "narrator_mode": "On-camera", "character_profiles": char_profiles, "actors": 1,
            "custom_note": active_note, "presentation_format": active_format
        })
    return more_scripts

# ==============================================================================
# 10. GIAO DIỆN THANH BÊN (SIDEBAR) & QUẢN TRỊ ADMIN
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        tabs = st.tabs(["🔐 Đăng Nhập", "🚀 Đăng Ký"])
        with tabs[0]:
            with st.form("login_form", border=False):
                email_input = st.text_input("Email:", key="f_login_email")
                pass_input = st.text_input("Mật khẩu:", type="password", key="f_login_pass")
                submit_login = st.form_submit_button("🔑 Đăng Nhập", type="primary", use_container_width=True)
                if submit_login:
                    email_c, pass_c = email_input.strip(), pass_input.strip()
                    if email_c in st.session_state.licensed_accounts and st.session_state.licensed_accounts[email_c].get("password") == pass_c:
                        st.session_state.licensed_accounts[email_c]["active_session_id"] = st.session_state.session_id
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
                    if email_r and phone_r and pass_r and is_valid_phone(phone_r) and email_r not in st.session_state.licensed_accounts:
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
            
        st.session_state.active_project_title = st.text_input("Tên dự án hiện tại:", value=st.session_state.active_project_title, disabled=is_system_busy)
        if st.session_state.get("last_autosave_time"):
            st.markdown(f"<div class='autosave-badge'>☁️ Đã tự động lưu lúc {st.session_state.last_autosave_time}</div>", unsafe_allow_html=True)

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
            new_title = f"{st.session_state.active_project_title} (Bản sao)"
            success, msg = save_project_to_db(st.session_state.current_email, new_title, payload, project_id=None)
            if success: 
                st.session_state.active_project_title = new_title
                st.toast("✅ Đã lưu thành dự án mới độc lập!"); st.rerun()
            else: st.error(f"❌ {msg}")
        
        st.markdown("---")
        st.markdown("### 📂 KHO DỰ ÁN")
        is_admin_user = (st.session_state.current_email == ADMIN_EMAIL)
        
        if supabase:
            try:
                if is_admin_user:
                    res = supabase.table("saved_projects").select("id, project_title, user_email, created_at").order("created_at", desc=True).limit(50).execute()
                else:
                    res = supabase.table("saved_projects").select("id, project_title, user_email, created_at").eq("user_email", st.session_state.current_email).order("created_at", desc=True).limit(30).execute()
                all_projects = res.data or []
            except: all_projects = []

            if is_admin_user and all_projects:
                creator_emails = sorted(list(set(p.get("user_email", "") for p in all_projects if p.get("user_email"))))
                sel_creator = st.selectbox("👤 Lọc theo thành viên:", ["Tất cả thành viên"] + creator_emails, key="admin_sel_creator", disabled=is_system_busy)
                if sel_creator != "Tất cả thành viên": all_projects = [p for p in all_projects if p.get("user_email") == sel_creator]

            search_proj = st.text_input("🔍 Tìm kiếm dự án:", placeholder="Nhập tên dự án...", key="search_proj_input", disabled=is_system_busy)
            display_projects = [p for p in all_projects if search_proj.strip().lower() in p['project_title'].lower()] if search_proj.strip() else (all_projects if st.session_state.show_all_projects else all_projects[:3])

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
                    if st.session_state.show_all_projects:
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
            other_accs = [item for item in st.session_state.licensed_accounts.items() if item[0] != ADMIN_EMAIL]
            filt_accs = [item for item in other_accs if search_acc.strip().lower() in item[0].lower() or search_acc.strip() in item[1].get('phone', '')] if search_acc.strip() else (other_accs if st.session_state.show_all_admin_accounts else other_accs[:3])

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
                if st.session_state.show_all_admin_accounts:
                    if st.button("🔼 Thu gọn danh sách tài khoản", use_container_width=True, disabled=is_system_busy):
                        st.session_state.show_all_admin_accounts = False; st.rerun()
                else:
                    if st.button(f"🔽 Xem thêm {len(other_accs)-3} tài khoản", use_container_width=True, disabled=is_system_busy):
                        st.session_state.show_all_admin_accounts = True; st.rerun()

        st.markdown("---")
        st.markdown("""<div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:1.5px solid #86efac;border-radius:12px;padding:10px;text-align:center;margin-bottom:10px;"><div style="font-size:13px;font-weight:800;color:#15803d;">🎧 HỖ TRỢ TRỰC TIẾP (ZALO/HOTLINE)</div><div style="font-size:18px;font-weight:900;color:#991b1b;margin-top:4px;">0869 628 316</div></div>""", unsafe_allow_html=True)
        u_info = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        u_plan = u_info.get("plan_type", "Trial")
        u_used = u_info.get("daily_usage_count", 0) if u_info.get("last_generation_date") == datetime.now().strftime("%Y-%m-%d") else 0
        u_lim = "Không giới hạn" if u_plan == "VIP" else (20 if u_plan == "Advanced" else (10 if u_plan == "Basic" else 3))
        st.info(f"**GÓI {u_plan.upper()}**\n\n• Email: {st.session_state.current_email}\n• Đã tạo: **{u_used}/{u_lim}**\n• Hạn dùng: {u_info.get('expires_at')}")
        if st.button("🚪 Đăng Xuất", disabled=is_system_busy): 
            st.session_state.is_logged_in = False; st.rerun()

if not st.session_state.is_logged_in: st.info("👈 Vui lòng đăng nhập ở thanh bên."); st.stop()

# ==============================================================================
# 11. KHÔNG GIAN SÁNG TẠO CHÍNH (MAIN APP UI)
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Đạo Diễn AI - Hệ Thống Kịch Bản Pro</div></div>""", unsafe_allow_html=True)

user_allowed_modules = st.session_state.licensed_accounts.get(st.session_state.current_email, {}).get("roles", ALL_MODULES) or ALL_MODULES
mode = st.selectbox("🎯 Thể loại:", user_allowed_modules, key=f"mode_sel_{st.session_state.reset_key}", disabled=is_system_busy)
is_viral_mode = "Viral" in mode

up_files, custom_note = [], ""
viral_persona, viral_topic = "", ""

if not st.session_state.is_analyzed:
    if is_viral_mode:
        col_v1, col_v2 = st.columns(2)
        viral_persona = col_v1.text_input("👤 Định vị Kênh:", placeholder="Ví dụ: Mẹ bỉm sữa thông thái...", key=f"viral_persona_{st.session_state.reset_key}", disabled=is_system_busy)
        viral_topic = col_v2.text_area("💡 Chủ đề / Mẹo:", height=68, placeholder="Ví dụ: 3 mẹo setup góc làm việc gọn gàng...", key=f"viral_topic_{st.session_state.reset_key}", disabled=is_system_busy)
        up_files = st.file_uploader("📦 Upload Ảnh:", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_viral_{st.session_state.reset_key}", disabled=is_system_busy)
        if up_files:
            with st.expander(f"👁 Xem lại {len(up_files)} ảnh đã tải lên", expanded=False):
                n_cols = min(len(up_files), 4)
                cols = st.columns(n_cols)
                for idx, f in enumerate(up_files): cols[idx % n_cols].image(f, caption=f"Ảnh {idx + 1}", use_container_width=True)
        custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất - ví dụ: quần là dạng váy 1 ống rộng):", key=f"custom_note_viral_{st.session_state.reset_key}", disabled=is_system_busy)
        hero_sku_override = ""
    else:
        products_data = supabase.table("products").select("*").execute().data if supabase else []
        if products_data:
            selected_name = st.selectbox("📌 Chọn sản phẩm:", [p["product_name"] for p in products_data], key=f"prod_select_{st.session_state.reset_key}", disabled=is_system_busy)
            st.session_state.current_product_data = next(p for p in products_data if p["product_name"] == selected_name)
        col_f1, col_f2 = st.columns([2, 1])
        up_files = col_f1.file_uploader("📦 Upload Ảnh SP (Quét OCR Giá, Hero SKU & Bảng màu):", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_prod_{st.session_state.reset_key}", disabled=is_system_busy)
        hero_sku_override = col_f2.text_input("🎯 Màu / SKU ưu tiên (Tùy chọn):", placeholder="Ví dụ: Trắng tinh...", key=f"hero_override_{st.session_state.reset_key}", disabled=is_system_busy)
        if up_files:
            with st.expander(f"👁 Xem lại {len(up_files)} ảnh sản phẩm đã tải lên", expanded=False):
                n_cols = min(len(up_files), 4)
                cols = st.columns(n_cols)
                for idx, f in enumerate(up_files): cols[idx % n_cols].image(f, caption=f"Ảnh {idx + 1}", use_container_width=True)
        custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất - ví dụ: quần là dạng váy 1 ống rộng):", key=f"custom_note_prod_{st.session_state.reset_key}", disabled=is_system_busy)

    style = "Điện Ảnh Chân Thực"
    col_strat, col_role, col_actor_img = st.columns([1.4, 1.6, 1.0])
    unified_strategy_format = col_strat.selectbox("🧭 Chiến lược & Hình thức Video:", UNIFIED_STRATEGY_FORMAT_OPTS, index=0, key=f"unified_strat_format_{st.session_state.reset_key}", disabled=is_system_busy)
    role_input = col_role.text_input("👤 Vai trò NV (Để trống = AI tự phân tích):", value="", placeholder="Ví dụ: Nam 25t...", key=f"r_0_{st.session_state.reset_key}", disabled=is_system_busy)
    c_file = col_actor_img.file_uploader("📸 Ảnh mẫu NV (Tùy chọn):", type=["jpg", "png"], key=f"f_0_{st.session_state.reset_key}", disabled=is_system_busy)

    char_inputs = [{"id": 1, "role": role_input.strip(), "file": c_file}] if (c_file or role_input.strip()) else []

    if st.button("🚀 Phân Tích Sản Phẩm Và Tạo Kịch Bản", type="primary", use_container_width=True, disabled=is_system_busy):
        can_run, msg = check_usage_limit(st.session_state.current_email)
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
    args = st.session_state.temp_main_args
    with st.spinner("⏳ Đạo diễn AI đang phân tích sản phẩm, tạo 5 kịch bản & tự động lưu dự án theo tên sản phẩm..."):
        try:
            char_inputs = []
            if args.get("avatar_file") or args.get("role_input"):
                char_inputs.append({"id": 1, "role": args["role_input"], "file_bytes": args["avatar_file"]})
            
            st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs] if char_inputs else [{"id": 1, "role": ""}]
            char_rules = generate_char_rules_string(st.session_state.character_profiles)
            st.session_state.update({
                "last_mode": mode, "last_style": "Điện Ảnh Chân Thực", "last_narrator": "On-camera", 
                "last_presentation_format": args["unified_strategy_format"],
                "current_input_context": args["custom_note"]
            })
            
            if is_viral_mode:
                st.session_state.current_product_data_saved = {"channel_persona": args["viral_persona"], "topic_or_tips": args["viral_topic"]}
                input_context_str = f"KÊNH: '{args['viral_persona']}' | CHỦ ĐỀ: '{args['viral_topic']}' | NOTE: '{args['custom_note']}'"
            else:
                st.session_state.current_product_data_saved = st.session_state.get("current_product_data", {})
                input_context_str = f"SP: {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)} | NOTE: '{args['custom_note']}'"
            
            st.session_state["saved_reference_images"] = args["temp_images"]

            override_instruction = f"Khóa màu/Họa tiết Hero SKU: '{args['hero_sku_override']}'. NẾU CÓ NHIỀU MÀU TRONG ẢNH, CHỈ GIỮ LẠI ĐÚNG MÀU/HỌA TIẾT NÀY!" if args['hero_sku_override'] else "Ưu tiên SKU có icon 🔥/Hot. NẾU ẢNH CÓ HỌA TIẾT, BẮT BUỘC PHẢI MÔ TẢ CHI TIẾT HỌA TIẾT. NẾU ẢNH CÓ NHIỀU MÀU, CHỈ CHỌN 1 MÀU DUY NHẤT ĐỂ KHÓA, BỎ QUA CÁC MÀU KHÁC!"
            skirt_note_rule = "ĐẶC BIỆT: Ghi chú có yêu cầu 'quần dạng váy 1 ống / quần váy', trong 'product_visual_en' BẮT BUỘC mô tả là 'full-length A-line maxi skirt (single unified unsplit skirt tube, zero leg division)', TUYỆT ĐỐI CẤM dùng từ 'pants' hoặc 'trousers'!" if detect_single_tube_skirt(args["custom_note"]) else ""

            prompt = f"""
            INPUT: {input_context_str} | THỂ LOẠI: '{mode}' | CHIẾN LƯỢC: '{args["unified_strategy_format"]}'
            HERO SKU: {override_instruction}
            {skirt_note_rule}
            - Tách biệt 100% SP khỏi người mẫu gốc trong ảnh. Tự thiết kế KOC người Việt phù hợp ('koc_demographic_analysis') & phối đồ Stylist ('stylist_coordination_vi').
            - MÔ TẢ ĐÚNG VẬT LÝ SẢN PHẨM: Cần miêu tả chi tiết vị trí tay cầm (nếu có, VD: top flexible strap). Nếu không có tay cầm phụ, bắt buộc ghi 'NO side handles' để chặn AI tự vẽ thêm. 

            TRẢ VỀ JSON:
            {{
                "content_analysis": {{
                    "self_pronoun": "em",
                    "audience_pronoun": "anh em / các chị em",
                    "setting_archetype": "Bối cảnh chuẩn mực đời thực",
                    "is_fixed_location": true,
                    "koc_demographic_analysis": {{
                        "gender": "male hoặc female",
                        "persona_vi": "Mô tả KOC người Việt: tuổi, vóc dáng, làn da, kiểu tóc",
                        "persona_en": "25yo Vietnamese woman",
                        "body_and_hair_en": "slender figure, fair-warm skin, neat jet-black hair"
                    }},
                    "stylist_coordination_vi": "Set đồ Stylist đồng nhất 4 cảnh: Trang phục + Giày + Phụ kiện",
                    "how_to_use": "Thao tác sử dụng thực tế (giữ nguyên hình khối SP)",
                    "correct_ergonomic_grip": "Tư thế cầm nắm chuẩn",
                    "exact_original_price_ocr": "Giá gốc OCR",
                    "exact_sale_price_ocr": "Giá sale OCR",
                    "original_price_spoken": "giá gốc bằng chữ",
                    "sale_price_spoken": "giá sale bằng chữ",
                    "rounded_soft_original_spoken": "khoảng giá gốc",
                    "rounded_soft_sale_spoken": "khoảng giá sale",
                    "recommended_setting_en": "Clean modern setting under 12 words",
                    "target_audience": "Tệp khách hàng mục tiêu",
                    "core_value": "Giá trị cốt lõi",
                    "pain_points": "Nỗi đau thực tế",
                    "hook_element": "Yếu tố Hook 3s đầu",
                    "recommended_format": "Hình thức đề xuất",
                    "format_reason": "Lý do đề xuất",
                    "hero_sku_color": "Màu sắc/Họa tiết Hero SKU tiếng Việt (VD: Trắng họa tiết hoa)",
                    "hero_sku_color_en": "Exact English color and pattern (e.g., floral printed red, striped blue, or exact reference color)",
                    "product_visual_en": "Concise English product description under 18 words. MUST include specific handle/strap positions (e.g., top flexible strap, NO side handle) to prevent AI from hallucinating extra parts.",
                    "color_palette": "Bảng màu",
                    "what_and_unique": "[Tên SP]: [Điểm độc bản USP]",
                    "target_user": "Đối tượng phù hợp",
                    "why_buy": "Lý do nên mua",
                    "where_and_convenience": "Hoàn cảnh & tiện ích",
                    "product_dimensions": "Kích thước (VD: 47x28x17cm)",
                    "prompt_dna_lock": "Visual DNA lock"
                }},
                "outlines": [
                    {{ "id": 1, "title": "Tên kịch bản 1", "setting": "Bối cảnh 1...", "hook": "Câu hook 1...", "actors": 1 }},
                    {{ "id": 2, "title": "Tên kịch bản 2", "setting": "Bối cảnh 2...", "hook": "Câu hook 2...", "actors": 1 }},
                    {{ "id": 3, "title": "Tên kịch bản 3", "setting": "Bối cảnh 3...", "hook": "Câu hook 3...", "actors": 1 }},
                    {{ "id": 4, "title": "Tên kịch bản 4", "setting": "Bối cảnh 4...", "hook": "Câu hook 4...", "actors": 1 }},
                    {{ "id": 5, "title": "Tên kịch bản 5", "setting": "Bối cảnh 5...", "hook": "Câu hook 5...", "actors": 1 }}
                ]
            }}
            """
            payload = ["PRODUCT IMAGES (EXTRACT RIGID 3D STRUCTURE, EXACT HANDLES/STRAPS, TRUE COLOR, AND OCR PRICES - IGNORE HUMAN MODELS):"]
            for cb, cm in args["temp_images"]:
                payload.append(types.Part.from_bytes(data=cb, mime_type=cm))
            for c in char_inputs:
                if c.get("file_bytes"):
                    payload.extend([f"ACTOR {c['id']} (EXTRACT AGE, GENDER, HAIR ONLY):", types.Part.from_bytes(data=c["file_bytes"]["data"], mime_type=c["file_bytes"]["mime"])])
            payload.append(prompt)
            
            res = call_gemini(payload, get_sys_inst_outlines(mode, "Điện Ảnh Chân Thực", "On-camera", char_rules, 1, args["unified_strategy_format"], args["custom_note"], args["unified_strategy_format"]), max_tokens=4096)
            ca_result = res.get("content_analysis") or {}
            st.session_state.content_analysis = ca_result
            outlines = res.get("outlines", res.get("script_outlines", []))
            
            if not outlines: raise Exception("AI bị ngắt quãng do kết nối mạng. Vui lòng bấm tạo lại.")
            
            for o in outlines: 
                if "hook" in o: o["hook"] = clean_and_normalize_voiceover(o["hook"])
                o.update({
                    "duration_instruction": "Max 10s", 
                    "narrator_mode": "On-camera", 
                    "character_profiles": st.session_state.character_profiles, 
                    "actors": 1,
                    "custom_note": args["custom_note"],
                    "presentation_format": args["unified_strategy_format"]
                })
            
            auto_proj_title = extract_bold_product_title(ca_result, fallback_topic=args["viral_topic"])
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

ca = st.session_state.content_analysis
if isinstance(ca, dict):
    st.divider()
    col_hdr1, col_hdr2 = st.columns([2.5, 1.5])
    col_hdr1.markdown("### 🔍 **Phân Tích Chi Tiết**")
    if st.session_state.get("last_autosave_time"):
        col_hdr2.markdown(f"<div style='text-align:right;'><span class='autosave-badge'>☁️ Dự án: <b>{st.session_state.active_project_title}</b> (Đã tự động lưu {st.session_state.last_autosave_time})</span></div>", unsafe_allow_html=True)
    
    col_row1_left, col_row1_right = st.columns(2)
    with col_row1_left:
        st.markdown(clean_html(f"""
        <div class="dna-card">
            <div class="dna-card-title">🎯 1. Chân dung Khách hàng & Hook 3s (Attention)</div>
            <div class="dna-row"><span class="dna-label">👥 Tệp khách hàng:</span><span class="dna-text">{clean_analysis_text(ca.get('target_audience', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">💔 Nỗi đau thực tế:</span><span class="dna-text">{clean_analysis_text(ca.get('pain_points', ''))}</span></div>
            <div class="dna-row"><span class="dna-label" style="color:#d90429;">⚡ Yếu tố Hook 3s đầu:</span><span class="dna-text" style="color:#d90429; font-weight:600;">{clean_analysis_text(ca.get('hook_element', ''))}</span></div>
            <div class="dna-row"><span class="dna-label" style="color:#2563eb;">🎬 Chiến lược & Hình thức tối ưu:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{clean_analysis_text(ca.get('recommended_format', 'Review / Trải nghiệm'))}</span></div>
            <div class="dna-row"><span class="dna-label">💡 Lý do đề xuất:</span><span class="dna-text">{clean_analysis_text(ca.get('format_reason', ''))}</span></div>
        </div>"""), unsafe_allow_html=True)

    with col_row1_right:
        koc_persona_desc = ca.get('koc_demographic_analysis', {}).get('persona_vi', 'Tự động chọn KOC thuần Việt phù hợp') if isinstance(ca.get('koc_demographic_analysis'), dict) else 'Tự động chọn KOC'
        user_specified_actors = [p['role'] for p in st.session_state.get('character_profiles', []) if str(p.get('role', '')).strip()]
        koc_display_str = f"👤 <b>KOC:</b> {', '.join(user_specified_actors)} (Người dùng chỉ định)" if user_specified_actors else f"🤖 <b>KOC thuần Việt:</b> {koc_persona_desc}"
        stylist_coord_str = clean_analysis_text(ca.get('stylist_coordination_vi', 'Phối trang phục, giày dép & phụ kiện đồng bộ 4 cảnh'))
        locked_color_preview = translate_and_lock_color_en(ca.get('hero_sku_color', ''), ca.get('hero_sku_color_en', ''))
        pronoun_badge = f"🗣 <b>Nhân xưng:</b> KOC xưng <b>'{ca.get('self_pronoun', 'em')}'</b> - Gọi người xem là <b>'{ca.get('audience_pronoun', 'anh em / các bác')}'</b>"
        
        if is_viral_mode:
            st.markdown(clean_html(f"""
            <div class="dna-card">
                <div class="dna-card-title">🌟 2. Định Vị Kênh, Vóc Dáng KOC & Stylist</div>
                <div class="dna-row"><span class="dna-label">🎭 Chân dung KOC:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{koc_display_str}</span></div>
                <div class="dna-row"><span class="dna-label">👗 Stylist Phối đồ:</span><span class="dna-text" style="color:#7c3aed; font-weight:600;">{stylist_coord_str}</span></div>
                <div class="dna-row"><span class="dna-label">🗣 Nhân xưng chuẩn:</span><span class="dna-text" style="color:#15803d; font-weight:700;">{pronoun_badge}</span></div>
                <div class="dna-row"><span class="dna-label">💎 Giá trị cốt lõi:</span><span class="dna-text">{clean_analysis_text(ca.get('core_value', ''))}</span></div>
            </div>"""), unsafe_allow_html=True)
        else:
            st.markdown(clean_html(f"""
            <div class="dna-card">
                <div class="dna-card-title">🔥 2. KOC Thuần Việt, Stylist & Khóa Màu Sản Phẩm</div>
                <div class="dna-row"><span class="dna-label">🎭 Chân dung KOC:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{koc_display_str}</span></div>
                <div class="dna-row"><span class="dna-label">👗 Stylist Phối đồ:</span><span class="dna-text" style="color:#7c3aed; font-weight:600;">{stylist_coord_str}</span></div>
                <div class="dna-row"><span class="dna-label">⭐ Khóa màu/Họa tiết (4 cảnh):</span><span class="dna-text" style="color:#dc2626; font-weight:700;">{clean_analysis_text(ca.get('hero_sku_color', 'Tự động'))} ({locked_color_preview})</span></div>
                <div class="dna-row"><span class="dna-label">🗣 Nhân xưng chuẩn:</span><span class="dna-text" style="color:#15803d; font-weight:700;">{pronoun_badge}</span></div>
                <div class="dna-row"><span class="dna-label">🎨 Bảng màu SP:</span><span class="dna-text">{clean_analysis_text(ca.get('color_palette', ''))}</span></div>
            </div>"""), unsafe_allow_html=True)

    col_row2_left, col_row2_right = st.columns(2)
    with col_row2_left:
        st.markdown(clean_html(f"""
        <div class="dna-card">
            <div class="dna-card-title">💎 3. Giải phẫu Sản phẩm & Khóa Hình Học 3D (Anti-Morphing)</div>
            <div class="dna-row"><span class="dna-label">📦 Chủ đề & Điểm đặc biệt:</span><span class="dna-text">{format_product_name_bold(ca.get('what_and_unique', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">🧱 Khóa Hình Học 3D (Rigid Lock):</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{ca.get('product_visual_en', 'Chuẩn ảnh gốc')}</span></div>
            <div class="dna-row"><span class="dna-label">👥 Đối tượng phù hợp:</span><span class="dna-text">{clean_analysis_text(ca.get('target_user', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">🔥 Tại sao nên mua:</span><span class="dna-text">{clean_analysis_text(ca.get('why_buy', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">🛠 Thao tác chuẩn:</span><span class="dna-text">{clean_analysis_text(ca.get('how_to_use', ''))}</span></div>
        </div>"""), unsafe_allow_html=True)

    with col_row2_right:
        dim_txt_display = ca.get('product_dimensions', 'Chuẩn đời thực')
        loc_type_str = "Khóa Master (Đồng nhất 1 bối cảnh)" if ca.get('is_fixed_location', True) else "Chuyển cảnh theo mạch truyện (Dynamic)"
        if is_viral_mode:
            st.markdown(clean_html(f"""
            <div class="dna-card">
                <div class="dna-card-title">💡 4. Chuẩn Bối Cảnh Sự Kiện & Mẹo Đời Sống</div>
                <div class="dna-row"><span class="dna-label">🏙 Chuẩn bối cảnh sự kiện:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{clean_analysis_text(ca.get('setting_archetype', 'Sảnh chờ / Văn phòng'))}</span></div>
                <div class="dna-row"><span class="dna-label">📍 Cơ chế tọa độ:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{loc_type_str}</span></div>
                <div class="dna-row"><span class="dna-label">📐 Tỉ lệ thực tế:</span><span class="dna-text" style="color:#d97706; font-weight:600;">{dim_txt_display}</span></div>
                <div class="dna-row"><span class="dna-label" style="color:#15803d;">📣 Kêu gọi (CTA):</span><span class="dna-text" style="color:#15803d; font-weight:700;">Thảo luận, chia sẻ mẹo hay & Follow kênh</span></div>
            </div>"""), unsafe_allow_html=True)
        else:
            orig_p_display, sale_p_display = ca.get('original_price_spoken', ''), ca.get('sale_price_spoken', '')
            exact_orig_raw, exact_sale_raw = str(ca.get('exact_original_price_ocr', '')), str(ca.get('exact_sale_price_ocr', ''))
            soft_orig = ca.get('rounded_soft_original_spoken') or convert_to_soft_price_range(orig_p_display, is_orig=True, exact_raw_str=exact_orig_raw)
            soft_sale = ca.get('rounded_soft_sale_spoken') or convert_to_soft_price_range(sale_p_display, is_orig=False, exact_raw_str=exact_sale_raw)
            st.markdown(clean_html(f"""
            <div class="dna-card">
                <div class="dna-card-title">⚙ 4. Chuẩn Bối Cảnh Sự Kiện & Mức Giá</div>
                <div class="dna-row"><span class="dna-label">🏙 Chuẩn bối cảnh sự kiện:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{clean_analysis_text(ca.get('setting_archetype', 'Sảnh chờ tiệc cưới / Văn phòng'))}</span></div>
                <div class="dna-row"><span class="dna-label">📍 Cơ chế tọa độ:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{loc_type_str}</span></div>
                <div class="dna-row"><span class="dna-label">📐 Tỉ lệ thực tế:</span><span class="dna-text" style="color:#d97706; font-weight:700;">{dim_txt_display}</span></div>
                <div class="dna-row"><span class="dna-label">💰 Mức giá (OCR):</span><span class="dna-text">{format_ocr_prices(ca)}</span></div>
                <div class="dna-row"><span class="dna-label" style="color:#dc2626;">🎯 Mức giá (Nay giảm):</span><span class="dna-text" style="color:#dc2626; font-weight:700;">Bình thường {soft_orig}, nay giảm {soft_sale}</span></div>
            </div>"""), unsafe_allow_html=True)

all_sc = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
if all_sc:
    st.divider()
    def is_generated(sc_id): return (str(sc_id) in st.session_state.generated_details or sc_id in st.session_state.generated_details)

    comp_sc = [sc for sc in all_sc if is_generated(sc.get("id"))]
    pend_sc = [sc for sc in all_sc if not is_generated(sc.get("id"))]

    if st.session_state.active_script_id is not None:
        if st.button("🔼 Thu gọn kịch bản chi tiết", disabled=is_system_busy):
            st.session_state.active_script_id = None; st.rerun()
            
        active_id = st.session_state.active_script_id
        asc = st.session_state.generated_details.get(str(active_id), st.session_state.generated_details.get(active_id, {}))
        
        st.markdown("<div id='detailed-view-anchor'></div>", unsafe_allow_html=True)
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(asc.get('title', '')).upper()}**")
        
        director_summary_html = asc.get('director_summary', '')
        if not director_summary_html:
            total_sec = sum([float(str(s.get('dur', '8s')).replace('s', '')) for s in asc.get("scenes", [])])
            goal_badge = "🌟 <b>Định hướng:</b> Xây Kênh & Kéo Tương Tác / Follow" if is_viral_mode else "🛒 <b>Định hướng:</b> Chốt đơn TikTok Shop an toàn"
            cam_mode_badge = "🎯 <b>Chế độ Quay (Product-Hero Centerpiece):</b> Khóa tỷ lệ thực tế, cấm khổng lồ hóa sản phẩm."
            summary_lines = [
                f"⏱ <b>Thời lượng:</b> Khoảng {int(total_sec)}s (Tối đa 10s/cảnh)",
                f"🏙 <b>Bối cảnh sự kiện thông minh:</b> Khớp chuẩn sự kiện | {goal_badge}",
                f"{cam_mode_badge}",
                f"🔗 <b>Cầu nối Ngữ nghĩa 3 Nhánh:</b> Tự động khớp nối Cảnh 1 & Cảnh 2",
                f"🛡 <b>Bảo vệ Veo 3:</b> Đã gắn nhãn nhân vật hư cấu AI & lọc sạch từ khóa nhạy cảm"
            ]
            director_summary_html = "<br>".join(summary_lines)
        st.markdown(f"<div class='detail-header-box'>{director_summary_html}</div>", unsafe_allow_html=True)
        
        for idx, scn in enumerate(asc.get("scenes", []), 1):
            vo_text = clean_and_normalize_voiceover(scn.get('voiceover', ''))
            actual_words = count_words(vo_text)
            comma_count, period_count = vo_text.count(',') + vo_text.count(';'), vo_text.count('.') + vo_text.count('!') + vo_text.count('?')
            curr_mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
            is_tts = ("Viral" not in curr_mode)
            speech_sec = scn.get('actual_speech_sec', calculate_speech_duration(vo_text, is_tts))
            dur_int = int(str(scn.get('dur', '8s')).replace('s', ''))
            safe_cushion = round(max(0.0, dur_int - speech_sec), 1)
            
            st.markdown(f"#### 📍 Phân cảnh {idx} - Giai đoạn {scn.get('aida_stage')}")
            st.markdown(f"<span class='timing-badge'>⏱ Khung phân cảnh chuẩn: {scn.get('dur')} (Max 10s Veo 3) | Khớp nhịp đọc thực tế: ~{speech_sec}s ({actual_words} từ, {comma_count} phẩy, {period_count} ngắt | ~{round(actual_words/max(1.0, speech_sec), 1)} từ/s) | 🛡 Đệm diễn xuất tự nhiên: +{safe_cushion}s</span>", unsafe_allow_html=True)
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting')}*\n\n**😊 Vi biểu cảm & Cử chỉ:** *{scn.get('expression_en', 'Tự nhiên, rạng rỡ')}*\n\n**🎵 Hiệu ứng âm thanh (SFX & Foley thuần - Không nhạc nền):** *{scn.get('sfx', 'Âm thanh thực tế sống động')}*\n\n**🎙 Đạo diễn KOC:** *{scn.get('director')}*\n\n**💬 Thoại nhân vật nói trực tiếp on-camera từ 0.00s (100% Giọng Hà Nội chuẩn, dùng 'nghìn', số 4 đọc 'bốn'):** <div class='voiceover-text'>{vo_text}</div>", unsafe_allow_html=True)
            
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
                st.markdown("**🎥 Prompt Video Tinh Gọn (Veo 3 Pro - m thanh Studio, Chống Vấp Thoại):**")
                st.code(vid_p := scn.get('vid_p', ''), language="text")
                safe_copy_button(vid_p, f"📋 Sao Chép Prompt Video Cảnh {idx}")
            
            with st.expander(f"🛡 Negative Prompt Chuyên Biệt Cảnh {idx}", expanded=False):
                neg_val = scn.get('vid_neg', 'extra fingers, text, watermark, background music')
                st.code(neg_val, language="text")
                safe_copy_button(neg_val, f"📋 Sao Chép Negative Prompt Cảnh {idx}", custom_color="#475569")
            st.markdown("---")

    if comp_sc:
        st.markdown("### 🎬 **1. Kịch Bản ĐÃ Dựng Chi Tiết**")
        for outline in comp_sc:
            sc_id = outline["id"]
            with st.container(border=True):
                c1, c2, c3 = st.columns([2.5, 1, 1])
                c1.markdown(f"**#{sc_id}. {outline.get('title')}** <span class=badge-ready>ĐÃ LƯU</span>", unsafe_allow_html=True)
                c1.caption(f"⚡ *{clean_and_normalize_voiceover(outline.get('hook', ''))}*")
                if str(sc_id) != str(st.session_state.active_script_id):
                    if c2.button("👁 Xem lại", key=f"r_{sc_id}", use_container_width=True, disabled=is_system_busy):
                        st.session_state.active_script_id = int(sc_id)
                        st.session_state.scroll_to_detail = True
                        st.rerun()
                btn_clone_ph = c3.empty()
                if str(st.session_state.current_cloning_id) == str(sc_id):
                    if btn_clone_ph.button("🛑 Đang nhân bản... (Bấm để Hủy)", key=f"unhang_c_{sc_id}", type="secondary", use_container_width=True):
                        st.session_state.current_cloning_id = None; st.rerun()
                else:
                    if btn_clone_ph.button("🚀 Nhân bản", key=f"c_{sc_id}", type="primary", use_container_width=True, disabled=is_system_busy):
                        can_run, msg = check_usage_limit(st.session_state.current_email)
                        if can_run: st.session_state.current_cloning_id = sc_id; st.rerun()
                        else: st.error(msg)

    if pend_sc:
        st.markdown("### ⏳ **2. Kịch Bản Chờ Dựng**")
        for outline in pend_sc:
            sc_id = outline["id"]
            with st.container(border=True):
                c1, c2 = st.columns([3, 1.2])
                c1.markdown(f"**#{sc_id}. {outline.get('title')}** <span class=badge-pending>CHỜ DỰNG</span>", unsafe_allow_html=True)
                c1.caption(f"⚡ *{clean_and_normalize_voiceover(outline.get('hook', ''))}*")
                btn_detail_ph = c2.empty()
                if str(st.session_state.current_processing_id) == str(sc_id):
                    if btn_detail_ph.button("🛑 Đang dựng... (Bấm để Hủy kẹt)", key=f"unhang_p_{sc_id}", type="secondary", use_container_width=True):
                        st.session_state.current_processing_id = None; st.rerun()
                else:
                    if btn_detail_ph.button("✨ Tạo chi tiết ngay", key=f"cr_{sc_id}", type="secondary", use_container_width=True, disabled=is_system_busy):
                        can_run, msg = check_usage_limit(st.session_state.current_email, is_detailing=True)
                        if can_run: st.session_state.current_processing_id = sc_id; st.rerun()
                        else: st.error(msg)

    if st.session_state.current_processing_id is not None:
        target_id_to_run = st.session_state.current_processing_id
        success, error_msg = False, ""
        try:
            with st.spinner(f"⏳ Đang dựng nhanh kịch bản #{target_id_to_run} (Chống ảo giác Cấu trúc tay cầm)..."):
                create_scene_details(target_id_to_run, st.session_state.last_mode, "Điện Ảnh Chân Thực")
                st.session_state.active_script_id = int(target_id_to_run)
                success = True
        except Exception as e: error_msg = str(e)
            
        st.session_state.current_processing_id = None
        if success: 
            st.toast(f"✅ Đã dựng kịch bản #{target_id_to_run} & tự động lưu cập nhật vào dự án!")
            st.session_state.scroll_to_detail = True
            st.rerun()
        else: st.error(f"❌ Lỗi khi dựng kịch bản: {error_msg}")

    if st.session_state.current_cloning_id is not None:
        clone_id_to_run = st.session_state.current_cloning_id
        success, error_msg = False, ""
        try:
            with st.spinner(f"⏳ Đang nhân bản 5 biến thể cho kịch bản #{clone_id_to_run} & tự động lưu cập nhật..."):
                st.session_state.cloned_scripts.extend(clone_script(clone_id_to_run))
                auto_save_current_session()
                success = True
        except Exception as e: error_msg = str(e)
            
        st.session_state.current_cloning_id = None
        if success: 
            st.toast("✅ Đã nhân bản thành công 5 kịch bản voice bám sát gốc!")
            st.session_state.scroll_to_top = True
            st.rerun()
        else: st.error(f"❌ Lỗi khi nhân bản kịch bản: {error_msg}")

    # ==========================================================================
    # KHU VỰC GỌI THÊM 5 KỊCH BẢN MỚI
    # ==========================================================================
    st.divider()
    st.markdown("### ➕ **Gọi Thêm 5 Kịch Bản Mới**")
    
    cy1, cy2, cy3 = st.columns([1.4, 1.6, 1.0])
    c_unified_more = cy1.selectbox("🧭 Chiến lược & Hình thức Video mới:", UNIFIED_STRATEGY_FORMAT_OPTS, index=0, key=f"more_unified_{st.session_state.reset_key}", disabled=is_system_busy)
    e_role = cy2.text_input("👤 Vai trò NV mới (Để trống = AI tự phân tích):", value="", placeholder="Để trống = Giữ nguyên hoặc AI tự phân tích...", key=f"er_0_{st.session_state.reset_key}", disabled=is_system_busy)
    e_file = cy3.file_uploader("📸 Ảnh mẫu NV mới (Tùy chọn):", type=["jpg", "png"], key=f"ef_0_{st.session_state.reset_key}", disabled=is_system_busy)
    extra_custom_note = st.text_area("✍ Ghi chú AI cho kịch bản thêm (Ưu tiên cao nhất):", placeholder="Ví dụ: Quần là dạng váy 1 ống rộng...", key=f"extra_custom_note_{st.session_state.reset_key}", disabled=is_system_busy)

    if st.button("🚀 Gọi Thêm 5 Kịch Bản Mới", type="primary", use_container_width=True, disabled=is_system_busy):
        can_run, msg = check_usage_limit(st.session_state.current_email)
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
    args = st.session_state.temp_more_args
    with st.spinner("⏳ Đang sáng tạo thêm 5 kịch bản & tự động lưu cập nhật vào dự án..."):
        try:
            p_chars = [{"id": 1, "role": args["role"]}] if args["role"] else st.session_state.character_profiles
            new_sc = generate_more_scripts(args["format"], p_chars, args["note"])
            st.session_state.expanded_scripts.extend(new_sc)
            auto_save_current_session()
            st.toast("✅ Đã sinh thêm 5 kịch bản mới & tự động lưu cập nhật vào dự án!")
            st.session_state.scroll_to_top = True
            st.rerun()
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
