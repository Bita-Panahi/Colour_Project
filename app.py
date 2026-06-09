"""
Color Space Explorer — Streamlit App
=====================================
An interactive tool for colour scientists, engineers, and curious people.

Features
--------
Tab 1 - RGB Explorer
  • Pick a colour with a colour picker or type RGB values
  • Instant conversions: XYZ, CIE L*a*b*, HSV, hex
  • CIE 1931 xy chromaticity diagram showing where the colour sits

Tab 2 - Spectral Reflectance Viewer
  • Upload a CSV of spectral reflectance (wavelength | reflectance columns)
     - or choose from built-in reference samples
  • See the spectral curve, the derived CIE XYZ / L*a*b*, and colour swatch
  • Chromaticity diagram pin

Tab 3 - ΔE Color Comparison
  • Pick / enter two colours
  • Side-by-side swatches
  • ΔE CIE 2000 and ΔE 94 with a visual gauge and perceptual interpretation

Author: Bita Panahi - PhD Researcher, NTNU
"""

import streamlit as st
import numpy as np
import pandas as pd
import os
from scipy.interpolate import interp1d

from utils.conversions import (
    rgb_to_xyz, rgb_to_lab, rgb_to_hsv, rgb_to_xy,
    spectra_to_XYZ, spectra_to_lab, spectra_to_rgb_display,
    delta_e_2000, delta_e_94, interpret_delta_e,
    rgb_to_hex, WAVELENGTHS,
)
from utils.plots import (
    chromaticity_diagram,
    spectral_plot,
    color_swatch,
    delta_e_gauge,
    two_color_comparison,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Color_Project",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS — dark theme tweaks
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main { background-color: #0f0f1e; }
    .stApp { background-color: #0f0f1e; color: #e0e0f0; }
    .metric-card {
        background: #1a1a2e;
        border: 1px solid #333366;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 4px 0;
    }
    .metric-label { font-size: 0.75rem; color: #888; text-transform: uppercase; }
    .metric-value { font-size: 1.25rem; font-weight: 600; color: #e0e0ff; }
    h1, h2, h3 { color: #c0c0ff; }
    .stTabs [data-baseweb="tab"] { color: #aaa; }
    .stTabs [aria-selected="true"] { color: #fff; border-bottom-color: #7b68ee; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def metric_card(label: str, value: str):
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


SAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), "sample_data", "sample_spectra.csv")


@st.cache_data
def load_sample_spectra() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_DATA_PATH)


# ---------------------------------------------------------------------------
# App header
# ---------------------------------------------------------------------------
st.title("🎨 Color Space Explorer")
st.markdown(
    "Interactive colour science tool. Convert between colour spaces, "
    "visualise spectral reflectance, and measure perceptual colour differences."
)
st.divider()

tab_rgb, tab_spectral, tab_delta = st.tabs([
    "🟥 RGB Explorer",
    "📈 Spectral Reflectance",
    "🔀 ΔE Color Comparison",
])


# ===========================================================================
# TAB 1 — RGB Explorer
# ===========================================================================
with tab_rgb:
    st.subheader("RGB → XYZ / L*a*b* / HSV")

    col_input, col_results = st.columns([1, 2], gap="large")

    with col_input:
        st.markdown("**Pick or enter a colour**")

        hex_pick = st.color_picker("Colour picker", value="#3498db")

        # Parse hex from picker
        hex_clean = hex_pick.lstrip("#")
        r_pick = int(hex_clean[0:2], 16)
        g_pick = int(hex_clean[2:4], 16)
        b_pick = int(hex_clean[4:6], 16)

        st.markdown("**Or type RGB values (0–255)**")
        c1, c2, c3 = st.columns(3)
        r_in = c1.number_input("R", 0, 255, r_pick, key="r_in")
        g_in = c2.number_input("G", 0, 255, g_pick, key="g_in")
        b_in = c3.number_input("B", 0, 255, b_pick, key="b_in")

        # Use typed values as source of truth
        r, g, b = int(r_in), int(g_in), int(b_in)
        hex_color = rgb_to_hex(r, g, b)

        st.markdown(f"**Hex:** `{hex_color}`")
        st.plotly_chart(color_swatch(hex_color, label=hex_color),
                        use_container_width=False, config={"displayModeBar": False})

    with col_results:
        # --- Compute conversions ---
        xyz = rgb_to_xyz(r, g, b)
        lab = rgb_to_lab(r, g, b)
        h, s, v = rgb_to_hsv(r, g, b)
        cx, cy = rgb_to_xy(r, g, b)

        # --- Display metrics ---
        st.markdown("**Colour Space Values**")
        m1, m2, m3 = st.columns(3)

        with m1:
            metric_card("sRGB", f"({r}, {g}, {b})")
            metric_card("Hex", hex_color)
            metric_card("CIE x", f"{cx:.4f}")
            metric_card("CIE y", f"{cy:.4f}")

        with m2:
            metric_card("CIE X", f"{xyz[0]:.4f}")
            metric_card("CIE Y", f"{xyz[1]:.4f}")
            metric_card("CIE Z", f"{xyz[2]:.4f}")

        with m3:
            metric_card("L*", f"{lab[0]:.2f}")
            metric_card("a*", f"{lab[1]:.2f}")
            metric_card("b*", f"{lab[2]:.2f}")

        st.markdown("")
        mh, ms, mv = st.columns(3)
        mh.metric("Hue (°)", f"{h:.1f}")
        ms.metric("Saturation", f"{s:.3f}")
        mv.metric("Value", f"{v:.3f}")

        # --- Chromaticity diagram ---
        st.markdown("**CIE 1931 Chromaticity**")
        fig_chrom = chromaticity_diagram(cx, cy, label=hex_color,
                                         color_hex=hex_color)
        st.plotly_chart(fig_chrom, use_container_width=False,
                        config={"displayModeBar": False})

    # --- Explanation section ---
    with st.expander("📖 What do these values mean?"):
        st.markdown("""
**sRGB**: the standard red-green-blue values used by screens (0–255 per channel).

**CIE XYZ**: a device-independent colour space defined by the CIE in 1931, based on human cone sensitivity.
Y is closely related to *luminance* (perceived brightness).

**CIE L\*a\*b\***: a perceptually uniform space where equal numerical distances correspond to
roughly equal perceived colour differences.
- **L\*** = lightness (0 = black, 100 = white)
- **a\*** = green (−) to red (+)
- **b\*** = blue (−) to yellow (+)

**HSV**: Hue / Saturation / Value; intuitive for artists.
- Hue 0°/360° = red, 120° = green, 240° = blue.

**CIE xy chromaticity**: the *chromaticity* of a colour ignoring luminance.
The coloured horseshoe is the spectral locus; the dotted triangle is the sRGB gamut.
        """)


# ===========================================================================
# TAB 2 — Spectral Reflectance
# ===========================================================================
with tab_spectral:
    st.subheader("Spectral Reflectance → XYZ / L*a*b*")

    st.markdown(
        "Upload your own **CSV or Excel (.xlsx)** file with spectral reflectance data, "
        "or explore the built-in reference samples."
    )

    source = st.radio("Data source", ["Built-in reference samples", "Upload file (CSV or Excel)"],
                      horizontal=True)

    if source == "Built-in reference samples":
        df_spec = load_sample_spectra()
        sample_cols = [c for c in df_spec.columns if c != "wavelength_nm"]
        chosen = st.selectbox("Choose a reference sample", sample_cols)
        wavelengths = df_spec["wavelength_nm"].values.astype(float)
        reflectance = df_spec[chosen].values.astype(float)
        label = chosen.replace("_", " ")

    else:  # Upload
        uploaded = st.file_uploader(
            "Upload spectral data file",
            type=["csv", "xlsx"],
            help="CSV or Excel. Must have a wavelength column (nm) and one or more reflectance columns (0–1).",
        )
        if uploaded is None:
            st.info("Upload a CSV or Excel file to continue. Expected: a wavelength column + reflectance columns.")
            st.stop()

        # Load based on file type
        fname = uploaded.name.lower()
        if fname.endswith(".xlsx"):
            # Show sheet picker for Excel files
            import openpyxl
            wb = openpyxl.load_workbook(uploaded, read_only=True)
            sheet_names = wb.sheetnames
            wb.close()
            uploaded.seek(0)
            if len(sheet_names) > 1:
                chosen_sheet = st.selectbox("Sheet", sheet_names)
            else:
                chosen_sheet = sheet_names[0]
            df_up = pd.read_excel(uploaded, sheet_name=chosen_sheet)
        else:
            df_up = pd.read_csv(uploaded)

        all_cols = df_up.columns.tolist()
        wl_col  = st.selectbox("Wavelength column", all_cols, index=0)
        ref_col = st.selectbox("Reflectance column", all_cols, index=min(1, len(all_cols)-1))
        wavelengths = df_up[wl_col].values.astype(float)
        reflectance = df_up[ref_col].values.astype(float)
        label = ref_col

    # --- Resample to 5 nm / 380–780 nm grid (matches CMF and D65 files) ---
    R_5nm = np.clip(
        interp1d(wavelengths, reflectance, bounds_error=False, fill_value="extrapolate")(WAVELENGTHS),
        0.0, 1.0,
    )

    # --- Compute ---
    xyz_sp = spectra_to_XYZ(R_5nm)
    lab_sp = spectra_to_lab(R_5nm)
    r_disp, g_disp, b_disp = spectra_to_rgb_display(R_5nm)
    hex_sp = rgb_to_hex(r_disp, g_disp, b_disp)
    cx_sp = xyz_sp[0] / xyz_sp.sum() if xyz_sp.sum() > 0 else 0.3127
    cy_sp = xyz_sp[1] / xyz_sp.sum() if xyz_sp.sum() > 0 else 0.3290

    col_a, col_b = st.columns([2, 1], gap="large")

    with col_a:
        fig_sp = spectral_plot(wavelengths, reflectance, label=label,
                               color_hex=hex_sp)
        st.plotly_chart(fig_sp, use_container_width=True,
                        config={"displayModeBar": False})

        fig_sp_chrom = chromaticity_diagram(cx_sp, cy_sp, label=label,
                                             color_hex=hex_sp)
        st.plotly_chart(fig_sp_chrom, use_container_width=False,
                        config={"displayModeBar": False})

    with col_b:
        st.markdown("**Approximate display colour**")
        st.plotly_chart(color_swatch(hex_sp, label=hex_sp),
                        use_container_width=False, config={"displayModeBar": False})

        st.markdown("**Derived colour space values**")
        metric_card("CIE X", f"{xyz_sp[0]:.4f}")
        metric_card("CIE Y", f"{xyz_sp[1]:.4f}")
        metric_card("CIE Z", f"{xyz_sp[2]:.4f}")
        metric_card("L*", f"{lab_sp[0]:.2f}")
        metric_card("a*", f"{lab_sp[1]:.2f}")
        metric_card("b*", f"{lab_sp[2]:.2f}")
        metric_card("CIE x", f"{cx_sp:.4f}")
        metric_card("CIE y", f"{cy_sp:.4f}")
        metric_card("sRGB (approx)", f"({r_disp}, {g_disp}, {b_disp})")
        metric_card("Hex (approx)", hex_sp)

    with st.expander("📋 Raw spectral data"):
        df_show = pd.DataFrame({
            "Wavelength (nm)": wavelengths,
            "Reflectance": np.round(reflectance, 4),
        })
        st.dataframe(df_show, use_container_width=True, height=250)


# ===========================================================================
# TAB 3 — ΔE Color Comparison
# ===========================================================================
with tab_delta:
    st.subheader("ΔE Color Comparison")
    st.markdown(
        "Compare two colours and measure their **perceptual difference** "
        "using the ΔE CIE 2000 formula, the industry standard in colour quality control."
    )

    col_ca, col_cb = st.columns(2, gap="large")

    with col_ca:
        st.markdown("### Color A")
        hex_a = st.color_picker("Pick Color A", value="#e74c3c", key="hex_a")
        ha = hex_a.lstrip("#")
        ra_p, ga_p, ba_p = int(ha[0:2], 16), int(ha[2:4], 16), int(ha[4:6], 16)
        ca1, ca2, ca3 = st.columns(3)
        ra = ca1.number_input("R", 0, 255, ra_p, key="ra")
        ga = ca2.number_input("G", 0, 255, ga_p, key="ga")
        ba = ca3.number_input("B", 0, 255, ba_p, key="ba")
        hex_a_final = rgb_to_hex(int(ra), int(ga), int(ba))
        st.plotly_chart(color_swatch(hex_a_final, label=f"A: {hex_a_final}"),
                        use_container_width=False, config={"displayModeBar": False})

    with col_cb:
        st.markdown("### Color B")
        hex_b = st.color_picker("Pick Color B", value="#3498db", key="hex_b")
        hb = hex_b.lstrip("#")
        rb_p, gb_p, bb_p = int(hb[0:2], 16), int(hb[2:4], 16), int(hb[4:6], 16)
        cb1, cb2, cb3 = st.columns(3)
        rb = cb1.number_input("R", 0, 255, rb_p, key="rb")
        gb = cb2.number_input("G", 0, 255, gb_p, key="gb")
        bb = cb3.number_input("B", 0, 255, bb_p, key="bb")
        hex_b_final = rgb_to_hex(int(rb), int(gb), int(bb))
        st.plotly_chart(color_swatch(hex_b_final, label=f"B: {hex_b_final}"),
                        use_container_width=False, config={"displayModeBar": False})

    st.divider()

    # --- Compute ---
    lab_a = rgb_to_lab(int(ra), int(ga), int(ba))
    lab_b = rgb_to_lab(int(rb), int(gb), int(bb))
    de2000 = delta_e_2000(lab_a, lab_b)
    de94 = delta_e_94(lab_a, lab_b)
    interpretation = interpret_delta_e(de2000)

    # --- Side-by-side swatches ---
    st.plotly_chart(
        two_color_comparison(hex_a_final, hex_b_final, "Color A", "Color B"),
        use_container_width=False, config={"displayModeBar": False},
    )

    # --- ΔE gauge ---
    st.plotly_chart(delta_e_gauge(de2000), use_container_width=True,
                    config={"displayModeBar": False})

    # --- Metrics ---
    d1, d2, d3 = st.columns(3)
    d1.metric("ΔE CIE 2000", f"{de2000:.3f}")
    d2.metric("ΔE CIE 94", f"{de94:.3f}")
    d3.metric("Interpretation", interpretation.split("(")[0].strip())

    # --- L*a*b* table ---
    st.markdown("**L\*a\*b\* values**")
    df_lab = pd.DataFrame({
        "Color": ["A", "B", "Difference"],
        "L*": [f"{lab_a[0]:.2f}", f"{lab_b[0]:.2f}", f"{abs(lab_a[0]-lab_b[0]):.2f}"],
        "a*": [f"{lab_a[1]:.2f}", f"{lab_b[1]:.2f}", f"{abs(lab_a[1]-lab_b[1]):.2f}"],
        "b*": [f"{lab_a[2]:.2f}", f"{lab_b[2]:.2f}", f"{abs(lab_a[2]-lab_b[2]):.2f}"],
    })
    st.dataframe(df_lab, use_container_width=False, hide_index=True)

    with st.expander("📖 Understanding ΔE"):
        st.markdown("""
**ΔE CIE 2000** is the current industry standard for measuring perceptual colour difference.
It was designed to be more uniform than earlier metrics; equal ΔE values correspond to
approximately equal perceived differences across the colour gamut.

| ΔE CIE 2000 | Perception |
|---|---|
| < 1 | Imperceptible to the human eye |
| 1 – 2 | Perceptible only by trained observers |
| 2 – 3.5 | Perceptible at a glance |
| 3.5 – 5 | Colors are similar but clearly different |
| > 5 | Distinctly different colors |

**Applications:** paint and coating quality control (Jotun, Sherwin-Williams),
textile colour matching, display calibration, print proofing.

**ΔE 94** ΔE 94 improves on ΔE 76 by weighting the chroma and hue differences separately from lightness, making it more perceptually uniform, especially in saturated regions. 
It was the industry standard for textiles and coatings before CIEDE2000, and is still widely used in applications where a simpler formula than CIE 2000 is preferred.
        """)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Built by **Bita Panahi** - PhD in Computer Science (NTNU) · "
    "Specialisation: material appearance, colourscience, spectral BRDF  \n"
    "Tech: `colour-science` · `plotly` · `streamlit` · `numpy` · `scipy`  \n"
    "[GitHub](https://github.com/Bita-Panahi) · "
    "[LinkedIn](https://linkedin.com/in/bita-panahi-1994-)"
)
