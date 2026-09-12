
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, date, timedelta
import math, re

BASE = Path(__file__).parent
ASSET = BASE / "assets"
DATA = BASE / "detections.csv"
if not DATA.exists():
    DATA = Path("/mnt/data/detections.csv")

st.set_page_config(
    page_title="Bengaluru Urban Avian Bio-Acoustic Monitor",
    page_icon="🐦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root {
  --beige:#f3eadb;
  --beige2:#eadbc2;
  --ink:#202a24;
  --muted:#514f47;
  --leaf:#3f5f47;
  --leaf2:#6f8c63;
  --amber:#9a5f2e;
  --cream:#fffdf8;
  --line:#d8ccb8;
}

/* Global page */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"] {
  background: var(--beige) !important;
  color: var(--ink) !important;
}

[data-testid="stAppViewContainer"] * {
  color: var(--ink);
}

.block-container { padding-top: 1.2rem; padding-bottom: 3rem; }

/* Headings / markdown / normal text */
h1,h2,h3,h4,h5,h6,
.stMarkdown, .stMarkdown p, .stMarkdown span,
[data-testid="stText"], [data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] * {
  color: var(--ink) !important;
}

.small-note { color:var(--muted) !important; font-size:.92rem; }

/* Cards */
.card {
  background: var(--cream) !important;
  color: var(--ink) !important;
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1rem 1.1rem;
  box-shadow: 0 7px 24px rgba(70,55,35,.08);
}
.card * { color: var(--ink) !important; }

.hero {
  background: linear-gradient(135deg,#fbf4e8,#eadcc5) !important;
  color: var(--ink) !important;
  border:1px solid var(--line);
  border-radius:26px;
  padding:1.4rem 1.5rem;
  margin-bottom:1rem;
}
.hero h1, .hero p { color: var(--ink) !important; }

.pill {
  display:inline-block; padding:.35rem .65rem; border-radius:999px;
  background:#dce8d4 !important; color:#284530 !important;
  font-weight:700; font-size:.82rem;
  margin-right:.35rem; margin-bottom:.35rem;
}

/* Metrics */
[data-testid="stMetric"] {
  background: var(--cream) !important;
  border: 1px solid var(--line) !important;
  border-radius: 16px !important;
  padding: 0.75rem 0.9rem !important;
}
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] {
  color: var(--ink) !important;
}
[data-testid="stMetricLabel"] * { color: var(--muted) !important; }

/* Sidebar */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
  background: #eee2cd !important;
  color: var(--ink) !important;
}
section[data-testid="stSidebar"] * { color: var(--ink) !important; }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * { color: var(--muted) !important; }

/* Form controls */
.stSelectbox label, .stMultiSelect label, .stDateInput label,
.stNumberInput label, .stSlider label, .stTextInput label,
.stRadio label, .stCheckbox label {
  color: var(--ink) !important;
}
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div,
.stNumberInput input,
.stTextInput input,
.stDateInput input {
  background: var(--cream) !important;
  color: var(--ink) !important;
  border-color: var(--line) !important;
}
div[data-baseweb="popover"] * { color: var(--ink) !important; }

/* Tables / dataframes */
[data-testid="stDataFrame"] { background: var(--cream) !important; }
[data-testid="stDataFrame"] * { color: var(--ink) !important; }

/* Alerts */
div[data-testid="stAlert"] { color: var(--ink) !important; }
div[data-testid="stAlert"] * { color: var(--ink) !important; }

