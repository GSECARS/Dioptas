Dioptas
===

**https://dioptas.readthedocs.io/**

A GUI program for fast analysis of powder X-ray diffraction images. It provides the capability of calibrating, creating masks, having pattern overlays and showing phase lines.

Installation
===

First, get the source: either clone with [Git](https://git-scm.com/downloads) or [download the ZIP](https://github.com/GSECARS/Dioptas/archive/refs/heads/gsecars.zip) and extract it. Then follow one of the options below.

---

### Option 1 — uv (recommended)

**Requires:** [uv](https://docs.astral.sh/uv/getting-started/installation/)

uv automatically manages the Python version and virtual environment. No separate Python install needed.

**Create the desktop shortcut**
```bash
cd Dioptas && uv run dioptas makeshortcut
```

This creates a desktop icon. Double-click it to launch Dioptas from then on.

---

### Option 2 — conda

**Requires:** [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/download)

All commands below must be run in a **conda-enabled terminal**: on Windows use the *Anaconda Prompt* (found in the Start menu); on macOS/Linux use your regular terminal after conda has been initialized.

**1. Enter the directory**
```bash
cd Dioptas
```

**2. Create the environment**
```bash
conda create -n dioptasENV python=3.13
```

**3. Activate the environment**
```bash
conda activate dioptasENV
```

**4. Install the package**
```bash
pip install .
```

**5. Create the desktop shortcut**
```bash
dioptas --make-icon
```

This creates a desktop icon. Double-click it to launch Dioptas from then on.

---

Maintainers
===

Christofanis Skordas (skordasc@uchicago.edu)  
Stella Chariton (stellachariton@uchicago.edu)
GSECARS, Center for Advanced Radiation Sources, University of Chicago
