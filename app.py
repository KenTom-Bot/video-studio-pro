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
    div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important; color: white !important; border-radius: 8px !important; font-weight: bold; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

ADMIN_EMAIL = "binhnguyenmedia.vn@gmail.com"
ALL_MODULES = ["🛒 TikTok Shop", "👶 Mẹ & Bé", "📺 TVC Quảng Cáo", "🏡 Nhà Cửa", "🌿 Du Lịch", "🚗 Xe Cộ", "🍲 Ẩm Thực", "📖 Giáo Dục", "🧘 Chữa Lành", "🏢 Doanh Nghiệp"]
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
    default_acc = {ADMIN_EMAIL: {"contact": ADMIN_EMAIL, "roles": ["Tất cả thể loại"], "expires_at": "2099-12-31"}}
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(default_acc, f)
    except: pass
    return default_acc

def save_licensed_accounts(acc_dict):
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(acc_dict, f, ensure_ascii=False, indent=2)
    except: pass

# ==============================================================================
# 2. KHỞI TẠO BỘ NHỚ
# ==============================================================================
for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", load_licensed_accounts()),
    ("all_scripts", []), ("generated_details", {}), ("active_script_id", None),
    ("current_product_data", None), ("action_trigger", None), ("action_param", None)
]:
    if key not in st.session_state: st.session_state[key] = default_val

# ==============================================================================
# 3. SIDEBAR (ĐĂNG NHẬP & QUẢN TRỊ)
# ==============================================================================
with st.sidebar:
    st.markdown("### 🔐 HỆ THỐNG ĐĂNG NHẬP")
    if not st.session_state.is_logged_in:
        email_input = st.text_input("Nhập Email / SĐT đã cấp quyền:")
        if st.button("🔑 Đăng Nhập", type="primary"):
            if email_input.strip() in st.session_state.licensed_accounts:
                st.session_state.is_logged_in = True
                st.session_state.current_email = email_input.strip()
                st.rerun()
            else: st.error("Tài khoản chưa được cấp quyền!")
    else:
        st.success(f"Đang đăng nhập: **{st.session_state.current_email}**")
        if st.button("🚪 Đăng Xuất"):
            st.session_state.is_logged_in = False
            st.rerun()
        
        if st.session_state.current_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙️ QUẢN TRỊ VIÊN")
            with st.form("add_license"):
                new_acc = st.text_input("Cấp quyền cho Email mới:")
                if st.form_submit_button("💾 Cấp Quyền"):
                    st.session_state.licensed_accounts[new_acc.strip()] = {"roles": ALL_MODULES, "expires_at": "2099-12-31"}
                    save_licensed_accounts(st.session_state.licensed_accounts)
                    st.success(f"Đã cấp cho {new_acc}")

if not st.session_state.is_logged_in:
    st.info("👈 Vui lòng đăng nhập ở thanh công cụ bên trái để sử dụng hệ thống Studio Pro.")
    st.stop()

# ==============================================================================
# 4. HÀM AI LÕI & LƯU DB
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

