import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from supabase import create_client, Client
import json, base64, os, re, time, ast, uuid, io
from PIL import Image
from datetime import datetime, timedelta

# ==============================================================================
# 1. CẤU HÌNH GIAO DIỆN & GA4
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
    st.markdown("<style>div[data-testid='stAppViewContainer'] { pointer-events: none; opacity: 0.65; }</style>", unsafe_allow_html=True)

st.markdown("""
<style>
    .header-container { text-align: center; padding: 1.2rem; background: radial-gradient(circle, rgba(255,75,75,0.08) 0%, rgba(255,255,255,0) 70%); border-radius: 16px; margin-bottom: 1rem; }
    .main-title { font-size: 2.2rem !important; font-weight: 900 !important; background: linear-gradient(90deg, #ff0050 0%, #ff5252 50%, #ff7300 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important; color: white !important; border-radius: 8px !important; font-weight: bold; width: 100%; }
    div[data-testid="stButton"] > button[kind="secondary"] { background: linear-gradient(135deg, #ff4b4b 0%, #ff7300 100%) !important; color: #ffffff !important; border-radius: 8px !important; font-weight: bold !important; width: 100%; }
    .voiceover-text { color: #15803d; background: #f0fdf4; padding: 8px 12px; border-radius: 6px; font-size: 15.5px; border: 1px solid #bbf7d0; display: inline-block; width: 100%; line-height: 1.6; }
    .detail-header-box { background: #eff6ff; border: 1.5px solid #bfdbfe; border-radius: 10px; padding: 15px; margin-bottom: 20px; color: #1e3a8a; }
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
        if acc.get("daily_usage_count", 0) >= limit: return False, f"Hết lượt tạo chi tiết ({limit}/{limit})."
        acc["daily_usage_count"] += 1
        save_single_account(email, acc)
    return True, ""

def safe_copy_button(text_to_copy: str, button_label: str = "📋 Sao Chép"):
    b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    html_id = f"btn_{int(time.time()*10000)}_{len(text_to_copy)}"
    components.html(f"""
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
    """, height=45)

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
    ("reset_key", 0), ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"),
    ("last_mode", ""), ("last_style", ""), ("last_narrator", ""),
    ("target_duration_instruction", ""), ("character_profiles", []), ("current_project_id", None)
]:
    if key not in st.session_state: st.session_state[key] = default_val

# ==============================================================================
# 2. HÀM AI LÕI & KHÓA ĐỒNG NHẤT
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
            raise Exception("AI JSON lỗi cấu trúc. Vui lòng thử lại.")

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
    if not profiles: return "IDENTITY_LOCK: Khóa cố định 100% khuôn mặt, vóc dáng và DUY NHẤT một kiểu tóc cố định (buộc cao hoặc xõa thẳng) xuyên suốt tất cả phân cảnh."
    rules = "IDENTITY_LOCK:\n"
    for p in profiles: rules += f" - Diễn viên {p['id']} ({p['role']}): Khóa cố định 100% diện mạo, kiểu tóc duy nhất và trang phục qua mọi cảnh.\n"
    return rules

def get_sys_inst_outlines(mode, style, narrator_mode, char_rules, num_chars, angle):
    strat = "MIX ĐA DẠNG 5 GÓC ĐỘ" if "Tự động mix" in angle else f"TUÂN THỦ: '{angle}'"
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL TIKTOK SHOP. {strat}. PHONG CÁCH: {style}
    QUY TẮC CỐT LÕI:
    1. ƯU TIÊN HERO SKU: Quét kỹ nhãn bán chạy (như 'Đã bán 1K+', viền đỏ, mẫu da báo/thỏ hoa) từ ảnh để làm sản phẩm chủ đạo xuyên suốt.
    2. BỐI CẢNH NATIVE: Ga gối đệm trên giường phòng ngủ; đồ bếp ở bàn bếp; xả kho ở kho hàng.
    3. CÔNG THỨC GIÁ: Neo giá gốc làm tròn (gần... nghìn), khẳng định giảm cực sâu, giấu giá sale, miễn trừ thời gian.
    4. CHÍNH SÁCH: Cấm từ cam kết (100%, tuyệt đối, thuốc). Trẻ em bắt buộc có mẹ kề bên.
    5. {char_rules}
    """

def get_sys_inst_details(mode, style, narrator_mode, char_rules, duration_instruction):
    is_on_camera = "On-camera" in narrator_mode
    audio_cmd = "Chèn lệnh `Audio:` vào `vid_p`." if is_on_camera else "KHÔNG chèn Audio vào `vid_p`."
    return f"""
    BẠN LÀ ĐẠO DIỄN VIRTUAL VEO 3. PHONG CÁCH: {style}
    
    🛑 QUY TẮC KHÓA BẢO TỒN ĐỒNG NHẤT 100%:
    1. KHÓA KIỂU TÓC & DIỆN MẠO (HAIR & IDENTITY LOCK):
       - Khóa DUY NHẤT 1 kiểu tóc trong `global_identity_en` (VD: tóc xõa tự nhiên hoặc tóc búi cao). TÁI SỬ DỤNG CHÍNH XÁC MÔ TẢ NÀY TRONG CẢ 4 CẢNH. CẤM cảnh xõa tóc, cảnh búi tóc.
    2. KHÓA HỌA TIẾT SẢN PHẨM (EXACT PRODUCT PRINT & PATTERN LOCK):
       - Trích xuất chính xác mẫu mã/họa tiết của sản phẩm tham chiếu trong `prod_dna` (VD: họa tiết da báo chuẩn màu nâu-đen, hoặc thỏ hoa). CẤM đổi họa tiết giữa các cảnh.
    3. KHÓA TRANG PHỤC CỐ ĐỊNH: Tái sử dụng nguyên văn `global_outfit_en` trong cả 4 cảnh.
    4. THỜI LƯỢNG & SỐ TỪ CHUẨN:
       - Cảnh 1 (Attention - 4s): 13 - 14 từ (Khởi động 0.00s, trực quan hóa nỗi đau).
       - Cảnh 2 (Interest - 6s): 20 - 22 từ (Thao tác thực tế).
       - Cảnh 3 (Desire - 8s): 28 - 30 từ (Trải nghiệm vượt trội, bảng màu).
       - Cảnh 4 (Action - 6s/8s): 20 - 26 từ (Chốt giá tương phản).
    5. CHÍNH SÁCH: Cấm từ cam kết. Mẹ & bé luôn có mẹ bế/giám sát an toàn.
    6. KHÔNG CHỮ / SUBTITLES / ICONS: "NO generated text, NO subtitles, NO floating icons, NO UI elements. Clean frame."
    7. {audio_cmd}
    8. {char_rules}
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
    
    audio_instruction = 'Chèn: Audio: "[CHÉP ĐỦ 100% VOICEOVER]", Layered SFX: [MÔ TẢ SFX THỰC TẾ]' if is_on_camera else 'Chỉ chèn Layered SFX thực tế, không chèn thoại.'
    voice_hint = "Giọng [Nam/Nữ] HÀ NỘI CHUẨN ĐẦY NỘI LỰC, ĐANH THÉP, BẮT ĐẦU NÓI NGAY 0.00S, NHỊP ĐỘ ĐỀU METRONOME (4.3 - 4.5 từ/s)."

    prompt = f"""
    DỮ LIỆU: {prod_data_ctx} | DNA: {dna_data_ctx}
    Viết chi tiết kịch bản ID {target_id}: '{outline.get('title')}'. Hook: {outline.get('hook')}. Bối cảnh: {outline.get('setting')}.
    THUYẾT MINH: {audio_instruction} | LOẠI: {mode}
    
    🛑 YÊU CẦU ĐẶC BIỆT:
    - BẮT BUỘC KHÓA DUY NHẤT 1 KIỂU TÓC TRONG `global_identity_en` CHO CẢ 4 CẢNH (CẤM cảnh xõa tóc cảnh búi tóc).
    - BẮT BUỘC KHÓA ĐÚNG HỌA TIẾT VÀ MÀU SẮC CHÍNH XÁC CỦA SẢN PHẨM TRONG `prod_dna` (VD: họa tiết da báo hoặc thỏ hoa theo đúng ảnh tham chiếu).
    - CẢNH 1: Trực quan hóa nỗi đau thực tế.
    - CẢNH 4: Đòn bẩy giá tương phản.
    - BẮT BUỘC ĐỦ 4 CẢNH AIDA (Scene 1: 4s/13-14 từ; Scene 2: 6s/20-22 từ; Scene 3: 8s/28-30 từ; Scene 4: 6s-8s/20-26 từ).
    
    TRẢ VỀ JSON:
    {{
        "title": "{outline.get('title')}",
        "total_dur": "24s-30s",
        "outfit_vi": "Trang phục và kiểu tóc khóa cố định duy nhất cho cả 4 cảnh",
        "global_identity_en": "Fixed English description of Face, EXACT LOCKED HAIRSTYLE (choose strictly ONE: either neatly tied high bun OR loose hair, invariant across all scenes), Body.",
        "global_outfit_en": "Fixed English description of EXACT outfit. REUSED 100% IN ALL SCENES.",
        "global_setting_en": "Fixed English description of native setting.",
        "prod_dna": "Exact product description specifying EXACT pattern/print (e.g. identical brown leopard fleece pattern) locked across all scenes.",
        "voice": {{"gender": "Nam/Nữ", "tone": "{voice_hint}"}},
        "scenes": [
            {{
                "scene": 1, "aida_stage": "Attention", "dur": "4s", "trans": "Chuyển cảnh mới",
                "setting": "Bối cảnh thực trạng nỗi đau...",
                "action_en": "Close-up pain point shot. [global_identity_en] wearing [global_outfit_en]. Mouth articulates at 0.00s.",
                "director": "Attention | Trực quan hóa nỗi đau | SFX thực tế | Khởi động: 0.00s | Tông đanh thép",
                "voiceover": "Thoại 13-14 từ...",
                "img_p": "Vertical 9:16 photo. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Product: [prod_dna]. Clean frame.",
                "vid_p": "Vertical 9:16 video. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Action: [action_en]. Immediate speech at 0.00s. Audio: \\"[ĐIỀN ĐỦ VOICEOVER]\\", Layered SFX: [tiếng động thực tế]. Product: [prod_dna]. Strict persistent geometry and invariant pattern. NO text, NO UI. Clean frame."
            }},
            {{
                "scene": 2, "aida_stage": "Interest", "dur": "6s", "trans": "Chuyển cảnh mới",
                "setting": "Bối cảnh giải pháp...",
                "action_en": "Real-life usage action. Same locked hairstyle and outfit. Mouth articulates at 0.00s.",
                "director": "Interest | Thao tác thực tế | SFX | Khởi động: 0.00s | Tông tự nhiên",
                "voiceover": "Thoại 20-22 từ...",
                "img_p": "Vertical 9:16 photo. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Clean frame.",
                "vid_p": "Vertical 9:16 video. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Audio: \\"[ĐIỀN ĐỦ VOICEOVER]\\", Layered SFX: [SFX]. Product: [prod_dna]. Clean frame."
            }},
            {{
                "scene": 3, "aida_stage": "Desire", "dur": "8s", "trans": "Chuyển cảnh mới",
                "setting": "Bối cảnh trải nghiệm...",
                "action_en": "Delightful sensory interaction. Same locked hairstyle. Mouth articulates at 0.00s.",
                "director": "Desire | Trải nghiệm & Bảng màu | SFX | Khởi động: 0.00s | Tông nội lực",
                "voiceover": "Thoại 28-30 từ...",
                "img_p": "Vertical 9:16 photo. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Clean frame.",
                "vid_p": "Vertical 9:16 video. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Audio: \\"[ĐIỀN ĐỦ VOICEOVER]\\", Layered SFX: [SFX]. Product: [prod_dna]. Clean frame."
            }},
            {{
                "scene": 4, "aida_stage": "Action", "dur": "6s", "trans": "Chuyển cảnh mới",
                "setting": "Bối cảnh chốt deal...",
                "action_en": "Warm closing gesture. Same locked hairstyle. Mouth articulates at 0.00s.",
                "director": "Action | Đòn bẩy giá | SFX | Khởi động: 0.00s | Tông chốt deal",
                "voiceover": "Thoại 20-26 từ đòn bẩy giá tương phản...",
                "img_p": "Vertical 9:16 photo. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Product: [prod_dna]. Clean frame.",
                "vid_p": "Vertical 9:16 video. [global_setting_en]. Character: [global_identity_en] wearing [global_outfit_en]. Audio: \\"[ĐIỀN ĐỦ VOICEOVER]\\", Layered SFX: [SFX]. Product: [prod_dna]. Clean frame."
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
    Sinh 5 kịch bản mới chuẩn AIDA theo chiến lược: '{angle}'. Diễn viên: {num_chars}.
    TRẢ VỀ JSON:
    {{
        "outlines": [
            {{ "id": {cur_len+1}, "title": "Tên 1", "setting": "Bối cảnh...", "hook": "Hook 3s...", "actors": {num_chars} }}
        ]
    }}
    BẮT BUỘC ĐỦ 5 KỊCH BẢN.
    """
    res = call_gemini([prompt], get_sys_inst_outlines(mode, style, narrator_mode_more, char_rules, num_chars, angle), max_tokens=3000)
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
    
    prompt = f"Nhân bản: {json.dumps(target, ensure_ascii=False)} thành 5 biến thể AIDA mới."
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
# 3. THANH BÊN (SIDEBAR)
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

        st.markdown("---")
        u_info = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
        u_plan = u_info.get("plan_type", "Trial")
        u_used = u_info.get("daily_usage_count", 0) if u_info.get("last_generation_date") == datetime.now().strftime("%Y-%m-%d") else 0
        u_lim = "Không giới hạn" if u_plan == "VIP" else (20 if u_plan == "Advanced" else (10 if u_plan == "Basic" else 3))
        st.info(f"**GÓI {u_plan.upper()}**\n\n• Email: {st.session_state.current_email}\n• Tạo chi tiết: **{u_used}/{u_lim}**\n• Hạn dùng: {u_info.get('expires_at')}")

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
        with st.spinner("⏳ Đang quét OCR bảng màu, nhận diện Hero SKU và phân tích DNA..."):
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
                        "target_audience": "Nhận diện TỆP KHÁCH HÀNG MỤC TIÊU",
                        "core_value": "Giá trị cốt lõi giải quyết vấn đề gì",
                        "pain_points": "Nỗi đau / Rào cản lớn nhất của khách hàng (TRỰC QUAN HÓA CẢNH 1)",
                        "hook_element": "Yếu tố giật gân, tạo tò mò hoặc xúc động đánh đúng tâm lý trong 3 giây đầu",
                        "hero_sku_color": "MÃ MÀU BÁN CHẠY NHẤT (HERO SKU): Quét nhãn 'Đã bán 1K+', viền đỏ, hoặc họa tiết đặc trưng (VD: da báo, thỏ hoa).",
                        "color_palette": "BẢNG MÀU TOÀN BỘ: Liệt kê danh sách tất cả các màu/họa tiết có trong ảnh",
                        "what_and_unique": "Sản phẩm là gì & điểm độc bản (USP)",
                        "target_user": "Dành cho ai",
                        "why_buy": "Tại sao nên mua",
                        "where_and_convenience": "Dùng ở đâu tiện ích ra sao",
                        "how_to_use": "Cách sử dụng thực tế",
                        "product_size_class": "Phân loại kích thước",
                        "product_color_lock": "KHÓA MÀU SẮC & HỌA TIẾT HERO SKU CHUẨN XÁC",
                        "lid_mechanism": "Cơ chế mở nắp / vòi xịt",
                        "detected_prices": "Giá niêm yết OCR",
                        "rounded_price_anchor": "Làm tròn giá niêm yết (gần... nghìn)",
                        "product_dimensions": "Thông số kích thước",
                        "prompt_dna_lock": "Visual DNA cho video"
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

ca = st.session_state.content_analysis
if isinstance(ca, dict):
    st.divider()
    st.markdown("### 🔍 **Phân Tích DNA Chi Tiết Theo Mô Hình AIDA & Hero SKU**")
    with st.container(border=True):
        col_dna1, col_dna2 = st.columns(2)
        col_dna1.markdown(f"##### 🎯 **1. Chân dung Khách hàng & Hook 3s (Attention):**<br><div style='line-height: 1.8;'>{format_analysis_field(ca.get('target_audience', ''))}<br>{format_analysis_field(ca.get('pain_points', ''))}<br><b>⚡ Yếu tố Hook 3s đầu:</b> <span style='color:#d90429; font-weight:bold;'>{ca.get('hook_element', '')}</span></div>", unsafe_allow_html=True)
        col_dna2.markdown(f"##### 🔥 **2. Mã Màu Bán Chạy Nhất (Hero SKU):**<br><div style='line-height: 1.8;'><b>⭐ Màu ưu tiên làm video:</b> <span style='color:#d90429; font-size:16px; font-weight:bold;'>{ca.get('hero_sku_color', 'Tự động')}</span><br><b>🎨 Toàn bộ bảng màu:</b> <span style='color:#0284c7;'>{format_analysis_field(ca.get('color_palette', ''))}</span></div>", unsafe_allow_html=True)
        st.markdown(f"--- \n##### 💎 **3. Giải phẫu Sản phẩm (Interest & Desire):**<br><div style='line-height: 1.8;'><b>📦 Sản phẩm là gì & Điểm đặc biệt:</b> {ca.get('what_and_unique', '')}<br><b>👥 Sản phẩm dành cho ai:</b> {ca.get('target_user', '')}<br><b>🔥 Tại sao nên mua:</b> {ca.get('why_buy', '')}<br><b>📍 Dùng ở đâu & Tiện lợi:</b> {ca.get('where_and_convenience', '')}<br><b>🛠 Cách sử dụng:</b> {ca.get('how_to_use', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"--- \n##### 🏭 **4. Vật lý, Cơ chế & Giá tiền OCR:**<br><div style='line-height: 1.8;'><b>📐 Thông số:</b> {ca.get('product_dimensions', '')}<br><b>🎨 Khóa màu chi tiết:</b> {ca.get('product_color_lock', '')}<br><b>💰 Giá niêm yết OCR:</b> {ca.get('detected_prices', '')} (Làm tròn: <b>{ca.get('rounded_price_anchor', '')}</b>)</div>", unsafe_allow_html=True)
    if ca.get('prompt_dna_lock'):
        st.markdown("##### 📌 **Visual DNA Lock:**")
        st.code(ca.get('prompt_dna_lock'), language="text")

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
        st.markdown(f"<div class='detail-header-box'>⏱ Thời lượng: <b>{asc.get('total_dur')}</b> | 🎙 Giọng: <b>{vp.get('gender', 'Nữ')}</b> | 👔 <b>Khóa diện mạo & kiểu tóc:</b> {asc.get('outfit_vi')}</div>", unsafe_allow_html=True)
        
        for idx, scn in enumerate(asc.get("scenes", []), 1):
            vo_text = scn.get('voiceover', '')
            actual_words = count_words(vo_text)
            comma_count = vo_text.count(',')
            
            st.markdown(f"#### 📍 Phân cảnh {idx} ({scn.get('dur')}) - Giai đoạn {scn.get('aida_stage')}")
            st.markdown(f"🏛 **Bối cảnh:** *{scn.get('setting')}*\n\n**🎙 Đạo diễn & SFX:** *{scn.get('director')}*\n\n**💬 Thoại (Đếm thực tế: {actual_words} từ | {comma_count} dấu phẩy):** <span class='voiceover-text'>{vo_text}</span>", unsafe_allow_html=True)
            if scn.get('img_p'): st.markdown("**🖼 Prompt Ảnh:**"); st.code(img_p := scn.get('img_p'), language="text"); safe_copy_button(img_p, f"📋 Sao Chép Ảnh Cảnh {idx}")
            if scn.get('vid_p'): st.markdown("**🎥 Prompt Video (Khóa kiểu tóc & họa tiết):**"); st.code(vid_p := scn.get('vid_p'), language="text"); safe_copy_button(vid_p, f"📋 Sao Chép Video Cảnh {idx}")
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
                    with st.spinner("⏳ Đang dựng đủ 4 cảnh AIDA..."):
                        create_scene_details(sc_id, st.session_state.last_mode, st.session_state.last_style)
                        st.session_state.active_script_id = sc_id
                        st.rerun()
                else: st.error(msg)

    st.markdown("--- \n##### ➕ **Gọi Thêm 5 Kịch Bản Mới**")
    cg1, cg2, cg3, cg4 = st.columns([1.5, 0.8, 1.2, 1.5])
    a_opts = ["🌟 Tự động mix", "⚡ Flash Sale & Deal hời", "🎭 Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Chia sẻ", "😂 Hài hước"]
    c_ang = cg1.selectbox("🧭 Chiến lược mới:", a_opts, key=f"ea_{st.session_state.reset_key}")
    c_num = cg2.number_input("Số diễn viên:", 1, 8, 1, key=f"en_{st.session_state.reset_key}")
    c_dur_choice = cg3.selectbox("⏳ Thời lượng:", ["Tự động (~24-30s)", "Tùy chỉnh (s)"], key=f"ed_{st.session_state.reset_key}")
    c_dur_str = f"Chính xác {cg3.number_input('Số giây:', 10, 300, 60, key=f'eds_{st.session_state.reset_key}')} giây." if "Tùy" in c_dur_choice else "Khoảng 24-30 giây."
    c_nar = cg4.selectbox("🎙 Thuyết minh:", ["Nhân vật xuất hiện (On-camera)", "🎙 Lồng tiếng ngoài (Off-screen)"], key=f"ena_{st.session_state.reset_key}")

    e_chars = []
    for i in range(c_num):
        c_r, c_i = st.columns([2, 1])
        e_role = c_r.text_input(f"Vai trò NV {i+1} mới:", key=f"er_{i}_{st.session_state.reset_key}")
        e_file = c_i.file_uploader(f"Ảnh NV {i+1}", type=["jpg", "png"], key=f"ef_{i}_{st.session_state.reset_key}", label_visibility="collapsed")
        if e_file: e_chars.append({"id": i+1, "role": e_role or "AI phân tích", "file": e_file})

    if st.button("🚀 Gọi Thêm 5 Kịch Bản Mới", type="primary", use_container_width=True):
        can_run, msg = check_usage_limit(st.session_state.current_email)
        if can_run:
            with st.spinner("⏳ Đang sáng tạo thêm 5 kịch bản..."):
                p_chars = [{"id": c["id"], "role": c["role"]} for c in e_chars] if e_chars else st.session_state.character_profiles
                new_sc = generate_more_scripts(c_ang, c_num, e_chars, c_nar, c_dur_str, p_chars)
                st.session_state.expanded_scripts.extend(new_sc)
                st.toast("✅ Đã sinh thêm 5 kịch bản!")
                time.sleep(0.5); st.rerun()
        else: st.error(msg)
