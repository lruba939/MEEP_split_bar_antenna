# MEEP Plasmonic Antennas

A modular framework for designing, simulating and analyzing plasmonic nanoantennas using MEEP.

The project provides a complete workflow from parametric geometry generation through FDTD simulations to automated post-processing and visualization.

---

## Features

- Parametric antenna geometries
- Layered material support (substrates, adhesion layers, etc.)
- Modular simulation pipeline
- Automatic caching of simulation results
- Near-field enhancement analysis
- Transmission / Reflection / Loss (TRL)
- Scattering analysis
- Gap DFT monitors
- Automated plots and animations

---

## Simulation Workflow

```
Geometry
    ↓
Simulation setup
    ↓
Run / Load cache
    ↓
Field recording
    ↓
Post-processing
    ├── Enhancement
    ├── TRL
    ├── Scattering
    └── Gap DFT
    ↓
Plots & animations
```

Each structure (`empty`, `substrate`, `antenna`) is simulated independently and stored in a cache. Final quantities are computed afterwards from cached data, avoiding unnecessary reruns.

---

## Project Structure

```
main/
    run.py
    src/
        experiments.py

utils/
    geometry.py
    enhancement.py
    meep_utils.py
    plotter.py
    ...

results/
    cache/
        empty/
        substrate/
        antenna/
        enhancement/

    TRL/
    SCATTERING/
    GAP_DFT/
    ENHANCEMENT/
```

---

## Available Geometries

Currently implemented antenna classes:

- `BowTie`
- `BowTieEquilateral`
- `SplitBar`
- `Bar`

Each geometry exposes a common interface and can be exchanged without modifying the simulation pipeline.

---

## Output

A typical simulation generates:

- cached field data (HDF5)
- enhancement maps
- TRL spectra
- scattering spectra
- gap DFT spectra
- geometry plots
- animations
- simulation metadata

---

## Design Philosophy

The project separates:

- geometry generation
- simulation execution
- cached field storage
- post-processing
- visualization

This makes individual modules independent and allows expensive FDTD simulations to be performed only once while enabling repeated analysis using the cached results.

## Simulations

### Cell Structure
![Cell](Assets/cell.png)

### EM Field
![GIF](https://github.com/lruba939/MEEP_plasmonic_antennas/blob/main/Assets/xyplanar_ex.gif)

### Antenna Enhancement Effect
![GIF](https://github.com/lruba939/MEEP_plasmonic_antennas/blob/main/Assets/enh_xy_e2.gif)

![Antenna](Assets/antenna.png)

## Getting Started
Clone the repository and explore the simulation files to get started with the antenna design.

## Analytical calculations for half-wave dipole nanoantennas
Based on Novotny L.'s publication, *Effective wavelength scaling for optical antennas* (Phys Rev Lett. 2007 doi: https://doi.org/10.1103/PhysRevLett.98.266802), a script was created at:

> utils/novotny2007_effective_wavelength/

that allows one to calculate the half-wavelength of a dipole antenna and the effective wavelength for gold and silver.

![effwave](Assets/eff_wave_novotny2007.png)

## To Do:
- [ ] Autosave source shape in Hz and um
- [ ] Alternatively load all params from file than using flags
- [ ] Integrate Novotny (2007) calculations into the main code
	- [ ] Take eps data from meep.materials for Novotny model

## Done:
- [x] Calcs for substrate and antenna-substrate system
- [x] Load data for empty cell
- [x] Add comments to experiment.txt
- [x] Better dir namespace
- [x] Add scattering calculations (DFT flux boxes)
- [x] Flux monitors:
	- [x] Transimtance monitor
	- [x] Reflectance monitor
- [x] Warning before calculations that we asume PML
- [x] Fixes for parallel calculations 
- [x] Get rid of params.py file
    - [x] Remove calculations
    - [x] Remove geometry definitions
    - [x] New config.py
- [x] Split geometry.py into make_geometry and geometry utilities
- [x] Make a manager of experiments
- [x] Move geometry definitions to separate files
    - [x] Add bow-tie antenna
    - [x] Add split-bar antenna
    - [x] Add half-dipol antenna
- [x] Source visualization procces:
	- [x] Spectrum of source intensity in time
	- [x] Conclusions
- [x] Warning about PML and wavelength
