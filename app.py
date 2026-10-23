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
# 1. CẤU HÌNH GIAO DIỆN & HẰNG SỐ
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

@st.cache_resource(show_spinner=False)
def init_supabase():
    try:
        url = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL", ""))
        key = st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY", ""))
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None

@st.cache_resource(show_spinner=False)
def init_gemini_client():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
        if api_key:
            return genai.Client(api_key=api_key)
    except Exception:
        pass
    return None

supabase = init_supabase()
client = init_gemini_client()

# ==============================================================================
# 2. CÁC HÀM TIỆN ÍCH & XỬ LÝ DỮ LIỆU
# ==============================================================================
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

def extract_bold_product_title(ca_data: dict, fallback_topic: str = "") -> str:
    raw = ""
    if isinstance(ca_data, dict):
        raw = str(ca_data.get("what_and_unique", "")).strip()
    if not raw and fallback_topic:
        raw = fallback_topic.strip()
    if not raw: return f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
    pattern = r'^(?:SẢN PHẨM LÀ GÌ\s*&?\s*(?:CÓ GÌ ĐẶC BIỆT)?|CHỦ ĐỀ|SẢN PHẨM)\s*:\s*'
    clean = re.sub(pattern, '', raw, flags=re.IGNORECASE).strip()
    if ":" in clean: prod_name = clean.split(":", 1)[0].strip()
    elif " - " in clean: prod_name = clean.split(" - ", 1)[0].strip()
    else: prod_name = clean
    prod_name = re.sub(r'[\[\]\*\"\'`]', '', prod_name).strip()
    if len(prod_name) > 55: prod_name = prod_name[:52].strip() + "..."
    return f"{prod_name} ({datetime.now().strftime('%d/%m')})" if prod_name else f"Chiến dịch ({datetime.now().strftime('%d/%m')})"

def detect_strict_rigid_appliance(text_to_check: str) -> bool:
    if not text_to_check: return False
    t = text_to_check.lower()
    appliance_keywords = [
        "giỏ", "rổ", "kệ", "hộp", "thùng", "tủ", "móc", "chậu", "cây lau", "bàn chải", 
        "máy giặt", "túi đựng", "khay", "nồi", "chảo", "dao", "thớt", "máy xay", "bếp", 
        "bình", "cốc", "ly", "ghế", "bàn", "đèn", "quạt", "máy sấy", "bàn là", "bàn ủi",
        "basket", "rack", "organizer", "bin", "box", "hamper", "shelf", "holder", "pan", "pot", "tool"
    ]
    return any(k in t for k in appliance_keywords)

def detect_single_tube_skirt(text_to_check: str) -> bool:
    if not text_to_check: return False
    t = text_to_check.lower()
    return any(k in t for k in ["1 ống", "một ống", "quần váy", "váy 1 ống", "dạng váy", "quần giả váy", "single tube", "skirt-pants", "culottes skirt", "unsplit skirt"])

def enforce_single_tube_skirt_syntax(text_en: str) -> str:
    if not text_en: return ""
    cleaned = text_en
    patterns = [
        r'\bwide-?leg\s+(?:silk\s+)?(?:skirt-?pants|pants|trousers)\b',
        r'\bskirt-?pants\b', r'\bsilk\s+(?:pants|trousers)\b', r'\bflowing\s+(?:pants|trousers)\b',
        r'\bloose\s+(?:pants|trousers)\b', r'\bpants\b', r'\btrousers\b'
    ]
    for pat in patterns:
        cleaned = re.sub(pat, 'full-length A-line maxi skirt (single unified unsplit skirt tube, zero leg division)', cleaned, flags=re.IGNORECASE)
    return cleaned

def translate_and_lock_color_en(color_vi: str, ai_color_en: str = "") -> str:
    c = f"{color_vi} {ai_color_en}".lower().strip()
    if any(k in c for k in ["trắng", "white", "kem", "sữa"]): return "solid pure matte-white (monochrome white, zero grey)"
    elif any(k in c for k in ["đen", "black"]): return "solid matte-black"
    elif any(k in c for k in ["xám", "ghi", "grey", "gray"]): return "solid uniform light-grey"
    elif any(k in c for k in ["hồng", "pink", "pastel"]): return "solid pastel-pink"
    elif any(k in c for k in ["đỏ mận", "đỏ đô", "rượu vang", "burgundy", "maroon", "wine"]): return "solid deep burgundy-red"
    elif any(k in c for k in ["đỏ", "red"]): return "solid vibrant-red"
    elif any(k in c for k in ["xanh dương", "xanh biển", "xanh lam", "blue", "navy"]): return "solid classic-blue"
    elif any(k in c for k in ["xanh lá", "xanh rêu", "xanh bơ", "green", "mint", "sage"]): return "solid sage-green"
    elif any(k in c for k in ["vàng", "yellow", "gold"]): return "solid warm-yellow"
    elif any(k in c for k in ["nâu", "brown", "mocha", "cafe"]): return "solid mocha-brown"
    elif any(k in c for k in ["be", "beige", "nude"]): return "solid cream-beige"
    elif any(k in c for k in ["tím", "purple", "lavender", "lilac"]): return "solid lavender-purple"
    if ai_color_en and len(ai_color_en.strip()) > 2: return f"solid uniform {ai_color_en.strip()}"
    return "solid uniform reference-color"

def sanitize_destructive_motion_verbs(action_text: str, is_fashion: bool = False) -> str:
    if not action_text: return ""
    cleaned = action_text
    if not is_fashion:
        destructive_patterns = [
            (r'\bunfolding\b', 'holding steadily'), (r'\bfolding\b', 'holding securely'),
            (r'\bcollapsing\b', 'presenting up close'), (r'\bflexing\b', 'pressing fingers gently on'),
            (r'\bbending\b', 'tilting slightly'), (r'\btwisting\b', 'turning 15 degrees'),
            (r'\btransforming\b', 'showcasing'), (r'\bdeforming\b', 'presenting'),
            (r'\bstretching\b', 'tracing fingers along'), (r'\bsqueezing\b', 'gripping firmly'),
            (r'\bopening\s+and\s+closing\b', 'displaying clearly')
        ]
        for pat, rep in destructive_patterns:
            cleaned = re.sub(pat, rep, cleaned, flags=re.IGNORECASE)
    return cleaned

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
    return re.sub(r'\s+', ' ', text).strip() + " đồng"

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

def get_demographics_description(char_profiles, ai_persona_en="", ai_body_and_hair_en=""):
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
    combined = f"{strategy_str} {title_str}".lower()
    return any(k in combined for k in ["nỗi đau", "pas", "đời sống", "lifestyle", "pov", "tình huống", "hài hước", "đời thường"])

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
    fashion_keywords = ["áo", "quần", "váy", "đầm", "hoodie", "sweater", "blazer", "jacket", "shirt", "pants", "jeans", "shorts", "t-shirt", "set đồ", "bộ đồ", "cardigan", "polo", "chân váy", "pijama"]
    return any(k in t for k in fashion_keywords)

def detect_footwear_or_accessory(text_to_check: str) -> bool:
    if not text_to_check: return False
    t = text_to_check.lower()
    if any(k in t for k in ["giỏ", "rổ", "thùng", "hộp", "kệ", "basket", "hamper", "organizer", "bin"]): return False
    return any(k in t for k in ["giày", "dép", "sneaker", "boot", "sandal", "heel", "túi xách", "ví", "balo", "mũ", "nón", "kính", "thắt lưng", "đồng hồ", "trang sức", "dây chuyền", "nhẫn", "khuyên tai", "shoe", "handbag", "backpack", "wallet", "watch", "glasses"])

COMPACT_CORE_RULES = """
🛑 QUY TẮC CỐT LÕI (BẮT BUỘC TUÂN THỦ 100%):
1. CẦU NỐI 3 NHÁNH (CẢNH 1 -> CẢNH 2, CẤM LẶP TỪ CỦA CẢNH 1):
   - Nhánh 1 (Giá rẻ/Săn sale) -> Cảnh 2: "Cận cảnh minh chứng chất lượng..." (CẤM dùng từ "Bí quyết").
   - Nhánh 2 (Nỗi đau PAS) -> Cảnh 2: "Cứu tinh giải pháp cho vấn đề...".
   - Nhánh 3 (Mẹo hay) -> Cảnh 2: "Bí quyết nằm ở chỗ...".
2. PRODUCT-CENTRIC FOCUS & STRICT REFERENCE TRACKING:
   - Nếu là Thời trang: Lấy phom dáng cơ thể, đường rũ vải làm trung tâm. Nếu ghi chú "quần váy / váy 1 ống" -> BẮT BUỘC dịch "full-length A-line maxi skirt (single unsplit skirt tube, zero leg division)", CẤM "pants/trousers".
   - Nếu là Đồ gia dụng / Thiết bị (Strict Rigid Appliance): BẮT BUỘC KHOÁ CHẶT THEO ẢNH THAM CHIẾU (100% exact shape, color, surface details identical to reference image). Zero morphing, zero hallucinated parts! Zoom thẳng vào SP ở tiền cảnh (60% khung hình).
3. VĂN NÓI HÀ NỘI THUẦN VIỆT 100%:
   - 'voiceover': 100% Tiếng Việt, giọng Hà Nội ('mềm rũ', 'bốn', 'nghìn', 'một trăm'). TUYỆT ĐỐI CẤM chèn từ tiếng Anh vào thoại. Cấm 'thuật toán', 'trợ giá'.
   - Cảnh 4: Neo giá Flash Sale hoặc Soft CTA nhắc lại nỗi đau + bấm giỏ hàng.
"""

