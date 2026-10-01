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
    .custom-card { background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
    .support-box { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1.5px solid #86efac; border-radius: 12px; padding: 12px; text-align: center; margin-top: 15px; }
    /* Icon CSS */
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
    return default_acc

def save_licensed_accounts(acc_dict):
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(acc_dict, f, ensure_ascii=False, indent=2)
    except: pass

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict): return "<br>".join([f"• <b>{str(k).replace('_', ' ').title()}:</b> {str(v)}" for k, v in field_val.items()])
    elif isinstance(field_val, list): return "<br>".join([f"• {str(item)}" for item in field_val])
    text = str(field_val).strip()
    text = re.sub(r'<<\.?', '', text).replace('<b>', '').replace('</b>', '')
    lines = [l.strip() for l in text.split('<br>') if l.strip()]
    formatted = [f"<div style='margin-top: 6px;'>{line}</div>" if line.startswith('•') else f"<div style='margin-left: 15px; margin-top: 4px;'>• {line}</div>" for line in lines if line]
    return "".join(formatted) if formatted else text

# Khởi tạo bộ nhớ (Thêm reset_key để làm mới toàn bộ Form/Ảnh)
for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", load_licensed_accounts()),
    ("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []),
    ("generated_details", {}), ("content_analysis", None), ("active_script_id", None),
    ("current_product_data", None), ("current_input_context", ""),
    ("action_trigger", None), ("action_param", None), ("reset_key", 0),
    ("extra_angle_type", "⚡ Dạng Flash Sale & Deal hời (Tập trung chốt đơn)"),
    ("extra_num_chars", 1), ("extra_duration_mins", 1.0),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}")
]:
    if key not in st.session_state: st.session_state[key] = default_val

# ==============================================================================
# 2. HÀM AI LÕI & CHÍNH SÁCH
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
    for p in profiles: rules += f"   + Nhân vật {p['id']} ({p['role']}): Dùng lệnh 'Character {p['id']} featuring exact identity of reference image {p['id']}'.\n"
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

def create_scene_details(target_id, mode, style, aspect, narrator_mode, char_rules):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_combined if sc["id"] == target_id), None)
    if not outline: return
    prompt = f"Viết chi tiết kịch bản ID {target_id}: '{outline.get('title')}'. Hook: {outline.get('target_hook')}. Trả JSON key 'scenes' (duration 4s/6s/8s, voiceover_vi, image_prompt, video_prompt)."
    res = call_gemini([prompt], get_system_instructions(mode, style, aspect, narrator_mode, char_rules))
    st.session_state.generated_details[target_id] = res

def clone_script(script_id):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    target = next((sc for sc in all_combined if sc["id"] == script_id), None)
    if not target: return []
    cur_len = len(all_combined)
    prompt = f"Nhân bản kịch bản gốc: {json.dumps(target, ensure_ascii=False)}. Tạo 5 biến thể mới. Format JSON key 'script_outlines' (id bắt đầu từ {cur_len+1}, title, setting_style, target_hook)."
    res = call_gemini([prompt], get_system_instructions("Bán Hàng", "Điện ảnh", "9:16", "On-camera", ""))
    clones = res.get("script_outlines", [])
    for idx, cl in enumerate(clones): cl["id"] = cur_len + idx + 1
    return clones

def generate_more_scripts(angle, num_chars, duration_mins):
    all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    cur_len = len(all_combined)
    prod_ctx = f"SẢN PHẨM: {json.dumps(st.session_state.current_product_data, ensure_ascii=False)}" if st.session_state.current_product_data else ""
    dna_ctx = f"DNA: {json.dumps(st.session_state.content_analysis, ensure_ascii=False)}" if st.session_state.content_analysis else ""
    prompt = f"{prod_ctx}\n{dna_ctx}\nYÊU CẦU MỚI: Thể loại '{angle}', {num_chars} nhân vật, thời lượng {duration_mins} phút.\nTạo thêm 5 kịch bản MỚI. Format JSON key 'script_outlines' (id bắt đầu từ {cur_len+1}, title, setting_style, target_hook)."
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
    except: return False


