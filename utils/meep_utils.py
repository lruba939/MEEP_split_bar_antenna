import meep as mp
from meep.materials import *
import numpy as np
import os
import json

from visualization.plotter import *

from utils.logger import append_time_to_file

from utils.sys_utils import *

from utils.enhancement import *

from utils.simulation.cache import *
from utils.simulation.trl import *
from utils.simulation.scattering import *
from utils.simulation.gap_dft import *

# !!!!!!!!! ---> from main.src.simulation import * # CANT IMPORT DUE TO CIRCULAR DEPENDENCY

def get_materials_dict(material_name=None):
    materials = {
        # dielectrics / semiconductors
        "air": mp.air,
        "cSi": cSi,
        "aSi": aSi,
        "SiO2": SiO2,
        "ITO": ITO,
        "Al2O3": Al2O3,
        "GaAs": GaAs,
        "AlAs": AlAs,
        "AlN": AlN,
        "BK7": BK7,
        "FQ": fused_quartz,
        "Si3N4": Si3N4,
        "Ge": Ge,
        "InP": InP,
        "GaN": GaN,
        "CdTe": CdTe,
        "LiNbO3": LiNbO3,
        "BaB2O4": BaB2O4,
        "CaWO4": CaWO4,
        "CaCO3": CaCO3,
        "Y2O3": Y2O3,
        "YAG": YAG,
        "PMMA": PMMA,
        # metals
        "Ag": Ag,
        "Au": Au,
        "Cu": Cu,
        "Al": Al,
        "Be": Be,
        "Cr": Cr,
        "Ni": Ni,
        "Pd": Pd,
        "Pt": Pt,
        "Ti": Ti,
        "W": W,
    }
    if material_name not in materials:
        raise ValueError(f"Unknown material: {material_name}")
    if material_name is None:
        return materials["air"]

    return materials[material_name]

def collect_fields_with_output(
    sim,
    volumes,          # dict: {name: mp.Volume}
    delta_t,
    until,
    start_time=0.0,
    path=None,
    calc_E_fields=True,
    calc_H_fields=False,
    calc_Dpwr=False,
    extra_run_functions=None,
    config=None,
):
    """
    Collect selected field data for multiple volumes in ONE sim.run().

    Field components to be recorded are controlled by boolean flags.

    FIXED BEHAVIOR
    --------------
    * Data are written as HDF5 files using mp.to_appended(...)
    * All outputs follow the naming scheme:
          <prefix>_<field>.h5
      where <prefix> comes from the `volumes` dict.
    * Output directory is controlled at the Simulation level via
      sim.use_output_directory().

    PARAMETERS
    ----------
    sim : mp.Simulation
        Initialized Meep simulation object.

    volumes : dict[str, mp.Volume]
        Mapping of output prefixes to Meep volumes, e.g.:
            {
                "planar": planar_vol,
                "volume": volume_vol
            }

    delta_t : float
        Time interval between successive field outputs.

    until : float
        End time of the simulation.

    start_time : float, optional
        Time after which field recording starts.
        If 0.0, recording starts immediately.

    path : str or None, optional
        Directory where all HDF5 output files are written.
        If None, default Meep behavior is used.

    calc_E_fields : bool, optional
        If True, record electric field components:
            Ex, Ey, Ez

    calc_H_fields : bool, optional
        If True, record magnetic field components:
            Hx, Hy, Hz

    calc_Dpwr : bool, optional
        If True, record electric field energy density (Dpwr).

    extra_run_functions : callable or list of callables, optional
        Additional Meep step functions passed directly to sim.run().
    
        These can be used to extend the simulation with custom runtime
        behaviors such as:
    
            * mp.after_sources(mp.Harminv(...)) — modal (Harminv) analysis
            * mp.at_every(...) — custom field sampling
            * mp.at_end(...) — post-run callbacks
    
        The provided function(s) are appended to the internally constructed
        run actions and executed within the same sim.run() call.
    
        If None (default), no additional step functions are applied.

    NOTES
    -----
    * At least one of (calc_E_fields, calc_H_fields, calc_Dpwr)
      should be True, otherwise no data will be collected.
    * Default configuration records only E-field components.
    """
    # --------------------------------------------------
    # Disable default filename prefix (clean filenames)
    # --------------------------------------------------
    sim.filename_prefix = ""

    # --------------------------------------------------
    # Set output directory (Simulation-level, per docs)
    # --------------------------------------------------
    if path is not None:
        sim.use_output_directory(path)

    run_actions = []

    for prefix, volume in volumes.items():

        actions = []

        # -------------------------
        # Electric field components
        # -------------------------
        if calc_E_fields:
            actions.extend([
                mp.to_appended(f"{prefix}_ex", mp.at_every(delta_t, mp.output_efield_x)),
                mp.to_appended(f"{prefix}_ey", mp.at_every(delta_t, mp.output_efield_y)),
                mp.to_appended(f"{prefix}_ez", mp.at_every(delta_t, mp.output_efield_z)),
            ])

        # -------------------------
        # Magnetic field components
        # -------------------------
        if calc_H_fields:
            actions.extend([
                mp.to_appended(f"{prefix}_hx", mp.at_every(delta_t, mp.output_hfield_x)),
                mp.to_appended(f"{prefix}_hy", mp.at_every(delta_t, mp.output_hfield_y)),
                mp.to_appended(f"{prefix}_hz", mp.at_every(delta_t, mp.output_hfield_z)),
            ])

        # -------------------------
        # Energy density
        # -------------------------
        if calc_Dpwr:
            actions.append(
                mp.to_appended(f"{prefix}_dpwr", mp.at_every(delta_t, mp.output_dpwr))
            )

        # -------------------------
        # Skip volumes with no actions
        # -------------------------
        if not actions:
            continue

        # -------------------------
        # Volume action
        # -------------------------
        if start_time > 0:
            vol_action = mp.in_volume(
                volume,
                mp.after_time(start_time, *actions)
            )
        else:
            vol_action = mp.in_volume(volume, *actions)

        run_actions.append(vol_action)

    # --------------------------------------------------
    # Safety check
    # --------------------------------------------------
    if not run_actions:
        raise ValueError(
            "No field outputs selected. "
            "Set at least one of calc_E_fields, calc_H_fields, calc_Dpwr to True."
        )
        
    # --------------------------------------------------
    # Include extra funcs
    # --------------------------------------------------
    if extra_run_functions is not None:
        if isinstance(extra_run_functions, list):
            run_actions.extend(extra_run_functions)
        else:
            run_actions.append(extra_run_functions)

    # --------------------------------------------------
    # Single sim.run()
    # --------------------------------------------------
    ########################
    log_system_usage(
        config.path_to_save,
        "start_sim.run()",
    )
    #######################
    sim.run(*run_actions, until=until)
    ########################
    log_system_usage(
        config.path_to_save,
        "end_sim.run()",
    )
    #######################
    return sim

