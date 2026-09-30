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
    .support-box { background: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; margin-top: 10px; font-size: 0.9rem; }
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

# Khởi tạo bộ nhớ Session State
for key, default_val in [
    ("is_logged_in", False), ("current_email", ""), ("licensed_accounts", load_licensed_accounts()),
    ("all_scripts", []), ("generated_details", {}), ("active_script_id", None),
    ("current_product_data", None), ("action_trigger", None), ("action_param", None),
    ("active_project_title", f"Chiến dịch {datetime.now().strftime('%d/%m/%Y')}")
]:
    if key not in st.session_state: st.session_state[key] = default_val

# ==============================================================================
# 2. HÀM AI LÕI & LƯU DATABASE
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
# 3. THANH BÊN (SIDEBAR) TỐI ƯU UX MỚI
# ==============================================================================
with st.sidebar:
    if st.session_state.is_logged_in:
        # KHU VỰC 1: ĐẶT TÊN DỰ ÁN
        st.markdown("### 🗂️ LÀM VIỆC")
        st.session_state.active_project_title = st.text_input("💾 Tên dự án hiện tại:", st.session_state.active_project_title)
        st.markdown("---")
        
        # KHU VỰC 2: KHO LƯU TRỮ VÀO SIDEBAR
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
            except Exception:
                projects = []

            if not projects:
                st.info("Chưa có dự án nào.")
            else:
                for p in projects:
                    display_title = f"🎬 {p['project_title']}"
                    with st.expander(display_title):
                        st.caption(f"{p['created_at'][:10]}")
                        if st.session_state.current_email == ADMIN_EMAIL:
                            st.caption(f"Tạo bởi: {p['user_email']}")
                        # Hiển thị tóm tắt kịch bản
                        saved_scripts = p.get("script_content", [])
                        for i, sc in enumerate(saved_scripts):
                            st.write(f"- {sc.get('title', 'Idea')}")
                        if st.button("🗑️ Xóa", key=f"del_proj_{p['id']}", use_container_width=True):
                            supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                            st.rerun()

        # KHU VỰC 3: QUẢN TRỊ ADMIN (NẾU CÓ)
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
                    st.success(f"Đã cấp quyền!")

    # KHU VỰC 4: ĐĂNG NHẬP / ĐĂNG XUẤT (DƯỚI CÙNG SIDEBAR)
    st.markdown("---")
    st.markdown("### 🔐 TÀI KHOẢN")
    if not st.session_state.is_logged_in:
        email_input = st.text_input("Nhập Email đã cấp quyền:")
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
                st.rerun()
            else: st.error("Tài khoản chưa được cấp quyền!")
    else:
        st.success(f"Đang dùng: {st.session_state.current_email}")
        if st.button("🚪 Đăng Xuất"):
            st.session_state.is_logged_in = False
            st.rerun()

    # KHU VỰC 5: HỖ TRỢ LIÊN HỆ
    st.markdown("---")
    st.markdown("### 🎧 LIÊN HỆ HỖ TRỢ")
    st.markdown("""
    <div class="support-box">
        <p>📞 <b>Hotline/Zalo:</b> 0968.484.369</p>
        <p>🌐 <b>Facebook:</b> <a href="[https://facebook.com/](https://facebook.com/)" target="_blank">Bình Nguyễn Media</a></p>
        <p>🎵 <b>TikTok:</b> <a href="[https://tiktok.com/](https://tiktok.com/)" target="_blank">@binhnguyenmedia</a></p>
    </div>
    """, unsafe_allow_html=True)

if not st.session_state.is_logged_in:
    st.info("👈 Vui lòng đăng nhập ở thanh công cụ bên trái.")
    st.stop()

# ==============================================================================
# 3. THANH BÊN (SIDEBAR) TỐI ƯU UX MỚI
# ==============================================================================
with st.sidebar:
    if st.session_state.is_logged_in:
        # KHU VỰC 1: ĐẶT TÊN DỰ ÁN
        st.markdown("### 🗂️ LÀM VIỆC")
        st.session_state.active_project_title = st.text_input("💾 Tên dự án hiện tại:", st.session_state.active_project_title)
        st.markdown("---")
        
        # KHU VỰC 2: KHO LƯU TRỮ VÀO SIDEBAR
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
            except Exception:
                projects = []

            if not projects:
                st.info("Chưa có dự án nào.")
            else:
                for p in projects:
                    display_title = f"🎬 {p['project_title']}"
                    with st.expander(display_title):
                        st.caption(f"{p['created_at'][:10]}")
                        if st.session_state.current_email == ADMIN_EMAIL:
                            st.caption(f"Tạo bởi: {p['user_email']}")
                        # Hiển thị tóm tắt kịch bản
                        saved_scripts = p.get("script_content", [])
                        for i, sc in enumerate(saved_scripts):
                            st.write(f"- {sc.get('title', 'Idea')}")
                        if st.button("🗑️ Xóa", key=f"del_proj_{p['id']}", use_container_width=True):
                            supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                            st.rerun()

        # KHU VỰC 3: QUẢN TRỊ ADMIN (NẾU CÓ)
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
                    st.success(f"Đã cấp quyền!")

    # KHU VỰC 4: ĐĂNG NHẬP / ĐĂNG XUẤT (DƯỚI CÙNG SIDEBAR)
    st.markdown("---")
    st.markdown("### 🔐 TÀI KHOẢN")
    if not st.session_state.is_logged_in:
        email_input = st.text_input("Nhập Email đã cấp quyền:")
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
                st.rerun()
            else: st.error("Tài khoản chưa được cấp quyền!")
    else:
        st.success(f"Đang dùng: {st.session_state.current_email}")
        if st.button("🚪 Đăng Xuất"):
            st.session_state.is_logged_in = False
            st.rerun()

    # KHU VỰC 5: HỖ TRỢ LIÊN HỆ
    st.markdown("---")
    st.markdown("### 🎧 LIÊN HỆ HỖ TRỢ")
    st.markdown("""
    <div class="support-box">
        <p>📞 <b>Hotline/Zalo:</b> 0968.484.369</p>
        <p>🌐 <b>Facebook:</b> <a href="[https://facebook.com/](https://facebook.com/)" target="_blank">Bình Nguyễn Media</a></p>
        <p>🎵 <b>TikTok:</b> <a href="[https://tiktok.com/](https://tiktok.com/)" target="_blank">@binhnguyenmedia</a></p>
    </div>
    """, unsafe_allow_html=True)

if not st.session_state.is_logged_in:
    st.info("👈 Vui lòng đăng nhập ở thanh công cụ bên trái.")
    st.stop()
