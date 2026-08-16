# Centrifugal Effects Stellar Evolution

This repository contains a simplified stellar-evolution script and a new parallel feature module named Sigil Atlas.

## Installation

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

## Core Simulation

Run the baseline simulation with:

```bash
python stellar_evolution.py
```

## Sigil Atlas

`SigilAtlas/` provides:

- registry-backed sigil metadata and SVG geometry
- operator classification and geometry families
- interactive browsing cards in `/home/runner/work/Centrifugal-Effects-Stellar-Evolution/Centrifugal-Effects-Stellar-Evolution/SigilAtlas/ui/`
- integration maps for stellar-evolution parameter overrides
- validation schemas and automated tests

### Validate the atlas

```bash
python integration/stellar-evolution/validate_sigil_atlas.py
```

### Export a sigil mapping into stellar-evolution input format

```bash
python integration/stellar-evolution/export_sigil_parameters.py aurora-spin
```

### Generate optional mapping plots

```bash
python integration/stellar-evolution/plot_sigil_mappings.py
```

### Browse the UI cards

Serve the repository root and open the browser at `/SigilAtlas/ui/index.html`:

```bash
python -m http.server 8000
```

## Tests

Run the automated tests with:

```bash
python -m unittest discover -s tests
```