##############################################
def compute_fields(
    sim_antenna,
    sim_empty,
    volumes,
    config,
    mode="BOTH",
    calc_E=True,
    calc_H=False,
    calc_DPWR=False,
    fluxes=True,
    fluxes_X_size=None,
    fluxes_Y_size=None,
    scattering=False,
    scattering_antenna=None,
    dft_gap_spectrum=False,
    harminv=False,
):
    pass


# def compute_fields(
#     sim_antenna,
#     sim_empty,
#     volumes,
#     config,
#     mode="BOTH",
#     calc_E=True,
#     calc_H=False,
#     calc_DPWR=False,
#     fluxes=True,
#     fluxes_X_size=None,
#     fluxes_Y_size=None,
#     scattering=False,
#     scattering_antenna=None,
#     dft_gap_spectrum=False,
#     harminv=False,
# ):
#     """
#     Run field simulations and compute enhancement maps.

#     Parameters
#     ----------
#     mode : str
#         "WITH_ANTENNA", "EMPTY", "BOTH", "ENH_ONLY" or "WITH_EMPTY_CACHE"

#     calc_E : bool
#         Whether to calculate E-field enhancement.

#     calc_H : bool
#         Whether to calculate H-field enhancement.

#     calc_DPWR : bool
#         Whether to calculate power density fields.
#     """

#     valid_modes = ["WITH_ANTENNA", "EMPTY", "BOTH", "ENH_ONLY", "WITH_EMPTY_CACHE"]

#     if mode not in valid_modes:
#         raise ValueError(f"mode must be one of {valid_modes}")

#     # ============================================================
#     # Plane configuration
#     # ============================================================
#     planes = {
#         "xyplanar": volumes.volume["XY"],
#         "xyplanarTOP": volumes.volume["XY_TOP"],
#         "xzplanar": volumes.volume["XZ"],
#         "yzplanar": volumes.volume["YZ"],
#     }

#     fcen = config.frequency
#     df = config.frequency_width
#     nfreq = config.nfreq
#     # ============================================================
#     # FLUX MONITORS
#     # ============================================================
#     if fluxes:
#         if fluxes_X_size is None:
#             fluxes_X_size = config.src_size[0]
#         if fluxes_Y_size is None:
#             fluxes_Y_size = config.src_size[1]
    
#         refl_fr = mp.FluxRegion(
#             center=mp.Vector3(0, 0, config.z_reflection),
#             size=mp.Vector3(
#                 fluxes_X_size,
#                 fluxes_Y_size,
#                 0)
#         )

#         tran_fr = mp.FluxRegion(
#             center=mp.Vector3(0, 0, config.z_transmission),
#             size=mp.Vector3(
#                 fluxes_X_size,
#                 fluxes_Y_size,
#                 0)
#         )

#         refl_empty = sim_empty.add_flux(fcen, df, nfreq, refl_fr)
#         tran_empty = sim_empty.add_flux(fcen, df, nfreq, tran_fr)
#         refl = sim_antenna.add_flux(fcen, df, nfreq, refl_fr)
#         tran = sim_antenna.add_flux(fcen, df, nfreq, tran_fr)
#     # ============================================================
#     # SCATTERING MONITORS
#     # ============================================================
#     if scattering:
#         if scattering_antenna is None:
#             raise ValueError("scattering_antenna must be provided for scattering spectrum")
#         # scattering box
#         Lx, Ly, Lz = make_scattering_box(
#             antenna=scattering_antenna,
#             config=config, padding_perc=10,
#             extra_padding_nm=(0, 0, 0))

#         cx, cy = scattering_antenna.center
#         cz = scattering_antenna.z_offset

