import numpy as np
import os
import h5py

def float_to_complex(array):
    """
    Convert interleaved float array to complex array.

    Meep stores complex DFT data as:

        Re0 Im0 Re1 Im1 Re2 Im2 ...

    This function converts it into:

        Re0 + i Im0,
        Re1 + i Im1,
        ...

    Parameters
    ----------
    array : ndarray
        Float array returned by save_flux().

    Returns
    -------
    ndarray
        Complex-valued array.
    """
    return array[0::2] + 1j * array[1::2]


def compute_flux(E, H):
    """
    Compute flux spectrum from DFT electric and magnetic fields.

    This reproduces Meep's internal dft_flux::flux():

        F = sum( Re(E * conj(H)) )

    Parameters
    ----------
    E : ndarray
        Complex electric DFT fields.
        Shape = (Npoints, Nfreq)

    H : ndarray
        Complex magnetic DFT fields.
        Shape = (Npoints, Nfreq)

    Returns
    -------
    ndarray
        Flux spectrum.
    """
    if E.shape != H.shape:
        raise ValueError(
            f"E and H must have the same shape "
            f"({E.shape} != {H.shape})"
        )
    return np.real(
        E * np.conj(H)
    ).sum(axis=0)

def compute_flux_difference(
    E_sample,
    H_sample,
    E_reference,
    H_reference,
):
    """
    Compute flux after offline load_minus operation.

    Equivalent to:
        sim.load_minus_flux_data(...)
        sim.run(...)
        mp.get_fluxes(...)
        
    Parameters
    ----------
    E_sample, H_sample : ndarray
        DFT fields of simulated structure.

    E_reference, H_reference : ndarray
        Reference DFT fields.

    Returns
    -------
    ndarray
        Flux spectrum after subtracting reference fields.
    """
    if E_sample.shape != E_reference.shape:
        raise ValueError("Electric DFT arrays have different shapes.")
    
    if H_sample.shape != H_reference.shape:
        raise ValueError("Magnetic DFT arrays have different shapes.")

    return compute_flux(
        E_sample - E_reference,
        H_sample - H_reference,
    )

def load_dft_h5(path, Nfreq):
    """
    Load DFT fields saved by Meep save_flux().

    Parameters
    ----------
    path : str
        Path to *.h5 file.

    Nfreq : int
        Number of frequency points.

    Returns
    -------
    E, H : ndarray
        Complex DFT electric and magnetic fields.
        Shape = (Npoints, Nfreq)
    """

    with h5py.File(path, "r") as f:

        keys = list(f.keys())

        E = float_to_complex(
            f[keys[0]][:]
        )

        H = float_to_complex(
            f[keys[1]][:]
        )

    E = E.reshape(-1, Nfreq)
    H = H.reshape(-1, Nfreq)

    return E, H

def save_flux_monitor(
    sim,
    monitor,
    name,
    path,
    subdirectory="",
):
    """
    Save Meep flux monitor to cache.

    Parameters
    ----------
    sim : mp.Simulation

    monitor : mp.DftFlux

    name : str
        Monitor name.

    path : str
        Absolute directory for .npz file.

    subdirectory : str
        Relative directory for Meep .h5 file.
    """

    os.makedirs(path, exist_ok=True)

    np.savez(
        os.path.join(path, f"{name}.npz"),
        flux=np.asarray(mp.get_fluxes(monitor)),
        freqs=np.asarray(mp.get_flux_freqs(monitor)),
    )

    sim.save_flux(
        os.path.join(subdirectory, f"{name}_dft"),
        monitor,
    )

def load_flux_monitor(
    path,
    name,
    Nfreq,
):
    """
    Load cached flux monitor.

    Parameters
    ----------
    path : str
        Directory containing monitor cache.

    name : str
        Monitor name, e.g. "refl", "tran", "x1", ...

    Nfreq : int

    Returns
    -------
    dict
    """

    npz = np.load(
        os.path.join(path, f"{name}.npz")
    )

    E, H = load_dft_h5(
        os.path.join(path, f"{name}_dft.h5"),
        Nfreq,
    )

    return {
        "name": name,
        "flux": npz["flux"],
        "freqs": npz["freqs"],
        "E": E,
        "H": H,
    }
