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

def lock_ui():
    st.markdown("""
    <style>
        div[data-testid="stAppViewContainer"], div[data-testid="stSidebar"] { pointer-events: none !important; user-select: none !important; }
        button, div[data-testid="stButton"] button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"] {
            pointer-events: none !important; opacity: 0.35 !important; cursor: not-allowed !important; filter: grayscale(60%) !important;
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
    .dna-bullet { margin-left: 10px; margin-top: 3px; color: #334155; font-weight: 400; font-size: 14px; line-height: 1.65; }
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

def calculate_speech_duration(text: str, is_tiktok_shop: bool = True) -> float:
    words = count_words(text)
    commas = text.count(',') + text.count(';')
    periods = text.count('.') + text.count('!') + text.count('?')
    rate = 4.8 if is_tiktok_shop else 4.0
    comma_pause = 0.08 if is_tiktok_shop else 0.12
    period_pause = 0.12 if is_tiktok_shop else 0.20
    duration = (words / rate) + (commas * comma_pause) + (periods * period_pause)
    return round(duration, 1)

def is_valid_phone(phone):
    phone = phone.strip()
    return phone.isdigit() and phone.startswith('0') and 9 <= len(phone) <= 11

def compress_image_bytes(uploaded_file, max_dimension=768, quality=75):
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
# THUẬT TOÁN PHIÊN ÂM TIỀN TỆ TIẾNG VIỆT CHUẨN XÁC TỪNG CON SỐ (KHÓA CỨNG "BỐN")
# ==============================================================================
def number_to_vietnamese_words(n: int) -> str:
    if n == 0: return "không đồng"
    digits = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    
    def read_block_3(num_str, is_highest=False):
        num_str = num_str.zfill(3)
        h, t, u = int(num_str[0]), int(num_str[1]), int(num_str[2])
        res = []
        if not is_highest or h > 0:
            res.append(digits[h] + " trăm")
        if t == 0 and u == 0:
            pass
        elif t == 0 and u != 0:
            if not is_highest or h > 0: res.append("linh " + digits[u])
            else: res.append(digits[u])
        elif t == 1:
            res.append("mười")
            if u == 1: res.append("một")
            elif u == 4: res.append("bốn")   # KHÓA CỨNG "mười bốn" (TUYỆT ĐỐI KHÔNG DÙNG "TƯ")
            elif u == 5: res.append("lăm")
            elif u != 0: res.append(digits[u])
        else:
            res.append(digits[t] + " mươi")
            if u == 1: res.append("mốt")
            elif u == 4: res.append("bốn")   # KHÓA CỨNG "hai mươi bốn..." (TUYỆT ĐỐI KHÔNG DÙNG "TƯ")
            elif u == 5: res.append("lăm")
            elif u != 0: res.append(digits[u])
        return " ".join(res)

    s = str(abs(n))
    groups = []
    while s:
        groups.append(s[-3:])
        s = s[:-3]
    units = ["", "nghìn", "triệu", "tỷ"]
    result_parts = []
    for i in range(len(groups) - 1, -1, -1):
        val = int(groups[i])
        if val > 0:
            part = read_block_3(groups[i], is_highest=(i == len(groups) - 1))
            if units[i]: part += " " + units[i]
            result_parts.append(part)
    text = " ".join(result_parts).strip()
    text = re.sub(r'\s+', ' ', text).strip()
    return text + " đồng"

def extract_and_convert_prices_in_text(raw_text: str) -> str:
    if not raw_text: return ""
    def replace_k(match):
        val = int(match.group(1)) * 1000
        return number_to_vietnamese_words(val)
    text = re.sub(r'\b(\d{1,4})\s*[kK]\b', replace_k, raw_text)

    def replace_num(match):
        num_str = match.group(1).replace('.', '').replace(',', '')
        try:
            val = int(num_str)
            if val >= 1000:
                return number_to_vietnamese_words(val)
        except: pass
        return match.group(0)
    cleaned = re.sub(r'(\b\d{1,3}(?:[.,]\d{3})+\b)', replace_num, text)
    return cleaned

# ==============================================================================
# HÀM XÁC ĐỊNH NHÂN KHẨU HỌC BẤT BIẾN (HỖ TRỢ ĐƠN & ĐA NHÂN VẬT)
# ==============================================================================
def get_demographics_description(char_profiles):
    if not char_profiles:
        return "female", "A 26-year-old native Vietnamese woman"
    
    parts = []
    primary_gender = "female"
    for idx, p in enumerate(char_profiles):
        role_lower = str(p.get("role", "")).lower()
        if any(k in role_lower for k in ["bố", "ba", "chồng", "bác trai"]):
            desc = "a 28-year-old native Vietnamese father"
            if idx == 0: primary_gender = "male"
        elif any(k in role_lower for k in ["nam", "anh", "trai", "thanh niên"]):
            desc = "a 26-year-old native Vietnamese young man"
            if idx == 0: primary_gender = "male"
        elif any(k in role_lower for k in ["ông", "già", "bác già", "ông nội", "ông ngoại"]):
            desc = "a 65-year-old native Vietnamese elderly man"
            if idx == 0: primary_gender = "male"
        elif any(k in role_lower for k in ["bà", "bà nội", "bà ngoại"]):
            desc = "a 65-year-old native Vietnamese elderly woman"
            if idx == 0: primary_gender = "female"
        elif any(k in role_lower for k in ["bé trai", "con trai"]):
            desc = "a cute 4-year-old native Vietnamese boy"
            if idx == 0: primary_gender = "male"
        elif any(k in role_lower for k in ["bé gái", "con gái"]):
            desc = "a cute 3-year-old native Vietnamese girl"
            if idx == 0: primary_gender = "female"
        elif any(k in role_lower for k in ["mẹ", "chị", "cô", "vợ"]):
            desc = "a 26-year-old native Vietnamese mother"
            if idx == 0: primary_gender = "female"
        else:
            desc = f"a 26-year-old native Vietnamese {'man' if 'nam' in role_lower else 'woman'}"
            if idx == 0: primary_gender = "male" if 'nam' in role_lower else "female"
        parts.append(desc)
    
    if len(parts) == 1:
        full_demo = parts[0].capitalize()
    elif len(parts) == 2:
        full_demo = f"{parts[0].capitalize()} and {parts[1]}"
    else:
        full_demo = f"{', '.join(parts[:-1]).capitalize()} and {parts[-1]}"
    
    return primary_gender, full_demo

# ==============================================================================
# BỘ LỌC BẢN QUYỀN & NGƯỜI NỔI TIẾNG (IP & CELEBRITY SAFEGUARD)
# ==============================================================================
def sanitize_third_party_ip(text: str) -> str:
    if not text: return ""
    cleaned = text
    platforms = [r'\btiktok\s*(?:shop)?\b', r'\bshopee\b', r'\blazada\b', r'\bfacebook\b', r'\binstagram\b', r'\byoutube\b']
    for p in platforms:
        cleaned = re.sub(p, 'commercial marketplace', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:emoon|disney|marvel|spider-?man|spiderman|nike|apple|samsung|lego|barbie)\b', 'custom premium brand', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bin\s+logo\s+voi\s+con\s+màu\s+cam\s+emoon\b', 'featuring a minimalist cute stylized cartoon mascot graphic and clean brand typography', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\borange\s+elephant\s+emoon\s+logo\b', 'minimalist stylized cartoon mascot emblem with clean typography', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bspider-?man\s+(?:face|badge|figure)\b', 'stylized cute heroic cartoon mascot emblem', cleaned, flags=re.IGNORECASE)
    return cleaned

# ==============================================================================
# TỪ ĐIỂN BẢN ĐỊA HÓA TIẾNG HÀ NỘI TOÀN DIỆN CHO TẤT CẢ NGÀNH NGHỀ & SỐ "BỐN"
# ==============================================================================
POLICY_REPLACEMENTS = {
    r'\btuyệt\s*đối\b': 'rất', r'\bhoàn\s*toàn\b': 'thực sự', r'\b100\s*%\b': 'rất nhiều',
    r'\bchắc\s*chắn\b': 'rất có thể', r'\bcam\s*kết\b': 'an tâm', r'\bdứt\s*điểm\b': 'cải thiện',
    r'\bđặc\s*trị\b': 'hỗ trợ', r'\bkhỏi\s*hẳn\b': 'đỡ hẳn', r'\bvĩnh\s*viễn\b': 'lâu dài',
    r'\bchuẩn\s*đét\b': 'vừa vặn', r'\bchữa\s*khỏi\b': 'hỗ trợ', r'\bthần\s*dược\b': 'bí quyết',
    r'\btốt\s*nhất\b': 'rất tốt', r'\bsố\s*1\b': 'hàng đầu', r'\btrắng\s*cấp\s*tốc\b': 'sáng khỏe tự nhiên',
    r'\bgiảm\s*béo\s*cấp\s*tốc\b': 'vóc dáng thon gọn', r'\bxóa\s*sạch\s*nám\b': 'mờ thâm sạm',
    r'\bthuốc\s*trị\b': 'sản phẩm hỗ trợ', r'\bđiều\s*trị\b': 'hỗ trợ cải thiện', r'\btriệt\s*để\b': 'hiệu quả',
    r'\btrợ\s*giá\b': 'giảm giá sâu có hạn',
    r'\bphiên\s*live\b': 'đợt ưu đãi này',
    r'\btrên\s*live\b': 'đợt này',
    r'\blivestream\b': 'chương trình ưu đãi'
}

SOUTHERN_TO_HANOI = {
    # 1. KHÓA CỨNG TOÀN BỘ SỐ 4 PHÁT ÂM CHUẨN LÀ "BỐN" (DIỆT SẠCH "TƯ")
    r'\btư\s+mươi\b': 'bốn mươi',
    r'\bmười\s+tư\b': 'mười bốn',
    r'\btrăm\s+tư\b': 'trăm bốn mươi',
    r'\bnghìn\s+tư\b': 'nghìn bốn trăm',
    r'\b(\w+)\s+mươi\s+tư\b': r'\1 mươi bốn',
    r'\bbốn\s+tư\b': 'bốn mươi bốn',
    r'\bnăm\s+tư\b': 'năm mươi bốn',
    r'\bsáu\s+tư\b': 'sáu mươi bốn',
    r'\bbảy\s+tư\b': 'bảy mươi bốn',
    r'\btám\s+tư\b': 'tám mươi bốn',
    r'\bchín\s+tư\b': 'chín mươi bốn',
    r'\bhai\s+tư\b': 'hai mươi bốn',
    r'\bba\s+tư\b': 'ba mươi bốn',
    r'\bhăm\s+tư\b': 'hai mươi bốn',

    # 2. F&B, ĐỒ ĂN VẶT & ẨM THỰC
    r'\bba\s*rọi\b': 'ba chỉ',
    r'\bchiên\s*(?:giòn|phồng|ngập\s*dầu)?\b': 'rán giòn',
    r'\bchiên\b': 'rán',
    r'\báo\s*(?:đều|lớp\s*sốt|sốt)\b': 'ngấm đẫm sốt',
    r'\bcay\s*the\b': 'cay tê',
    r'\bthe\s*the\b': 'tê tê',
    r'\bsánh\s*dẻo\b': 'sền sệt',
    r'\bkẹo\s*lại\b': 'sệt lại',
    r'\bđậu\s*phộng\b': 'hạt lạc',
    r'\btrái\s*cây\s*dầm\b': 'hoa quả dầm',
    r'\btrái\s*cây\b': 'hoa quả',
    r'\brỗng\s*ruột\b': 'xốp tan',
    r'\bcực\s*kỳ\s*vừa\s*vặn\b': 'vừa miệng dã man',
    r'\bđã\s*cái\s*nư\b': 'đã miệng cực kỳ',

    # 3. GIA DỤNG, BẾP & TẨY RỬA
    r'\bxả\s*sơ(?:\s*qua)?\b': 'tráng qua',
    r'\bxả\s*nước\b': 'tráng nước',
    r'\brải\s+vào\b': 'xếp vào',
    r'\brải\b(?=\s+[a-zà-ỹ]+)': 'cho',
    r'\brửa\s*chén\b': 'rửa bát',
    r'\bnước\s*rửa\s*chén\b': 'nước rửa bát',
    r'\bly\s+nước\b': 'cốc nước',
    r'\bly\s+trà\b': 'cốc trà',
    r'\bly\s+đá\b': 'cốc đá',
    r'\bly\b(?=\s+(?:uống|nước|thủy tinh|nhựa))': 'cốc',
    r'\bmuỗng\b': 'thìa',
    r'\bbàn\s*ủi\b': 'bàn là',
    r'\bbao\s*rác\b': 'túi rác',
    r'\bchổi\s*lông\s*gà\b': 'chổi phất trần',

    # 4. CÔNG NGHỆ, ĐIỆN TỬ & PHỤ KIỆN
    r'\bkhít\s+tai\s+êm\s+ái\b': 'vừa khít mà êm ru',
    r'\bêm\s+ái\b': 'êm ru',
    r'\bgiữa\s+tiếng\s+còi\s+xe\s+inh\s+ỏi\b': 'ngoài đường còi xe ồn ào',
    r'\bkèm\s+dây\s+đeo\s+cực\s+kỳ\s+tiện\s+lợi\b': 'có sẵn cả dây đeo tiện lắm',
    r'\bvỏ\s+ngoài\b': 'bên ngoài',
    r'\bnét\s+căng\b': 'rõ mồn một',
    r'\bpin\s*trâu\b': 'pin dùng trâu bò',
    r'\bsạc\s*lẹ\b': 'sạc nhanh',

    # 5. MỸ PHẨM & LÀM ĐẸP
    r'\bthấm\s*lẹ\b': 'thấm nhanh',
    r'\bbết\s*rít\b': 'nhờn dính',
    r'\bxài\s*êm\b': 'dùng êm',
    r'\bmịn\s*mướt\b': 'căng mướt',
    r'\blột\s*mụn\b': 'hút mụn',

    # 6. THỜI TRANG & MAY MẶC
    r'\bbận\s+đồ\b': 'mặc đồ',
    r'\bbận\s+áo\b': 'mặc áo',
    r'\bbận\s+quần\b': 'mặc quần',
    r'\bbận\s+váy\b': 'mặc váy',
    r'\bbận\b(?=\s+[a-zà-ỹ]+)': 'mặc',
    r'\bđầm\b': 'váy',
    r'\báo\s*thun\b': 'áo phông',
    r'\bmang\s*giày\b': 'đi giày',
    r'\bmang\s*dép\b': 'đi dép',
    r'\bdây\s*nịt\b': 'thắt lưng',
    r'\bbóp\s*tiền\b': 'ví tiền',

    # 7. ĐẠI TỪ & KHẨU NGỮ THÔNG DỤNG
    r'\bngàn\b': 'nghìn',
    r'\bxài\b': 'dùng',
    r'\bgiùm\b': 'hộ',
    r'\bdùm\b': 'hộ',
    r'\btui\b': 'tôi',
    r'\bhén\b': 'nhỉ',
    r'\bnghen\b': 'nhé',
    r'\bhen\b': 'nhé',
    r'\brùi\b': 'rồi',
    r'\bmần\b': 'làm',
    r'\bkiếng\b': 'kính',
    r'\bhổng\b': 'không',
    r'\bthiệt\b': 'thật',
    r'\bmắc\s+cỡ\b': 'ngại',
    r'\bhết\s+sẩy\b': 'tuyệt cú mèo',
    r'\brẻ\s+bèo\b': 'rẻ thế',
    r'\bquá\s+trời\b': 'rất nhiều',
    r'\bquá\s+chừng\b': 'rất nhiều',
    r'\bnè\b': 'này',
    r'\bnha\b': 'nhé',
    r'\bcưng\s+xỉu\b': 'yêu cực kỳ',
    r'\bcoi\b': 'xem',
    r'\bmua\s+liền\b': 'mua ngay',
    r'\bliền\s+tay\b': 'ngay tay',
    r'\bbữa\s+nay\b': 'hôm nay',
    r'\bbữa\s+hổm\b': 'hôm trước',
    r'\bhổm\s+rày\b': 'dạo này',
    r'\bmấy\s+chế\b': 'các chị em',
    r'\bmấy\s+bà\b': 'các chị em',
    r'\bưng\s+bụng\b': 'vừa ý'
}

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
    cleaned = re.sub(r'\btrợ\s*giá\b', 'giảm giá sâu có hạn', cleaned, flags=re.IGNORECASE)
    return cleaned

def clean_and_normalize_voiceover(text: str) -> str:
    if not text: return ""
    cleaned = sanitize_policy_text(text)
    cleaned = extract_and_convert_prices_in_text(cleaned)
    for pattern, rep in [
        (r'\b14\b', 'mười bốn'), (r'\b24\b', 'hai mươi bốn'), (r'\b34\b', 'ba mươi bốn'),
        (r'\b40\b', 'bốn mươi'), (r'\b44\b', 'bốn mươi bốn'), (r'\b4\b', 'bốn'),
        (r'\bmười\s+tư\b', 'mười bốn'), (r'\bhai\s+tư\b', 'hai mươi bốn'),
        (r'\btrăm\s+tư\b', 'trăm bốn mươi'), (r'\btư\s+mươi\b', 'bốn mươi')
    ]:
        cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    return cleaned

def sanitize_veo3_prompt(prompt_text: str) -> str:
    if not prompt_text: return ""
    p = re.sub(r'\bunzipping\s+(?:front\s+)?(?:zipper\s+)?(?:halfway\s+)?(?:on\s+)?chest\b', 'smoothly demonstrating the front zipper', prompt_text, flags=re.IGNORECASE)
    p = re.sub(r'\bparting\s+(?:front\s+)?lapel\b', 'displaying the jacket inner lining cleanly', p, flags=re.IGNORECASE)
    p = re.sub(r'\brevealing\b', 'showing', p, flags=re.IGNORECASE)
    p = re.sub(r'\bundressing\b', 'wearing outerwear', p, flags=re.IGNORECASE)
    p = re.sub(r'\btouching\s+(?:the\s+)?child\b', 'standing gently beside child', p, flags=re.IGNORECASE)
    p = re.sub(r'\bgesturing\s+(?:warmly\s+)?(?:downward\s+)?(?:toward\s+)?(?:lower\s+)?(?:left\s+)?corner\b', 'sharing recommendations with an open-palm hand gesture', p, flags=re.IGNORECASE)
    p = re.sub(r'\bpointing\s+(?:downward\s+)?(?:to\s+)?(?:corner|cart)\b', 'speaking with welcoming open hands', p, flags=re.IGNORECASE)
    return sanitize_third_party_ip(p)

def clean_analysis_text(text) -> str:
    if not text: return ""
    if isinstance(text, (dict, list)):
        return format_analysis_field(text)
    pattern = r'^(?:SẢN PHẨM LÀ GÌ\s*&?\s*(?:CÓ GÌ ĐẶC BIỆT)?|SẢN PHẨM DÀNH CHO AI|TẠI SAO NÊN MUA|DÙNG Ở ĐÂU\s*&?\s*(?:TIỆN LỢI LÀ GÌ)?|CÁCH SỬ DỤNG|THAO TÁC.*|MỤC ĐÍCH|ĐỐI TƯỢNG|LÝ DO MUA)\s*:\s*'
    res = re.sub(pattern, '', str(text).strip(), flags=re.IGNORECASE).strip()
    return clean_and_normalize_voiceover(res)

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict): 
        return "<br>".join([f"<span class='dna-label'>{str(k).replace('_', ' ').title()}:</span> <span class='dna-text'>{clean_analysis_text(v)}</span>" for k, v in field_val.items()])
    if isinstance(field_val, list): 
        return "<br>".join([f"<div class='dna-bullet'>• <span class='dna-text'>{clean_analysis_text(item)}</span></div>" for item in field_val])
    val_str = clean_analysis_text(str(field_val))
    return "".join([f"<div class='dna-bullet'>• <span class='dna-text'>{line.strip()}</span></div>" for line in val_str.split('<br>') if line.strip()])

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
                "last_generation_date": "", "active_session_id": ""
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

# ==============================================================================
# QUẢN LÝ DỰ ÁN NÂNG CẤP: TỰ ĐỘNG KHÔI PHỤC KHI LƯU & ĐỔI TÊN DỄ DÀNG
# ==============================================================================
def save_project_to_db(email, title, payload_data, project_id=None):
    if not supabase: return False, "Chưa kết nối cơ sở dữ liệu."
    try:
        clean_content = json.loads(json.dumps(payload_data, default=str))
        if project_id:
            res = supabase.table("saved_projects").update({
                "project_title": title,
                "script_content": clean_content
            }).eq("id", project_id).execute()
            if res.data and len(res.data) > 0:
                return True, "Đã cập nhật dự án thành công!"
        
        res = supabase.table("saved_projects").insert({
            "user_email": email,
            "project_title": title,
            "script_content": clean_content
        }).execute()
        if res.data and len(res.data) > 0:
            st.session_state.current_project_id = res.data[0]['id']
            return True, "Đã lưu thành dự án mới thành công!"
        return False, "Không thể lưu dữ liệu dự án."
    except Exception as e:
        return False, str(e)

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
    ("last_mode", "🛒 TikTok Shop & Bán Hàng"), ("last_style", "Điện Ảnh Chân Thực"), ("last_narrator", "On-camera"),
    ("last_presentation_format", "🌟 AI Tự Động Phân Tích & Đề Xuất"),
    ("target_duration_instruction", ""), ("character_profiles", []), ("current_project_id", None),
    ("saved_reference_images", []), ("show_all_projects", False), ("show_all_admin_accounts", False),
    ("current_processing_id", None), ("current_cloning_id", None)
]:
    if key not in st.session_state: st.session_state[key] = default_val

is_system_busy = (
    st.session_state.get("current_processing_id") is not None or 
    st.session_state.get("current_cloning_id") is not None
)

if is_system_busy: lock_ui()

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
    open_curly = candidate.count('{') - candidate.count('}')
    open_square = candidate.count('[') - candidate.count(']')
    candidate += (']' * max(0, open_square)) + ('}' * max(0, open_curly))
    try: return json.loads(candidate, strict=False)
    except: pass

    try:
        py_str = candidate.replace('true', 'True').replace('false', 'False').replace('null', 'None')
        parsed = ast.literal_eval(py_str)
        return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict) else parsed
    except: pass
    raise Exception("AI sinh JSON lỗi cấu trúc. Vui lòng bấm tạo lại.")

def call_gemini(contents, sys_inst="Bạn là AI hỗ trợ JSON.", max_tokens=6500):
    models_to_try = ["gemini-3.8-flash", "gemini-3.8-flash-lite"]
    last_exception = None
    for model_name in models_to_try:
        for attempt in range(3):
            try:
                res = client.models.generate_content(
                    model=model_name, contents=contents,
                    config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.7, max_output_tokens=max_tokens)
                )
                return repair_and_parse_json(res.text)
            except Exception as e:
                last_exception = e
                err_str = str(e).lower()
                if "404" in err_str or "not_found" in err_str: break
                if "503" in err_str or "unavailable" in err_str or "429" in err_str or "resource_exhausted" in err_str:
                    time.sleep((attempt + 1) * 2.0); continue
                time.sleep(1.0)
    if last_exception:
        if "503" in str(last_exception) or "unavailable" in str(last_exception).lower():
            raise Exception("Máy chủ AI của Google đang bị quá tải tạm thời (503). Vui lòng đợi 5-10 giây rồi bấm tạo lại.")
        raise last_exception

def build_voice_direction(mode, num_chars, character_profiles):
    is_tiktok_shop = ("Viral" not in mode)
    speed_txt = "tốc độ dồn dập (4.8 - 5.2 từ/s), rướn người, dứt khoát" if is_tiktok_shop else "tốc độ tự nhiên, truyền cảm, nhả chữ chân thực đời thường (3.8 - 4.2 từ/s)"
    if num_chars <= 1:
        return f"Nhân vật nói trực tiếp: 100% Giọng Hà Nội chuẩn bản địa đúng độ tuổi, phát âm tròn vành rõ chữ, số 4 đọc là 'bốn', {speed_txt}. Giữ nguyên duy nhất một phong thái giọng Hà Nội nhất quán suốt 4 cảnh."
    dirs = []
    for p in character_profiles:
        r = str(p.get('role', '')).lower()
        if any(k in r for k in ["bé", "con", "trẻ", "nhỏ", "gái", "trai", "thiếu nhi"]):
            dirs.append(f"• NV {p['id']} ({p['role']}): Giọng thiếu nhi Hà Nội chuẩn, trong trẻo, líu lo, ngây thơ, xưng con/cháu.")
        elif any(k in r for k in ["ông", "bà", "già", "cao tuổi"]):
            dirs.append(f"• NV {p['id']} ({p['role']}): Giọng người cao tuổi Hà Nội chuẩn, từ tốn, đôn hậu, trầm ấm.")
        elif any(k in r for k in ["bố", "ba", "chồng", "nam", "anh", "bác trai"]):
            dirs.append(f"• NV {p['id']} ({p['role']}): Giọng nam Hà Nội chuẩn, trầm ấm, chững chạc, nội lực.")
        else:
            dirs.append(f"• NV {p['id']} ({p['role']}): Giọng nữ Hà Nội chuẩn, thanh lịch, ngọt ngào, dịu dàng.")
    return " | ".join(dirs)

def generate_char_rules_string(profiles):
    if not profiles: return "100% người Việt Nam bản địa, nhân vật hư cấu đời thường, tóc đen tuyền tự nhiên, khóa duy nhất 1 kiểu tóc suốt 4 cảnh."
    rules = "DANH SÁCH DIỄN VIÊN (KHÓA 100% NGƯỜI VIỆT HƯ CẤU, TUYỆT ĐỐI KHÔNG DÙNG HÌNH ẢNH NGƯỜI NỔI TIẾNG, DIỆN MẠO BẤT BIẾN SUỐT 4 CẢNH):\n"
    for p in profiles: 
        rules += f" - Diễn viên {p['id']} ({p['role']}): 100% thuần Việt hư cấu (fictional persona), tóc đen tuyền tự nhiên. KHÓA DUY NHẤT 1 MÀU TÓC ĐEN TUYỀN, 1 KIỂU TÓC, 1 GIỚI TÍNH CỐ ĐỊNH VÀ 1 KHUÔN MẶT XUYÊN SUỐT 4 CẢNH.\n"
    return rules

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, angle, custom_note="", presentation_format=""):
    is_multi = (num_chars >= 2)
    is_viral = ("Viral" in mode)
    format_direction = f"ĐỊNH DẠNG: TIỂU PHẨM ĐỐI THOẠI {num_chars} NHÂN VẬT THUẦN VIỆT NÓI TRỰC TIẾP." if is_multi else "ĐỊNH DẠNG: ĐỘC THOẠI KOC THUẦN VIỆT NÓI TRỰC TIẾP."
    strat_cmd = "BẠN PHẢI MIX ĐA DẠNG 5 GÓC ĐỘ NỘI DUNG." if "Tự động mix" in angle else f"VIẾT CẢ 5 KỊCH BẢN THEO: '{angle}'."
    override_rule = f"🛑 CHỈ THỊ ƯU TIÊN CAO NHẤT TỪ NGƯỜI DÙNG: '{custom_note}'. Bạn BẮT BUỘC phải thực hiện đúng chỉ thị này trong toàn bộ 5 kịch bản!" if custom_note else ""
    pres_rule = f"🛑 HÌNH THỨC VIDEO CHỈ ĐỊNH: '{presentation_format}'. Hãy định hướng kịch bản bám sát hình thức này." if presentation_format else ""

    viral_directive = """
    🛑 PHÂN NHÁNH THỂ LOẠI: ĐÂY LÀ VIDEO 'VIRAL & XÂY KÊNH':
    - Mục tiêu cốt lõi: Tối đa hóa tỷ lệ giữ chân (Retention) và kích thích tương tác thảo luận (Engagement), kiếm Follower.
    - CẢ 5 KỊCH BẢN PHẢI TẬP TRUNG: Chia sẻ kiến thức, mẹo vặt hữu ích, sự thật bất ngờ, giải quyết hiểu lầm, hoặc câu chuyện đời thường chân thật chạm cảm xúc.
    - TUYỆT ĐỐI KHÔNG BÁN HÀNG, KHÔNG GIỚI THIỆU GIÁ TIỀN, KHÔNG GIỎ HÀNG, KHÔNG KHUYẾN MÃI, KHÔNG DEAL HỜI.
    """ if is_viral else """
    🛑 PHÂN NHÁNH THỂ LOẠI: ĐÂY LÀ VIDEO 'TIKTOK SHOP & BÁN HÀNG':
    - Mục tiêu: Chuyển đổi bán hàng trực tiếp, giải quyết nỗi đau khách hàng, phô diễn công năng sản phẩm, đòn bẩy neo giá và chốt deal giỏ hàng an toàn.
    """

    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL TIKTOK & REELS TRIỆU VIEW. PHONG CÁCH: {style}
    {strat_cmd} | {format_direction}
    {override_rule}
    {pres_rule}
    {viral_directive}
    
    🛑 YÊU CẦU ĐA DẠNG HÓA 5 BỐI CẢNH HOÀN TOÀN KHÁC NHAU:
    - BẮT BUỘC mỗi kịch bản trong 5 kịch bản phải diễn ra ở 1 BỐI CẢNH ĐỜI THỰC KHÁC NHAU (tuyệt đối không trùng lặp bối cảnh giữa 5 kịch bản).
    - Phân tích linh hoạt theo đúng thực tế sản phẩm và góc độ kịch bản.

    🛑 BỘ MÁY NGỮ PHÁP VĂN NÓI XUÔI CHIỀU, ẨM THỰC ĐA GIÁC QUAN & PHÁT ÂM CHUẨN HÀ NỘI:
    - CÂU CÚ PHẢI TUYỆT ĐỐI XUÔI THEO VĂN NÓI ĐỜI THƯỜNG CỦA NGƯỜI HÀ NỘI: Chủ ngữ -> Vị ngữ -> Cảm xúc/Hiệu quả.
    - TUYỆT ĐỐI CẤM CÂU BỊ ĐỘNG HOẶC ĐẢO NGỮ LỦNG CỦNG KIỂU DỊCH MÁY: Cấm mở đầu câu bằng 'Với thiết kế...', 'Được làm từ...', 'Giúp cho việc...'.
    - TUYỆT ĐỐI CẤM các từ ngữ công nghệ/máy móc sáo rỗng: CẤM 'thuật toán gợi ý', CẤM 'máy vừa phân tích', CẤM 'hệ thống vừa báo', CẤM 'AI phát hiện'.
    - QUY TẮC SỐ BỐN: 100% các số có số 4 BẮT BUỘC đọc và viết là 'bốn' (mười bốn, hai mươi bốn, bốn mươi, bốn trăm...). TUYỆT ĐỐI CẤM đọc số bốn thành 'tư' (CẤM 'mười tư', CẤM 'tư mươi', CẤM 'trăm tư').
    - NẾU LÀ ĐỒ ĂN / ẨM THỰC: Mô tả kích thích tối đa tam giác giác quan (thị giác: độ bóng/khói, xúc giác: độ giòn/bẻ đôi xốp tan, thính giác: tiếng cắn rộp rộp ASMR).
    - 100% CẢ 4 CẢNH LỜI THOẠI ĐỀU BẮT ĐẦU NGAY TỪ 0.00s.
    - CẤM TUYỆT ĐỐI TỪ 'NGÀN' (BẮT BUỘC DÙNG 'NGHÌN').
    - CẤM TUYỆT ĐỐI TỪ 'TRỢ GIÁ', 'PHIÊN LIVE', 'TRÊN LIVE'.
    - CẤM TUYỆT ĐỐI KHẨU NGỮ MIỀN NAM. BẮT BUỘC 100% khẩu ngữ Hà Nội chuẩn: 'ba chỉ', 'rán', 'sền sệt', 'cay tê', 'dùng', 'này', 'nhé', 'nhỉ', 'xem', 'hôm nay', 'các chị em', 'các bác', 'ạ'.
    - TUYỆT ĐỐI KHÔNG CÓ GIỌNG THUYẾT MINH NGOÀI.
    🛑 100% NGƯỜI VIỆT HƯ CẤU: Tuyệt đối cấm mặt ngoại quốc, cấm người nổi tiếng.
    🛑 {char_rules}
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction, num_chars, character_profiles, custom_note="", presentation_format="", self_pronoun="em", audience_pronoun="các chị em", setting_archetype="Nhà phố / Chung cư hiện đại sạch sẽ", is_fixed_location=True):
    is_multi = (num_chars >= 2)
    is_viral = ("Viral" in mode)
    voice_guidance = build_voice_direction(mode, num_chars, character_profiles)
    dialogue_type_rule = f"🛑 ĐỐI THOẠI {num_chars} NHÂN VẬT: Tách từng câu thoại nói trực tiếp (Mẹ: '...' | Bé: '...'). Giọng thiếu nhi Hà Nội ngây thơ, mẹ dịu dàng đúng độ tuổi." if is_multi else "🛑 ĐỘC THOẠI KOC: Lời thoại liền mạch do chính KOC mở miệng nói trực tiếp trước ống kính."
    
    if is_viral:
        outro_instruction = f"""
        🛑 QUY TẮC CẢNH 4 CHO THỂ LOẠI 'VIRAL & XÂY KÊNH' (ENGAGEMENT & RETENTION - KHÔNG BÁN HÀNG):
        - Sử dụng đúng cặp nhân xưng: KOC xưng '{self_pronoun}', gọi người xem là '{audience_pronoun}'.
        - Mục tiêu: Giữ chân người xem, tạo cảm giác gần gũi, kích thích người xem comment thảo luận, lưu video và bấm Follow kênh.
        - Lời thoại Cảnh 4 chuẩn giọng Hà Nội tự nhiên, câu văn mượt mà ấm áp dưới 28 từ.
        - Công thức: Đặt câu hỏi thảo luận hoặc kết lại bài học tâm đắc + Kêu gọi bấm follow đón xem video tiếp theo.
        - TUYỆT ĐỐI CẤM: Không nhắc đến giá tiền, không mã giảm giá, không voucher, không giỏ hàng, không mua hàng!
        """
    else:
        outro_instruction = f"""
        🛑 CÔNG THỨC CHỐT DEAL CẢNH 4 TIKTOK SHOP SIÊU KÍCH THÍCH & AN TOÀN TUYỆT ĐỐI (DƯỚI 30 TỪ):
        - Lời thoại Cảnh 4 chuẩn giọng Hà Nội, tuân thủ đúng 3 vế xuôi tai:
          1. Neo giá thực tế & Báo giá giảm kích thích:
             'Bình thường set này hơn [X] nghìn, đợt này áp mã voucher vào chỉ còn khoảng [Y] mấy nghìn thôi...' (hoặc 'giá gốc khoảng [X] nghìn, hiện tại áp mã còn tầm [Y] mấy nghìn...')
          2. Miễn trừ thời điểm phòng ngừa quét chính sách:
             'nhưng giá từng thời điểm có thể khác nhau tùy đợt ưu đãi...' (hoặc 'tùy thời điểm giá sẽ chênh lệch một chút...')
          3. Rào voucher tài khoản cá nhân & CTA:
             '{audience_pronoun} cứ bấm góc trái kiểm tra tài khoản mình xem nhé!'
        - QUY TẮC SỐ BỐN: Đọc là 'bốn' (bốn mươi nghìn, một trăm bốn mươi nghìn...). CẤM TUYỆT ĐỐI 'tư'.
        - CẤM TUYỆT ĐỐI các từ: 'phiên live', 'trên live', 'trợ giá'.
        - CẤM gọi 'các mẹ' nếu đại từ khán giả quy định là '{audience_pronoun}'.
        - TUYỆT ĐỐI KHÔNG yêu cầu hiện text/chữ/subtitles trên video để tránh lỗi font/chính tả của AI Veo 3.
        """

    override_rule = f"🛑 CHỈ THỊ ƯU TIÊN CAO NHẤT TỪ NGƯỜI DÙNG (DIRECTOR'S SPECIAL OVERRIDE): '{custom_note}'. BẮT BUỘC tuân thủ 100% trong toàn bộ các phân cảnh, lời thoại, và cấu trúc prompt ảnh/video!" if custom_note else ""

    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL TIKTOK SHOP & VIRAL ĐA GIÁC QUAN (AUDIO-VISUAL MASTER). PHONG CÁCH: {style}
    CHỈ ĐẠO GIỌNG: {voice_guidance}
    {dialogue_type_rule}
    {outro_instruction}
    {override_rule}
    
    🛑 MA TRẬN NHÂN XƯNG ĐỒNG NHẤT (PRONOUN INVARIANCE LOCK):
    - Toàn bộ 4 phân cảnh BẮT BUỘC sử dụng đúng cặp đại từ nhân xưng: KOC tự xưng là '{self_pronoun}' và gọi khán giả là '{audience_pronoun}'.
    - TUYỆT ĐỐI CẤM dùng từ 'các mẹ' nếu sản phẩm không phải đồ Mẹ & Bé! (Ví dụ: Miếng rửa bát, đồ bếp, gia dụng thì BẮT BUỘC gọi là 'các chị em', 'các bác' hoặc 'nhà mình').
    - Giữ nguyên duy nhất một cách xưng hô này từ Cảnh 1 đến Cảnh 4, cấm thay đổi giữa chừng.

    🛑 KHÓA BỐI CẢNH ĐỜI THỰC THẤU CẢM (RELATABLE REALISM & SPATIAL INVARIANCE):
    - Chuẩn không gian: '{setting_archetype}' (nhà phố hiện đại hoặc chung cư sạch sẽ, ngăn nắp, tường men sáng, ánh sáng tự nhiên).
    - TUYỆT ĐỐI CẤM 2 THÁI CỰC PHI THỰC TẾ:
      1. Cấm bối cảnh nhà cấp 4 cũ kỹ, tường bẩn, bếp ẩm thấp nhếch nhác.
      2. Cấm bối cảnh biệt thự cung điện xa hoa lộng lẫy, dát vàng giả tạo.
    - NẾU SẢN PHẨM CỐ ĐỊNH (is_fixed_location = {is_fixed_location}): BẮT BUỘC cả 4 cảnh diễn ra tại DUY NHẤT 1 TỌA ĐỘ VẬT LÝ CỐ ĐỊNH (ví dụ: bồn rửa bát inox đôi sạch sẽ), chỉ thay đổi góc máy quay!

    🛑 KHÓA TRẠNG THÁI SƠ VIN TRANG PHỤC ĐỒNG BỘ THEO PHÂN TÍCH THỰC TẾ:
    - Trạng thái cạp áo (sơ vin nhét vào cạp quần HOẶC buông thõng tự nhiên) được quyết định dựa vào phân tích thời trang và hoàn cảnh thực tế, sau đó BẮT BUỘC phải đồng nhất 100% xuyên suốt cả 4 phân cảnh!
    - Tuyệt đối cấm cảnh trước sơ vin mà cảnh sau lại thả áo buông thõng.

    🛑 NGUYÊN TẮC ĐẠO DIỄN ẨM THỰC ĐA GIÁC QUAN (SENSORY FOOD-PORN DIRECTIVE):
    - Khi làm về đồ ăn/thực phẩm:
      • Thị giác: Góc máy Macro / Close-Up đặc tả độ bóng sốt mắm, khói nóng bốc lên, ruột xốp rỗng.
      • Xúc giác: Hành động bẻ đôi rơi vụn giòn tan, chấm ngập bát sốt sền sệt, đầu ngón tay dính sốt chân thật.
      • Thính giác: Âm thanh cắn 'rộp rộp' giòn tan, tiếng bẻ 'rắc', tiếng mỡ sôi xèo xèo.
      • Vi biểu cảm: 3 nhịp sinh học: Hít hà mùi thơm -> Cắn giòn mở to mắt bất ngờ -> Nhắm mắt gật đầu thảng thốt khen ngon.

    🛑 QUY TẮC PHÁT ÂM SỐ BỐN CHUẨN THỰC TẾ:
    - 100% các con số có số 4 BẮT BUỘC đọc và viết là 'bốn' (mười bốn, hai mươi bốn, bốn mươi, bốn trăm, bốn triệu...). TUYỆT ĐỐI CẤM đọc số bốn thành 'tư' (CẤM 'mười tư', CẤM 'tư mươi', CẤM 'trăm tư', CẤM 'hai tư nghìn').

    🛑 GIỚI HẠN CỨNG THỜI LƯỢNG VEO 3 (TỐI ĐA 10 GIÂY / PHÂN CẢNH):
    - MỖI PHÂN CẢNH (CẢNH 1, 2, 3, 4) CÓ THỜI LƯỢNG LINH HOẠT TỪ 4s ĐẾN TỐI ĐA 10 GIÂY (đã bao gồm đệm diễn xuất tự nhiên).
    - CẢNH 1 HOÀN TOÀN CÓ THỂ DÀI 7s, 8s, 9s HOẶC 10s nếu mở đầu bằng một câu chuyện hay, tình huống kịch tính hoặc tâm sự chạm cảm xúc.
    - TUYỆT ĐỐI CẤM BẤT KỲ CẢNH NÀO VƯỢT QUÁ 10 GIÂY (để đảm bảo tương thích 100% với AI Veo 3).
    - ĐỂ THỜI LƯỢNG KHÔNG QUÁ 10s: Số từ của mỗi phân cảnh BẮT BUỘC nằm trong khoảng từ 16 đến TỐI ĐA 35 TỪ!

    🛑 BỘ MÁY NGỮ PHÁP VĂN NÓI XUÔI CHIỀU (SPOKEN-SYNTAX DIRECTIVE):
    - Lời thoại phải xuôi tai, gãy gọn, đúng văn phong nói chuyện hằng ngày của người Hà Nội: Chủ ngữ -> Vị ngữ -> Hiệu quả thực tế.
    - CẤM TUYỆT ĐỐI câu bị động, câu đảo ngữ rườm rà kiểu dịch máy ('Với thiết kế...', 'Được làm từ...').
    - Từng câu thoại liên kết tự nhiên, có trợ từ ngữ khí ('nhé', 'luôn', 'này', 'đây này', 'cơ', 'ạ').

    🛑 KHÓA CHẶT GIỚI TÍNH & ĐỘ TUỔI DIỄN VIÊN BẤT BIẾN (STRICT DEMOGRAPHIC INVARIANCE):
    - BẮT BUỘC phải xác định rõ ràng và duy trì duy nhất 1 GIỚI TÍNH CỤ THỂ ('a Vietnamese woman' hoặc 'a Vietnamese man') và ĐỘ TUỔI CỤ THỂ ('approx 26 years old') xuyên suốt cả 4 phân cảnh!
    - TUYỆT ĐỐI CẤM dùng từ chung chung trung tính ('Character', 'Person') làm AI vẽ lúc thì ra nam, lúc thì ra nữ!
    - Negative Prompt bắt buộc có: opposite gender, celebrity likeness, public figure, deepfake.

    🛑 KHÓA MẠCH TRUYỆN CHẶT CHẼ THEO TIÊU ĐỀ (THEMATIC ALIGNMENT LOCK):
    - Toàn bộ 4 phân cảnh (từ Cảnh 1 đến Cảnh 4) BẮT BUỘC phải phát triển nội dung, hành động và lời thoại bám sát 100% tiêu đề kịch bản và câu Hook gốc!
    - TUYỆT ĐỐI CẤM tiêu đề ghi một đằng mà nội dung 4 cảnh lại viết một nẻo.

    🛑 KHÓA KÍCH THƯỚC VẬT LÝ VÀ TỶ LỆ CHUẨN XÁC CỦA SẢN PHẨM (PHYSICAL SCALE INVARIANCE LOCK):
    - Sản phẩm BẮT BUỘC phải giữ nguyên một kích thước vật lý đời thực nhất quán xuyên suốt từ Cảnh 1 đến Cảnh 4 so với cơ thể người và bàn tay.
    - TUYỆT ĐỐI CẤM lỗi biến dạng kích thước (lúc to khổng lồ chiếm trọn khung hình, lúc lại teo nhỏ xíu như đồ chơi).

    🛑 100% CẢ 4 CẢNH LÀ NHÂN VẬT MỞ MIỆNG NÓI TRỰC TIẾP NGAY TỪ 0.00s (ON-CAMERA LIP-SYNC DIALOGUE AT 0.00s):
    - CẢ 4 CẢNH (CẢNH 1, 2, 3, 4) LỜI THOẠI ĐỀU BẮT ĐẦU NGAY TỪ 0.00s, KHẨU HÌNH NHÂN VẬT KHỚP TỪNG TỪ.
    - CẢNH 1: Bắt đầu ngay bằng câu Voice Hook ấn tượng do nhân vật nói trực tiếp trước camera tại 0.00s!
    - CẢNH 2: KOC xưng tôi/mình/em, nói chuyện tâm sự chỉ cho người xem xem tính năng hoặc mẹo hay. CẤM THUYẾT MINH!
    - Đồng nhất 100% chất giọng, tông giọng, độ tuổi và kiểu thoại xuyên suốt cả 4 cảnh.

    🛑 NGUYÊN TẮC PHỐI ĐỒ THỜI TRANG (SMART MIX & MATCH):
    1. THỜI TRANG PHỐI ĐỒ (is_fashion_styling = true): 
       - Khuôn mặt, kiểu tóc, màu tóc đen tuyền giữ nguyên 100%.
       - Trang phục ('scene_outfit_en'): Áp dụng các mẫu quần/chân váy phối đồ ăn khớp với hoàn cảnh từng cảnh.
    2. CÁC SẢN PHẨM KHÁC (is_fashion_styling = false): Trang phục khóa cứng 1 bộ suốt 4 cảnh.

    🛑 CƯỠNG CHẾ 100% GIỌNG HÀ NỘI CHUẨN:
    - 100% dùng từ 'nghìn' (CẤM TUYỆT ĐỐI TỪ 'NGÀN'). CẤM TUYỆT ĐỐI TỪ 'TRỢ GIÁ', 'PHIÊN LIVE'. CẤM giọng thuyết minh ngoài.
    - {char_rules}
    """

# ==============================================================================
# HÀM TẠO CHI TIẾT KỊCH BẢN - V161.0 HOÀN HẢO TOÀN DIỆN
# ==============================================================================
def create_scene_details(target_id, mode, style):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if str(sc.get("id")) == str(target_id)), None)
    if not outline: raise Exception(f"Không tìm thấy kịch bản #{target_id} trong danh sách dự án.")
    
    char_profiles = outline.get("character_profiles", st.session_state.get("character_profiles", []))
    char_rules = generate_char_rules_string(char_profiles)
    num_chars = outline.get("actors", outline.get("actor_count", len(char_profiles) if char_profiles else 1))
    
    current_active_mode = mode or st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    is_tiktok_shop = ("Viral" not in current_active_mode)
    is_viral = ("Viral" in current_active_mode)
    voice_guidance = build_voice_direction(current_active_mode, num_chars, char_profiles)
    
    detected_gender, detected_demographic_en = get_demographics_description(char_profiles)

    fixed_title = outline.get('title', 'Kịch bản chi tiết')
    fixed_hook = clean_and_normalize_voiceover(outline.get('hook', ''))
    fixed_setting_base = outline.get('setting', 'Không gian thực tế phù hợp')
    user_custom_note = outline.get("custom_note") or st.session_state.get("current_input_context", "").strip()
    presentation_format = outline.get("presentation_format") or st.session_state.get("last_presentation_format", "🌟 AI Tự Động Phân Tích & Đề Xuất")
    
    dna = st.session_state.get("content_analysis") or {}
    
    raw_price_anchor = dna.get("rounded_price_anchor", "")
    spelled_out_price_anchor = clean_and_normalize_voiceover(raw_price_anchor)

    # MA TRẬN NHÂN XƯNG ĐỒNG NHẤT
    self_pronoun = dna.get("self_pronoun") or "em"
    audience_pronoun = dna.get("audience_pronoun") or ("các chị em" if not is_viral else "mọi người")
    setting_archetype = dna.get("setting_archetype") or "Nhà phố / Chung cư hiện đại sạch sẽ"
    is_fixed_location = dna.get("is_fixed_location", True)

    # PHÂN TÍCH SƠ VIN ĐỘNG THEO THỜI TRANG & HOÀN CẢNH
    tuck_analysis_data = dna.get("tuck_in_analysis", {})
    locked_tuck_en = ""
    if isinstance(tuck_analysis_data, dict):
        locked_tuck_en = tuck_analysis_data.get("en_prompt_lock", "")
    
    if not locked_tuck_en:
        lower_setting = setting_archetype.lower()
        if is_fixed_location or any(k in lower_setting for k in ["bếp", "kitchen", "tắm", "phòng khách", "mặc nhà", "bàn ăn"]):
            locked_tuck_en = "shirt hem strictly cleanly untucked, resting naturally at hips for casual home comfort"
        else:
            locked_tuck_en = "shirt hem strictly neatly tucked into waistband with a clean flat waistline"

    # PHÂN TÍCH ẨM THỰC ĐA GIÁC QUAN
    culinary_info = dna.get("culinary_dna", {})
    is_culinary = False
    if isinstance(culinary_info, dict) and culinary_info.get("is_culinary"):
        is_culinary = True
    else:
        prod_kw = str(dna.get("what_and_unique", "")).lower()
        is_culinary = any(k in prod_kw for k in ["ăn", "thịt", "bánh", "tóp mỡ", "sốt", "mắm", "chả", "nem", "gà", "cá", "ẩm thực", "đồ ăn", "món"])

    condensed_dna = {
        "product": dna.get("what_and_unique", ""),
        "hero_sku": dna.get("hero_sku_color", ""),
        "color_lock": dna.get("product_color_lock", ""),
        "dimensions": dna.get("product_dimensions", "Kích thước đời thực chuẩn xác"),
        "product_scale_relative": dna.get("product_scale_relative", "Kích thước đời thực tương xứng bàn tay người lớn"),
        "mechanism": dna.get("lid_mechanism", "Kết cấu cơ học chuẩn xác theo đời thực"),
        "operational_mechanism": dna.get("operational_mechanism", "Cơ chế vận hành thực tế chuẩn xác của sản phẩm"),
        "correct_ergonomic_grip": dna.get("correct_ergonomic_grip", "Tư thế cầm nắm công thái học chuẩn đời thực"),
        "how_to_use": dna.get("how_to_use", "Thao tác sử dụng thực tế chuẩn công thái học"),
        "price_anchor": spelled_out_price_anchor or raw_price_anchor,
        "self_pronoun": self_pronoun,
        "audience_pronoun": audience_pronoun,
        "setting_archetype": setting_archetype,
        "is_fixed_location": is_fixed_location,
        "is_culinary": is_culinary,
        "culinary_sensory": culinary_info.get("sensory_cues", {}) if isinstance(culinary_info, dict) else {},
        "locked_tuck_en": locked_tuck_en,
        "recommended_setting_en": dna.get("recommended_setting_en", "tidy modern Vietnamese townhouse kitchen with clean stainless steel sink"),
        "recommended_wardrobe_en": dna.get("recommended_wardrobe_en", f"cream-white casual tee {locked_tuck_en} with beige linen apron"),
        "recommended_format": dna.get("recommended_format", "Review bóc hộp kết hợp trải nghiệm thực tế"),
        "fashion_mix_and_match": dna.get("fashion_mix_and_match_rules", {}),
        "connector_specs": dna.get("flexible_connector_specs", "Không có dây nối"),
        "assembly_structure": dna.get("product_assembly_structure", "Nguyên khối thực tế"),
        "anti_morph_targets": dna.get("strict_anti_morph_targets", "ống tiêm y tế xylanh, que nhựa đơn chiếc"),
        "visual_dna": dna.get("prompt_dna_lock", "")
    }

    fallback_prod_name = f"authentic {condensed_dna.get('hero_sku', '')} {condensed_dna.get('product', 'product')}".strip()
    clean_prod_en = sanitize_third_party_ip(fallback_prod_name)

    if is_viral:
        scene4_instruction = f"""
        🛑 CHỈ THỊ CẢNH 4 CHO THỂ LOẠI VIRAL & XÂY KÊNH (TUYỆT ĐỐI KHÔNG BÁN HÀNG):
        - Sử dụng đúng cặp nhân xưng: KOC xưng '{self_pronoun}', gọi người xem là '{audience_pronoun}'.
        - Đoạn thoại dưới 28 từ, chuẩn giọng Hà Nội tự nhiên ấm áp, câu văn mượt mà truyền cảm.
        - Kêu gọi tương tác, đặt câu hỏi gợi mở thảo luận hoặc chia sẻ mẹo hay + mời Follow kênh đón xem video tiếp theo.
        - TUYỆT ĐỐI CẤM: Không nhắc đến giá tiền, voucher, giảm giá, mua hàng hay giỏ hàng!
        """
        scene4_sample = f"Đoạn thoại kết nối người xem tự nhiên dưới 28 từ: {audience_pronoun} còn mẹo nào hay hơn thì chia sẻ bên dưới cho {self_pronoun} biết nhé, và đừng quên bấm follow kênh để đón xem video sau!"
    else:
        scene4_instruction = f"""
        🛑 CHỈ THỊ CẢNH 4 CHO TIKTOK SHOP (CẢ GIÁ GỐC + GIÁ GIẢM KÍCH THÍCH + MIỄN TRỪ THỜI ĐIỂM < 30 TỪ):
        - Lời thoại Cảnh 4 chuẩn giọng Hà Nội, tuân thủ đúng 3 vế xuôi tai:
          1. Neo giá thực tế & Báo giá giảm kích thích: 'Bình thường set này hơn [X] nghìn, đợt này áp mã voucher vào chỉ còn khoảng [Y] mấy nghìn thôi...' (hoặc 'giá gốc khoảng [X] nghìn, áp mã vào còn tầm [Y] mấy nghìn...')
          2. Miễn trừ thời điểm chống quét bot sai lệch giá: 'nhưng giá từng thời điểm có thể khác nhau tùy đợt ưu đãi...' (hoặc 'tùy thời điểm giá sẽ khác nhau...')
          3. Rào kiểm tra tài khoản + CTA: '{audience_pronoun} cứ bấm góc trái kiểm tra tài khoản mình xem nhé!'
        - QUY TẮC SỐ BỐN: Đọc là 'bốn' (bốn mươi nghìn, một trăm bốn mươi nghìn...). CẤM TUYỆT ĐỐI 'tư'.
        - BẮT BUỘC gọi người xem là '{audience_pronoun}' và xưng là '{self_pronoun}'. CẤM gọi 'các mẹ' nếu audience_pronoun là '{audience_pronoun}'.
        - ĐỌC CHUẨN XÁC SỐ TIỀN BẰNG CHỮ: Tham khảo phiên âm chuẩn: '{condensed_dna.get("price_anchor")}'. Đọc chuẩn xác các hàng đơn vị, chục, trăm, nghìn (CẤM đọc lộn số!).
        - Tuyệt đối không yêu cầu hiện chữ/text trên màn hình video!
        """
        scene4_sample = f"Bình thường khoảng [X] nghìn, áp voucher còn tầm [Y mấy nghìn] thôi, nhưng giá từng thời điểm có thể khác nhau, {audience_pronoun} cứ bấm góc trái kiểm tra tài khoản mình nhé!"

    culinary_special_directive = """
    🛑 CHỈ ĐẠO ĐẶC BIỆT DÀNH CHO ẨM THỰC / MÓN ĂN:
    - Cảnh 1: Cận cảnh/Macro Food-porn cắn thử miếng ăn bóng bẩy hoặc mỡ sôi giòn rụm, âm thanh cắn giòn ASMR.
    - Cảnh 2: Siêu cận bẻ đôi chậm rãi lộ ruột xốp rỗng, vụn giòn rơi nhẹ.
    - Cảnh 3: Góc 45 độ chấm ngập vào bát sốt sền sệt, vi biểu cảm 3 nhịp hưởng thụ vị giác đỉnh cao.
    - Cảnh 4: Kết thúc với đĩa/hộp thành phẩm sạch sẽ hấp dẫn.
    """ if is_culinary else ""

    prompt_text = f"""
    THÔNG TIN NỀN TẢNG: {json.dumps(condensed_dna, ensure_ascii=False)}
    THỂ LOẠI VIDEO: '{current_active_mode}'
    KỊCH BẢN #{target_id}: 
    - TIÊU ĐỀ: '{fixed_title}'
    - HOOK GỐC: '{fixed_hook}'
    - BỐI CẢNH KỊCH BẢN: {fixed_setting_base}
    - HÌNH THỨC VIDEO: '{presentation_format}'
    - DIỄN VIÊN CHỈ ĐỊNH: BẮT BUỘC KHÓA CHẶT: {detected_demographic_en} (CẤM ĐỔI GIỚI TÍNH/DIỆN MẠO QUA CÁC CẢNH!).
    - MA TRẬN NHÂN XƯNG CƯỠNG CHẾ: KOC tự xưng là '{self_pronoun}', gọi người xem là '{audience_pronoun}'. CẢ 4 PHÂN CẢNH BẮT BUỘC tuân thủ đúng cặp nhân xưng này!
    - QUY CHUẨN BỐI CẢNH: {setting_archetype} ({'Khóa 1 vị trí cố định qua cả 4 cảnh' if is_fixed_location else 'Chuyển cảnh theo mạch truyện'}). CẤM nhà cấp 4 tồi tàn, CẤM biệt thự xa hoa.
    - QUY CHUẨN SƠ VIN: Khóa cứng '{locked_tuck_en}' đồng nhất 100% qua cả 4 phân cảnh.
    - HÌNH THỨC NÓI: 100% Lời thoại do CHÍNH NHÂN VẬT MỞ MIỆNG NÓI TRỰC TIẾP TRƯỚC ỐNG KÍNH (ON-CAMERA LIP-SYNC) NGAY TỪ 0.00S Ở CẢ 4 CẢNH (CẢNH 1, 2, 3, 4). TUYỆT ĐỐI CẤM THUYẾT MINH NGOÀI. TUYỆT ĐỐI CẤM TỪ 'NGÀN' (PHẢI DÙNG TỪ 'NGHÌN'). TUYỆT ĐỐI CẤM TỪ 'TRỢ GIÁ'.
    {culinary_special_directive}
    
    🛑 CHỈ THỊ ƯU TIÊN 1: NGHỆ THUẬT KỂ CHUYỆN VĂN HỌC & GIỚI HẠN THỜI LƯỢNG VEO 3 (TỐI ĐA 10 GIÂY/CẢNH)
    - CẢNH 1 HOÀN TOÀN CÓ THỂ DÀI 7s, 8s, 9s HOẶC 10s nếu mở đầu bằng một câu chuyện đời thường ấn tượng, tình huống kịch tính hoặc nỗi niềm chạm cảm xúc.
    - CÁC CẢNH 2, 3, 4 LINH HOẠT THỜI LƯỢNG tùy theo mạch kể chuyện.
    - BẮT BUỘC MỖI PHÂN CẢNH DÀI TỐI ĐA 10 GIÂY (đã bao gồm đệm diễn xuất).
    - TRẦN SỐ TỪ AN TOÀN CHO MỖI CẢNH (ĐỂ KHÔNG VƯỢT QUÁ 10 GIÂY VEO 3): Cảnh 1 (18-35 từ), Cảnh 2 (20-35 từ), Cảnh 3 (20-35 từ), Cảnh 4 (dưới 30 từ).
    - QUY TẮC SỐ BỐN: Đọc là 'bốn' (mười bốn, hai mươi bốn, bốn mươi, bốn trăm...). TUYỆT ĐỐI CẤM 'tư'.
    - Câu thoại viết theo lối văn nói trực diện của người Hà Nội: Chủ ngữ -> Vị ngữ -> Cảm xúc/Hiệu quả. CẤM mở câu bằng 'Với thiết kế...', 'Được làm từ...'.
    - Lời thoại phải xuôi tai, cuốn hút, kết nối mượt mà giữa 4 cảnh, nói tự nhiên như người thật trò chuyện, tuyệt đối không lủng củng như dịch máy!
    
    🛑 CHỈ THỊ ƯU TIÊN 2: KHÓA CHẶT GIỚI TÍNH, ĐỘ TUỔI & TRẠNG THÁI SƠ VIN QUA CẢ 4 CẢNH
    - Diễn viên chính: {detected_demographic_en}.
    - CẢ 4 PHÂN CẢNH (Cảnh 1, 2, 3, 4) BẮT BUỘC mô tả đúng nhân vật {detected_demographic_en}. TUYỆT ĐỐI CẤM dùng từ chung chung 'Character' hay 'Person'!
    - KHÓA CỨNG TRẠNG THÁI SƠ VIN: Bắt buộc dùng '{locked_tuck_en}' và GIỮ NGUYÊN 100% QUA CẢ 4 CẢNH!
    
    {scene4_instruction}

    🛑 CHỈ THỊ ƯU TIÊN 3: KHÓA MẠCH TRUYỆN THEO ĐÚNG TIÊU ĐỀ '{fixed_title}' VÀ ĐỒNG NHẤT KÍCH THƯỚC VẬT LÝ
    - Số đo thực tế: '{condensed_dna.get("dimensions")}'.
    - Tỷ lệ kích thước sản phẩm: '{condensed_dna.get("product_scale_relative")}' (bất biến qua 4 cảnh so với bàn tay và thân người).
    - CẢ 4 CẢNH BẮT ĐẦU NÓI NGAY TỪ 0.00S.
    - NẾU LÀ SẢN PHẨM THỜI TRANG (is_fashion_styling = true): Áp dụng các mẫu quần/chân váy cụ thể từ 'fashion_mix_and_match' vào 'scene_outfit_en'.
    - HÀNH ĐỘNG THỰC TẾ SỐNG ĐỘNG (action_en): Mô tả hành động cụ thể chân thực bằng tiếng Anh gắn liền với tính năng/hương vị sản phẩm mà không lặp lại từ 'Character'.
    
    ĐỊNH DẠNG JSON TRẢ VỀ:
    {{
        "title": "{fixed_title}",
        "is_fashion_styling": true/false,
        "presentation_format_used": "{presentation_format}",
        "voice": {{"tone": "{voice_guidance}"}},
        "outfit_vi": "Mô tả chi tiết trang phục kèm trạng thái sơ vin/thả ngoài phù hợp với bối cảnh {fixed_setting_base}",
        "clean_product_name_en": "Concise photorealistic English description of hero product under 10 words",
        "product_scale_en": "approx real-life dimensions matching adult hand-scale",
        "connector_physics_en": "none",
        "character_matrix": {{
            "full_characters_appearance": "{detected_demographic_en}, authentic Vietnamese facial features, warm skin tone, strictly non-celebrity persona",
            "locked_hairstyles": "neat tidy jet-black hair",
            "locked_tops": "casual top",
            "locked_tuck_style": "{locked_tuck_en}",
            "locked_bottoms": "trousers",
            "locked_setting": "{condensed_dna.get('recommended_setting_en')}"
        }},
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention",
                "setting": "Mô tả bối cảnh mở màn bám sát {fixed_setting_base}...",
                "setting_en": "{condensed_dna.get('recommended_setting_en')}",
                "scene_outfit_en": "Mô tả trang phục phối đồ nếu is_fashion_styling = true",
                "camera_shot": "{'Vertical 9:16 macro close-up food shot' if is_culinary else 'Vertical 9:16 eye-level medium shot'}",
                "expression": "Ánh mắt đồng cảm, nụ cười hào hứng mở màn nhìn thẳng camera",
                "expression_en": "{'anticipating delicious bite with focused appetite' if is_culinary else 'looking at camera with an empathetic warm smile'}",
                "action_en": "{'taking a crisp loud bite of the glistening food close to camera, tiny crumbs falling' if is_culinary else 'holding product steadily at chest level with invariant real-life scale, establishing clear focus'}",
                "sfx": "{'Tiếng cắn rộp rộp đanh giòn ASMR' if is_culinary else 'Tiếng mở hộp hoặc âm thanh đời thực nhẹ nhàng'}",
                "director": "Attention | Bám sát tiêu đề '{fixed_title}' | Câu xuôi chuẩn tiếng Hà Nội | Thoại on-camera từ 0.00s",
                "voiceover": "Đoạn thoại mở màn cuốn hút tự nhiên bám sát tiêu đề '{fixed_title}' (từ 18-35 từ) xưng '{self_pronoun}' gọi '{audience_pronoun}' bằng tiếng Hà Nội chuẩn xuôi tai, dùng từ 'nghìn', số 4 đọc là 'bốn'..."
            }},
            {{
                "scene": 2, "aida_stage": "Interest",
                "setting": "Mô tả bối cảnh góc quay ngang tầm mắt thấy rõ người và bàn thao tác...",
                "setting_en": "{condensed_dna.get('recommended_setting_en')}",
                "scene_outfit_en": "Mô tả trang phục nếu is_fashion_styling = true",
                "camera_shot": "{'Vertical 9:16 extreme macro close-up cross-section shot' if is_culinary else 'Vertical 9:16 eye-level medium close-up'}",
                "expression": "Ánh mắt bừng sáng, thần thái hào hứng chia sẻ trực tiếp với người xem",
                "expression_en": "speaking enthusiastically with bright attentive eyes",
                "action_en": "{'slowly snapping the food in half with fingers to display airy hollow crisp interior texture' if is_culinary else 'demonstrating key functional texture or mechanism with steady hands in sharp focus'}",
                "sfx": "{'Tiếng bẻ rắc giòn tan đanh chắc' if is_culinary else 'Tiếng cơ học đanh chắc hoặc tiếng vuốt chất liệu ASMR'}",
                "director": "Interest | Đặc tả chi tiết cơ chế hoặc giá trị bài học bám sát tiêu đề '{fixed_title}' | Thoại on-camera từ 0.00s",
                "voiceover": "Đoạn thoại KOC nói trực tiếp bằng tiếng Hà Nội chuẩn xưng '{self_pronoun}' gọi '{audience_pronoun}' câu văn xuôi tai đào sâu đúng nội dung '{fixed_title}' (từ 20-35 từ)..."
            }},
            {{
                "scene": 3, "aida_stage": "Desire",
                "setting": "Mô tả bối cảnh trải nghiệm thực tế sinh động bám sát {fixed_setting_base}...",
                "setting_en": "{condensed_dna.get('recommended_setting_en')}",
                "scene_outfit_en": "Mô tả trang phục nếu is_fashion_styling = true",
                "camera_shot": "{'Vertical 9:16 close-up 45-degree tasting shot' if is_culinary else 'Vertical 9:16 eye-level lifestyle shot'}",
                "expression": "Nụ cười mãn nguyện, ánh mắt ánh lên sự thỏa mãn, gật đầu khẳng định",
                "expression_en": "{'eyes widening in delightful flavor shock then nodding approvingly with pure satisfaction' if is_culinary else 'smiling contentedly with an approving head nod'}",
                "action_en": "{'dipping deeply into rich glistening thick sauce and chewing contentedly' if is_culinary else 'performing practical real-world task with the product, displaying immediate effective results'}",
                "sfx": "{'Tiếng nhai giòn rụm và tiếng chấm sốt sền sệt' if is_culinary else 'Tiếng giác quan đời sống thực tế'}",
                "director": "Desire | Trải nghiệm công năng hoặc góc nhìn sâu sắc bám sát tiêu đề '{fixed_title}' | Thoại on-camera từ 0.00s",
                "voiceover": "Đoạn thoại KOC nói trực tiếp đặc tả trải nghiệm thực tế bám sát '{fixed_title}' xưng '{self_pronoun}' gọi '{audience_pronoun}' nối tiếp tự nhiên từ cảnh 2 bằng tiếng Hà Nội chuẩn xuôi tai (từ 20-35 từ)..."
            }},
            {{
                "scene": 4, "aida_stage": "Action",
                "setting": "Mô tả bối cảnh kết thúc ấm áp bám sát {fixed_setting_base}...",
                "setting_en": "{condensed_dna.get('recommended_setting_en')}",
                "scene_outfit_en": "Mô tả trang phục nếu is_fashion_styling = true",
                "camera_shot": "Vertical 9:16 warm eye-level closing shot",
                "expression": "Nụ cười rạng rỡ, ánh mắt chân thành ấm áp, hai bàn tay mở tự nhiên hướng về camera",
                "expression_en": "smiling warmly into lens with open welcoming hands",
                "action_en": "speaking with welcoming open-palm gestures, product neatly placed nearby in realistic position",
                "sfx": "Tiếng chuông ting trong trẻo vui tai",
                "director": "{'Action | Kêu gọi tương tác thảo luận & follow kênh (CẤM giá/giỏ hàng) | Khởi động: 0.00s' if is_viral else 'Action | Chốt deal giá gốc + giá giảm kích thích + miễn trừ thời điểm (CẤM chữ trên màn hình) | Khởi động: 0.00s'}",
                "voiceover": "{scene4_sample}"
            }}
        ]
    }}
    """
    sys_inst = get_sys_inst_details(
        mode=current_active_mode, style=style, narrator_mode="On-camera",
        char_rules=char_rules, duration_instruction="Thời lượng động sinh học tối đa 10s",
        num_chars=num_chars, character_profiles=char_profiles,
        custom_note=user_custom_note, presentation_format=presentation_format,
        self_pronoun=self_pronoun, audience_pronoun=audience_pronoun,
        setting_archetype=setting_archetype, is_fixed_location=is_fixed_location
    )
    res = call_gemini([prompt_text], sys_inst, max_tokens=6500)
    if not res: raise Exception("AI không phản hồi hoặc trả về dữ liệu rỗng. Vui lòng bấm tạo lại.")
    
    scenes = res.get("scenes") or res.get("script") or []
    if not scenes: raise Exception("AI không tạo được danh sách phân cảnh. Vui lòng bấm tạo lại.")
    
    c_mat = res.get("character_matrix") or {}
    full_char = c_mat.get("full_characters_appearance") or f"{detected_demographic_en}, authentic natural Vietnamese facial features, warm skin tone"
    locked_hair = c_mat.get("locked_hairstyles") or "neat tidy jet-black hair"
    locked_tops = c_mat.get("locked_tops") or "casual top"
    locked_tuck = c_mat.get("locked_tuck_style") or locked_tuck_en
    locked_bottoms = c_mat.get("locked_bottoms") or "comfortable trousers"
    default_setting = c_mat.get("locked_setting") or condensed_dna.get("recommended_setting_en") or (outline.get("setting") or "warm realistic indoor setting")
    
    is_fashion_styling = res.get("is_fashion_styling", False)
    clean_prod_en = sanitize_third_party_ip(res.get("clean_product_name_en") or fallback_prod_name)
    product_scale_en = res.get("product_scale_en") or "approx real-life dimensions matching adult hand-scale"
    
    connector_physics_en = res.get("connector_physics_en", "").strip()
    connector_phrase = f", {connector_physics_en}" if connector_physics_en and connector_physics_en.lower() not in ["none", "không có dây nối", "no cable"] else ""
    
    actor_base = f"{full_char}, neat {locked_hair}"
    wardrobe_str = f"wearing {locked_tops}, {locked_tuck}, and {locked_bottoms}"
    
    # BỘ CHẶN ĐỜI THỰC THẤU CẢM: TRIỆT TIÊU NHÀ CẤP 4 TỒI TÀN & BIỆT THỰ XA HOA & LỆCH SƠ VIN
    realism_blockers = "dilapidated house, old rural hut, dirty kitchen, stained wall, peeling paint, messy background, luxury palace, ultra-luxury mansion, golden decorations, hyper-luxurious penthouse, tucked shifting to untucked, untucked shifting to tucked, inconsistent waistband"
    
    total_sec = 0.0
    for scn in scenes:
        if "voiceover" in scn: 
            scn["voiceover"] = clean_and_normalize_voiceover(scn["voiceover"])
        if "director" in scn: 
            scn["director"] = sanitize_policy_text(scn["director"])
        
        # THUẬT TOÁN THỜI LƯỢNG ĐỘNG SINH HỌC - KHÓA CỨNG TỐI ĐA 10 GIÂY VEO 3
        raw_speech_time = calculate_speech_duration(scn.get("voiceover", ""), is_tiktok_shop)
        acting_cushion = 1.0 if is_tiktok_shop else 1.3
        
        dynamic_scene_sec = min(10, max(4, math.ceil(raw_speech_time + acting_cushion)))
        
        if raw_speech_time >= dynamic_scene_sec:
            actual_speech_time = round(dynamic_scene_sec - 0.8, 1)
        else:
            actual_speech_time = raw_speech_time
            
        final_bucket = f"{dynamic_scene_sec}s"
        scn["dur"] = final_bucket
        scn["actual_speech_sec"] = actual_speech_time
        total_sec += float(dynamic_scene_sec)
        
        camera_shot = scn.get("camera_shot", "Vertical 9:16 eye-level medium shot")
        sfx_sound = scn.get("sfx", "Natural Foley sound")
        micro_expr_en = scn.get("expression_en", "looking at camera with a natural confident smile")
        scene_num = scn.get("scene", 1)
        
        # KHÓA TỌA ĐỘ VẬT LÝ NẾU IS_FIXED_LOCATION = TRUE
        if is_fixed_location:
            scene_setting_en = default_setting
        else:
            scene_setting_en = scn.get("setting_en") or default_setting
        
        # TỐI ƯU TRANG PHỤC & KHÓA SƠ VIN ĐỒNG NHẤT
        if is_fashion_styling:
            active_outfit = f"wearing {scn.get('scene_outfit_en') or wardrobe_str}"
            img_neg = f"opposite gender, celebrity likeness, public figure, inconsistent scale, oversized, miniaturized, deformed hands, extra fingers, text, watermark, subtitles, morphed plastic, {realism_blockers}"
            vid_neg = f"opposite gender, celebrity likeness, inconsistent scale, oversized, deformed hands, extra fingers, text, watermark, morphed object, {realism_blockers}"
        else:
            active_outfit = f"strictly wearing identical {wardrobe_str} across all scenes"
            img_neg = f"opposite gender, changing clothes, different outfit, celebrity likeness, public figure, inconsistent scale, oversized, miniaturized, deformed hands, extra fingers, text, watermark, subtitles, morphed plastic, {realism_blockers}"
            vid_neg = f"opposite gender, changing clothes, different outfit, celebrity likeness, inconsistent scale, oversized, deformed hands, extra fingers, text, watermark, morphed object, {realism_blockers}"
            
        actor_full = f"{actor_base}, {active_outfit}"
        
        # GIỮ HÀNH ĐỘNG THỰC TẾ SỐNG ĐỘNG CỦA TỪNG PHÂN CẢNH
        raw_action = scn.get("action_en") or f"demonstrating {clean_prod_en} with steady hands"
        clean_action = re.sub(r'^(?:Character\s+(?:is\s+)?|Subject\s+(?:is\s+)?)', '', raw_action, flags=re.IGNORECASE).strip()
        clean_action = re.sub(r'\[.*?\]', '', clean_action).strip()
        
        # PROMPT ẢNH SIÊU TINH GỌN (100% TIẾNG ANH, KHÔNG LẶP TỪ)
        if is_culinary:
            if scene_num == 1:
                scene_focus = f"Macro close-up food shot in {scene_setting_en}. {clean_prod_en} glistening with rich glossy sauce, steam rising. {actor_full}. {micro_expr_en}, {clean_action}."
            elif scene_num == 2:
                scene_focus = f"Extreme macro food cross-section in {scene_setting_en}. {actor_full}. {micro_expr_en}, {clean_action}, highlighting airy crisp texture."
            elif scene_num == 3:
                scene_focus = f"Close-up 45-degree tasting shot in {scene_setting_en}. {actor_full}. {micro_expr_en}, {clean_action}."
            else:
                scene_focus = f"Warm closing shot in {scene_setting_en}. {actor_full}. {micro_expr_en}, holding authentic package of {clean_prod_en}."
        else:
            if scene_num == 1:
                scene_focus = f"Establishing shot in {scene_setting_en}. {actor_full}. {micro_expr_en}, holding {clean_prod_en} at chest level, open packaging nearby."
            elif scene_num == 2:
                scene_focus = f"Medium close-up in {scene_setting_en}. {actor_full}. {micro_expr_en}, {clean_action}, holding {clean_prod_en} with steady hands."
            elif scene_num == 3:
                scene_focus = f"Lifestyle shot in {scene_setting_en}. {actor_full}. {micro_expr_en}, {clean_action}, demonstrating practical benefits."
            else:
                scene_focus = f"Commercial closing in {scene_setting_en}. {actor_full}. {micro_expr_en}, holding {clean_prod_en} beside them."
            
        raw_img = (
            f"{camera_shot}. {scene_focus} "
            f"Authentic rigid {clean_prod_en} with invariant 1:1 real-life proportions ({product_scale_en}). "
            f"Commercial photography, clean soft studio-lifestyle lighting, 8k sharp focus. "
            f"Negative prompt: {img_neg}."
        )
        scn["img_p"] = sanitize_third_party_ip(raw_img)
        
        # PROMPT VIDEO SIÊU TINH GỌN (VEO 3 SAFE: MỎ NEO NGỮ ÂM HÀ NỘI CHUẨN, SẠCH RÁC CODE & GIỮ HÀNH ĐỘNG CHÂN THỰC)
        speaker_line = scn.get("voiceover", "")
        audio_anchor = "Audio Direction: Spoken in clear authentic native Northern Vietnamese Hanoi accent, local Hanoi urban cadence, crisp natural conversational pacing, zero Southern dialect bleed."
        
        if is_viral and scene_num == 4:
            action_phrase = "Hands in welcoming natural open-palm gestures, speaking directly into camera"
        else:
            action_phrase = f"Character visibly performing: {clean_action}. Steady hands interacting with rigid {clean_prod_en} ({product_scale_en}){connector_phrase}, zero wrist wobble, zero plastic morphing"

        raw_vid = (
            f"{camera_shot}. Commercial live-action footage. Setting: {scene_setting_en}. Subject: {actor_full}. "
            f"Action: Visibly speaking directly to camera with natural on-camera lip-sync from 0.00s. {audio_anchor} Spoken audio: \"{speaker_line}\", Foley: [{sfx_sound}]. "
            f"{action_phrase}. "
            f"Pure camera footage, strictly no text, no subtitles, no UI overlay. "
            f"Negative prompt: {vid_neg}."
        )
        scn["vid_p"] = sanitize_veo3_prompt(raw_vid)
        
    res["scenes"] = scenes
    res["total_dur"] = f"Khoảng {int(total_sec)} giây"
    
    # BẢNG TỔNG QUAN TINH GỌN 4 DÒNG CỐT LÕI
    goal_badge = "🌟 <b>Định hướng:</b> Xây Kênh & Kéo Tương Tác / Follow (Không bán hàng)" if is_viral else "🛒 <b>Định hướng:</b> Chốt đơn TikTok Shop an toàn"
    summary_lines = [
        f"⏱ <b>Thời lượng:</b> Khoảng {int(total_sec)}s (Thời lượng động sinh học $\le$ 10s/cảnh) | 🎬 <b>Hình thức:</b> {presentation_format} | 👤 <b>Khóa diễn viên:</b> {detected_demographic_en}",
        f"🗣 <b>Đại từ xưng hô:</b> '{self_pronoun}' - '{audience_pronoun}' | 🏙 <b>Bối cảnh chuẩn:</b> {setting_archetype} ({'Khóa 1 vị trí cố định' if is_fixed_location else 'Chuyển cảnh linh hoạt'}) | {goal_badge}",
        f"👗 <b>Trang phục & Cạp áo:</b> {res.get('outfit_vi', 'Trang phục đời thường phù hợp bối cảnh')} (Đồng nhất 100%)",
        f"🛠 <b>Đặc điểm sản phẩm:</b> {condensed_dna.get('dimensions')} - {condensed_dna.get('operational_mechanism', '')}"
    ]
    
    if user_custom_note and user_custom_note.lower() not in ["mặc định chuẩn", "không có", "không có ghi chú đặc biệt, tuân thủ kịch bản chuẩn."]:
        summary_lines.append(f"🎯 <b>Ghi chú riêng:</b> {user_custom_note}")
        
    res["director_summary"] = "<br>".join(summary_lines)
    
    st.session_state.generated_details[int(target_id)] = res
    st.session_state.generated_details[str(target_id)] = res