#         scatt_regions = [
#             # --- X planes ---
#             mp.FluxRegion(
#                 center=mp.Vector3(cx - Lx/2, cy, cz),
#                 size=mp.Vector3(0, Ly, Lz)
#             ),
#             mp.FluxRegion(
#                 center=mp.Vector3(cx + Lx/2, cy, cz),
#                 size=mp.Vector3(0, Ly, Lz)
#             ),

#             # --- Y planes ---
#             mp.FluxRegion(
#                 center=mp.Vector3(cx, cy - Ly/2, cz),
#                 size=mp.Vector3(Lx, 0, Lz)
#             ),
#             mp.FluxRegion(
#                 center=mp.Vector3(cx, cy + Ly/2, cz),
#                 size=mp.Vector3(Lx, 0, Lz)
#             ),

#             # --- Z planes ---
#             mp.FluxRegion(
#                 center=mp.Vector3(cx, cy, cz - Lz/2),
#                 size=mp.Vector3(Lx, Ly, 0)
#             ),
#             mp.FluxRegion(
#                 center=mp.Vector3(cx, cy, cz + Lz/2),
#                 size=mp.Vector3(Lx, Ly, 0)
#             ),
#         ]

#         scatt_empty = [sim_empty.add_flux(fcen, df, nfreq, r) for r in scatt_regions]
#         scatt = [sim_antenna.add_flux(fcen, df, nfreq, r) for r in scatt_regions]
#     # ============================================================
#     # GAP DFT MONITORS
#     # ============================================================
#     if dft_gap_spectrum:
#         if dft_gap_spectrum and mode != "BOTH":
#             raise ValueError("DFT gap spectrum requires mode='BOTH'")
#         if scattering_antenna is None:
#             raise ValueError("scattering_antenna must be provided for DFT gap spectrum")
            
#         cx, cy = scattering_antenna.center
#         cz = scattering_antenna.z_offset
#         t = scattering_antenna.thickness

#         dz = 1 / config.resolution

#         z_min = cz - t / 2
#         z_max = cz + t / 2

#         Nz = int(np.round(t / dz)) + 1
#         z_points = z_min + np.arange(Nz) * dz

#         gap_dft_empty = []
#         gap_dft_antenna = []

#         for z in z_points:
#             pt = mp.Vector3(cx, cy, z)
#             # EMPTY
#             gap_dft_empty.append(
#                 sim_empty.add_dft_fields(
#                     [mp.Ex, mp.Ey, mp.Ez],
#                     fcen,
#                     df,
#                     nfreq,
#                     where=mp.Volume(center=pt, size=mp.Vector3(0, 0, 0))
#                 )
#             )
#             # ANTENNA
#             gap_dft_antenna.append(
#                 sim_antenna.add_dft_fields(
#                     [mp.Ex, mp.Ey, mp.Ez],
#                     fcen,
#                     df,
#                     nfreq,
#                     where=mp.Volume(center=pt, size=mp.Vector3(0, 0, 0))
#                 )
#             )

#     # ============================================================
#     # HARMONIC INVERSION IN GAP
#     # ============================================================
#     if harminv:
#         if scattering_antenna is None:
#             raise ValueError("scattering_antenna must be provided for Harminv")

#         harminv_t0 = 8 # for debug !! after -> to config
    
#         cx, cy = scattering_antenna.center
#         cz = scattering_antenna.z_offset
#         t = scattering_antenna.thickness
    
#         dz = 1 / config.resolution
    
#         # --- in gap ---
#         gap_points = [
#             mp.Vector3(cx, cy, cz - t/2 + 2*dz),  # bottom
#             mp.Vector3(cx, cy, cz),             # center
#             mp.Vector3(cx, cy, cz + t/2 - 2*dz),  # top
#         ]
    
#         # --- corner of antena ---
#         # To have the same distance from the corner to the point as from the main corner to the gap center,
#         # we need to take the angle into account
#         corner_deg = np.arctan(scattering_antenna.width / 2 / scattering_antenna.length)
#         corner_cx = cx + scattering_antenna.gap/2 + scattering_antenna.length + (scattering_antenna.gap/2.0)*np.cos(corner_deg) 
#         corner_cy = cy + scattering_antenna.width/2 + (scattering_antenna.gap/2.0)*np.sin(corner_deg)
#         tip_points = [
#             mp.Vector3(corner_cx,corner_cy, cz),
#             mp.Vector3(corner_cx,corner_cy, cz + 2*dz),
#             mp.Vector3(corner_cx,corner_cy, cz - 2*dz),
#         ]
    
#         # --- arm ---
#         arm_cx = cx + scattering_antenna.length + scattering_antenna.gap
#         arm_points = [
#             mp.Vector3(arm_cx, cy, cz),
#             mp.Vector3(arm_cx, cy, cz + 2*dz),
#             mp.Vector3(arm_cx, cy, cz - 2*dz),
#         ]
    
#         # --- far above ---
#         far_point = mp.Vector3(cx, cy, cz + 2*t)
    
#         harminv_points = (
#             gap_points +
#             tip_points +
#             arm_points +
#             [far_point]
#         )
    
#         harminv_objects = []
    
