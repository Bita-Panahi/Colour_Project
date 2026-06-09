"""
plots.py — Plotly visualisation utilities for the Color Space Explorer.

Functions:
  chromaticity_diagram(x, y, label)  — CIE 1931 xy diagram with the colour
                                        gamut boundary and a marker for the
                                        input colour
  spectral_plot(wavelengths, reflectance, label)
                                     — Spectral reflectance curve
  color_swatch(hex_color, label)     — Simple filled square swatch
  delta_e_gauge(de_value)            — A semicircular gauge for ΔE

Author: Bita Panahi
"""

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import colour


# ---------------------------------------------------------------------------
# CIE 1931 spectral locus (pre-computed from colour-science)
# ---------------------------------------------------------------------------

def _spectral_locus_xy():
    """Return (x_locus, y_locus) arrays tracing the CIE 1931 spectral locus."""
    cmfs = colour.MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]
    # cmfs.wavelengths gives 360–780 nm in 1 nm steps
    XYZ = cmfs.values  # shape (N, 3)
    total = XYZ.sum(axis=1)
    # Avoid division by zero at very low wavelengths
    mask = total > 0
    x = np.where(mask, XYZ[:, 0] / total, 0)
    y = np.where(mask, XYZ[:, 1] / total, 0)
    return x, y


_LOCUS_X, _LOCUS_Y = _spectral_locus_xy()


# ---------------------------------------------------------------------------
# CIE 1931 chromaticity background image (coloured gamut fill)
# ---------------------------------------------------------------------------

def _gamut_mesh_traces():
    """
    Returns a list of very thin scatter traces that paint the interior of the
    chromaticity diagram with approximate perceptual colours.  We sample a
    grid of (x, y) points inside the locus and map each to an sRGB colour.
    """
    from utils.conversions import rgb_to_hex

    traces = []
    step = 0.005
    xs = np.arange(0.0, 0.85, step)
    ys = np.arange(0.0, 0.85, step)

    # Build a polygon from the locus for point-in-polygon test
    from matplotlib.path import Path  # lightweight; only used here
    locus_path = Path(np.column_stack([_LOCUS_X, _LOCUS_Y]))

    marker_x, marker_y, marker_colors = [], [], []

    for xi in xs:
        for yi in ys:
            if xi + yi > 1.0:
                continue
            if not locus_path.contains_point((xi, yi)):
                continue
            z = 1.0 - xi - yi
            # XYZ normalised so Y = 0.4 (mid-luminance)
            Y = 0.4
            X = xi * Y / (yi if yi > 0 else 1e-6)
            Z = z * Y / (yi if yi > 0 else 1e-6)
            illuminant = colour.CCS_ILLUMINANTS[
                "CIE 1931 2 Degree Standard Observer"
            ]["D65"]
            rgb_enc = colour.XYZ_to_RGB(
                np.array([X, Y, Z]),
                colourspace="sRGB",
                illuminant=illuminant,
                apply_cctf_encoding=True,
            )
            rgb_enc = np.clip(rgb_enc, 0, 1)
            r, g, b = (int(round(c * 255)) for c in rgb_enc)
            marker_x.append(xi)
            marker_y.append(yi)
            marker_colors.append(rgb_to_hex(r, g, b))

    traces.append(go.Scatter(
        x=marker_x, y=marker_y,
        mode="markers",
        marker=dict(color=marker_colors, size=6, symbol="square"),
        hoverinfo="skip",
        showlegend=False,
        name="_gamut",
    ))
    return traces


# ---------------------------------------------------------------------------
# Public plot functions
# ---------------------------------------------------------------------------

def chromaticity_diagram(x: float, y: float, label: str = "Input colour",
                         color_hex: str = "#888888") -> go.Figure:
    """
    Plot the CIE 1931 xy chromaticity diagram with the spectral locus and a
    marker for the given (x, y) chromaticity.

    Parameters
    ----------
    x, y        : chromaticity coordinates
    label       : name shown in the legend
    color_hex   : sRGB hex of the colour being plotted
    """
    fig = go.Figure()

    # --- spectral locus boundary ---
    lx = list(_LOCUS_X) + [_LOCUS_X[0]]
    ly = list(_LOCUS_Y) + [_LOCUS_Y[0]]
    fig.add_trace(go.Scatter(
        x=lx, y=ly,
        mode="lines",
        line=dict(color="black", width=1.5),
        name="Spectral locus",
        showlegend=True,
    ))

    # --- sRGB triangle ---
    srgb_primaries = colour.RGB_COLOURSPACES["sRGB"].primaries  # shape (3, 2)
    wp = colour.RGB_COLOURSPACES["sRGB"].whitepoint
    tri_x = list(srgb_primaries[:, 0]) + [srgb_primaries[0, 0]]
    tri_y = list(srgb_primaries[:, 1]) + [srgb_primaries[0, 1]]
    fig.add_trace(go.Scatter(
        x=tri_x, y=tri_y,
        mode="lines",
        line=dict(color="grey", width=1, dash="dot"),
        name="sRGB gamut",
        showlegend=True,
    ))

    # --- D65 white point ---
    illuminant = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"]
    fig.add_trace(go.Scatter(
        x=[illuminant[0]], y=[illuminant[1]],
        mode="markers+text",
        marker=dict(color="white", size=8, line=dict(color="black", width=1)),
        text=["D65"], textposition="top right",
        name="D65 white point",
        showlegend=True,
    ))

    # --- input colour marker ---
    fig.add_trace(go.Scatter(
        x=[x], y=[y],
        mode="markers+text",
        marker=dict(color=color_hex, size=14,
                    line=dict(color="black", width=1.5)),
        text=[label], textposition="top right",
        name=label,
        showlegend=True,
    ))

    fig.update_layout(
        title="CIE 1931 xy Chromaticity Diagram",
        xaxis=dict(title="x", range=[0, 0.85], dtick=0.1),
        yaxis=dict(title="y", range=[0, 0.90], dtick=0.1, scaleanchor="x"),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="white",
                    borderwidth=1),
        width=560, height=520,
        margin=dict(l=50, r=20, t=50, b=50),
    )
    return fig