def get_product_centric_camera_shot(scene_idx: int, is_fashion: bool, is_footwear_acc: bool, is_pas_scene1: bool, clean_prod_en: str, is_appliance: bool) -> str:
    if is_pas_scene1 and not is_fashion: return "Vertical 9:16 eye-level medium shot"
    if is_fashion:
        if scene_idx == 0: return "Vertical 9:16 eye-level three-quarter full-body shot showcasing the outfit"
        elif scene_idx == 1: return "Vertical 9:16 smooth camera dolly-in to medium close-up focusing sharply on garment neckline, waist cut, and fabric weave"
        elif scene_idx == 2: return "Vertical 9:16 dynamic close-up tracking shot following the flowing garment drape and silhouette in motion"
        else: return "Vertical 9:16 warm eye-level medium shot"
    elif is_appliance:
        if scene_idx == 0: return f"Vertical 9:16 product-focused medium shot, exact reference-matching {clean_prod_en} held steadily in foreground center"
        elif scene_idx == 1: return f"Vertical 9:16 macro close-up shot locked strictly on {clean_prod_en} maintaining 100% identical proportions and structure to reference image, tack-sharp focus"
        elif scene_idx == 2: return f"Vertical 9:16 tight close-up action shot centered directly on {clean_prod_en} during clean subtle interaction, zero extra details added"
        else: return f"Vertical 9:16 balanced medium shot with exact reference-matching {clean_prod_en} displayed clearly"
    else:
        if scene_idx == 0: return f"Vertical 9:16 product-focused medium shot, {clean_prod_en} held prominently in foreground center toward the lens"
        elif scene_idx == 1: return f"Vertical 9:16 direct camera zoom-in (dolly-in) macro close-up locked onto {clean_prod_en} filling 60% of the center frame, tack-sharp focus on product surface and rim"
        elif scene_idx == 2: return f"Vertical 9:16 tight close-up action shot centered directly on {clean_prod_en} in real-time use"
        else: return f"Vertical 9:16 balanced medium shot with {clean_prod_en} displayed clearly in foreground center"

def get_universal_physics_rules(product_name: str, vo_text: str = "", is_fashion: bool = False, is_appliance: bool = False) -> str:
    if is_fashion: return "Natural fabric drape in motion; subject steps smoothly, turns 45 degrees, and touches fabric softly (worn on body, zero duplicate item in hands)."
    elif is_appliance: return "STRICT REFERENCE TRACKING: The appliance maintains 100% exact shape, color, proportions, and surface details identical to the reference image. Zero morphing, zero hallucinated parts, zero extra details. The product stays completely rigid while presenter's hands perform a clean, subtle interaction."
    else: return "CAMERA FOCUS LOCKED ON PRODUCT IN FOREGROUND: 100% rigid non-deforming 3D geometry from 0.0s to end (zero morphing); hands hold product in center frame, tilt 15 degrees, and trace surface."

def get_action_templates_by_industry(clean_prod_en: str, check_str: str, is_fashion_wearable: bool, is_appliance: bool):
    if is_fashion_wearable: return ("stepping forward confidently and gesturing expressively while speaking", "turning 45 degrees gracefully while running one hand smoothly along the waist and neckline fabric", "swaying slightly so the hem flows naturally and touching the fabric to show softness", "posing confidently with a warm open-palm gesture")
    elif is_appliance: return (f"holding the exact reference-matching {clean_prod_en} steadily at chest level", f"presenting the exact reference-matching {clean_prod_en} up close without any added details or shape changes", f"demonstrating {clean_prod_en} with clean, precise hand interaction while keeping 100% fidelity to reference image", f"holding {clean_prod_en} steadily with a warm open-palm gesture")
    else: return (f"holding the rigid {clean_prod_en} prominently in foreground center toward the lens", f"positioning {clean_prod_en} right in front of the close-up lens, tilting it 15 degrees and tracing fingers along its solid surface", f"demonstrating {clean_prod_en} in foreground center focus with steady hand movements while preserving 100% rigid geometry", f"holding {clean_prod_en} clearly in foreground center with a warm open-palm gesture")

def build_multi_industry_stylist_rules(product_en: str, hero_color: str, setting_vi: str, gender: str, intimate_type: str, is_fashion: bool, raw_vi_info: str = "") -> str:
    s_lower = f"{product_en} {setting_vi} {raw_vi_info}".lower()
    h_lower = hero_color.lower()
    is_home = any(k in s_lower for k in ["pijama", "đồ ngủ", "mặc nhà", "phòng ngủ", "nhà bếp", "phòng tắm", "máy giặt", "giặt"])
    is_evening = any(k in s_lower for k in ["váy", "đầm", "dự tiệc", "đi tiệc", "công sở", "thanh lịch", "áo dài", "dress", "gown"])
    is_single_skirt = detect_single_tube_skirt(s_lower)
    
    if is_home and not is_fashion: footwear = "clean minimalist pastel indoor slippers"
    elif is_fashion and is_evening and gender == "female": footwear = "elegant pointed-toe high heels or strappy heeled sandals"
    else: footwear = "clean minimalist white sneakers or smart-casual loafers"

    contrast = "Áo KOC màu Beige/Mocha/Xanh pastel tương phản làm nổi bật SP màu sáng" if any(k in h_lower for k in ["trắng", "white", "kem"]) else "Trang phục tông sáng/trung tính thanh lịch tôn SP"
    jewelry = "dainty necklace, pearl stud earrings, and thin bracelet/watch" if gender == "female" else "minimalist wristwatch"
    skirt_rule = " | ĐẶC BIỆT: Phần dưới là VÁY 1 ỐNG RỘNG (full-length A-line maxi skirt, single unified unsplit skirt tube, zero leg division - CẤM viết từ pants/trousers)!" if is_single_skirt else ""
    return f"STYLIST LOCK: {contrast} | Giày: {footwear} | Phụ kiện cố định 4 cảnh: {jewelry}{skirt_rule}."

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
    r'\bsexy\b': 'elegant modern',
    r'\báo\s*lót\b': 'seamless comfort top garment',
    r'\bquần\s*lót\b': 'seamless base-layer garment',
    r'\bđồ\s*lót\b': 'comfort apparel piece',
    r'\bnội\s*y\b': 'comfort loungewear piece'
}