#         for pt in harminv_points:
#             hi_fcen = fcen
#             hi_df = df
#             h = mp.Harminv(mp.Ex, pt, hi_fcen, hi_df, mxbands=100) # !! mp.Ex for debug -> after should be config.component
#             harminv_objects.append((pt, h))
#     # ============================================================
#     # EMPTY STRUCTURE
#     # ============================================================
#     if mode in ["EMPTY", "BOTH"]:
#         if mp.am_master():
#             print("Running simulation WITHOUT antenna")
#             append_time_to_file(config, prefix="Running simulation WITHOUT antenna: ")

#         empty_planes = {f"{k}-empty": v for k, v in planes.items()}

#         sim_empty = collect_fields_with_output(
#             sim_empty,
#             volumes=empty_planes,
#             delta_t=config.sim_time_step,
#             until=config.sim_time,
#             start_time=0,
#             path=config.path_to_save,
#             calc_E_fields=calc_E,
#             calc_H_fields=calc_H,
#             calc_Dpwr=calc_DPWR,
#         )
#         if fluxes and mode == "BOTH":
#             incident_flux = mp.get_fluxes(tran_empty)
#             refl_data = sim_empty.get_flux_data(refl_empty)
#             sim_antenna.load_minus_flux_data(refl, refl_data)
#         if scattering and mode == "BOTH":
#             scatt_data = [sim_empty.get_flux_data(f) for f in scatt_empty]
#             scatt_flux_faces_empty = [np.asarray(mp.get_fluxes(f)) for f in scatt_empty]
#             for f, d in zip(scatt, scatt_data):
#                 sim_antenna.load_minus_flux_data(f, d)
#             incident_flux_top = np.asarray(mp.get_fluxes(scatt_empty[5]))
#             intensity = incident_flux_top / (Lx * Ly)
#         if dft_gap_spectrum and mode == "BOTH":
#             gap_data_empty = {
#                 "Ex": [],
#                 "Ey": [],
#                 "Ez": [],
#             }
        
#             for dft_e in gap_dft_empty:
        
#                 Ex_e = np.array([
#                     sim_empty.get_dft_array(dft_e, mp.Ex, i)
#                     for i in range(nfreq)
#                 ])
#                 Ey_e = np.array([
#                     sim_empty.get_dft_array(dft_e, mp.Ey, i)
#                     for i in range(nfreq)
#                 ])
#                 Ez_e = np.array([
#                     sim_empty.get_dft_array(dft_e, mp.Ez, i)
#                     for i in range(nfreq)
#                 ])
        
#                 gap_data_empty["Ex"].append(np.abs(Ex_e)**2)
#                 gap_data_empty["Ey"].append(np.abs(Ey_e)**2)
#                 gap_data_empty["Ez"].append(np.abs(Ez_e)**2)
        
#             # numpy
#             for comp in gap_data_empty:
#                 gap_data_empty[comp] = np.array(gap_data_empty[comp])

#         if mp.am_master():
#             print("Done.")
#         sim_empty.reset_meep()

#     # ============================================================
#     # WITH ANTENNA
#     # ============================================================
#     if mode in ["WITH_ANTENNA", "BOTH"]:
#         if mp.am_master():
#             print("Running simulation WITH antenna")
#             append_time_to_file(config, prefix="Running simulation WITH antenna: ")

#         if harminv:
#             extra_run_functions = [
#                 mp.after_time(harminv_t0, h) for _, h in harminv_objects
#             ]
#         else:
#             extra_run_functions = None
        
#         sim_antenna = collect_fields_with_output(
#             sim_antenna,
#             volumes=planes,
#             delta_t=config.sim_time_step,
#             until=config.sim_time,
#             start_time=0,
#             path=config.path_to_save,
#             calc_E_fields=calc_E,
#             calc_H_fields=calc_H,
#             calc_Dpwr=calc_DPWR,
#             extra_run_functions=extra_run_functions,
#         )
#         if fluxes and mode == "BOTH":
#             refl_flux = mp.get_fluxes(refl)
#             tran_flux = mp.get_fluxes(tran)
#             flux_freqs = mp.get_flux_freqs(tran)
#         if scattering and mode == "BOTH":
#             scatt_flux_faces = [np.asarray(mp.get_fluxes(f)) for f in scatt]

#             x1, x2, y1, y2, z1, z2 = scatt_flux_faces

#             scatt_flux_total = (
#                 x1 - x2 +
#                 y1 - y2 +
#                 z1 - z2
#             )
#             scatt_cross_section = scatt_flux_total / intensity # <- from empty
#             flux_freqs_scatt = mp.get_flux_freqs(scatt_empty[5])  # z2
#         if dft_gap_spectrum and mode == "BOTH":
#             gap_data = {
#                 "Ex": {"empty": gap_data_empty["Ex"], "antenna": []},
#                 "Ey": {"empty": gap_data_empty["Ey"], "antenna": []},
#                 "Ez": {"empty": gap_data_empty["Ez"], "antenna": []},
#             }

#             for dft_a in gap_dft_antenna:

#                 Ex_a = np.array([
#                     sim_antenna.get_dft_array(dft_a, mp.Ex, i)
#                     for i in range(nfreq)
#                 ])
#                 Ey_a = np.array([
#                     sim_antenna.get_dft_array(dft_a, mp.Ey, i)
#                     for i in range(nfreq)
#                 ])
#                 Ez_a = np.array([
#                     sim_antenna.get_dft_array(dft_a, mp.Ez, i)
#                     for i in range(nfreq)
#                 ])

