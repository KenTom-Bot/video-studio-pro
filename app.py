import streamlit as st
from google import genai
from google.genai import types
from supabase import create_client, Client
import json
import os

# 1. CẤU HÌNH TRANG & KẾT NỐI
st.set_page_config(page_title="Video Studio Pro", layout="wide")
ADMIN_EMAIL = "binhnguyenmedia.vn@gmail.com" # Đổi thành email của bạn

@st.cache_resource
def init_supabase():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None
supabase = init_supabase()

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
client = genai.Client(api_key=api_key) if api_key else None

# 2. BỘ NHỚ TẠM (SESSION)
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
    st.session_state.current_email = ""
    st.session_state.current_scripts = []

# 3. GIAO DIỆN ĐĂNG NHẬP (SIDEBAR)
with st.sidebar:
    st.markdown("### 🔐 CỔNG ĐĂNG NHẬP")
    if not st.session_state.is_logged_in:
        email_input = st.text_input("Nhập Email của bạn:")
        if st.button("Đăng nhập"):
            if email_input.strip():
                st.session_state.is_logged_in = True
                st.session_state.current_email = email_input.strip()
                st.rerun()
            else:
                st.error("Vui lòng nhập Email!")
    else:
        st.success(f"Xin chào: **{st.session_state.current_email}**")
        role = "👑 ADMIN" if st.session_state.current_email == ADMIN_EMAIL else "👤 USER"
        st.info(f"Quyền hạn: {role}")
        if st.button("Đăng xuất"):
            st.session_state.is_logged_in = False
            st.session_state.current_email = ""
            st.rerun()

if not st.session_state.is_logged_in:
    st.warning("👈 Vui lòng nhập Email ở menu bên trái để truy cập hệ thống.")
    st.stop()

# 4. HÀM XỬ LÝ DỮ LIỆU & AI
def save_project_to_db(email, title, content_list):
    if not supabase: return False
    try:
        data = {
            "user_email": email,
            "project_title": title,
            "script_content": content_list # Lưu kịch bản thành JSON
        }
        supabase.table("saved_projects").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi lưu dự án: {e}")
        return False

# 5. KHU VỰC SÁNG TẠO KỊCH BẢN MỚI
st.title("🎬 HỆ THỐNG SÁNG TẠO VIDEO AI")
tab1, tab2 = st.tabs(["✨ Tạo Kịch Bản Mới", "📂 Kho Lưu Trữ Dự Án"])

with tab1:
    st.markdown("### ✍️ Nhập thông tin sản phẩm/dự án")
    project_name = st.text_input("Tên dự án (để lưu trữ):", "Chiến dịch Video mới")
    product_info = st.text_area("Mô tả sản phẩm, nỗi đau khách hàng, điểm nổi bật:")
    
    if st.button("🚀 Sinh Kịch Bản AI", type="primary"):
        if not product_info:
            st.warning("Vui lòng nhập mô tả sản phẩm!")
        else:
            with st.spinner("Đang kết nối Gemini AI..."):
                prompt = f"""
                Dựa vào thông tin sau: {product_info}. 
                Hãy tạo 3 ý tưởng kịch bản video ngắn.
                Trả về ĐÚNG định dạng JSON chứa 1 mảng 'scripts', mỗi phần tử có: 
                'title' (tên kịch bản), 'hook' (câu mở đầu), 'body' (nội dung chính).
                """
                try:
                    res = client.models.generate_content(
                        model="gemini-3.6-flash", contents=prompt,
                        config=types.GenerateContentConfig(response_mime_type="application/json")
                    )
                    # Xử lý JSON trả về
                    text_res = res.text.strip().replace('```json', '').replace('```', '')
                    st.session_state.current_scripts = json.loads(text_res).get("scripts", [])
                    st.success("Tạo kịch bản thành công!")
                except Exception as e:
                    st.error("Lỗi AI hoặc định dạng JSON. Thử lại nhé!")

    # Hiển thị kịch bản vừa tạo & Nút Lưu
    if st.session_state.current_scripts:
        st.markdown("---")
        for idx, sc in enumerate(st.session_state.current_scripts):
            st.info(f"**Kịch bản {idx+1}: {sc.get('title', '')}**\n\n**Hook:** {sc.get('hook', '')}\n\n**Nội dung:** {sc.get('body', '')}")
        
        if st.button("💾 Lưu Dự Án Này Vào Database"):
            if save_project_to_db(st.session_state.current_email, project_name, st.session_state.current_scripts):
                st.success("✅ Đã lưu dự án thành công! Hãy sang tab 'Kho Lưu Trữ' để xem.")

# 6. KHU VỰC KHO LƯU TRỮ PHÂN QUYỀN
with tab2:
    st.markdown("### 📂 Quản Lý Dự Án")
    if not supabase:
        st.error("Lỗi: Chưa kết nối Database Supabase.")
    else:
        # LOGIC PHÂN QUYỀN: 
        # Nếu là Admin -> Lấy tất cả. Nếu là User -> Chỉ lấy của User đó.
        try:
            if st.session_state.current_email == ADMIN_EMAIL:
                st.write("👑 **Góc nhìn Admin:** Toàn bộ dự án trên hệ thống")
                response = supabase.table("saved_projects").select("*").order("created_at", desc=True).execute()
            else:
                st.write("👤 **Góc nhìn User:** Các dự án cá nhân của bạn")
                response = supabase.table("saved_projects").select("*").eq("user_email", st.session_state.current_email).order("created_at", desc=True).execute()
            
            projects = response.data
        except Exception as e:
            projects = []
            st.error(f"Lỗi tải dữ liệu: {e}")

        if not projects:
            st.info("Chưa có dự án nào được lưu.")
        else:
            for p in projects:
                # Trình bày giao diện thẻ
                display_name = f"🎬 {p['project_title']} (Tạo bởi: {p['user_email']})" if st.session_state.current_email == ADMIN_EMAIL else f"🎬 {p['project_title']}"
                
                with st.expander(display_name):
                    st.caption(f"Thời gian tạo: {p['created_at']}")
                    
                    # Đọc kịch bản từ JSON
                    saved_scripts = p.get("script_content", [])
                    for i, sc in enumerate(saved_scripts):
                        st.markdown(f"**Ý tưởng {i+1}: {sc.get('title', 'Không tên')}**")
                        st.write(f"- Hook: {sc.get('hook', '')}")
                    
                    # Nút Xóa (Chỉ Admin hoặc Chủ dự án mới thấy)
                    if st.button("🗑️ Xóa dự án", key=f"del_{p['id']}"):
                        supabase.table("saved_projects").delete().eq("id", p['id']).execute()
                        st.toast("Đã xóa!")
                        st.rerun()
                        
