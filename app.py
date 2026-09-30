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
    .social-icons { display: flex; justify-content: center; gap: 25px; margin-top: 10px; margin-bottom: 5px; }
    .social-icons img { width: 42px; border-radius: 8px; transition: transform 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .social-icons img:hover { transform: scale(1.15); }
    .hotline-text { text-align: center; font-weight: 800; color: #d90429; font-size: 1.2rem; margin-bottom: 5px; }
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

for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", load_licensed_accounts()),
    ("all_scripts", []), ("generated_details", {}), ("active_script_id", None),
    ("current_product_data", None), ("action_trigger", None), ("action_param", None),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}")
]:
    if key not in st.session_state: st.session_state[key] = default_val

# ==============================================================================
# 2. HÀM AI LÕI & DATABASE
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
    2. TÍNH VẬT LÝ THỰC TẾ: Trong prompt video Veo 3, BẮT BUỘC miêu tả chi tiết tương tác vật lý (gió thổi làm bay tóc, đổ bóng, trọng lực, khói/nước).
    {char_rules}
    4. SẢN PHẨM THỰC TẾ: Phải giữ nguyên 100% hình dáng gốc (Lệnh: 'Maintain exact original product appearance').
    5. CƠ CHẾ GIỌNG NÓI & BIỂU CẢM: {narrator_mode}. Lời thoại phải khớp khẩu hình.
    6. THỜI LƯỢNG VEO 3 BẮT BUỘC: 4s, 6s, 8s, hoặc 10s (Không dùng số lẻ).
    7. CHUYỂN ĐỘNG CAMERA: Chỉ định rõ (Pan, Tilt, Zoom in/out, Tracking shot, Close-up).
    """

def create_scene_details(target_id, mode, style, aspect, narrator_mode, char_rules):
    outline = next((sc for sc in st.session_state.all_scripts if sc["id"] == target_id), None)
    if not outline: return
    prompt = f"Viết chi tiết kịch bản ID {target_id}: '{outline.get('title')}'. Hook: {outline.get('target_hook')}. Trả JSON key 'scenes' (duration, voiceover_vi, image_prompt, video_prompt)."
    res = call_gemini([prompt], get_system_instructions(mode, style, aspect, narrator_mode, char_rules))
    st.session_state.generated_details[target_id] = res

def save_project_to_db(email, title, content_list):
    if not supabase: return False
    try:
        data = {"user_email": email, "project_title": title, "script_content": content_list}
        supabase.table("saved_projects").insert(data).execute()
        return True
    except: return False


# ==============================================================================
# 3. THANH BÊN (SIDEBAR) - TỐI ƯU UX
# ==============================================================================
with st.sidebar:
    # --- 1. TÀI KHOẢN (TRÊN CÙNG) ---
    st.markdown("### 🔐 TÀI KHOẢN")
    if not st.session_state.is_logged_in:
        email_input = st.text_input("Nhập Email:", key="login_email_input")
        if st.button("🔑 Đăng Nhập", type="primary"):
            email_check = email_input.strip()
            if email_check in st.session_state.licensed_accounts:
                acc_info = st.session_state.licensed_accounts[email_check]
                exp_date_str = acc_info.get("expires_at", "2099-12-31")
                try:
                    if datetime.now() > datetime.strptime(exp_date_str, "%Y-%m-%d"):
                        st.error(f"❌ Tài khoản hết hạn: {exp_date_str}!")
                        st.stop()
                except: pass
                st.session_state.is_logged_in = True
                st.session_state.current_email = email_check
                st.toast("✅ Đăng nhập thành công!")
                st.rerun()
            else: 
                st.error("Tài khoản chưa được cấp quyền!")
                st.toast("❌ Đăng nhập thất bại!")
    else:
        st.success(f"Đang dùng: {st.session_state.current_email}")
        if st.button("🚪 Đăng Xuất"):
            st.session_state.is_logged_in = False
            st.toast("✅ Đã đăng xuất thành công!")
            st.rerun()

    # --- KHU VỰC HIỂN THỊ KHI ĐÃ ĐĂNG NHẬP ---
    if st.session_state.is_logged_in:
        st.markdown("---")
        
        # 2. TẠO & LƯU DỰ ÁN
        st.markdown("### 🗂️ LÀM VIỆC")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True):
            st.session_state.all_scripts = []
            st.session_state.generated_details = {}
            st.session_state.active_script_id = None
            st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
            st.toast("✅ Đã mở không gian dự án mới!")
            st.rerun()
            
        st.session_state.active_project_title = st.text_input("Tên dự án hiện tại:", st.session_state.active_project_title, key="sidebar_proj_input")
        if st.button("💾 Lưu Dự Án Này", use_container_width=True):
            if not st.session_state.all_scripts:
                st.warning("⚠️ Chưa có kịch bản nào để lưu!")
            elif save_project_to_db(st.session_state.current_email, st.session_state.active_project_title, st.session_state.all_scripts):
                st.toast("✅ Đã lưu dự án vào Kho lưu trữ thành công!")
            else:
                st.error("❌ Lỗi khi lưu dự án.")
        
        st.markdown("---")
        
        # 3. KHO LƯU TRỮ
        st.markdown("### 📂 KHO LƯU TRỮ")
        if not supabase:
            st.error("Chưa kết nối Database.")
        else:
            try:
                if st.session_state.current_email == ADMIN_EMAIL:
                    res = supabase.table("saved_projects").select("*").order("created_at", desc=True).execute()
                else:
                    res = supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
                projects = res.data
            except: projects = []

            if not projects:
                st.info("Chưa có dự án nào.")
            else:
                for p in projects:
                    display_title = f"🎬 {p['project_title']}"
                    with st.expander(display_title):
                        st.caption(f"{p['created_at'][:10]}")
                        if st.session_state.current_email == ADMIN_EMAIL:
                            st.caption(f"Tạo bởi: {p['user_email']}")
                        saved_scripts = p.get("script_content", [])
                        for i, sc in enumerate(saved_scripts):
                            st.write(f"- {sc.get('title', 'Idea')}")
                        if st.button("🗑️ Xóa dự án này", key=f"del_proj_{p['id']}", use_container_width=True):
                            supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                            st.toast("✅ Đã xóa dự án thành công!")
                            st.rerun()

        # 4. QUẢN TRỊ ADMIN
        if st.session_state.current_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙️ QUẢN TRỊ ADMIN")
            with st.form("add_license"):
                new_acc = st.text_input("Email cấp quyền:")
                duration_opt = st.selectbox("Thời hạn:", ["Dùng thử 3 ngày", "1 Tháng", "6 Tháng", "1 Năm", "Vĩnh viễn"])
                if st.form_submit_button("💾 Cấp Quyền"):
                    exp_date = "2099-12-31" if "Vĩnh viễn" in duration_opt else (datetime.now() + timedelta(days=3 if "3 ngày" in duration_opt else int(duration_opt.split()[0])*30)).strftime("%Y-%m-%d")
                    st.session_state.licensed_accounts[new_acc.strip()] = {"roles": ALL_MODULES, "expires_at": exp_date}
                    save_licensed_accounts(st.session_state.licensed_accounts)
                    st.toast(f"✅ Đã cấp quyền thành công cho {new_acc}!")

    # --- 5. HỖ TRỢ LIÊN HỆ (LUÔN Ở DƯỚI CÙNG SIDEBAR) ---
    st.markdown("---")
    st.markdown("### 🎧 HỖ TRỢ")
    st.markdown("""
    <div class="hotline-text">📞 0968.484.369</div>
    <div class="social-icons">
        <a href="#" target="_blank"><img src="[https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg](https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg)" alt="Facebook"></a>
        <a href="#" target="_blank"><img src="[https://upload.wikimedia.org/wikipedia/en/a/a9/TikTok_logo.svg](https://upload.wikimedia.org/wikipedia/en/a/a9/TikTok_logo.svg)" alt="TikTok"></a>
        <a href="#" target="_blank"><img src="[https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Icon_of_Zalo.svg/512px-Icon_of_Zalo.svg.png](https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Icon_of_Zalo.svg/512px-Icon_of_Zalo.svg.png)" alt="Zalo"></a>
    </div>
    """, unsafe_allow_html=True)
    
if not st.session_state.is_logged_in:
    st.info("👈 Vui lòng đăng nhập ở thanh công cụ bên trái.")
    st.stop()

# ==============================================================================
# XỬ LÝ NÚT BẤM ĐỘNG AI
# ==============================================================================
if st.session_state.action_trigger == "create_detail":
    param = st.session_state.action_param
    st.session_state.action_trigger = None
    with st.spinner(f"Đang dựng kịch bản Veo 3 chi tiết..."):
        char_rules = generate_char_rules_string(st.session_state.get("character_profiles", []))
        create_scene_details(param, st.session_state.get("last_mode", ""), st.session_state.get("last_style", ""), st.session_state.get("last_aspect", ""), st.session_state.get("last_narrator", ""), char_rules)
        st.session_state.active_script_id = param
        st.toast("✅ Đã tạo kịch bản chi tiết thành công!")
    st.rerun()

# ==============================================================================
# 4. KHÔNG GIAN SÁNG TẠO (MÀN HÌNH MẶC ĐỊNH)
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div></div>""", unsafe_allow_html=True)

