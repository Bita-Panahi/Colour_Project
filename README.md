# Colour Project 🎨
Interactive colour science tool: RGB ↔ XYZ ↔ L*a*b* conversions, spectral reflectance visualisation, and ΔE colour difference measurement. Built with Streamlit and custom CIE calculations from CMF/D65 reference data.

My name is [Bita Panahi](https://linkedin.com/in/bita-panahi-1994-), and I am a PhD researcher in Computer Science, NTNU, Norway.

---

## What the app does

### Tab 1: RGB Explorer
- Pick a colour with a visual colour picker or type RGB values (0–255)
- Instant conversion to **CIE XYZ**, **CIE L\*a\*b\***, **HSV**, and **hex**
- Interactive **CIE 1931 xy chromaticity diagram** showing where the colour sits relative to the spectral locus and sRGB gamut

### Tab 2: Spectral Reflectance Viewer
- Choose from **7 reference samples** (red, green, blue, yellow, white, grey, black)
- Or **upload your own CSV/Excel** (wavelength + reflectance columns)
- Visualise the spectral curve, the derived XYZ / L\*a\*b\* values, and the approximate display colour

### Tab 3: ΔE Color Comparison
- Compare any two sRGB colours side-by-side
- **ΔE CIE 2000** and ΔE 94 metrics with a visual gauge
- Perceptual interpretation (imperceptible → distinctly different)

---
## What I used

- `colour-science` -- Standards-compliant colour space conversions, spectral data, ΔE
- `plotly` -- Interactive chromaticity diagrams, spectral curves, gauges 
- `streamlit` -- Web UI 
- `numpy` / `scipy` -- Numerical computation 
- `pandas` -- CSV handling 
- `matplotlib` 

---

## Data & standards

All colour calculations follow CIE (Commission Internationale de l'Éclairage) standards and are implemented from scratch; no library black-box for the core math.

Reference data:
- `CMF_2deg_5nm.xlsx`: CIE 1931 2° colour matching functions (x̄, ȳ, z̄), 380–780 nm at 5 nm intervals
- `D65_5nm.xlsx`: D65 standard illuminant spectral power distribution, same grid

---

## Skills I learned

- Scientific Python (`colour-science`, `numpy`, `scipy`)
- Interactive data visualisation with `plotly`
- Domain expertise in **colour science** (XYZ, L\*a\*b\*, spectral reflectance, ΔE)
- Streamlit app architecture (multi-tab, upload handling, caching)
- End-to-end pipeline: spectral data → perceptual colour metrics → UI

---

