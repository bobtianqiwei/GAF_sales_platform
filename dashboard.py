import streamlit as st
import pandas as pd
import requests
import pydeck as pdk

API_URL = "http://localhost:8000"

# 用户角色选择放最顶
user_role = st.sidebar.selectbox("I am (User Role)", ["Sales Rep", "Manager", "Business Analyst", "Other"])

st.title("Contractor Insights Dashboard")

# Sidebar filters
city = st.sidebar.text_input("City")
state = st.sidebar.text_input("State")
min_rating = st.sidebar.number_input("Min Rating", min_value=0.0, max_value=5.0, step=0.1, value=0.0)
max_rating = st.sidebar.number_input("Max Rating", min_value=0.0, max_value=5.0, step=0.1, value=5.0)
certification = st.sidebar.text_input("Certification contains")
order_by = st.sidebar.selectbox("Order by", [None, "rating", "reviews", "updated_at", "priority_suggestion"])
order_desc = st.sidebar.checkbox("Descending", value=True)
limit = st.sidebar.slider("Limit", 1, 100, 20)

params = {
    "city": city or None,
    "state": state or None,
    "min_rating": min_rating if min_rating > 0 else None,
    "max_rating": max_rating if max_rating < 5 else None,
    "certification": certification or None,
    "order_by": order_by or None,
    "order_desc": order_desc,
    "limit": limit,
}
params = {k: v for k, v in params.items() if v is not None}

resp = requests.get(f"{API_URL}/contractors", params=params)
data = resp.json() if resp.status_code == 200 else []
df = pd.DataFrame(data)

# 防御性检查：确保每一行都是dict，否则报错
if not all(isinstance(item, dict) for item in data):
    st.error("API返回数据格式错误：每一项应为dict。请检查后端API返回值。")
    st.stop()

# 地图可视化
st.subheader("Contractor Map")
if not df.empty and 'latitude' in df and 'longitude' in df:
    # priority颜色映射
    def get_priority_color(priority):
        if not isinstance(priority, str):
            return [128,128,128]
        p = priority.lower()
        if 'high' in p:
            return [34, 139, 34]  # 绿
        elif 'medium' in p:
            return [30, 144, 255]  # 蓝
        elif 'low' in p:
            return [148, 0, 211]  # 紫
        else:
            return [128,128,128]  # 灰
    df_map = df.dropna(subset=['latitude','longitude']).copy()
    df_map['color'] = df_map['priority_suggestion'].apply(get_priority_color)
    df_map['tooltip'] = (
        df_map['name'] + ' (' + df_map['city'] + ', ' + df_map['state'] + ')\\n'
        + 'Phone: ' + df_map['phone'].astype(str) + '\\n'
        + 'Rating: ' + df_map['rating'].astype(str) + '\\n'
        + 'Type: ' + df_map['type'].astype(str) + '\\n'
        + 'Cert: ' + df_map['certifications'].astype(str)
    )
    # 更新图例
    st.markdown("""
    <div style='font-size:14px;'>
    <b>Priority Legend:</b>
    <span style='color:#228B22;'>● High</span>
    <span style='color:#1E90FF;'>● Medium</span>
    <span style='color:#9400D3;'>● Low</span>
    <span style='color:#888888;'>● Unknown</span>
    </div>
    """, unsafe_allow_html=True)
    # pydeck图层，点半径更大，带文本
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position='[longitude, latitude]',
        get_color='color',
        get_radius=800,
        pickable=True,
        auto_highlight=True,
    )
    text_layer = pdk.Layer(
        "TextLayer",
        data=df_map,
        get_position='[longitude, latitude]',
        get_text='name',
        get_size=14,
        get_color=[40,40,40],
        get_angle=0,
        get_alignment_baseline="bottom",
    )
    view_state = pdk.ViewState(
        latitude=df_map['latitude'].mean(),
        longitude=df_map['longitude'].mean(),
        zoom=8,
        pitch=0
    )
    # 获取当前位置（如有权限，可用st.session_state或geolocation API，这里用默认中心点）
    user_lat, user_lng = df_map['latitude'].mean(), df_map['longitude'].mean()
    # 增加当前位置点（蓝色大点）
    user_layer = pdk.Layer(
        "ScatterplotLayer",
        data=pd.DataFrame([{ 'latitude': user_lat, 'longitude': user_lng }]),
        get_position='[longitude, latitude]',
        get_color=[0, 0, 255],
        get_radius=1200,
        pickable=False,
    )
    # 高亮当前选中点
    highlight_layer = None
    if 'selected_name' in locals() and selected_name:
        match = df_map[df_map['name'] == selected_name]
        if not match.empty:
            row = match.iloc[0]
            st.markdown(f"<h3 style='font-weight:bold'>{row['name']} ({row['city']}, {row['state']})</h3>", unsafe_allow_html=True)
            if row.get('url'):
                st.markdown(f"<a href='{row['url']}' target='_blank' style='font-size:16px'>GAF Website</a>", unsafe_allow_html=True)
            st.markdown("<h4 style='font-weight:bold'>Priority</h4>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:16px'>{row.get('priority_suggestion','')}</div>", unsafe_allow_html=True)
            st.markdown("<h4 style='font-weight:bold'>Business Summary</h4>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:16px'>{row.get('business_summary','')}</div>", unsafe_allow_html=True)
            st.markdown("<h4 style='font-weight:bold'>Sales Tip</h4>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:16px'>{row.get('sales_tip','')}</div>", unsafe_allow_html=True)
            st.markdown("<h4 style='font-weight:bold'>Risk Alert</h4>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:16px'>{row.get('risk_alert','')}</div>", unsafe_allow_html=True)
            st.markdown("<h4 style='font-weight:bold'>Next Action</h4>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:16px'>{row.get('next_action','')}</div>", unsafe_allow_html=True)
            st.markdown("<h4 style='font-weight:bold'>AI Insight</h4>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:16px'>{row.get('insight','')}</div>", unsafe_allow_html=True)
            if st.button("Generate Sales Proposal Text"):
                proposal = f"Dear {row['name']},\n\n{row['business_summary']}\n\n{row['sales_tip']}\n\nRecommended Next Action: {row['next_action']}\n\nBest regards,\n[Your Name]"
                st.code(proposal)
        else:
            st.warning("No details found for the selected contractor.")
    layers = [layer, text_layer, user_layer]
    if highlight_layer:
        layers.append(highlight_layer)
    r = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip={"text": "{tooltip}\n(See tooltip for info)"},
    )
    st.pydeck_chart(r)