st.markdown("## 📊 Tự Động Hóa Dữ Liệu Sản Phẩm")
if supabase:
    try: products_data = supabase.table("products").select("*").execute().data
    except: products_data = []
    
    if products_data:
        prod_names = [p["product_name"] for p in products_data]
        selected_name = st.selectbox("📌 Chọn sản phẩm từ Database:", options=prod_names, key="select_prod_main")
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
with col_m: mode = st.selectbox("🎯 Thể loại (Chỉ đạo cốt lõi):", ALL_MODULES, key="mode_sel")
with col_s: style = st.selectbox("🎨 Phong cách hình ảnh:", ["Điện Ảnh Chân Thực", "Hoạt Hình 3D", "Hoạt Hình 2D / Anime", "Studio Tối Giản"], key="style_sel")
with col_r: aspect = st.selectbox("Khung hình:", ["9:16 (Dọc TikTok/Reels)", "16:9 (Ngang YouTube)"], key="aspect_sel")

narrator_mode = st.selectbox("🎙️ Thuyết minh & Nhân vật:", ["Nhân vật xuất hiện nói chuyện (On-camera, Lip-sync)", "🎙️ Lồng tiếng ngoài (Off-screen, Show sản phẩm)"], key="narrator_sel")

col_p_img, col_c_img = st.columns([1, 1])
with col_p_img:
    up_files = st.file_uploader("📦 Ảnh SP/Bối cảnh (Sẽ được AI giữ nguyên gốc 100%):", type=["jpg", "png"], accept_multiple_files=True, key="up_main_files")