# ==============================================================================
# 3. THANH BÊN (SIDEBAR) - BỐ CỤC CHUẨN UX
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
        # 1. LÀM VIỆC & RESET HOÀN TOÀN DỮ LIỆU
        st.markdown("### 🗂️️ LÀM VIỆC")
        if st.button("➕ TẠO DỰ ÁN MỚI", type="primary", use_container_width=True):
            st.session_state.all_scripts, st.session_state.cloned_scripts, st.session_state.expanded_scripts = [], [], []
            st.session_state.generated_details, st.session_state.content_analysis = {}, None
            st.session_state.active_script_id = None
            st.session_state.active_project_title = f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}"
            st.session_state.reset_key += 1 # KÍCH HOẠT LÀM MỚI TOÀN BỘ ẢNH VÀ FORM NHẬP LIỆU
            st.toast("✅ Đã dọn dẹp và mở dự án mới sạch sẽ!")
            st.rerun()
            
        st.session_state.active_project_title = st.text_input("Tên dự án hiện tại:", st.session_state.active_project_title)
        if st.button("💾 Lưu Dự Án Này", use_container_width=True):
            all_com = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
            if not all_com: st.warning("⚠️ Chưa có kịch bản nào để lưu!")
            elif save_project_to_db(st.session_state.current_email, st.session_state.active_project_title, all_com): st.toast("✅ Đã lưu dự án!")
            else: st.error("❌ Lỗi khi lưu dự án.")
        
        st.markdown("---")
        
        # 2. KHO LƯU TRỮ
        st.markdown("### 📂 KHO LƯU TRỮ")
        if not supabase: st.error("Chưa kết nối Database.")
        else:
            try:
                if st.session_state.current_email == ADMIN_EMAIL: res = supabase.table("saved_projects").select("*").order("created_at", desc=True).execute()
                else: res = supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
                projects = res.data
            except: projects = []

            if not projects: st.info("Chưa có dự án nào.")
            else:
                for p in projects:
                    with st.expander(f"🎬 {p['project_title']}"):
                        st.caption(f"{p['created_at'][:10]}")
                        if st.session_state.current_email == ADMIN_EMAIL: st.caption(f"Tạo bởi: {p['user_email']}")
                        for i, sc in enumerate(p.get("script_content", [])): st.write(f"- {sc.get('title', 'Idea')}")
                        if st.button("🗑️ Xóa", key=f"del_{p['id']}", use_container_width=True):
                            supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                            st.toast("✅ Đã xóa dự án!")
                            st.rerun()

        # 3. QUẢN TRỊ ADMIN (Bổ sung cấp quyền Thể loại)
        if st.session_state.current_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙️ QUẢN TRỊ ADMIN")
            with st.form("add_license"):
                new_acc = st.text_input("Email cấp quyền:")
                assigned_modules = st.multiselect("Phân quyền thể loại:", options=ALL_MODULES, default=ALL_MODULES)
                duration_opt = st.selectbox("Thời hạn:", ["Dùng thử 3 ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "3 Năm", "5 Năm", "10 Năm", "Vĩnh viễn (Trọn đời)"])
                if st.form_submit_button("💾 Cấp Quyền"):
                    exp_date = "2099-12-31" if "Vĩnh viễn" in duration_opt else (datetime.now() + timedelta(days=3 if "Dùng thử" in duration_opt else {"1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730, "3 Năm": 1095, "5 Năm": 1825, "10 Năm": 3650}.get(duration_opt, 30))).strftime("%Y-%m-%d")
                    st.session_state.licensed_accounts[new_acc.strip()] = {"roles": assigned_modules, "expires_at": exp_date}
                    save_licensed_accounts(st.session_state.licensed_accounts)
                    st.toast(f"✅ Đã cấp quyền cho {new_acc}!")
            
            if st.session_state.licensed_accounts:
                with st.expander(f"📋 Danh sách tài khoản ({len(st.session_state.licensed_accounts)})"):
                    for acc, info in list(st.session_state.licensed_accounts.items()):
                        st.markdown(f"**👤 {acc}**")
                        st.caption(f"Quyền: {', '.join(info.get('roles', ALL_MODULES))}")
                        st.caption(f"Hết hạn: {info.get('expires_at')}")
                        if acc != ADMIN_EMAIL and st.button(f"🗑️ Xóa {acc}", key=f"del_acc_{acc}"):
                            del st.session_state.licensed_accounts[acc]
                            save_licensed_accounts(st.session_state.licensed_accounts)
                            st.toast("✅ Đã xóa tài khoản!")
                            st.rerun()
                        st.markdown("---")

        # 4. HỖ TRỢ LIÊN HỆ
        st.markdown("---")
        st.markdown("""
        <div class="support-box">
            <b style="color: #166534; font-size: 0.95rem;">💬 Cần Hỗ Trợ / Mua Gói?</b><br>
            <p style="font-size: 0.85rem; color: #15803d; margin: 6px 0 8px 0;">Kết nối ngay với chúng tôi:</p>
            <div class="social-icons-container">
                <a href="#" class="btn-zalo" target="_blank">Zalo</a>
                <a href="#" class="btn-fb" target="_blank">f</a>
                <a href="#" class="btn-tt" target="_blank">♪</a>
            </div>
            <div style="font-weight: 700; color: #166534; font-size: 12px; margin-top: 8px;">📞 Hotline: 0968.484.369</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 5. TÀI KHOẢN
        st.markdown("---")
        st.markdown("### 🔐 TÀI KHOẢN")
        st.success(f"Đang dùng: {st.session_state.current_email}")
        if st.button("🚪 Đăng Xuất"):
            st.session_state.is_logged_in = False
            st.toast("✅ Đã đăng xuất!")
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
            create_scene_details(param, st.session_state.get("last_mode", ""), st.session_state.get("last_style", ""), st.session_state.get("last_aspect", ""), st.session_state.get("last_narrator", ""), char_rules)
            st.session_state.active_script_id = param
            st.toast("✅ Đã tạo kịch bản chi tiết thành công!")
    elif action == "clone_script":
        with st.spinner(f"Đang phân tích và nhân bản 5 biến thể Win từ ID {param}..."):
            new_clones = clone_script(param)
            st.session_state.cloned_scripts.extend(new_clones)
            st.toast("✅ Đã nhân bản kịch bản thành công!")
    elif action == "generate_more":
        with st.spinner("Đang mở rộng đa vũ trụ, sáng tạo thêm 5 kịch bản mới..."):
            new_scripts = generate_more_scripts(st.session_state.extra_angle_type, st.session_state.extra_num_chars, st.session_state.extra_duration_mins)
            st.session_state.expanded_scripts.extend(new_scripts)
            st.toast("✅ Đã sinh thêm kịch bản thành công!")
    st.rerun()

# ==============================================================================
# 4. KHÔNG GIAN SÁNG TẠO CHÍNH
# ==============================================================================
st.markdown("""<div class="header-container"><div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div></div>""", unsafe_allow_html=True)

# KIỂM TRA PHÂN QUYỀN THỂ LOẠI CHO USER HIỆN TẠI
current_acc_info = st.session_state.licensed_accounts.get(st.session_state.current_email, {})
user_roles = current_acc_info.get("roles", ALL_MODULES)
allowed_categories = [m for m in ALL_MODULES if m in user_roles]
if not allowed_categories: allowed_categories = ALL_MODULES

if supabase:
    try: products_data = supabase.table("products").select("*").execute().data
    except: products_data = []
    
    if products_data:
        prod_names = [p["product_name"] for p in products_data]
        selected_name = st.selectbox("📌 Chọn sản phẩm từ Database:", options=prod_names, key=f"select_prod_main_{st.session_state.reset_key}")
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
with col_m: mode = st.selectbox("🎯 Thể loại (Đã được phân quyền):", allowed_categories, key=f"mode_sel_{st.session_state.reset_key}")
with col_s: style = st.selectbox("🎨 Phong cách hình ảnh:", ["Điện Ảnh Chân Thực", "Hoạt Hình 3D", "Hoạt Hình 2D / Anime", "Studio Tối Giản"], key=f"style_sel_{st.session_state.reset_key}")
with col_r: aspect = st.selectbox("Khung hình:", ["9:16 (Dọc TikTok/Reels)", "16:9 (Ngang YouTube)"], key=f"aspect_sel_{st.session_state.reset_key}")

narrator_mode = st.selectbox("🎙️ Thuyết minh & Nhân vật:", ["Nhân vật xuất hiện nói chuyện (On-camera, Lip-sync)", "🎙️ Lồng tiếng ngoài (Off-screen, Show sản phẩm)"], key=f"narrator_sel_{st.session_state.reset_key}")

col_p_img, col_c_img = st.columns([1, 1])
with col_p_img:
    up_files = st.file_uploader("📦 Ảnh SP/Bối cảnh (Sẽ được AI giữ nguyên gốc 100%):", type=["jpg", "png"], accept_multiple_files=True, key=f"up_main_files_{st.session_state.reset_key}")
with col_c_img:
    num_chars = st.number_input("👤 Số lượng Diễn viên (Tối đa 8):", min_value=0, max_value=8, step=1, key=f"num_chars_main_{st.session_state.reset_key}")

char_inputs = []
if num_chars > 0:
    for i in range(0, num_chars, 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < num_chars:
                idx = i + j
                with cols[j]:
                    c_role = st.text_input(f"Vai trò NV {idx+1}", key=f"role_{idx}_{st.session_state.reset_key}")
                    c_file = st.file_uploader(f"Ảnh NV {idx+1}", type=["jpg", "png"], key=f"file_{idx}_{st.session_state.reset_key}")
                    if c_file and c_role: char_inputs.append({"id": idx+1, "role": c_role, "file": c_file})

custom_note = st.text_area("✍️ Ghi chú đặc biệt cho AI:", key=f"note_main_{st.session_state.reset_key}")

# ==================== NÚT SINH KỊCH BẢN & PHÂN TÍCH DNA ====================
if st.button("🚀 PHÂN TÍCH DNA & SINH 5 KỊCH BẢN ĐA VŨ TRỤ", type="primary", use_container_width=True):
    with st.spinner("Đạo diễn AI đang tính toán vật lý, nhân vật, và luật TikTok..."):
        st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
        char_rules = generate_char_rules_string(st.session_state.character_profiles)
        st.session_state.last_mode, st.session_state.last_style, st.session_state.last_aspect, st.session_state.last_narrator = mode, style, aspect, narrator_mode
        
        prod_ctx = f"SẢN PHẨM: {json.dumps(st.session_state.current_product_data, ensure_ascii=False)}" if st.session_state.current_product_data else ""
        prompt = f"""
        {prod_ctx}\nGHI CHÚ: {custom_note}
        BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON CHUẨN GỒM:
        {{
            "content_analysis": {{
                "primary_target_audience": "Tệp khách hàng",
                "mechanical_and_accessories": "Kiểu dáng, chất liệu",
                "customer_pain_points": "Nỗi đau",
                "core_desires": "Mong muốn",
                "emotional_or_usp_hook": "USP độc quyền",
                "visual_physics_rules": "Vật lý chuyển động",
                "prompt_dna_lock": "Khóa thị giác"
            }},
            "script_outlines": [ {{"id": 1, "title": "Tên", "setting_style": "Bối cảnh", "target_hook": "Mở đầu"}} ]
        }}
        Tạo đúng 5 kịch bản.
        """
        
        payload = [types.Part.from_bytes(data=f.getvalue(), mime_type=f.type) for f in up_files] if up_files else []
        for c in char_inputs: payload.append(types.Part.from_bytes(data=c['file'].getvalue(), mime_type=c['file'].type))
        payload.append(prompt)
        
        try:
            res = call_gemini(payload, get_system_instructions(mode, style, aspect, narrator_mode, char_rules))
            st.session_state.content_analysis = res.get("content_analysis")
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.cloned_scripts, st.session_state.expanded_scripts = [], []
            st.session_state.generated_details, st.session_state.active_script_id = {}, None
            st.toast("✅ Đã sinh xong 5 kịch bản và phân tích DNA!")
        except Exception as e:
            st.error("❌ Lỗi sinh kịch bản. Vui lòng thử lại!")
        st.rerun()

# ==================== HIỂN THỊ PHÂN TÍCH DNA ====================
if st.session_state.content_analysis and isinstance(st.session_state.content_analysis, dict) and not st.session_state.action_trigger:
    st.divider()
    st.markdown(f"### 🔍 **Phân Tích DNA Chi Tiết Đa Tầng**")
    ca = st.session_state.content_analysis
    with st.container(border=True):
        st.markdown("##### 🎯 **1. Chân dung Khách hàng & Nỗi đau:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Tệp khách hàng mục tiêu:</b> {format_analysis_field(ca.get('primary_target_audience', 'N/A'))}<br>{format_analysis_field(ca.get('customer_pain_points', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 🏭 **2. Thông số Cốt lõi & Vật lý:**")
        st.markdown(f"<div style='line-height: 1.8;'>{format_analysis_field(ca.get('mechanical_and_accessories', 'N/A'))}<br>• <b>Vật lý:</b> {format_analysis_field(ca.get('visual_physics_rules', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 💡 **3. Mong muốn cốt lõi & USP:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Mong muốn:</b> {format_analysis_field(ca.get('core_desires', 'N/A'))}<br>• <b>USP:</b> {format_analysis_field(ca.get('emotional_or_usp_hook', 'N/A'))}</div>", unsafe_allow_html=True)
    st.markdown("##### 📌 **Chuỗi khóa thị giác (Visual DNA Lock):**")
    st.code(str(ca.get('prompt_dna_lock', 'N/A')), language="text")

# ==============================================================================
# DANH SÁCH KỊCH BẢN & XEM CHI TIẾT (SPLIT THEO TRẠNG THÁI)
# ==============================================================================
all_combined_scripts_list = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts

if all_combined_scripts_list and st.session_state.active_script_id is None and not st.session_state.action_trigger:
    st.divider()
    
    completed_scripts = [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) in st.session_state.generated_details]
    pending_scripts = [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) not in st.session_state.generated_details]

    # KHU VỰC 1: ĐÃ HOÀN THIỆN CHI TIẾT (CÓ NÚT NHÂN BẢN)
    st.markdown("### 🎬 **1. Kịch Bản Đã Hoàn Thiện Chi Tiết (Sẵn Sàng Sản Xuất & Nhân Bản)**")
    if not completed_scripts:
        st.info("💡 Chưa có kịch bản nào được tạo chi tiết.")
    else:
        for outline in completed_scripts:
            sc_id = int(outline.get("id", 0))
            with st.container(border=True):
                col_i1, col_btn1, col_btn2 = st.columns([2.5, 1, 1])
                with col_i1:
                    st.markdown(f"**#{sc_id}. {outline.get('title')}** — <span class='badge-ready'>ĐÃ HOÀN THIỆN</span>", unsafe_allow_html=True)
                    st.caption(f"🏛️ Bối cảnh: {outline.get('setting_style')} | ⚡ Hook: *\"{outline.get('target_hook')}\"*")
                with col_btn1:
                    if st.button("👁️ Xem lại chi tiết", key=f"btn_rev_{sc_id}", use_container_width=True):
                        st.session_state.active_script_id = sc_id
                        st.rerun()
                with col_btn2:
                    if st.button("🚀 Nhân bản", key=f"btn_clone_{sc_id}", type="primary", use_container_width=True):
                        st.session_state.action_trigger = "clone_script"
                        st.session_state.action_param = sc_id
                        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # KHU VỰC 2: ĐANG CHỜ (KHÔNG CÓ NÚT NHÂN BẢN)
    st.markdown("### ⏳ **2. Kịch Bản Đang Chờ Tạo Chi Tiết**")
    if not pending_scripts:
        st.success("🎉 Tất cả kịch bản đã được tạo chi tiết thành công.")
    else:
        for outline in pending_scripts:
            sc_id = int(outline.get("id", 0))
            with st.container(border=True):
                col_i2, col_a2 = st.columns([3, 1.2])
                with col_i2:
                    st.markdown(f"**#{sc_id}. {outline.get('title')}** — <span class='badge-pending'>ĐANG CHỜ</span>", unsafe_allow_html=True)
                    st.caption(f"🏛️ Bối cảnh: {outline.get('setting_style')} | ⚡ Hook: *\"{outline.get('target_hook')}\"*")
                with col_a2:
                    if st.button("✨ Tạo chi tiết ngay", key=f"btn_cre_{sc_id}", use_container_width=True):
                        st.session_state.action_trigger = "create_detail"
                        st.session_state.action_param = sc_id
                        st.rerun()

    # KHU VỰC 3: TÙY CHỈNH & GỌI THÊM KỊCH BẢN
    st.markdown("---")
    with st.container(border=True):
        st.markdown("##### ➕ **Tùy Chỉnh & Gọi Thêm Kịch Bản Mới**")
        col_g1, col_g2, col_g3 = st.columns([2, 1, 1])
        with col_g1:
            st.session_state.extra_angle_type = st.selectbox(
                "Định hướng chiến lược:",
                ["⚡ Flash Sale & Deal hời (Tập trung chốt đơn)", "🎭 Tình huống đời sống / Nỗi đau (PAS)", "🔍 Review thực chiến", "💡 Mẹo vặt / Chia sẻ", "😂 Tình huống hài hước"],
                key=f"extra_angle_selectbox_main_{st.session_state.reset_key}"
            )
        with col_g2:
            st.session_state.extra_num_chars = st.number_input("Số diễn viên:", min_value=1, max_value=8, value=1, step=1, key=f"extra_num_chars_main_{st.session_state.reset_key}")
        with col_g3:
            st.session_state.extra_duration_mins = st.number_input("Thời lượng (Phút):", min_value=0.5, max_value=5.0, value=1.0, step=0.5, key=f"extra_duration_mins_main_{st.session_state.reset_key}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Gọi Thêm 5 Kịch Bản Mới", key="btn_add_more_main", type="primary", use_container_width=True):
            st.session_state.action_trigger = "generate_more"
            st.rerun()

# ==============================================================================
# HIỂN THỊ CHI TIẾT
# ==============================================================================
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
        st.markdown(f"**💬 Thoại & Âm thanh (Chuẩn chính tả):** `{scene.get('voiceover_vi', '')}`")
        if scene.get('image_prompt'): st.markdown(f"**🖼️ Prompt Ảnh (Imagen 3):** `{scene.get('image_prompt')}`")
        if scene.get('video_prompt'): st.markdown(f"**🎥 Prompt Video (Veo 3):** `{scene.get('video_prompt')}`")
        st.markdown("---")

