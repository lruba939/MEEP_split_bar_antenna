import meep as mp
import numpy as np
import os
import pickle

from visualization.plotter import *

def get_scattering_box_size(
    antenna,
    config,
    padding_perc=10,
    extra_padding_nm=(0, 0, 0),
):
    """
    Compute scattering box dimensions.

    Parameters
    ----------
    antenna : antenna object
        Must implement:
            antenna.bounding_box()

    config : SimulationConfig

    padding_perc : float
        Relative padding [%] added to all dimensions.

    extra_padding_nm : tuple
        Additional anisotropic padding:
        (dx, dy, dz) in nm.

    Returns
    -------
    dict
        {
            "Lx": ...,
            "Ly": ...,
            "Lz": ...,
            "padding_perc": ...,
            "extra_padding_nm": (...),
        }
    """

    # =====================================================
    # ANTENNA SIZE
    # =====================================================

    Lx, Ly, Lz = antenna.bounding_box()

    # =====================================================
    # MINIMAL GRID PADDING
    # =====================================================

    min_padding = 2 / config.resolution

    requested_padding = (
        padding_perc / 100.0 *
        min(Lx, Ly, Lz)
    )

    if requested_padding < min_padding:

        if mp.am_master():
            print(
                f"Warning: scattering padding "
                f"{padding_perc:.2f}% too small."
            )

        padding_perc = (
            min_padding /
            min(Lx, Ly, Lz)
        ) * 100

        if mp.am_master():
            print(
                f"Increased to "
                f"{padding_perc:.2f}%."
            )

    # =====================================================
    # ISOTROPIC PADDING
    # =====================================================

    scale = 1 + padding_perc / 100

    Lx *= scale
    Ly *= scale
    Lz *= scale

    # =====================================================
    # ANISOTROPIC PADDING
    # =====================================================

    dx, dy, dz = extra_padding_nm

    xm = 1000.0

    Lx += dx / xm
    Ly += dy / xm
    Lz += dz / xm

    # =====================================================
    # ROUND TO NM
    # =====================================================

    Lx = np.ceil(Lx * xm) / xm
    Ly = np.ceil(Ly * xm) / xm
    Lz = np.ceil(Lz * xm) / xm

    # =====================================================
    # PRINT
    # =====================================================

    if mp.am_master():

        print("\nScattering box:")

        print(f"  Lx = {Lx*xm:.1f} nm")
        print(f"  Ly = {Ly*xm:.1f} nm")
        print(f"  Lz = {Lz*xm:.1f} nm")

        print(
            f"  padding = {padding_perc:.2f}%"
        )

        print(
            f"  extra = {extra_padding_nm} nm\n"
        )

    # =====================================================
    # RETURN
    # =====================================================

    return {
        "Lx": Lx,
        "Ly": Ly,
        "Lz": Lz,
        "padding_perc": padding_perc,
        "extra_padding_nm": extra_padding_nm,
    }

def setup_scattering_monitors(
    sim,
    scattering_object,
    config,
    padding_perc=10,
    extra_padding_nm=(0, 0, 0),
):
    """
    Create scattering box flux monitors.

    Parameters
    ----------
    sim : meep.Simulation

    scattering_object : object
        Must implement scattering_object.bounding_box().

    config : SimulationConfig

    padding_perc : float
        Relative padding [%].

    extra_padding_nm : tuple
        Additional padding (dx, dy, dz) in nm.

    Returns
    -------
    dict
        {
            "monitors": {...},
            "metadata": {...}
        }
    """

    # =====================================================
    # BOX SIZE
    # =====================================================

    box = get_scattering_box_size(
        antenna=scattering_object,
        config=config,
        padding_perc=padding_perc,
        extra_padding_nm=extra_padding_nm,
    )

    Lx = box["Lx"]
    Ly = box["Ly"]
    Lz = box["Lz"]

    hx = Lx / 2.0
    hy = Ly / 2.0
    hz = Lz / 2.0

    fcen = config.frequency
    df = config.frequency_width
    nfreq = config.nfreq

    # =====================================================
    # X FACES
    # =====================================================

    x1 = sim.add_flux(
        fcen,
        df,
        nfreq,
        mp.FluxRegion(
            center=mp.Vector3(-hx, 0, 0),
            size=mp.Vector3(
                0,
                Ly,
                Lz,
            ),
            weight=-1.0,
        ),
    )

    x2 = sim.add_flux(
        fcen,
        df,
        nfreq,
        mp.FluxRegion(
            center=mp.Vector3(hx, 0, 0),
            size=mp.Vector3(
                0,
                Ly,
                Lz,
            ),
            weight=1.0,
        ),
    )

    # =====================================================
    # Y FACES
    # =====================================================

    y1 = sim.add_flux(
        fcen,
        df,
        nfreq,
        mp.FluxRegion(
            center=mp.Vector3(0, -hy, 0),
            size=mp.Vector3(
                Lx,
                0,
                Lz,
            ),
            weight=-1.0,
        ),
    )

    y2 = sim.add_flux(
        fcen,
        df,
        nfreq,
        mp.FluxRegion(
            center=mp.Vector3(0, hy, 0),
            size=mp.Vector3(
                Lx,
                0,
                Lz,
            ),
            weight=1.0,
        ),
    )

    # =====================================================
    # Z FACES
    # =====================================================

    z1 = sim.add_flux(
        fcen,
        df,
        nfreq,
        mp.FluxRegion(
            center=mp.Vector3(0, 0, -hz),
            size=mp.Vector3(
                Lx,
                Ly,
                0,
            ),
            weight=-1.0,
        ),
    )

    z2 = sim.add_flux(
        fcen,
        df,
        nfreq,
        mp.FluxRegion(
            center=mp.Vector3(0, 0, hz),
            size=mp.Vector3(
                Lx,
                Ly,
                0,
            ),
            weight=1.0,
        ),
    )

    # =====================================================
    # RETURN
    # =====================================================

    return {
        "monitors": {
            "x1": x1,
            "x2": x2,
            "y1": y1,
            "y2": y2,
            "z1": z1,
            "z2": z2,
        },

        "metadata": box,
    }

