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
from datetime import datetime, timedelta

# ==============================================================================
# 1. CẤU HÌNH GIAO DIỆN & KẾT NỐI
# ==============================================================================
st.set_page_config(page_title="Universal AI Video Studio Pro", page_icon="🎬", layout="wide")

st.markdown("""
<style>
    .header-container { text-align: center; padding: 1.2rem; background: radial-gradient(circle, rgba(255,75,75,0.08) 0%, rgba(255,255,255,0) 70%); border-radius: 16px; margin-bottom: 1rem; }
    .main-title { font-size: 2.2rem !important; font-weight: 900 !important; background: linear-gradient(90deg, #ff0050 0%, #ff5252 50%, #ff7300 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important; color: white !important; border-radius: 8px !important; font-weight: bold; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .support-box { background: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; margin-top: 10px; }
    .support-box a { text-decoration: none; font-weight: 600; color: #0284c7; }
</style>
""", unsafe_allow_html=True)

ALL_MODULES = ["🛒 TikTok Shop & Bán Hàng", "🌟 Viral & Xây Kênh"]
ADMIN_EMAIL = "binhnguyenmedia.vn@gmail.com"
ACCOUNTS_FILE = "accounts.json"

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
    default_acc = {ADMIN_EMAIL: {"roles": ALL_MODULES, "expires_at": "2099-12-31"}}
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(default_acc, f)
    except: pass
    return default_acc

def save_licensed_accounts(acc_dict):
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(acc_dict, f, ensure_ascii=False, indent=2)
    except: pass

# Khởi tạo bộ nhớ
for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", load_licensed_accounts()),
    ("all_scripts", []), ("generated_details", {}), ("active_script_id", None),
    ("current_product_data", None), ("action_trigger", None), ("action_param", None),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}")
]:
    if key not in st.session_state: st.session_state[key] = default_val

