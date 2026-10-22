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

def clean_html(raw_html: str) -> str:
    if not raw_html: return ""
    return "\n".join(line.strip() for line in raw_html.strip().splitlines() if line.strip())

# ==============================================================================
# THUẬT TOÁN PHIÊN ÂM TIỀN TỆ TIẾNG VIỆT CHUẨN XÁC
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
        return number_to_vietnamese_words(val).replace(" đồng", "")
    text = re.sub(r'\b(\d{1,4})\s*[kK]\b', replace_k, raw_text)

    def replace_num(match):
        num_str = match.group(1).replace('.', '').replace(',', '')
        try:
            val = int(num_str)
            if val >= 1000:
                return number_to_vietnamese_words(val).replace(" đồng", "")
        except: pass
        return match.group(0)
    cleaned = re.sub(r'(\b\d{1,3}(?:[.,]\d{3})+\b)', replace_num, text)
    return cleaned

def convert_to_soft_price_range(price_text: str, is_orig: bool = False, exact_raw_str: str = "") -> str:
    combined = f"{exact_raw_str} {price_text}".lower().strip()
    num_matches = [int(n.replace('.', '').replace(',', '')) for n in re.findall(r'\b\d{1,3}(?:[.,]\d{3})+\b', combined)]
    
    if num_matches:
        val = num_matches[0]
        if is_orig:
            if 100000 <= val <= 125000:
                return "gần một trăm hai mươi nghìn"
            elif val > 1000000:
                ceil_mil = math.ceil(val / 1000000)
                return f"gần {number_to_vietnamese_words(ceil_mil * 1000000).replace(' đồng', '')}"
            elif val > 100000:
                ceil_hundred = math.ceil(val / 100000) * 100000
                if val % 100000 > 70000:
                    return f"gần {number_to_vietnamese_words(ceil_hundred).replace(' đồng', '')}"
                ceil_ten = math.ceil(val / 10000) * 10000
                return f"gần {number_to_vietnamese_words(ceil_ten).replace(' đồng', '')}"
            else:
                ceil_ten = math.ceil(val / 10000) * 10000
                return f"gần {number_to_vietnamese_words(ceil_ten).replace(' đồng', '')}"
        else:
            if val < 50000:
                return "mấy chục nghìn"
            elif val < 100000:
                floor_ten = math.floor(val / 10000) * 10000
                return f"hơn {number_to_vietnamese_words(floor_ten).replace(' đồng', '')}"
            elif val < 1000000:
                floor_hundred = math.floor(val / 100000) * 100000
                return f"hơn {number_to_vietnamese_words(floor_hundred).replace(' đồng', '')}"
            else:
                floor_mil = math.floor(val / 1000000) * 1000000
                return f"hơn {number_to_vietnamese_words(floor_mil).replace(' đồng', '')}"
                
    p_lower = str(price_text).lower().strip()
    p_lower = re.sub(r'^(?:khoảng\s+|hơn\s+|tầm\s+|gần\s+)+', '', p_lower).strip()
    return f"gần {p_lower}" if is_orig else f"hơn {p_lower}"

# ==============================================================================
# HÀM XÁC ĐỊNH NHÂN KHẨU HỌC: ƯU TIÊN USER > TỰ ĐỘNG THEO SẢN PHẨM CỦA AI
# ==============================================================================
def get_demographics_description(char_profiles, ai_persona_en=""):
    user_roles = [str(p.get("role", "")).strip() for p in (char_profiles or []) if str(p.get("role", "")).strip()]
    
    if not user_roles and ai_persona_en and len(ai_persona_en.strip()) > 8:
        ai_p_lower = ai_persona_en.lower()
        gender = "male" if any(k in ai_p_lower for k in ["man", "male", "boy", "father", "gentleman", "anh", "nam"]) else "female"
        return gender, ai_persona_en.strip().capitalize()
    
    if not char_profiles or not user_roles:
        return "female", "A 26-year-old native Vietnamese woman"
    
    parts = []
    primary_gender = "female"
    for idx, p in enumerate(char_profiles):
        role_str = str(p.get("role", "")).strip()
        if not role_str: continue
        role_lower = role_str.lower()
        if any(k in role_lower for k in ["bố", "ba", "chồng", "bác trai"]):
            desc = f"a 28-year-old native Vietnamese father ({role_str})"
            if idx == 0: primary_gender = "male"
        elif any(k in role_lower for k in ["nam", "anh", "trai", "thanh niên"]):
            desc = f"a 26-year-old native Vietnamese young man ({role_str})"
            if idx == 0: primary_gender = "male"
        elif any(k in role_lower for k in ["ông", "già", "bác già", "ông nội", "ông ngoại"]):
            desc = f"a 65-year-old native Vietnamese elderly man ({role_str})"
            if idx == 0: primary_gender = "male"
        elif any(k in role_lower for k in ["bà", "bà nội", "bà ngoại"]):
            desc = f"a 65-year-old native Vietnamese elderly woman ({role_str})"
            if idx == 0: primary_gender = "female"
        elif any(k in role_lower for k in ["bé trai", "con trai"]):
            desc = f"a cute 4-year-old native Vietnamese boy ({role_str})"
            if idx == 0: primary_gender = "male"
        elif any(k in role_lower for k in ["bé gái", "con gái"]):
            desc = f"a cute 3-year-old native Vietnamese girl ({role_str})"
            if idx == 0: primary_gender = "female"
        elif any(k in role_lower for k in ["mẹ", "chị", "cô", "vợ"]):
            desc = f"a 26-year-old native Vietnamese mother ({role_str})"
            if idx == 0: primary_gender = "female"
        else:
            is_m = ("nam" in role_lower or "trai" in role_lower or "anh" in role_lower)
            desc = f"a 26-year-old native Vietnamese {'man' if is_m else 'woman'} ({role_str})"
            if idx == 0: primary_gender = "male" if is_m else "female"
        parts.append(desc)
    
    if not parts:
        return "female", "A 26-year-old native Vietnamese woman"
    if len(parts) == 1:
        return primary_gender, parts[0].capitalize()
    return primary_gender, (", ".join(parts[:-1]).capitalize() + " and " + parts[-1])

# ==============================================================================
# HỆ THỐNG BẢO VỆ TỰ ĐỘNG & BỘ MÁY STYLIST ĐA NGÀNH
# ==============================================================================
def detect_intimate_apparel(text_to_check: str) -> str:
    if not text_to_check: return "normal"
    t = text_to_check.lower()
    if any(k in t for k in [
        "áo lót", "quần lót", "đồ lót", "nội y", "áo ngực", "su đúc", "quần chip", 
        "quần sịp", "bikini", "đồ bơi", "váy ngủ", "đồ ngủ", "miếng dán ngực", 
        "dung dịch vệ sinh", "bra", "panties", "underwear", "lingerie", "briefs", "thong"
    ]):
        return "underwear_bra"
    if any(k in t for k in ["áo 2 dây", "áo hai dây", "áo ống", "áo quây", "camisole", "spaghetti strap"]):
        return "camisole"
    return "normal"

def detect_wearable_fashion(text_to_check: str) -> bool:
    if not text_to_check: return False
    t = text_to_check.lower()
    fashion_keywords = [
        "áo", "quần", "váy", "đầm", "giày", "dép", "mũ", "nón", "túi", "balo", 
        "thắt lưng", "ví", "khăn", "kính", "hoodie", "sweater", "blazer", "jacket",
        "sneakers", "boots", "shirt", "pants", "jeans", "shorts", "hat", "cap", "t-shirt"
    ]
    return any(k in t for k in fashion_keywords)

def build_multi_industry_stylist_rules(product_en: str, hero_color: str, setting_vi: str, gender: str, intimate_type: str, is_fashion: bool) -> str:
    s_lower = f"{product_en} {setting_vi}".lower()
    h_lower = hero_color.lower()
    
    is_home_interior = any(k in s_lower for k in ["phòng ngủ", "giường", "nhà bếp", "bếp", "phòng tắm", "sofa", "phòng khách", "mặc nhà"])
    if is_home_interior:
        footwear_rule = "clean minimalist indoor house slippers (hoặc clean white ankle socks)"
    else:
        footwear_rule = "clean minimalist white leather sneakers or smart-casual loafers" if gender == "male" else "clean minimalist white sneakers, elegant beige loafers, or modest low-block slingback flats"
        
    if any(k in h_lower for k in ["đen", "black", "xám", "grey", "gray", "xanh đậm", "navy", "nâu", "dark"]):
        color_contrast_rule = "Màu áo/trang phục làm nền BẮT BUỘC là tông SÁNG/TRUNG TÍNH (Kem Ivory, Trắng Sữa, Be Sáng, Xanh Pastel nhạt) để tôn sản phẩm tối màu lên nổi bật."
    elif any(k in h_lower for k in ["trắng", "white", "kem", "cream", "be", "beige", "vàng nhạt", "hồng nhạt"]):
        color_contrast_rule = "Màu áo/trang phục làm nền BẮT BUỘC là tông TRẦM/ĐẬM THANH LỊCH (Xanh Navy, Nâu Mocha, Xám Than, Xanh Rêu trầm) để tôn sản phẩm sáng màu lên nổi bật."
    else:
        color_contrast_rule = "Màu áo/trang phục làm nền là tông TRUNG TÍNH ĐƠN SẮC (Trắng Kem, Be, Xám Nhạt hoặc Xanh Navy) sang trọng, không rối mắt."

    if intimate_type == "underwear_bra":
        industry_outfit = "Áo sơ mi lụa/linen dài tay cài cúc lịch sự hoặc áo thun cổ tròn phối khoác ngoài bằng cardigan dệt kim mỏng + Quần âu ống suông dài cạp cao thanh lịch."
    elif is_fashion:
        industry_outfit = "Nhân vật mặc trực tiếp sản phẩm thời trang này lên người. Phối cùng phụ kiện và trang phục phụ trợ tinh tế, gọn gàng, tôn phom dáng (silhouette) thực tế."
    else:
        industry_outfit = (
            "Phối đồ chuyên gia chuẩn KOC: "
            "(1) Nam: Áo Polo dệt kim có cổ / Sơ mi Oxford xắn tay áo gọn gàng + Quần Chinos/Quần âu ống đứng; "
            "(2) Nữ: Áo sơ mi kiểu Hàn Quốc / Áo thun ôm vừa vặn sơ vin gọn gàng cùng Quần âu ống suông cạp cao hoặc chân váy dài thanh lịch."
        )

    return f"""
    🛑 BỘ MÁY STYLIST ĐA NGÀNH & BỐI CẢNH THÔNG MINH ('wardrobe_lock'):
    - PHỐI TRANG PHỤC CHUẨN NGÀNH HÀNG: {industry_outfit}
    - TƯƠNG PHẢN MÀU SẮC TÔN SẢN PHẨM: {color_contrast_rule}
    - GIÀY DÉP CHUẨN KHÔNG GIAN: Sử dụng '{footwear_rule}'.
    - KHÓA CHI TIẾT ĐỒNG NHẤT: Trong 'master_outfit_en', mô tả chi tiết chất liệu vải, kiểu cổ áo, tay áo và giày dép để giữ bất biến 100% suốt 4 cảnh.
    """

INTIMATE_SAFE_ENGLISH_LEXICON = {
    r'\b(?:push-?up\s+|lace\s+|wireless\s+|seamless\s+)?bras?\b': 'ergonomic seamless comfort top garment',
    r'\bbrassieres?\b': 'seamless molded fabric support garment',
    r'\b(?:lace\s+|cotton\s+|seamless\s+)?panties\b': 'seamless breathable modal base-layer garment',
    r'\bunderwears?\b': 'soft breathable cotton comfort apparel piece',
    r'\bbriefs?\b': 'seamless comfort base-layer garment',
    r'\bthongs?\b': 'seamless invisible-edge fabric garment',
    r'\blingerie\b': 'delicate pastel loungewear apparel',
    r'\bbikinis?\b': 'summer resort activewear piece',
    r'\bcamisoles?\b': 'sleek layered inner tank top styled under an open casual overshirt',
    r'\bspaghetti\s+straps?\b': 'delicate shoulder straps layered under a light cardigan',
    r'\bcleavage\b': 'neat modest neckline',
    r'\bunderwires?\b': 'wireless ergonomic support structure',
    r'\bcrotch\b': 'inner breathable cotton lining',
    r'\bbuttocks?\b': 'hip contour',
    r'\bbreasts?\b': 'upper silhouette',
    r'\bboobs?\b': 'upper silhouette',
    r'\bnipples?\b': 'fabric center',
    r'\bsexy\b': 'elegant modern',
    r'\bseductive\b': 'graceful',
    r'\bsensual\b': 'refined',
    r'\báo\s*lót\b': 'ergonomic seamless comfort top garment',
    r'\báo\s*ngực\b': 'ergonomic seamless comfort top garment',
    r'\bquần\s*lót\b': 'seamless breathable modal base-layer garment',
    r'\bquần\s*chip\b': 'seamless breathable modal base-layer garment',
    r'\bđồ\s*lót\b': 'soft breathable comfort apparel piece',
    r'\bnội\s*y\b': 'delicate comfort loungewear piece',
    r'\báo\s*(?:2|hai)\s*dây\b': 'sleek inner tank top layered under an open casual shirt'
}

