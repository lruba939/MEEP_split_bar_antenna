import json
import os
import numpy as np

def save_metadata(
            cache_dir,
            config,
            structure_name,
            TRL_monitors=None,
            scattering_monitors=None,
            dft_gap_monitors=None,
        ):
    """
    Save simulation metadata required for cache validation.

    Parameters
    ----------
    cache_dir : str
        Path to cache/<structure_name>.

    config : object
        Simulation configuration.

    structure_name : str
        Name of simulated structure ("empty", "substrate", "antenna", ...).

    TRL_monitors : dict, optional
        Dictionary returned by setup_TRL_monitors().

    scattering_monitors : dict, optional
        Reserved for future use.

    dft_gap_monitors : dict, optional
        Reserved for future use.
    """

    def r(x):
        return round(float(x), 10)

    metadata = {
        # =====================================================
        # CACHE
        # =====================================================
        "structure": structure_name,

        # =====================================================
        # COMPUTATIONAL CELL
        # =====================================================
        "cell_size": [r(v) for v in config.cell_size],
        "resolution": config.resolution,

        # =====================================================
        # SOURCE
        # =====================================================
        "frequency": r(config.frequency),
        "frequency_width": r(config.frequency_width),
        "nfreq": config.nfreq,
    }

    # =====================================================
    # TRL
    # =====================================================
    if TRL_monitors is not None:
        metadata["TRL"] = {
            "x_size": r(TRL_monitors["metadata"]["x_size"]),
            "y_size": r(TRL_monitors["metadata"]["y_size"]),
            "z_reflection": r(TRL_monitors["metadata"]["z_reflection"]),
            "z_transmission": r(TRL_monitors["metadata"]["z_transmission"]),
        }

    # =====================================================
    # SCATTERING (future)
    # =====================================================
    if scattering_monitors is not None:
        metadata["SCATTERING"] = scattering_monitors["metadata"]

    # =====================================================
    # DFT (future)
    # =====================================================
    if dft_gap_monitors is not None:
        metadata["DFT"] = dft_gap_monitors["metadata"]

    with open(
        os.path.join(cache_dir, "metadata.json"),
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            metadata,
            f,
            indent=4,
        )

def load_metadata(path):
    """
    Load cache metadata.
    """

    with open(
        os.path.join(path, "metadata.json"),
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)

def validate_cache(
    metadata,
    config,
    TRL=False,
    TRL_X_size=None,
    TRL_Y_size=None,
    scattering=False,
    dft=False,
    harminv=False,
):
    """
    Validate cache metadata against current simulation config.

    Parameters
    ----------
    metadata : dict
        Cache metadata loaded from metadata.json.

    config : SimulationConfig
        Current simulation configuration.

    Raises
    ------
    ValueError
        If cache is incompatible.
    """

    atol = 1e-12

    # =====================================================
    # CELL SIZE
    # =====================================================
    if not np.allclose(
        metadata["cell_size"],
        config.cell_size,
        atol=atol,
    ):
        raise ValueError(
            "Cache validation failed:\n"
            f"cell_size mismatch\n"
            f"cache   : {metadata['cell_size']}\n"
            f"current : {list(config.cell_size)}"
        )

    # =====================================================
    # RESOLUTION
    # =====================================================
    if metadata["resolution"] != config.resolution:
        raise ValueError(
            "Cache validation failed:\n"
            f"resolution mismatch\n"
            f"cache   : {metadata['resolution']}\n"
            f"current : {config.resolution}"
        )

    # =====================================================
    # FREQUENCY
    # =====================================================
    if not np.isclose(
        metadata["frequency"],
        config.frequency,
        atol=atol,
    ):
        raise ValueError(
            "Cache validation failed:\n"
            f"frequency mismatch\n"
            f"cache   : {metadata['frequency']}\n"
            f"current : {config.frequency}"
        )

    # =====================================================
    # FREQUENCY WIDTH
    # =====================================================
    if not np.isclose(
        metadata["frequency_width"],
        config.frequency_width,
        atol=atol,
    ):
        raise ValueError(
            "Cache validation failed:\n"
            f"frequency_width mismatch\n"
            f"cache   : {metadata['frequency_width']}\n"
            f"current : {config.frequency_width}"
        )

    # =====================================================
    # NFREQ
    # =====================================================
    if metadata["nfreq"] != config.nfreq:
        raise ValueError(
            "Cache validation failed:\n"
            f"nfreq mismatch\n"
            f"cache   : {metadata['nfreq']}\n"
            f"current : {config.nfreq}"
        )

    # =====================================================
    # TRL
    # =====================================================
    if TRL:
        if TRL_X_size is None:
            TRL_X_size = config.src_size[0]
        
        if TRL_Y_size is None:
            TRL_Y_size = config.src_size[1]

        if "TRL" not in metadata:
            raise ValueError(
                "Cache validation failed:\n"
                "TRL metadata not found."
            )

        trl = metadata["TRL"]

        checks = {
            "x_size": TRL_X_size,
            "y_size": TRL_Y_size,
            "z_reflection": config.z_reflection,
            "z_transmission": config.z_transmission,
        }

        for key, current in checks.items():

            if not np.isclose(
                trl[key],
                current,
                atol=1e-12,
            ):
                raise ValueError(
                    "Cache validation failed:\n"
                    f"TRL {key} mismatch\n"
                    f"cache   : {trl[key]}\n"
                    f"current : {current}"
                )
    # =====================================================
    # FUTURE MODULES
    # =====================================================
    if scattering:
        pass

    if dft:
        pass

    if harminv:
        pass

    print("\n=======================================")
    print("CACHE VALIDATION PASSED")
    print("=======================================\n")