def clone_script(script_id):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    style = st.session_state.get("last_style", "Điện Ảnh Chân Thực")
    is_viral = ("Viral" in mode)
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if str(sc.get("id")) == str(script_id)), None)
    if not target: return []
    
    cur_len = len(all_combined)
    target_detail = st.session_state.generated_details.get(int(script_id), st.session_state.generated_details.get(str(script_id), {}))
    user_custom_note = target.get("custom_note") or st.session_state.get("current_input_context", "").strip()
    presentation_format = target.get("presentation_format") or st.session_state.get("last_presentation_format", "🌟 AI Tự Động Phân Tích & Đề Xuất")
    
    original_voices = []
    if target_detail and "scenes" in target_detail:
        for s in target_detail["scenes"]:
            original_voices.append(f"- Cảnh {s.get('scene')} ({s.get('aida_stage')}): \"{s.get('voiceover')}\"")
        full_voice_text = "\n".join(original_voices)
    else:
        full_voice_text = f"- Hook 3s đầu: \"{target.get('hook', '')}\""

    dna = st.session_state.get("content_analysis") or {}
    self_pronoun = dna.get("self_pronoun", "em")
    audience_pronoun = dna.get("audience_pronoun", "các chị em" if not is_viral else "mọi người")
    condensed_dna = {
        "product": dna.get("what_and_unique", ""),
        "hero_sku": dna.get("hero_sku_color", ""),
        "price_anchor": dna.get("rounded_price_anchor", ""),
        "self_pronoun": self_pronoun,
        "audience_pronoun": audience_pronoun
    }

    target_actors_count = target.get("actors", 1)
    target_char_profiles = target.get("character_profiles", st.session_state.get("character_profiles", []))

    if is_viral:
        mission_text = f"""
        NHIỆM VỤ NHÂN BẢN: Giữ nguyên 90% nội dung, ý tưởng, phong cách và thông điệp của kịch bản gốc.
        🛑 TUYỆT ĐỐI CẤM các từ ngữ công nghệ/máy móc/rác AI: CẤM 'thuật toán gợi ý', CẤM 'máy vừa phân tích', CẤM 'hệ thống vừa báo', CẤM 'AI phát hiện', CẤM 'theo phân tích'...
        - Chỉ đổi mới: Bối cảnh sinh hoạt và biến tấu câu từ một chút cho mới mẻ (paraphrase tự nhiên, đổi cách mở màn đời thường), nhưng GIỮ NGUYÊN giải pháp và thông điệp cốt lõi.
        - Sử dụng đúng đại từ KOC xưng '{self_pronoun}' và gọi khán giả là '{audience_pronoun}'.
        - QUY TẮC SỐ BỐN: Đọc là 'bốn' (mười bốn, hai mươi bốn, bốn mươi...). CẤM TUYỆT ĐỐI 'tư'.
        - Lời thoại dưới 35 từ/cảnh, chuẩn văn nói Hà Nội xuôi tai. Cảnh 4 kêu gọi thảo luận hoặc follow kênh (CẤM bán hàng/giá).
        """
    else:
        mission_text = f"""
        NHIỆM VỤ NHÂN BẢN: Giữ nguyên 90% nội dung, ý tưởng, phong cách và thông điệp của kịch bản gốc.
        🛑 TUYỆT ĐỐI CẤM các từ ngữ công nghệ/máy móc/rác AI: CẤM 'thuật toán gợi ý', CẤM 'máy vừa phân tích', CẤM 'hệ thống vừa báo', CẤM 'AI phát hiện', CẤM 'theo phân tích'...
        - Chỉ đổi mới: Bối cảnh sinh hoạt và biến tấu câu từ một chút cho mới mẻ (paraphrase tự nhiên, đổi cách mở màn đời thường), nhưng GIỮ NGUYÊN công năng, nỗi đau và đòn bẩy neo giá của kịch bản gốc.
        - Cảnh 4 tuân thủ đúng công thức: Neo giá gốc + Giá giảm kích thích + Miễn trừ thời điểm ('nhưng giá từng thời điểm có thể khác nhau...') + CTA kiểm tra tài khoản.
        - Sử dụng đúng đại từ KOC xưng '{self_pronoun}' và gọi khán giả là '{audience_pronoun}'.
        - QUY TẮC SỐ BỐN: Đọc là 'bốn' (bốn mươi nghìn, một trăm bốn mươi nghìn...). CẤM TUYỆT ĐỐI 'tư'.
        - Lời thoại dưới 35 từ/cảnh, đọc chính xác từng con số tiền bằng chữ, chuẩn văn nói Hà Nội xuôi tai.
        """

    prompt = f"""
    SẢN PHẨM / CHỦ ĐỀ: {json.dumps(condensed_dna, ensure_ascii=False)} | KỊCH BẢN GỐC #{script_id}: TIÊU ĐỀ: '{target.get('title', '')}'
    THOẠI GỐC:\n{full_voice_text}
    HÌNH THỨC VIDEO: '{presentation_format}'
    GHI CHÚ AI TỪ NGƯỜI DÙNG: '{user_custom_note}'
    DIỄN VIÊN KHÓA CỐ ĐỊNH: {target_actors_count} nhân vật theo kịch bản gốc.
    ĐẠI TỪ BẮT BUỘC: Xưng '{self_pronoun}' - Gọi '{audience_pronoun}'.
    {mission_text}
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên biến thể 1", "setting": "Bối cảnh đời thực 1...", "hook": "Câu hook ngắn gọn do nhân vật nói trực tiếp bám sát kịch bản gốc...", "actors": {target_actors_count} }},
            {{ "id": {cur_len+2}, "title": "Tên biến thể 2", "setting": "Bối cảnh đời thực 2...", "hook": "...", "actors": {target_actors_count} }},
            {{ "id": {cur_len+3}, "title": "Tên biến thể 3", "setting": "Bối cảnh đời thực 3...", "hook": "...", "actors": {target_actors_count} }},
            {{ "id": {cur_len+4}, "title": "Tên biến thể 4", "setting": "Bối cảnh đời thực 4...", "hook": "...", "actors": {target_actors_count} }},
            {{ "id": {cur_len+5}, "title": "Tên biến thể 5", "setting": "Bối cảnh đời thực 5...", "hook": "...", "actors": {target_actors_count} }}
        ]
    }}
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, "On-camera", "", target_actors_count, "Nhân bản thoại trung thành", user_custom_note, presentation_format), max_tokens=2500)
    clones = res.get("outlines", res.get("script_outlines", []))
    formatted_clones = []
    for idx, cl in enumerate(clones):
        formatted_clones.append({
            "id": cur_len + idx + 1, "title": cl.get("title", f"Biến thể kịch bản #{cur_len + idx + 1}"),
            "setting": cl.get("setting", f"Bối cảnh sinh hoạt #{idx+1}"), "hook": clean_and_normalize_voiceover(cl.get("hook", "")),
            "actors": target_actors_count, "character_profiles": target_char_profiles,
            "duration_instruction": target.get("duration_instruction", "Thời lượng động sinh học tối đa 10s"), 
            "narrator_mode": "Nhân vật xuất hiện (On-camera)",
            "custom_note": user_custom_note,
            "presentation_format": presentation_format
        })
    return formatted_clones

def generate_more_scripts(angle, num_chars, extra_char_inputs, narrator_mode_more, duration_inst, char_profiles, extra_note="", presentation_format=""):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    style = st.session_state.get("last_style", "Điện Ảnh Chân Thực")
    is_viral = ("Viral" in mode)
    char_rules = generate_char_rules_string(char_profiles)
    cur_len = len(st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts)
    active_note = extra_note.strip() if extra_note.strip() else st.session_state.get("current_input_context", "").strip()
    active_format = presentation_format if presentation_format else st.session_state.get("last_presentation_format", "🌟 AI Tự Động Phân Tích & Đề Xuất")
    dna = st.session_state.get("content_analysis") or {}
    self_pronoun = dna.get("self_pronoun", "em")
    audience_pronoun = dna.get("audience_pronoun", "các chị em" if not is_viral else "mọi người")
    condensed_dna = {
        "product": dna.get("what_and_unique", ""), "hero_sku": dna.get("hero_sku_color", ""), "price_anchor": dna.get("rounded_price_anchor", ""),
        "self_pronoun": self_pronoun, "audience_pronoun": audience_pronoun
    }

    if is_viral:
        special_viral_rule = f"THỂ LOẠI VIRAL & XÂY KÊNH: Tập trung vào nội dung giữ chân, chia sẻ kiến thức, bài học thực tế, câu chuyện chạm cảm xúc. Xưng '{self_pronoun}', gọi '{audience_pronoun}'. Câu văn xuôi tai chuẩn văn nói người Hà Nội, tối đa 35 từ/cảnh. Cảnh 4 kêu gọi thảo luận hoặc follow kênh. TUYỆT ĐỐI KHÔNG BÁN HÀNG, KHÔNG NHẮC ĐẾN GIÁ CẢ, VOUCHER HAY GIỎ HÀNG."
    else:
        special_viral_rule = f"THỂ LOẠI TIKTOK SHOP: 100% dùng từ 'nghìn', cấm từ 'ngàn', cấm 'trợ giá'. Xưng '{self_pronoun}', gọi '{audience_pronoun}'. Cảnh 4 có giá gốc + giá giảm kích thích + miễn trừ thời điểm. Câu văn xuôi tai chuẩn văn nói người Hà Nội, đọc chính xác từng con số tiền, số 4 đọc là 'bốn', tối đa 35 từ/cảnh. Neo giá linh hoạt và chốt deal giỏ hàng an toàn."

    prompt = f"""
    SẢN PHẨM / CHỦ ĐỀ: {json.dumps(condensed_dna, ensure_ascii=False)} | CHIẾN LƯỢC: '{angle}' | DIỄN VIÊN: {num_chars} người Việt.
    HÌNH THỨC VIDEO: '{active_format}'
    ĐẠI TỪ BẮT BUỘC: Xưng '{self_pronoun}' - Gọi '{audience_pronoun}'.
    🛑 CHỈ THỊ ƯU TIÊN CAO NHẤT TỪ NGƯỜI DÙNG CHO 5 KỊCH BẢN THÊM NÀY: '{active_note if active_note else "Tuân thủ chiến lược kịch bản"}'
    BẮT BUỘC TẠO RA 5 KỊCH BẢN Ở 5 BỐI CẢNH ĐỜI THỰC HOÀN TOÀN KHÁC NHAU (tuyệt đối không trùng lặp bối cảnh giữa 5 kịch bản).
    100% CẢ 4 PHÂN CẢNH ĐỀU LÀ NHÂN VẬT MỞ MIỆNG NÓI TRỰC TIẾP ON-CAMERA BẰNG GIỌNG HÀ NỘI CHUẨN ĐÚNG ĐỘ TUỔI TỪ 0.00S, TUYỆT ĐỐI CẤM THUYẾT MINH.
    {special_viral_rule}
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên kịch bản 1", "setting": "Bối cảnh đời thực 1...", "hook": "Câu hook ngắn gọn nhân vật nói trực tiếp bằng tiếng Hà Nội chuẩn xuôi tai...", "actors": {num_chars} }},
            {{ "id": {cur_len+2}, "title": "Tên kịch bản 2", "setting": "Bối cảnh đời thực 2...", "hook": "...", "actors": {num_chars} }},
            {{ "id": {cur_len+3}, "title": "Tên kịch bản 3", "setting": "Bối cảnh đời thực 3...", "hook": "...", "actors": {num_chars} }},
            {{ "id": {cur_len+4}, "title": "Tên kịch bản 4", "setting": "Bối cảnh đời thực 4...", "hook": "...", "actors": {num_chars} }},
            {{ "id": {cur_len+5}, "title": "Tên kịch bản 5", "setting": "Bối cảnh đời thực 5...", "hook": "...", "actors": {num_chars} }}
        ]
    }}
    BẮT BUỘC ĐỦ 5 KỊCH BẢN.
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, "On-camera", char_rules, num_chars, angle, active_note, active_format), max_tokens=2500)
    more_scripts = res.get("outlines", res.get("script_outlines", []))
    for idx, sc in enumerate(more_scripts):
        if "hook" in sc: sc["hook"] = clean_and_normalize_voiceover(sc["hook"])
        sc.update({
            "id": cur_len + idx + 1, "duration_instruction": duration_inst, 
            "narrator_mode": "Nhân vật xuất hiện (On-camera)", 
            "character_profiles": char_profiles, "actors": num_chars,
            "custom_note": active_note,
            "presentation_format": active_format
        })
    return more_scripts

