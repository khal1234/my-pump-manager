import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Pump Track Manager", layout="centered")

# [핵심] 여백 최소화 및 깔끔한 폰트 조절 CSS
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    .main-title {
        font-size: 1.2rem !important;
        font-weight: bold;
        margin-top: -20px !important;
        margin-bottom: 12px !important;
        color: #111;
    }
    .filter-label {
        font-size: 0.8rem !important;
        font-weight: bold;
        color: #555;
        margin-top: 6px !important;
        margin-bottom: -4px !important;
    }
    .badge-container {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 5px !important;
        margin-top: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

def load_pump_data():
    return pd.read_excel("pump_list.xlsx")

df = load_pump_data()
diff_cols = [f'Diff{i}' for i in range(1, 8)]

# --- 상호 배제 로직을 위한 세션 상태 세팅 ---
if "active_filter_type" not in st.session_state:
    st.session_state.active_filter_type = "ALL"  # "ALL", "S", "D"
if "current_s" not in st.session_state:
    st.session_state.current_s = None
if "current_d" not in st.session_state:
    st.session_state.current_d = None

# 1. 제목 출력
st.markdown('<div class="main-title">펌프 커스텀 매니저</div>', unsafe_allow_html=True)

# 2. 장르(Category) 선택 - 자판 안 뜨는 가로 알약 배지 형태
st.markdown('<div class="filter-label">Genre</div>', unsafe_allow_html=True)
raw_categories = df["Category"].dropna().unique()
cat_options = ["전체"] + sorted([str(cat) for cat in raw_categories])
selected_category = st.pills("GenreSelect", cat_options, selection_mode="single", default="전체", label_visibility="collapsed")

if selected_category != "전체":
    cat_df = df[df["Category"] == selected_category]
else:
    cat_df = df.copy()

# 현재 활성화된 장르 내에서 모든 난이도 수집
all_diffs = set()
for col in diff_cols:
    all_diffs.update(cat_df[col].dropna().astype(str).unique())

s_levels = sorted([d for d in all_diffs if d.startswith("S")], key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
d_levels = sorted([d for d in all_diffs if d.startswith("D")], key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)

# 3. 싱글 레벨 선택 필터
st.markdown('<div class="filter-label">Single Level</div>', unsafe_allow_html=True)
selected_s = st.pills("SingleSelect", s_levels, selection_mode="single", label_visibility="collapsed")

# 4. 더블 레벨 선택 필터
st.markdown('<div class="filter-label">Double Level</div>', unsafe_allow_html=True)
selected_d = st.pills("DoubleSelect", d_levels, selection_mode="single", label_visibility="collapsed")

# --- 교차 리셋 및 상호배제 로직 정교화 ---
# S를 새로 눌렀다면 D 필터 무시
if selected_s and selected_s != st.session_state.current_s:
    st.session_state.active_filter_type = "S"
    st.session_state.current_s = selected_s
# D를 새로 눌렀다면 S 필터 무시
if selected_d and selected_d != st.session_state.current_d:
    st.session_state.active_filter_type = "D"
    st.session_state.current_d = selected_d

# 아무것도 안 눌려있다면 초기화
if not selected_s and not selected_d:
    st.session_state.active_filter_type = "ALL"
    st.session_state.current_s = None
    st.session_state.current_d = None

# --- 데이터 최종 필터링 ---
filtered_df = cat_df.copy()

if st.session_state.active_filter_type == "S" and selected_s:
    filtered_df = filtered_df[filtered_df[diff_cols].apply(lambda row: selected_s in row.values, axis=1)]
elif st.session_state.active_filter_type == "D" and selected_d:
    filtered_df = filtered_df[filtered_df[diff_cols].apply(lambda row: selected_d in row.values, axis=1)]

st.markdown('<hr style="margin-top: 8px; margin-bottom: 8px; opacity: 0.2;">', unsafe_allow_html=True)

# --- 리스트 출력 ---
st.markdown(f'<div style="font-size: 0.85rem; font-weight: 600; margin-bottom: 6px; color: #666;">리스트 ({len(filtered_df)}곡)</div>', unsafe_allow_html=True)

for index, row in filtered_df.iterrows():
    diffs = [row[f"Diff{i}"] for i in range(1, 8) if pd.notna(row[f"Diff{i}"])]
    
    tag_html = '<div class="badge-container">'
    for d in diffs:
        bg_color = "#e74c3c" if str(d).startswith("S") else "#2ecc71"
        tag_html += f'<span style="background-color: {bg_color}; color: white; padding: 2px 7px; border-radius: 12px; font-size: 8.5pt; font-weight: bold; display: inline-block; line-height: 1.2; border: 1px solid rgba(0,0,0,0.05);">{d}</span>'
    tag_html += '</div>'
    
    with st.container(border=True):
        st.markdown(f'<div style="font-size: 13pt; font-weight: bold; color: #111; line-height: 1.2;">{row["Song Title"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 9.5pt; color: #666; margin-top: 1px;">{row["Addition"]} <span style="font-size: 8pt; color: #ccc; margin-left: 5px;">| {row["Category"]}</span></div>', unsafe_allow_html=True)
        st.markdown(tag_html, unsafe_allow_html=True)