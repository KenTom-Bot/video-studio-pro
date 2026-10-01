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
    /* Vẽ Icon bằng CSS siêu bền, không bao giờ lỗi ảnh */
    .btn-zalo { background: #0068FF; color: white !important; font-weight: 900; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 15px; border: 1px solid #0056d6; }
    .btn-fb { background: #1877F2; color: white !important; font-weight: 900; padding: 8px 24px; border-radius: 8px; text-decoration: none; font-size: 16px; border: 1px solid #166fe5; font-family: serif; }
    .btn-tt { background: #000000; color: white !important; font-weight: 900; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 15px; border: 1px solid #333; }
    .social-icons-container { display: flex; gap: 12px; justify-content: center; margin-top: 10px; margin-bottom: 10px; }
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

# Khởi tạo bộ nhớ Session State toàn diện
for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", load_licensed_accounts()),
    ("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []), 
    ("generated_details", {}), ("product_analysis", None),
    ("active_script_id", None), ("current_product_data", None), 
    ("action_trigger", None), ("action_param", None),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}")
]:
    if key not in st.session_state: st.session_state[key] = default_val

# ==============================================================================
# 2. HÀM AI LÕI & CÁC CHỨC NĂNG ĐA VŨ TRỤ
# ==============================================================================
def clean_json(text):
    cleaned = re.sub(r'```(?:json)?', '', text).strip()
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    try:
        parsed = json.loads(match.group(0) if match else cleaned)
        return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else parsed
    except: return {}

def call_gemini(contents, sys_inst="Bạn là AI hỗ trợ JSON."):
    res = client.models.generate_content(
        model="gemini-3.6-flash", contents=contents,
        config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.7)
    )
    return clean_json(res.text)

def generate_char_rules_string(profiles):
    if not profiles: return "🔹 NHÂN VẬT: Linh hoạt theo kịch bản."
    rules = "🔹 KHÓA KHUÔN MẶT KOC:\n"
    for p in profiles:
        rules += f"   + Nhân vật {p['id']} ({p['role']}): Dùng lệnh 'Character {p['id']} featuring exact identity of reference image {p['id']}'.\n"
    return rules

def get_system_instructions(mode, style, aspect, narrator_mode, char_rules):
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL CHO VEO 3 VÀ IMAGEN 3.
    THỂ LOẠI: {mode} | PHONG CÁCH: {style} | ĐỊNH DẠNG: {aspect}
    
    🛑 QUY TẮC BẮT BUỘC KHÔNG ĐƯỢC VI PHẠM:
    1. TIÊU CHUẨN TIKTOK & AN TOÀN: Tuân thủ tuyệt đối quy tắc cộng đồng. An toàn 100% cho ngành Mẹ & Bé (Không để trẻ em một mình, không nguy hiểm, cấm lạm dụng từ y tế/cam kết chữa bệnh).
    2. CẤM BÁO GIÁ: Tuyệt đối KHÔNG đưa giá tiền cụ thể bằng con số vào kịch bản hay lời thoại.
    3. THỜI LƯỢNG VEO 3: Các phân cảnh CHỈ ĐƯỢC CHIA THÀNH 4s, 6s, 8s (TUYỆT ĐỐI KHÔNG DÙNG 10s).
    4. VẬT LÝ & SẢN PHẨM: Bắt buộc miêu tả vật lý (gió, đổ bóng). Giữ nguyên 100% sản phẩm gốc.
    5. GIỌNG NÓI & CHÍNH TẢ ({narrator_mode}): Lời thoại phải đúng chính tả 100%, từ ngữ rõ ràng, ngắt nghỉ chuẩn để AI Voice đọc không bị vấp/sai. Khớp khẩu hình nếu có nhân vật.
    6. CAMERA: Chỉ định góc máy rõ ràng. {char_rules}
    """

def analyze_product_dna(product_info, note, up_files):
    prompt = f"Thông tin SP: {product_info}. Ghi chú: {note}. Phân tích sâu và trả JSON chứa keys: 'pain_points' (Nỗi đau), 'customer_insight' (Sự thật ngầm hiểu), 'visual_hooks' (Khóa thị giác gây nghiện), 'core_message' (Thông điệp lõi)."
    payload = [types.Part.from_bytes(data=f.getvalue(), mime_type=f.type) for f in up_files] if up_files else []
    payload.append(prompt)
    return call_gemini(payload, "Bạn là Chuyên gia Tâm lý & Marketing.")

def clone_script(script_id):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if sc["id"] == script_id), None)
    if not target: return []
    cur_len = len(all_combined)
    prompt = f"Nhân bản kịch bản gốc: {json.dumps(target, ensure_ascii=False)}. Tạo 3 biến thể mới với hướng tiếp cận (Hook) khác nhau. Format JSON key 'script_outlines' (id bắt đầu từ {cur_len+1}, title, setting_style, target_hook)."
    res = call_gemini([prompt], get_system_instructions("Bán Hàng", "Điện ảnh", "9:16", "On-camera", ""))
    clones = res.get("script_outlines", [])
    for idx, cl in enumerate(clones): cl["id"] = cur_len + idx + 1
    return clones

def generate_more_scripts():
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    cur_len = len(all_combined)
    prod_ctx = f"SẢN PHẨM: {json.dumps(st.session_state.current_product_data, ensure_ascii=False)}" if st.session_state.current_product_data else ""
    prompt = f"{prod_ctx}\nTạo thêm 3 kịch bản MỚI HOÀN TOÀN, không trùng lặp các ý tưởng cũ. Format JSON key 'script_outlines' (id bắt đầu từ {cur_len+1}, title, setting_style, target_hook)."
    res = call_gemini([prompt], get_system_instructions("Bán Hàng", "Điện ảnh", "9:16", "On-camera", ""))
    more_scripts = res.get("script_outlines", [])
    for idx, sc in enumerate(more_scripts): sc["id"] = cur_len + idx + 1
    return more_scripts

def save_project_to_db(email, title, content_list):
    if not supabase: return False
    try:
        data = {"user_email": email, "project_title": title, "script_content": content_list}
        supabase.table("saved_projects").insert(data).execute()
        return True
    except: return False.


# ==============================================================================
# 3. THANH BÊN (SIDEBAR) - CHUẨN UX & ICON CSS
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        st.markdown("### 🔐 ĐĂNG NHẬP")
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
    else:
        # LÀM VIỆC & LƯU DỰ ÁN
        st.markdown("### 🗂️ LÀM VIỆC")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True):
            st.session_state.all_scripts, st.session_state.cloned_scripts, st.session_state.expanded_scripts = [], [], []
            st.session_state.generated_details, st.session_state.product_analysis = {}, None
            st.session_state.active_script_id = None
            st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
            st.toast("✅ Đã mở không gian dự án mới!")
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.session_state.active_project_title = st.text_input("Tên dự án hiện tại:", st.session_state.active_project_title)
        if st.button("💾 Lưu Dự Án Này", use_container_width=True):
            all_com = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
            if not all_com:
                st.warning("⚠️ Chưa có kịch bản nào để lưu!")
            elif save_project_to_db(st.session_state.current_email, st.session_state.active_project_title, all_com):
                st.toast("✅ Đã lưu dự án vào Kho lưu trữ thành công!")
            else:
                st.error("❌ Lỗi khi lưu dự án.")
        
        st.markdown("---")
        
        # KHO LƯU TRỮ
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
                        if st.button("🗑️ Xóa dự án này", key=f"del_{p['id']}", use_container_width=True):
                            supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                            st.toast("✅ Đã xóa dự án thành công!")
                            st.rerun()

        # QUẢN TRỊ ADMIN
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
                    st.toast(f"✅ Đã cấp quyền cho {new_acc}!")

        # HỖ TRỢ LIÊN HỆ (Icon CSS)
        st.markdown("---")
        st.markdown("### 🎧 HỖ TRỢ")
        st.markdown("""
        <div class="hotline-text">📞 0968.484.369</div>
        <div class="social-icons-container">
            <a href="#" class="btn-zalo" target="_blank">Zalo</a>
            <a href="#" class="btn-fb" target="_blank">f</a>
            <a href="#" class="btn-tt" target="_blank">♪</a>
        </div>
        """, unsafe_allow_html=True)
        
        # TÀI KHOẢN (DƯỚI CÙNG)
        st.markdown("---")
        st.markdown("### 🔐 TÀI KHOẢN")
        st.success(f"Đang dùng: {st.session_state.current_email}")
        if st.button("🚪 Đăng Xuất"):
            st.session_state.is_logged_in = False
            st.toast("✅ Đã đăng xuất thành công!")
            st.rerun()

if not st.session_state.is_logged_in:
    st.info("👈 Vui lòng đăng nhập ở thanh công cụ bên trái.")
    st.stop()

# ==============================================================================
# XỬ LÝ NÚT BẤM ĐỘNG AI (ĐA VŨ TRỤ)
# ==============================================================================
if st.session_state.action_trigger:
    action = st.session_state.action_trigger
    param = st.session_state.action_param
    st.session_state.action_trigger = None
    
    if action == "create_detail":
        with st.spinner(f"Đang dựng kịch bản Veo 3 chi tiết..."):
            char_rules = generate_char_rules_string(st.session_state.get("character_profiles", []))
            outline = next((sc for sc in st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts if sc["id"] == param), None)
            if outline:
                prompt = f"Viết chi tiết kịch bản ID {param}: '{outline.get('title')}'. Hook: {outline.get('target_hook')}. Trả JSON key 'scenes' (duration 4s, 6s, 8s, voiceover_vi, image_prompt, video_prompt)."
                res = call_gemini([prompt], get_system_instructions(st.session_state.get("last_mode", ""), st.session_state.get("last_style", ""), st.session_state.get("last_aspect", ""), st.session_state.get("last_narrator", ""), char_rules))
                st.session_state.generated_details[param] = res
                st.session_state.active_script_id = param
                st.toast("✅ Đã tạo kịch bản chi tiết thành công!")
    elif action == "clone_script":
        with st.spinner(f"Đang phân tích DNA và nhân bản 3 kịch bản Win từ ID {param}..."):
            new_clones = clone_script(param)
            st.session_state.cloned_scripts.extend(new_clones)
            st.toast("✅ Đã nhân bản kịch bản thành công!")
    elif action == "generate_more":
        with st.spinner("Đang mở rộng đa vũ trụ, sáng tạo thêm kịch bản mới..."):
            new_scripts = generate_more_scripts()
            st.session_state.expanded_scripts.extend(new_scripts)
            st.toast("✅ Đã sinh thêm kịch bản thành công!")
    st.rerun()

# ==============================================================================
# 4. KHÔNG GIAN SÁNG TẠO CHÍNH
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div></div>""", unsafe_allow_html=True)

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

