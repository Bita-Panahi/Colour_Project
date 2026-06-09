"""
conversions.py - Color space conversions using YOUR CMF and D65 Excel files.

All XYZ / sRGB / L*a*b* calculations are a direct Python translation of the
MATLAB code (Phil Green's Colour Engineering Toolbox + your lab workflow).
No colour-science library is used for the core math.

Colour-science is only used for:
  - ΔE CIE 2000 / CIE 76  (no custom formula was provided)
  - sRGB → XYZ back-conversion (for the RGB Explorer tab)
  - HSV conversion

Reference:
  CIE 15:2004, xyz2srgb.m / xyz2lab.m by Phil Green
  MATLAB script: XYZ and RGB calculations (Bita Panahi)

Author: Bita Panahi
"""

import pathlib
import numpy as np
import pandas as pd
import colour  # only for ΔE and the RGB-Explorer back-conversions

# ---------------------------------------------------------------------------
# Load CMF and D65 from Excel — 380–780 nm, 5 nm intervals
# ---------------------------------------------------------------------------
_HERE    = pathlib.Path(__file__).parent.parent  # project root
_CMF_FILE = _HERE / "CMF_2deg_5nm.xlsx"
_D65_FILE = _HERE / "D65_5nm.xlsx"

def _load_references():
    """Load CMF and D65 from Excel, filter to 380–780 nm, return arrays."""
    df_cmf = pd.read_excel(_CMF_FILE, sheet_name="Tabelle1")
    mask_c = (df_cmf["Wavelength"] >= 380) & (df_cmf["Wavelength"] <= 780)
    df_cmf = df_cmf[mask_c].reset_index(drop=True)

    df_d65 = pd.read_excel(_D65_FILE, sheet_name="Tabelle1")
    mask_d = (df_d65["l"] >= 380) & (df_d65["l"] <= 780)
    df_d65 = df_d65[mask_d].reset_index(drop=True)

    wl    = df_cmf["Wavelength"].values.astype(float)   # 380–780 nm, 81 pts
    xbar  = df_cmf["xbar"].values.astype(float)
    ybar  = df_cmf["ybar"].values.astype(float)
    zbar  = df_cmf["zbar"].values.astype(float)
    d65   = df_d65["D65"].values.astype(float)

    # Normalisation constant — MATLAB: k = 100 / sum(D65' * ybar)
    k = 100.0 / np.sum(d65 * ybar)

    # Whitepoint (XYZ of perfect white reflector, R=1 everywhere)
    Xn = k * np.sum(d65 * xbar)   # ≈ 95.04
    Yn = k * np.sum(d65 * ybar)   # = 100.00 by construction
    Zn = k * np.sum(d65 * zbar)   # ≈ 108.89

    return wl, xbar, ybar, zbar, d65, k, np.array([Xn, Yn, Zn])


WAVELENGTHS, XBAR, YBAR, ZBAR, D65, K, XYZ_WHITE = _load_references()

# sRGB linear-to-XYZ matrix (IEC 61966, Phil Green xyz2srgb.m)
_M_XYZ_TO_SRGB = np.array([
    [ 3.2410, -1.5374, -0.4986],
    [-0.9692,  1.8760,  0.0416],
    [ 0.0556, -0.2040,  1.0570],
])


# ---------------------------------------------------------------------------
# Core functions (direct translation of MATLAB)
# ---------------------------------------------------------------------------

def spectra_to_XYZ(reflectance: np.ndarray) -> np.ndarray:
    """
    Convert a spectral reflectance curve to CIE XYZ.

    Matches MATLAB:
        XYZ(i,1) = k * sum(D65 .* xbar .* R')
        XYZ(i,2) = k * sum(D65 .* ybar .* R')
        XYZ(i,3) = k * sum(D65 .* zbar .* R')

    Parameters
    ----------
    reflectance : 1-D array, 81 values at 380–780 nm / 5 nm
                  Values in 0–1 range.

    Returns
    -------
    np.ndarray [X, Y, Z] in 0–100 scale (Y_white = 100)
    """
    R = np.asarray(reflectance, dtype=float)
    X = K * np.sum(D65 * XBAR * R)
    Y = K * np.sum(D65 * YBAR * R)
    Z = K * np.sum(D65 * ZBAR * R)
    return np.array([X, Y, Z])


def xyz_to_srgb(XYZ: np.ndarray) -> np.ndarray:
    """
    Convert CIE XYZ (0–100 scale) to sRGB (0–255 integers).

    Matches MATLAB xyz2srgb.m (Phil Green, IEC 61966):
        sRGB = M * (XYZ / 100)
        gamma: 1.055 * sRGB^(1/2.4) - 0.055   for sRGB > 0.00304
                12.92 * sRGB                    for sRGB ≤ 0.00304
        scale to 0–255 and clip.

    Parameters
    ----------
    XYZ : array [X, Y, Z] in 0–100 scale

    Returns
    -------
    np.ndarray [R, G, B] integers in 0–255
    """
    xyz = np.asarray(XYZ, dtype=float)
    sRGB = _M_XYZ_TO_SRGB @ (xyz / 100.0)

    # Clip linear sRGB to [0, 1]
    sRGB = np.clip(sRGB, 0.0, 1.0)

    # Apply sRGB gamma (IEC 61966)
    g = 1.0 / 2.4
    out = np.where(
        sRGB > 0.00304,
        1.055 * np.power(sRGB, g) - 0.055,
        12.92 * sRGB,
    )

    # Scale to 0–255 and clip
    out = np.clip(out * 255.0, 0, 255)
    return np.round(out).astype(int)


