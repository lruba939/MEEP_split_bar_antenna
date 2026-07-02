import meep as mp
import numpy as np
import os
import pickle

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

def load_TRL(path):
    """
    Load cached TRL data.
    """
    results = {
        "monitors": {},
    }

    for name in ["refl"]: #, "tran"

        npz = np.load(
            os.path.join(path, f"{name}.npz")
        )

        with open(
            os.path.join(path, f"{name}_flux_data.pkl"),
            "rb"
        ) as f:
            flux_data = pickle.load(f)

        results["monitors"][name] = {
            "flux": npz["flux"],
            "freqs": npz["freqs"],
            "flux_data": flux_data,
        }

    # fd = results["monitors"]["refl"]["flux_data"]
    # 
    # print(type(fd))
    # print(dir(fd))
    # print(type(fd.E))
    # print(type(fd.H))
    # 
    # print(fd.E.shape)
    # print(fd.H.shape)
    # 
    # print(fd.E.nbytes/1024**3)
    # print(fd.H.nbytes/1024**3)

    return results

def compute_TRL(
    reference,
    structure,
    save_path=None,
    save_name="TRL",
):
    """
    Compute reflection, transmission and loss spectra.

    Parameters
    ----------
    reference : dict
        Reference TRL cache, usually empty structure.

    structure : dict
        Structure TRL cache.

    save_path : str or None
        Output directory.

    save_name : str
        Prefix for saved files.

    Returns
    -------
    dict
        {
            "wavelength": ...,
            "R": ...,
            "T": ...,
            "L": ...,
        }
    """

    if not mp.am_master():
        return

    # =====================================================
    # LOAD DATA
    # =====================================================

    incident_flux = np.asarray(
        reference["monitors"]["tran"]["flux"]
    )

    refl_flux = np.asarray(
        structure["monitors"]["refl"]["flux"]
    )

    tran_flux = np.asarray(
        structure["monitors"]["tran"]["flux"]
    )

    flux_freqs = np.asarray(
        structure["monitors"]["tran"]["freqs"]
    )

    # =====================================================
    # WAVELENGTH
    # =====================================================

    wavelength = 1.0 / flux_freqs

    # =====================================================
    # R T L
    # =====================================================

    R = -refl_flux / incident_flux
    T = tran_flux / incident_flux
    L = 1.0 - R - T

    results = {
        "frequency": flux_freqs,
        "wavelength": wavelength,
        "R": R,
        "T": T,
        "L": L,
    }

    # =====================================================
    # SAVE
    # =====================================================

    if save_path is not None:

        trl_dir = os.path.join(
            save_path,
            "TRL",
        )

        os.makedirs(
            trl_dir,
            exist_ok=True,
        )

        data = np.column_stack(
            [
                flux_freqs,
                wavelength,
                R,
                T,
                L,
            ]
        )

        np.savetxt(
            os.path.join(
                trl_dir,
                f"{save_name}.txt",
            ),
            data,
            header="frequency wavelength R T L",
        )

        np.savez(
            os.path.join(
                trl_dir,
                f"{save_name}.npz",
            ),
            frequency=flux_freqs,
            wavelength=wavelength,
            R=R,
            T=T,
            L=L,
        )

        multi_line_plotter_same_axes(
            xdata_list=[wavelength, wavelength, wavelength],
            ydata_list=[R,T,L],
            labels=["R","T","L"],
            colors=["blue","red","green"],
            linestyles=["-","--","-."],
            xlabel="Wavelength [μm]",
            ylabel="Fraction",
            title=f"{save_name} vs wavelength",
            legend=True,
            save_path=trl_dir,
            save_name=f"{save_name}_lambda.png",
        )
        
        multi_line_plotter_same_axes(
            xdata_list=[flux_freqs,flux_freqs,flux_freqs],
            ydata_list=[R,T,L],
            labels=["R","T","L"],
            colors=["blue","red","green"],
            linestyles=["-","--","-."],
            xlabel="Frequency [1/μm]",
            ylabel="Fraction",
            title=f"{save_name} vs frequency",
            legend=True,
            save_path=trl_dir,
            save_name=f"{save_name}_frequency.png",
        )
        
    return results