# ==================== NÚT PHÂN TÍCH DNA SẢN PHẨM ====================
if st.button("🔍 PHÂN TÍCH DNA SẢN PHẨM & KHÁCH HÀNG", type="secondary", use_container_width=True):
    with st.spinner("Đang đào sâu tâm lý khách hàng và khóa thị giác..."):
        prod_ctx = json.dumps(st.session_state.current_product_data, ensure_ascii=False) if st.session_state.current_product_data else ""
        st.session_state.product_analysis = analyze_product_dna(prod_ctx, custom_note, up_files)
        st.toast("✅ Đã phân tích xong DNA Sản phẩm!")

if st.session_state.product_analysis:
    with st.container(border=True):
        st.markdown("#### 🧠 Kết Quả Phân Tích Chuyên Sâu")
        dna = st.session_state.product_analysis
        st.markdown(f"**💔 Nỗi đau khách hàng:** {dna.get('pain_points', '')}")
        st.markdown(f"**💡 Insight ngầm hiểu:** {dna.get('customer_insight', '')}")
        st.markdown(f"**👁️ Khóa thị giác gây nghiện:** {dna.get('visual_hooks', '')}")
        st.markdown(f"**🎯 Thông điệp lõi:** {dna.get('core_message', '')}")

st.markdown("<br>", unsafe_allow_html=True)