with col_c_img:
    num_chars = st.number_input("👤 Số lượng Diễn viên (Tối đa 8):", min_value=0, max_value=8, step=1, key="num_chars_main")

# Hiển thị nhân vật tối đa 8 người
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

custom_note = st.text_area("✍️ Ghi chú đặc biệt cho AI:", key="note_main")

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
        
        try:
            res = call_gemini(payload, get_system_instructions(mode, style, aspect, narrator_mode, char_rules))
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.generated_details = {}
            st.session_state.active_script_id = None
            st.toast("✅ Đã sinh xong 5 kịch bản thành công!")
        except Exception as e:
            st.error("❌ Lỗi khi sinh kịch bản. Vui lòng thử lại!")
        st.rerun()

# ==============================================================================
# DANH SÁCH KỊCH BẢN & XEM CHI TIẾT
# ==============================================================================
if st.session_state.all_scripts and st.session_state.active_script_id is None:
    st.divider()
    st.markdown("### 🎬 Danh sách Ý Tưởng AI")
    for sc in st.session_state.all_scripts:
        sc_id = sc.get("id", 0)
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                status = "<span class='badge-ready'>ĐÃ CHI TIẾT</span>" if sc_id in st.session_state.generated_details else "<span class='badge-pending'>ĐANG CHỜ</span>"
                st.markdown(f"**#{sc_id}. {sc.get('title')}** {status}", unsafe_allow_html=True)
                st.caption(f"⚡ Hook: {sc.get('target_hook')}")
            with col2:
                if sc_id in st.session_state.generated_details:
                    if st.button("👁️ Xem chi tiết", key=f"view_{sc_id}", use_container_width=True):
                        st.session_state.active_script_id = sc_id
                        st.toast("✅ Đang mở chi tiết kịch bản!")
                        st.rerun()
                else:
                    if st.button("✨ Đạo diễn phân cảnh", key=f"cre_{sc_id}", type="primary", use_container_width=True):
                        st.session_state.action_trigger = "create_detail"
                        st.session_state.action_param = sc_id
                        st.toast("⏳ Đang gửi yêu cầu phân cảnh...")
                        st.rerun()

if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details:
    st.divider()
    if st.button("⬅️ Quay lại danh sách tổng"):
        st.session_state.active_script_id = None
        st.toast("✅ Đã quay lại danh sách!")
        st.rerun()
    
    active_sc = st.session_state.generated_details[st.session_state.active_script_id]
    if isinstance(active_sc, list): active_sc = active_sc[0] if active_sc else {}
    
    st.markdown(f"### 🎬 CHI TIẾT: {active_sc.get('title', '')}")
    scenes = active_sc.get("scenes", [])
    if isinstance(scenes, dict): scenes = [scenes]
    for idx, scene in enumerate(scenes, 1):
        st.markdown(f"#### 📍 Cảnh {idx} ({scene.get('duration', '8s')})")
        st.markdown(f"**💬 Thoại & Âm thanh:** `{scene.get('voiceover_vi', '')}`")
        if scene.get('image_prompt'): st.markdown(f"**🖼️️ Prompt Ảnh (Imagen 3):** `{scene.get('image_prompt')}`")
        if scene.get('video_prompt'): st.markdown(f"**🎥 Prompt Video (Veo 3):** `{scene.get('video_prompt')}`")
        st.markdown("---")