#                 gap_data["Ex"]["antenna"].append(np.abs(Ex_a)**2)
#                 gap_data["Ey"]["antenna"].append(np.abs(Ey_a)**2)
#                 gap_data["Ez"]["antenna"].append(np.abs(Ez_a)**2)

#             # numpy
#             for comp in gap_data:
#                 gap_data[comp]["antenna"] = np.array(gap_data[comp]["antenna"])

#             gap_data["E2"] = {}

#             gap_data["E2"]["antenna"] = (
#                 gap_data["Ex"]["antenna"] +
#                 gap_data["Ey"]["antenna"] +
#                 gap_data["Ez"]["antenna"]
#             )

#             gap_data["E2"]["empty"] = (
#                 gap_data["Ex"]["empty"] +
#                 gap_data["Ey"]["empty"] +
#                 gap_data["Ez"]["empty"]
#             )

#             eps = 1e-20

#             for comp in gap_data:
#                 gap_data[comp]["enh"] = (
#                     gap_data[comp]["antenna"] /
#                     (gap_data[comp]["empty"] + eps)
#                 )
#         if mp.am_master():
#             print("Done.")
#         sim_antenna.reset_meep()

#     # ============================================================
#     # TRAN AND REFL CALCULATION
#     # ============================================================
#     if fluxes and mode == "BOTH":
#         if mp.am_master():
#             print("Calculating fluxes")
#         compute_T_R_A(
#             incident_flux,
#             tran_flux, refl_flux,
#             flux_freqs,
#             config.path_to_save)
#         if mp.am_master():
#             print("Done.")

#     # ============================================================
#     # SCATT CALCULATION
#     # ============================================================        
#     if scattering and mode == "BOTH":
#         if mp.am_master():
#             print("Calculating scattering")
#         compute_scattering(
#             scatt_cross_section,
#             intensity,
#             flux_freqs,
#             scatt_flux_faces,
#             scatt_flux_faces_empty,
#             save_path=config.path_to_save,
#         )
#         if mp.am_master():
#             print("Done.")

#     # ============================================================
#     # GAP DFT DATA COLLECTION
#     # ============================================================        
#     if dft_gap_spectrum and mode == "BOTH":
#         if mp.am_master():
#             print("Calculating gap DFT spectrum")
#         freqs = np.linspace(fcen - df/2, fcen + df/2, nfreq)
#         compute_gap_spectrum(
#             gap_data,
#             z_points,
#             freqs,
#             save_path=config.path_to_save,
#         )
#         if mp.am_master():
#             print("Done.")

#     # ============================================================
#     # HARMINV CALCULATION
#     # ============================================================
#     if harminv and mode in ["WITH_ANTENNA", "BOTH"]:
#         if mp.am_master():
#             print("Calculating Harminv modes")
#         compute_harminv(
#             harminv_objects,
#             save_path=config.path_to_save,
#         )
#         if mp.am_master():
#             print("Done.")

#     # ============================================================
#     # ENHANCEMENT CALCULATION
#     # ============================================================
#     if (mode == "BOTH" or mode == "ENH_ONLY") and mp.am_master():
#         if mp.am_master():
#             print("Computing enhancement maps")
#             append_time_to_file(config, prefix="Computing enhancement maps: ")
        
#         enhancement_planes = [
#             "xyplanar",
#             "xyplanarTOP",
#             "xzplanar",
#             "yzplanar",
#         ]

#         # ---------- E FIELD ENHANCEMENT ----------
#         if calc_E:
#             for base_name in enhancement_planes:

#                 enhancement_divided_by_maxes_arr(
#                     [f"{base_name}_ex.h5", f"{base_name}_ey.h5", f"{base_name}_ez.h5"],
#                     [f"{base_name}-empty_ex.h5", f"{base_name}-empty_ey.h5", f"{base_name}-empty_ez.h5"],
#                     save_to=f"enhancement_{base_name}_e2.h5",
#                     path=config.path_to_save,
#                     out_dataset_name="enhancement",
#                 )

#         # ---------- H FIELD ENHANCEMENT ----------
#         if calc_H:
#             for base_name in enhancement_planes:

#                 enhancement_divided_by_maxes_arr(
#                     [f"{base_name}_hx.h5", f"{base_name}_hy.h5", f"{base_name}_hz.h5"],
#                     [f"{base_name}-empty_hx.h5", f"{base_name}-empty_hy.h5", f"{base_name}-empty_hz.h5"],
#                     save_to=f"enhancement_{base_name}_h2.h5",
#                     path=config.path_to_save,
#                     out_dataset_name="enhancement",
#                 )
#     return 0

