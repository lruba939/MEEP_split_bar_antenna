import meep as mp
import numpy as np
import os, h5py

from utils.field_utils import *
from utils.simulation.cache import *

from visualization.plotter import *

def setup_gap_dft_monitors(
    sim,
    dft_object,
    config,
):
    """
    Create DFT point monitors along the object thickness.

    Parameters
    ----------
    sim : mp.Simulation

    dft_object : object
        Must provide:
            center
            z_offset
            thickness

    config : SimulationConfig

    Returns
    -------
    dict
        {
            "monitors": {
                "point000": monitor,
                "point001": monitor,
                ...
            },
            "metadata": {
                "points": {
                    "point000": (x, y, z),
                    ...
                }
            }
        }
    """
    cx, cy = dft_object.center
    cz = dft_object.z_offset
    thickness = dft_object.thickness

    dz = 1 / config.resolution

    z_min = cz - thickness / 2
    z_max = cz + thickness / 2

    Nz = int(np.round(thickness / dz)) + 1
    z_points = np.linspace(
        z_min,
        z_max,
        Nz,
    )
    monitors = {}
    metadata = {"points": {}}

    for i, z in enumerate(z_points):
        name = f"point{i:03d}"
        point = mp.Vector3(cx, cy, z)

        monitors[name] = sim.add_dft_fields(
            [mp.Ex, mp.Ey, mp.Ez],
            config.frequency,
            config.frequency_width,
            config.nfreq,
            where=mp.Volume(
                center=point,
                size=mp.Vector3(),
            ),
        )

        metadata["points"][name] = {
            "x": cx,
            "y": cy,
            "z": float(z),
        }

    return {
        "monitors": monitors,
        "metadata": metadata,
    }

def save_gap_dft_monitor(
    sim,
    monitor,
    name,
    config,
    path,
):
    """
    Save DFT spectrum at a single point.
    """
    os.makedirs(
        path,
        exist_ok=True,
    )

    data = {
        "freqs": np.linspace(
            config.frequency - config.frequency_width / 2.0,
            config.frequency + config.frequency_width / 2.0,
            config.nfreq,
        ),
    }

    for comp_name, comp in (
        ("Ex", mp.Ex),
        ("Ey", mp.Ey),
        ("Ez", mp.Ez),
    ):
        data[comp_name] = np.array([
            sim.get_dft_array(
                monitor,
                comp,
                i,
            )
            for i in range(config.nfreq)
        ])

    np.savez(
        os.path.join(
            path,
            f"{name}.npz",
        ),
        **data,
    )

def load_gap_dft(
    path,
):
    """
    Load cached DFT point monitors.
    """
    metadata = load_metadata(
        os.path.dirname(path)
    )

    monitors = {}

    for name in metadata["GAP_DFT"]["points"]:
        data = np.load(
            os.path.join(path, f"{name}.npz")
        )

        monitors[name] = {
            "freqs": data["freqs"],
            "Ex": data["Ex"],
            "Ey": data["Ey"],
            "Ez": data["Ez"],
        }

    return {
        "monitors": monitors,
        "metadata": metadata,
    }

def save_gap_dft(
    results,
    save_path,
):
    """
    Save gap DFT spectra.
    """
    os.makedirs(
        save_path,
        exist_ok=True,
    )

    components = (
        "Ex",
        "Ey",
        "Ez",
        "E2",
    )

    datasets = (
        "empty",
        "substrate",
        "antenna",
        "substrate_over_empty",
        "antenna_over_empty",
        "antenna_over_substrate",
    )

    for point_name, point in results.items():
        columns = [
            point["frequency"],
            point["wavelength"],
        ]
        header = [
            "frequency",
            "wavelength",
        ]
        for dataset in datasets:
            if dataset not in point:
                continue

            for comp in components:
                columns.append(
                    point[dataset][comp]
                )
                header.append(
                    f"{dataset}_{comp}"
                )

        np.savetxt(
            os.path.join(
                save_path,
                f"{point_name}.dat",
            ),
            np.column_stack(columns),
            header=" ".join(header),
        )