# ==============================================================================
# 3. THANH BÊN (SIDEBAR) & QUẢN LÝ DỰ ÁN NÂNG CẤP
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
                submit_reg = st.form_submit_button("🚀 Đăng Ký", type="secondary", use_container_width=True)
                if submit_reg:
                    email_r, phone_r, pass_r = r_email.strip(), r_phone.strip(), r_pass.strip()
                    if email_r and phone_r and pass_r and is_valid_phone(phone_r) and email_r not in st.session_state.licensed_accounts:
                        exp = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[email_r] = {
                            "roles": ALL_MODULES, "phone": phone_r, "password": pass_r,
                            "expires_at": exp, "plan_type": "Trial", "daily_usage_count": 0,
                            "last_generation_date": "", "active_session_id": ""
                        }
                        save_single_account(email_r, st.session_state.licensed_accounts[email_r])
                        st.session_state.is_logged_in = True
                        st.session_state.current_email = email_r
                        st.toast("✅ Đăng ký thành công!"); time.sleep(0.4); st.rerun()
                    else: st.error("⚠️ Thông tin không hợp lệ hoặc tài khoản đã tồn tại!")
    else:
        st.markdown("### 🗂 DỰ ÁN")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True, disabled=is_system_busy):
            st.session_state.reset_key += 1
            st.session_state.update({
                "all_scripts": [], "cloned_scripts": [], "expanded_scripts": [],
                "generated_details": {}, "content_analysis": None, "active_script_id": None,
                "current_input_context": "", "current_product_data_saved": None, "current_product_data": None,
                "current_project_id": None, "saved_reference_images": [], "character_profiles": [],
                "current_processing_id": None, "current_cloning_id": None
            })
            st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
            st.rerun()
            
        st.session_state.active_project_title = st.text_input("Tên dự án hiện tại:", value=st.session_state.active_project_title)
        
        c_save1, c_save2 = st.columns(2)
        if c_save1.button("💾 Lưu Dự Án", use_container_width=True, disabled=is_system_busy):
            payload = {k: st.session_state[k] for k in ["content_analysis", "all_scripts", "cloned_scripts", "expanded_scripts", "generated_details", "character_profiles", "current_input_context"]}
            success, msg = save_project_to_db(st.session_state.current_email, st.session_state.active_project_title, payload, st.session_state.current_project_id)
            if success: st.toast(f"✅ {msg}")
            else: st.error(f"❌ {msg}")
            
        if c_save2.button("📑 Lưu Bản Mới", use_container_width=True, disabled=is_system_busy, help="Lưu nội dung hiện tại thành một dự án mới hoàn toàn"):
            payload = {k: st.session_state[k] for k in ["content_analysis", "all_scripts", "cloned_scripts", "expanded_scripts", "generated_details", "character_profiles", "current_input_context"]}
            success, msg = save_project_to_db(st.session_state.current_email, f"{st.session_state.active_project_title} (Bản sao)", payload, project_id=None)
            if success: 
                st.session_state.active_project_title = f"{st.session_state.active_project_title} (Bản sao)"
                st.toast("✅ Đã lưu thành dự án mới độc lập!"); time.sleep(0.4); st.rerun()
            else: st.error(f"❌ {msg}")
        
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
                        new_p_name = st.text_input("Đổi tên dự án:", value=p['project_title'], key=f"ren_txt_{p['id']}")
                        if st.button("✏️ Cập Nhật Tên", key=f"ren_btn_{p['id']}", use_container_width=True, disabled=is_system_busy):
                            if new_p_name.strip() and new_p_name.strip() != p['project_title']:
                                supabase.table("saved_projects").update({"project_title": new_p_name.strip()}).eq("id", p['id']).execute()
                                if str(st.session_state.get("current_project_id")) == str(p['id']):
                                    st.session_state.active_project_title = new_p_name.strip()
                                st.toast("✅ Đã đổi tên dự án thành công!"); time.sleep(0.3); st.rerun()
                        
                        col_o, col_d = st.columns(2)
                        if col_o.button("📂 Mở", key=f"o_{p['id']}", use_container_width=True, disabled=is_system_busy):
                            sd = p.get("script_content", {})
                            loaded_details = {}
                            for k, v in sd.get("generated_details", {}).items():
                                try: loaded_details[int(k)] = v
                                except: pass
                                loaded_details[str(k)] = v
                            st.session_state.update({
                                "content_analysis": sd.get("content_analysis"), 
                                "all_scripts": sd.get("all_scripts", []),
                                "cloned_scripts": sd.get("cloned_scripts", []), 
                                "expanded_scripts": sd.get("expanded_scripts", []),
                                "generated_details": loaded_details, 
                                "character_profiles": sd.get("character_profiles", []),
                                "current_input_context": sd.get("current_input_context", ""),
                                "current_project_id": p['id'], 
                                "active_project_title": p['project_title'], 
                                "scroll_to_detail": True
                            })
                            st.rerun()
                        if col_d.button("🗑 Xóa", key=f"d_{p['id']}", type="secondary", use_container_width=True, disabled=is_system_busy):
                            supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                            if str(st.session_state.get("current_project_id")) == str(p['id']):
                                st.session_state.current_project_id = None
                            st.toast("✅ Đã xóa dự án!"); time.sleep(0.3); st.rerun()

                if not search_proj.strip() and len(all_projects) > 3:
                    if st.session_state.show_all_projects:
                        if st.button("🔼 Thu gọn kho dự án", use_container_width=True, disabled=is_system_busy):
                            st.session_state.show_all_projects = False; st.rerun()
                    else:
                        if st.button(f"🔽 Xem thêm {len(all_projects)-3} dự án", use_container_width=True, disabled=is_system_busy):
                            st.session_state.show_all_projects = True; st.rerun()

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
                elif adm_dur == "Vĩnh viễn": calculated_exp_str = "2099-12-31"
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
                    st.write(f"📞 SĐT: `{info.get('phone', 'N/A')}` | ⏳ Hạn: `{info.get('expires_at')}`")
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
                    elif renew_choice == "Vĩnh viễn": target_exp_str = "2099-12-31"
                    elif renew_choice != "Giữ nguyên hạn hiện tại":
                        dur_map_v = {"3 Ngày": 3, "7 Ngày": 7, "1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730}
                        target_exp_str = (datetime.now() + timedelta(days=dur_map_v.get(renew_choice, 30))).strftime("%Y-%m-%d")

                    c_act1, c_act2 = st.columns(2)
                    if c_act1.button("🔄 Cập Nhật", key=f"save_renew_{acc_mail}", use_container_width=True, disabled=is_system_busy):
                        st.session_state.licensed_accounts[acc_mail]["roles"] = new_roles
                        st.session_state.licensed_accounts[acc_mail]["plan_type"] = new_plan
                        st.session_state.licensed_accounts[acc_mail]["expires_at"] = target_exp_str
                        save_single_account(acc_mail, st.session_state.licensed_accounts[acc_mail])
                        st.toast("✅ Đã cập nhật thành công!"); time.sleep(0.4); st.rerun()
                    if c_act2.button("🗑 Xóa", key=f"del_acc_{acc_mail}", type="secondary", use_container_width=True, disabled=is_system_busy):
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
        <!DOCTYPE html><html><head><meta charset="utf-8">
        <style>* { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, sans-serif; } .support-container { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1.5px solid #86efac; border-radius: 14px; padding: 12px 10px; text-align: center; } .support-title { font-size: 14px; font-weight: 800; color: #15803d; margin-bottom: 7px; display: flex; align-items: center; justify-content: center; gap: 6px; } .hotline-card { background: linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%); border-radius: 10px; padding: 8px 6px; text-align: center; } .hotline-label { color: #fecdd3 !important; font-size: 12.5px; font-weight: 700; margin-bottom: 3px; display: flex; align-items: center; justify-content: center; gap: 5px; } .hotline-number { color: #ffffff !important; font-size: 20px; font-weight: 900; letter-spacing: 1.2px; line-height: 1.2; text-shadow: 0 1px 3px rgba(0,0,0,0.35); }</style></head>
        <body><div class="support-container"><div class="support-title"><svg style="width: 17px; height: 17px; fill: #15803d;" viewBox="0 0 24 24"><path d="M12 1a9 9 0 0 0-9 9v7c0 1.66 1.34 3 3 3h3v-8H5v-2a7 7 0 0 1 14 0v2h-4v8h3c.55 0 1-.45 1-1v-4.18A3 3 0 0 0 21 14V10a9 9 0 0 0-9-9z"/></svg><span>HỖ TRỢ TRỰC TIẾP</span></div><div class="hotline-card"><div class="hotline-label"><span>Hotline / Zalo:</span></div><div class="hotline-number">0869 628 316</div></div></div></body></html>
        """
        components.html(support_iframe_code, height=115)
        u_info = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        u_plan = u_info.get("plan_type", "Trial")
        u_used = u_info.get("daily_usage_count", 0) if u_info.get("last_generation_date") == datetime.now().strftime("%Y-%m-%d") else 0
        u_lim = "Không giới hạn" if u_plan == "VIP" else (20 if u_plan == "Advanced" else (10 if u_plan == "Basic" else 3))
        st.info(f"**GÓI {u_plan.upper()}**\n\n• Email: {st.session_state.current_email}\n• Đã tạo: **{u_used}/{u_lim}**\n• Hạn dùng: {u_info.get('expires_at')}")
        if st.button("🚪 Đăng Xuất", disabled=is_system_busy): 
            st.session_state.is_logged_in = False; st.rerun()

if not st.session_state.is_logged_in: st.info("👈 Vui lòng đăng nhập ở thanh bên."); st.stop()

# ==============================================================================
# 5. KHÔNG GIAN SÁNG TẠO CHÍNH - XEM TRƯỚC ẢNH ẨN GỌN (0 TOKEN)
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Đạo Diễn AI - Hệ Thống Kịch Bản Pro</div></div>""", unsafe_allow_html=True)

user_allowed_modules = st.session_state.licensed_accounts.get(st.session_state.current_email, {}).get("roles", ALL_MODULES) or ALL_MODULES
mode = st.selectbox("🎯 Thể loại:", user_allowed_modules, key=f"mode_sel_{st.session_state.reset_key}")
is_viral_mode = "Viral" in mode

up_files, custom_note = [], ""
viral_persona, viral_topic = "", ""
if is_viral_mode:
    col_v1, col_v2 = st.columns(2)
    viral_persona = col_v1.text_input("👤 Định vị Kênh:", placeholder="Ví dụ: Mẹ bỉm sữa thông thái, KOC chuyên gia đồ gia dụng...", key=f"viral_persona_{st.session_state.reset_key}")
    viral_topic = col_v2.text_area("💡 Chủ đề / Mẹo:", height=68, placeholder="Ví dụ: 3 sai lầm khiến chảo chống dính nhanh hỏng, mẹo cọ xoong chảo dầu mỡ...", key=f"viral_topic_{st.session_state.reset_key}")
    up_files = st.file_uploader("📦 Upload Ảnh:", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_viral_{st.session_state.reset_key}")
    
    if up_files:
        with st.expander(f"👁 Xem lại {len(up_files)} ảnh đã tải lên", expanded=False):
            n_cols = min(len(up_files), 4)
            cols = st.columns(n_cols)
            for idx, f in enumerate(up_files):
                cols[idx % n_cols].image(f, caption=f"Ảnh {idx + 1}", use_container_width=True)
                
    custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất - ví dụ: oneshot chỉ cầm trên tay nói chuyện):", key=f"custom_note_viral_{st.session_state.reset_key}")
    hero_sku_override = ""
else:
    products_data = supabase.table("products").select("*").execute().data if supabase else []
    if products_data:
        selected_name = st.selectbox("📌 Chọn sản phẩm:", [p["product_name"] for p in products_data], key=f"prod_select_{st.session_state.reset_key}")
        st.session_state.current_product_data = next(p for p in products_data if p["product_name"] == selected_name)
    
    col_f1, col_f2 = st.columns([2, 1])
    up_files = col_f1.file_uploader("📦 Upload Ảnh SP (Quét OCR Giá, Hero SKU & Bảng màu):", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_prod_{st.session_state.reset_key}")
    hero_sku_override = col_f2.text_input("🎯 Màu / SKU ưu tiên (Tùy chọn):", placeholder="Ví dụ: Đỏ, Be, Size L...", key=f"hero_override_{st.session_state.reset_key}")
    
    if up_files:
        with st.expander(f"👁 Xem lại {len(up_files)} ảnh sản phẩm đã tải lên", expanded=False):
            n_cols = min(len(up_files), 4)
            cols = st.columns(n_cols)
            for idx, f in enumerate(up_files):
                cols[idx % n_cols].image(f, caption=f"Ảnh {idx + 1}", use_container_width=True)
                
    custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất - ví dụ: oneshot chỉ cầm trên tay nói chuyện):", key=f"custom_note_prod_{st.session_state.reset_key}")

col_opt1, col_opt2, col_opt3 = st.columns([1.2, 1.2, 1.2])
style = col_opt1.selectbox("🎨 Phong cách:", ["Điện Ảnh Chân Thực", "Hoạt Hình 3D", "Studio Tối Giản"], key=f"style_sel_{st.session_state.reset_key}")
angle_options = ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Chia sẻ", "😂 Hài hước"]
initial_angle = col_opt1.selectbox("🧭 Chiến lược:", angle_options, key=f"angle_sel_{st.session_state.reset_key}")

presentation_format_opts = [
    "🌟 AI Tự Động Phân Tích & Đề Xuất", 
    "📦 Review & Bóc Hộp Soi Chi Tiết (Freshly Unboxed)", 
    "👶 Trải Nghiệm Thực Tế Đời Sống (Lifestyle POV)", 
    "⚡ Kết Hợp Cả Hai (Bóc Hộp + Trải Nghiệm Thực Tế)"
]
selected_presentation_format = col_opt2.selectbox("🎬 Hình thức video:", presentation_format_opts, key=f"pres_format_{st.session_state.reset_key}")
narrator_mode = col_opt2.selectbox("🎙 Thuyết minh:", ["Nhân vật xuất hiện (On-camera)"], key=f"narrator_sel_{st.session_state.reset_key}")

num_chars = col_opt3.number_input("👤 Số Diễn viên (1 = Độc thoại KOC, ≥2 = Tiểu phẩm đối thoại):", 1, 8, 1, key=f"num_chars_{st.session_state.reset_key}")

char_inputs = []
for i in range(num_chars):
    c_r, c_i = st.columns([2, 1])
    role_default = "Mẹ trẻ 26 tuổi người Việt" if (num_chars >= 2 and i == 0) else ("Bé trai 4 tuổi người Việt" if (num_chars >= 2 and i == 1) else ("Bé gái 1 tuổi người Việt" if (num_chars >= 2 and i == 2) else ""))
    role = c_r.text_input(f"Vai trò NV {i+1}:", value=role_default, key=f"r_{i}_{st.session_state.reset_key}")
    c_file = c_i.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"f_{i}_{st.session_state.reset_key}", label_visibility="collapsed")
    if c_file: char_inputs.append({"id": i+1, "role": role or f"Diễn viên {i+1}", "file": c_file})

