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

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Universal AI Video Studio Pro", page_icon="🎬", layout="wide")
st.markdown("""
<style>
    .header-container { text-align: center; padding: 1.2rem; background: radial-gradient(circle, rgba(255,75,75,0.08) 0%, rgba(255,255,255,0) 70%); }
    .main-title { font-size: 2.2rem !important; font-weight: 900 !important; background: linear-gradient(90deg, #ff0050 0%, #ff5252 50%, #ff7300 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important; color: white !important; font-weight: bold; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 3px 8px; border-radius: 4px; font-size: 12px; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 3px 8px; border-radius: 4px; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# --- KẾT NỐI HỆ THỐNG ---
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
client = genai.Client(api_key=api_key)

@st.cache_resource
def init_supabase():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None
supabase = init_supabase()

# --- KHỞI TẠO BỘ NHỚ TẠM (SESSION STATE) ---
for key in ["is_logged_in", "all_scripts", "generated_details", "active_script_id", "current_product_data"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "is_logged_in" else ([] if key == "all_scripts" else ({} if key == "generated_details" else None))

# --- SIDEBAR & ĐĂNG NHẬP ---
with st.sidebar:
    if not st.session_state.is_logged_in:
        st.markdown("### 🔐 Đăng Nhập")
        if st.button("🔑 Bắt đầu phiên làm việc", type="primary", use_container_width=True):
            st.session_state.is_logged_in = True
            st.rerun()
    else:
        st.markdown("### 🗂️ Quản Lý Dự Án")
        if st.button("➕ Tạo Dự Án Mới", type="primary", use_container_width=True):
            st.session_state.all_scripts, st.session_state.generated_details, st.session_state.active_script_id = [], {}, None
            st.rerun()
        if st.button("🚪 Đăng Xuất", use_container_width=True):
            st.session_state.is_logged_in = False
            st.rerun()

if not st.session_state.is_logged_in:
    st.info("👈 Vui lòng đăng nhập ở thanh công cụ bên trái.")
    st.stop()

# --- LÕI AI ĐẠO DIỄN VÀ TIỆN ÍCH ---
def clean_json(text):
    cleaned = re.sub(r'```(?:json)?', '', text).strip()
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    return json.loads(match.group(0)) if match else {}

def call_gemini(contents, sys_inst):
    res = client.models.generate_content(
        model="gemini-3.6-flash", contents=contents,
        config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.7)
    )
    return clean_json(res.text)

def get_system_instructions(mode, style, aspect, goal):
    return f"""
    BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL ĐA NĂNG. CHUYÊN SẢN XUẤT VIDEO NGẮN THƯƠNG MẠI.
    - PHONG CÁCH: {style}
    - ĐỊNH DẠNG: {aspect}
    - MỤC TIÊU: {goal}
    
    QUY TẮC BẮT BUỘC:
    1. TRẢ VỀ JSON HỢP LỆ.
    2. NHỊP ĐỘ CHỚP NHOÁNG: Video phải có nhịp điệu nhanh, chia thành nhiều phân đoạn nhỏ.
    3. THỜI LƯỢNG CẢNH VEO 3: Các phân cảnh BẮT BUỘC phải được chia chính xác thành các mốc 8 giây hoặc 10 giây để tối ưu công cụ tạo video AI Veo 3. Không dùng các số thời lượng lẻ tẻ.
    4. VOICE-OVER: Lời thoại lồng tiếng cần gắn liền trực tiếp với hướng dẫn hành động trong từng phân cảnh.
    5. ĐỒNG NHẤT NHÂN VẬT: Đảm bảo tính nhất quán của nhân vật xuyên suốt các phân cảnh bằng các prompt ảnh chi tiết.
    """

def create_scene_details(script_id, mode, style, aspect, goal):
    outline = next((sc for sc in st.session_state.all_scripts if sc["id"] == script_id), None)
    if not outline: return
    
    prompt = f"""
    Viết kịch bản chi tiết cho ID {script_id}: "{outline['title']}".
    Hook: {outline['target_hook']}. Bối cảnh: {outline['setting_style']}.
    Chia kịch bản thành các cảnh 8 giây và 10 giây.
    Xuất JSON: chứa key 'scenes' với mảng các object (duration, voiceover_vi, image_prompt, video_prompt).
    Trong video_prompt cho Veo 3, miêu tả rõ chuyển động camera (Pan, Zoom, Tracking).
    """
    sys_inst = get_system_instructions(mode, style, aspect, goal)
    res = call_gemini([prompt], sys_inst)
    st.session_state.generated_details[script_id] = res if isinstance(res, dict) else res[0]

# --- GIAO DIỆN CHÍNH & SUPABASE ---
st.markdown("""<div class="header-container"><div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div></div>""", unsafe_allow_html=True)

st.markdown("## 📊 Creator Dashboard")
with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Video đã đăng", "217", "+12")
    c2.metric("GMV (Doanh thu)", "45.2 Triệu", "+5.4M")
    c3.metric("Tỷ lệ chuyển đổi", "3.2%", "+0.4%")
    c4.metric("Angle tốt nhất", "Review & Test", "Chốt đơn cao nhất")

st.markdown("### 🛒 Chọn Sản Phẩm Từ Database")
if supabase:
    try: products_data = supabase.table("products").select("*").execute().data
    except: products_data = []
    
    if products_data:
        prod_names = [p["product_name"] for p in products_data]
        selected_name = st.selectbox("📌 Chọn sản phẩm:", options=prod_names)
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
else:
    st.error("Chưa kết nối Supabase.")

# --- CẤU HÌNH & RUN AI ---
col_m, col_s, col_r = st.columns(3)
with col_m: mode = st.selectbox("Thể loại:", ["🛒 Bán Hàng & Chuyển đổi", "🌟 Viral & Thương hiệu"])
with col_s: style = st.selectbox("Phong cách:", ["Điện Ảnh Chân Thực", "Studio Tối Giản"])
with col_r: aspect = st.selectbox("Khung hình:", ["9:16", "16:9"])

up_files = st.file_uploader("📦 Ảnh sản phẩm tham chiếu:", type=["jpg", "png"], accept_multiple_files=True)

if st.button("🚀 Sinh 5 Kịch Bản Đa Vũ Trụ", type="primary", use_container_width=True):
    with st.spinner("Đang phân tích DNA Sản phẩm và sinh kịch bản..."):
        try:
            prod_ctx = f"THÔNG TIN SP: {json.dumps(st.session_state.current_product_data, ensure_ascii=False)}" if st.session_state.current_product_data else ""
            prompt = f"{prod_ctx}\nTạo 5 kịch bản ngắn. Xuất JSON key 'script_outlines' (id, title, setting_style, target_hook)."
            payload = [types.Part.from_bytes(data=f.getvalue(), mime_type=f.type) for f in up_files] if up_files else []
            payload.append(prompt)
            
            res = call_gemini(payload, get_system_instructions(mode, style, aspect, "Sales"))
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.generated_details, st.session_state.active_script_id = {}, None
            st.rerun()
        except Exception as e: st.error(f"Lỗi: {e}")

# --- SPLIT SCREEN UI ---
if st.session_state.all_scripts and st.session_state.active_script_id is None:
    st.divider()
    st.markdown("### 🎬 Kịch Bản Đề Xuất")
    for sc in st.session_state.all_scripts:
        sc_id = sc["id"]
        with st.container(border=True):
            c_info, c_btn = st.columns([3, 1])
            with c_info:
                status = "<span class='badge-ready'>ĐÃ CHI TIẾT</span>" if sc_id in st.session_state.generated_details else "<span class='badge-pending'>ĐANG CHỜ</span>"
                st.markdown(f"**#{sc_id}. {sc.get('title')}** {status}", unsafe_allow_html=True)
                st.caption(f"⚡ Hook: {sc.get('target_hook')}")
            with c_btn:
                if sc_id in st.session_state.generated_details:
                    if st.button("👁️ Xem chi tiết", key=f"view_{sc_id}", use_container_width=True):
                        st.session_state.active_script_id = sc_id
                        st.rerun()
                else:
                    if st.button("✨ Tạo phân cảnh Veo 3", key=f"cre_{sc_id}", use_container_width=True):
                        with st.spinner("Đang lên khung hình 8s/10s..."):
                            create_scene_details(sc_id, mode, style, aspect, "Sales")
                            st.session_state.active_script_id = sc_id
                            st.rerun()

if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details:
    st.divider()
    if st.button("⬅️ Quay lại danh sách"):
        st.session_state.active_script_id = None
        st.rerun()
    
    active_sc = st.session_state.generated_details[st.session_state.active_script_id]
    st.markdown(f"### 🎬 CHI TIẾT: {active_sc.get('title', '')}")
    
    scenes = active_sc.get("scenes", [])
    for idx, scene in enumerate(scenes, 1):
        st.markdown(f"#### 📍 Cảnh {idx} ({scene.get('duration', '8s')})")
        st.markdown(f"**💬 Thoại:** `{scene.get('voiceover_vi', '')}`")
        if scene.get('image_prompt'): st.markdown(f"**🖼️ Prompt Ảnh:** `{scene.get('image_prompt')}`")
        if scene.get('video_prompt'): st.markdown(f"**🎥 Prompt Veo 3:** `{scene.get('video_prompt')}`")
        st.markdown("---")
