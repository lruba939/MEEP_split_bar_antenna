import meep as mp
import numpy as np
import os, h5py

from utils.field_utils import *

from visualization.plotter import *

def setup_TRL_monitors(sim, config, TRL_X_size=None, TRL_Y_size=None):

    if TRL_X_size is None:
        TRL_X_size = config.src_size[0]

    if TRL_Y_size is None:
        TRL_Y_size = config.src_size[1]

    refl_fr = mp.FluxRegion(
        center=mp.Vector3(
            0,
            0,
            config.z_reflection
        ),
        size=mp.Vector3(
            TRL_X_size,
            TRL_Y_size,
            0
        )
    )

    tran_fr = mp.FluxRegion(
        center=mp.Vector3(
            0,
            0,
            config.z_transmission
        ),
        size=mp.Vector3(
            TRL_X_size,
            TRL_Y_size,
            0
        )
    )
    return {
        "monitors": {
            "refl": sim.add_flux(
                config.frequency,
                config.frequency_width,
                config.nfreq,
                refl_fr
            ),
            "tran": sim.add_flux(
                config.frequency,
                config.frequency_width,
                config.nfreq,
                tran_fr
            ),
        },
        "metadata": {
            "x_size": TRL_X_size,
            "y_size": TRL_Y_size,
            "z_reflection": config.z_reflection,
            "z_transmission": config.z_transmission,
        }
    }

def load_TRL(path, Nfreq):
    return {
        "monitors": {
            "refl": load_flux_monitor(
                path,
                "refl",
                Nfreq,
            ),
            "tran": load_flux_monitor(
                path,
                "tran",
                Nfreq,
            ),
        }
    }

def save_TRL(
    frequency,
    wavelength,
    R,
    T,
    L,
    save_path,
    save_name,
):
    """
    Save TRL spectra to text and NumPy files.

    Parameters
    ----------
    frequency : ndarray

    wavelength : ndarray

    R, T, L : ndarray

    save_path : str

    save_name : str
    """

    os.makedirs(save_path,exist_ok=True)

    data = np.column_stack([frequency, wavelength, T, R, L])

    np.savetxt(os.path.join(save_path, f"{save_name}.dat"), data, header="frequency wavelength T R L")

    np.savez(
        os.path.join(
            save_path,
            f"{save_name}.npz",
        ),
        frequency=frequency,
        wavelength=wavelength,
        T=T,
        R=R,
        L=L,
    )

def plot_TRL(
    frequency,
    wavelength,
    R,
    T,
    L,
    save_path,
    save_name,
):
    """
    Plots for TRL spectra.

    Parameters
    ----------
    frequency : ndarray
    wavelength : ndarray
    R, T, L : ndarray
    save_path : str
    save_name : str
    """

    multi_line_plotter_same_axes(
        xdata_list=[wavelength, wavelength, wavelength],
        ydata_list=[T, R, L],
        labels=["T", "R", "L"],
        colors=["red", "blue", "green"],
        linestyles=["-", "--", "-."],
        xlabel="Wavelength [μm]",
        ylabel="Fraction",
        title=save_name,
        legend=True,
        save_path=save_path,
        save_name=f"{save_name}_lambda.png",
    )

    # multi_line_plotter_same_axes(
    #     xdata_list=[frequency, frequency, frequency],
    #     ydata_list=[T, R, L],
    #     labels=["T", "R", "L"],
    #     colors=["red", "blue", "green"],
    #     linestyles=["-", "--", "-."],
    #     xlabel="Frequency [1/μm]",
    #     ylabel="Fraction",
    #     title=save_name,
    #     legend=True,
    #     save_path=save_path,
    #     save_name=f"{save_name}_frequency.png",
    # )

def plot_TRL_antenna_substrate(
    frequency,
    wavelength,
    Ra,
    Ta,
    La,
    Rs,
    Ts,
    Ls,
    save_path,
    save_name="antenna_and_substrate",
):
    """
    Plots for TRL spectra.

    Parameters
    ----------
    frequency : ndarray
    wavelength : ndarray
    R{a/s}, T{a/s}, L{a/s} : ndarray
    save_path : str
    save_name : str
    """

    multi_line_plotter_same_axes(
        xdata_list=[wavelength, wavelength, wavelength, wavelength, wavelength, wavelength],
        ydata_list=[Ta, Ra, La, Ts, Rs, Ls],
        labels=["T antenna", "R antenna", "L antenna", "T substrate", "R substrate", "L substrate"],
        colors=["red", "blue", "green", "tab:red", "tab:blue", "tab:green"],
        linestyles=["-", "-", "-", ":", ":", ":"],
        xlabel="Wavelength [μm]",
        ylabel="Fraction",
        title=save_name,
        legend=True,
        save_path=save_path,
        save_name=f"{save_name}_lambda.png",
    )
    