def sanitize_third_party_ip(text: str) -> str:
    if not text: return ""
    cleaned = text
    platforms = [r'\btiktok\s*(?:shop)?\b', r'\bshopee\b', r'\blazada\b', r'\bfacebook\b', r'\binstagram\b', r'\byoutube\b']
    for p in platforms:
        cleaned = re.sub(p, 'commercial marketplace', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:emoon|disney|marvel|spider-?man|spiderman|nike|apple|samsung|lego|barbie)\b', 'custom premium brand', cleaned, flags=re.IGNORECASE)
    for pattern, safe_term in INTIMATE_SAFE_ENGLISH_LEXICON.items():
        cleaned = re.sub(pattern, safe_term, cleaned, flags=re.IGNORECASE)
    return cleaned

POLICY_REPLACEMENTS = {
    r'\ban\s*toàn\s*tuyệt\s*đối\b': 'cực kỳ an toàn',
    r'\byên\s*tâm\s*tuyệt\s*đối\b': 'cực kỳ yên tâm',
    r'\btuyệt\s*đối\s*an\s*toàn\b': 'cực kỳ an toàn',
    r'\btuyệt\s*đối\s*yên\s*tâm\b': 'cực kỳ yên tâm',
    r'\bhoàn\s*toàn\s*yên\s*tâm\b': 'cực kỳ yên tâm',
    r'\bhoàn\s*toàn\s*an\s*toàn\b': 'rất an toàn',
    r'\b100\s*%\s*an\s*toàn\b': 'rất an toàn',
    r'\ban\s*toàn\s*100\s*%\b': 'cực kỳ an toàn',
    r'(\b[a-zà-ỹ]+)\s+tuyệt\s*đối\b': r'cực kỳ \1',
    r'\btuyệt\s*đối\b': 'rất',
    r'\bhoàn\s*toàn\b': 'thực sự',
    r'\b100\s*%\b': 'rất nhiều',
    r'\bchắc\s*chắn\b': 'rất có thể',
    r'\bcam\s*kết\b': 'an tâm',
    r'\bdứt\s*điểm\b': 'cải thiện',
    r'\bđặc\s*trị\b': 'hỗ trợ',
    r'\bkhỏi\s*hẳn\b': 'đỡ hẳn',
    r'\bvĩnh\s*viễn\b': 'lâu dài',
    r'\bchuẩn\s*đét\b': 'vừa vặn',
    r'\bchữa\s*khỏi\b': 'hỗ trợ',
    r'\bthần\s*dược\b': 'bí quyết',
    r'\btốt\s*nhất\b': 'rất tốt',
    r'\bsố\s*1\b': 'hàng đầu',
    r'\btrắng\s*cấp\s*tốc\b': 'sáng khỏe tự nhiên',
    r'\bgiảm\s*béo\s*cấp\s*tốc\b': 'vóc dáng thon gọn',
    r'\bxóa\s*sạch\s*nám\b': 'mờ thâm sạm',
    r'\bthuốc\s*trị\b': 'sản phẩm hỗ trợ',
    r'\bđiều\s*trị\b': 'hỗ trợ cải thiện',
    r'\btriệt\s*để\b': 'hiệu quả',
    r'\btrợ\s*giá\b': 'giảm giá sâu có hạn',
    r'\bphiên\s*live\b': 'đợt ưu đãi này',
    r'\btrên\s*live\b': 'đợt này',
    r'\blivestream\b': 'chương trình ưu đãi',
    r'\bkhe\s*ngực\b': 'phom dáng',
    r'\bnâng\s*ngực\b': 'nâng đỡ phom dáng',
    r'\bchống\s*xệ\s*ngực\b': 'giữ phom săn chắc',
    r'\bxệ\s*ngực\b': 'mất phom',
    r'\bvùng\s*kín\b': 'vùng nhạy cảm',
    r'\bnhũ\s*hoa\b': 'điểm nhạy cảm',
    r'\blộ\s*nhũ\s*hoa\b': 'lộ viền kém duyên',
    r'\bgợi\s*cảm\b': 'tinh tế cuốn hút',
    r'\bsexy\b': 'thanh lịch tôn dáng',
    r'\bquyến\s*rũ\b': 'nữ tính',
    r'\bhở\s*bạo\b': 'thoải mái'
}

SOUTHERN_TO_HANOI = {
    r'\báp\s*mã\b': 'nay giảm',
    r'\báp\s*voucher\b': 'nay giảm',
    r'\b1\s*trăm\s*(?:tư|tứ|bốn)?\s*mươi\b': 'một trăm bốn mươi',
    r'\b1\s*trăm\s*(?:tư|tứ)\b': 'một trăm bốn mươi',
    r'\bmột\s*trăm\s*(?:tư|tứ)\s*mươi\b': 'một trăm bốn mươi',
    r'\bmột\s*trăm\s*(?:tư|tứ)\b': 'một trăm bốn mươi',
    r'\btrăm\s*(?:tư|tứ)\s*mươi\b': 'trăm bốn mươi',
    r'\btrăm\s*(?:tư|tứ)\b': 'trăm bốn mươi',
    r'\b(?:tư|tứ)\s+mươi\b': 'bốn mươi',
    r'\bmười\s+(?:tư|tứ)\b': 'mười bốn',
    r'\bnghìn\s+(?:tư|tứ)\b': 'nghìn bốn trăm',
    r'\b1\s+trăm\b': 'một trăm',
    r'\b1\s+nghìn\b': 'một nghìn',
    r'\b1\s+triệu\b': 'một triệu',
    r'\b(\w+)\s+mươi\s+(?:tư|tứ)\b': r'\1 mươi bốn',
    r'\bbốn\s+(?:tư|tứ)\b': 'bốn mươi bốn',
    r'\bnăm\s+(?:tư|tứ)\b': 'năm mươi bốn',
    r'\bsáu\s+(?:tư|tứ)\b': 'sáu mươi bốn',
    r'\bbảy\s+(?:tư|tứ)\b': 'bảy mươi bốn',
    r'\btám\s+(?:tư|tứ)\b': 'tám mươi bốn',
    r'\bchín\s+(?:tư|tứ)\b': 'chín mươi bốn',
    r'\bhai\s+(?:tư|tứ)\b': 'hai mươi bốn',
    r'\bba\s+(?:tư|tứ)\b': 'ba mươi bốn',
    r'\bhăm\s+(?:tư|tứ)\b': 'hai mươi bốn',
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
    r'\bkhít\s+tai\s+êm\s+ái\b': 'vừa khít mà êm ru',
    r'\bêm\s+ái\b': 'êm ru',
    r'\bvỏ\s*ngoài\b': 'bên ngoài',
    r'\bnét\s+căng\b': 'rõ mồn một',
    r'\bpin\s*trâu\b': 'pin dùng trâu bò',
    r'\bsạc\s*lẹ\b': 'sạc nhanh',
    r'\bthấm\s*lẹ\b': 'thấm nhanh',
    r'\bbết\s*rít\b': 'nhờn dính',
    r'\bxài\s*êm\b': 'dùng êm',
    r'\bmịn\s*mướt\b': 'căng mướt',
    r'\blột\s*mụn\b': 'hút mụn',
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
    r'\bmấy\s+bồ\b': 'các bạn',
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
        (r'\báp\s*mã\b', 'nay giảm'),
        (r'\báp\s*voucher\b', 'nay giảm'),
        (r'\b1\s*trăm\s*(?:tư|tứ|bốn)?\s*mươi\b', 'một trăm bốn mươi'),
        (r'\b1\s*trăm\s*(?:tư|tứ)\b', 'một trăm bốn mươi'),
        (r'\bmột\s*trăm\s*(?:tư|tứ)\s*mươi\b', 'một trăm bốn mươi'),
        (r'\bmột\s*trăm\s*(?:tư|tứ)\b', 'một trăm bốn mươi'),
        (r'\btrăm\s*(?:tư|tứ)\s*mươi\b', 'trăm bốn mươi'),
        (r'\btrăm\s*(?:tư|tứ)\b', 'trăm bốn mươi'),
        (r'\b1\s*trăm\b', 'một trăm'),
        (r'\b1\s*nghìn\b', 'một nghìn'),
        (r'\b1\s*triệu\b', 'một triệu'),
        (r'\b140\s*(?:k|nghìn|ngàn)\b', 'một trăm bốn mươi nghìn'),
        (r'\b140\b', 'một trăm bốn mươi'),
        (r'\b14\b', 'mười bốn'), (r'\b24\b', 'hai mươi bốn'), (r'\b34\b', 'ba mươi bốn'),
        (r'\b40\b', 'bốn mươi'), (r'\b44\b', 'bốn mươi bốn'), (r'\b4\b', 'bốn'),
        (r'\bmười\s+(?:tư|tứ)\b', 'mười bốn'),
        (r'\bhai\s+(?:tư|tứ)\b', 'hai mươi bốn'),
        (r'\bba\s+(?:tư|tứ)\b', 'ba mươi bốn'),
        (r'\b(?:tư|tứ)\s+mươi\b', 'bốn mươi'),
        (r'\b(\w+)\s+mươi\s+(?:tư|tứ)\b', r'\1 mươi bốn')
    ]:
        cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\ban\s*toàn\s*rất\s*luôn\b', 'cực kỳ an toàn luôn', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\ban\s*toàn\s*rất\b', 'rất an toàn', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b([a-zà-ỹ]+)\s+rất\s+luôn\b', r'cực kỳ \1 luôn', cleaned, flags=re.IGNORECASE)
    return cleaned

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

def format_ocr_prices(ca_data: dict) -> str:
    if not isinstance(ca_data, dict): return "<span style='color:#dc2626; font-weight:700;'>Chưa xác định</span>"
    exact_orig = ca_data.get('exact_original_price_ocr', '')
    exact_sale = ca_data.get('exact_sale_price_ocr', '')
    det = ca_data.get('detected_prices', '')
    
    if exact_orig and exact_sale:
        return f"<b style='color:#475569;'>Giá gốc:</b> <span style='color:#64748b; text-decoration:line-through; font-weight:700; font-size:14px;'>{clean_analysis_text(exact_orig)}</span> &nbsp;|&nbsp; <b style='color:#dc2626;'>Giá giảm:</b> <span style='color:#dc2626; font-weight:800; font-size:15.5px;'>{clean_analysis_text(exact_sale)}</span>"
    elif det and ("-" in det or "|" in det or "đ" in det.lower()):
        return f"<span style='color:#dc2626; font-weight:800; font-size:14.5px;'>{clean_analysis_text(det)}</span>"
    
    orig = ca_data.get('original_price_spoken', '')
    sale = ca_data.get('sale_price_spoken', '')
    if orig and sale:
        return f"<b style='color:#475569;'>Giá gốc:</b> <span style='color:#64748b; text-decoration:line-through; font-weight:700;'>{clean_analysis_text(orig)}</span> &nbsp;|&nbsp; <b style='color:#dc2626;'>Giá giảm:</b> <span style='color:#dc2626; font-weight:800; font-size:15px;'>{clean_analysis_text(sale)}</span>"
    return "<span style='color:#dc2626; font-weight:700;'>Chưa xác định</span>"

