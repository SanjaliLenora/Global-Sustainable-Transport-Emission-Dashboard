import streamlit as st
import pandas as pd
import plotly.express as px

# PAGE CONFIG

st.set_page_config(page_title="Transport Emissions Dashboard", layout="wide")


# GLOBAL CSS

st.markdown("""
<style>
.stApp {
    background-color: black;
}

section[data-testid="stSidebar"] {
    background-color: black;
    padding-top: 20px;
}

section[data-testid="stSidebar"] > div {
    background-color: #111111;
    border-right: 1px solid white;
    padding: 20px;
}

label, .stSelectbox label, .stMultiSelect label {
    color: white !important;
    font-weight: 600;
}

h1, h2, h3, h4 {
    color: white !important;
}

div[data-baseweb="select"] {
    background-color: #1f2630 !important;
    border-radius: 8px !important;
}

div[data-baseweb="tag"] {
    background-color: #4da6ff !important;
    color: white !important;
    border-radius: 6px !important;
}

div[data-testid="stPlotlyChart"] {
    background-color: #1f2630;
    border: 1px solid white;
    border-radius: 12px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)


# LOAD DATA

@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_transport_emissions.csv")
    df.columns = df.columns.str.strip()
    return df

df = load_data()

# Remove world aggregate
df = df[df["Country"] != "World"]


# SIDEBAR FILTERS

st.sidebar.markdown("## Filter Panel")

years = sorted(df["Year"].unique())
selected_year = st.sidebar.selectbox("Select Year", years, index=len(years)-1)

countries = sorted(df["Country"].unique())

default_countries = (
    df[df["Year"] == df["Year"].max()]
    .sort_values(by="Emissions", ascending=False)
    .head(10)["Country"]
    .tolist()
)

selected_countries = st.sidebar.multiselect(
    "Select Countries",
    countries,
    default=default_countries
)

df_year = df[df["Year"] == selected_year]


# KPI CALCULATIONS

latest_year = df["Year"].max()
base_year = df["Year"].min()

df_latest = df[df["Year"] == latest_year]
df_base = df[df["Year"] == base_year]

total_latest = df_latest["Emissions"].sum()
total_base = df_base["Emissions"].sum()

growth_pct = ((total_latest - total_base) / total_base) * 100

top_country = df_latest.loc[df_latest["Emissions"].idxmax(), "Country"]

growth_df = df_latest.merge(df_base, on="Country", suffixes=("_latest", "_base"))
growth_df = growth_df[growth_df["Emissions_base"] > 50]

growth_df["Growth %"] = (
    (growth_df["Emissions_latest"] - growth_df["Emissions_base"])
    / growth_df["Emissions_base"]
) * 100

fastest_country = growth_df.loc[growth_df["Growth %"].idxmax(), "Country"]

# TITLE

st.markdown(
    "<h1 style='color:white;'>🌍 Global Sustainable Transport Emissions Dashboard</h1>",
    unsafe_allow_html=True
)


# KPI CARDS

col1, col2, col3, col4 = st.columns(4)

card_style = """
background-color:#1f2630;
padding:20px;
border:1px solid white;
border-radius:12px;
height:120px;
"""

with col1:
    st.markdown(f"""
    <div style="{card_style}">
        <div style="color:white;font-size:18px;">Global Total Emissions (2021)</div>
        <div style="color:white;font-size:28px;font-weight:bold;">{total_latest:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="{card_style}">
        <div style="color:white;font-size:18px;">Global Emission Growth Since 1990</div>
        <div style="color:white;font-size:28px;font-weight:bold;">{growth_pct:.2f}%</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="{card_style}">
        <div style="color:white;font-size:18px;">Highest Emitting Country</div>
        <div style="color:white;font-size:28px;font-weight:bold;">{top_country}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div style="{card_style}">
        <div style="color:white;font-size:18px;">Fastest Growing Major Emitter</div>
        <div style="color:white;font-size:28px;font-weight:bold;">{fastest_country}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

# COMMON CHART STYLE

common_layout = dict(
    plot_bgcolor='#1f2630',
    paper_bgcolor='#1f2630',
    font=dict(color='white'),
    title_font=dict(color='white', size=18),
    height=450,
    margin=dict(l=40, r=40, t=60, b=40),

)

# GLOBAL TREND

global_trend = df.groupby("Year")["Emissions"].sum().reset_index()

fig_line = px.line(
    global_trend,
    x="Year",
    y="Emissions",
    title="Global Transport Emissions Trend over time (1990-2021)"
)

fig_line.update_traces(line=dict(color="#4da6ff", width=3))
fig_line.update_layout(common_layout)


# WORLD MAP

fig_map = px.choropleth(
    df_year,
    locations="Country_Code",
    color="Emissions",
    hover_name="Country",
    title=f"Distribution of Transport Emissions by Country ({selected_year})",
    color_continuous_scale="RdPu"
)

fig_map.update_layout(common_layout)
fig_map.update_geos(bgcolor='#1f2630')


# TOP 10 HIGHEST EMITTERS

top10 = df_year.sort_values(by="Emissions", ascending=False).head(10)

fig_bar = px.bar(
    top10,
    x="Country",
    y="Emissions",
    title=f"Top 10 Highest Emitting Countries in {selected_year}"
)

fig_bar.update_traces(marker_color="#208dfa")
fig_bar.update_layout(common_layout)


# TOP 10 FASTEST GROWTH

top_growth = growth_df.sort_values(by="Growth %", ascending=False).head(10)

fig_growth = px.bar(
    top_growth,
    x="Growth %",
    y="Country",
    orientation="h",
    title="Top 10 Fastest Growing Major Transport Emitters Since 1990"
)

fig_growth.update_traces(marker_color="#4fd1c5")
fig_growth.update_layout(common_layout)


# HEATMAP
top_countries = df.groupby("Country")["Emissions"].sum().nlargest(10).index

heatmap_df = df[df["Country"].isin(top_countries)].pivot(
    index="Country",
    columns="Year",
    values="Emissions"
)

fig_heatmap = px.imshow(
    heatmap_df,
    aspect="auto",
    title="Heatmap of Emission Patterns Across Top 10 Highest Emitting Countries",
    color_continuous_scale="Blues"
)

fig_heatmap.update_layout(common_layout)

# HISTOGRAM FIXED

fig_hist = px.histogram(
    df_year,
    x="Emissions",
    nbins=30,
    title=f"Distribution of Country Level Transport Emissions in {selected_year}"
)

fig_hist.update_traces(marker_color="#4fd1c5")
fig_hist.update_layout(common_layout)

# DISPLAY
st.plotly_chart(fig_line, use_container_width=True)

st.plotly_chart(fig_map, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.plotly_chart(fig_growth, use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(fig_heatmap, use_container_width=True)

with col4:
    st.plotly_chart(fig_hist, use_container_width=True)