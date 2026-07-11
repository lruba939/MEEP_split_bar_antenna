import meep as mp
import numpy as np
import os, h5py

from utils.field_utils import *
from utils.simulation.cache import *

from visualization.plotter import *

def build_scattering_box(
    scattering_object,
    config,
    padding_perc=10,
    extra_padding_nm=(0, 0, 0),
):
    """
    Compute scattering box geometry.

    Returns
    -------
    dict
        {
            "cx": ...,
            "cy": ...,
            "cz": ...,
            "Lx": ...,
            "Ly": ...,
            "Lz": ...,
            "padding_perc": ...,
            "extra_padding_nm": (...),
        }
    """
    # =====================================================
    # OBJECT SIZE & CENTER
    # =====================================================
    Lx, Ly, Lz = scattering_object.bounding_box()

    cx, cy = scattering_object.center
    cz = scattering_object.z_offset

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

        print(f"  center = ({cx*xm:.1f}, {cy*xm:.1f}, {cz*xm:.1f}) nm")

        print(f"  Lx = {Lx*xm:.1f} nm")
        print(f"  Ly = {Ly*xm:.1f} nm")
        print(f"  Lz = {Lz*xm:.1f} nm")

        print(f"  padding = {padding_perc:.2f}%")
        print(f"  extra = {extra_padding_nm} nm\n")

    # =====================================================
    # RETURN
    # =====================================================
    return {
        "cx": cx,
        "cy": cy,
        "cz": cz,
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
    # BOX
    # =====================================================
    box = build_scattering_box(
        scattering_object=scattering_object,
        config=config,
        padding_perc=padding_perc,
        extra_padding_nm=extra_padding_nm,
    )

    cx = box["cx"]
    cy = box["cy"]
    cz = box["cz"]

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
    x1 = sim.add_flux(fcen, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(cx - hx, cy, cz),
            size=mp.Vector3(
                0,
                Ly,
                Lz,
            ),
            weight=-1.0,
        ),
    )
    x2 = sim.add_flux(fcen, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(cx + hx, cy, cz),
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
    y1 = sim.add_flux(fcen, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(cx, cy - hy, cz),
            size=mp.Vector3(
                Lx,
                0,
                Lz,
            ),
            weight=-1.0,
        ),
    )
    y2 = sim.add_flux(fcen, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(cx, cy + hy, cz),
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
    z1 = sim.add_flux(fcen, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(cx, cy, cz - hz),
            size=mp.Vector3(
                Lx,
                Ly,
                0,
            ),
            weight=-1.0,
        ),
    )
    z2 = sim.add_flux(fcen, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(cx, cy, cz + hz),
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
            "x-": x1,
            "x+": x2,
            "y-": y1,
            "y+": y2,
            "z-": z1,
            "z+": z2,
        },

        "metadata": box,
    }

def load_scattering(path, Nfreq):
    """
    Load cached scattering monitor data.
    """

    return {
        "monitors": {
            "x-": load_flux_monitor(path, "x-", Nfreq),
            "x+": load_flux_monitor(path, "x+", Nfreq),
            "y-": load_flux_monitor(path, "y-", Nfreq),
            "y+": load_flux_monitor(path, "y+", Nfreq),
            "z-": load_flux_monitor(path, "z-", Nfreq),
            "z+": load_flux_monitor(path, "z+", Nfreq),
        },

        "metadata": load_metadata(
            os.path.dirname(path)
        ),
    }

def save_scattering(
    frequency,
    wavelength,
    scattering,
    faces,
    save_path,
    save_name,
):
    """
    Save scattering spectra.

    Parameters
    ----------
    frequency : ndarray

    wavelength : ndarray

    scattering : ndarray
        Total scattering spectrum.

    faces : dict
        Scattering flux through each box face.

    save_path : str

    save_name : str
    """

    os.makedirs(
        save_path,
        exist_ok=True,
    )

    # =====================================================
    # TOTAL SCATTERING
    # =====================================================

    data = np.column_stack([
        frequency,
        wavelength,
        scattering,
    ])

    np.savetxt(
        os.path.join(
            save_path,
            f"{save_name}.dat",
        ),
        data,
        header="frequency wavelength scattering",
    )

    np.savez(
        os.path.join(
            save_path,
            f"{save_name}.npz",
        ),
        frequency=frequency,
        wavelength=wavelength,
        scattering=scattering,
    )

    # =====================================================
    # SCATTERING PER FACE
    # =====================================================

    data = np.column_stack([
        frequency,
        wavelength,
        faces["x-"],
        faces["x+"],
        faces["y-"],
        faces["y+"],
        faces["z-"],
        faces["z+"],
    ])

    np.savetxt(
        os.path.join(
            save_path,
            f"{save_name}_faces.dat",
        ),
        data,
        header="frequency wavelength x- x+ y- y+ z- z+",
    )

    np.savez(
        os.path.join(
            save_path,
            f"{save_name}_faces.npz",
        ),
        frequency=frequency,
        wavelength=wavelength,
        **faces,
    )