# ==============================================================================
# CẢM BIẾN THỜI TIẾT, ÁNH SÁNG MÔI TRƯỜNG & FOLEY TỰ ĐỘNG
# ==============================================================================
def extract_environmental_lighting_and_weather(vo_text: str, setting_text: str = ""):
    combined_text = f"{vo_text} {setting_text}".lower()
    
    outdoor_keywords = ["ngoài trời", "sân vườn", "đường phố", "công viên", "vỉa hè", "ban công", "sân thượng", "dã ngoại", "bãi biển", "cắm trại", "outdoor", "street", "garden", "park", "balcony"]
    is_indoor = not any(k in combined_text for k in outdoor_keywords)
    
    weather_desc = []
    weather_sfx = []
    
    if any(k in combined_text for k in ["mưa", "mưa rào", "mưa to", "mưa phùn", "giông bão", "ẩm ướt", "nồm"]):
        weather_desc.append(
            "visible rain droplets streaking down window glass in background, cozy overcast diffused indoor lighting" 
            if is_indoor else 
            "atmospheric light rain falling, wet reflective ground surfaces, soft overcast sky"
        )
        weather_sfx.append("soft ambient rain pattering against window" if is_indoor else "gentle natural rain falling Foley")
    elif any(k in combined_text for k in ["nắng gắt", "nắng nóng", "trưa hè", "chói chang", "oi bức", "nắng đẹp"]):
        weather_desc.append(
            "bright warm sunbeams streaming through window blinds with soft natural shadow play" 
            if is_indoor else 
            "vibrant sunny daylight, warm golden sunbeams, crisp natural shadows"
        )
        weather_sfx.append("subtle warm summer breeze ambiance")
    elif any(k in combined_text for k in ["sáng sớm", "buổi sáng", "bình minh", "ngủ dậy"]):
        weather_desc.append(
            "fresh soft morning sunlight filtering through sheer curtains, airy daytime atmosphere" 
            if is_indoor else 
            "fresh golden hour morning sunlight, clear sky, gentle morning mist"
        )
        weather_sfx.append("peaceful morning room tone" if is_indoor else "faint distant morning birds and gentle breeze Foley")
    elif any(k in combined_text for k in ["hoàng hôn", "chiều tà", "cuối ngày", "tan làm", "buổi chiều"]):
        weather_desc.append(
            "warm amber sunset glow casting long soft shadows across the room" 
            if is_indoor else 
            "cinematic golden hour sunset lighting, warm orange and amber sky tones"
        )
        weather_sfx.append("calm evening ambient room tone")
    elif any(k in combined_text for k in ["ban đêm", "tối muộn", "đêm muộn", "khuya", "buổi tối", "đi ngủ"]):
        weather_desc.append(
            "cozy nighttime interior ambiance, warm tungsten desk and ambient lamp lighting, soft shadows" 
            if is_indoor else 
            "cinematic nighttime urban lighting, warm streetlamp glow with soft bokeh background"
        )
        weather_sfx.append("quiet peaceful nighttime room tone")
    elif any(k in combined_text for k in ["mùa đông", "trời lạnh", "gió mùa", "rét"]):
        weather_desc.append(
            "cozy warm indoor lighting contrasting with cool pale winter daylight outside window" 
            if is_indoor else 
            "crisp cool winter daylight, soft pale sky tones"
        )
        weather_sfx.append("soft cozy indoor ambiance" if is_indoor else "gentle crisp winter wind Foley")
    else:
        weather_desc.append(
            "clean balanced natural daylight mixed with soft warm interior fill light" 
            if is_indoor else 
            "bright natural commercial daylight, even skin-flattering illumination"
        )
        
    return ", ".join(weather_desc), ", ".join(weather_sfx)

def sanitize_veo3_prompt(prompt_text: str) -> str:
    if not prompt_text: return ""
    p = re.sub(r'\bgesturing\s+(?:warmly\s+)?(?:toward\s+)?corner\b', 'sharing recommendations with an open-palm hand gesture', prompt_text, flags=re.IGNORECASE)
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

def safe_copy_button(text_to_copy: str, button_label: str = "📋 Sao Chép Prompt", custom_color: str = "#16a34a"):
    b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    html_id = f"btn_{int(time.time()*10000)}_{len(text_to_copy)}"
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