def spectral_plot(wavelengths: np.ndarray, reflectance: np.ndarray,
                  label: str = "Reflectance", color_hex: str = "#3af") -> go.Figure:
    """
    Plot a spectral reflectance curve.

    Parameters
    ----------
    wavelengths : 1-D array, nm
    reflectance : 1-D array, 0–1 scale
    label       : curve label
    color_hex   : line colour
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=wavelengths, y=reflectance,
        mode="lines",
        line=dict(color=color_hex, width=2.5),
        fill="tozeroy",
        fillcolor="rgba({},{},{},0.15)".format(
            int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16)
        ) if color_hex.startswith("#") and len(color_hex) == 7 else color_hex,
        name=label,
    ))
    fig.update_layout(
        title="Spectral Reflectance",
        xaxis=dict(title="Wavelength (nm)", range=[380, 780]),
        yaxis=dict(title="Reflectance", range=[0, 1.05]),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        legend=dict(bgcolor="rgba(0,0,0,0.3)"),
        width=580, height=350,
        margin=dict(l=50, r=20, t=50, b=50),
    )
    return fig


def color_swatch(hex_color: str, label: str = "") -> go.Figure:
    """Return a small filled rectangle as a colour swatch."""
    fig = go.Figure()
    fig.add_shape(
        type="rect", x0=0, y0=0, x1=1, y1=1,
        fillcolor=hex_color, line=dict(color="white", width=1),
    )
    fig.update_layout(
        title=f"Colour swatch: {label}",
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=hex_color,
        width=200, height=160,
        margin=dict(l=5, r=5, t=40, b=5),
        font=dict(color="white"),
    )
    return fig


def delta_e_gauge(de_value: float) -> go.Figure:
    """
    Render a simple horizontal bar gauge for a ΔE value (0 – 20 scale).
    Colour zones: green (0–1), yellow (1–3.5), orange (3.5–5), red (>5).
    """
    max_val = 20.0
    clamped = min(de_value, max_val)

    # Background zones
    zones = [
        (0, 1,   "#27ae60", "< 1: imperceptible"),
        (1, 3.5, "#f1c40f", "1–3.5: perceptible"),
        (3.5, 5, "#e67e22", "3.5–5: clearly different"),
        (5, 20,  "#e74c3c", "> 5: distinctly different"),
    ]

    fig = go.Figure()
    for z0, z1, col, name in zones:
        fig.add_shape(
            type="rect", x0=z0, y0=0, x1=z1, y1=1,
            fillcolor=col, opacity=0.35,
            line=dict(width=0),
        )

    # Needle line
    fig.add_shape(
        type="line", x0=clamped, y0=0, x1=clamped, y1=1,
        line=dict(color="white", width=3),
    )
    fig.add_annotation(
        x=clamped, y=1.15, text=f"ΔE = {de_value:.2f}",
        showarrow=False, font=dict(size=14, color="white"),
    )

    fig.update_layout(
        title="ΔE CIE 2000",
        xaxis=dict(title="ΔE", range=[0, max_val], dtick=2.5),
        yaxis=dict(visible=False, range=[0, 1.4]),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        width=580, height=180,
        margin=dict(l=50, r=20, t=50, b=50),
    )
    return fig


def two_color_comparison(hex1: str, hex2: str,
                         label1: str = "Color A",
                         label2: str = "Color B") -> go.Figure:
    """Side-by-side colour swatches for comparison."""
    fig = go.Figure()
    # Left swatch
    fig.add_shape(type="rect", x0=0, y0=0, x1=0.47, y1=1,
                  fillcolor=hex1, line=dict(color="white", width=1))
    # Right swatch
    fig.add_shape(type="rect", x0=0.53, y0=0, x1=1.0, y1=1,
                  fillcolor=hex2, line=dict(color="white", width=1))
    fig.add_annotation(x=0.235, y=-0.12, text=label1, showarrow=False,
                       font=dict(color="white", size=13))
    fig.add_annotation(x=0.765, y=-0.12, text=label2, showarrow=False,
                       font=dict(color="white", size=13))
    fig.update_layout(
        title="Side-by-side Comparison",
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[-0.25, 1]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#1a1a2e",
        width=400, height=200,
        margin=dict(l=10, r=10, t=40, b=30),
        font=dict(color="white"),
    )
    return fig