if st.button("🚀 PHÂN TÍCH DNA & SINH 5 KỊCH BẢN ĐA VŨ TRỤ", type="primary", use_container_width=True, disabled=is_system_busy):
    can_run, msg = check_usage_limit(st.session_state.current_email)
    if not can_run: st.error(msg)
    else:
        with st.spinner("⏳ Đạo diễn AI đang quét dữ liệu, định danh nhân xưng chuẩn xác và thiết lập bối cảnh..."):
            try:
                st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs] if char_inputs else [{"id": i+1, "role": f"Diễn viên {i+1}"} for i in range(num_chars)]
                char_rules = generate_char_rules_string(st.session_state.character_profiles)
                st.session_state.update({
                    "last_mode": mode, "last_style": style, "last_narrator": "On-camera", 
                    "last_presentation_format": selected_presentation_format,
                    "current_input_context": custom_note.strip()
                })
                
                if is_viral_mode:
                    st.session_state.current_product_data_saved = {
                        "channel_persona": viral_persona.strip(),
                        "topic_or_tips": viral_topic.strip()
                    }
                    input_context_str = f"KÊNH / ĐỊNH VỊ: '{viral_persona.strip()}' | CHỦ ĐỀ / MẸO: '{viral_topic.strip()}' | NOTE: '{custom_note.strip()}'"
                else:
                    st.session_state.current_product_data_saved = st.session_state.get("current_product_data", {})
                    input_context_str = f"SẢN PHẨM: {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)} | NOTE: '{custom_note.strip()}'"
                
                st.session_state["saved_reference_images"] = []
                if up_files:
                    for f in up_files:
                        cb, cm = compress_image_bytes(f, 768, 75)
                        st.session_state["saved_reference_images"].append((cb, cm))

                override_instruction = f"BẮT BUỘC KHÓA HERO SKU LÀ: '{hero_sku_override.strip()}' theo yêu cầu trực tiếp của người dùng." if hero_sku_override.strip() else "QUÉT OCR ƯU TIÊN TUYỆT ĐỐI Ô PHÂN LOẠI CÓ GẮN ICON NGỌN LỬA '🔥', 'Hot', 'Bán chạy', 'Top 1'. Nếu ô có tag này, BẮT BUỘC 100% chọn ô đó là Hero SKU! Không chọn màu khác khi đã có tag Hot/Bán chạy."

                special_prompt_mode = "MỤC TIÊU VIRAL & XÂY KÊNH: Kích thích tương tác thảo luận, tạo bài học hữu ích hoặc sự thật bất ngờ, kéo Follower. TUYỆT ĐỐI KHÔNG BÁN HÀNG." if is_viral_mode else "MỤC TIÊU BÁN HÀNG TIKTOK SHOP: Tập trung vào giải quyết vấn đề, công năng và chốt đơn an toàn."

                prompt = f"""
                INPUT: {input_context_str}
                THỂ LOẠI: '{mode}' ({special_prompt_mode})
                HÌNH THỨC VIDEO YÊU CẦU: '{selected_presentation_format}'
                DIỄN VIÊN: {num_chars} nhân vật 100% người Việt bản địa ({', '.join([p['role'] for p in st.session_state.character_profiles])}).
                
                🛑 QUY CHUẨN MA TRẬN NHÂN XƯNG (PRONOUN MATRIX SPECIFICATION):
                - Hãy phân tích đúng tệp người mua để gán cặp nhân xưng chuẩn:
                  • Đồ bếp, gia dụng, tẩy rửa (miếng rửa bát, chảo, cọ xoong): self_pronoun = 'em', audience_pronoun = 'các chị em' (hoặc 'các bác', 'nhà mình'). CẤM gọi 'các mẹ'!
                  • Mẹ & Bé (bình sữa, tã bỉm, chậu tắm): self_pronoun = 'em' / 'mình', audience_pronoun = 'các mẹ' / 'ba mẹ'.
                  • Thời trang nữ / Mỹ phẩm: self_pronoun = 'em' / 'mình', audience_pronoun = 'các nàng' / 'các chị em'.
                  • Công nghệ, Nam giới, Xe cộ: self_pronoun = 'em', audience_pronoun = 'anh em' / 'các bác'.
                  • Ăn vặt, sức khỏe đại chúng: self_pronoun = 'em', audience_pronoun = 'mọi người' / 'cả nhà' / 'các bác'.

                🛑 QUY CHUẨN BỐI CẢNH ĐỜI THỰC THẤU CẢM (RELATABLE REALISM LOCK):
                - Phân loại setting_archetype: 'Gian bếp nhà phố/chung cư sạch sẽ', 'Phòng tắm gia đình ốp gạch men', 'Góc bàn làm việc gọn gàng', 'Phòng khách ấm cúng'...
                - Cắm cờ is_fixed_location = true/false (true nếu sản phẩm gắn với 1 vị trí cố định như bồn rửa bát, thiết bị cắm điện).
                - Mô tả recommended_setting_en: chuẩn nhà ở trung lưu Việt Nam sạch sẽ, ánh sáng tự nhiên.

                🛑 QUY CHUẨN PHÂN TÍCH SƠ VIN THỜI TRANG ĐỘNG (DYNAMIC TUCK-IN ANALYSIS):
                - Đánh giá hoàn cảnh sử dụng và phom dáng trang phục để ra quyết định sơ vin hay thả ngoài:
                  • Đồ bếp, làm sạch, nội trợ, ở nhà, ăn uống, áo phông rộng, áo len nỉ dày -> decision = 'untucked', en_prompt_lock = 'shirt hem strictly cleanly untucked, resting naturally at hips for casual comfort'.
                  • Công sở, văn phòng, đồ công nghệ, áo phông/sơ mi ôm cạp cao -> decision = 'tucked', en_prompt_lock = 'shirt hem strictly neatly tucked into waistband with a clean flat waistline'.

                🛑 QUY CHUẨN ẨM THỰC ĐA GIÁC QUAN (CULINARY SENSORY ANALYSIS):
                - Nếu là đồ ăn/thực phẩm/nấu nướng:
                  • visual_cues: đặc tả độ bóng sốt mắm tỏi ớt màu hổ phách, khói nóng bốc lên, hạt ớt/tỏi óng ả.
                  • tactile_cues: bẻ đôi chậm rãi thấy ruột rỗng xốp, chấm đẫm sốt sền sệt, đầu ngón tay dính sốt.
                  • auditory_cues: tiếng bẻ 'rắc', tiếng nhai 'rộp rộp' giòn tan ASMR.

                100% CẢ 4 PHÂN CẢNH ĐỀU LÀ DO CHÍNH NHÂN VẬT MỞ MIỆNG NÓI TRỰC TIẾP TRƯỚC ỐNG KÍNH (ON-CAMERA LIP-SYNC) NGAY TỪ 0.00S BẰNG GIỌNG HÀ NỘI CHUẨN ĐÚNG ĐỘ TUỔI, TUYỆT ĐỐI CẤM THUYẾT MINH.
                🛑 CÂU THOẠI PHẢI XUÔI TAI, TỰ NHIÊN, CẤM CÂU BỊ ĐỘNG HOẶC ĐẢO NGỮ LỦNG CỦNG KIỂU DỊCH MÁY.
                🛑 CẤM TUYỆT ĐỐI TỪ 'NGÀN'. 100% BẮT BUỘC DÙNG TỪ 'NGHÌN'.
                🛑 QUY TẮC SỐ BỐN: 100% các số có số 4 BẮT BUỘC đọc và viết là 'bốn' (mười bốn, hai mươi bốn, bốn mươi, bốn trăm...). TUYỆT ĐỐI CẤM 'tư'.
                🛑 CẤM TUYỆT ĐỐI TỪ 'TRỢ GIÁ', 'PHIÊN LIVE', 'TRÊN LIVE'.
                🛑 CẤM TUYỆT ĐỐI KHẨU NGỮ MIỀN NAM. 100% dùng từ ngữ Hà Nội chuẩn.
                🛑 BẮT BUỘC TẠO RA 5 KỊCH BẢN Ở 5 BỐI CẢNH ĐỜI THỰC KHÁC NHAU (tuyệt đối không trùng lặp bối cảnh giữa 5 kịch bản).
                CHỈ ĐẠO HERO SKU: {override_instruction}
                
                BẮT BUỘC TRẢ VỀ JSON:
                {{
                    "content_analysis": {{
                        "self_pronoun": "em",
                        "audience_pronoun": "các chị em (hoặc các bác / các mẹ / anh em phù hợp)",
                        "setting_archetype": "Phân loại không gian chuẩn mực (Gian bếp hiện đại sạch sẽ / Phòng tắm gia đình / Góc làm việc...)",
                        "is_fixed_location": true/false,
                        "tuck_in_analysis": {{
                            "decision": "tucked / untucked",
                            "fashion_reason": "Lý do thời trang thực tế (ví dụ: làm bếp/ăn uống cần thoải mái nên thả áo ngoài tự nhiên)",
                            "en_prompt_lock": "shirt hem strictly cleanly untucked, resting naturally at hips (hoặc strictly neatly tucked into waistband)"
                        }},
                        "culinary_dna": {{
                            "is_culinary": true/false,
                            "texture_profile": "Cấu trúc giòn tan/sền sệt/xốp mềm của món ăn",
                            "sensory_cues": {{
                                "visual_en": "golden crispy crackling glistening with amber sauce, rising steam",
                                "tactile_en": "slowly breaking piece in half with fingers showing airy hollow interior",
                                "auditory_foley": "loud sharp crunch snap and crispy chewing mastication"
                            }}
                        }},
                        "recommended_setting_en": "Realistic clean modern Vietnamese townhouse or apartment setting under 15 words",
                        "recommended_wardrobe_en": "Appropriate contextual outfit under 12 words (e.g. casual tee with beige linen apron)",
                        "target_audience": "Tệp khách hàng mục tiêu",
                        "core_value": "Giá trị cốt lõi",
                        "pain_points": "Nỗi đau thực tế",
                        "hook_element": "Yếu tố giật gân 3 giây đầu",
                        "recommended_format": "Phân tích và đề xuất hình thức phù hợp nhất (Review bóc hộp soi chi tiết / Trải nghiệm thực tế / Hybrid)",
                        "format_reason": "Lý do vì sao sản phẩm này nên làm theo hình thức trên",
                        "product_scale_relative": "Mô tả tỷ lệ kích thước chuẩn xác so với cơ thể người lớn. Tuyệt đối giữ đúng tỷ lệ này qua mọi phân cảnh!",
                        "operational_mechanism": "Phân tích bản chất cơ chế hoạt động thực tế từng bước. Tuyệt đối không bịa sai bản chất!",
                        "correct_ergonomic_grip": "Tư thế cầm nắm công thái học chuẩn đời thực của sản phẩm",
                        "fashion_mix_and_match_rules": {{
                            "is_fashion_item": true/false,
                            "silhouette_and_fabric": "Phân tích phom dáng áo và chất liệu vải",
                            "proportion_formula": "Quy tắc tỷ lệ hình khối chuẩn",
                            "color_harmony": "Phối màu tương phản / tone-sur-tone thanh lịch",
                            "curated_looks": [
                                {{"occasion": "Công sở / Đi làm", "outfit_suggestion": "Phối cùng quần tây âu cạp cao ống suông xếp ly...", "en_prompt": "high-waisted tailored wide-leg trousers in charcoal grey"}},
                                {{"occasion": "Dạo phố / Cuối tuần", "outfit_suggestion": "Phối cùng quần jeans ống đứng cạp cao vintage...", "en_prompt": "vintage light-wash high-rise straight-leg denim jeans"}},
                                {{"occasion": "Hẹn hò / Tiệc nhẹ", "outfit_suggestion": "Phối cùng chân váy lụa satin midi dáng chữ A...", "en_prompt": "flowing high-waisted A-line midi skirt in cream white silk satin"}}
                            ]
                        }},
                        "hero_sku_color": "Mã màu bán chạy nhất (Hero SKU - Ưu tiên tuyệt đối ô có tag '🔥 Hot' / 'Bán chạy')",
                        "color_palette": "Bảng màu toàn bộ",
                        "what_and_unique": "Định danh sản phẩm và điểm độc bản (USP) vượt trội (chỉ viết nội dung)",
                        "target_user": "Đối tượng cụ thể phù hợp nhất (chỉ viết nội dung)",
                        "why_buy": "Lý do thuyết phục không thể chối từ (chỉ viết nội dung)",
                        "where_and_convenience": "Hoàn cảnh ứng dụng thực tế và sự tiện lợi (chỉ viết nội dung)",
                        "how_to_use": "Mô tả thao tác đời thực chuẩn xác theo loại sản phẩm (chỉ viết nội dung)",
                        "product_size_class": "Phân loại kích thước",
                        "product_color_lock": "Khóa màu sắc và họa tiết Hero SKU",
                        "lid_mechanism": "Cơ chế cơ học/kết cấu thực tế",
                        "product_assembly_structure": "Bóc tách cấu trúc đa linh kiện",
                        "flexible_connector_specs": "Nếu có dây nối/ống silicone: Ghi rõ thông số. Nếu không có dây thì ghi 'Không có dây nối'.",
                        "strict_anti_morph_targets": "Các vật thể AI dễ vẽ nhầm để cấm tiệt.",
                        "detected_prices": "Quét OCR giá tiền (giá gốc và giá sale)",
                        "rounded_price_anchor": "TÂM LÝ HỌC NEO GIÁ TƯƠNG PHẢN LINH HOẠT (100% DÙNG TỪ 'NGHÌN', CẤM 'NGÀN', CẤM 'TRỢ GIÁ'): Làm tròn giá gốc TIẾN LÊN mốc chẵn cao hơn, giá sale linh hoạt dùng các từ 'khoảng...', 'gần...', 'chưa tới...', 'tầm...'.",
                        "product_dimensions": "Thông số kích thước",
                        "prompt_dna_lock": "Visual DNA cho video"
                    }},
                    "outlines": [
                        {{ "id": 1, "title": "Tên kịch bản 1", "setting": "Bối cảnh đời thực 1...", "hook": "Câu hook ngắn gọn nhân vật nói trực tiếp xưng hô chuẩn, dùng từ 'bốn'...", "actors": {num_chars} }},
                        {{ "id": 2, "title": "Tên kịch bản 2", "setting": "Bối cảnh đời thực 2...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 3, "title": "Tên kịch bản 3", "setting": "Bối cảnh đời thực 3...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 4, "title": "Tên kịch bản 4", "setting": "Bối cảnh đời thực 4...", "hook": "...", "actors": {num_chars} }},
                        {{ "id": 5, "title": "Tên kịch bản 5", "setting": "Bối cảnh đời thực 5...", "hook": "...", "actors": {num_chars} }}
                    ]
                }}
                """
                payload = ["IMAGES:"]
                for cb, cm in st.session_state["saved_reference_images"]:
                    payload.append(types.Part.from_bytes(data=cb, mime_type=cm))
                for c in char_inputs:
                    cb, cm = compress_image_bytes(c['file'], 768, 75)
                    payload.extend([f"ACTOR {c['id']}:", types.Part.from_bytes(data=cb, mime_type=cm)])
                payload.append(prompt)
                
                res = call_gemini(payload, get_sys_inst_outlines(mode, style, "On-camera", char_rules, num_chars, initial_angle, custom_note.strip(), selected_presentation_format), max_tokens=6000)
                st.session_state.content_analysis = res.get("content_analysis")
                outlines = res.get("outlines", res.get("script_outlines", []))
                
                if not outlines:
                    raise Exception("AI bị ngắt quãng do kết nối mạng trong lúc sinh kịch bản. Vui lòng bấm tạo lại.")
                
                for o in outlines: 
                    if "hook" in o: o["hook"] = clean_and_normalize_voiceover(o["hook"])
                    o.update({
                        "duration_instruction": "Thời lượng động sinh học tối đa 10s", 
                        "narrator_mode": "Nhân vật xuất hiện (On-camera)", 
                        "character_profiles": st.session_state.character_profiles, 
                        "actors": num_chars,
                        "custom_note": custom_note.strip(),
                        "presentation_format": selected_presentation_format
                    })
                st.session_state.update({"all_scripts": outlines, "cloned_scripts": [], "expanded_scripts": [], "generated_details": {}, "active_script_id": None})
                st.toast("✅ Đã thiết lập Ma trận Giác quan, Nhân xưng & Bối cảnh chuẩn cho 5 kịch bản!"); time.sleep(0.3); st.rerun()
            except Exception as e: st.error(f"❌ Lỗi: {e}")