if "session_id" not in st.session_state: st.session_state.session_id = str(uuid.uuid4())
for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", load_licensed_accounts()),
    ("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []),
    ("generated_details", {}), ("content_analysis", None), ("active_script_id", None),
    ("current_input_context", ""), ("current_product_data_saved", None), ("current_product_data", None),
    ("reset_key", 0), ("scroll_to_top", False), ("scroll_to_detail", False),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"),
    ("last_mode", "🛒 TikTok Shop & Bán Hàng"), ("last_style", "Điện Ảnh Chân Thực"), ("last_narrator", "On-camera"),
    ("last_presentation_format", "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng"),
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
            raise Exception("Google API bận tạm thời (503). Vui lòng đợi 5s rồi bấm lại.")
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
    
    is_auto_mix = any(k in str(angle) for k in ["Tự động", "Tự Động", "Mix"])
    strat_cmd = "BẠN PHẢI TỰ ĐỘNG PHÂN TÍCH ĐỂ ĐỀ XUẤT HÌNH THỨC VIDEO TỐI ƯU VÀ MIX ĐA DẠNG 5 GÓC ĐỘ NỘI DUNG KHÁC NHAU." if is_auto_mix else f"VIẾT CẢ 5 KỊCH BẢN BÁM SÁT CHIẾN LƯỢC & HÌNH THỨC: '{angle}'."
    override_rule = f"🛑 CHỈ THỊ ƯU TIÊN CAO NHẤT TỪ NGƯỜI DÙNG: '{custom_note}'. Bạn BẮT BUỘC phải thực hiện đúng chỉ thị này trong toàn bộ 5 kịch bản!" if custom_note else ""
    pres_rule = f"🛑 CHIẾN LƯỢC & HÌNH THỨC VIDEO CHỈ ĐỊNH: '{presentation_format}'. Hãy định hướng kịch bản bám sát định hướng này." if presentation_format else ""

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
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL TIKTOK & REELS TRIỆU VIEW. PHONG CÁCH: Điện Ảnh Chân Thực
    {strat_cmd} | {format_direction}
    {override_rule}
    {pres_rule}
    {viral_directive}
    
    🛑 YÊU CẦU ĐA DẠNG HÓA 5 BỐI CẢNH HOÀN TOÀN KHÁC NHAU:
    - BẮT BUỘC mỗi kịch bản trong 5 kịch bản phải diễn ra ở 1 BỐI CẢNH ĐỜI THỰC KHÁC NHAU.
    - BỐI CẢNH PHẢI ĐÚNG VỚI SẢN PHẨM: Đồ công nghệ / PC / Gaming thì bối cảnh là góc setup máy tính gaming, bàn làm việc công nghệ, phòng riêng streamer... TUYỆT ĐỐI KHÔNG đưa bối cảnh nhà bếp hay nấu nướng vào đồ công nghệ!

    🛑 QUY TẮC BẢO VỆ NỘI DUNG NHẠY CẢM & THỜI TRANG:
    - Nếu sản phẩm là áo lót, quần lót, nội y, bikini: TUYỆT ĐỐI KHÔNG cho nhân vật mặc trực tiếp lên người! Nhân vật mặc đồ đời thường kín đáo và CẦM SẢN PHẨM TRÊN TAY (hoặc treo trên móc) để kiểm tra độ co giãn, chất vải. Dùng từ ngữ thanh lịch ('vòng một', 'gom phom', 'nâng đỡ tự nhiên'), CẤM dùng từ nhạy cảm ('khe ngực', 'vú', 'vùng kín', 'sexy').
    - Nếu sản phẩm là thời trang mặc trên người (quần áo, váy, giày dép): Nhân vật MẶC TRỰC TIẾP SẢN PHẨM LÊN NGƯỜI, tạo dáng tự nhiên, xoay người khoe phom dáng và chỉ tay vào điểm nhấn (chất liệu, cúc áo, đường may) đang mặc trên người.

    🛑 BỘ MÁY NGỮ PHÁP VĂN NÓI XUÔI CHIỀU & PHÁT ÂM CHUẨN HÀ NỘI:
    - CÂU CÚ PHẢI TUYỆT ĐỐI XUÔI THEO VĂN NÓI ĐỜI THƯỜNG CỦA NGƯỜI HÀ NỘI.
    - TUYỆT ĐỐI CẤM các từ ngữ công nghệ/máy móc sáo rỗng: CẤM 'thuật toán gợi ý', CẤM 'máy vừa phân tích', CẤM 'hệ thống vừa báo', CẤM 'AI phát hiện'.
    - 🛑 QUY TẮC PHÁT ÂM: 100% viết và đọc là 'bốn' (bốn mươi, mười bốn...). CẤM 'tư', CẤM 'tứ'. Viết rõ 'một trăm'.
    - CẤM TUYỆT ĐỐI TỪ 'NGÀN' (DÙNG 'NGHÌN'). CẤM 'TRỢ GIÁ', 'PHIÊN LIVE'.
    - 100% CẢ 4 CẢNH LỜI THOẠI ĐỀU BẮT ĐẦU NGAY TỪ 0.00s.
    🛑 100% NGƯỜI VIỆT HƯ CẤU: {char_rules}
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction, num_chars, character_profiles, custom_note="", presentation_format="", self_pronoun="em", audience_pronoun="các chị em", setting_archetype="", is_fixed_location=True):
    is_multi = (num_chars >= 2)
    is_viral = ("Viral" in mode)
    voice_guidance = build_voice_direction(mode, num_chars, character_profiles)
    dialogue_type_rule = f"🛑 ĐỐI THOẠI {num_chars} NHÂN VẬT: Tách từng câu thoại nói trực tiếp." if is_multi else "🛑 ĐỘC THOẠI KOC: Lời thoại do chính KOC mở miệng nói trực tiếp trước ống kính từ 0.00s."
    
    if is_viral:
        outro_instruction = f"""
        🛑 QUY TẮC CẢNH 4 CHO 'VIRAL & XÂY KÊNH':
        - KOC xưng '{self_pronoun}', gọi người xem là '{audience_pronoun}'.
        - Đặt câu hỏi thảo luận hoặc kết lại bài học tâm đắc + Kêu gọi follow đón xem tập sau.
        - TUYỆT ĐỐI CẤM: Không nhắc giá tiền, không mã giảm giá, không giỏ hàng!
        """
    else:
        outro_instruction = f"""
        🛑 CÔNG THỨC CHỐT DEAL CẢNH 4 TIKTOK SHOP AN TOÀN (KHÓA KÉP 'KHOẢNG' & 'NAY GIẢM'):
        - Neo khoảng giá: 'Bình thường khoảng [giá gốc làm tròn LÊN], nay giảm chỉ còn khoảng [giá sale làm tròn XUỐNG] thôi...'
        - Miễn trừ: 'nhưng giá từng thời điểm có thể khác nhau tùy đợt ưu đãi...'
        - CTA: '{audience_pronoun} cứ bấm góc trái kiểm tra tài khoản mình xem nhé!'
        - Số 4 đọc là 'bốn'. CẤM 'tư', CẤM 'tứ'. CẤM 'phiên live', CẤM 'trên live', CẤM 'trợ giá'.
        """

    override_rule = f"🛑 CHỈ THỊ ƯU TIÊN CAO NHẤT TỪ NGƯỜI DÙNG: '{custom_note}'. BẮT BUỘC tuân thủ 100%!" if custom_note else ""

    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL TIKTOK SHOP & VIRAL ĐA GIÁC QUAN. PHONG CÁCH: Điện Ảnh Chân Thực
    CHỈ ĐẠO GIỌNG: {voice_guidance}
    {dialogue_type_rule}
    {outro_instruction}
    {override_rule}

    🛑 QUY TẮC BẮT BUỘC VỀ TRANG PHỤC & ĐỒNG NHẤT NHÂN VẬT CHO MỌI SẢN PHẨM:
    1. TRANG PHỤC PHẢI THÍCH ỨNG CHÍNH XÁC VỚI SẢN PHẨM VÀ BỐI CẢNH CỤ THỂ CỦA KỊCH BẢN ĐÓ:
       - Phân tích kỹ ngành hàng để chọn trang phục chuẩn xác:
         • Đồ công nghệ / Gaming / PC: Áo phông/polo, hoodie/cardigan, quần jogger/chinos, giày sneaker. TUYỆT ĐỐI CẤM TẠP ĐỀ!
         • Đồ nấu ăn, bếp núc: Áo thun/polo, tạp dề nấu ăn sạch sẽ.
         • Đồ công sở, văn phòng: Sơ mi/blouse thanh lịch, quần âu, giày da/cao gót.
         • Đồ lót / Nội y: Áo sơ mi pastel hoặc cardigan thanh lịch kín đáo kết hợp quần dài (tuyệt đối không mặc đồ lót lên người, chỉ cầm trên tay).
         • Sản phẩm thời trang (quần áo, váy, áo khoác): Nhân vật MẶC TRỰC TIẾP sản phẩm thời trang đó lên người để review phom dáng.
       - Áp dụng linh hoạt cho MỌI SẢN PHẨM, không giới hạn ngành hàng.
    2. KHÓA ĐỒNG NHẤT 100% XUYÊN SUỐT 4 PHÂN CẢNH TRONG CÙNG 1 KỊCH BẢN:
       - Từ Cảnh 1 đến Cảnh 4, nhân vật BẮT BUỘC giữ nguyên 100% duy nhất: khuôn mặt thuần Việt, màu tóc đen tuyền, kiểu tóc, trang phục và giày dép.

    🛑 KHÓA ÂM THANH: CHỈ DÙNG FOLEY HIỆU ỨNG THỰC TẾ & VOICE, KHỬ 100% NHẠC NỀN (ZERO BGM).
    🛑 KHÓA TIẾP XÚC VẬT LÝ: Tương tác tự nhiên với sản phẩm (mặc trên người hoặc cầm chắc trên tay), cấm thả rơi, cấm biến mất.
    🛑 100% CẢ 4 CẢNH LÀ NHÂN VẬT MỞ MIỆNG NÓI TRỰC TIẾP NGAY TỪ 0.00S.
    {char_rules}
    """

# ==============================================================================
# HÀM TẠO CHI TIẾT KỊCH BẢN - TÍCH HỢP BỘ MÁY STYLIST ĐA NGÀNH & VEO 3 5-LAYER
# ==============================================================================
def create_scene_details(target_id, mode, style="Điện Ảnh Chân Thực"):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if str(sc.get("id")) == str(target_id)), None)
    if not outline: raise Exception(f"Không tìm thấy kịch bản #{target_id} trong danh sách dự án.")
    
    char_profiles = outline.get("character_profiles", st.session_state.get("character_profiles", []))
    char_rules = generate_char_rules_string(char_profiles)
    num_chars = 1
    
    current_active_mode = mode or st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    is_tiktok_shop = ("Viral" not in current_active_mode)
    is_viral = ("Viral" in current_active_mode)

    fixed_title = outline.get('title', 'Kịch bản chi tiết')
    fixed_hook = clean_and_normalize_voiceover(outline.get('hook', ''))
    fixed_setting_base = outline.get('setting', 'Không gian thực tế phù hợp')
    user_custom_note = outline.get("custom_note") or st.session_state.get("current_input_context", "").strip()
    presentation_format = outline.get("presentation_format") or st.session_state.get("last_presentation_format", "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng")
    
    dna = st.session_state.get("content_analysis") or {}
    
    ai_koc_data = dna.get("koc_demographic_analysis", {})
    ai_persona_en = ai_koc_data.get("persona_en", "") if isinstance(ai_koc_data, dict) else ""
    detected_gender, detected_demographic_en = get_demographics_description(char_profiles, ai_persona_en)

    raw_orig_price = dna.get("original_price_spoken", "")
    raw_sale_price = dna.get("sale_price_spoken", "")
    exact_orig_raw = str(dna.get("exact_original_price_ocr", ""))
    exact_sale_raw = str(dna.get("exact_sale_price_ocr", ""))
    
    if not raw_orig_price or not raw_sale_price:
        detected_p = str(dna.get("detected_prices", ""))
        num_matches = [int(n.replace('.', '').replace(',', '')) for n in re.findall(r'\b\d{1,3}(?:[.,]\d{3})+\b', detected_p)]
        if len(num_matches) >= 2:
            num_matches.sort()
            sale_num, orig_num = num_matches[0], num_matches[-1]
            raw_orig_price = number_to_vietnamese_words(orig_num).replace(" đồng", "")
            raw_sale_price = number_to_vietnamese_words(sale_num).replace(" đồng", "")
        elif len(num_matches) == 1:
            raw_orig_price = number_to_vietnamese_words(int(num_matches[0] * 1.25)).replace(" đồng", "")
            raw_sale_price = number_to_vietnamese_words(num_matches[0]).replace(" đồng", "")
        else:
            raw_orig_price = "ba trăm năm mươi nghìn"
            raw_sale_price = "hai trăm chín mươi nghìn"

    orig_price_spoken = clean_and_normalize_voiceover(raw_orig_price)
    sale_price_spoken = clean_and_normalize_voiceover(raw_sale_price)

    soft_orig_price = dna.get("rounded_soft_original_spoken") or convert_to_soft_price_range(orig_price_spoken, is_orig=True, exact_raw_str=exact_orig_raw)
    soft_sale_price = dna.get("rounded_soft_sale_spoken") or convert_to_soft_price_range(sale_price_spoken, is_orig=False, exact_raw_str=exact_sale_raw)

    self_pronoun = dna.get("self_pronoun") or "em"
    audience_pronoun = dna.get("audience_pronoun") or ("các chị em" if not is_viral else "mọi người")

    hero_color_str = dna.get("hero_sku_color", "").strip()
    raw_prod_name = str(dna.get("what_and_unique", "product")).strip()
    if ":" in raw_prod_name: raw_prod_name = raw_prod_name.split(":", 1)[0].strip()

    check_str = f"{raw_prod_name} {fixed_title} {fixed_hook} {user_custom_note} {dna.get('what_and_unique', '')}"
    intimate_type = detect_intimate_apparel(check_str)
    is_fashion_wearable = detect_wearable_fashion(check_str) and intimate_type == "normal"
    
    intimate_safety_rule = ""
    if intimate_type == "underwear_bra":
        fallback_prod_name = f"authentic {hero_color_str} seamless ergonomic comfort fabric garment piece".strip()
        intimate_safety_rule = """
        🛑 CHẾ ĐỘ AN TOÀN TUYỆT ĐỐI CHO ĐỒ LÓT / NỘI Y:
        - TUYỆT ĐỐI CẤM MẶC LÊN NGƯỜI! Nhân vật mặc sơ mi/cardigan kín đáo và CẦM SẢN PHẨM TRÊN TAY để review chất liệu, đệm mút.
        """
    elif is_fashion_wearable:
        fallback_prod_name = f"authentic {hero_color_str} {raw_prod_name}".strip() if hero_color_str else f"authentic {raw_prod_name}"
        intimate_safety_rule = """
        🛑 QUY CHUẢN TRÌNH BÀY SẢN PHẨM THỜI TRANG (WEARABLE ON-BODY TRY-ON):
        1. Nhân vật MẶC TRỰC TIẾP sản phẩm thời trang này lên người để khoe phom dáng (silhouette) thực tế.
        2. HÀNH ĐỘNG: Nhân vật tạo dáng tự nhiên, xoay người nhẹ nhàng và đưa tay chạm/chỉ vào điểm nhấn (chất liệu vải, cúc áo, đường may) đang mặc trên người.
        """
    else:
        fallback_prod_name = f"authentic {hero_color_str} {raw_prod_name}".strip() if hero_color_str else f"authentic {raw_prod_name}"

    clean_prod_en = sanitize_third_party_ip(fallback_prod_name)

    stylist_rules_text = build_multi_industry_stylist_rules(clean_prod_en, hero_color_str, fixed_setting_base, detected_gender, intimate_type, is_fashion_wearable)

    condensed_dna = {
        "product": clean_prod_en,
        "hero_sku_color_locked": hero_color_str,
        "dimensions": dna.get("product_dimensions", "Kích thước chuẩn đời thực"),
        "self_pronoun": self_pronoun,
        "audience_pronoun": audience_pronoun,
        "script_setting": fixed_setting_base,
        "how_to_use": dna.get("how_to_use", ""),
        "correct_ergonomic_grip": dna.get("correct_ergonomic_grip", "")
    }

    action_phrases = (
        f"wearing {clean_prod_en} naturally on body, gracefully turning to show silhouette and gesturing toward the garment details" 
        if is_fashion_wearable else 
        f"holding or interacting with {clean_prod_en} naturally in hands"
    )

    prompt_text = f"""
    DỮ LIỆU ĐẦU VÀO:
    {json.dumps(condensed_dna, ensure_ascii=False)}

    THỂ LOẠI: '{current_active_mode}' | CHIẾN LƯỢC & HÌNH THỨC: '{presentation_format}'
    KỊCH BẢN #{target_id}: TIÊU ĐỀ: '{fixed_title}' | HOOK ĐÃ DUYỆT: '{fixed_hook}' | BỐI CẢNH CỤ THỂ CỦA KỊCH BẢN NÀY: '{fixed_setting_base}'
    DIỄN VIÊN / KOC (ĐÃ PHÂN TÍCH TƯƠNG THÍCH): {detected_demographic_en}.
    SẢN PHẨM: {clean_prod_en}
    GHI CHÚ ƯU TIÊN: {user_custom_note if user_custom_note else 'none'}
    {intimate_safety_rule}
    {stylist_rules_text}

    TRẢ VỀ JSON:
    {{
        "title": "{fixed_title}",
        "wardrobe_lock": {{
            "outfit_vi": "Mô tả chi tiết bằng tiếng Việt trang phục phối theo Bộ máy Stylist đa ngành ăn khớp với {clean_prod_en} và bối cảnh {fixed_setting_base}",
            "master_outfit_en": "Detailed English description of outfit matching {clean_prod_en} following multi-industry stylist rules",
            "hair_and_face_en": "{detected_demographic_en}, neat jet-black hair, warm natural skin tone"
        }},
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention",
                "setting": "Mô tả bối cảnh mở màn tiếng Việt ăn khớp 100% với kịch bản...",
                "setting_en": "English setting description",
                "camera_shot": "Vertical 9:16 eye-level medium shot",
                "expression_en": "looking at camera with natural engaging expression",
                "action_en": "First, {action_phrases}; then smoothly speaking to camera with steady hands",
                "sfx": "Foley âm thanh thao tác thực tế (không nhạc nền)",
                "director": "Attention | Bám sát '{fixed_title}' | Thoại on-camera từ 0.00s",
                "voiceover": "Đoạn thoại mở màn (18-35 từ) xưng '{self_pronoun}' gọi '{audience_pronoun}' chuẩn tiếng Hà Nội..."
            }},
            {{
                "scene": 2, "aida_stage": "Interest",
                "setting": "Mô tả bối cảnh cận cảnh ăn khớp với thoại...",
                "setting_en": "English setting description",
                "camera_shot": "Vertical 9:16 eye-level medium close-up",
                "expression_en": "focused and confident",
                "action_en": "First, demonstrating the key feature of {clean_prod_en}; then inspecting with clean hand separation",
                "sfx": "Tiếng thao tác vật lý chân thực của sản phẩm (không nhạc nền)",
                "director": "Interest | Thao tác trực quan | Thoại on-camera từ 0.00s",
                "voiceover": "Đoạn thoại KOC nói trực tiếp đào sâu tính năng (20-35 từ)..."
            }},
            {{
                "scene": 3, "aida_stage": "Desire",
                "setting": "Mô tả bối cảnh trải nghiệm ăn khớp với thoại...",
                "setting_en": "English setting description",
                "camera_shot": "Vertical 9:16 eye-level lifestyle shot",
                "expression_en": "smiling contentedly with an approving head nod",
                "action_en": "First, completing the usage smoothly; then presenting the satisfying outcome to camera",
                "sfx": "Tiếng trải nghiệm thực tế đời sống (không nhạc nền)",
                "director": "Desire | Bằng chứng thực tế | Thoại on-camera từ 0.00s",
                "voiceover": "Đoạn thoại KOC nói trực tiếp trải nghiệm (20-35 từ)..."
            }},
            {{
                "scene": 4, "aida_stage": "Action",
                "setting": "Mô tả bối cảnh kết thúc...",
                "setting_en": "English warm closing setting",
                "camera_shot": "Vertical 9:16 warm eye-level closing shot",
                "expression_en": "smiling warmly into lens with welcoming hands",
                "action_en": "First, interacting with {clean_prod_en} steadily; then smoothly sharing recommendations with an open-palm hand gesture while smiling warmly to finish",
                "sfx": "Tiếng chuông ting nhẹ nhàng (không nhạc nền)",
                "director": "{'Action | Kêu gọi tương tác follow' if is_viral else 'Action | Chốt deal an toàn'}",
                "voiceover": "{'Đoạn thoại kết nối người xem tự nhiên dưới 28 từ kêu gọi follow' if is_viral else f'Bình thường khoảng {soft_orig_price}, nay giảm chỉ còn khoảng {soft_sale_price} thôi, nhưng giá từng thời điểm có thể khác nhau tùy đợt ưu đãi, {audience_pronoun} cứ bấm góc trái kiểm tra tài khoản mình xem nhé!'}"
            }}
        ]
    }}
    """
    sys_inst = get_sys_inst_details(
        mode=current_active_mode, style="Điện Ảnh Chân Thực", narrator_mode="On-camera",
        char_rules=char_rules, duration_instruction="Thời lượng động sinh học tối đa 10s",
        num_chars=1, character_profiles=char_profiles,
        custom_note=user_custom_note, presentation_format=presentation_format,
        self_pronoun=self_pronoun, audience_pronoun=audience_pronoun,
        setting_archetype=fixed_setting_base, is_fixed_location=True
    )
    res = call_gemini([prompt_text], sys_inst, max_tokens=6500)
    if not res: raise Exception("AI không phản hồi hoặc trả về dữ liệu rỗng. Vui lòng bấm tạo lại.")
    
    scenes = res.get("scenes") or res.get("script") or []
    if not scenes: raise Exception("AI không tạo được danh sách phân cảnh. Vui lòng bấm tạo lại.")
    
    w_lock = res.get("wardrobe_lock", {})
    fallback_outfit_en = "modern clean casual top with comfortable trousers and lifestyle footwear"
    fallback_outfit_vi = "Trang phục phối theo Bộ máy Stylist đa ngành gọn gàng và lịch sự"

    final_outfit_en = sanitize_third_party_ip(w_lock.get("master_outfit_en") or fallback_outfit_en)
    final_outfit_vi = w_lock.get("outfit_vi") or fallback_outfit_vi
    final_actor_head = w_lock.get("hair_and_face_en") or f"{detected_demographic_en}, neat jet-black hair, warm natural skin tone"

    locked_character_prompt_segment = f"{final_actor_head}, strictly wearing identical {final_outfit_en} across all scenes without variation"

    base_negative_prompt = (
        "nsfw, nude, nudity, cleavage, exposed skin, wearing underwear, wearing bra, lingerie model, "
        "suggestive pose, revealing clothes, sheer see-through fabric, opposite gender, celebrity likeness, "
        "public figure, deepfake, inconsistent scale, oversized, deformed hands, extra fingers, text, watermark, "
        "subtitles, blurry, oversaturated, changing clothes, changing outfit, changing hairstyle, different facial identity, "
        "changing shoes, barefoot, apron when not cooking, dropping product, falling product, "
        "morphing object, floating object, background music, musical score, instrumental music, bgm, soundtrack, melody, singing"
    )
    
    total_sec = 0.0
    for scn in scenes:
        if "voiceover" in scn: 
            scn["voiceover"] = clean_and_normalize_voiceover(scn["voiceover"])
        if "director" in scn: 
            scn["director"] = sanitize_policy_text(scn["director"])
        
        raw_speech_time = calculate_speech_duration(scn.get("voiceover", ""), is_tiktok_shop)
        acting_cushion = 1.0 if is_tiktok_shop else 1.3
        dynamic_scene_sec = min(10, max(4, math.ceil(raw_speech_time + acting_cushion)))
        
        actual_speech_time = round(dynamic_scene_sec - 0.8, 1) if raw_speech_time >= dynamic_scene_sec else raw_speech_time
        cushion_sec = round(max(0.5, dynamic_scene_sec - actual_speech_time), 1)
        
        scn["dur"] = f"{dynamic_scene_sec}s"
        scn["actual_speech_sec"] = actual_speech_time
        total_sec += float(dynamic_scene_sec)
        
        vo_text_current = scn.get("voiceover", "")
        setting_vi_current = scn.get("setting", fixed_setting_base)
        env_lighting_en, env_sfx_en = extract_environmental_lighting_and_weather(vo_text_current, setting_vi_current)
        
        camera_shot = scn.get("camera_shot", "Vertical 9:16 eye-level medium shot")
        
        base_sfx = scn.get("sfx", "Natural physical interaction Foley")
        base_sfx = re.sub(r'\b(?:music|soundtrack|melody|song|bgm)\b', 'Foley effect', base_sfx, flags=re.IGNORECASE)
        combined_sfx = f"{base_sfx}, {env_sfx_en}" if env_sfx_en else base_sfx
        scn["sfx"] = combined_sfx
        
        micro_expr_en = scn.get("expression_en", "looking directly at camera lens with a natural engaging expression")
        scene_setting_en = sanitize_third_party_ip(scn.get("setting_en") or fixed_setting_base)
        raw_action = scn.get("action_en") or f"First, demonstrating {clean_prod_en} naturally; then smoothly speaking to camera with steady hands"
        clean_action = sanitize_third_party_ip(re.sub(r'^(?:Character\s+(?:is\s+)?|Subject\s+(?:is\s+)?)', '', raw_action, flags=re.IGNORECASE).strip())

        img_core = (
            f"{camera_shot}, commercial live-action photography, {scene_setting_en}, {env_lighting_en}. "
            f"Subject: {locked_character_prompt_segment}, {micro_expr_en}, {clean_action}, "
            f"featuring {clean_prod_en} with firm anatomical finger grip and accurate real-world scale"
        )
        scn["img_p"] = sanitize_third_party_ip(f"{img_core}, 8k resolution, photorealistic skin texture, sharp focus --ar 9:16 --style raw --v 6.1")
        scn["img_neg"] = base_negative_prompt
        
        clean_vo_for_audio = re.sub(r'\.{2,}', '.', vo_text_current).strip()

        raw_vid = (
            f"[CAMERA & LIGHTING]: {camera_shot}, smooth Steadicam gimbal live-action footage, {env_lighting_en}. "
            f"[SETTING]: {scene_setting_en}. "
            f"[SUBJECT LOCK]: {locked_character_prompt_segment}, {micro_expr_en}. "
            f"[ACTION & RIGID PHYSICS]: {clean_action}. Subject interacts with solid {clean_prod_en} maintaining consistent 3D geometry, "
            f"rigid-body physics, and firm anatomical finger grip (or resting stably on surface, never floating, morphing, or dropping). "
            f"[LIP-SYNC & TIMING ({dynamic_scene_sec}s total)]: From 0.0s to {actual_speech_time}s, subject speaks directly to camera with accurate "
            f"Vietnamese lip-sync and natural facial micro-expressions; for the final {cushion_sec}s, subject smoothly closes mouth into a natural "
            f"warm smile with gentle breathing and subtle head nod. "
            f"[AUDIO & VOICEOVER]: Clear native Northern Vietnamese (Hanoi accent) voice speaking at a natural pace: \"{clean_vo_for_audio}\". "
            f"Strictly diegetic Foley sound effects only [{combined_sfx}], 100% zero background music, no BGM, pure clean camera footage."
        )
        scn["vid_p"] = sanitize_veo3_prompt(raw_vid)
        scn["vid_neg"] = base_negative_prompt
        
    res["scenes"] = scenes
    res["total_dur"] = f"Khoảng {int(total_sec)} giây"
    
    goal_badge = "🌟 <b>Định hướng:</b> Xây Kênh & Kéo Tương Tác / Follow" if is_viral else "🛒 <b>Định hướng:</b> Chốt đơn TikTok Shop an toàn"
    summary_lines = [
        f"⏱ <b>Thời lượng:</b> Khoảng {int(total_sec)}s (Tối đa 10s/cảnh) | 🎬 <b>Chiến lược & Hình thức:</b> {presentation_format} | 👤 <b>Khóa diễn viên:</b> {detected_demographic_en}",
        f"🗣 <b>Đại từ xưng hô:</b> '{self_pronoun}' - '{audience_pronoun}' | 🏙 <b>Bối cảnh kịch bản:</b> {fixed_setting_base} | {goal_badge}",
        f"👗 <b>Khóa trang phục (Bộ máy Stylist):</b> {final_outfit_vi} (Đồng nhất 100% cả 4 cảnh)",
        f"🎨 <b>Khóa màu Hero SKU:</b> {hero_color_str if hero_color_str else 'Chuẩn ảnh'} (Đồng nhất 100% cả 4 cảnh)",
        f"🌤 <b>Cảm biến môi trường & Veo 3 5-Layer:</b> Tự động đồng bộ Ánh sáng thời tiết, Khóa vật lý 3D & Định thời gian Lip-Sync chuẩn từng giây",
        f"🔇 <b>Âm thanh bản quyền:</b> Thuần Foley SFX thực tế đời sống & Voiceover, triệt tiêu 100% nhạc nền (Zero BGM)",
        f"💰 <b>Khoảng giá an toàn (Cảnh 4):</b> Bình thường khoảng {soft_orig_price}, nay giảm khoảng {soft_sale_price}"
    ]
    if is_fashion_wearable:
        summary_lines.append("👗 <b>Chế độ Thời trang Wearable:</b> Nhân vật mặc trực tiếp sản phẩm lên người, xoay người khoe phom dáng.")
    if user_custom_note and user_custom_note.lower() not in ["mặc định chuẩn", "không có", "không có ghi chú đặc biệt, tuân thủ kịch bản chuẩn."]:
        summary_lines.append(f"🎯 <b>Ghi chú riêng:</b> {user_custom_note}")
    res["director_summary"] = "<br>".join(summary_lines)
    
    st.session_state.generated_details[int(target_id)] = res
    st.session_state.generated_details[str(target_id)] = res

def clone_script(script_id):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    style = "Điện Ảnh Chân Thực"
    is_viral = ("Viral" in mode)
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if str(sc.get("id")) == str(script_id)), None)
    if not target: return []
    
    cur_len = len(all_combined)
    target_detail = st.session_state.generated_details.get(int(script_id), st.session_state.generated_details.get(str(script_id), {}))
    user_custom_note = target.get("custom_note") or st.session_state.get("current_input_context", "").strip()
    presentation_format = target.get("presentation_format") or st.session_state.get("last_presentation_format", "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng")
    
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
        "self_pronoun": self_pronoun,
        "audience_pronoun": audience_pronoun
    }

    target_char_profiles = target.get("character_profiles", st.session_state.get("character_profiles", []))

    prompt = f"""
    SẢN PHẨM: {json.dumps(condensed_dna, ensure_ascii=False)} | GỐC #{script_id}: '{target.get('title', '')}'
    THOẠI GỐC:\n{full_voice_text}
    NHIỆM VỤ: Giữ nguyên 90% cốt truyện, thông điệp, đòn bẩy giá. Chỉ đổi bối cảnh sinh hoạt và diễn đạt tự nhiên (CẤM các từ 'thuật toán', 'máy phân tích').
    ĐẠI TỪ: Xưng '{self_pronoun}' - Gọi '{audience_pronoun}'.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên biến thể 1", "setting": "Bối cảnh đời thực 1...", "hook": "Câu hook ngắn gọn nhân vật nói trực tiếp bám sát gốc...", "actors": 1 }},
            {{ "id": {cur_len+2}, "title": "Tên biến thể 2", "setting": "Bối cảnh đời thực 2...", "hook": "...", "actors": 1 }},
            {{ "id": {cur_len+3}, "title": "Tên biến thể 3", "setting": "Bối cảnh đời thực 3...", "hook": "...", "actors": 1 }},
            {{ "id": {cur_len+4}, "title": "Tên biến thể 4", "setting": "Bối cảnh đời thực 4...", "hook": "...", "actors": 1 }},
            {{ "id": {cur_len+5}, "title": "Tên biến thể 5", "setting": "Bối cảnh đời thực 5...", "hook": "...", "actors": 1 }}
        ]
    }}
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, "On-camera", "", 1, "Nhân bản thoại trung thành", user_custom_note, presentation_format), max_tokens=2500)
    clones = res.get("outlines", res.get("script_outlines", []))
    formatted_clones = []
    for idx, cl in enumerate(clones):
        formatted_clones.append({
            "id": cur_len + idx + 1, "title": cl.get("title", f"Biến thể kịch bản #{cur_len + idx + 1}"),
            "setting": cl.get("setting", f"Bối cảnh sinh hoạt #{idx+1}"), "hook": clean_and_normalize_voiceover(cl.get("hook", "")),
            "actors": 1, "character_profiles": target_char_profiles,
            "duration_instruction": target.get("duration_instruction", "Thời lượng động sinh học tối đa 10s"), 
            "narrator_mode": "Nhân vật xuất hiện (On-camera)",
            "custom_note": user_custom_note,
            "presentation_format": presentation_format
        })
    return formatted_clones

