import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pump Track Manager", layout="centered")

# [UI 최적화] 모바일 여백 최소화 및 레이아웃 CSS
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

# 엑셀 로드 및 데이터 캐싱
@st.cache_data
def load_pump_data():
    return pd.read_excel("pump_list.xlsx")

df = load_pump_data()

# 새 헤더 정의 (S_1 ~ S_7, D_1 ~ D_7)
s_cols = [f'S_{i}' for i in range(1, 8)]
d_cols = [f'D_{i}' for i in range(1, 8)]

# --- 상호 배제 로직 세션 상태 세팅 ---
if "active_filter_type" not in st.session_state:
    st.session_state.active_filter_type = "ALL"  # "ALL", "S", "D"
if "current_s" not in st.session_state:
    st.session_state.current_s = None
if "current_d" not in st.session_state:
    st.session_state.current_d = None

# 1. 제목 출력
st.markdown('<div class="main-title">펌프 커스텀 매니저</div>', unsafe_allow_html=True)

# 2. Genre (Category) 선택 필터 (1차 필터)
st.markdown('<div class="filter-label">Genre</div>', unsafe_allow_html=True)
raw_categories = df["Category"].dropna().unique()
cat_options = ["전체"] + sorted([str(cat) for cat in raw_categories])
selected_category = st.pills("GenreSelect", cat_options, selection_mode="single", default="전체", label_visibility="collapsed")

if selected_category != "전체":
    cat_df = df[df["Category"] == selected_category]
else:
    cat_df = df.copy()

# 🌟 3. [핵심 추가] Addition 검색/드롭다운 필터 (2차 필터)
st.markdown('<div class="filter-label">세부 팩 / 분류 (Addition)</div>', unsafe_allow_html=True)
raw_additions = cat_df["Addition"].dropna().unique()
add_options = ["전체"] + sorted([str(add) for add in raw_additions])

# 컴팩트한 검색형 드롭다운 컴포넌트 배치
selected_addition = st.selectbox("AdditionSelect", add_options, index=0, label_visibility="collapsed")

if selected_addition != "전체":
    final_filtered_df = cat_df[cat_df["Addition"] == selected_addition]
else:
    final_filtered_df = cat_df.copy()


# 현재 필터링된 데이터 내에서 실제 입력된 숫자 추출 후 S/D 문자열 결합
s_levels_set = set()
for col in s_cols:
    if col in final_filtered_df.columns:
        valid_vals = final_filtered_df[col].dropna().astype(int).unique()
        s_levels_set.update([f"S{v}" for v in valid_vals])

d_levels_set = set()
for col in d_cols:
    if col in final_filtered_df.columns:
        valid_vals = final_filtered_df[col].dropna().astype(int).unique()
        d_levels_set.update([f"D{v}" for v in valid_vals])

# 정렬할 때 숫자 크기대로 정렬
s_levels = sorted(list(s_levels_set), key=lambda x: int(x[1:]))
d_levels = sorted(list(d_levels_set), key=lambda x: int(x[1:]))

# 4. Single Level 필터
st.markdown('<div class="filter-label">Single Level</div>', unsafe_allow_html=True)
selected_s = st.pills("SingleSelect", s_levels, selection_mode="single", label_visibility="collapsed")

# 5. Double Level 필터
st.markdown('<div class="filter-label">Double Level</div>', unsafe_allow_html=True)
selected_d = st.pills("DoubleSelect", d_levels, selection_mode="single", label_visibility="collapsed")


# --- 교차 리셋 로직 조율 ---
if selected_s and selected_s != st.session_state.current_s:
    st.session_state.active_filter_type = "S"
    st.session_state.current_s = selected_s
if selected_d and selected_d != st.session_state.current_d:
    st.session_state.active_filter_type = "D"
    st.session_state.current_d = selected_d

if not selected_s and not selected_d:
    st.session_state.active_filter_type = "ALL"
    st.session_state.current_s = None
    st.session_state.current_d = None


# --- 최종 데이터 필터링 로직 ---
if st.session_state.active_filter_type == "S" and selected_s:
    target_num = int(selected_s[1:])
    final_filtered_df = final_filtered_df[final_filtered_df[s_cols].apply(lambda row: target_num in row.values, axis=1)]
elif st.session_state.active_filter_type == "D" and selected_d:
    target_num = int(selected_d[1:])
    final_filtered_df = final_filtered_df[final_filtered_df[d_cols].apply(lambda row: target_num in row.values, axis=1)]

st.markdown('<hr style="margin-top: 8px; margin-bottom: 8px; opacity: 0.2;">', unsafe_allow_html=True)


# --- 카드 리스트 출력 ---
st.markdown(f'<div style="font-size: 0.85rem; font-weight: 600; margin-bottom: 6px; color: #666;">리스트 ({len(final_filtered_df)}곡)</div>', unsafe_allow_html=True)

for index, row in final_filtered_df.iterrows():
    s_list = [f"S{int(row[c])}" for c in s_cols if c in df.columns and pd.notna(row[c])]
    d_list = [f"D{int(row[c])}" for c in d_cols if c in df.columns and pd.notna(row[c])]
    total_diffs = s_list + d_list
    
    tag_html = '<div class="badge-container">'
    for d in total_diffs:
        bg_color = "#e74c3c" if d.startswith("S") else "#2ecc71"
        tag_html += f'<span style="background-color: {bg_color}; color: white; padding: 2px 7px; border-radius: 12px; font-size: 8.5pt; font-weight: bold; display: inline-block; line-height: 1.2; border: 1px solid rgba(0,0,0,0.05);">{d}</span>'
    tag_html += '</div>'
    
    with st.container(border=True):
        st.markdown(f'<div style="font-size: 13pt; font-weight: bold; color: #111; line-height: 1.2;">{row["Song Title"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 9.5pt; color: #666; margin-top: 1px;">{row["Addition"]} <span style="font-size: 8pt; color: #ccc; margin-left: 5px;">| {row["Category"]}</span></div>', unsafe_allow_html=True)
        st.markdown(tag_html, unsafe_allow_html=True)