/* Links */
a { color: #2f6840 !important; font-weight: 600; }

a:hover { color: #20492c !important; }

/* Plotly/SVG text that otherwise follows a dark Streamlit theme */
.js-plotly-plot .plotly,
.js-plotly-plot .plot-container,
.js-plotly-plot .main-svg { background: transparent !important; }
.js-plotly-plot .xtick text,
.js-plotly-plot .ytick text,
.js-plotly-plot .gtitle,
.js-plotly-plot .legendtext,
.js-plotly-plot .annotation-text,
.js-plotly-plot .colorbar .cbaxis text,
.js-plotly-plot .axistext { fill: var(--ink) !important; }

/* Buttons */
.stButton button, .stDownloadButton button {
  background: var(--leaf) !important;
  color: #ffffff !important;
  border: none !important;
}
.stButton button:hover, .stDownloadButton button:hover {
  background: #314c38 !important;
  color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

PLOT_BG = "rgba(0,0,0,0)"
PLOT_PAPER = "rgba(0,0,0,0)"
PLOT_FONT = "#202a24"
GRID = "#d8ccb8"

def theme_fig(fig, height=None):
    kwargs = dict(
        paper_bgcolor=PLOT_PAPER,
        plot_bgcolor=PLOT_BG,
        font=dict(color=PLOT_FONT, family="Arial, sans-serif"),
        title_font=dict(color=PLOT_FONT),
        legend=dict(font=dict(color=PLOT_FONT)),
        margin=dict(l=20, r=20, t=55, b=35),
    )
    if height is not None:
        kwargs["height"] = height
    fig.update_layout(**kwargs)
    fig.update_xaxes(title_font=dict(color=PLOT_FONT), tickfont=dict(color=PLOT_FONT), gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(title_font=dict(color=PLOT_FONT), tickfont=dict(color=PLOT_FONT), gridcolor=GRID, zerolinecolor=GRID)
    return fig

@st.cache_data
def load_data():
    df = pd.read_csv(DATA)
    df["timestamp_raw"] = df["timestamp"].astype(str)
    # Current/legacy station files wrote the IST wall-clock with +00:00.
    # Preserve the displayed wall-clock as IST rather than shifting it again.
    df["timestamp_ist"] = pd.to_datetime(
        df["timestamp_raw"].str.replace(r"[+-]\d\d:\d\d$", "", regex=True),
        errors="coerce"
    )
    df["date"] = df["timestamp_ist"].dt.date
    df["hour"] = df["timestamp_ist"].dt.hour
    df["confidence_pct"] = df["confidence"] * 100
    df["rms"] = pd.to_numeric(df["rms"], errors="coerce")
    return df

df = load_data()
confirmed = df[df["detection_status"].eq("CONFIRMED")].copy()

# Source-derived bird information from the supplied Bangalore PDFs.
bird_info = {
    "Wren": {
        "sci":"Troglodytes troglodytes",
        "diet":"Insectivore",
        "foods":"Small insects and arthropods",
        "habitat":"Species-specific; use as a user-observed low-confidence field category.",
        "notes":"Observed by the project user and supported by low-confidence CSV events. Exact local species identity should be resolved before making a species-level conservation claim.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Not assigned here without exact species identification",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":None,
        "user_observed":True,
    },
    "Rose-ringed Parakeet": {
        "sci":"Psittacula krameri",
        "diet":"Fruit / seed feeder",
        "foods":"Fruit, grains and seeds",
        "habitat":"City, fields and fruit-gardens; often flocks",
        "notes":"Observed by the project user and supported by low-confidence CSV events; the supplied Bangalore guide notes evening flights into the city to roost.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":"rose_ringed_parakeet.png",
        "user_observed":True,
    },
    "Coppersmith Barbet": {
        "sci":"Psilopogon haemacephalus",
        "diet":"Fruit feeder",
        "foods":"Fruit and other plant foods",
        "habitat":"Trees and gardens",
        "notes":"Observed by the project user and supported by low-confidence CSV events; the supplied guide describes the repeated single-note call and exposed-tree perching.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":None,
        "user_observed":True,
    },
    "Common Tailorbird": {
        "sci":"Orthotomus sutorius",
        "diet":"Insectivore",
        "foods":"Insects and other small arthropods",
        "habitat":"Gardens and residential vegetation",
        "notes":"Observed by the project user and supported by low-confidence CSV events; the supplied guide notes leaf-binding nests in garden plants.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":None,
        "user_observed":True,
    },
    "Indian Robin": {
        "sci":"Corvus splendens",
        "diet":"Omnivore",
        "foods":"Insects, scraps and other opportunistic foods",
        "habitat":"Highly urban; gardens/open areas",
        "notes":"Widespread and common in the supplied Bangalore field guide.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Use species-source field below; not stated in supplied PDFs.",
        "icon":"house_crow.png",
    },
    "Common Myna": {
        "sci":"Acridotheres tristis",
        "diet":"Omnivore",
        "foods":"Insects, fruit and varied human-associated foods",
        "habitat":"Open urban areas; often on the ground",
        "notes":"The supplied guide notes ground-foraging for insects.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":"common_myna.png",
    },
    "Red-vented Bulbul": {
        "sci":"Pycnonotus cafer",
        "diet":"Fruit / mixed plant food; broad diet",
        "foods":"Fruits and other plant material; insects can supplement diet",
        "habitat":"Scrub and garden land",
        "notes":"The supplied Bangalore guide places bulbuls in scrub and garden habitats.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":None,
    },
    "Red-whiskered Bulbul": {
        "sci":"Pycnonotus jocosus",
        "diet":"Fruit / mixed diet",
        "foods":"Fruit and soft plant foods; insects also taken",
        "habitat":"Scrub and gardens",
        "notes":"The supplied guide says bulbuls occur in scrub and garden land and can occur in the city centre.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":None,
    },
    "Purple Sunbird": {
        "sci":"Cinnyris asiaticus",
        "diet":"Nectar feeder",
        "foods":"Nectar; insects especially when feeding young",
        "habitat":"Parks and gardens with flowering trees/shrubs",
        "notes":"The supplied Bangalore guide explicitly describes nectar feeding in flowering habitats.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":None,
    },
    "White-throated Kingfisher": {
        "sci":"Halcyon smyrnensis",
        "diet":"Insectivore / small aquatic-terrestrial prey",
        "foods":"Fish and other small prey; insects",
        "habitat":"Open urban areas; often perched away from water too",
        "notes":"The supplied guide says it is often seen away from water on electric wires.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":None,
    },
    "House Sparrow": {
        "sci":"Passer domesticus",
        "diet":"Omnivore / granivore",
        "foods":"Seeds/grains and insects",
        "habitat":"Human-associated nesting sites/buildings",
        "notes":"The supplied guide says House Sparrow is declining in Bangalore and commoner on the outskirts.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Average lifespan about 3 years (external source).",
        "icon":"house_sparrow.png",
    },
    "Rose-ringed Parakeet": {
        "sci":"Psittacula krameri",
        "diet":"Fruit / seed feeder",
        "foods":"Fruit and grains",
        "habitat":"City, fields and fruit-gardens; often flocks",
        "notes":"The supplied guide notes evening movements into the city to roost.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":"rose_ringed_parakeet.png",
    },
    "Black Kite": {
        "sci":"Milvus migrans",
        "diet":"Scavenger / carnivore",
        "foods":"Carrion and other opportunistic food",
        "habitat":"Urban and open areas",
        "notes":"The supplied guide calls it a widespread and common scavenger.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":"black_kite.png",
    },
    "Brahminy Kite": {
        "sci":"Haliastur indus",
        "diet":"Carnivore / scavenger",
        "foods":"Fish and other aquatic/terrestrial prey",
        "habitat":"Often near water",
        "notes":"The supplied guide highlights its association with water.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":"brahminy_kite.png",
    },
    "Blue Rock-Pigeon": {
        "sci":"Columba livia",
        "diet":"Granivore",
        "foods":"Seeds and grain",
        "habitat":"Buildings and urban structures",
        "notes":"The supplied guide describes its adaptation from cliffs to tall buildings.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":"blue_rock_pigeon.png",
    },
    "Jungle Myna": {
        "sci":"Acridotheres fuscus",
        "diet":"Insectivore / omnivore",
        "foods":"Insects and ground-foraged foods",
        "habitat":"Open areas and ground foraging",
        "notes":"The supplied guide notes a forehead feather tuft and insect foraging.",
        "pdf":"common_bangalore_birds.pdf",
        "status":"Least Concern (global)",
        "lifespan":"Not stated in supplied PDFs.",
        "icon":"jungle_myna.png",
    },
}


# Local image assets: the dashboard deliberately maps detected species to the
# supplied generic bird-category images. Exact/specific images take priority
# for bulbuls, crows, barbets, myna, tailorbird and Purple Sunbird.
def _asset_file(folder: str, stem: str):
    folder_path = ASSET / folder
    if not folder_path.exists():
        return None
    stem_norm = stem.lower().replace("-", "_").replace(" ", "_")
    for p in folder_path.iterdir():
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            p_norm = p.stem.lower().replace("-", "_").replace(" ", "_")
            if p_norm == stem_norm:
                return p
    return None

def bird_image_for_species(species: str):
    """Return a supplied local image for the detected/model species.
    Specific project images are kept where requested; otherwise a generic
    category image is used for the detected bird-name family."""
    s = re.sub(r"[^a-z0-9]+", " ", str(species).lower()).strip()

    # Project-specific images: preserve these instead of generic categories.
    specific = [
        (("red vented bulbul",), "red_vented_bulbul"),
        (("red whiskered bulbul",), "red_whiskered_bulbul"),
        (("bulbul",), "red_vented_bulbul"),
        (("house crow", "jungle crow", "crow", "rook"), "house_crow"),
        (("barbet", "barbett"), "white_cheeked_barbett"),
        (("purple sunbird",), "purple_sunbird"),
        (("common myna", "myna"), "common_myna"),
        (("common tailorbird", "tailorbird"), "common_tailorbird"),
    ]
    for keys, stem in specific:
        if any(k in s for k in keys):
            p = _asset_file("birds", stem)
            if p is not None:
                return p, f"Specific project image: {p.name}"

    # Generic category images supplied by the user.
    generic = [
        (("hornbill",), "hornbill"),
        (("kingfisher",), "kingfisher"),
        (("owl",), "owl"),
        (("parakeet",), "parakeet"),
        (("pigeon",), "pigeon"),
        (("dove",), "dove"),
        (("drongo",), "drongo"),
        (("heron", "bittern", "egret"), "heron"),
        (("oriole",), "oriole"),
        (("robin",), "robin"),
        (("sparrow",), "sparrow"),
        (("wren",), "wren"),
        (("nightingale",), "nightingale"),
    ]
    for keys, stem in generic:
        if any(k in s for k in keys):
            p = _asset_file("birds", stem)
            if p is not None:
                return p, f"Generic category image: {p.name}"

    return None, "No supplied category image matches this BirdNET label."

badge = ""

def food_image_for_label(label: str):
    food_map = {
        "Fruit": "fruits",
        "Seeds / grains": "seeds",
        "Nectar / flowers": "nectar",
        "Insects": "insects",
        "Fish / aquatic prey": "fish",
    }
    stem = food_map.get(label)
    if stem:
        p = _asset_file("food", stem)
        if p is not None:
            return p
    return None

# Sidebar

st.sidebar.markdown("## 🐦 Monitor controls")
min_d = df["date"].min()
max_d = df["date"].max()
date_range = st.sidebar.date_input("Observation dates", value=(min_d, max_d), min_value=min_d, max_value=max_d)
if isinstance(date_range, tuple) and len(date_range)==2:
    d0,d1=date_range
else:
    d0=d1=date_range

status_options = sorted(df["detection_status"].dropna().unique())
statuses = st.sidebar.multiselect("Event classes", status_options, default=status_options)

species_options = sorted(confirmed["species"].unique())
sel_species = st.sidebar.multiselect("Confirmed species", species_options, default=species_options)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📍 Vicinity map")
lat = st.sidebar.number_input("Latitude", value=12.9716, format="%.6f")
lon = st.sidebar.number_input("Longitude", value=77.5946, format="%.6f")
radius_km = st.sidebar.slider("Radius (km)", 3.0, 4.0, 4.0, 0.5)
st.sidebar.caption("Enter your observation coordinates to highlight your actual 3–4 km vicinity. Precise device location is not inferred by this dashboard.")

f = df[(df["date"]>=d0)&(df["date"]<=d1)]
if statuses:
    f = f[f["detection_status"].isin(statuses)]
fc = f[f["detection_status"].eq("CONFIRMED")]
if sel_species:
    fc = fc[fc["species"].isin(sel_species)]

# Hero
st.markdown("""
<div class="hero">
  <div class="pill">EDGE AI</div>
  <div class="pill">BIRDNET v2.4</div>
  <div class="pill">URBAN LOW-SNR</div>
  <div class="pill">BENGALURU</div>
  <h1>Urban Avian Bio-Acoustic Observatory</h1>
  <p class="small-note">A field-facing dashboard for real-time acoustic monitoring, urban habitat context, false-positive analysis and conservation storytelling.</p>
</div>
""", unsafe_allow_html=True)

# KPIs
k1,k2,k3,k4,k5 = st.columns(5)
k1.metric("Events recorded", f"{len(f):,}")
k2.metric("Confirmed detections", f"{len(fc):,}")
k3.metric("Confirmed species", f"{fc['species'].nunique():,}")
k4.metric("Non-whitelisted / rejected", f"{int((f['detection_status']=='NON_WHITELISTED').sum()):,}")
k5.metric("Low-confidence events", f"{int((f['detection_status']=='LOW_CONFIDENCE').sum()):,}")

st.markdown("### 🖼️ Local bird-image mapping")
st.info(
    "Every detected BirdNET label is matched to a supplied local image whenever its name contains "
    "one of the configured bird categories. Generic categories include dove, drongo, heron/bittern/egret, "
    "hornbill, oriole, owl, parakeet, pigeon, robin, sparrow, wren, nightingale and kingfisher. "
    "Specific supplied images are retained for bulbuls, crows, barbets, Purple Sunbird, Common Myna and "
    "Common Tailorbird. The image is a visual reference category, not a species-level identification."
)

mapping_preview = pd.DataFrame([
    ["Barn Owl", "owl.png", "Generic"],
    ["Grey Hornbill", "hornbill.png", "Generic"],
    ["Black Drongo", "drongo.png", "Generic"],
    ["White-throated Kingfisher", "kingfisher.png", "Generic"],
    ["Ring-necked Parakeet", "parakeet.png", "Generic"],
    ["Red-vented Bulbul", "red_vented_bulbul.png", "Specific"],
    ["Red-whiskered Bulbul", "red_whiskered_bulbul.png", "Specific"],
    ["House Crow", "house_crow.png", "Specific"],
    ["Coppersmith Barbet", "white_cheeked_barbett.jpeg", "Specific"],
], columns=["Detected label", "Local image", "Mapping type"])
st.dataframe(mapping_preview, use_container_width=True, hide_index=True)

st.markdown("### 🌿 What the station is hearing")
c1,c2 = st.columns([1.15, 1])
with c1:
    counts = fc["species"].value_counts().reset_index()
    counts.columns = ["species","detections"]
    if len(counts):
        fig=px.bar(counts, x="detections", y="species", orientation="h",
                   title="Confirmed acoustic detections",
                   labels={"species":"","detections":"Confirmed detections"})
        theme_fig(fig, 410)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No confirmed detections for the current filter.")
with c2:
    hour_counts = fc.groupby("hour").size().reindex(range(24), fill_value=0)
    fig=px.line(x=hour_counts.index, y=hour_counts.values, markers=True,
                title="Confirmed bird activity by hour (station time)",
                labels={"x":"Hour (IST)","y":"Detections"})
    fig.update_xaxes(dtick=1)
    fig.update_layout(height=410, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### 🔎 Low-SNR & false-positive laboratory")
c1,c2 = st.columns(2)
with c1:
    stat = f.groupby("detection_status").size().reset_index(name="events")
    fig=px.pie(stat, names="detection_status", values="events", hole=.55,
               title="What the model produced")
    fig.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
with c2:
    ff = f.dropna(subset=["rms","confidence_pct"]).copy()
    fig=px.scatter(ff, x="rms", y="confidence_pct", color="detection_status",
                   hover_data=["species","timestamp_raw"],
                   title="Confidence vs acoustic energy (RMS)",
                   labels={"rms":"Window RMS","confidence_pct":"BirdNET score (%)"})
    fig.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### 🕒 Species occurrence across the day")
if len(fc):
    heat=fc.pivot_table(index="species", columns="hour", values="confidence", aggfunc="count", fill_value=0)
    heat=heat.reindex(columns=range(24), fill_value=0)
    fig=px.imshow(heat, aspect="auto", color_continuous_scale="YlGnBu",
                  labels={"x":"Hour (IST)","y":"Species","color":"Detections"})
    fig.update_layout(height=max(340, 55*len(heat)), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### 🍎 Bird diets & habitat cues")
diet_cols = st.columns(3)
diet_icon = {"Omnivore":"seeds.png","Granivore":"seeds.png","Fruit / mixed plant food":"fruit.png",
             "Fruit / mixed diet":"fruit.png","Fruit / seed feeder":"fruit.png",
             "Nectar feeder":"nectar.png","Insectivore / small aquatic-terrestrial prey":"insects.png",
             "Insectivore / omnivore":"insects.png","Insectivore":"insects.png",
             "Carnivore / scavenger":"fish.png","Scavenger / carnivore":"fish.png"}
for i, sp in enumerate(sorted(set(fc["species"]).intersection(bird_info.keys()))):
    info=bird_info[sp]
    col=diet_cols[i%3]
    with col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        img_path, img_note = bird_image_for_species(sp)
        if img_path is not None:
            st.image(str(img_path), width=220, caption=img_note)
        else:
            st.caption(img_note)

        st.markdown(f"**{sp}**{badge}")
        st.caption(info["sci"])
        st.write(f"**Diet:** {info['diet']}")
        st.write(f"**Habitat:** {info['habitat']}")
        st.caption(info["notes"])
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### 👁️ Field observations + acoustic evidence")
st.info(
    "These entries are shown because they were personally observed in the field. "
    "Where the CSV contains a low-confidence or differently named BirdNET prediction, "
    "that evidence is shown separately rather than silently upgrading it to a confirmed "
    "species identification."
)

observations = [
    ("Rose-ringed / Ring-necked Parakeet", "Field observed", 
     "CSV also contains BirdNET predictions labelled 'Ring-necked Parakeet'."),
    ("Barbets", "Field observed",
     "CSV contains low-confidence Coppersmith Barbet and Crested Barbet predictions."),
    ("Wren", "Field observed",
     "CSV contains low-confidence Canyon Wren; other wren labels are treated as model outputs, not local confirmation."),
    ("Robin", "Field observed",
     "The CSV contains a low-confidence Rüppell's Robin-Chat prediction; this is not treated as proof of Indian Robin."),
    ("Tailorbird", "Field observed",
     "CSV contains a low-confidence Green-backed Tailorbird result and repeated Common Tailorbird outputs; these remain separate from confirmed local acoustic detections."),
]
st.dataframe(
    pd.DataFrame(
        observations,
        columns=["Field observation", "Evidence basis", "Acoustic-data note"]
    ),
    use_container_width=True,
    hide_index=True,
)


# Add exact BirdNET output spellings encountered in the research CSV.
bird_info.setdefault("Ring-necked Parakeet", bird_info.get("Rose-ringed Parakeet", {}).copy())
bird_info.setdefault("Crested Barbet", {
    "sci":"Psilopogon sp.",
    "diet":"Fruit feeder",
    "foods":"Fruit and plant foods",
    "habitat":"Trees and gardens",
    "notes":"Model output encountered in the supplied CSV; exact species identity should be verified before ecological interpretation.",
    "pdf":"Not identified in supplied Bangalore PDF.",
    "status":"Verify species before assigning status",
    "lifespan":"Not stated in supplied PDFs.",
    "icon":None,
    "user_observed":False,
})
bird_info.setdefault("Canyon Wren", {
    "sci":"Catherpes mexicanus",
    "diet":"Insectivore",
    "foods":"Insects and arthropods",
    "habitat":"Not treated as a confirmed Bengaluru species here.",
    "notes":"Low-confidence model output only; included for false-positive/threshold analysis.",
    "pdf":"Not identified in supplied Bangalore PDF.",
    "status":"Not assigned for Bengaluru",
    "lifespan":"Not stated in supplied PDFs.",
    "icon":None,
    "user_observed":False,
})
bird_info.setdefault("Green-backed Tailorbird", {
    "sci":"Orthotomus sepium",
    "diet":"Insectivore",
    "foods":"Insects and small arthropods",
    "habitat":"Not treated as a confirmed Bengaluru species here.",
    "notes":"Low-confidence model output only; included for false-positive/threshold analysis.",
    "pdf":"Not identified in supplied Bangalore PDF.",
    "status":"Not assigned for Bengaluru",
    "lifespan":"Not stated in supplied PDFs.",
    "icon":None,
    "user_observed":False,
})

st.markdown("### 🍎 What they eat — real reference photographs")
food_cols = st.columns(5)
food_labels = ["Fruit", "Seeds / grains", "Nectar / flowers", "Insects", "Fish / aquatic prey"]
for i, food_name in enumerate(food_labels):
    with food_cols[i]:
        img = food_image_for_label(food_name)
        if img is not None:
            st.image(str(img), width=150)
        st.markdown(f"**{food_name}**")
st.caption(
    "These are the real local food/prey photographs supplied in assets/food. "
    "They illustrate food categories, not a claim that every individual species consumes the pictured item."
)

st.markdown("### 🐦 Species profile & conservation status")
st.caption(
    "Species cards use the supplied local bird-category photographs. Exact project images are used "
    "for bulbuls, crows, barbets, myna, tailorbird and Purple Sunbird; other BirdNET labels are "
    "hooked to the closest supplied generic bird category (for example Barn Owl → owl.png, "
    "Grey Hornbill → hornbill.png)."
)

rows=[]
profile_species = set(fc["species"]).union(
    {
        "Rose-ringed Parakeet",
        "Coppersmith Barbet",
        "Wren",
        "Indian Robin",
        "Common Tailorbird",
    }
)

for sp in sorted(profile_species):
    if sp not in bird_info:
        continue
    info=bird_info[sp]
    n=int((fc["species"]==sp).sum())
    rows.append({
        "Species":sp,
        "Scientific name":info["sci"],
        "Confirmed detections":n,
        "Global IUCN":info["status"],
        "Diet":info["diet"],
        "Habitat":info["habitat"],
        "Lifespan note":info["lifespan"],
        "Source":info["pdf"],
    })
if rows:
    st.dataframe(pd.DataFrame(rows).sort_values(["Confirmed detections","Species"], ascending=[False,True]),
                 use_container_width=True, hide_index=True)
st.caption("Conservation categories shown here are global IUCN status, not Bengaluru population status. The supplied Bangalore PDFs do not themselves provide IUCN categories or lifespan values; those fields are clearly separated from source-derived habitat/diet notes.")

st.markdown("### 🌳 Bengaluru green infrastructure & habitat context")
c1,c2 = st.columns(2)
with c1:
    p=ASSET/"blr-tree-census-286k.png"
    if p.exists():
        st.image(str(p), caption="Bengaluru tree census infographic supplied for this project.")
with c2:
    p=ASSET/"bbmp tree survey.jpeg"
    if p.exists():
        st.image(str(p), caption="BBMP tree survey / tree distribution map supplied for this project.")
st.caption("The supplied 1981 Garden Birds of Bangalore paper argues that gardens and remaining natural vegetation become increasingly important refuges as wooded areas are lost to urbanization, and that ~80% of the garden birds it surveyed preferred woodland. (source: Garden Birds of Bangalore, supplied project reference)")

st.markdown("### 🏙️ Urban form & acoustic pressure")
p=ASSET/"building heights survey bangalore.jpeg"
if p.exists():
    st.image(str(p), caption="Ward-wise average building heights, Bengaluru — supplied project reference.")

st.markdown("### 📍 Vicinity / nearby habitat map")
st.info("The dashboard requires your observation latitude/longitude to highlight your actual 3–4 km vicinity. The current default is central Bengaluru only and is not your inferred location.")
try:
    import folium
    from streamlit_folium import st_folium

    m=folium.Map(location=[lat,lon], zoom_start=12, tiles="OpenStreetMap")
    folium.Circle([lat,lon], radius=radius_km*1000, color="#7c5c3d", fill=True, fill_opacity=.10).add_to(m)
    folium.Marker([lat,lon], tooltip="Observation / station vicinity",
                 icon=folium.Icon(color="green", icon="leaf")).add_to(m)

    # Broad Bengaluru ecological reference points; exact nearby set should be
    # populated after the user enters their coordinates.
    places=[
        ("Lalbagh Botanical Garden",12.9507,77.5848,"Park / botanical garden"),
        ("Cubbon Park",12.9763,77.5929,"Urban woodland / park"),
        ("Hebbal Lake",13.0358,77.5984,"Waterbody"),
        ("Sankey Tank",13.0050,77.5736,"Waterbody"),
        ("Jakkur Lake",13.0775,77.6027,"Waterbody"),
        ("Kaikondrahalli Lake",12.9281,77.6897,"Waterbody"),
    ]
    for name,la,lo,kind in places:
        dlat=math.radians(la-lat); dlon=math.radians(lo-lon)
        a=math.sin(dlat/2)**2+math.cos(math.radians(lat))*math.cos(math.radians(la))*math.sin(dlon/2)**2
        dist=6371*2*math.asin(math.sqrt(a))
        if dist <= radius_km*1.4:
            folium.Marker([la,lo], tooltip=f"{name} • {kind} • {dist:.1f} km",
                          icon=folium.Icon(color="blue" if "Water" in kind else "green",
                                           icon="tint" if "Water" in kind else "tree")).add_to(m)
    st_folium(m, width=None, height=520)
except Exception as e:
    st.warning(f"Interactive map dependencies are not installed yet: {e}")

st.markdown("### 🌅 Daylight rhythm")
# Visual-only sunrise/sunset horizon; daily exact times can be added later from a
# sunrise/sunset API once the station location is fixed.
now= datetime.now()
minutes = now.hour*60+now.minute
sunrise=6*60
sunset=18*60+15
x=np.linspace(0,24,240)
y=np.sin((x-6)/12*np.pi)
fig=go.Figure()
fig.add_trace(go.Scatter(x=x,y=y,mode="lines",fill="tozeroy",line=dict(width=3)))
fig.add_vline(x=minutes/60,line_dash="dash")
fig.add_vline(x=sunrise/60,line_dash="dot")
fig.add_vline(x=sunset/60,line_dash="dot")
fig.update_layout(title=f"Daylight horizon — {now.strftime('%d %b %Y')}",
                  xaxis_title="Hour", yaxis_title="Horizon phase",
                  height=260, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig, use_container_width=True)

st.markdown("### 📅 Observation calendar")
daily = f.groupby("date").size().reset_index(name="events")
if len(daily):
    cal=px.bar(daily, x="date", y="events", title="Recorded acoustic events by day")
    cal.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(cal, use_container_width=True)

st.markdown("### 📡 Station health")
latest=df["timestamp_ist"].max()
age=None if pd.isna(latest) else (pd.Timestamp.now()-latest).total_seconds()/60
a,b,c=st.columns(3)
a.metric("Latest dataset timestamp", "—" if pd.isna(latest) else latest.strftime("%Y-%m-%d %H:%M IST"))
b.metric("Latest known battery", f"{int(df['battery'].dropna().iloc[-1])}%" if df["battery"].notna().any() else "N/A")
c.metric("Data freshness", "Recent" if age is not None and abs(age)<60*24 else "Historical dataset")

st.markdown("### 📰 Bird Spotters of Bangalore")
reddit_links = [
    ("Birds of Lalbagh — 2026", "https://www.reddit.com/r/bangalore/comments/1rvcjyl/birds_of_lalbagh/"),
    ("Rich bird biodiversity in Bangalore", "https://www.reddit.com/r/bangalore/comments/1s6og7i/rich_bird_biodiversity_in_bangalore/"),
    ("Cubbon Park mornings", "https://www.reddit.com/r/bangalore/comments/1o4hny2/cubbon_park_mornings_are_a_bliss/"),
    ("Trees disappearing / urban habitat loss", "https://www.reddit.com/r/bangalore/comments/1rnxwhr/seeing_an_area_full_of_trees_vanish_into_thin_air/"),
    ("Tree being cut — conservation discussion", "https://www.reddit.com/r/bangalore/comments/1sv45fp/tree_being_cut_what_can_i_do/"),
    ("Your supplied Reddit post", "https://www.reddit.com/r/bangalore/s/mEQoF21CcO"),
]
for title,url in reddit_links:
    st.markdown(f"- [{title}]({url})")


st.markdown("### 🍎 Food-photo assets")
food_rows = []
for label in ["Fruit", "Seeds / grains", "Nectar / flowers", "Insects", "Fish / aquatic prey"]:
    img = food_image_for_label(label)
    food_rows.append((label, img.name if img is not None else "Missing"))
st.dataframe(pd.DataFrame(food_rows, columns=["Food / prey", "Local asset"]), use_container_width=True, hide_index=True)

st.markdown("### 📚 Source shelf")
st.markdown("""
**Supplied project references**
- `common_bangalore_birds.pdf` — species illustrations, Bangalore field notes and habitat/food clues.
- `gardenbirdsofbangalore.pdf` — long-form habitat, trophic, garden-management and historical Bangalore bird observations.
- `blr-tree-census-286k.png` and `bbmp tree survey.jpeg` — urban tree context.
- `building heights survey bangalore.jpeg` — urban form context.
- `grey hornbill detection.jpeg` — example visual evidence from the project.
- User-observed species are explicitly separated from confirmed acoustic detections.

**External research sources used for status cross-checking**
- IUCN Red List
- State of India's Birds
- Cornell Lab / All About Birds
""")

st.caption("Design note: the dashboard deliberately separates model output, temporal confirmation, habitat interpretation and conservation status. It should not be read as proving a causal link between tree removal and any single species trend.")
