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

All conversions follow **CIE** (Commission Internationale de l'Éclairage) standards:
- Illuminant **D65** (standard daylight)
- **CIE 1931 2° standard observer** (CIE CMFs)
- ΔE formula: **CIE 2000** (CIEDE2000)

Powered by the [`colour-science`](https://www.colour-science.org/) Python library.

---

## Skills I learned

- Scientific Python (`colour-science`, `numpy`, `scipy`)
- Interactive data visualisation with `plotly`
- Domain expertise in **colour science** (XYZ, L\*a\*b\*, spectral reflectance, ΔE)
- Streamlit app architecture (multi-tab, upload handling, caching)
- End-to-end pipeline: spectral data → perceptual colour metrics → UI

---