def sanitize_third_party_ip(text: str) -> str:
    if not text: return ""
    cleaned = text
    for p in [r'\btiktok\s*(?:shop)?\b', r'\bshopee\b', r'\blazada\b', r'\bfacebook\b', r'\binstagram\b', r'\byoutube\b']:
        cleaned = re.sub(p, 'online store', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\blụa\s*titan\b', 'lustrous satin silk', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\btitan\s*silk\b', 'lustrous satin silk', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\btitan\b', 'lustrous satin', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:emoon|disney|marvel|spider-?man|spiderman|nike|adidas|gucci|chanel|dior|lv|louis\s+vuitton|zara|uniqlo|apple|samsung|xiaomi|dyson|philips|vaseline|lego|barbie)\b', 'premium everyday', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:celebrity|celebrities|public\s+figure|famous\s+person|famous\s+model|supermodel|star|idol|influencer|koc|kol|deepfake|real\s+person|real\s+human|authentic\s+person)\b', 'fictional everyday character', cleaned, flags=re.IGNORECASE)
    for pattern, safe_term in INTIMATE_SAFE_ENGLISH_LEXICON.items():
        cleaned = re.sub(pattern, safe_term, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bwearing\s+wearing\b', 'wearing', cleaned, flags=re.IGNORECASE)
    return re.sub(r'\.\.+', '.', cleaned)

POLICY_REPLACEMENTS = {
    r'\ban\s*toàn\s*tuyệt\s*đối\b': 'cực kỳ an toàn', r'\byên\s*tâm\s*tuyệt\s*đối\b': 'cực kỳ yên tâm',
    r'\btuyệt\s*đối\s*an\s*toàn\b': 'cực kỳ an toàn', r'\btuyệt\s*đối\s*yên\s*tâm\b': 'cực kỳ yên tâm',
    r'\bhoàn\s*toàn\s*yên\s*tâm\b': 'cực kỳ yên tâm', r'\bhoàn\s*toàn\s*an\s*toàn\b': 'rất an toàn',
    r'\b100\s*%\s*an\s*toàn\b': 'rất an toàn', r'\ban\s*toàn\s*100\s*%\b': 'cực kỳ an toàn',
    r'(\b[a-zà-ỹ]+)\s+tuyệt\s*đối\b': r'cực kỳ \1', r'\btuyệt\s*đối\b': 'rất', r'\bhoàn\s*toàn\b': 'thực sự',
    r'\b100\s*%\b': 'rất nhiều', r'\bchắc\s*chắn\b': 'rất có thể', r'\bcam\s*kết\b': 'an tâm',
    r'\bdứt\s*điểm\b': 'cải thiện', r'\bđặc\s*trị\b': 'hỗ trợ', r'\bkhỏi\s*hẳn\b': 'đỡ hẳn',
    r'\bvĩnh\s*viễn\b': 'lâu dài', r'\bchuẩn\s*đét\b': 'vừa vặn', r'\bchữa\s*khỏi\b': 'hỗ trợ',
    r'\bthần\s*dược\b': 'bí quyết', r'\btốt\s*nhất\b': 'rất tốt', r'\bsố\s*1\b': 'hàng đầu',
    r'\btrắng\s*cấp\s*tốc\b': 'sáng khỏe tự nhiên', r'\bgiảm\s*béo\s*cấp\s*tốc\b': 'vóc dáng thon gọn',
    r'\bxóa\s*sạch\s*nám\b': 'mờ thâm sạm', r'\bthuốc\s*trị\b': 'sản phẩm hỗ trợ',
    r'\bđiều\s*trị\b': 'hỗ trợ cải thiện', r'\btriệt\s*để\b': 'hiệu quả', r'\btrợ\s*giá\b': 'giảm giá sâu có hạn',
    r'\bphiên\s*live\b': 'đợt ưu đãi này', r'\btrên\s*live\b': 'đợt này', r'\blivestream\b': 'chương trình ưu đãi',
    r'\bkhe\s*ngực\b': 'phom dáng', r'\bnâng\s*ngực\b': 'nâng đỡ phom dáng', r'\bchống\s*xệ\s*ngực\b': 'giữ phom săn chắc',
    r'\bxệ\s*ngực\b': 'mất phom', r'\bvùng\s*kín\b': 'vùng nhạy cảm', r'\bnhũ\s*hoa\b': 'điểm nhạy cảm',
    r'\blộ\s*nhũ\s*hoa\b': 'lộ viền kém duyên', r'\bgợi\s*cảm\b': 'tinh tế cuốn hút',
    r'\bsexy\b': 'thanh lịch tôn dáng', r'\bquyến\s*rũ\b': 'nữ tính', r'\bhở\s*bạo\b': 'thoải mái'
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
        (r'\blụa\s+premium\s+everyday\b', 'lụa cao cấp'), (r'\bpremium\s+everyday\b', 'cao cấp'),
        (r'\bmềm\s*rủ\b', 'mềm rũ'), (r'\bđộ\s*rủ\b', 'độ rũ'),
        (r'\báp\s*mã\b', 'nay giảm'), (r'\báp\s*voucher\b', 'nay giảm'),
        (r'\b1\s*trăm\s*(?:tư|tứ|bốn)?\s*mươi\b', 'một trăm bốn mươi'), (r'\b1\s*trăm\s*(?:tư|tứ)\b', 'một trăm bốn mươi'),
        (r'\bmột\s*trăm\s*(?:tư|tứ)\s*mươi\b', 'một trăm bốn mươi'), (r'\bmột\s*trăm\s*(?:tư|tứ)\b', 'một trăm bốn mươi'),
        (r'\btrăm\s*(?:tư|tứ)\s*mươi\b', 'trăm bốn mươi'), (r'\btrăm\s*(?:tư|tứ)\b', 'trăm bốn mươi'),
        (r'\b1\s*trăm\b', 'một trăm'), (r'\b1\s*nghìn\b', 'một nghìn'), (r'\b1\s*triệu\b', 'một triệu'),
        (r'\b140\s*(?:k|nghìn|ngàn)\b', 'một trăm bốn mươi nghìn'), (r'\b140\b', 'một trăm bốn mươi'),
        (r'\b14\b', 'mười bốn'), (r'\b24\b', 'hai mươi bốn'), (r'\b34\b', 'ba mươi bốn'),
        (r'\b40\b', 'bốn mươi'), (r'\b44\b', 'bốn mươi bốn'), (r'\b4\b', 'bốn'),
        (r'\bmười\s+(?:tư|tứ)\b', 'mười bốn'), (r'\bhai\s+(?:tư|tứ)\b', 'hai mươi bốn'),
        (r'\bba\s+(?:tư|tứ)\b', 'ba mươi bốn'), (r'\b(?:tư|tứ)\s+mươi\b', 'bốn mươi'),
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
    if exact_orig and exact_sale: return f"<b style='color:#475569;'>Giá gốc:</b> <span style='color:#64748b; text-decoration:line-through; font-weight:700; font-size:14px;'>{clean_analysis_text(exact_orig)}</span> &nbsp;|&nbsp; <b style='color:#dc2626;'>Giá giảm:</b> <span style='color:#dc2626; font-weight:800; font-size:15.5px;'>{clean_analysis_text(exact_sale)}</span>"
    elif det and ("-" in det or "|" in det or "đ" in det.lower()): return f"<span style='color:#dc2626; font-weight:800; font-size:14.5px;'>{clean_analysis_text(det)}</span>"
    orig = ca_data.get('original_price_spoken', '')
    sale = ca_data.get('sale_price_spoken', '')
    if orig and sale: return f"<b style='color:#475569;'>Giá gốc:</b> <span style='color:#64748b; text-decoration:line-through; font-weight:700;'>{clean_analysis_text(orig)}</span> &nbsp;|&nbsp; <b style='color:#dc2626;'>Giá giảm:</b> <span style='color:#dc2626; font-weight:800; font-size:15px;'>{clean_analysis_text(sale)}</span>"
    return "<span style='color:#dc2626; font-weight:700;'>Chưa xác định</span>"

def extract_environmental_lighting_and_weather(vo_text: str, setting_text: str = ""):
    combined_text = f"{vo_text} {setting_text}".lower()
    outdoor_keywords = ["ngoài trời", "sân vườn", "đường phố", "công viên", "vỉa hè", "ban công", "sân thượng", "dã ngoại", "bãi biển", "outdoor", "street", "garden", "park", "balcony"]
    is_indoor = not any(k in combined_text for k in outdoor_keywords)
    if any(k in combined_text for k in ["mưa", "ẩm ướt", "nồm"]): return ("rain droplets on window, soft overcast indoor lighting" if is_indoor else "light rain, wet ground, overcast sky"), "soft rain Foley"
    elif any(k in combined_text for k in ["nắng", "trưa hè"]): return ("warm sunbeams through window" if is_indoor else "sunny daylight, golden sunbeams"), "summer breeze ambiance"
    elif any(k in combined_text for k in ["sáng sớm", "buổi sáng", "bình minh"]): return "fresh morning sunlight", "peaceful morning room tone"
    elif any(k in combined_text for k in ["hoàng hôn", "chiều tà", "buổi chiều"]): return "warm amber sunset glow", "calm evening room tone"
    elif any(k in combined_text for k in ["ban đêm", "tối muộn", "buổi tối", "đi ngủ"]): return "cozy warm tungsten lamp lighting", "quiet nighttime room tone"
    return ("clean natural daylight with soft warm fill light" if is_indoor else "bright commercial daylight"), ""

def sanitize_veo3_prompt(prompt_text: str) -> str:
    if not prompt_text: return ""
    p = re.sub(r'\bgesturing\s+(?:warmly\s+)?(?:toward\s+)?corner\b', 'sharing recommendations with an open-palm gesture', prompt_text, flags=re.IGNORECASE)
    p = re.sub(r'\bpointing\s+(?:downward\s+)?(?:to\s+)?(?:corner|cart)\b', 'speaking with welcoming open hands', p, flags=re.IGNORECASE)
    return sanitize_third_party_ip(p)

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
    except Exception as e: return False, str(e)

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
    except Exception as e: return False, str(e)

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
    return f"""
    ĐẠO DIỄN TIKTOK PRO | MỤC TIÊU: {goal} | CHIẾN LƯỢC: {presentation_format or angle}
    {f"🛑 CHỈ THỊ ƯU TIÊN SỐ 1 TỪ NGƯỜI DÙNG: {custom_note}" if custom_note else ""}
    {COMPACT_CORE_RULES}
    - 5 kịch bản = 5 bối cảnh đời thực khác nhau khớp sản phẩm & sự kiện.
    - Diễn viên: {char_rules}
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction, num_chars, character_profiles, custom_note="", presentation_format="", self_pronoun="em", audience_pronoun="các chị em", setting_archetype="", is_fixed_location=True, is_pas_story=False):
    is_viral = ("Viral" in mode)
    pas_flow = "PAS Flow: Cảnh 1 tại nhà nêu nỗi đau (KHÔNG có SP) -> Cảnh 2,3,4 có SP làm TRỌNG TÂM TIỀN CẢNH giải quyết vấn đề." if is_pas_story else "Direct Flow: SP làm TRỌNG TÂM TIỀN CẢNH xuyên suốt 4 cảnh, Cảnh 2 nối mượt từ Cảnh 1."
    return f"""
    ĐẠO DIỄN TIKTOK PRO | Xưng '{self_pronoun}' - Gọi '{audience_pronoun}' | {pas_flow}
    {f"🛑 CHỈ THỊ ƯU TIÊN SỐ 1 TỪ NGƯỜI DÙNG (BẮT BUỘC TUÂN THỦ TUYỆT ĐỐI): {custom_note}" if custom_note else ""}
    {COMPACT_CORE_RULES}
    - Cảnh 4: {"Kêu gọi thảo luận & follow (không bán hàng)" if is_viral else "Chốt deal chuẩn quy tắc"}.
    - 'action_en' viết ngắn gọn (dưới 22 từ), 100% tiếng Anh, đặt sản phẩm ở trung tâm tiền cảnh và giữ nguyên khung hình học cứng của sản phẩm.
    """

# ==============================================================================
# 3. KHỞI TẠO SESSION STATE CHUẨN XÁC
# (Phải nằm ngay trên cùng, trước khi bất kỳ UI sidebar nào được gọi)
# ==============================================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", None),
    ("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []),
    ("generated_details", {}), ("content_analysis", None), ("active_script_id", None),
    ("current_input_context", ""), ("current_product_data_saved", None), ("current_product_data", None),
    ("reset_key", 0), ("scroll_to_top", False), ("scroll_to_detail", False),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"),
    ("last_mode", "🛒 TikTok Shop & Bán Hàng"), ("last_style", "Điện Ảnh Chân Thực"), ("last_narrator", "On-camera"),
    ("last_presentation_format", "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng"),
    ("target_duration_instruction", ""), ("character_profiles", []), ("current_project_id", None),
    ("saved_reference_images", []), ("show_all_projects", False), ("show_all_admin_accounts", False),
    ("current_processing_id", None), ("current_cloning_id", None), ("is_analyzed", False),
    ("last_autosave_time", "")
]:
    if key not in st.session_state:
        st.session_state[key] = default_val

if st.session_state.licensed_accounts is None:
    st.session_state.licensed_accounts = load_licensed_accounts()

is_system_busy = (
    st.session_state.get("current_processing_id") is not None or 
    st.session_state.get("current_cloning_id") is not None
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
# HÀM LOGIC CHÍNH: TẠO CHI TIẾT & NHÂN BẢN KỊCH BẢN
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
    fixed_hook = clean_and_normalize_voiceover(outline.get('hook', ''))
    fixed_setting_base = outline.get('setting', 'Không gian thực tế phù hợp')
    user_custom_note = outline.get("custom_note") or st.session_state.get("current_input_context", "").strip()
    presentation_format = outline.get("presentation_format") or st.session_state.get("last_presentation_format", "🌟 AI Tự Động Phân Tích, Đề Xuất & Mix Đa Dạng")
    is_pas_story = is_pas_storytelling_strategy(presentation_format, fixed_title)
    dna = st.session_state.get("content_analysis") or {}
    
    ai_koc_data = dna.get("koc_demographic_analysis", {})
    ai_persona_en = ai_koc_data.get("persona_en", "") if isinstance(ai_koc_data, dict) else ""
    ai_body_and_hair_en = ai_koc_data.get("body_and_hair_en", "") if isinstance(ai_koc_data, dict) else ""
    detected_gender, detected_demographic_en = get_demographics_description(char_profiles, ai_persona_en, ai_body_and_hair_en)

    raw_orig_price, raw_sale_price = dna.get("original_price_spoken", ""), dna.get("sale_price_spoken", "")
    exact_orig_raw, exact_sale_raw = str(dna.get("exact_original_price_ocr", "")), str(dna.get("exact_sale_price_ocr", ""))
    
    if not raw_orig_price or not raw_sale_price:
        detected_p = str(dna.get("detected_prices", ""))
        num_matches = [int(n.replace('.', '').replace(',', '')) for n in re.findall(r'\b\d{1,3}(?:[.,]\d{3})+\b', detected_p)]
        if len(num_matches) >= 2:
            num_matches.sort()
            raw_orig_price = number_to_vietnamese_words(num_matches[-1]).replace(" đồng", "")
            raw_sale_price = number_to_vietnamese_words(num_matches[0]).replace(" đồng", "")
        elif len(num_matches) == 1:
            raw_orig_price = number_to_vietnamese_words(int(num_matches[0] * 1.25)).replace(" đồng", "")
            raw_sale_price = number_to_vietnamese_words(num_matches[0]).replace(" đồng", "")
        else:
            raw_orig_price, raw_sale_price = "ba trăm năm mươi nghìn", "hai trăm chín mươi nghìn"

    orig_price_spoken = clean_and_normalize_voiceover(raw_orig_price)
    sale_price_spoken = clean_and_normalize_voiceover(raw_sale_price)
    soft_orig_price = dna.get("rounded_soft_original_spoken") or convert_to_soft_price_range(orig_price_spoken, is_orig=True, exact_raw_str=exact_orig_raw)
    soft_sale_price = dna.get("rounded_soft_sale_spoken") or convert_to_soft_price_range(sale_price_spoken, is_orig=False, exact_raw_str=exact_sale_raw)

    self_pronoun = dna.get("self_pronoun") or "em"
    audience_pronoun = dna.get("audience_pronoun") or ("các chị em" if not is_viral else "mọi người")
    hero_color_str = dna.get("hero_sku_color", "").strip()
    ai_hero_color_en = dna.get("hero_sku_color_en", "").strip()
    locked_color_en = translate_and_lock_color_en(hero_color_str, ai_hero_color_en)

    raw_prod_name = str(dna.get("what_and_unique", "sản phẩm")).strip()
    if ":" in raw_prod_name: raw_prod_name = raw_prod_name.split(":", 1)[0].strip()

    ai_product_visual_en = str(dna.get("product_visual_en", "")).strip()
    dimensions_str = str(dna.get("product_dimensions", "")).strip()

    check_str = f"{raw_prod_name} {fixed_title} {fixed_hook} {user_custom_note} {dna.get('what_and_unique', '')}"
    intimate_type = detect_intimate_apparel(check_str)
    is_footwear_accessory = detect_footwear_or_accessory(check_str)
    is_fashion_wearable = detect_wearable_fashion(check_str) and intimate_type == "normal" and not is_footwear_accessory
    is_single_skirt_mode = detect_single_tube_skirt(check_str)
    is_strict_appliance = detect_strict_rigid_appliance(check_str) and not is_fashion_wearable
    is_flashsale_script = any(k in f"{fixed_title} {fixed_hook} {presentation_format}".lower() for k in ["flash sale", "săn deal", "deal hời", "giảm sốc", "ưu đãi sốc"])
    
    base_prod_en = f"{locked_color_en} seamless comfort fabric garment" if intimate_type == "underwear_bra" else (ai_product_visual_en if ai_product_visual_en else f"{locked_color_en} {raw_prod_name}")
    clean_prod_en = sanitize_third_party_ip(base_prod_en)
    
    if is_single_skirt_mode: clean_prod_en = enforce_single_tube_skirt_syntax(clean_prod_en)
    elif not is_fashion_wearable: clean_prod_en = re.sub(r'\b(?:foldable|collapsible|folding)\b', 'rigid structured', clean_prod_en, flags=re.IGNORECASE)

    dim_tag = f" ({dimensions_str})" if dimensions_str and len(dimensions_str) < 25 else ""
    if is_strict_appliance:
        locked_product_prompt_segment = f"STRICT REFERENCE APPLIANCE: exact reference-matching {clean_prod_en} in {locked_color_en}{dim_tag} maintaining 100% identical shape, proportions, and surface details. Zero hallucinated parts, zero extra details"
    else:
        locked_product_prompt_segment = f"HERO PRODUCT CENTERPIECE: {clean_prod_en} in {locked_color_en}{dim_tag} occupying foreground center focus (100% rigid non-deforming geometry, identical solid color across all scenes)" if not is_fashion_wearable else f"Garment Lock: wearing {clean_prod_en} in {locked_color_en} directly on body"

    stylist_rules_text = build_multi_industry_stylist_rules(clean_prod_en, hero_color_str, fixed_setting_base, detected_gender, intimate_type, is_fashion_wearable, raw_vi_info=check_str)
    action_scene_1, action_scene_2, action_scene_3, action_scene_4 = get_action_templates_by_industry(clean_prod_en, check_str, is_fashion_wearable, is_strict_appliance)
    
    scene_4_voiceover_guide = f"Bình thường khoảng {soft_orig_price}, nay giảm chỉ còn khoảng {soft_sale_price} thôi, nhưng giá từng thời điểm có thể khác nhau tùy đợt ưu đãi, {audience_pronoun} cứ bấm góc trái kiểm tra tài khoản mình xem nhé!" if is_flashsale_script else f"Nay hãng đang có giá ưu đãi cực sâu, {audience_pronoun} nào mà đang gặp tình trạng [nhắc lại nỗi đau cụ thể] thì rinh ngay em nó ở giỏ hàng góc trái nhé!"

    prompt_text = f"""
    TÊN SẢN PHẨM TIẾNG VIỆT (DÙNG CHO 'voiceover'): {raw_prod_name} (Màu: {hero_color_str})
    MÔ TẢ TIẾNG ANH (CHỈ DÙNG CHO 'action_en'): {clean_prod_en} ({locked_color_en})
    Nỗi đau: {dna.get('pain_points', '')} | Công năng: {dna.get('how_to_use', '')}
    Kịch bản #{target_id}: '{fixed_title}' | Hook: '{fixed_hook}' | Bối cảnh: '{fixed_setting_base}'
    GHI CHÚ BẮT BUỘC: '{user_custom_note if user_custom_note else 'none'}'
    KOC: {detected_demographic_en} | {stylist_rules_text}

    TRẢ VỀ JSON GỌN (LƯU Ý: 'voiceover' 100% Tiếng Việt thuần túy, CẤM chèn từ tiếng Anh vào lời thoại):
    {{
        "title": "{fixed_title}",
        "wardrobe_lock": {{
            "outfit_vi": "Set đồ Stylist tiếng Việt",
            "master_outfit_en": "Concise English outfit + footwear (under 18 words, DO NOT start with 'Wearing', {'MUST use full-length A-line maxi skirt (single unified unsplit skirt tube, zero leg division), NEVER use the word pants or trousers' if is_single_skirt_mode else 'coordinated style'})",
            "jewelry_and_accessories_en": "Concise English jewelry (under 10 words)"
        }},
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention",
                "setting": "Bối cảnh mở màn tiếng Việt...",
                "setting_en": "Concise English setting (under 12 words)",
                "expression_en": "{'troubled, frustrated expression' if is_pas_story else 'lively, engaging expression'}",
                "action_en": "{'expressing frustration with empty hands, zero product' if is_pas_story else action_scene_1} (under 18 words)",
                "sfx": "Foley thực tế (không nhạc)",
                "director": "Attention | {'Nêu nỗi đau mở màn' if is_pas_story else 'Đưa sản phẩm ra tiền cảnh'}",
                "voiceover": "Thoại mở màn 100% tiếng Việt tự nhiên (18-30 từ)..."
            }},
            {{
                "scene": 2, "aida_stage": "Interest",
                "setting": "Bối cảnh thực tế...",
                "setting_en": "Concise English setting (under 12 words)",
                "expression_en": "relieved, confident and enthusiastic",
                "action_en": "{action_scene_2} (under 20 words, product in foreground center focus, keep rigid shape)",
                "sfx": "Tiếng thao tác thực tế",
                "director": "Interest | Máy quay zoom thẳng vào chính giữa sản phẩm + Cầu nối 3 nhánh",
                "voiceover": "Thoại Cảnh 2 100% tiếng Việt (22-34 từ)..."
            }},
            {{
                "scene": 3, "aida_stage": "Desire",
                "setting": "Bối cảnh đồng bộ...",
                "setting_en": "Concise English setting (under 12 words)",
                "expression_en": "smiling contentedly with approving nod",
                "action_en": "{action_scene_3} (under 20 words, product in foreground center focus, keep rigid shape)",
                "sfx": "Tiếng trải nghiệm thực tế",
                "director": "Desire | Cận cảnh khóa nét vào điểm hoạt động của sản phẩm",
                "voiceover": "Thoại Cảnh 3 100% tiếng Việt (20-34 từ)..."
            }},
            {{
                "scene": 4, "aida_stage": "Action",
                "setting": "Bối cảnh kết thúc...",
                "setting_en": "Concise English setting (under 12 words)",
                "expression_en": "smiling warmly with open-palm gesture",
                "action_en": "{action_scene_4} (under 18 words)",
                "sfx": "Tiếng chuông ting nhẹ",
                "director": "Action | Giữ sản phẩm nổi bật ở tiền cảnh & Chốt deal",
                "voiceover": "{scene_4_voiceover_guide}"
            }}
        ]
    }}
    """
    sys_inst = get_sys_inst_details(current_active_mode, "Điện Ảnh Chân Thực", "On-camera", char_rules, "Max 10s", 1, char_profiles, user_custom_note, presentation_format, self_pronoun, audience_pronoun, fixed_setting_base, True, is_pas_story)
    res = call_gemini([prompt_text], sys_inst, max_tokens=4096)
    if not res: raise Exception("AI không phản hồi. Vui lòng bấm tạo lại.")
    scenes = res.get("scenes") or res.get("script") or []
    if not scenes: raise Exception("AI không tạo được danh sách phân cảnh. Vui lòng bấm tạo lại.")
    
    w_lock = res.get("wardrobe_lock", {})
    raw_outfit_en = sanitize_third_party_ip(w_lock.get("master_outfit_en") or "smart-casual coordinated outfit with clean sneakers")
    final_outfit_en = re.sub(r'^(?:consistently\s+)?wearing\s+', '', raw_outfit_en.strip(), flags=re.IGNORECASE).strip().rstrip('.')
    if is_single_skirt_mode: final_outfit_en = enforce_single_tube_skirt_syntax(final_outfit_en)
    
    raw_jewelry_en = sanitize_third_party_ip(w_lock.get("jewelry_and_accessories_en") or "minimalist stud earrings and wristwatch")
    final_jewelry_en = re.sub(r'^(?:styled\s+with\s+)', '', raw_jewelry_en.strip(), flags=re.IGNORECASE).strip().rstrip('.')
    final_outfit_vi = w_lock.get("outfit_vi") or "Trang phục Stylist đồng bộ 4 cảnh"
    locked_character_prompt_segment = f"Fictional everyday {detected_demographic_en} (synthetic AI persona, ordinary citizen), wearing {final_outfit_en}, styled with {final_jewelry_en}"

    skirt_neg_extra = "split-leg pants, bifurcated trousers, two separate pant legs, divided culottes, " if is_single_skirt_mode else ""
    appliance_neg_extra = "hallucinated parts, extra handles, extra spouts, modified shape, changing proportions, warped structure, " if is_strict_appliance else ""
    base_negative_prompt = f"{skirt_neg_extra}{appliance_neg_extra}product out of focus, blurry product, tiny product in background, camera zooming on face instead of product, morphing product, deforming geometry, melting plastic, folding/collapsing glitch, inconsistent product color, grey parts on white product, duplicate garment in hands, extra fingers, deformed hands, floating objects, nsfw, nudity, cleavage, text, watermark, subtitles, UI elements, bending down, background music, bgm, singing"
    
    total_sec = 0.0
    for idx_scn, scn in enumerate(scenes):
        if "voiceover" in scn: scn["voiceover"] = clean_and_normalize_voiceover(scn["voiceover"])
        if "director" in scn: scn["director"] = sanitize_policy_text(scn["director"])
        
        raw_speech_time = calculate_speech_duration(scn.get("voiceover", ""), is_tiktok_shop)
        actual_speech_time = round(min(10, max(4, math.ceil(raw_speech_time + (1.0 if is_tiktok_shop else 1.3)))) - 0.8, 1) if raw_speech_time >= min(10, max(4, math.ceil(raw_speech_time + (1.0 if is_tiktok_shop else 1.3)))) else raw_speech_time
        dynamic_scene_sec = min(10, max(4, math.ceil(raw_speech_time + (1.0 if is_tiktok_shop else 1.3))))
        cushion_sec = round(max(0.5, dynamic_scene_sec - actual_speech_time), 1)
        
        scn["dur"] = f"{dynamic_scene_sec}s"
        scn["actual_speech_sec"] = actual_speech_time
        total_sec += float(dynamic_scene_sec)
        
        vo_text_current = scn.get("voiceover", "")
        setting_vi_current = scn.get("setting", fixed_setting_base)
        env_lighting_en, env_sfx_en = extract_environmental_lighting_and_weather(vo_text_current, setting_vi_current)
        
        is_pas_scn1_no_prod = (idx_scn == 0 and is_pas_story and not is_fashion_wearable)
        camera_shot = get_product_centric_camera_shot(idx_scn, is_fashion_wearable, is_footwear_accessory, is_pas_scn1_no_prod, clean_prod_en, is_strict_appliance)
        
        base_sfx = re.sub(r'\b(?:music|soundtrack|melody|song|bgm)\b', 'Foley', scn.get("sfx", "Natural Foley"), flags=re.IGNORECASE)
        scn["sfx"] = f"{base_sfx}, {env_sfx_en}" if env_sfx_en else base_sfx
        
        micro_expr_en = sanitize_third_party_ip(scn.get("expression_en", "natural engaging expression")).strip().rstrip('.')
        scene_setting_en = sanitize_third_party_ip(scn.get("setting_en") or fixed_setting_base).strip().rstrip('.')
        clean_action = sanitize_destructive_motion_verbs(sanitize_third_party_ip(re.sub(r'^(?:Character\s+(?:is\s+)?|Subject\s+(?:is\s+)?)', '', scn.get("action_en") or action_scene_2, flags=re.IGNORECASE).strip()).rstrip('.'), is_fashion=is_fashion_wearable)
        if is_single_skirt_mode: clean_action = enforce_single_tube_skirt_syntax(clean_action)

        scene_physics = get_universal_physics_rules(clean_prod_en, vo_text_current, is_fashion=is_fashion_wearable, is_appliance=is_strict_appliance)

        if is_pas_scn1_no_prod:
            img_core = f"{camera_shot}, {scene_setting_en}, {env_lighting_en}. Subject: {locked_character_prompt_segment}, {micro_expr_en}, {clean_action} (empty hands, zero product)"
        elif not is_fashion_wearable and idx_scn in [1, 2]:
            img_core = f"{camera_shot}, {scene_setting_en}, {env_lighting_en}. [{locked_product_prompt_segment}]. Presenter in background: {locked_character_prompt_segment}, {micro_expr_en}, {clean_action}"
        else:
            img_core = f"{camera_shot}, {scene_setting_en}, {env_lighting_en}. [{locked_product_prompt_segment}]. Subject: {locked_character_prompt_segment}, {micro_expr_en}, {clean_action}"

        scn["img_p"] = sanitize_third_party_ip(f"{img_core}, tack-sharp focus on product, photorealistic 8k --ar 9:16 --style raw --v 6.1")
        scn["img_neg"] = base_negative_prompt
        clean_vo_for_audio = clean_and_normalize_voiceover(re.sub(r'\.{2,}', '.', vo_text_current).strip())

        if is_pas_scn1_no_prod:
            raw_vid = f"[CAMERA & SETTING]: {camera_shot}, gimbal live-action, {scene_setting_en}, {env_lighting_en}. [SUBJECT]: {locked_character_prompt_segment}, {micro_expr_en}, {clean_action} (empty hands, zero product). [TIMING ({dynamic_scene_sec}s)]: 0.0s-{actual_speech_time}s accurate Vietnamese lip-sync; final {cushion_sec}s natural breathing nod. [AUDIO]: Native Hanoi Vietnamese voice: \"{clean_vo_for_audio}\". Foley only [{scn['sfx']}], zero BGM, no text overlays."
        elif not is_fashion_wearable:
            raw_vid = f"[PRODUCT-CENTRIC CAMERA & SETTING]: {camera_shot}, gimbal live-action, {scene_setting_en}, {env_lighting_en}. [{locked_product_prompt_segment}]. [PRODUCT ACTION & PHYSICS]: {clean_action}. {scene_physics} [PRESENTER]: {locked_character_prompt_segment}, {micro_expr_en}. [TIMING ({dynamic_scene_sec}s)]: 0.0s-{actual_speech_time}s accurate Vietnamese lip-sync while demonstrating the product in foreground; final {cushion_sec}s warm smile & nod. [AUDIO]: Native Hanoi Vietnamese voice: \"{clean_vo_for_audio}\". Foley only [{scn['sfx']}], zero BGM, no text overlays."
        else:
            raw_vid = f"[CAMERA & SETTING]: {camera_shot}, gimbal live-action, {scene_setting_en}, {env_lighting_en}. [SUBJECT]: {locked_character_prompt_segment}, {micro_expr_en}. [{locked_product_prompt_segment}]. [ACTION & PHYSICS]: {clean_action}. {scene_physics} [TIMING ({dynamic_scene_sec}s)]: 0.0s-{actual_speech_time}s accurate Vietnamese lip-sync; final {cushion_sec}s warm smile & nod. [AUDIO]: Native Hanoi Vietnamese voice: \"{clean_vo_for_audio}\". Foley only [{scn['sfx']}], zero BGM, no text overlays."

        vid_parts = raw_vid.split('Native Hanoi Vietnamese voice:')
        if len(vid_parts) == 2: scn["vid_p"] = sanitize_veo3_prompt(vid_parts[0]) + "Native Hanoi Vietnamese voice:" + vid_parts[1]
        else: scn["vid_p"] = sanitize_veo3_prompt(raw_vid)
        scn["vid_neg"] = base_negative_prompt
        
    res["scenes"] = scenes
    res["total_dur"] = f"Khoảng {int(total_sec)} giây"
    
    goal_badge = "🌟 <b>Định hướng:</b> Xây Kênh & Follow" if is_viral else "🛒 <b>Định hướng:</b> Chốt đơn TikTok Shop an toàn"
    cam_mode_badge = "👗 <b>Chế độ Quay (Wearable Fashion):</b> Lấy phom dáng và đường rũ vải làm trung tâm." if is_fashion_wearable else "🎯 <b>Chế độ Quay (Product-Hero Centerpiece):</b> Ép máy quay Zoom & Khóa nét thẳng vào Sản phẩm ở trung tâm tiền cảnh."
    summary_lines = [
        f"⏱ <b>Thời lượng:</b> Khoảng {int(total_sec)}s (Tối đa 10s/cảnh) | 🎬 <b>Chiến lược & Hình thức:</b> {presentation_format} | 👤 <b>Khóa diễn viên (Anti-Celebrity):</b> {detected_demographic_en}",
        f"🗣 <b>Đại từ xưng hô:</b> '{self_pronoun}' - '{audience_pronoun}' | 🏙 <b>Bối cảnh sự kiện thông minh:</b> {fixed_setting_base} | {goal_badge}",
        f"{cam_mode_badge}",
        f"👗 <b>Bộ máy Stylist Chuyên Sâu (Set đồ + Giày dép + Phụ kiện Vòng cổ/Khuyên tai/Đồng hồ):</b> {final_outfit_vi} (Đồng nhất 100% cả 4 cảnh)",
        f"🎨 <b>Khóa Màu & Thiết Kế Sản Phẩm (Product Color Lock):</b> {hero_color_str if hero_color_str else 'Chuẩn ảnh'} -> <code>{clean_prod_en} in {locked_color_en}</code> (Tách biệt hoàn toàn khỏi người mẫu trong ảnh gốc)",
        f"🔗 <b>Cầu nối Ngữ nghĩa 3 Nhánh:</b> Tự động khớp nối Cảnh 1 & Cảnh 2 theo Nhánh Giá rẻ/Săn sale (Nhánh 1), Giải pháp Nỗi đau (Nhánh 2) hoặc Giải mã Bí quyết (Nhánh 3)",
        f"⚡ <b>Ma trận Bộ luật Hành động Thực chiến & Dolly-In:</b> Cảnh 2 & 3 tự động đẩy máy quay cận cảnh, kích hoạt chuyển động thực tế mạnh mẽ theo đúng ngành hàng",
        f"🛡 <b>Bảo vệ Veo 3 (Fictional Persona Lock):</b> Đã gắn nhãn nhân vật hư cấu AI & lọc sạch từ khóa nhạy cảm chống lỗi vi phạm chính sách người nổi tiếng",
        f"💰 <b>Cảnh 4 (Chốt deal):</b> {'Neo giá Flash Sale đối lập' if is_flashsale_script else 'Soft CTA xoáy sâu nỗi đau (An toàn TikTok Shop)'}"
    ]
    if is_single_skirt_mode: summary_lines.append("👗 <b>Khóa Váy 1 Ống Rộng (Single Unsplit Skirt Tube Lock):</b> Đã chuyển đổi thành Maxi Skirt, loại bỏ hoàn toàn từ khóa 'pants/trousers' và chặn quần 2 ống trong Negative Prompt.")
    if is_strict_appliance: summary_lines.append("🏠 <b>Khóa Tham Chiếu Đồ Gia Dụng (Strict Reference Appliance):</b> Bám sát 100% hình mẫu tham chiếu, khóa cứng hình học 3D, chặn hoàn toàn các chi tiết thừa và chống biến dạng.")
    if user_custom_note and user_custom_note.lower() not in ["mặc định chuẩn", "không có", "không có ghi chú đặc biệt, tuân thủ kịch bản chuẩn."]: summary_lines.append(f"🎯 <b>Ghi chú riêng của người dùng:</b> {user_custom_note}")
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
# 4. GIAO DIỆN THANH BÊN (SIDEBAR) & QUẢN TRỊ ADMIN
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
            
        st.session_state.active_project_title = st.text_input("Tên dự án hiện tại:", value=st.session_state.active_project_title)
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
                sel_creator = st.selectbox("👤 Lọc theo thành viên:", ["Tất cả thành viên"] + creator_emails, key="admin_sel_creator")
                if sel_creator != "Tất cả thành viên": all_projects = [p for p in all_projects if p.get("user_email") == sel_creator]

            search_proj = st.text_input("🔍 Tìm kiếm dự án:", placeholder="Nhập tên dự án...", key="search_proj_input")
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
                        
                        new_p_name = st.text_input("Đổi tên dự án:", value=p['project_title'], key=f"ren_txt_{p['id']}")
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
            search_acc = st.text_input("🔍 Tìm tài khoản:", placeholder="Nhập Email hoặc SĐT...", key="search_acc_input")
            other_accs = [item for item in st.session_state.licensed_accounts.items() if item[0] != ADMIN_EMAIL]
            filt_accs = [item for item in other_accs if search_acc.strip().lower() in item[0].lower() or search_acc.strip() in item[1].get('phone', '')] if search_acc.strip() else (other_accs if st.session_state.show_all_admin_accounts else other_accs[:3])

            for acc_mail, info in filt_accs:
                with st.expander(f"👤 {acc_mail} ({info.get('plan_type')})"):
                    st.write(f"📞 SĐT: `{info.get('phone', 'N/A')}` | ⏳ Hạn: `{info.get('expires_at')}`")
                    new_user_pass = st.text_input("🔑 Đổi mật khẩu:", value=info.get("password", ""), key=f"pass_edit_{acc_mail}")
                    if st.button("⚡ Đặt 123456", key=f"btn_quick_reset_{acc_mail}", use_container_width=True, disabled=is_system_busy):
                        st.session_state.licensed_accounts[acc_mail]["password"] = "123456"
                        save_single_account(acc_mail, st.session_state.licensed_accounts[acc_mail])
                        st.toast(f"✅ Đã reset mật khẩu của {acc_mail} về '123456'!"); st.rerun()

                    new_roles = st.multiselect("Đổi thể loại:", ALL_MODULES, default=info.get("roles", ALL_MODULES), key=f"roles_sel_{acc_mail}")
                    new_plan = st.selectbox("Đổi gói:", ["Trial", "Basic", "Advanced", "VIP"], index=["Trial", "Basic", "Advanced", "VIP"].index(info.get("plan_type", "Trial")), key=f"plan_sel_{acc_mail}")
                    renew_choice = st.selectbox("Gia hạn:", ["Giữ nguyên hạn hiện tại", "3 Ngày", "7 Ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "Vĩnh viễn", "Tùy chỉnh (Chọn ngày)"], key=f"renew_opt_{acc_mail}")
                    target_exp_str = info.get("expires_at", "2099-12-31")
                    if renew_choice == "Tùy chỉnh (Chọn ngày)":
                        try: cur_d = datetime.strptime(info.get("expires_at", ""), "%Y-%m-%d").date()
                        except: cur_d = date.today() + timedelta(days=30)
                        target_exp_str = st.date_input("Chọn ngày hết hạn mới:", value=cur_d, min_value=date.today(), key=f"rdate_{acc_mail}").strftime("%Y-%m-%d")
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
# 5. KHÔNG GIAN SÁNG TẠO CHÍNH
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Đạo Diễn AI - Hệ Thống Kịch Bản Pro</div></div>""", unsafe_allow_html=True)