def compute_harminv(
    harminv_objects,
    save_path=None,
    save_name="harminv_modes.txt",
):
    """
    Process and save Harminv results.

    Creates a dedicated folder 'harminv' and stores:
        - raw data file
        - plots: amplitude, Q, error vs frequency

    Parameters
    ----------
    harminv_objects : list of tuples
        [(point, harminv_instance), ...]

    save_path : str or None
        Output directory.

    save_name : str
        Output filename.
    """

    if not mp.am_master():
        return

    # -----------------------------------------
    # create folder
    # -----------------------------------------
    harminv_dir = os.path.join(save_path, "harminv")
    os.makedirs(harminv_dir, exist_ok=True)

    # -----------------------------------------
    # collect data
    # -----------------------------------------
    all_data = []

    for i, (pt, h) in enumerate(harminv_objects):

        x, y, z = pt.x, pt.y, pt.z

        for m in h.modes:

            freq = m.freq
            Q = m.Q
            amp = np.abs(m.amp)
            err = m.err
            decay = m.decay

            all_data.append([
                i, x, y, z,
                freq, Q, decay, amp, err
            ])

    if len(all_data) == 0:
        print("No Harminv modes found.")
        return

    all_data = np.array(all_data)

    # -----------------------------------------
    # save data
    # -----------------------------------------
    header = (
        "id x y z freq Q decay amplitude error\n"
        "Harminv modal analysis"
    )

    np.savetxt(
        os.path.join(harminv_dir, save_name),
        all_data,
        header=header
    )

    # -----------------------------------------
    # split columns
    # -----------------------------------------
    freq = all_data[:, 4]
    Q = all_data[:, 5]
    decay = all_data[:, 6]
    amp = all_data[:, 7]
    err = all_data[:, 8]

    # -----------------------------------------
    # PLOTS
    # -----------------------------------------

    # --- Amplitude ---
    line_plotter(
        freq,
        amp,
        xlabel="Frequency",
        ylabel="|Amplitude|",
        title="Harminv: Amplitude vs Frequency",
        save_path=harminv_dir,
        save_name="harminv_amplitude.png",
    )

    # --- Q factor ---
    line_plotter(
        freq,
        Q,
        xlabel="Frequency",
        ylabel="Q factor",
        title="Harminv: Q vs Frequency",
        save_path=harminv_dir,
        save_name="harminv_Q.png",
    )

    # --- decay ---
    line_plotter(
        freq,
        decay,
        xlabel="Frequency",
        ylabel="Decay",
        title="Harminv: Decay vs Frequency",
        save_path=harminv_dir,
        save_name="harminv_decay.png",
    )

    # --- Error ---
    line_plotter(
        freq,
        err,
        xlabel="Frequency",
        ylabel="Error",
        title="Harminv: Error vs Frequency",
        save_path=harminv_dir,
        save_name="harminv_error.png",
    )
    return all_data

def run_structure(
    sim,
    structure_name,
    planes,
    config,
    calc_E=True,
    calc_H=False,
    calc_DPWR=False,
    TRL=False,
    TRL_monitors=None,
    scattering=False,
    scattering_monitors=None,
    dft_gap_spectrum=False,
    dft_gap_monitors=None,
    harminv=False,
    harminv_objects=None,
):
    """
    Run simulation and save all raw data to cache.

    Parameters
    ----------
    structure_name : str
        "empty", "substrate", "antenna", ...

    Returns
    -------
    str
        Path to cache directory.
    """
    cache_dir = os.path.join(
        config.path_to_save,
        "cache",
        structure_name,
    )

    os.makedirs(cache_dir, exist_ok=True)

    save_metadata(
        cache_dir=cache_dir,
        config=config,
        structure_name=structure_name,
        TRL_monitors=TRL_monitors,
        scattering_monitors=scattering_monitors,
        dft_gap_monitors=dft_gap_monitors,
    )

    log_system_usage(config.path_to_save, "save_cache_metadata")

    if mp.am_master():
        print(f"Running structure: {structure_name}")
        append_time_to_file(
            config,
            prefix=f"Running structure {structure_name}: ",
        )

    # =====================================================
    # HARMINV CALLBACKS
    # =====================================================
    if harminv and harminv_objects:
        extra_run_functions = [
            mp.after_time(config.harminv_t0, h)
            for _, h in harminv_objects
        ]
    else:
        extra_run_functions = None

    # =====================================================
    # MAIN SIMULATION
    # =====================================================
    log_system_usage(config.path_to_save, "before_collect")

    sim = collect_fields_with_output(
        sim,
        volumes=planes,
        delta_t=config.sim_time_step,
        until=config.sim_time,
        start_time=0,
        path=cache_dir,
        calc_E_fields=calc_E,
        calc_H_fields=calc_H,
        calc_Dpwr=calc_DPWR,
        extra_run_functions=extra_run_functions,
        config=config,
    )

    log_system_usage(config.path_to_save, "after_collect")

    # =====================================================
    # TRL
    # =====================================================
    if TRL and TRL_monitors:
        trl_dir = os.path.join(cache_dir, "TRL")

        for name, monitor in TRL_monitors["monitors"].items():
            save_flux_monitor(
                sim,
                monitor,
                name,
                path=trl_dir,
                subdirectory="TRL",
            )

    # =====================================================
    # SCATTERING
    # =====================================================
    if scattering and scattering_monitors:
        scattering_dir = os.path.join(cache_dir, "SCATTERING")

        for name, monitor in scattering_monitors["monitors"].items():
            save_flux_monitor(
                sim,
                monitor,
                name,
                path=scattering_dir,
                subdirectory="SCATTERING",
            )

    # =====================================================
    # GAP DFT
    # =====================================================
    if dft_gap_spectrum and dft_gap_monitors:
        dft_dir = os.path.join(
            cache_dir,
            "GAP_DFT",
        )

        for name, monitor in dft_gap_monitors["monitors"].items():
            save_gap_dft_monitor(
                sim,
                monitor,
                name,
                config,
                dft_dir,
            )

    # =====================================================
    # HARMINV
    # =====================================================
    if harminv and harminv_objects:
        # harminv_dir = os.path.join( cache_dir, "HARMINV")

        # os.makedirs(harminv_dir, exist_ok=True)

        # save_harminv_raw(
        #     harminv_objects,
        #     harminv_dir,
        # )
        pass

    if mp.am_master():
        print(f"Finished structure: {structure_name}")

    sim.reset_meep()

    return cache_dir