def compute_TRL(
    Nfreq,
    empty_path,
    substrate_path=None,
    antenna_path=None,
    save_path=None,
):
    """
    Compute TRL spectra from cached DFT fields.

    Parameters
    ----------
    empty_path : str
        Path to cache/empty/TRL.

    substrate_path : str or None
        Path to cache/substrate/TRL.

    antenna_path : str or None
        Path to cache/antenna/TRL.

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
    empty = load_TRL(empty_path, Nfreq)

    substrate = None
    antenna = None

    if substrate_path is not None:
        substrate = load_TRL(substrate_path, Nfreq)

    if antenna_path is not None:
        antenna = load_TRL(antenna_path, Nfreq)

    # =====================================================
    # REFERENCE
    # =====================================================
    frequency = empty["monitors"]["tran"]["freqs"]
    wavelength = 1.0 / frequency

    incident_flux = compute_flux(
        empty["monitors"]["tran"]["E"],
        empty["monitors"]["tran"]["H"],
    )

    results = {}

    # =====================================================
    # EMPTY
    # =====================================================
    refl = compute_flux(
        empty["monitors"]["refl"]["E"],
        empty["monitors"]["refl"]["H"],
    )

    tran = compute_flux(
        empty["monitors"]["tran"]["E"],
        empty["monitors"]["tran"]["H"],
    )

    R = -refl / incident_flux
    T = tran / incident_flux
    L = 1.0 - R - T

    results["empty"] = {
        "frequency": frequency,
        "wavelength": wavelength,
        "R": R,
        "T": T,
        "L": L,
    }

    # =====================================================
    # SUBSTRATE
    # =====================================================
    if substrate is not None:

        refl = compute_flux_difference(
            substrate["monitors"]["refl"]["E"],
            substrate["monitors"]["refl"]["H"],
            empty["monitors"]["refl"]["E"],
            empty["monitors"]["refl"]["H"],
        )

        tran = compute_flux(
            substrate["monitors"]["tran"]["E"],
            substrate["monitors"]["tran"]["H"],
        )

        R = -refl / incident_flux
        T = tran / incident_flux
        L = 1.0 - R - T

        results["substrate"] = {
            "frequency": frequency,
            "wavelength": wavelength,
            "R": R,
            "T": T,
            "L": L,
        }

    # =====================================================
    # ANTENNA
    # =====================================================
    if antenna is not None:

        refl = compute_flux_difference(
            antenna["monitors"]["refl"]["E"],
            antenna["monitors"]["refl"]["H"],
            empty["monitors"]["refl"]["E"],
            empty["monitors"]["refl"]["H"],
        )

        tran = compute_flux(
            antenna["monitors"]["tran"]["E"],
            antenna["monitors"]["tran"]["H"],
        )

        R = -refl / incident_flux
        T = tran / incident_flux
        L = 1.0 - R - T

        results["antenna"] = {
            "frequency": frequency,
            "wavelength": wavelength,
            "R": R,
            "T": T,
            "L": L,
        }

    # =====================================================
    # ANTENNA - SUBSTRATE
    # =====================================================
    if substrate is not None and antenna is not None:

        R = (results["antenna"]["R"] - results["substrate"]["R"])
        T = (results["antenna"]["T"] - results["substrate"]["T"])
        L = (results["antenna"]["L"] - results["substrate"]["L"])

        results["antenna_minus_substrate"] = {
            "frequency": frequency,
            "wavelength": wavelength,
            "R": R,
            "T": T,
            "L": L,
        }

    # =====================================================
    # SAVE
    # =====================================================
    if save_path is not None:

        os.makedirs(save_path, exist_ok=True)

        for name, data in results.items():
            save_TRL(
                frequency=data["frequency"],
                wavelength=data["wavelength"],
                R=data["R"],
                T=data["T"],
                L=data["L"],
                save_path=save_path,
                save_name=name,
            )
            plot_TRL(
                frequency=data["frequency"],
                wavelength=data["wavelength"],
                R=data["R"],
                T=data["T"],
                L=data["L"],
                save_path=save_path,
                save_name=name,
            )
            
        if substrate is not None and antenna is not None:
            plot_TRL_antenna_substrate(
                frequency=data["frequency"],
                wavelength=data["wavelength"],
                Ra=results["antenna"]["R"], Ta=results["antenna"]["T"], La=results["antenna"]["L"],
                Rs=results["substrate"]["R"], Ts=results["substrate"]["T"], Ls=results["substrate"]["L"],
                save_path=save_path,
            )

    return results