# ==================== NÚT SINH KỊCH BẢN ====================
if st.button("🚀 SINH 5 KỊCH BẢN ĐA VŨ TRỤ", type="primary", use_container_width=True):
    with st.spinner("Đạo diễn AI đang tính toán vật lý, nhân vật, và luật TikTok..."):
        st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
        char_rules = generate_char_rules_string(st.session_state.character_profiles)
        st.session_state.last_mode, st.session_state.last_style, st.session_state.last_aspect, st.session_state.last_narrator = mode, style, aspect, narrator_mode
        
        prod_ctx = f"SẢN PHẨM: {json.dumps(st.session_state.current_product_data, ensure_ascii=False)}" if st.session_state.current_product_data else ""
        dna_ctx = f"DNA: {json.dumps(st.session_state.product_analysis, ensure_ascii=False)}" if st.session_state.product_analysis else ""
        prompt = f"{prod_ctx}\n{dna_ctx}\nGHI CHÚ: {custom_note}\nTạo 5 kịch bản. Format JSON key 'script_outlines' (id, title, setting_style, target_hook)."
        
        payload = [types.Part.from_bytes(data=f.getvalue(), mime_type=f.type) for f in up_files] if up_files else []
        for c in char_inputs: payload.append(types.Part.from_bytes(data=c['file'].getvalue(), mime_type=c['file'].type))
        payload.append(prompt)
        
        try:
            res = call_gemini(payload, get_system_instructions(mode, style, aspect, narrator_mode, char_rules))
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.cloned_scripts, st.session_state.expanded_scripts = [], []
            st.session_state.generated_details, st.session_state.active_script_id = {}, None
            st.toast("✅ Đã sinh xong 5 kịch bản!")
        except Exception as e:
            st.error("❌ Lỗi sinh kịch bản. Vui lòng thử lại!")
        st.rerun()