def plot_gap_dft(
    results,
    save_path,
):
    """
    Plot gap DFT spectra.
    """
    os.makedirs(
        save_path,
        exist_ok=True,
    )

    components = (
        "Ex",
        "Ey",
        "Ez",
        "E2",
    )

    datasets = (
        "empty",
        "substrate",
        "antenna",
        "substrate_over_empty",
        "antenna_over_empty",
        "antenna_over_substrate",
    )

    point_names = list(results.keys())

    z_points = [
        results[p]["position"]["z"]
        for p in point_names
    ]

    cmap = plt.get_cmap("inferno")

    if len(point_names) == 1:
        colors = [cmap(0.5)]
    else:
        colors = [
            cmap(i/(len(point_names)-1))
            for i in range(len(point_names))
        ]

    for dataset in datasets:
        if dataset not in results[point_names[0]]:
            continue

        for comp in components:
            multi_line_plotter_same_axes(
                xdata_list=[
                    results[p]["wavelength"]
                    for p in point_names
                ],
                ydata_list=[
                    results[p][dataset][comp]
                    for p in point_names
                ],
                labels=[
                    f"z={z:.3f}"
                    for z in z_points
                ],
                colors=colors,
                xlabel="Wavelength [μm]",
                ylabel=comp,
                title=f"{comp} ({dataset.replace('_',' ')})",
                legend=False,
                save_path=save_path,
                save_name=f"{comp}_{dataset}.png",
            )
    
    # =====================================================
    # OFFSET PLOTS
    # =====================================================
    for dataset in (
        "substrate_over_empty",
        "antenna_over_empty",
        "antenna_over_substrate",
    ):
        if dataset not in results[point_names[0]]:
            continue

        for comp in ("Ex", "Ey", "Ez", "E2"):
            plt.figure(figsize=(5,6))

            offset_step = 1.2 * np.max([
                np.max(results[p][dataset][comp])
                for p in point_names
            ])

            for i, point_name in enumerate(point_names):
                color = colors[i]

                x = results[point_name]["wavelength"] * 1000
                y = results[point_name][dataset][comp] + i*offset_step

                plt.plot(x, y, color=color)

                z_nm = (results[point_name]["position"]["z"]*1000)

                plt.text(
                    x[-1]*1.01,
                    y[-1],
                    f"{z_nm:.0f} nm",
                    fontsize=8,
                    color=color,
                    va="center",
                )

            plt.xlabel("Wavelength [nm]")
            plt.ylabel(f"{comp} + offset")
            plt.tight_layout()

            plt.savefig(
                os.path.join(
                    save_path,
                    f"{comp}_{dataset}_offset.png",
                ),
                dpi=300,
                bbox_inches="tight",
            )
            plt.close()

def compute_gap_dft(
    empty_path,
    substrate_path=None,
    antenna_path=None,
    save_path=None,
):
    """
    Compute gap DFT spectra from cached point monitors.

    Parameters
    ----------
    empty_path : str

    substrate_path : str or None

    antenna_path : str or None

    save_path : str or None

    Returns
    -------
    dict
    """
    if not mp.am_master():
        return

    # =====================================================
    # LOAD
    # =====================================================
    empty = load_gap_dft(empty_path)

    substrate = None
    antenna = None

    if substrate_path is not None:
        substrate = load_gap_dft(substrate_path)

    if antenna_path is not None:
        antenna = load_gap_dft(antenna_path)

    # =====================================================
    # FREQUENCY
    # =====================================================
    if not empty["monitors"]:
        raise RuntimeError(
            "No GAP DFT monitors found."
        )

    first_point = next(iter(empty["monitors"]))

    frequency = empty["monitors"][first_point]["freqs"]
    wavelength = 1.0 / frequency

    eps = 1e-30

    components = ("Ex", "Ey", "Ez")
    components_all = (*components, "E2")

    results = {}

    # =====================================================
    # COMPUTE
    # =====================================================
    for name, position in empty["metadata"]["GAP_DFT"]["points"].items():
        results[name] = {
            "position": position,
            "frequency": frequency,
            "wavelength": wavelength,
        }

        # -------------------------------------------------
        # EMPTY
        # -------------------------------------------------
        empty_data = {}
        for comp in components:
            empty_data[comp] = np.abs(
                empty["monitors"][name][comp]
            )**2

        empty_data["E2"] = sum(
            empty_data[comp]
            for comp in components
        )

        results[name]["empty"] = empty_data

        # -------------------------------------------------
        # SUBSTRATE
        # -------------------------------------------------
        substrate_data = None
        if substrate is not None:
            substrate_data = {}
            for comp in components:
                substrate_data[comp] = np.abs(
                    substrate["monitors"][name][comp]
                )**2

            substrate_data["E2"] = sum(
                substrate_data[comp]
                for comp in components
            )

            results[name]["substrate"] = substrate_data

            results[name]["substrate_over_empty"] = {
                comp:
                substrate_data[comp] /
                (empty_data[comp] + eps)
                for comp in components_all
            }

        # -------------------------------------------------
        # ANTENNA
        # -------------------------------------------------
        antenna_data = None
        if antenna is not None:
            antenna_data = {}
            for comp in components:
                antenna_data[comp] = np.abs(
                    antenna["monitors"][name][comp]
                )**2

            antenna_data["E2"] = sum(
                antenna_data[comp]
                for comp in components
            )

            results[name]["antenna"] = antenna_data

            results[name]["antenna_over_empty"] = {
                comp:
                antenna_data[comp] /
                (empty_data[comp] + eps)
                for comp in components_all
            }

            if substrate_data is not None:
                results[name]["antenna_over_substrate"] = {
                    comp:
                    antenna_data[comp] /
                    (substrate_data[comp] + eps)
                    for comp in components_all
                }

    # =====================================================
    # SAVE
    # =====================================================
    if save_path is not None:
        os.makedirs(
            save_path,
            exist_ok=True,
        )
        save_gap_dft(
            results,
            save_path,
        )
        plot_gap_dft(
            results,
            save_path,
        )
    return results