# ==============================================================================
# 2. THANH BÊN (SIDEBAR) BỐ CỤC MỚI
# ==============================================================================
with st.sidebar:
    # --- KHU VỰC 1: QUẢN LÝ DỰ ÁN (ĐẨY LÊN TRÊN CÙNG) ---
    if st.session_state.is_logged_in:
        st.markdown("### 🗂️ QUẢN LÝ DỰ ÁN")
        st.session_state.active_project_title = st.text_input("💾 Tên dự án (Lưu trữ Database):", st.session_state.active_project_title)
        st.markdown("---")

    # --- KHU VỰC 2: TÀI KHOẢN & ĐĂNG NHẬP (CHUYỂN XUỐNG DƯỚI) ---
    st.markdown("### 🔐 TÀI KHOẢN HỆ THỐNG")
    if not st.session_state.is_logged_in:
        email_input = st.text_input("Nhập Email đã cấp quyền:")
        if st.button("🔑 Đăng Nhập", type="primary"):
            email_check = email_input.strip()
            if email_check in st.session_state.licensed_accounts:
                acc_info = st.session_state.licensed_accounts[email_check]
                exp_date_str = acc_info.get("expires_at", "2099-12-31")
                try:
                    if datetime.now() > datetime.strptime(exp_date_str, "%Y-%m-%d"):
                        st.error(f"❌ Tài khoản đã hết hạn vào ngày {exp_date_str}!")
                        st.stop()
                except: pass
                st.session_state.is_logged_in = True
                st.session_state.current_email = email_check
                st.rerun()
            else: st.error("Tài khoản chưa được cấp quyền!")
    else:
        st.success(f"Đang dùng: **{st.session_state.current_email}**")
        if st.button("🚪 Đăng Xuất"):
            st.session_state.is_logged_in = False
            st.rerun()
        
        # --- QUẢN TRỊ ADMIN ---
        if st.session_state.current_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙️ CẤP QUYỀN ADMIN")
            with st.form("add_license"):
                new_acc = st.text_input("Email khách hàng mới:")
                duration_opt = st.selectbox("Thời hạn:", ["Dùng thử 3 ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "Vĩnh viễn"])
                if st.form_submit_button("💾 Cấp Quyền"):
                    exp_date = "2099-12-31" if "Vĩnh viễn" in duration_opt else (datetime.now() + timedelta(days=3 if "3 ngày" in duration_opt else int(duration_opt.split()[0])*30)).strftime("%Y-%m-%d")
                    st.session_state.licensed_accounts[new_acc.strip()] = {"roles": ALL_MODULES, "expires_at": exp_date}
                    save_licensed_accounts(st.session_state.licensed_accounts)
                    st.success(f"Đã cấp quyền cho {new_acc} (Hết hạn: {exp_date})")

    # --- KHU VỰC 3: HỖ TRỢ (THÊM MỚI Ở DƯỚI CÙNG) ---
    st.markdown("---")
    st.markdown("### 🎧 LIÊN HỆ HỖ TRỢ")
    st.markdown("""
    <div class="support-box">
        <p>📞 <b>Hotline/Zalo:</b> 090.xxx.xxxx</p>
        <p>🌐 <b>Facebook:</b> <a href="#" target="_blank">Bình Nguyễn Media</a></p>
        <p>🎵 <b>TikTok:</b> <a href="#" target="_blank">@binhnguyenmedia</a></p>
        <p>✉️ <b>Email:</b> hotro@binhnguyenmedia.vn</p>
    </div>
    """, unsafe_allow_html=True)

if not st.session_state.is_logged_in:
    st.info("👈 Vui lòng đăng nhập ở thanh công cụ bên trái.")
    st.stop()

# ==============================================================================
# 3. LÕI ĐẠO DIỄN AI 
# ==============================================================================
def clean_json(text):
    cleaned = re.sub(r'```(?:json)?', '', text).strip()
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    try:
        parsed = json.loads(match.group(0) if match else cleaned)
        return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else parsed
    except: return {}

def call_gemini(contents, sys_inst):
    res = client.models.generate_content(
        model="gemini-3.6-flash", contents=contents,
        config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.7)
    )
    return clean_json(res.text)

def generate_char_rules_string(profiles):
    if not profiles: return "3. NHÂN VẬT: Linh hoạt theo kịch bản."
    rules = "3. KHÓA KHUÔN MẶT KOC VÀ ĐỒNG NHẤT NHÂN VẬT:\n"
    for p in profiles:
        rules += f"   + Nhân vật {p['id']} ({p['role']}): BẮT BUỘC dùng lệnh 'Character {p['id']} featuring the exact identity of reference image {p['id']}'.\n"
    return rules

def get_system_instructions(mode, style, aspect, narrator_mode, char_rules):
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL ĐA NĂNG CHO VEO 3 VÀ IMAGEN 3.
    THỂ LOẠI: {mode} | PHONG CÁCH: {style} | ĐỊNH DẠNG: {aspect}
    
    🛑 QUY TẮC BẮT BUỘC KHÔNG ĐƯỢC VI PHẠM:
    1. TRẢ VỀ JSON HỢP LỆ.
    2. TÍNH VẬT LÝ THỰC TẾ: Trong prompt video Veo 3, BẮT BUỘC miêu tả chi tiết tương tác vật lý (gió thổi làm bay tóc/quần áo, đổ bóng, trọng lực, hiệu ứng khói/nước).
    {char_rules}
    4. SẢN PHẨM THỰC TẾ: Cấm AI tự bịa ra thiết kế sản phẩm. Phải giữ nguyên 100% hình dáng, màu sắc gốc (Lệnh: 'Maintain exact original product appearance from reference').
    5. CƠ CHẾ GIỌNG NÓI & BIỂU CẢM: {narrator_mode}. Lời thoại phải khớp khẩu hình và hành động.
    6. THỜI LƯỢNG VEO 3 BẮT BUỘC: Mỗi phân cảnh BẮT BUỘC quy định chính xác là 4s, 6s, 8s, hoặc 10s (Không dùng số lẻ).
    7. CHUYỂN ĐỘNG CAMERA: Chỉ định rõ (Pan, Tilt, Zoom in/out, Tracking shot, Close-up).
    """

def create_scene_details(target_id, mode, style, aspect, narrator_mode, char_rules):
    outline = next((sc for sc in st.session_state.all_scripts if sc["id"] == target_id), None)
    if not outline: return
    prompt = f"Viết chi tiết kịch bản ID {target_id}: '{outline.get('title')}'. Hook: {outline.get('target_hook')}. Trả JSON key 'scenes' (duration, voiceover_vi, image_prompt, video_prompt)."
    sys_inst = get_system_instructions(mode, style, aspect, narrator_mode, char_rules)
    res = call_gemini([prompt], sys_inst)
    st.session_state.generated_details[target_id] = res

def save_project_to_db(email, title, content_list):
    if not supabase: return False
    try:
        data = {"user_email": email, "project_title": title, "script_content": content_list}
        supabase.table("saved_projects").insert(data).execute()
        return True
    except: return False

# ==============================================================================
# XỬ LÝ NÚT BẤM ĐỘNG
# ==============================================================================
if st.session_state.action_trigger == "create_detail":
    param = st.session_state.action_param
    st.session_state.action_trigger = None
    with st.spinner(f"Đang dựng kịch bản Veo 3 chi tiết (Vật lý, Camera, Voiceover)..."):
        char_rules = generate_char_rules_string(st.session_state.get("character_profiles", []))
        create_scene_details(param, st.session_state.get("last_mode", ""), st.session_state.get("last_style", ""), st.session_state.get("last_aspect", ""), st.session_state.get("last_narrator", ""), char_rules)
        st.session_state.active_script_id = param
    st.rerun()

# ==============================================================================
# 4. GIAO DIỆN CHÍNH (TABS)
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div></div>""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["✨ KHÔNG GIAN SÁNG TẠO", "📂 KHO LƯU TRỮ DỰ ÁN"])

with tab1:
    st.markdown("## 📊 Tự Động Hóa Dữ Liệu Sản Phẩm")
    if supabase:
        try: products_data = supabase.table("products").select("*").execute().data
        except: products_data = []
        
        if products_data:
            prod_names = [p["product_name"] for p in products_data]
            selected_name = st.selectbox("📌 Chọn sản phẩm từ Database:", options=prod_names)
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
    
    st.markdown("---")
    st.markdown("### ⚙️ Thiết Lập Đạo Diễn & Nguồn Ảnh")
    col_m, col_s, col_r = st.columns(3)
    with col_m: mode = st.selectbox("🎯 Thể loại (Chỉ đạo cốt lõi):", ALL_MODULES)
    with col_s: style = st.selectbox("🎨 Phong cách hình ảnh:", ["Điện Ảnh Chân Thực (Người thật / Siêu thực 8K)", "Hoạt Hình 3D (Pixar / Disney)", "Hoạt Hình 2D / Anime", "Studio Tối Giản"])
    with col_r: aspect = st.selectbox("Khung hình:", ["9:16 (Dọc TikTok/Reels)", "16:9 (Ngang YouTube)"])

    narrator_mode = st.selectbox("🎙️ Thuyết minh & Nhân vật:", ["Nhân vật xuất hiện nói chuyện (On-camera, Lip-sync)", "🎙️ Lồng tiếng ngoài (Off-screen, Show sản phẩm)"])

    col_p_img, col_c_img = st.columns([1, 1])
    with col_p_img:
        up_files = st.file_uploader("📦 Ảnh SP/Bối cảnh (Sẽ được AI giữ nguyên gốc 100%):", type=["jpg", "png"], accept_multiple_files=True)
    with col_c_img:
        num_chars = st.number_input("👤 Số lượng Diễn viên/KOC (Tối đa 8):", min_value=0, max_value=8, step=1)

    # Hiển thị nhân vật dạng Grid (4 cột / 1 hàng) để không bị méo UI
    char_inputs = []
    if num_chars > 0:
        for i in range(0, num_chars, 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < num_chars:
                    idx = i + j
                    with cols[j]:
                        c_role = st.text_input(f"Vai trò NV {idx+1}", key=f"role_{idx}")
                        c_file = st.file_uploader(f"Ảnh NV {idx+1}", type=["jpg", "png"], key=f"file_{idx}")
                        if c_file and c_role: char_inputs.append({"id": idx+1, "role": c_role, "file": c_file})

    custom_note = st.text_area("✍️ Ghi chú đặc biệt cho AI (Ví dụ: Angle hài hước, yêu cầu bão tuyết...):")

    if st.button("🚀 Sinh 5 Kịch Bản Đa Vũ Trụ", type="primary", use_container_width=True):
        with st.spinner("Phân tích AI: Tính toán vật lý, nhân vật, và insight sản phẩm..."):
            st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
            char_rules = generate_char_rules_string(st.session_state.character_profiles)
            
            st.session_state.last_mode, st.session_state.last_style, st.session_state.last_aspect, st.session_state.last_narrator = mode, style, aspect, narrator_mode
            
            prod_ctx = f"SẢN PHẨM: {json.dumps(st.session_state.current_product_data, ensure_ascii=False)}" if st.session_state.current_product_data else ""
            prompt = f"{prod_ctx}\nGHI CHÚ: {custom_note}\nTạo 5 kịch bản. Format JSON key 'script_outlines' (id, title, setting_style, target_hook)."
            
            payload = [types.Part.from_bytes(data=f.getvalue(), mime_type=f.type) for f in up_files] if up_files else []
            for c in char_inputs: payload.append(types.Part.from_bytes(data=c['file'].getvalue(), mime_type=c['file'].type))
            payload.append(prompt)
            
            res = call_gemini(payload, get_system_instructions(mode, style, aspect, narrator_mode, char_rules))
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.generated_details = {}
            st.session_state.active_script_id = None
            st.rerun()

    # ==========================================================================
    # KHU VỰC SPLIT SCREEN HIỂN THỊ KỊCH BẢN
    # ==========================================================================
    if st.session_state.all_scripts and st.session_state.active_script_id is None:
        st.divider()
        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.markdown("### 🎬 Danh sách Ý Tưởng AI")
            for sc in st.session_state.all_scripts:
                sc_id = sc.get("id", 0)
                with st.container(border=True):
                    status = "<span class='badge-ready'>ĐÃ CHI TIẾT</span>" if sc_id in st.session_state.generated_details else "<span class='badge-pending'>ĐANG CHỜ</span>"
                    st.markdown(f"**#{sc_id}. {sc.get('title')}** {status}", unsafe_allow_html=True)
                    st.caption(f"⚡ Hook: {sc.get('target_hook')}")
                    
                    if sc_id in st.session_state.generated_details:
                        if st.button("👁️ Xem chi tiết kịch bản", key=f"view_{sc_id}"):
                            st.session_state.active_script_id = sc_id
                            st.rerun()
                    else:
                        if st.button("✨ Đạo diễn phân cảnh (Veo 3)", key=f"cre_{sc_id}", type="primary"):
                            st.session_state.action_trigger = "create_detail"
                            st.session_state.action_param = sc_id
                            st.rerun()
        with c_right:
            st.markdown("### 💾 Lưu trữ Database")
            st.info("Lưu lại kịch bản AI vừa thiết kế vào hệ thống (Sử dụng tên dự án bạn đã đặt ở thanh bên trái).")
            if st.button("💾 LƯU TOÀN BỘ DỰ ÁN NÀY", type="primary", use_container_width=True):
                # Sử dụng tên dự án lấy từ Sidebar
                if save_project_to_db(st.session_state.current_email, st.session_state.active_project_title, st.session_state.all_scripts):
                    st.success("✅ Đã lưu thành công! Hãy kiểm tra tab 'Kho Lưu Trữ'.")

    # XEM CHI TIẾT KỊCH BẢN
    if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details:
        st.divider()
        if st.button("⬅️ Quay lại danh sách tổng"):
            st.session_state.active_script_id = None
            st.rerun()
        
        active_sc = st.session_state.generated_details[st.session_state.active_script_id]
        if isinstance(active_sc, list): active_sc = active_sc[0] if active_sc else {}
        
        st.markdown(f"### 🎬 CHI TIẾT: {active_sc.get('title', '')}")
        scenes = active_sc.get("scenes", [])
        if isinstance(scenes, dict): scenes = [scenes]
        for idx, scene in enumerate(scenes, 1):
            st.markdown(f"#### 📍 Cảnh {idx} ({scene.get('duration', '8s')})")
            st.markdown(f"**💬 Thoại & Âm thanh:** `{scene.get('voiceover_vi', '')}`")
            if scene.get('image_prompt'): st.markdown(f"**🖼️ Prompt Ảnh (Imagen 3):** `{scene.get('image_prompt')}`")
            if scene.get('video_prompt'): st.markdown(f"**🎥 Prompt Video (Veo 3 - Camera/Vật lý):** `{scene.get('video_prompt')}`")
            st.markdown("---")

# ==============================================================================
# 5. GIAO DIỆN KHO LƯU TRỮ DỰ ÁN
# ==============================================================================
with tab2:
    st.markdown("### 📂 Quản Lý & Xem Lại Dự Án")
    if not supabase:
        st.error("Chưa kết nối Database.")
    else:
        try:
            if st.session_state.current_email == ADMIN_EMAIL:
                st.write("👑 **Quyền Admin:** Đang hiển thị toàn bộ dự án trên hệ thống.")
                res = supabase.table("saved_projects").select("*").order("created_at", desc=True).execute()
            else:
                st.write("👤 **Quyền User:** Đang hiển thị không gian làm việc cá nhân của bạn.")
                res = supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
            
            projects = res.data
        except Exception as e:
            projects = []
            st.error(f"Lỗi tải dữ liệu: {e}")

        if not projects:
            st.info("Chưa có dự án nào được lưu.")
        else:
            for p in projects:
                display_title = f"🎬 {p['project_title']} | Tạo bởi: {p['user_email']}" if st.session_state.current_email == ADMIN_EMAIL else f"🎬 {p['project_title']}"
                
                with st.expander(display_title):
                    st.caption(f"Lưu lúc: {p['created_at']}")
                    
                    saved_scripts = p.get("script_content", [])
                    for i, sc in enumerate(saved_scripts):
                        st.markdown(f"**Ý tưởng #{sc.get('id', i+1)}: {sc.get('title', '')}**")
                        st.write(f"- Hook: {sc.get('target_hook', '')}")
                        st.write(f"- Bối cảnh: {sc.get('setting_style', '')}")
                        st.markdown("---")
                    
                    if st.button("🗑️ Xóa dự án này", key=f"del_proj_{p['id']}"):
                        supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                        st.toast("Đã xóa dự án!")
                        st.rerun()


