import os
import meep as mp
from mpi4py import MPI

HPC = os.environ.get("SCRATCH") is not None

def print_task(task_number, description=None):
    if mp.am_master():
        title = f"## TASK {task_number} ##"
        border = "#" * len(title)
        
        print(border)
        print(title)
        print(border)
        
        if description:
            print(f"Description: {description}")
        
        print("-\n-")

# def create_directory_names(SIM_NAME):
#     path_to_save = os.path.join("results", SIM_NAME)
#     animations_folder_path = os.path.join(path_to_save, "animations")
#     
#     if mp.am_master():
#         if not os.path.exists(path_to_save):
#             os.makedirs(path_to_save)
#         if not os.path.exists(animations_folder_path):
#             os.makedirs(animations_folder_path)
# 
#         return path_to_save, animations_folder_path

# def create_directory(SIM_NAME):
#     # ==========================================
#     # Select base directory
#     # ==========================================
#     if HPC:
#         base_dir = os.environ["SCRATCH"]
#     else:
#         base_dir = os.getcwd()

#     # ==========================================
#     # Paths
#     # ==========================================
#     path_to_save = os.path.join(
#         base_dir,
#         "results",
#         SIM_NAME
#     )

#     animations_folder_path = os.path.join(
#         path_to_save,
#         "animations"
#     )

#     # ==========================================
#     # Create directories only on master process
#     # ==========================================
#     if mp.am_master():

#         os.makedirs(path_to_save, exist_ok=True)
#         os.makedirs(animations_folder_path, exist_ok=True)

#         print("=" * 60)
#         print(f"HPC mode: {HPC}")
#         print(f"Saving results to:")
#         print(path_to_save)
#         print("=" * 60)

#     return path_to_save, animations_folder_path

def create_directory(SIM_NAME):
    """
    Creates unique simulation folder.

    Existing:
        test

    Creates:
        test__2
        test__3
        ...

    Works correctly with MPI.
    """

    comm = MPI.COMM_WORLD

    # ==========================================
    # Select base directory
    # ==========================================
    if HPC:
        base_dir = os.environ["SCRATCH"]
    else:
        base_dir = os.getcwd()

    # ==========================================
    # Requested path
    # ==========================================
    requested_path = os.path.join(
        base_dir,
        "results",
        SIM_NAME
    )

    # ==========================================
    # Master chooses final unique folder
    # ==========================================
    if mp.am_master():
        path_to_save = make_unique_path(requested_path)
    else:
        path_to_save = None

    # Broadcast to all MPI ranks
    path_to_save = comm.bcast(path_to_save, root=0)

    animations_folder_path = os.path.join(
        path_to_save,
        "animations"
    )

    # ==========================================
    # Create folders only once
    # ==========================================
    if mp.am_master():

        os.makedirs(path_to_save)
        os.makedirs(animations_folder_path)

        print("=" * 60)
        print(f"HPC mode: {HPC}")
        print("Saving results to:")
        print(path_to_save)
        print("=" * 60)

    # Wait until directories exist
    comm.Barrier()

    return path_to_save, animations_folder_path

def make_unique_path(path):
    """
    If path exists:
        folder
        folder__2
        folder__3
        ...
    """

    if not os.path.exists(path):
        return path

    counter = 2

    while True:
        candidate = f"{path}__{counter}"

        if not os.path.exists(candidate):
            return candidate

        counter += 1

def build_folder_name(
    structure,
    wavelength_nm,
    gap_nm,
    antenna_material,
    substrate_material,
    **kwargs
):
    """
    Example
    -------
    bowtie__lam-660__gap-6__L-87__T-30__R-5__ant-Au__sub-SiO2
    """

    parts = [
        structure,
        f"lam-{round(wavelength_nm)}",
        f"gap-{round(gap_nm)}",
    ]

    for key in ["L", "W", "T", "R", "H"]:
        value = kwargs.get(key)

        if value is not None:
            parts.append(f"{key}-{round(value)}")

    parts.append(f"ant-{antenna_material}")
    parts.append(f"sub-{substrate_material}")

    return "__".join(parts)