def run_or_load_structure(
    sim,
    cache_dir,
    structure_name,
    planes,
    config,
    calc_E=True,
    calc_H=False,
    calc_DPWR=False,
    TRL_monitors=None,
    scattering_monitors=None,
    dft_gap_spectrum=False,
    dft_gap_monitors=None,
    harminv=False,
    harminv_objects=None,
):
    """
    Load existing cache or run simulation.

    Parameters
    ----------
    sim : mp.Simulation or None

    cache_dir : str or None
        Existing cache directory. If not None, simulation is skipped.

    structure_name : str
        "empty", "substrate", "antenna", ...

    Returns
    -------
    str
        Path to structure cache.
    """
    # =====================================================
    # LOAD CACHE
    # =====================================================
    if cache_dir is not None:
        log_system_usage(
            config.path_to_save,
            f"{structure_name}_load_cache",
        )
        return cache_dir

    # =====================================================
    # NOTHING TO RUN
    # =====================================================
    if sim is None:
        return None

    log_system_usage(
        config.path_to_save,
        f"{structure_name}_start",
    )

    # =====================================================
    # RUN SIMULATION
    # =====================================================
    cache_dir = run_structure(
        sim=sim,
        structure_name=structure_name,
        planes=planes,
        config=config,
        calc_E=calc_E,
        calc_H=calc_H,
        calc_DPWR=calc_DPWR,
        TRL=TRL_monitors is not None,
        TRL_monitors=TRL_monitors,
        scattering=scattering_monitors is not None,
        scattering_monitors=scattering_monitors,
        dft_gap_spectrum=dft_gap_spectrum,
        dft_gap_monitors=dft_gap_monitors,
        harminv=harminv,
        harminv_objects=harminv_objects,
    )

    log_system_usage(
        config.path_to_save,
        f"{structure_name}_after_run_structure",
    )

    return cache_dir