user_allowed_modules = st.session_state.licensed_accounts.get(st.session_state.current_email, {}).get("roles", ALL_MODULES) or ALL_MODULES
mode = st.selectbox("🎯 Thể loại:", user_allowed_modules, key=f"mode_sel_{st.session_state.reset_key}")
is_viral_mode = "Viral" in mode

up_files, custom_note = [], ""
viral_persona, viral_topic = "", ""

if not st.session_state.is_analyzed:
    if is_viral_mode:
        col_v1, col_v2 = st.columns(2)
        viral_persona = col_v1.text_input("👤 Định vị Kênh:", placeholder="Ví dụ: Mẹ bỉm sữa thông thái...", key=f"viral_persona_{st.session_state.reset_key}")
        viral_topic = col_v2.text_area("💡 Chủ đề / Mẹo:", height=68, placeholder="Ví dụ: 3 mẹo setup góc làm việc gọn gàng...", key=f"viral_topic_{st.session_state.reset_key}")
        up_files = st.file_uploader("📦 Upload Ảnh:", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_viral_{st.session_state.reset_key}")
        if up_files:
            with st.expander(f"👁 Xem lại {len(up_files)} ảnh đã tải lên", expanded=False):
                n_cols = min(len(up_files), 4)
                cols = st.columns(n_cols)
                for idx, f in enumerate(up_files): cols[idx % n_cols].image(f, caption=f"Ảnh {idx + 1}", use_container_width=True)
        custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất - ví dụ: quần là dạng váy 1 ống rộng):", key=f"custom_note_viral_{st.session_state.reset_key}")
        hero_sku_override = ""
    else:
        products_data = supabase.table("products").select("*").execute().data if supabase else []
        if products_data:
            selected_name = st.selectbox("📌 Chọn sản phẩm:", [p["product_name"] for p in products_data], key=f"prod_select_{st.session_state.reset_key}")
            st.session_state.current_product_data = next(p for p in products_data if p["product_name"] == selected_name)
        col_f1, col_f2 = st.columns([2, 1])
        up_files = col_f1.file_uploader("📦 Upload Ảnh SP (Quét OCR Giá, Hero SKU & Bảng màu):", type=["jpg", "png"], accept_multiple_files=True, key=f"up_files_prod_{st.session_state.reset_key}")
        hero_sku_override = col_f2.text_input("🎯 Màu / SKU ưu tiên (Tùy chọn):", placeholder="Ví dụ: Trắng tinh...", key=f"hero_override_{st.session_state.reset_key}")
        if up_files:
            with st.expander(f"👁 Xem lại {len(up_files)} ảnh sản phẩm đã tải lên", expanded=False):
                n_cols = min(len(up_files), 4)
                cols = st.columns(n_cols)
                for idx, f in enumerate(up_files): cols[idx % n_cols].image(f, caption=f"Ảnh {idx + 1}", use_container_width=True)
        custom_note = st.text_area("✍ Ghi chú AI (Ưu tiên cao nhất - ví dụ: quần là dạng váy 1 ống rộng):", key=f"custom_note_prod_{st.session_state.reset_key}")

    style = "Điện Ảnh Chân Thực"
    col_strat, col_role, col_actor_img = st.columns([1.4, 1.6, 1.0])
    unified_strategy_format = col_strat.selectbox("🧭 Chiến lược & Hình thức Video:", UNIFIED_STRATEGY_FORMAT_OPTS, index=0, key=f"unified_strat_format_{st.session_state.reset_key}")
    role_input = col_role.text_input("👤 Vai trò NV (Để trống = AI tự phân tích):", value="", placeholder="Ví dụ: Nam 25t...", key=f"r_0_{st.session_state.reset_key}")
    c_file = col_actor_img.file_uploader("📸 Ảnh mẫu NV (Tùy chọn):", type=["jpg", "png"], key=f"f_0_{st.session_state.reset_key}")

    char_inputs = [{"id": 1, "role": role_input.strip(), "file": c_file}] if (c_file or role_input.strip()) else []

    if st.button("🚀 Phân Tích Sản Phẩm Và Tạo Kịch Bản", type="primary", use_container_width=True, disabled=is_system_busy):
        can_run, msg = check_usage_limit(st.session_state.current_email)
        if not can_run: st.error(msg)
        else:
            with st.spinner("⏳ Đạo diễn AI đang quét cấu trúc hình học 3D, khóa màu sắc tiếng Anh & phối đồ Stylist..."):
                try:
                    st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs] if char_inputs else [{"id": 1, "role": ""}]
                    char_rules = generate_char_rules_string(st.session_state.character_profiles)
                    st.session_state.update({
                        "last_mode": mode, "last_style": style, "last_narrator": "On-camera", 
                        "last_presentation_format": unified_strategy_format,
                        "current_input_context": custom_note.strip()
                    })
                    
                    if is_viral_mode:
                        st.session_state.current_product_data_saved = {"channel_persona": viral_persona.strip(), "topic_or_tips": viral_topic.strip()}
                        input_context_str = f"KÊNH: '{viral_persona.strip()}' | CHỦ ĐỀ: '{viral_topic.strip()}' | NOTE: '{custom_note.strip()}'"
                    else:
                        st.session_state.current_product_data_saved = st.session_state.get("current_product_data", {})
                        input_context_str = f"SP: {json.dumps(st.session_state.current_product_data_saved, ensure_ascii=False)} | NOTE: '{custom_note.strip()}'"
                    
                    st.session_state["saved_reference_images"] = []
                    if up_files:
                        for f in up_files:
                            cb, cm = compress_image_bytes(f, 768, 75)
                            st.session_state["saved_reference_images"].append((cb, cm))

                    override_instruction = f"Khóa Hero SKU: '{hero_sku_override.strip()}'." if hero_sku_override.strip() else "Ưu tiên SKU có icon 🔥/Hot/Bán chạy. Phân biệt rõ màu thật của SP với bóng đổ 3D xám trên ảnh!"
                    skirt_note_rule = "ĐẶC BIỆT: Ghi chú có yêu cầu 'quần dạng váy 1 ống / quần váy', trong 'product_visual_en' BẮT BUỘC mô tả là 'full-length A-line maxi skirt (single unified unsplit skirt tube, zero leg division)', TUYỆT ĐỐI CẤM dùng từ 'pants' hoặc 'trousers'!" if detect_single_tube_skirt(custom_note) else ""

                    prompt = f"""
                    INPUT: {input_context_str} | THỂ LOẠI: '{mode}' | CHIẾN LƯỢC: '{unified_strategy_format}'
                    HERO SKU: {override_instruction}
                    {skirt_note_rule}
                    - Tách biệt 100% SP khỏi người mẫu gốc trong ảnh. Tự thiết kế KOC người Việt phù hợp ('koc_demographic_analysis') & phối đồ Stylist ('stylist_coordination_vi').
                    - Tạo 'product_visual_en' mô tả ngắn gọn (dưới 14 từ) hình khối 3D cố định & chất liệu bằng tiếng Anh.

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
                            "hero_sku_color": "Mã màu Hero SKU tiếng Việt (VD: Trắng tinh)",
                            "hero_sku_color_en": "Exact English color (e.g., solid pure matte-white)",
                            "product_visual_en": "Concise English product description under 14 words",
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
                    payload = ["PRODUCT IMAGES (EXTRACT RIGID 3D STRUCTURE, TRUE COLOR, AND OCR PRICES - IGNORE HUMAN MODELS):"]
                    for cb, cm in st.session_state["saved_reference_images"]:
                        payload.append(types.Part.from_bytes(data=cb, mime_type=cm))
                    for c in char_inputs:
                        if c.get("file"):
                            cb, cm = compress_image_bytes(c['file'], 768, 75)
                            payload.extend([f"ACTOR {c['id']} (EXTRACT AGE, GENDER, HAIR ONLY):", types.Part.from_bytes(data=cb, mime_type=cm)])
                    payload.append(prompt)
                    
                    res = call_gemini(payload, get_sys_inst_outlines(mode, style, "On-camera", char_rules, 1, unified_strategy_format, custom_note.strip(), unified_strategy_format), max_tokens=4096)
                    ca_result = res.get("content_analysis") or {}
                    st.session_state.content_analysis = ca_result
                    outlines = res.get("outlines", res.get("script_outlines", []))
                    
                    if not outlines: raise Exception("AI bị ngắt quãng do kết nối mạng. Vui lòng bấm tạo lại.")
                    
                    for o in outlines: 
                        if "hook" in o: o["hook"] = clean_and_normalize_voiceover(o["hook"])
                        o.update({
                            "duration_instruction": "Max 10s", "narrator_mode": "On-camera", 
                            "character_profiles": st.session_state.character_profiles, "actors": 1,
                            "custom_note": custom_note.strip(), "presentation_format": unified_strategy_format
                        })
                    
                    auto_proj_title = extract_bold_product_title(ca_result, fallback_topic=viral_topic)
                    st.session_state.update({
                        "active_project_title": auto_proj_title, "current_project_id": None,
                        "all_scripts": outlines, "cloned_scripts": [], "expanded_scripts": [],
                        "generated_details": {}, "active_script_id": None, "is_analyzed": True
                    })
                    auto_save_current_session()
                    st.toast(f"✅ Đã phân tích & tự động lưu dự án: {auto_proj_title}!"); st.rerun()
                except Exception as e: st.error(f"❌ Lỗi: {e}")

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
                <div class="dna-row"><span class="dna-label">⭐ Khóa màu Hero SKU (4 cảnh):</span><span class="dna-text" style="color:#dc2626; font-weight:700;">{clean_analysis_text(ca.get('hero_sku_color', 'Tự động'))} ({locked_color_preview})</span></div>
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
        loc_type_str = "Khóa 1 vị trí cố định (Single-Location)" if ca.get('is_fixed_location', True) else "Chuyển cảnh theo mạch truyện (Dynamic)"
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
            st.session_state.active_script_id = None
            st.rerun()
            
        active_id = st.session_state.active_script_id
        asc = st.session_state.generated_details.get(str(active_id), st.session_state.generated_details.get(active_id, {}))
        
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(asc.get('title', '')).upper()}**")
        
        director_summary_html = asc.get('director_summary', '')
        if not director_summary_html:
            # KHÔI PHỤC FULL TÓM TẮT NẾU CHƯA CÓ
            total_sec = sum([float(str(s.get('dur', '8s')).replace('s', '')) for s in asc.get("scenes", [])])
            goal_badge = "🌟 <b>Định hướng:</b> Xây Kênh & Kéo Tương Tác / Follow" if is_viral_mode else "🛒 <b>Định hướng:</b> Chốt đơn TikTok Shop an toàn"
            cam_mode_badge = "🎯 <b>Chế độ Quay (Product-Hero Centerpiece):</b> Ép máy quay Zoom & Khóa nét thẳng vào Sản phẩm ở trung tâm tiền cảnh."
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
            comma_count = vo_text.count(',') + vo_text.count(';')
            period_count = vo_text.count('.') + vo_text.count('!') + vo_text.count('?')
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
                st.markdown("**🖼 Prompt Ảnh Tinh Gọn (Midjourney / Flux - Lấy Sản Phẩm Làm Trọng Tâm Tiền Cảnh):**")
                st.code(img_p := scn.get('img_p', ''), language="text")
                safe_copy_button(img_p, f"📋 Sao Chép Prompt Ảnh Cảnh {idx}")
                st.caption("💡 *Mẹo giữ nhân vật & màu sản phẩm đồng nhất:* Sau khi tạo ảnh Cảnh 1 ưng ý, copy link ảnh và gắn vào đuôi prompt Cảnh 2, 3, 4: `--cref [URL_ẢNH_CẢNH_1] --cw 100`")
                
            with c_p2:
                st.markdown("**🎥 Prompt Video Tinh Gọn (Veo 3 Pro - Zoom & Khóa Nét Vào Sản Phẩm, Anti-Morphing):**")
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
                        st.session_state.active_script_id = int(sc_id); st.rerun()
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
            with st.spinner(f"⏳ Đang dựng nhanh kịch bản #{target_id_to_run} (Khóa Tiêu Cự Trung Tâm Vào Sản Phẩm & Gemini 3.8 Flash)..."):
                create_scene_details(target_id_to_run, st.session_state.last_mode, "Điện Ảnh Chân Thực")
                st.session_state.active_script_id = int(target_id_to_run)
                success = True
        except Exception as e: error_msg = str(e)
            
        st.session_state.current_processing_id = None
        if success: st.toast(f"✅ Đã dựng kịch bản #{target_id_to_run} & tự động lưu cập nhật vào dự án!"); st.rerun()
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
        if success: st.toast("✅ Đã nhân bản 5 kịch bản & tự động lưu cập nhật vào dự án!"); st.rerun()
        else: st.error(f"❌ Lỗi khi nhân bản kịch bản: {error_msg}")

    # ==========================================================================
    # KHU VỰC GỌI THÊM 5 KỊCH BẢN MỚI
    # ==========================================================================
    st.divider()
    st.markdown("### ➕ **Gọi Thêm 5 Kịch Bản Mới**")
    
    cy1, cy2, cy3 = st.columns([1.4, 1.6, 1.0])
    c_unified_more = cy1.selectbox("🧭 Chiến lược & Hình thức Video mới:", UNIFIED_STRATEGY_FORMAT_OPTS, index=0, key=f"more_unified_{st.session_state.reset_key}")
    e_role = cy2.text_input("👤 Vai trò NV mới (Để trống = AI tự phân tích):", value="", placeholder="Để trống = Giữ nguyên hoặc AI tự phân tích...", key=f"er_0_{st.session_state.reset_key}")
    e_file = cy3.file_uploader("📸 Ảnh mẫu NV mới (Tùy chọn):", type=["jpg", "png"], key=f"ef_0_{st.session_state.reset_key}")
    extra_custom_note = st.text_area("✍ Ghi chú AI cho kịch bản thêm (Ưu tiên cao nhất):", placeholder="Ví dụ: Quần là dạng váy 1 ống rộng...", key=f"extra_custom_note_{st.session_state.reset_key}")

    if st.button("🚀 Gọi Thêm 5 Kịch Bản Mới", type="primary", use_container_width=True, disabled=is_system_busy):
        can_run, msg = check_usage_limit(st.session_state.current_email)
        if can_run:
            with st.spinner("⏳ Đang sáng tạo thêm 5 kịch bản & tự động lưu cập nhật vào dự án..."):
                p_chars = [{"id": 1, "role": e_role.strip()}] if e_role.strip() else st.session_state.character_profiles
                st.session_state.expanded_scripts.extend(generate_more_scripts(c_unified_more, p_chars, extra_custom_note))
                auto_save_current_session()
                st.toast("✅ Đã sinh thêm 5 kịch bản mới & tự động lưu cập nhật vào dự án!"); st.rerun()
        else: st.error(msg)