def xyz_to_lab(XYZ: np.ndarray, XYZn: np.ndarray = None) -> np.ndarray:
    """
    Convert CIE XYZ to L*a*b* according to CIE 15:2004.

    Matches MATLAB xyz2lab.m (Phil Green):
        const = (24/116)^3
        fY = Y/Yn ^ (1/3)   if Y/Yn > const
           = (841/108)*(Y/Yn) + 16/116   otherwise
        L = 116*fY - 16
        a = 500*(fX - fY)
        b = 200*(fY - fZ)

    Parameters
    ----------
    XYZ  : array [X, Y, Z] in 0–100 scale
    XYZn : reference white [Xn, Yn, Zn] in 0–100 scale.
           Defaults to the whitepoint computed from your CMF + D65 files.

    Returns
    -------
    np.ndarray [L*, a*, b*]
    """
    if XYZn is None:
        XYZn = XYZ_WHITE

    X, Y, Z     = np.asarray(XYZ, dtype=float)
    Xn, Yn, Zn  = np.asarray(XYZn, dtype=float)

    Xrel = X / Xn
    Yrel = Y / Yn
    Zrel = Z / Zn

    # CIE 15:2004 knee constant: (24/116)^3
    const = (24.0 / 116.0) ** 3

    def f(t):
        return np.where(t > const,
                        t ** (1.0 / 3.0),
                        (841.0 / 108.0) * t + 16.0 / 116.0)

    fX = f(Xrel)
    fY = f(Yrel)
    fZ = f(Zrel)

    L = 116.0 * fY - 16.0
    a = 500.0 * (fX - fY)
    b = 200.0 * (fY - fZ)

    return np.array([L, a, b])


def spectra_to_lab(reflectance: np.ndarray) -> np.ndarray:
    """Convenience: spectral reflectance → L*a*b* in one step."""
    return xyz_to_lab(spectra_to_XYZ(reflectance))


def spectra_to_rgb_display(reflectance: np.ndarray) -> tuple:
    """Spectral reflectance → sRGB (R, G, B) integers 0–255."""
    xyz = spectra_to_XYZ(reflectance)
    r, g, b = xyz_to_srgb(xyz)
    return int(r), int(g), int(b)


# ---------------------------------------------------------------------------
# ΔE (no custom MATLAB formula provided — using colour-science)
# ---------------------------------------------------------------------------

def delta_e_2000(lab1: np.ndarray, lab2: np.ndarray) -> float:
    """ΔE CIE 2000 between two L*a*b* colours."""
    return float(colour.delta_E(lab1, lab2, method="CIE 2000"))


def delta_e_76(lab1: np.ndarray, lab2: np.ndarray) -> float:
    """ΔE CIE 76 (Euclidean distance in L*a*b*)."""
    return float(colour.delta_E(lab1, lab2, method="CIE 1976"))


def delta_e_94(lab1: np.ndarray, lab2: np.ndarray) -> float:
    """ΔE CIE 94 (weighted chroma/hue, better than ΔE 76 in saturated regions)."""
    return float(colour.delta_E(lab1, lab2, method="CIE 1994"))


def interpret_delta_e(de: float) -> str:
    if de < 1:   return "Imperceptible (< 1)"
    elif de < 2: return "Perceptible to trained observers (1–2)"
    elif de < 3.5: return "Perceptible at a glance (2–3.5)"
    elif de < 5: return "Clearly different (3.5–5)"
    else:        return "Distinctly different (> 5)"


# ---------------------------------------------------------------------------
# RGB Explorer helpers (for Tab 1 of the Streamlit app)
# These use colour-science for the back-conversion sRGB→XYZ because
# Tab 1 works from screen RGB values, not spectral data.
# ---------------------------------------------------------------------------

_ILLUMINANT_D65 = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"]


def rgb_to_xyz(r: float, g: float, b: float) -> np.ndarray:
    """sRGB (0–255) → CIE XYZ via colour-science (used in RGB Explorer tab)."""
    rgb_norm = np.array([r, g, b]) / 255.0
    xyz = colour.RGB_to_XYZ(rgb_norm, colourspace="sRGB",
                             illuminant=_ILLUMINANT_D65,
                             apply_cctf_decoding=True)
    # Scale to 0–100 to match the rest of our pipeline
    return np.clip(xyz * 100.0, 0, None)


def rgb_to_lab(r: float, g: float, b: float) -> np.ndarray:
    """sRGB (0–255) → L*a*b* using your xyz_to_lab formula."""
    return xyz_to_lab(rgb_to_xyz(r, g, b))


def rgb_to_hsv(r: float, g: float, b: float) -> tuple:
    """sRGB (0–255) → HSV (H: 0–360°, S and V: 0–1)."""
    rgb_norm = np.array([r, g, b]) / 255.0
    h, s, v  = colour.RGB_to_HSV(rgb_norm)
    return float(h * 360), float(s), float(v)


def rgb_to_xy(r: float, g: float, b: float) -> tuple:
    """sRGB (0–255) → CIE xy chromaticity."""
    xyz = rgb_to_xyz(r, g, b)
    total = xyz.sum()
    if total == 0:
        return 0.3127, 0.3290
    return float(xyz[0] / total), float(xyz[1] / total)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{int(r):02X}{int(g):02X}{int(b):02X}"