def plot_scattering(
    frequency,
    wavelength,
    scattering,
    faces,
    save_path,
    save_name,
):
    """
    Plot scattering spectra.
    """

    line_plotter(
        wavelength,
        scattering,
        xlabel="Wavelength [μm]",
        ylabel="Scattering",
        title=f"{save_name} scattering",
        save_path=save_path,
        save_name=f"{save_name}_lambda.png",
    )

    multi_line_plotter_same_axes(
        xdata_list=[wavelength] * 6,
        ydata_list=[faces["x-"], faces["x+"], faces["y-"], faces["y+"], faces["z-"], faces["z+"]],
        labels=["x-","x+","y-","y+","z-","z+"],
        colors=["#149dff","#14517c","#ff7700","#914300","#5ec75e","#205220"],
        linestyles=["-","-.","-","-.","-","-."],
        xlabel="Wavelength [μm]",
        ylabel="Scattering",
        title=f"{save_name} scattering",
        legend=True,
        save_path=save_path,
        save_name=f"{save_name}_faces_lambda.png",
    )

    # line_plotter(
    #     frequency,
    #     scattering,
    #     xlabel="Frequency [1/μm]",
    #     ylabel="Scattering",
    #     title=f"{save_name} scattering",
    #     save_path=save_path,
    #     save_name=f"{save_name}_frequency.png",
    # )

    # multi_line_plotter_same_axes(
    #     xdata_list=[frequency] * 6,
    #     ydata_list=[faces["x-"], faces["x+"], faces["y-"], faces["y+"], faces["z-"], faces["z+"]],
    #     labels=["x-","x+","y-","y+","z-","z+"],
    #     colors=["#149dff","#14517c","#ff7700","#914300","#5ec75e","#205220"],
    #     linestyles=["-","-.","-","-.","-","-."],
    #     xlabel="Frequency [1/μm]",
    #     ylabel="Scattering",
    #     title=f"{save_name} scattering",
    #     legend=True,
    #     save_path=save_path,
    #     save_name=f"{save_name}_faces_frequency.png",
    # )

def compute_scattering(
    Nfreq,
    empty_path,
    substrate_path=None,
    antenna_path=None,
    save_path=None,
):
    """
    Compute scattering spectra from cached DFT fields.

    Parameters
    ----------
    empty_path : str
        Path to cache/empty/SCATTERING.

    substrate_path : str or None
        Path to cache/substrate/SCATTERING.

    antenna_path : str or None
        Path to cache/antenna/SCATTERING.

    save_path : str or None
        Directory for saving results.

    Returns
    -------
    dict
    """
    if not mp.am_master():
        return

    # =====================================================
    # LOAD
    # =====================================================
    empty = load_scattering(empty_path, Nfreq)

    substrate = None
    antenna = None

    if substrate_path is not None:
        substrate = load_scattering(substrate_path, Nfreq)

    if antenna_path is not None:
        antenna = load_scattering(antenna_path, Nfreq)

    # =====================================================
    # REFERENCE
    # =====================================================
    frequency = empty["monitors"]["x-"]["freqs"]
    wavelength = 1.0 / frequency

    incident_flux = empty["monitors"]["z+"]["flux"]

    Lx = empty["metadata"]["Lx"]
    Ly = empty["metadata"]["Ly"]

    intensity = incident_flux / (Lx * Ly)

    results = {}

    # =====================================================
    # SUBSTRATE (substrate - empty)
    # =====================================================
    if substrate is not None:

        faces = {}

        for name in substrate["monitors"]:

            faces[name] = compute_flux_difference(
                substrate["monitors"][name]["E"],
                substrate["monitors"][name]["H"],
                empty["monitors"][name]["E"],
                empty["monitors"][name]["H"],
            )

        power = np.zeros_like(frequency)

        for flux in faces.values():
            power += flux

        cross_section = power / intensity

        results["substrate"] = {
            "frequency": frequency,
            "wavelength": wavelength,
            "faces": faces,
            "power": power,
            "cross_section": cross_section,
        }

    # =====================================================
    # ANTENNA (antenna - substrate)
    # =====================================================
    if antenna is not None and substrate is not None:

        faces = {}

        for name in antenna["monitors"]:

            faces[name] = compute_flux_difference(
                antenna["monitors"][name]["E"],
                antenna["monitors"][name]["H"],
                substrate["monitors"][name]["E"],
                substrate["monitors"][name]["H"],
            )

        power = np.zeros_like(frequency)

        for flux in faces.values():
            power += flux

        cross_section = power / intensity

        results["antenna"] = {
            "frequency": frequency,
            "wavelength": wavelength,
            "faces": faces,
            "power": power,
            "cross_section": cross_section,
        }

    # =====================================================
    # SAVE
    # =====================================================
    if save_path is not None:

        os.makedirs(
            save_path,
            exist_ok=True,
        )

        for name, data in results.items():

            save_scattering(
                frequency=data["frequency"],
                wavelength=data["wavelength"],
                power=data["power"],
                cross_section=data["cross_section"],
                faces=data["faces"],
                save_path=save_path,
                save_name=name,
            )

            plot_scattering(
                frequency=data["frequency"],
                wavelength=data["wavelength"],
                power=data["power"],
                cross_section=data["cross_section"],
                faces=data["faces"],
                save_path=save_path,
                save_name=name,
            )

    return results