# ==============================================================================
# BỐ CỤC: 2 CỘT ĐỐI XỨNG (1-2, 3-4) & MỤC 5 CHỈ HIỆN KHI LÀ THỜI TRANG / ẨM THỰC
# ==============================================================================
ca = st.session_state.content_analysis
if isinstance(ca, dict):
    st.divider()
    st.markdown("### 🔍 **Phân Tích Chi Tiết**")
    
    col_row1_left, col_row1_right = st.columns(2)
    with col_row1_left:
        st.markdown(f"""
        <div class="dna-card">
            <div class="dna-card-title">🎯 1. Chân dung Khách hàng & Hook 3s (Attention)</div>
            <div class="dna-row"><span class="dna-label">👥 Tệp khách hàng:</span><span class="dna-text">{clean_analysis_text(ca.get('target_audience', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">💔 Nỗi đau thực tế:</span><span class="dna-text">{clean_analysis_text(ca.get('pain_points', ''))}</span></div>
            <div class="dna-row"><span class="dna-label" style="color:#d90429;">⚡ Yếu tố Hook 3s đầu:</span><span class="dna-text" style="color:#d90429; font-weight:600;">{clean_analysis_text(ca.get('hook_element', ''))}</span></div>
            <div class="dna-row"><span class="dna-label" style="color:#2563eb;">🎬 Hình thức tối ưu:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{clean_analysis_text(ca.get('recommended_format', 'Review / Trải nghiệm'))}</span></div>
            <div class="dna-row"><span class="dna-label">💡 Lý do đề xuất:</span><span class="dna-text">{clean_analysis_text(ca.get('format_reason', ''))}</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col_row1_right:
        pronoun_badge = f"🗣 <b>Nhân xưng:</b> KOC xưng <b>'{ca.get('self_pronoun', 'em')}'</b> - Gọi người xem là <b>'{ca.get('audience_pronoun', 'các chị em')}'</b>"
        tuck_info = ca.get('tuck_in_analysis', {})
        tuck_decision_str = tuck_info.get('decision', 'Tự nhiên').upper() if isinstance(tuck_info, dict) else 'TỰ NHIÊN'
        tuck_reason_str = tuck_info.get('fashion_reason', 'Phù hợp hoàn cảnh') if isinstance(tuck_info, dict) else 'Phù hợp hoàn cảnh'
        tuck_badge = f"👗 <b>Cạp áo:</b> {tuck_decision_str} ({tuck_reason_str})"
        if is_viral_mode:
            st.markdown(f"""
            <div class="dna-card">
                <div class="dna-card-title">🌟 2. Định Vị Kênh & Ma Trận Nhân Xưng</div>
                <div class="dna-row"><span class="dna-label">👤 Định vị kênh:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{clean_analysis_text(ca.get('target_user', viral_persona or 'KOC Chuyên gia đời sống'))}</span></div>
                <div class="dna-row"><span class="dna-label">🗣 Nhân xưng chuẩn:</span><span class="dna-text" style="color:#15803d; font-weight:700;">{pronoun_badge}</span></div>
                <div class="dna-row"><span class="dna-label">👗 Khóa cạp áo:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{tuck_badge}</span></div>
                <div class="dna-row"><span class="dna-label">💎 Giá trị cốt lõi:</span><span class="dna-text">{clean_analysis_text(ca.get('core_value', ''))}</span></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="dna-card">
                <div class="dna-card-title">🔥 2. Mã Màu Bán Chạy & Ma Trận Nhân Xưng</div>
                <div class="dna-row"><span class="dna-label">⭐ Mẫu ưu tiên làm video:</span><span class="dna-text" style="color:#dc2626; font-weight:700;">{clean_analysis_text(ca.get('hero_sku_color', 'Tự động'))}</span></div>
                <div class="dna-row"><span class="dna-label">🗣 Nhân xưng chuẩn:</span><span class="dna-text" style="color:#15803d; font-weight:700;">{pronoun_badge}</span></div>
                <div class="dna-row"><span class="dna-label">👗 Khóa cạp áo:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{tuck_badge}</span></div>
                <div class="dna-row"><span class="dna-label">🎨 Toàn bộ bảng màu:</span><span class="dna-text">{clean_analysis_text(ca.get('color_palette', ''))}</span></div>
            </div>
            """, unsafe_allow_html=True)

    col_row2_left, col_row2_right = st.columns(2)
    with col_row2_left:
        st.markdown(f"""
        <div class="dna-card">
            <div class="dna-card-title">💎 3. Giải phẫu Sản phẩm & Nội Dung (Interest & Desire)</div>
            <div class="dna-row"><span class="dna-label">📦 Chủ đề & Điểm đặc biệt:</span><span class="dna-text">{clean_analysis_text(ca.get('what_and_unique', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">👥 Đối tượng phù hợp:</span><span class="dna-text">{clean_analysis_text(ca.get('target_user', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">🔥 Tại sao nên xem/mua:</span><span class="dna-text">{clean_analysis_text(ca.get('why_buy', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">📍 Hoàn cảnh & Tiện ích:</span><span class="dna-text">{clean_analysis_text(ca.get('where_and_convenience', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">🛠 Thao tác & Cách dùng chuẩn thực tế:</span><span class="dna-text">{clean_analysis_text(ca.get('how_to_use', ''))}</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col_row2_right:
        loc_type_str = "Khóa 1 vị trí cố định (Single-Location)" if ca.get('is_fixed_location', True) else "Chuyển cảnh theo mạch truyện (Dynamic)"
        if is_viral_mode:
            st.markdown(f"""
            <div class="dna-card">
                <div class="dna-card-title">💡 4. Chuẩn Bối Cảnh & Mẹo Đời Sống</div>
                <div class="dna-row"><span class="dna-label">🏙 Chuẩn bối cảnh:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{clean_analysis_text(ca.get('setting_archetype', 'Nhà phố/Chung cư sạch sẽ'))}</span></div>
                <div class="dna-row"><span class="dna-label">📍 Cơ chế tọa độ:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{loc_type_str}</span></div>
                <div class="dna-row"><span class="dna-label">🔗 Động lực học chuyển động:</span><span class="dna-text" style="color:#d97706; font-weight:600;">{clean_analysis_text(ca.get('flexible_connector_specs', 'Không có dây nối'))}</span></div>
                <div class="dna-row"><span class="dna-label">🎨 Khóa phối cảnh chi tiết:</span><span class="dna-text">{clean_analysis_text(ca.get('product_color_lock', 'Tự nhiên'))}</span></div>
                <div class="dna-row"><span class="dna-label" style="color:#15803d;">📣 Kêu gọi tương tác (CTA):</span><span class="dna-text" style="color:#15803d; font-weight:700;">Thảo luận, chia sẻ mẹo hay & Follow kênh đón xem tập sau</span></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="dna-card">
                <div class="dna-card-title">⚙ 4. Chuẩn Bối Cảnh, Động Lực Học & Mức Giá</div>
                <div class="dna-row"><span class="dna-label">🏙 Chuẩn bối cảnh:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{clean_analysis_text(ca.get('setting_archetype', 'Nhà phố/Chung cư sạch sẽ'))}</span></div>
                <div class="dna-row"><span class="dna-label">📍 Cơ chế tọa độ:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{loc_type_str}</span></div>
                <div class="dna-row"><span class="dna-label">🧩 Cấu trúc linh kiện:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{clean_analysis_text(ca.get('product_assembly_structure', 'Nguyên khối'))}</span></div>
                <div class="dna-row"><span class="dna-label">💰 Mức giá (OCR):</span><span class="dna-text">{clean_analysis_text(ca.get('detected_prices', ''))}</span></div>
                <div class="dna-row"><span class="dna-label" style="color:#dc2626;">🎯 Đòn bẩy giá tương phản linh hoạt:</span><span class="dna-text" style="color:#dc2626; font-weight:700;">{clean_analysis_text(ca.get('rounded_price_anchor', ''))}</span></div>
            </div>
            """, unsafe_allow_html=True)

    # THẺ HIỂN THỊ ĐẶC BIỆT DÀNH CHO ẨM THỰC / F&B
    c_dna = ca.get('culinary_dna', {})
    if isinstance(c_dna, dict) and c_dna.get('is_culinary', False):
        sensory = c_dna.get('sensory_cues', {})
        st.markdown(f"""
        <div class="dna-card" style="border-left: 4px solid #f97316; margin-top: 6px;">
            <div class="dna-card-title" style="color:#ea580c;">🍗 5. Giải Phẫu Kích Hoạt Đa Giác Quan Ẩm Thực (Food-Porn Sensory Matrix)</div>
            <div class="dna-row"><span class="dna-label">✨ Cấu trúc vật lý:</span><span class="dna-text" style="font-weight:600; color:#c2410c;">{clean_analysis_text(c_dna.get('texture_profile', 'Giòn rụm xốp tan'))}</span></div>
            <div class="dna-row"><span class="dna-label">👁 Kích thích Thị giác:</span><span class="dna-text">{clean_analysis_text(sensory.get('visual_en', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">🖐 Kích thích Xúc giác:</span><span class="dna-text">{clean_analysis_text(sensory.get('tactile_en', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">👂 Kích thích Thính giác (ASMR):</span><span class="dna-text" style="color:#15803d; font-weight:600;">{clean_analysis_text(sensory.get('auditory_foley', ''))}</span></div>
        </div>
        """, unsafe_allow_html=True)

    f_rules = ca.get('fashion_mix_and_match_rules', {})
    if isinstance(f_rules, dict) and f_rules.get('is_fashion_item', False):
        looks_html = ""
        for lk in f_rules.get('curated_looks', []):
            looks_html += f"<div class='dna-bullet'>• <span class='dna-label'>{lk.get('occasion', 'Hoàn cảnh')}:</span> <span class='dna-text'>{lk.get('outfit_suggestion', '')}</span> (<i>Prompt: {lk.get('en_prompt', '')}</i>)</div>"

        st.markdown(f"""
        <div class="dna-card" style="border-left: 4px solid #ec4899; margin-top: 6px;">
            <div class="dna-card-title" style="color:#db2777;">👗 5. Gợi Ý Phối Đồ Chuẩn Fashionista (Mix & Match Styling DNA)</div>
            <div class="dna-row"><span class="dna-label">📐 Phom dáng & Chất liệu:</span><span class="dna-text">{clean_analysis_text(f_rules.get('silhouette_and_fabric', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">⚖ Quy tắc tỷ lệ hình khối:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{clean_analysis_text(f_rules.get('proportion_formula', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">🎨 Nguyên tắc phối màu:</span><span class="dna-text">{clean_analysis_text(f_rules.get('color_harmony', ''))}</span></div>
            <div class="dna-row" style="margin-top:6px;"><span class="dna-label">✨ Gợi ý 3 Look hoàn cảnh thực tế:</span>{looks_html}</div>
        </div>
        """, unsafe_allow_html=True)

    if ca.get('prompt_dna_lock'):
        st.markdown("##### 📌 **Visual DNA Lock:**")
        st.code(ca.get('prompt_dna_lock'), language="text")

all_sc = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
if all_sc:
    st.divider()
    def is_generated(sc_id):
        return (sc_id in st.session_state.generated_details or 
                str(sc_id) in st.session_state.generated_details or 
                int(sc_id) in st.session_state.generated_details)

    comp_sc = [sc for sc in all_sc if is_generated(sc.get("id"))]
    pend_sc = [sc for sc in all_sc if not is_generated(sc.get("id"))]

    if st.session_state.active_script_id is not None:
        st.markdown("<div id='detailed-view-anchor'></div>", unsafe_allow_html=True)
        if st.button("🔼 Thu gọn kịch bản chi tiết", disabled=is_system_busy):
            st.session_state.active_script_id = None
            st.session_state.scroll_to_top = True
            st.rerun()
            
        active_id = st.session_state.active_script_id
        asc = st.session_state.generated_details.get(int(active_id), st.session_state.generated_details.get(str(active_id), {}))
        vp = asc.get("voice", {})
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(asc.get('title', '')).upper()}**")
        
        director_summary_html = asc.get('director_summary', '')
        if not director_summary_html:
            tone_txt = vp.get('tone', 'Hội thoại tự nhiên')
            director_summary_html = f"⏱ <b>Thời lượng:</b> Khoảng 30s | 🎙 <b>Chỉ đạo giọng:</b> {tone_txt}"
        st.markdown(f"<div class='detail-header-box'>{director_summary_html}</div>", unsafe_allow_html=True)
        
        for idx, scn in enumerate(asc.get("scenes", []), 1):
            vo_text = scn.get('voiceover', '')
            actual_words = count_words(vo_text)
            comma_count = vo_text.count(',') + vo_text.count(';')
            period_count = vo_text.count('.') + vo_text.count('!') + vo_text.count('?')
            curr_mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
            is_tts = ("Viral" not in curr_mode)
            speech_sec = scn.get('actual_speech_sec', calculate_speech_duration(vo_text, is_tts))
            
            dur_int = int(str(scn.get('dur', '8s')).replace('s', ''))
            safe_cushion = round(max(0.0, dur_int - speech_sec), 1)
            
            st.markdown(f"#### 📍 Phân cảnh {idx} - Giai đoạn {scn.get('aida_stage')}")
            st.markdown(f"<span class='timing-badge'>⏱ Khung phân cảnh chuẩn: {scn.get('dur')} (Max 10s Veo 3) | Khớp nhịp đọc thực tế: ~{speech_sec}s ({actual_words} từ, {comma_count} phẩy, {period_count} ngắt | ~{round(actual_words/max(1.0, speech_sec), 1)} từ/s) | 🛡 Đệm diễn xuất tự nhiên: +{safe_cushion}s</span>", unsafe_allow_html=True)
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting')}*\n\n**😊 Vi biểu cảm & Cử chỉ:** *{scn.get('expression', 'Tự nhiên, rạng rỡ')}*\n\n**🎵 Hiệu ứng âm thanh (SFX & Foley):** *{scn.get('sfx', 'Âm thanh thực tế sống động')}*\n\n**🎙 Đạo diễn KOC:** *{scn.get('director')}*\n\n**💬 Thoại nhân vật nói trực tiếp on-camera từ 0.00s (100% Giọng Hà Nội chuẩn, dùng 'nghìn', số 4 đọc 'bốn'):** <div class='voiceover-text'>{vo_text}</div>", unsafe_allow_html=True)
            if scn.get('img_p'): st.markdown("**🖼 Prompt Ảnh (Midjourney / Flux - Siêu Tinh Gọn, Khóa Giới Tính, Cạp Áo & Kích Thước Thật):**"); st.code(img_p := scn.get('img_p'), language="text"); safe_copy_button(img_p, f"📋 Sao Chép Ảnh Cảnh {idx}")
            if scn.get('vid_p'): st.markdown("**🎥 Prompt Video (Veo 3 Safe / Kling AI - Tinh Gọn Mật Độ Cao, Mỏ Neo Giọng Hà Nội, Khóa Cứng Diễn Viên & Thoại 0.00s):**"); st.code(vid_p := scn.get('vid_p'), language="text"); safe_copy_button(vid_p, f"📋 Sao Chép Video Cảnh {idx}")
            st.markdown("---")

    st.markdown("### 🎬 **1. Kịch Bản ĐÃ Dựng Chi Tiết**")
    for outline in comp_sc:
        sc_id = outline["id"]
        with st.container(border=True):
            c1, c2, c3 = st.columns([2.5, 1, 1])
            c1.markdown(f"**#{sc_id}. {outline.get('title')}**")
            c1.caption(f"⚡ *{outline.get('hook')}*")
            if str(sc_id) != str(st.session_state.active_script_id):
                if c2.button("👁 Xem lại", key=f"r_{sc_id}", use_container_width=True, disabled=is_system_busy):
                    st.session_state.active_script_id = int(sc_id); st.session_state.scroll_to_detail = True; st.rerun()
            btn_clone_ph = c3.empty()
            if str(st.session_state.current_cloning_id) == str(sc_id):
                btn_clone_ph.markdown("<div style='background: #fffbeb; color: #dc2626; border-radius: 8px; padding: 8px; text-align: center; font-size: 13px; font-weight: bold; border: 1px solid #fca5a5;'>⏳ Đang nhân bản...</div>", unsafe_allow_html=True)
            else:
                if btn_clone_ph.button("🚀 Nhân bản", key=f"c_{sc_id}", type="primary", use_container_width=True, disabled=is_system_busy):
                    can_run, msg = check_usage_limit(st.session_state.current_email)
                    if can_run: st.session_state.current_cloning_id = sc_id; st.rerun()
                    else: st.error(msg)

    st.markdown("<br>### ⏳ **2. Kịch Bản Chờ Dựng**", unsafe_allow_html=True)
    for outline in pend_sc:
        sc_id = outline["id"]
        with st.container(border=True):
            c1, c2 = st.columns([3, 1.2])
            c1.markdown(f"**#{sc_id}. {outline.get('title')}** <span class=badge-pending>CHỜ DỰNG</span>", unsafe_allow_html=True)
            c1.caption(f"⚡ *{outline.get('hook')}*")
            btn_detail_ph = c2.empty()
            if str(st.session_state.current_processing_id) == str(sc_id):
                btn_detail_ph.markdown("<div style='background: #fffbeb; color: #d97706; border-radius: 8px; padding: 8px; text-align: center; font-size: 13px; font-weight: bold; border: 1px solid #fde68a;'>⏳ Đang dựng 4 cảnh...</div>", unsafe_allow_html=True)
            else:
                if btn_detail_ph.button("✨ Tạo chi tiết ngay", key=f"cr_{sc_id}", type="secondary", use_container_width=True, disabled=is_system_busy):
                    can_run, msg = check_usage_limit(st.session_state.current_email, is_detailing=True)
                    if can_run: st.session_state.current_processing_id = sc_id; st.rerun()
                    else: st.error(msg)

    if st.session_state.current_processing_id is not None:
        target_id_to_run = st.session_state.current_processing_id
        success = False
        error_msg = ""
        try:
            with st.spinner(f"⏳ Đang dựng kịch bản #{target_id_to_run} với các thông số tinh gọn..."):
                create_scene_details(target_id_to_run, st.session_state.last_mode, st.session_state.last_style)
                st.session_state.active_script_id = int(target_id_to_run); st.session_state.scroll_to_detail = True; success = True
        except Exception as e: error_msg = str(e)
            
        st.session_state.current_processing_id = None
        if success: st.toast(f"✅ Đã hoàn tất dựng kịch bản #{target_id_to_run}!"); time.sleep(0.3); st.rerun()
        else: st.error(f"❌ Lỗi khi dựng kịch bản: {error_msg}")

    if st.session_state.current_cloning_id is not None:
        clone_id_to_run = st.session_state.current_cloning_id
        success = False
        error_msg = ""
        try:
            with st.spinner(f"⏳ Đang nhân bản 5 biến thể trung thành cho kịch bản #{clone_id_to_run}..."):
                new_clones = clone_script(clone_id_to_run)
                st.session_state.cloned_scripts.extend(new_clones); success = True
        except Exception as e: error_msg = str(e)
            
        st.session_state.current_cloning_id = None
        if success: st.toast("✅ Đã nhân bản thành công 5 kịch bản voice bám sát gốc!"); time.sleep(0.3); st.rerun()
        else: st.error(f"❌ Lỗi khi nhân bản kịch bản: {error_msg}")

    # ==========================================================================
    # KHỞI TẠO KHU VỰC GỌI THÊM 5 KỊCH BẢN MỚI
    # ==========================================================================
    st.markdown("--- \n##### ➕ **Gọi Thêm 5 Kịch Bản Mới**")
    cg1, cg2, cg3, cg4 = st.columns([1.5, 0.8, 1.2, 1.5])
    a_opts = ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Chia sẻ", "😂 Hài hước"]
    c_ang = cg1.selectbox("🧭 Chiến lược mới:", a_opts, key=f"ea_{st.session_state.reset_key}")
    c_num = cg2.number_input("Số diễn viên:", 1, 8, num_chars, key=f"en_{st.session_state.reset_key}")
    c_dur_choice = cg3.selectbox("⏳ Thời lượng:", ["Thời lượng động sinh học", "Tùy chỉnh (s)"], key=f"ed_{st.session_state.reset_key}")
    c_dur_str = f"Chính xác {cg3.number_input('Số giây:', 10, 300, 60, key=f'eds_{st.session_state.reset_key}')} giây." if "Tùy" in c_dur_choice else "Thời lượng động sinh học (tối đa 10s/cảnh)"
    c_nar = cg4.selectbox("🎙 Thuyết minh:", ["Nhân vật xuất hiện (On-camera)"], key=f"ena_{st.session_state.reset_key}")

    c_format_more = st.selectbox(
        "🎬 Hình thức video cho kịch bản thêm:", 
        presentation_format_opts, 
        key=f"more_pres_format_{st.session_state.reset_key}"
    )

    extra_custom_note = st.text_area(
        "✍ Ghi chú AI cho kịch bản thêm (Ưu tiên cao nhất):", 
        placeholder="Ví dụ: Kịch bản mở đầu bằng câu chuyện 8-10 giây giàu cảm xúc, chuyển cảnh mượt mà, văn nói chuẩn người Hà Nội...", 
        key=f"extra_custom_note_{st.session_state.reset_key}"
    )

    e_chars = []
    for i in range(c_num):
        c_r, c_i = st.columns([2, 1])
        e_role = c_r.text_input(f"Vai trò NV {i+1} mới:", key=f"er_{i}_{st.session_state.reset_key}")
        e_file = c_i.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"ef_{i}_{st.session_state.reset_key}", label_visibility="collapsed")
        if e_file: e_chars.append({"id": i+1, "role": e_role or f"Diễn viên {i+1}", "file": e_file})

    if st.button("🚀 Gọi Thêm 5 Kịch Bản Mới", type="primary", use_container_width=True, disabled=is_system_busy):
        can_run, msg = check_usage_limit(st.session_state.current_email)
        if can_run:
            with st.spinner("⏳ Đang sáng tạo thêm 5 kịch bản theo đúng hình thức và ghi chú AI ưu tiên..."):
                p_chars = [{"id": c["id"], "role": c["role"]} for c in e_chars] if e_chars else st.session_state.character_profiles
                new_sc = generate_more_scripts(c_ang, c_num, e_chars, c_nar, c_dur_str, p_chars, extra_custom_note, c_format_more)
                st.session_state.expanded_scripts.extend(new_sc)
                st.toast("✅ Đã sinh thêm 5 kịch bản mới theo đúng yêu cầu!"); time.sleep(0.4); st.rerun()
        else: st.error(msg)