def generate_more_scripts(unified_strategy_format, char_profiles, extra_note=""):
    mode = st.session_state.get("last_mode", "🛒 TikTok Shop & Bán Hàng")
    style = "Điện Ảnh Chân Thực"
    duration_inst = "Thời lượng động sinh học (tối đa 10s/cảnh)"
    char_rules = generate_char_rules_string(char_profiles)
    cur_len = len(st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts)
    active_note = extra_note.strip() if extra_note.strip() else st.session_state.get("current_input_context", "").strip()
    active_format = unified_strategy_format if unified_strategy_format else st.session_state.get("last_presentation_format", "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng")
    dna = st.session_state.get("content_analysis") or {}
    self_pronoun = dna.get("self_pronoun", "em")
    audience_pronoun = dna.get("audience_pronoun", "các chị em" if "Viral" not in mode else "mọi người")
    condensed_dna = {
        "product": dna.get("what_and_unique", ""),
        "hero_sku": dna.get("hero_sku_color", ""),
        "self_pronoun": self_pronoun,
        "audience_pronoun": audience_pronoun
    }

    prompt = f"""
    SẢN PHẨM: {json.dumps(condensed_dna, ensure_ascii=False)} | CHIẾN LƯỢC & HÌNH THỨC: '{active_format}' | DIỄN VIÊN: 1 người Việt.
    ĐẠI TỪ: Xưng '{self_pronoun}' - Gọi '{audience_pronoun}'.
    GHI CHÚ ƯU TIÊN: '{active_note if active_note else "none"}'
    TẠO 5 KỊCH BẢN Ở 5 BỐI CẢNH ĐỜI THỰC KHÁC NHAU.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên kịch bản 1", "setting": "Bối cảnh đời thực 1...", "hook": "Câu hook ngắn gọn nhân vật nói trực tiếp...", "actors": 1 }},
            {{ "id": {cur_len+2}, "title": "Tên kịch bản 2", "setting": "Bối cảnh đời thực 2...", "hook": "...", "actors": 1 }},
            {{ "id": {cur_len+3}, "title": "Tên kịch bản 3", "setting": "Bối cảnh đời thực 3...", "hook": "...", "actors": 1 }},
            {{ "id": {cur_len+4}, "title": "Tên kịch bản 4", "setting": "Bối cảnh đời thực 4...", "hook": "...", "actors": 1 }},
            {{ "id": {cur_len+5}, "title": "Tên kịch bản 5", "setting": "Bối cảnh đời thực 5...", "hook": "...", "actors": 1 }}
        ]
    }}
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, "On-camera", char_rules, 1, active_format, active_note, active_format), max_tokens=2500)
    more_scripts = res.get("outlines", res.get("script_outlines", []))
    for idx, sc in enumerate(more_scripts):
        if "hook" in sc: sc["hook"] = clean_and_normalize_voiceover(sc["hook"])
        sc.update({
            "id": cur_len + idx + 1, "duration_instruction": duration_inst, 
            "narrator_mode": "Nhân vật xuất hiện (On-camera)", 
            "character_profiles": char_profiles, "actors": 1,
            "custom_note": active_note,
            "presentation_format": active_format
        })
    return more_scripts

# ==============================================================================
# 3. THANH BÊN (SIDEBAR) & QUẢN TRỊ ADMIN TOÀN NĂNG
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
            
            with st.expander("❓ Quên mật khẩu?"):
                st.info("💡 Nếu quên mật khẩu, vui lòng liên hệ Hotline / Zalo Admin: **0869 628 316** để được xác thực tài khoản và cấp lại mật khẩu ngay lập tức.")
                        
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
        is_admin_user = (st.session_state.current_email == ADMIN_EMAIL)
        
        if supabase:
            try:
                if is_admin_user:
                    res = supabase.table("saved_projects").select("*").order("created_at", desc=True).execute()
                else:
                    res = supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
                all_projects = res.data or []
            except: all_projects = []

            if is_admin_user and all_projects:
                creator_emails = sorted(list(set(p.get("user_email", "") for p in all_projects if p.get("user_email"))))
                sel_creator = st.selectbox("👤 Lọc theo thành viên:", ["Tất cả thành viên"] + creator_emails, key="admin_sel_creator")
                if sel_creator != "Tất cả thành viên":
                    all_projects = [p for p in all_projects if p.get("user_email") == sel_creator]

            search_proj = st.text_input("🔍 Tìm kiếm dự án:", placeholder="Nhập tên dự án...", key="search_proj_input")
            display_projects = [p for p in all_projects if search_proj.strip().lower() in p['project_title'].lower()] if search_proj.strip() else (all_projects if st.session_state.show_all_projects else all_projects[:3])

            if not display_projects: st.info("Chưa có dự án nào.")
            else:
                for p in display_projects:
                    proj_creator = p.get("user_email", "N/A")
                    with st.expander(f"🎬 {p['project_title']}"):
                        if is_admin_user:
                            st.markdown(f"<span style='font-size:12px; color:#1e40af; background:#dbeafe; padding:2px 8px; border-radius:4px; font-weight:600;'>👤 Tạo bởi: {proj_creator}</span>", unsafe_allow_html=True)
                            st.caption(f"📅 Ngày tạo: {p.get('created_at', '')[:10]}")
                        
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

        if is_admin_user:
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

            st.markdown("##### 👥 Danh Sách Tài Khoản & Mật Khẩu")
            search_acc = st.text_input("🔍 Tìm tài khoản:", placeholder="Nhập Email hoặc SĐT...", key="search_acc_input")
            other_accs = [item for item in st.session_state.licensed_accounts.items() if item[0] != ADMIN_EMAIL]
            filt_accs = [item for item in other_accs if search_acc.strip().lower() in item[0].lower() or search_acc.strip() in item[1].get('phone', '')] if search_acc.strip() else (other_accs if st.session_state.show_all_admin_accounts else other_accs[:3])

            for acc_mail, info in filt_accs:
                with st.expander(f"👤 {acc_mail} ({info.get('plan_type')})"):
                    st.write(f"📞 SĐT: `{info.get('phone', 'N/A')}` | ⏳ Hạn: `{info.get('expires_at')}`")
                    
                    new_user_pass = st.text_input("🔑 Đổi mật khẩu:", value=info.get("password", ""), key=f"pass_edit_{acc_mail}")
                    if st.button("⚡ Đặt 123456", key=f"btn_quick_reset_{acc_mail}", use_container_width=True, disabled=is_system_busy, help="Reset mật khẩu tài khoản này về 123456"):
                        st.session_state.licensed_accounts[acc_mail]["password"] = "123456"
                        save_single_account(acc_mail, st.session_state.licensed_accounts[acc_mail])
                        st.toast(f"✅ Đã reset mật khẩu của {acc_mail} về '123456'!"); time.sleep(0.3); st.rerun()

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
                        st.session_state.licensed_accounts[acc_mail]["password"] = new_user_pass.strip()
                        st.session_state.licensed_accounts[acc_mail]["roles"] = new_roles
                        st.session_state.licensed_accounts[acc_mail]["plan_type"] = new_plan
                        st.session_state.licensed_accounts[acc_mail]["expires_at"] = target_exp_str
                        save_single_account(acc_mail, st.session_state.licensed_accounts[acc_mail])
                        st.toast("✅ Đã cập nhật tài khoản và mật khẩu thành công!"); time.sleep(0.4); st.rerun()
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
# 5. KHÔNG GIAN SÁNG TẠO CHÍNH (ĐÃ TỐI ƯU HÓA GIAO DIỆN GỌN GÀNG)
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Đạo Diễn AI - Hệ Thống Kịch Bản Pro</div></div>""", unsafe_allow_html=True)