def compute_fields_2(
    sim_empty=None,
    empty_from_cache=None,

    sim_substrate=None,
    substrate_from_cache=None,

    sim_antenna=None,
    antenna_from_cache=None,

    volumes=None,
    config=None,

    calc_E=True,
    calc_H=False,
    calc_DPWR=False,

    TRL=True,
    TRL_X_size=None,
    TRL_Y_size=None,

    scattering=False,
    scattering_object=None,
    scattering_padding_perc=10,
    scattering_extra_padding_nm=(0, 0, 0),

    dft_gap_spectrum=False,
    dft_object=None,

    harminv=False,
    harminv_objects=None,

    calc_enh=True,
):
    """
    Run simulations (or load cache) and perform requested analyses.
    """
    # =====================================================
    # PLANES
    # =====================================================
    planes = {
        "xyplanar": volumes.volume["XY"],
        "xyplanarTOP": volumes.volume["XY_TOP"],
        "xzplanar": volumes.volume["XZ"],
        "yzplanar": volumes.volume["YZ"],
    }

    # =====================================================
    # EMPTY MONITORS
    # =====================================================
    empty_TRL = None
    empty_scattering = None
    empty_gap_dft = None

    if sim_empty is not None:

        if TRL:
            empty_TRL = setup_TRL_monitors(
                sim_empty,
                config,
                TRL_X_size,
                TRL_Y_size,
            )

        if scattering:
            empty_scattering = setup_scattering_monitors(
                sim=sim_empty,
                scattering_object=scattering_object,
                config=config,
                padding_perc=scattering_padding_perc,
                extra_padding_nm=scattering_extra_padding_nm,
            )

        if dft_gap_spectrum:
            empty_gap_dft = setup_gap_dft_monitors(
                sim=sim_empty,
                dft_object=dft_object,
                config=config,
            )

    # =====================================================
    # SUBSTRATE MONITORS
    # =====================================================
    substrate_TRL = None
    substrate_scattering = None
    substrate_gap_dft = None

    if sim_substrate is not None:

        if TRL:
            substrate_TRL = setup_TRL_monitors(
                sim_substrate,
                config,
                TRL_X_size,
                TRL_Y_size,
            )

        if scattering:
            substrate_scattering = setup_scattering_monitors(
                sim=sim_substrate,
                scattering_object=scattering_object,
                config=config,
                padding_perc=scattering_padding_perc,
                extra_padding_nm=scattering_extra_padding_nm,
            )

        if dft_gap_spectrum:
            substrate_gap_dft = setup_gap_dft_monitors(
                sim=sim_substrate,
                dft_object=dft_object,
                config=config,
            )

    # =====================================================
    # ANTENNA MONITORS
    # =====================================================
    antenna_TRL = None
    antenna_scattering = None
    antenna_gap_dft = None

    if sim_antenna is not None:

        if TRL:
            antenna_TRL = setup_TRL_monitors(
                sim_antenna,
                config,
                TRL_X_size,
                TRL_Y_size,
            )

        if scattering:
            antenna_scattering = setup_scattering_monitors(
                sim=sim_antenna,
                scattering_object=scattering_object,
                config=config,
                padding_perc=scattering_padding_perc,
                extra_padding_nm=scattering_extra_padding_nm,
            )

        if dft_gap_spectrum:
            antenna_gap_dft = setup_gap_dft_monitors(
                sim=sim_antenna,
                dft_object=dft_object,
                config=config,
            )

    # =====================================================
    # EMPTY
    # =====================================================
    empty_cache = run_or_load_structure(
        sim=sim_empty,
        cache_dir=empty_from_cache,
        structure_name="empty",
        planes=planes,
        config=config,

        calc_E=calc_E,
        calc_H=calc_H,
        calc_DPWR=calc_DPWR,

        TRL_monitors=empty_TRL,
        scattering_monitors=empty_scattering,

        dft_gap_spectrum=dft_gap_spectrum,
        dft_gap_monitors=empty_gap_dft,

        harminv=False,
    )

    # =====================================================
    # SUBSTRATE
    # =====================================================
    substrate_cache = run_or_load_structure(
        sim=sim_substrate,
        cache_dir=substrate_from_cache,
        structure_name="substrate",
        planes=planes,
        config=config,

        calc_E=calc_E,
        calc_H=calc_H,
        calc_DPWR=calc_DPWR,

        TRL_monitors=substrate_TRL,
        scattering_monitors=substrate_scattering,

        dft_gap_spectrum=dft_gap_spectrum,
        dft_gap_monitors=substrate_gap_dft,

        harminv=harminv,
        harminv_objects=harminv_objects,
    )

    # =====================================================
    # ANTENNA
    # =====================================================
    antenna_cache = run_or_load_structure(
        sim=sim_antenna,
        cache_dir=antenna_from_cache,
        structure_name="antenna",
        planes=planes,
        config=config,

        calc_E=calc_E,
        calc_H=calc_H,
        calc_DPWR=calc_DPWR,

        TRL_monitors=antenna_TRL,
        scattering_monitors=antenna_scattering,

        dft_gap_spectrum=dft_gap_spectrum,
        dft_gap_monitors=antenna_gap_dft,

        harminv=harminv,
        harminv_objects=harminv_objects,
    )

    # =====================================================
    # TRL
    # =====================================================
    if TRL:
        log_system_usage(
            config.path_to_save,
            "TRL_start",
        )

        compute_TRL(
            Nfreq = config.nfreq,
            
            empty_path=os.path.join(empty_cache, "TRL"),
            
            substrate_path=(
                os.path.join(substrate_cache, "TRL")
                if substrate_cache is not None else None
            ),
            
            antenna_path=(
                os.path.join(antenna_cache, "TRL")
                if antenna_cache is not None else None
            ),
            
            save_path=os.path.join(
                config.path_to_save,
                "TRL",
            )
        )

        log_system_usage(
            config.path_to_save,
            "TRL_end",
        )

    # =====================================================
    # SCATTERING
    # =====================================================
    if scattering:
        log_system_usage(
            config.path_to_save,
            "SCATTERING_start",
        )

        compute_scattering(
            Nfreq = config.nfreq,
                        
            empty_path=os.path.join(empty_cache, "SCATTERING"),
            
            substrate_path=(
                os.path.join(substrate_cache, "SCATTERING")
                if substrate_cache is not None else None
            ),
            
            antenna_path=(
                os.path.join(antenna_cache, "SCATTERING")
                if antenna_cache is not None else None
            ),
            
            save_path=os.path.join(
                config.path_to_save,
                "SCATTERING",
            )
        )
        
        log_system_usage(
            config.path_to_save,
            "SCATTERING_end",
        )

    # =====================================================
    # GAP DFT
    # =====================================================
    if dft_gap_spectrum:
        log_system_usage(
            config.path_to_save,
            "DFT_start",
        )

        compute_gap_dft(
            empty_path=os.path.join(empty_cache, "GAP_DFT"),

            substrate_path=(
                os.path.join(substrate_cache, "GAP_DFT")
                if substrate_cache is not None else None
            ),
            
            antenna_path=(
                os.path.join(antenna_cache, "GAP_DFT")
                if antenna_cache is not None else None
            ),
            
            save_path=os.path.join(
                config.path_to_save,
                "GAP_DFT",
            )
        )

        log_system_usage(
            config.path_to_save,
            "DFT_end",
        )

    # =====================================================
    # HARMINV
    # =====================================================
    if harminv:
        log_system_usage(
            config.path_to_save,
            "HARMINV_start",
        )

        # compute_harminv(...)

        log_system_usage(
            config.path_to_save,
            "HARMINV_end",
        )

    # =====================================================
    # ENHANCEMENT
    # =====================================================
    if calc_enh:
        log_system_usage(
            config.path_to_save,
            "ENHANCEMENT_start",
        )
        
        enhancement_dir = os.path.join(
            config.path_to_save,
            "cache",
            "enhancement",
        )
        compute_enhancement_maps(
            empty_path=empty_cache,
            substrate_path=substrate_cache,
            antenna_path=antenna_cache,
            save_path=enhancement_dir,
        )

        
        log_system_usage(
            config.path_to_save,
            "ENHANCEMENT_stop",
        )

    # =====================================================
    return {
        "empty": empty_cache,
        "substrate": substrate_cache,
        "antenna": antenna_cache,
    }
