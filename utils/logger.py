import os
from datetime import datetime
import meep as mp
from meep.materials import Au, Ti, SiO2, Pd

# --------------------------------------------------------
# MAIN LOGGER FUNCTION
# --------------------------------------------------------

def save_and_show_config(config, antenna, COMMENT=None):
    show_experiment(config, antenna)
    save_experiment(config, antenna, COMMENT=COMMENT)
    append_time_to_file(config, prefix="Start time: ")
    return 0

# --------------------------------------------------------
# MATERIAL NAME RESOLVER
# --------------------------------------------------------

def _format_value(value):
    
    # ---- Symmetries
    if isinstance(value, list):
        if len(value) > 0 and isinstance(value[0], mp.Mirror):
            formatted = []
            for m in value:
                direction = (
                    "X" if m.direction == mp.X else
                    "Y" if m.direction == mp.Y else
                    "Z"
                )
                phase = int(m.phase.real)
                formatted.append(f"Mirror({direction}, phase={phase})")
            return formatted
        return value

    # ---- Field components
    if value is mp.Ex: return "Ex"
    if value is mp.Ey: return "Ey"
    if value is mp.Ez: return "Ez"
    if value is mp.Hx: return "Hx"
    if value is mp.Hy: return "Hy"
    if value is mp.Hz: return "Hz"

    # ---- Standard materials (identity comparison ONLY)
    if value is Au: return "Au"
    if value is Ti: return "Ti"
    if value is SiO2: return "SiO2"
    if value is Pd: return "Pd"

    # ---- Custom Medium
    if isinstance(value, mp.Medium):
        return f"Medium(epsilon={value.epsilon})"

    # ---- numpy arrays → convert to list
    try:
        import numpy as np
        if isinstance(value, np.ndarray):
            return value.tolist()
    except:
        pass

    return value

# --------------------------------------------------------
# SHOW
# --------------------------------------------------------

def show_experiment(config, antennas):
    if mp.am_master():
        print("\n\n#################################")
        print("EXPERIMENT CONFIGURATION")
        print("#################################\n")

        # ---- Simulation ----
        print("---- Simulation ----")
        for key, value in config.__dict__.items():
            if key.startswith("_"):
                continue
            print(f"{key} = {_format_value(value)}")

        print("\nDerived:")
        print(f"frequency = {config.frequency}")
        print(f"frequency_width = {config.frequency_width}")

        # ---- Antennas ----
        if not isinstance(antennas, (list, tuple)):
            antennas = [antennas]

        print("\n---- Objects ----")

        for idx, antenna in enumerate(antennas, start=1):

            print(f"\nObject #{idx}")
            print(f"type = {antenna.__class__.__name__}")

            for key, value in antenna.__dict__.items():
                if key.startswith("_"):
                    continue
                print(f"{key} = {_format_value(value)}")

            if hasattr(antenna, "bounding_box"):
                print(f"bounding_box = {antenna.bounding_box()}")

        print("\n#################################\n")

# --------------------------------------------------------
# SAVE
# --------------------------------------------------------

def save_experiment(config, antennas, filename=None, COMMENT=None):
    if mp.am_master():
        if filename is None:
            filename = os.path.join(config.path_to_save, "experiment.txt")

        os.makedirs(config.path_to_save, exist_ok=True)
        os.makedirs(config.animations_folder_path, exist_ok=True)

        if not isinstance(antennas, (list, tuple)):
            antennas = [antennas]

        with open(filename, "w") as f:
            # ---- Comment ----
            if COMMENT is None:
                COMMENT = "No comment"
            f.write("#################################\n")
            f.write("COMMENT\n")
            f.write("#################################\n")
            f.write(f"{COMMENT}\n")
            f.write("#################################\n")

            f.write("\n\n#################################\n")
            f.write("EXPERIMENT CONFIGURATION\n")
            f.write("#################################\n\n")

            # ---- Simulation ----
            f.write("---- Simulation ----\n")
            for key, value in config.__dict__.items():
                if key.startswith("_"):
                    continue
                f.write(f"{key} = {_format_value(value)}\n")
            warning_PML2wav_ratio = warning_PML2wav(config)
            f.write(f"{warning_PML2wav_ratio}\n")

            f.write("\nDerived:\n")
            f.write(f"frequency = {config.frequency}\n")
            f.write(f"frequency_width = {config.frequency_width}\n")

            # ---- Objects ----
            f.write("\n---- Objects ----\n")

            for idx, antenna in enumerate(antennas, start=1):

                f.write(f"\nObject #{idx}\n")
                f.write(f"type = {antenna.__class__.__name__}\n")

                for key, value in antenna.__dict__.items():
                    if key.startswith("_"):
                        continue
                    f.write(f"{key} = {_format_value(value)}\n")

                if hasattr(antenna, "bounding_box"):
                    f.write(f"bounding_box = {antenna.bounding_box()}\n")

            f.write("\n#################################\n\n")

def warning_PML2wav(config):
    if mp.am_master():
        PML2wav_ratio = config.pml / config.lambda0
        if PML2wav_ratio < 0.5:
            PML2wav_ratio_warning = "\n\nWARNING! PML should be at least 0.5 times the wavelength used!!!\n"
            print(PML2wav_ratio_warning)
            return PML2wav_ratio_warning

def append_time_to_file(config, filename=None, prefix="Time: "):
    if mp.am_master():
        if filename is None:
            filename = os.path.join(config.path_to_save, "experiment.txt")

        now = datetime.now()
        current_time = now.strftime("%H:%M")

        with open(filename, "a") as f:
            f.write("\n---- TIME ----\n")
            f.write(f"{prefix}{current_time}\n")
    return 0