user_allowed_modules = st.session_state.licensed_accounts.get(st.session_state.current_email, {}).get("roles", ALL_MODULES) or ALL_MODULES
mode = st.selectbox("🎯 Thể loại:", user_allowed_modules, key=f"mode_sel_{st.session_state.reset_key}")
is_viral_mode = "Viral" in mode

up_files, custom_note = [], ""
viral_persona, viral_topic = "", ""
if is_viral_mode:
    col_v1, col_v2 = st.columns(2)
    viral_persona = col_v1.text_input("👤 Định vị Kênh:", placeholder="Ví dụ: Mẹ bỉm sữa thông thái, KOC chuyên gia công nghệ...", key=f"viral_persona_{st.session_state.reset_key}")
    viral_topic = col_v2.text_area("💡 Chủ đề / Mẹo:", height=68, placeholder="Ví dụ: 3 mẹo setup góc làm việc gọn gàng, cách chọn chuột công thái học...", key=f"viral_topic_{st.session_state.reset_key}")
    up_files = st.file_uploader("📦 Upload Ảnh:", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_viral_{st.session_state.reset_key}")
    
    if up_files:
        with st.expander(f"👁 Xem lại {len(up_files)} ảnh đã tải lên", expanded=False):
            n_cols = min(len(up_files), 4)
            cols = st.columns(n_cols)
            for idx, f in enumerate(up_files):
                cols[idx % n_cols].image(f, caption=f"Ảnh {idx + 1}", use_container_width=True)
                
    custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất - ví dụ: cầm chắc chuột trên pad lót bàn, thao tác click đanh chắc):", key=f"custom_note_viral_{st.session_state.reset_key}")
    hero_sku_override = ""
else:
    products_data = supabase.table("products").select("*").execute().data if supabase else []
    if products_data:
        selected_name = st.selectbox("📌 Chọn sản phẩm:", [p["product_name"] for p in products_data], key=f"prod_select_{st.session_state.reset_key}")
        st.session_state.current_product_data = next(p for p in products_data if p["product_name"] == selected_name)
    
    col_f1, col_f2 = st.columns([2, 1])
    up_files = col_f1.file_uploader("📦 Upload Ảnh SP (Quét OCR Giá, Hero SKU & Bảng màu):", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_prod_{st.session_state.reset_key}")
    hero_sku_override = col_f2.text_input("🎯 Màu / SKU ưu tiên (Tùy chọn):", placeholder="Ví dụ: Đen nhám, Trắng, RGB, Size M...", key=f"hero_override_{st.session_state.reset_key}")
    
    if up_files:
        with st.expander(f"👁 Xem lại {len(up_files)} ảnh sản phẩm đã tải lên", expanded=False):
            n_cols = min(len(up_files), 4)
            cols = st.columns(n_cols)
            for idx, f in enumerate(up_files):
                cols[idx % n_cols].image(f, caption=f"Ảnh {idx + 1}", use_container_width=True)
                
    custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất - ví dụ: cầm chắc chuột trên pad lót bàn, thao tác click đanh chắc):", key=f"custom_note_prod_{st.session_state.reset_key}")

# MẶC ĐỊNH HỆ THỐNG: Phong cách Điện Ảnh Chân Thực | 1 Diễn viên | Nhân vật nói trực tiếp On-camera
style = "Điện Ảnh Chân Thực"
num_chars = 1
narrator_mode = "Nhân vật xuất hiện (On-camera)"

# BỐ CỤC GỌN GÀNG TRÊN 1 HÀNG: GỘP CHIẾN LƯỢC & HÌNH THỨC + VAI TRÒ NV + UPLOAD ẢNH NV
col_strat, col_role, col_actor_img = st.columns([1.4, 1.6, 1.0])

unified_strategy_format = col_strat.selectbox(
    "🧭 Chiến lược & Hình thức Video:",
    UNIFIED_STRATEGY_FORMAT_OPTS,
    index=0,
    key=f"unified_strat_format_{st.session_state.reset_key}"
)

role_input = col_role.text_input(
    "👤 Vai trò NV (Để trống để AI tự phân tích phù hợp):",
    value="",
    placeholder="Để trống = AI tự phân tích KOC (hoặc nhập: Nam 25t, Bác 50t...)",
    key=f"r_0_{st.session_state.reset_key}"
)

c_file = col_actor_img.file_uploader(
    "📸 Ảnh mẫu NV (Tùy chọn):",
    type=["jpg", "png"],
    key=f"f_0_{st.session_state.reset_key}"
)