def get_system_instructions(mode, style, aspect, goal):
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL ĐA NĂNG.
    - PHONG CÁCH: {style}
    - ĐỊNH DẠNG: {aspect}
    - MỤC TIÊU: {goal}
    QUY TẮC: 1. Trả về JSON hợp lệ. 2. Các phân cảnh (nếu có) phải chia chính xác 8s hoặc 10s cho Veo 3. 3. Ghi rõ chuyển động camera.
    """

def create_scene_details(target_id, mode, style, aspect, goal):
    outline = next((sc for sc in st.session_state.all_scripts if sc["id"] == target_id), None)
    if not outline: return
    prompt = f"Viết chi tiết cho ID {target_id}: '{outline.get('title')}'. Hook: {outline.get('target_hook')}. Bối cảnh: {outline.get('setting_style')}. Trả JSON key 'scenes' (duration, voiceover_vi, image_prompt, video_prompt)."
    sys_inst = get_system_instructions(mode, style, aspect, goal)
    res = call_gemini([prompt], sys_inst)
    st.session_state.generated_details[target_id] = res

def save_project_to_db(email, title, content_list):
    if not supabase: return False
    try:
        data = {"user_email": email, "project_title": title, "script_content": content_list}
        supabase.table("saved_projects").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi lưu: {e}")
        return False

# ==============================================================================
# XỬ LÝ NÚT BẤM ĐỘNG (ACTION TRIGGER)
# ==============================================================================
if st.session_state.action_trigger == "create_detail":
    param = st.session_state.action_param
    st.session_state.action_trigger = None
    with st.spinner(f"Đang dựng chi tiết phân cảnh #{param}..."):
        create_scene_details(param, "TikTok", "Điện ảnh", "9:16", "Sales")
        st.session_state.active_script_id = param
    st.rerun()

# ==============================================================================
# 5. GIAO DIỆN CHÍNH (TABS)
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div></div>""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["✨ KHÔNG GIAN SÁNG TẠO", "📂 KHO LƯU TRỮ & QUẢN TRỊ"])

with tab1:
    st.markdown("## 📊 Creator Dashboard & Chọn Sản Phẩm")
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Video đã đăng", "217", "+12")
        c2.metric("GMV (Doanh thu)", "45.2 Triệu", "+5.4M")
        c3.metric("Tỷ lệ chuyển đổi", "3.2%", "+0.4%")
        c4.metric("Angle tốt nhất", "Review & Test", "Chốt đơn cao nhất")

    if supabase:
        try: products_data = supabase.table("products").select("*").execute().data
        except: products_data = []
        
        if products_data:
            prod_names = [p["product_name"] for p in products_data]
            selected_name = st.selectbox("📌 Tự động hóa Insight: Chọn sản phẩm từ Database", options=prod_names)
            st.session_state.current_product_data = next(p for p in products_data if p["product_name"] == selected_name)
            prod = st.session_state.current_product_data
            
            with st.container(border=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**💰 Hoa hồng:** <span style='color:#15803d; font-weight:900;'>{prod.get('commission_percent', 0)}%</span>", unsafe_allow_html=True)
                    st.markdown(f"**🎯 Khách hàng:** {prod.get('target_audience', '')}")
                with col_b:
                    st.markdown(f"**🧠 Insight:** {prod.get('product_insight', '')}")
                    st.markdown(f"**💔 Nỗi đau:** {prod.get('pain_points', '')}")
    
    st.markdown("---")
    st.markdown("### ⚙️ Cấu hình Kịch bản & Nguồn ảnh")
    col_m, col_s, col_r = st.columns(3)
    with col_m: mode = st.selectbox("Thể loại:", ALL_MODULES)
    with col_s: style = st.selectbox("Phong cách:", ["Điện Ảnh Chân Thực", "Hoạt Hình 3D", "Studio Tối Giản"])
    with col_r: aspect = st.selectbox("Khung hình:", ["9:16", "16:9"])

    up_files = st.file_uploader("📦 Ảnh sản phẩm / Bối cảnh tham chiếu:", type=["jpg", "png"], accept_multiple_files=True)
    custom_note = st.text_area("✍️ Ghi chú thêm cho AI:")
    project_name = st.text_input("💾 Tên dự án (Để lưu trữ):", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}")

    if st.button("🚀 Sinh 5 Kịch Bản Đa Vũ Trụ", type="primary", use_container_width=True):
        with st.spinner("Đang phân tích DNA Sản phẩm và sinh kịch bản..."):
            prod_ctx = f"THÔNG TIN SP: {json.dumps(st.session_state.current_product_data, ensure_ascii=False)}" if st.session_state.current_product_data else ""
            prompt = f"{prod_ctx}\nGHI CHÚ: {custom_note}\nTạo 5 kịch bản ngắn. Format JSON chứa key 'script_outlines', mỗi phần tử có: id, title, setting_style, target_hook."
            
            payload = [types.Part.from_bytes(data=f.getvalue(), mime_type=f.type) for f in up_files] if up_files else []
            payload.append(prompt)
            
            res = call_gemini(payload, get_system_instructions(mode, style, aspect, "Bán hàng"))
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.generated_details = {}
            st.session_state.active_script_id = None
            st.rerun()

    # KHU VỰC SPLIT SCREEN HIỂN THỊ KỊCH BẢN
    if st.session_state.all_scripts and st.session_state.active_script_id is None:
        st.divider()
        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.markdown("### 🎬 Danh sách kịch bản")
            for sc in st.session_state.all_scripts:
                sc_id = sc.get("id", 0)
                with st.container(border=True):
                    status = "<span class='badge-ready'>ĐÃ CHI TIẾT</span>" if sc_id in st.session_state.generated_details else "<span class='badge-pending'>ĐANG CHỜ</span>"
                    st.markdown(f"**#{sc_id}. {sc.get('title')}** {status}", unsafe_allow_html=True)
                    st.caption(f"⚡ Hook: {sc.get('target_hook')}")
                    
                    if sc_id in st.session_state.generated_details:
                        if st.button("👁️ Xem chi tiết", key=f"view_{sc_id}"):
                            st.session_state.active_script_id = sc_id
                            st.rerun()
                    else:
                        if st.button("✨ Phân cảnh chi tiết", key=f"cre_{sc_id}", type="primary"):
                            st.session_state.action_trigger = "create_detail"
                            st.session_state.action_param = sc_id
                            st.rerun()
        
        with c_right:
            st.markdown("### 💾 Quản lý Dự án")
            st.info("Khi đã ưng ý với các kịch bản bên trái, bạn có thể lưu lại toàn bộ vào cơ sở dữ liệu để xem lại sau.")
            if st.button("💾 LƯU DỰ ÁN NÀY VÀO KHO TRỮ", type="primary", use_container_width=True):
                if save_project_to_db(st.session_state.current_email, project_name, st.session_state.all_scripts):
                    st.success("✅ Đã lưu thành công! Hãy sang tab 'Kho Lưu Trữ & Quản Trị' để xem.")

    # XEM CHI TIẾT 1 KỊCH BẢN
    if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details:
        st.divider()
        if st.button("⬅️ Quay lại danh sách"):
            st.session_state.active_script_id = None
            st.rerun()
        
        active_sc = st.session_state.generated_details[st.session_state.active_script_id]
        if isinstance(active_sc, list): active_sc = active_sc[0] if active_sc else {}
        
        st.markdown(f"### 🎬 CHI TIẾT: {active_sc.get('title', '')}")
        scenes = active_sc.get("scenes", [])
        if isinstance(scenes, dict): scenes = [scenes]
        for idx, scene in enumerate(scenes, 1):
            st.markdown(f"#### 📍 Cảnh {idx} ({scene.get('duration', '8s')})")
            st.markdown(f"**💬 Thoại:** `{scene.get('voiceover_vi', '')}`")
            if scene.get('image_prompt'): st.markdown(f"**🖼️ Prompt Ảnh (Imagen 3):** `{scene.get('image_prompt')}`")
            if scene.get('video_prompt'): st.markdown(f"**🎥 Prompt Video (Veo 3):** `{scene.get('video_prompt')}`")
            st.markdown("---")

# ==============================================================================
# 5. GIAO DIỆN CHÍNH (TABS)
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div></div>""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["✨ KHÔNG GIAN SÁNG TẠO", "📂 KHO LƯU TRỮ & QUẢN TRỊ"])

with tab1:
    st.markdown("## 📊 Creator Dashboard & Chọn Sản Phẩm")
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Video đã đăng", "217", "+12")
        c2.metric("GMV (Doanh thu)", "45.2 Triệu", "+5.4M")
        c3.metric("Tỷ lệ chuyển đổi", "3.2%", "+0.4%")
        c4.metric("Angle tốt nhất", "Review & Test", "Chốt đơn cao nhất")

    if supabase:
        try: products_data = supabase.table("products").select("*").execute().data
        except: products_data = []
        
        if products_data:
            prod_names = [p["product_name"] for p in products_data]
            selected_name = st.selectbox("📌 Tự động hóa Insight: Chọn sản phẩm từ Database", options=prod_names)
            st.session_state.current_product_data = next(p for p in products_data if p["product_name"] == selected_name)
            prod = st.session_state.current_product_data
            
            with st.container(border=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**💰 Hoa hồng:** <span style='color:#15803d; font-weight:900;'>{prod.get('commission_percent', 0)}%</span>", unsafe_allow_html=True)
                    st.markdown(f"**🎯 Khách hàng:** {prod.get('target_audience', '')}")
                with col_b:
                    st.markdown(f"**🧠 Insight:** {prod.get('product_insight', '')}")
                    st.markdown(f"**💔 Nỗi đau:** {prod.get('pain_points', '')}")
    
    st.markdown("---")
    st.markdown("### ⚙️ Cấu hình Kịch bản & Nguồn ảnh")
    col_m, col_s, col_r = st.columns(3)
    with col_m: mode = st.selectbox("Thể loại:", ALL_MODULES)
    with col_s: style = st.selectbox("Phong cách:", ["Điện Ảnh Chân Thực", "Hoạt Hình 3D", "Studio Tối Giản"])
    with col_r: aspect = st.selectbox("Khung hình:", ["9:16", "16:9"])

    up_files = st.file_uploader("📦 Ảnh sản phẩm / Bối cảnh tham chiếu:", type=["jpg", "png"], accept_multiple_files=True)
    custom_note = st.text_area("✍️ Ghi chú thêm cho AI:")
    project_name = st.text_input("💾 Tên dự án (Để lưu trữ):", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}")

    if st.button("🚀 Sinh 5 Kịch Bản Đa Vũ Trụ", type="primary", use_container_width=True):
        with st.spinner("Đang phân tích DNA Sản phẩm và sinh kịch bản..."):
            prod_ctx = f"THÔNG TIN SP: {json.dumps(st.session_state.current_product_data, ensure_ascii=False)}" if st.session_state.current_product_data else ""
            prompt = f"{prod_ctx}\nGHI CHÚ: {custom_note}\nTạo 5 kịch bản ngắn. Format JSON chứa key 'script_outlines', mỗi phần tử có: id, title, setting_style, target_hook."
            
            payload = [types.Part.from_bytes(data=f.getvalue(), mime_type=f.type) for f in up_files] if up_files else []
            payload.append(prompt)
            
            res = call_gemini(payload, get_system_instructions(mode, style, aspect, "Bán hàng"))
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.generated_details = {}
            st.session_state.active_script_id = None
            st.rerun()

    # KHU VỰC SPLIT SCREEN HIỂN THỊ KỊCH BẢN
    if st.session_state.all_scripts and st.session_state.active_script_id is None:
        st.divider()
        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.markdown("### 🎬 Danh sách kịch bản")
            for sc in st.session_state.all_scripts:
                sc_id = sc.get("id", 0)
                with st.container(border=True):
                    status = "<span class='badge-ready'>ĐÃ CHI TIẾT</span>" if sc_id in st.session_state.generated_details else "<span class='badge-pending'>ĐANG CHỜ</span>"
                    st.markdown(f"**#{sc_id}. {sc.get('title')}** {status}", unsafe_allow_html=True)
                    st.caption(f"⚡ Hook: {sc.get('target_hook')}")
                    
                    if sc_id in st.session_state.generated_details:
                        if st.button("👁️ Xem chi tiết", key=f"view_{sc_id}"):
                            st.session_state.active_script_id = sc_id
                            st.rerun()
                    else:
                        if st.button("✨ Phân cảnh chi tiết", key=f"cre_{sc_id}", type="primary"):
                            st.session_state.action_trigger = "create_detail"
                            st.session_state.action_param = sc_id
                            st.rerun()
        
        with c_right:
            st.markdown("### 💾 Quản lý Dự án")
            st.info("Khi đã ưng ý với các kịch bản bên trái, bạn có thể lưu lại toàn bộ vào cơ sở dữ liệu để xem lại sau.")
            if st.button("💾 LƯU DỰ ÁN NÀY VÀO KHO TRỮ", type="primary", use_container_width=True):
                if save_project_to_db(st.session_state.current_email, project_name, st.session_state.all_scripts):
                    st.success("✅ Đã lưu thành công! Hãy sang tab 'Kho Lưu Trữ & Quản Trị' để xem.")

    # XEM CHI TIẾT 1 KỊCH BẢN
    if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details:
        st.divider()
        if st.button("⬅️ Quay lại danh sách"):
            st.session_state.active_script_id = None
            st.rerun()
        
        active_sc = st.session_state.generated_details[st.session_state.active_script_id]
        if isinstance(active_sc, list): active_sc = active_sc[0] if active_sc else {}
        
        st.markdown(f"### 🎬 CHI TIẾT: {active_sc.get('title', '')}")
        scenes = active_sc.get("scenes", [])
        if isinstance(scenes, dict): scenes = [scenes]
        for idx, scene in enumerate(scenes, 1):
            st.markdown(f"#### 📍 Cảnh {idx} ({scene.get('duration', '8s')})")
            st.markdown(f"**💬 Thoại:** `{scene.get('voiceover_vi', '')}`")
            if scene.get('image_prompt'): st.markdown(f"**🖼️ Prompt Ảnh (Imagen 3):** `{scene.get('image_prompt')}`")
            if scene.get('video_prompt'): st.markdown(f"**🎥 Prompt Video (Veo 3):** `{scene.get('video_prompt')}`")
            st.markdown("---")
