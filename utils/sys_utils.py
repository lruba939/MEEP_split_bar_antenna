import os
import csv
import socket
import datetime
import psutil
import resource
import pandas as pd
import meep as mp
from mpi4py import MPI
import time
PROGRAM_START_TIME = time.time()

from visualization.plotter import *

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

def log_system_usage(
    path_to_save,
    stage="unknown",
):
    """
    Save current system and process resource usage.
    """
    if not mp.am_master():
        return

    # =====================================================
    # OUTPUT DIR
    # =====================================================

    out_dir = os.path.join(
        path_to_save,
        "system_usage",
    )

    os.makedirs(
        out_dir,
        exist_ok=True,
    )

    logfile = os.path.join(
        out_dir,
        "resource_log.csv",
    )

    # =====================================================
    # MPI
    # =====================================================

    try:
        rank = mp.my_rank()
    except:
        rank = 0

    # =====================================================
    # PROCESS
    # =====================================================

    proc = psutil.Process(
        os.getpid()
    )

    mem = proc.memory_info()

    process_ram = (
        mem.rss / 1024**3
    )

    process_vms = (
        mem.vms / 1024**3
    )

    try:
        full_mem = proc.memory_full_info()

        process_uss = (
            full_mem.uss / 1024**3
        )

        process_pss = (
            full_mem.pss / 1024**3
        )

    except Exception:

        process_uss = -1
        process_pss = -1

    process_cpu = proc.cpu_percent(
        interval=0.1
    )

    process_threads = (
        proc.num_threads()
    )

    try:
        peak_ram = (
            resource.getrusage(
                resource.RUSAGE_SELF
            ).ru_maxrss
            / 1024**2
        )
    except Exception:
        peak_ram = -1

    # =====================================================
    # SYSTEM
    # =====================================================

    vm = psutil.virtual_memory()

    system_ram_total = (
        vm.total / 1024**3
    )

    system_ram_used = (
        vm.used / 1024**3
    )

    system_ram_available = (
        vm.available / 1024**3
    )

    system_ram_percent = (
        vm.percent
    )

    swap = psutil.swap_memory()

    swap_used = (
        swap.used / 1024**3
    )

    swap_percent = (
        swap.percent
    )

    system_cpu = psutil.cpu_percent(
        interval=0.1
    )

    # =====================================================
    # TIME
    # =====================================================

    elapsed = (
        time.time()
        - PROGRAM_START_TIME
    )

    # =====================================================
    # DATA
    # =====================================================

    row = {

        "timestamp":
            datetime.datetime.now().isoformat(),

        "elapsed_s":
            round(elapsed, 3),

        "stage":
            stage,

        "hostname":
            socket.gethostname(),

        "rank":
            rank,

        "pid":
            os.getpid(),

        "process_ram_GB":
            round(process_ram, 3),

        "process_vms_GB":
            round(process_vms, 3),

        "process_uss_GB":
            round(process_uss, 3),

        "process_pss_GB":
            round(process_pss, 3),

        "process_peak_ram_GB":
            round(peak_ram, 3),

        "process_cpu_percent":
            process_cpu,

        "process_threads":
            process_threads,

        "system_ram_used_GB":
            round(system_ram_used, 3),

        "system_ram_available_GB":
            round(system_ram_available, 3),

        "system_ram_total_GB":
            round(system_ram_total, 3),

        "system_ram_percent":
            system_ram_percent,

        "swap_used_GB":
            round(swap_used, 3),

        "swap_percent":
            swap_percent,

        "system_cpu_percent":
            system_cpu,

        "system_processes":
            len(psutil.pids()),
    }

    # =====================================================
    # SAVE
    # =====================================================

    write_header = (
        not os.path.isfile(
            logfile
        )
    )

    with open(
        logfile,
        "a",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=row.keys(),
        )

        if write_header:
            writer.writeheader()

        writer.writerow(row)

    # =====================================================
    # PRINT
    # =====================================================

    print(
        f"[RESOURCE] "
        f"{stage:25s} "
        f"| rank={rank} "
        f"| RSS={process_ram:.2f} GB "
        f"| USS={process_uss:.2f} GB "
        f"| peak={peak_ram:.2f} GB "
        f"| sys={system_ram_used:.1f}/{system_ram_total:.1f} GB "
        f"| swap={swap_used:.1f} GB "
        f"| CPU={system_cpu:.0f}%"
    )
    try:
        update_resource_plots(logfile)
    except Exception as e:
        print(
            "Could not update resource plots:",
            e
        )

def update_resource_plots(logfile):
    """
    Update monitoring plots after each log entry.
    """

    if not mp.am_master():
        return

    df = pd.read_csv(logfile)

    if len(df) < 2:
        return

    outdir = os.path.dirname(logfile)

    x = df["elapsed_s"]

    # =====================================================
    # RAM PROCESS
    # =====================================================

    plt.figure(figsize=(8,5))

    plt.plot(
        x,
        df["process_ram_GB"],
        label="RSS"
    )

    if "process_uss_GB" in df:
        plt.plot(
            x,
            df["process_uss_GB"],
            label="USS"
        )

    plt.plot(
        x,
        df["process_peak_ram_GB"],
        label="Peak"
    )

    plt.xlabel("Elapsed time [s]")
    plt.ylabel("Memory [GB]")
    plt.title("Process memory")
    plt.legend(loc="best")
    plt.grid()

    plt.savefig(
        os.path.join(
            outdir,
            "ram_usage.png"
        ),
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    # =====================================================
    # SYSTEM RAM
    # =====================================================

    plt.figure(figsize=(8,5))

    plt.plot(
        x,
        df["system_ram_used_GB"],
        label="RAM used"
    )

    plt.plot(
        x,
        df["system_ram_available_GB"],
        label="RAM available"
    )

    plt.plot(
        x,
        df["swap_used_GB"],
        label="Swap"
    )

    plt.axhline(
        y=df["system_ram_total_GB"].iloc[0],
        linestyle="--"
    )

    plt.xlabel("Elapsed time [s]")
    plt.ylabel("Memory [GB]")
    plt.title("System memory")
    plt.legend(loc="best")
    plt.grid()

    plt.savefig(
        os.path.join(
            outdir,
            "system_memory.png"
        ),
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    # =====================================================
    # CPU
    # =====================================================

    plt.figure(figsize=(8,5))

    plt.plot(
        x,
        df["process_cpu_percent"],
        label="Process"
    )

    plt.plot(
        x,
        df["system_cpu_percent"],
        label="System"
    )

    plt.xlabel("Elapsed time [s]")
    plt.ylabel("CPU [%]")
    plt.title("CPU usage")
    plt.legend(loc="best")
    plt.grid()

    plt.savefig(
        os.path.join(
            outdir,
            "cpu_usage.png"
        ),
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    # =====================================================
    # STAGES
    # =====================================================

    plt.figure(figsize=(12,8))

    plt.plot(
        x,
        range(len(df)),
        "o-"
    )

    plt.yticks(
        range(len(df)),
        df["stage"]
    )

    plt.xlabel("Elapsed time [s]")
    plt.title("Simulation stages")

    plt.grid("major")

    plt.savefig(
        os.path.join(
            outdir,
            "timing_stages.png"
        ),
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()