char_inputs = []
if c_file or role_input.strip():
    char_inputs.append({"id": 1, "role": role_input.strip(), "file": c_file})

if st.button("🚀 Phân Tích Sản Phẩm Và Tạo Kịch Bản", type="primary", use_container_width=True, disabled=is_system_busy):
    can_run, msg = check_usage_limit(st.session_state.current_email)
    if not can_run: st.error(msg)
    else:
        with st.spinner("⏳ Đạo diễn AI đang quét dữ liệu, phân tích KOC phù hợp & thiết lập Kịch bản..."):
            try:
                st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs] if char_inputs else [{"id": 1, "role": ""}]
                char_rules = generate_char_rules_string(st.session_state.character_profiles)
                st.session_state.update({
                    "last_mode": mode, "last_style": style, "last_narrator": "On-camera", 
                    "last_presentation_format": unified_strategy_format,
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
                CHIẾN LƯỢC & HÌNH THỨC VIDEO YÊU CẦU: '{unified_strategy_format}'
                DIỄN VIÊN: 1 nhân vật 100% người Việt bản địa nói trực tiếp trước ống kính (On-camera).
                
                🛑 QUY CHUẨN TỰ ĐỘNG PHÂN TÍCH CHÂN DUNG KOC PHÙ HỢP (KOC DEMOGRAPHIC ANALYSIS):
                - NẾU NGƯỜI DÙNG ĐỂ TRỐNG VAI TRÒ: BẮT BUỘC bạn phải tự động phân tích tính chất sản phẩm, ngành hàng và bối cảnh để chọn ra chân dung KOC (độ tuổi, giới tính, phong thái) phù hợp nhất:
                  • Đồ công nghệ / Gaming / Phụ kiện PC / Xe cộ: Nam thanh niên 22-26 tuổi am hiểu công nghệ, năng động, hiện đại.
                  • Đồ gia dụng bếp / Chảo nồi / Nấu ăn: Nữ nội trợ / mẹ trẻ 28-35 tuổi ấm áp, chu đáo.
                  • Mỹ phẩm / Chăm sóc da / Thời trang nữ / Nội y: Nữ 22-26 tuổi da sáng, tươi tắn, thanh lịch.
                  • Dụng cụ cầm tay / Cơ khí / Làm vườn / Cây cảnh: Nam trung niên / bác 40-50 tuổi từng trải, thực tế.
                  • Mẹ & Bé: Mẹ bỉm 26-32 tuổi dịu dàng hoặc bố trẻ 28-32 tuổi.
                - NẾU NGƯỜI DÙNG ĐÃ NHẬP VAI TRÒ CỤ THỂ: Ưu tiên 100% yêu cầu người dùng!
                - Ghi rõ kết quả vào trường 'koc_demographic_analysis' trong JSON.

                🛑 QUY CHUẨN AN TOÀN CHO SẢN PHẨM ĐỒ LÓT & THỜI TRANG:
                - Nếu sản phẩm là áo lót, quần lót, nội y, bikini: TUYỆT ĐỐI KHÔNG mặc trực tiếp lên người! Nhân vật mặc đồ đời thường kín đáo và CẦM SẢN PHẨM TRÊN TAY (hoặc treo trên móc) để kiểm tra độ co giãn, chất vải. Dùng từ ngữ thanh lịch ('vòng một', 'gom phom'), CẤM từ nhạy cảm ('khe ngực', 'vú', 'sexy').
                - Nếu sản phẩm là thời trang mặc trên người (quần áo, váy, giày dép): Nhân vật MẶC TRỰC TIẾP SẢN PHẨM LÊN NGƯỜI, tạo dáng tự nhiên, xoay người khoe phom dáng và chỉ tay vào điểm nhấn (chất liệu, cúc áo, đường may) đang mặc trên người.

                🛑 QUY CHUẨN ĐẶC BIỆT KHI CÓ ẢNH DIỄN VIÊN TẢI LÊN:
                - KHI CÓ ẢNH DIỄN VIÊN: CHỈ TRÍCH XUẤT ĐẶC TRƯNG SINH TRẮC HỌC KHUÔN MẶT, MẮT, SỐNG MŨI, TÔNG DA, TÓC ĐEN TỰ NHIÊN!
                - TUYỆT ĐỐI BỎ QUA 100% TRANG PHỤC CŨ TRONG ẢNH!

                🛑 QUY CHUẨN MA TRẬN NHÂN XƯNG CHO MỌI NGÀNH HÀNG:
                - Tự động nhận diện ngành hàng từ dữ liệu đầu vào:
                  • Đồ công nghệ / PC / Gaming / Thiết bị điện tử: self_pronoun = 'em', audience_pronoun = 'anh em' (hoặc 'các bác'). CẤM gọi 'các mẹ', CẤM 'các chị em'!
                  • Đồ gia dụng bếp, tẩy rửa: self_pronoun = 'em', audience_pronoun = 'các chị em' (hoặc 'các bác').
                  • Thời trang nữ / Mỹ phẩm / Nội y: self_pronoun = 'em', audience_pronoun = 'các chị em' / 'các nàng'.
                  • Mẹ & Bé: self_pronoun = 'em', audience_pronoun = 'các mẹ'.
                  • Đời sống / Ăn vặt: self_pronoun = 'em', audience_pronoun = 'mọi người' / 'cả nhà'.

                🛑 QUY CHUẨN BỐI CẢNH ĐỜI THỰC PHÙ HỢP VỚI TỪNG SẢN PHẨM:
                - BẮT BUỘC 5 kịch bản diễn ra ở 5 bối cảnh đời thực khác nhau ăn khớp tuyệt đối với tính chất của sản phẩm.

                100% CẢ 4 PHÂN CẢNH ĐỀU LÀ DO CHÍNH NHÂN VẬT MỞ MIỆNG NÓI TRỰC TIẾP TRƯỚC ỐNG KÍNH (ON-CAMERA LIP-SYNC) NGAY TỪ 0.00S BẰNG GIỌNG HÀ NỘI CHUẨN.
                🛑 CẤM TUYỆT ĐỐI TỪ 'NGÀN' (BẮT BUỘC DÙNG 'NGHÌN'). SỐ 4 ĐỌC LÀ 'BỐN' (CẤM 'TƯ', CẤM 'TỨ'). CẤM '1 TRĂM' (BẮT BUỘC VIẾT 'MỘT TRĂM'). CẤM 'TRỢ GIÁ', 'PHIÊN LIVE'.
                CHỈ ĐẠO HERO SKU: {override_instruction}
                
                BẮT BUỘC TRẢ VỀ JSON:
                {{
                    "content_analysis": {{
                        "self_pronoun": "em",
                        "audience_pronoun": "anh em / các chị em",
                        "setting_archetype": "Bối cảnh chuẩn mực đời thực phù hợp sản phẩm",
                        "is_fixed_location": true,
                        "koc_demographic_analysis": {{
                            "gender": "male hoặc female",
                            "persona_vi": "Mô tả chân dung KOC phù hợp bằng tiếng Việt",
                            "persona_en": "a 24-year-old native Vietnamese young woman"
                        }},
                        "how_to_use": "Mô tả thao tác đời thực chuẩn xác",
                        "correct_ergonomic_grip": "Tư thế cầm nắm công thái học của sản phẩm",
                        "exact_original_price_ocr": "Giá gốc OCR",
                        "exact_sale_price_ocr": "Giá sale OCR",
                        "original_price_spoken": "giá gốc bằng chữ",
                        "sale_price_spoken": "giá sale bằng chữ",
                        "rounded_soft_original_spoken": "khoảng giá gốc",
                        "rounded_soft_sale_spoken": "khoảng giá sale",
                        "recommended_setting_en": "Realistic clean modern setting under 15 words",
                        "target_audience": "Tệp khách hàng mục tiêu",
                        "core_value": "Giá trị cốt lõi",
                        "pain_points": "Nỗi đau thực tế",
                        "hook_element": "Yếu tố giật gân 3 giây đầu",
                        "recommended_format": "Hình thức & Chiến lược đề xuất tối ưu",
                        "format_reason": "Lý do đề xuất",
                        "hero_sku_color": "Mã màu Hero SKU",
                        "color_palette": "Bảng màu toàn bộ",
                        "what_and_unique": "[Tên sản phẩm]: [Điểm độc bản USP]",
                        "target_user": "Đối tượng phù hợp nhất",
                        "why_buy": "Lý do thuyết phục nên mua",
                        "where_and_convenience": "Hoàn cảnh ứng dụng và sự tiện lợi",
                        "product_dimensions": "Kích thước đời thực",
                        "prompt_dna_lock": "Visual DNA cho video"
                    }},
                    "outlines": [
                        {{ "id": 1, "title": "Tên kịch bản 1", "setting": "Bối cảnh đời thực 1 phù hợp sản phẩm...", "hook": "Câu hook ngắn gọn nhân vật nói trực tiếp...", "actors": 1 }},
                        {{ "id": 2, "title": "Tên kịch bản 2", "setting": "Bối cảnh đời thực 2...", "hook": "...", "actors": 1 }},
                        {{ "id": 3, "title": "Tên kịch bản 3", "setting": "Bối cảnh đời thực 3...", "hook": "...", "actors": 1 }},
                        {{ "id": 4, "title": "Tên kịch bản 4", "setting": "Bối cảnh đời thực 4...", "hook": "...", "actors": 1 }},
                        {{ "id": 5, "title": "Tên kịch bản 5", "setting": "Bối cảnh đời thực 5...", "hook": "...", "actors": 1 }}
                    ]
                }}
                """
                payload = ["IMAGES:"]
                for cb, cm in st.session_state["saved_reference_images"]:
                    payload.append(types.Part.from_bytes(data=cb, mime_type=cm))
                for c in char_inputs:
                    if c.get("file"):
                        cb, cm = compress_image_bytes(c['file'], 768, 75)
                        payload.extend([f"ACTOR {c['id']} (EXTRACT FACE, EYE, SKIN TONE, JET-BLACK HAIR ONLY - DISCARD OLD CLOTHES/BACKGROUND):", types.Part.from_bytes(data=cb, mime_type=cm)])
                payload.append(prompt)
                
                res = call_gemini(payload, get_sys_inst_outlines(mode, style, "On-camera", char_rules, 1, unified_strategy_format, custom_note.strip(), unified_strategy_format), max_tokens=6000)
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
                        "actors": 1,
                        "custom_note": custom_note.strip(),
                        "presentation_format": unified_strategy_format
                    })
                st.session_state.update({"all_scripts": outlines, "cloned_scripts": [], "expanded_scripts": [], "generated_details": {}, "active_script_id": None})
                st.toast("✅ Đã phân tích KOC & Thiết lập kịch bản hoàn hảo!"); time.sleep(0.3); st.rerun()
            except Exception as e: st.error(f"❌ Lỗi: {e}")

# ==============================================================================
# BỐ CỤC: 2 CỘT ĐỐI XỨNG & ĐÁNH SỐ ĐỘNG LIỀN MẠCH
# ==============================================================================
ca = st.session_state.content_analysis
if isinstance(ca, dict):
    st.divider()
    st.markdown("### 🔍 **Phân Tích Chi Tiết**")
    
    col_row1_left, col_row1_right = st.columns(2)
    with col_row1_left:
        c1_html = clean_html(f"""
        <div class="dna-card">
            <div class="dna-card-title">🎯 1. Chân dung Khách hàng & Hook 3s (Attention)</div>
            <div class="dna-row"><span class="dna-label">👥 Tệp khách hàng:</span><span class="dna-text">{clean_analysis_text(ca.get('target_audience', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">💔 Nỗi đau thực tế:</span><span class="dna-text">{clean_analysis_text(ca.get('pain_points', ''))}</span></div>
            <div class="dna-row"><span class="dna-label" style="color:#d90429;">⚡ Yếu tố Hook 3s đầu:</span><span class="dna-text" style="color:#d90429; font-weight:600;">{clean_analysis_text(ca.get('hook_element', ''))}</span></div>
            <div class="dna-row"><span class="dna-label" style="color:#2563eb;">🎬 Chiến lược & Hình thức tối ưu:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{clean_analysis_text(ca.get('recommended_format', 'Review / Trải nghiệm'))}</span></div>
            <div class="dna-row"><span class="dna-label">💡 Lý do đề xuất:</span><span class="dna-text">{clean_analysis_text(ca.get('format_reason', ''))}</span></div>
        </div>
        """)
        st.markdown(c1_html, unsafe_allow_html=True)

    with col_row1_right:
        koc_persona_desc = ca.get('koc_demographic_analysis', {}).get('persona_vi', 'Tự động chọn KOC phù hợp') if isinstance(ca.get('koc_demographic_analysis'), dict) else 'Tự động chọn KOC'
        user_specified_actors = [p['role'] for p in st.session_state.get('character_profiles', []) if str(p.get('role', '')).strip()]
        koc_display_str = f"👤 <b>KOC:</b> {', '.join(user_specified_actors)} (Người dùng chỉ định)" if user_specified_actors else f"🤖 <b>KOC tự động:</b> {koc_persona_desc}"

        pronoun_badge = f"🗣 <b>Nhân xưng:</b> KOC xưng <b>'{ca.get('self_pronoun', 'em')}'</b> - Gọi người xem là <b>'{ca.get('audience_pronoun', 'anh em / các bác')}'</b>"
        if is_viral_mode:
            c2_html = clean_html(f"""
            <div class="dna-card">
                <div class="dna-card-title">🌟 2. Định Vị Kênh & Ma Trận Nhân Xưng</div>
                <div class="dna-row"><span class="dna-label">🎭 Chân dung KOC:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{koc_display_str}</span></div>
                <div class="dna-row"><span class="dna-label">👤 Định vị kênh:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{clean_analysis_text(ca.get('target_user', viral_persona or 'KOC Chuyên gia đời sống'))}</span></div>
                <div class="dna-row"><span class="dna-label">🗣 Nhân xưng chuẩn:</span><span class="dna-text" style="color:#15803d; font-weight:700;">{pronoun_badge}</span></div>
                <div class="dna-row"><span class="dna-label">💎 Giá trị cốt lõi:</span><span class="dna-text">{clean_analysis_text(ca.get('core_value', ''))}</span></div>
            </div>
            """)
        else:
            c2_html = clean_html(f"""
            <div class="dna-card">
                <div class="dna-card-title">🔥 2. Diễn Viên KOC & Mã Màu Bán Chạy</div>
                <div class="dna-row"><span class="dna-label">🎭 Chân dung KOC:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{koc_display_str}</span></div>
                <div class="dna-row"><span class="dna-label">⭐ Mẫu ưu tiên làm video:</span><span class="dna-text" style="color:#dc2626; font-weight:700;">{clean_analysis_text(ca.get('hero_sku_color', 'Tự động'))}</span></div>
                <div class="dna-row"><span class="dna-label">🗣 Nhân xưng chuẩn:</span><span class="dna-text" style="color:#15803d; font-weight:700;">{pronoun_badge}</span></div>
                <div class="dna-row"><span class="dna-label">🎨 Toàn bộ bảng màu:</span><span class="dna-text">{clean_analysis_text(ca.get('color_palette', ''))}</span></div>
            </div>
            """)
        st.markdown(c2_html, unsafe_allow_html=True)

    col_row2_left, col_row2_right = st.columns(2)
    with col_row2_left:
        c3_html = clean_html(f"""
        <div class="dna-card">
            <div class="dna-card-title">💎 3. Giải phẫu Sản phẩm & Nội Dung (Interest & Desire)</div>
            <div class="dna-row"><span class="dna-label">📦 Chủ đề & Điểm đặc biệt:</span><span class="dna-text">{format_product_name_bold(ca.get('what_and_unique', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">👥 Đối tượng phù hợp:</span><span class="dna-text">{clean_analysis_text(ca.get('target_user', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">🔥 Tại sao nên xem/mua:</span><span class="dna-text">{clean_analysis_text(ca.get('why_buy', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">📍 Hoàn cảnh & Tiện ích:</span><span class="dna-text">{clean_analysis_text(ca.get('where_and_convenience', ''))}</span></div>
            <div class="dna-row"><span class="dna-label">🛠 Thao tác & Cách dùng chuẩn thực tế:</span><span class="dna-text">{clean_analysis_text(ca.get('how_to_use', ''))}</span></div>
        </div>
        """)
        st.markdown(c3_html, unsafe_allow_html=True)

    with col_row2_right:
        dim_txt_display = ca.get('product_dimensions', 'Chuẩn đời thực')
        loc_type_str = "Khóa 1 vị trí cố định (Single-Location)" if ca.get('is_fixed_location', True) else "Chuyển cảnh theo mạch truyện (Dynamic)"
        if is_viral_mode:
            c4_html = clean_html(f"""
            <div class="dna-card">
                <div class="dna-card-title">💡 4. Chuẩn Bối Cảnh & Mẹo Đời Sống</div>
                <div class="dna-row"><span class="dna-label">🏙 Chuẩn bối cảnh:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{clean_analysis_text(ca.get('setting_archetype', 'Góc làm việc / Phòng riêng hiện đại'))}</span></div>
                <div class="dna-row"><span class="dna-label">📍 Cơ chế tọa độ:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{loc_type_str}</span></div>
                <div class="dna-row"><span class="dna-label">📐 Tỉ lệ thực tế:</span><span class="dna-text" style="color:#d97706; font-weight:600;">{dim_txt_display}</span></div>
                <div class="dna-row"><span class="dna-label" style="color:#15803d;">📣 Kêu gọi tương tác (CTA):</span><span class="dna-text" style="color:#15803d; font-weight:700;">Thảo luận, chia sẻ mẹo hay & Follow kênh đón xem tập sau</span></div>
            </div>
            """)
        else:
            orig_p_display = ca.get('original_price_spoken', '')
            sale_p_display = ca.get('sale_price_spoken', '')
            exact_orig_raw = str(ca.get('exact_original_price_ocr', ''))
            exact_sale_raw = str(ca.get('exact_sale_price_ocr', ''))
            
            soft_orig = ca.get('rounded_soft_original_spoken') or convert_to_soft_price_range(orig_p_display, is_orig=True, exact_raw_str=exact_orig_raw)
            soft_sale = ca.get('rounded_soft_sale_spoken') or convert_to_soft_price_range(sale_p_display, is_orig=False, exact_raw_str=exact_sale_raw)
            
            c4_html = clean_html(f"""
            <div class="dna-card">
                <div class="dna-card-title">⚙ 4. Chuẩn Bối Cảnh, Động Lực Học & Mức Giá</div>
                <div class="dna-row"><span class="dna-label">🏙 Chuẩn bối cảnh:</span><span class="dna-text" style="color:#2563eb; font-weight:700;">{clean_analysis_text(ca.get('setting_archetype', 'Góc làm việc / Phòng riêng hiện đại'))}</span></div>
                <div class="dna-row"><span class="dna-label">📍 Cơ chế tọa độ:</span><span class="dna-text" style="color:#0284c7; font-weight:600;">{loc_type_str}</span></div>
                <div class="dna-row"><span class="dna-label">📐 Tỉ lệ thực tế:</span><span class="dna-text" style="color:#0284c7; font-weight:700;">{dim_txt_display}</span></div>
                <div class="dna-row"><span class="dna-label">💰 Mức giá (OCR):</span><span class="dna-text">{format_ocr_prices(ca)}</span></div>
                <div class="dna-row"><span class="dna-label" style="color:#dc2626;">🎯 Mức giá đồng bộ (Nay giảm):</span><span class="dna-text" style="color:#dc2626; font-weight:700;">Bình thường khoảng {soft_orig}, nay giảm khoảng {soft_sale}</span></div>
            </div>
            """)
        st.markdown(c4_html, unsafe_allow_html=True)

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
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting')}*\n\n**😊 Vi biểu cảm & Cử chỉ:** *{scn.get('expression_en', 'Tự nhiên, rạng rỡ')}*\n\n**🎵 Hiệu ứng âm thanh (SFX & Foley thuần - Đã gộp cảm biến thời tiết - Không nhạc nền):** *{scn.get('sfx', 'Âm thanh thực tế sống động')}*\n\n**🎙 Đạo diễn KOC:** *{scn.get('director')}*\n\n**💬 Thoại nhân vật nói trực tiếp on-camera từ 0.00s (100% Giọng Hà Nội chuẩn, dùng 'nghìn', số 4 đọc 'bốn'):** <div class='voiceover-text'>{vo_text}</div>", unsafe_allow_html=True)
            
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                st.markdown("**🖼 Prompt Ảnh (Midjourney / Flux - Khóa toàn diện Bối cảnh, Thời tiết & Trang phục):**")
                st.code(img_p := scn.get('img_p', ''), language="text")
                safe_copy_button(img_p, f"📋 Sao Chép Prompt Ảnh Cảnh {idx}")
                st.caption("💡 *Mẹo giữ nhân vật & đồ đồng nhất:* Sau khi tạo ảnh Cảnh 1 ưng ý, copy link ảnh và gắn vào đuôi prompt Cảnh 2, 3, 4: `--cref [URL_ẢNH_CẢNH_1] --cw 100`")
                
            with c_p2:
                st.markdown("**🎥 Prompt Video (Veo 3 Pro 5-Layer Architecture / Kling AI - Khóa Vật Lý 3D & Nhịp Lip-Sync):**")
                st.code(vid_p := scn.get('vid_p', ''), language="text")
                safe_copy_button(vid_p, f"📋 Sao Chép Prompt Video Cảnh {idx}")
            
            with st.expander(f"🛡 Negative Prompt Chuyên Biệt Cảnh {idx}", expanded=False):
                neg_val = scn.get('vid_neg', 'opposite gender, celebrity likeness, extra fingers, text, watermark')
                st.code(neg_val, language="text")
                safe_copy_button(neg_val, f"📋 Sao Chép Negative Prompt Cảnh {idx}", custom_color="#475569")
                
            st.markdown("---")

    if comp_sc:
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

    if pend_sc:
        st.markdown("### ⏳ **2. Kịch Bản Chờ Dựng**")
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
            with st.spinner(f"⏳ Đang dựng kịch bản #{target_id_to_run} với trang phục đồng nhất, cảm biến thời tiết & Veo 3 5-Layer..."):
                create_scene_details(target_id_to_run, st.session_state.last_mode, "Điện Ảnh Chân Thực")
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
    # KHU VỰC GỌI THÊM 5 KỊCH BẢN MỚI (ĐỒNG BỘ GIAO DIỆN GỌN GÀNG)
    # ==========================================================================
    st.divider()
    st.markdown("### ➕ **Gọi Thêm 5 Kịch Bản Mới**")
    
    cg1, cg2, cg3 = st.columns([1.4, 1.6, 1.0])
    c_unified_more = cg1.selectbox(
        "🧭 Chiến lược & Hình thức Video mới:",
        UNIFIED_STRATEGY_FORMAT_OPTS,
        index=0,
        key=f"more_unified_{st.session_state.reset_key}"
    )
    e_role = cg2.text_input(
        "👤 Vai trò NV mới (Để trống = AI tự phân tích):",
        value="",
        placeholder="Để trống = Giữ nguyên hoặc AI tự phân tích...",
        key=f"er_0_{st.session_state.reset_key}"
    )
    e_file = cg3.file_uploader(
        "📸 Ảnh mẫu NV mới (Tùy chọn):",
        type=["jpg", "png"],
        key=f"ef_0_{st.session_state.reset_key}"
    )

    extra_custom_note = st.text_area(
        "✍ Ghi chú AI cho kịch bản thêm (Ưu tiên cao nhất):", 
        placeholder="Ví dụ: Kịch bản mở đầu bằng câu chuyện đời thực, nhịp nói dồn dập, chuyển cảnh mượt mà...", 
        key=f"extra_custom_note_{st.session_state.reset_key}"
    )

    if st.button("🚀 Gọi Thêm 5 Kịch Bản Mới", type="primary", use_container_width=True, disabled=is_system_busy):
        can_run, msg = check_usage_limit(st.session_state.current_email)
        if can_run:
            with st.spinner("⏳ Đang sáng tạo thêm 5 kịch bản theo đúng chiến lược và ghi chú AI ưu tiên..."):
                p_chars = [{"id": 1, "role": e_role.strip()}] if e_role.strip() else st.session_state.character_profiles
                new_sc = generate_more_scripts(c_unified_more, p_chars, extra_custom_note)
                st.session_state.expanded_scripts.extend(new_sc)
                st.toast("✅ Đã sinh thêm 5 kịch bản mới theo đúng yêu cầu!"); time.sleep(0.4); st.rerun()
        else: st.error(msg)