else:
    st.info("No location data available for map visualization.")

st.subheader("Contractor Table")
if not df.empty:
    for idx, row in df.iterrows():
        # 防御性：如果row不是Series或dict，跳过
        if not (isinstance(row, pd.Series) or isinstance(row, dict)):
            continue
        with st.expander(f"{row['name']} ({row['city']}, {row['state']})"):
            # Show GAF website link
            if row.get('url'):
                st.markdown(f"[GAF Website]({row['url']})", unsafe_allow_html=True)
            # Show insights based on user role
            if user_role == "Sales Rep":
                st.markdown("<h4><b>Business Summary</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>{row.get('business_summary', '')}</div>", unsafe_allow_html=True)
                st.markdown("<h4><b>Sales Tip</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>{row.get('sales_tip', '')}</div>", unsafe_allow_html=True)
                st.markdown("<h4><b>Risk Alert</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>{row.get('risk_alert', '')}</div>", unsafe_allow_html=True)
                st.markdown("<h4><b>Priority Suggestion</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>{row.get('priority_suggestion', '')}</div>", unsafe_allow_html=True)
                st.markdown("<h4><b>Next Action</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>{row.get('next_action', '')}</div>", unsafe_allow_html=True)
            elif user_role == "Manager":
                st.markdown("<h4><b>Business Summary</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>{row.get('business_summary', '')}</div>", unsafe_allow_html=True)
                st.markdown("<h4><b>Priority Suggestion</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>{row.get('priority_suggestion', '')}</div>", unsafe_allow_html=True)
                st.markdown("<h4><b>AI Scores</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>Relevance: {row.get('relevance_score', '')}, Actionability: {row.get('actionability_score', '')}, Accuracy: {row.get('accuracy_score', '')}, Clarity: {row.get('clarity_score', '')}</div>", unsafe_allow_html=True)
                st.markdown("<h4><b>AI Comment</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>{row.get('evaluation_comment', '')}</div>", unsafe_allow_html=True)
            elif user_role == "Business Analyst":
                st.markdown("<h4><b>Business Summary</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>{row.get('business_summary', '')}</div>", unsafe_allow_html=True)
                st.markdown("<h4><b>AI Insight</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>{row.get('insight', '')}</div>", unsafe_allow_html=True)
                st.markdown("<h4><b>AI Scores</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>Relevance: {row.get('relevance_score', '')}, Actionability: {row.get('actionability_score', '')}, Accuracy: {row.get('accuracy_score', '')}, Clarity: {row.get('clarity_score', '')}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<h4><b>Business Summary</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>{row.get('business_summary', '')}</div>", unsafe_allow_html=True)
                st.markdown("<h4><b>AI Insight</b></h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px'>{row.get('insight', '')}</div>", unsafe_allow_html=True)
            # GAF官网链接已在上方显示
else:
    st.info("No contractors found for the current filters.")

# Export button
if st.button("Export as CSV"):
    export_resp = requests.get(f"{API_URL}/export", params=params)
    if export_resp.status_code == 200:
        st.download_button(
            label="Download CSV",
            data=export_resp.content,
            file_name="contractors_export.csv",
            mime="text/csv"
        )
    else:
        st.error("Export failed.")

# 仅Other角色显示调试信息
if user_role == "Other":
    st.write("Raw API data:", data)
    st.write("DataFrame columns:", df.columns) 