# ==============================================================================
# DANH SÁCH KỊCH BẢN & XEM CHI TIẾT
# ==============================================================================
all_combined_scripts = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts

if all_combined_scripts and st.session_state.active_script_id is None:
    st.divider()
    st.markdown("### 🎬 Danh sách Kịch bản & Biến thể")
    for sc in all_combined_scripts:
        sc_id = sc.get("id", 0)
        with st.container(border=True):
            col1, col2, col3 = st.columns([2.5, 1, 1])
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
            with col3:
                if st.button("🚀 Nhân Bản (Clone)", key=f"clone_{sc_id}", use_container_width=True):
                    st.session_state.action_trigger = "clone_script"
                    st.session_state.action_param = sc_id
                    st.toast("⏳ Đang nhân bản ý tưởng Win...")
                    st.rerun()
    
    # NÚT GỌI THÊM KỊCH BẢN
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 GỌI THÊM 3 KỊCH BẢN MỚI", type="secondary", use_container_width=True):
        st.session_state.action_trigger = "generate_more"
        st.toast("⏳ Đang mở rộng đa vũ trụ...")
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
        st.markdown(f"**💬 Thoại & Âm thanh (Chuẩn chính tả):** `{scene.get('voiceover_vi', '')}`")
        if scene.get('image_prompt'): st.markdown(f"**🖼️ Prompt Ảnh (Imagen 3):** `{scene.get('image_prompt')}`")
        if scene.get('video_prompt'): st.markdown(f"**🎥 Prompt Video (Veo 3):** `{scene.get('video_prompt')}`")
        st.markdown("---")

