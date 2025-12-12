from . import params
from . import containters
from . import simulation

import meep as mp
from visualization.plotter import *
import numpy as np
import os

from utils.meep_utils import *

# inicialize singleton of all parameters
p = params.SimParams()
con = containters.SimContainers()

# TASK 0 -------------------------------
# Triggering calculations and saving the most general results.

def task_0():
    
    p.showParams()

    if not os.path.exists(p.path_to_save):
        os.makedirs(p.path_to_save)
    if not os.path.exists(p.animations_folder_path):
        os.makedirs(p.animations_folder_path)
    
    p.saveParams(filename=os.path.join(p.path_to_save, "simulation_params.txt"))

    simulation.start_empty_cell_calc() # MUST BE CALLED FIRST
    sim = simulation.make_sim()
    simulation.start_calc(sim)

    np.savez(
        os.path.join(p.path_to_save, "data_general.npz"),
        Ey = con.E_comp_data_container,
        Ey_empty = con.empty_cell_E_comp_data_container,
        eps = con.eps_data_container
        )
    
    return sim

# TASK 1 -------------------------------
# Make medium - a split bar antenna.

def task_1():
    p.showParams()
    sim = simulation.make_sim()
    sim.plot2D()
    plt.savefig(os.path.join(p.path_to_save, "2Dplot.png"), dpi=300, bbox_inches="tight", format="png")
    if p.IMG_CLOSE:
        plt.show(block=False)
        plt.pause(2)
        plt.close("all")
    else:
        plt.show()

    return 0

# TASK 2 -------------------------------
# Plotting the dielectric constant of a system.

def task_2(plot=False, recalculate=False):
    
    p.showParams()

    if recalculate:    
        sim = simulation.make_sim()
        simulation.start_calc(sim)
      
    if plot:
        show_data_img(datas_arr =   [con.eps_data_container],
                      norm_bool =   [True],
                      abs_bool  =   [True],
                      cmap_arr  =   ["binary"],
                      alphas    =   [1.0],
                      IMG_CLOSE =   p.IMG_CLOSE)
    
    return 0

# TASK 3 -------------------------------
# Calculations of the scalar electric field E component and optional plotting and animation.

def task_3(plot=False, animation=False, animation_name="animation",
           plot_3D=False, sim=None,
           recalculate=False):
    p.showParams()
    
    if recalculate:
        sim = simulation.make_sim()
        simulation.start_calc(sim)
    
    if plot:
        show_data_img(datas_arr =   [con.eps_data_container, con.E_comp_data_container],
                      norm_bool =   [True, False],
                      abs_bool  =   [True, False],
                      cmap_arr  =   ["binary", "RdBu"],
                      alphas    =   [1.0, 0.9],
                      name_to_save = os.path.join(p.path_to_save, "E_component_with_antennas"),
                      IMG_CLOSE =   p.IMG_CLOSE)
        
    if plot:
        show_data_img(datas_arr =   [con.empty_cell_E_comp_data_container],
                      norm_bool =   [False],
                      abs_bool  =   [False],
                      cmap_arr  =   ["RdBu"],
                      alphas    =   [0.9],
                      name_to_save = os.path.join(p.path_to_save, "E_component_empty_cell"),
                      IMG_CLOSE =   p.IMG_CLOSE)
        
    if animation:
        make_animation(p, sim, animation_name)
        
    collected_data, time_steps, x_coords = collect_e_line(p, sim, delta_t=p.animations_step, width=5, plot_3d=plot_3D, name=animation_name)
    np.savez(
        os.path.join(p.path_to_save, f"data_E_line_{animation_name}.npz"),
        collected_data=collected_data,
        time_steps=time_steps,
        x_coords=x_coords
        )

    return 0
           
# TASK 4 -------------------------------

def task_4(skip_fraction=0.15, E_plot=False):
    p.reset_to_defaults()
    
    # --- With antennas ---
    sim = simulation.make_sim()
    E_max_with = collect_max_field(p, sim, delta_t=p.animations_step, skip_fraction=skip_fraction, optional_name="with_antennas")
    if E_plot:
        show_data_img(datas_arr =   [E_max_with],
                        norm_bool =   [False],
                        abs_bool  =   [False],
                        cmap_arr  =   ["inferno"],
                        alphas    =   [1.0],
                        name_to_save = os.path.join(p.path_to_save, "Max_E_with_antennas"),
                        IMG_CLOSE =   p.IMG_CLOSE)
    
    # --- Without antennas ---
    p.center = [mp.Vector3(0, 0, -10.), 
                mp.Vector3(0, 0, -10.)]
    sim = simulation.make_sim()
    E_max_without = collect_max_field(p, sim, delta_t=p.animations_step, skip_fraction=skip_fraction, optional_name="without_antennas")
    if E_plot:
        show_data_img(datas_arr =   [E_max_without],
                        norm_bool =   [False],
                        abs_bool  =   [False],
                        cmap_arr  =   ["inferno"],
                        alphas    =   [1.0],
                        name_to_save = os.path.join(p.path_to_save, "Max_E_without_antennas"),
                        IMG_CLOSE =   p.IMG_CLOSE)
    
    # --- Gain ---   
    gain = E_max_with / E_max_without

    # --- Outliers clipping ---
    vmin = np.nanpercentile(gain, 1)
    vmax = np.nanpercentile(gain, 99)
    gain_clipped = np.clip(gain, vmin, vmax)
    show_data_img(datas_arr =   [gain_clipped],
                    norm_bool =   [False],
                    abs_bool  =   [False],
                    cmap_arr  =   ["inferno"],
                    alphas    =   [1.0],
                    name_to_save = os.path.join(p.path_to_save, "Gain_linear_scale"),
                    IMG_CLOSE =   p.IMG_CLOSE)
    
    # --- Gain in dB ---
    gain_db = 20.0 * np.log10(gain + 1e-12)
    gain_db_clipped = np.clip(gain_db, vmin, vmax)
    show_data_img(datas_arr =   [gain_db_clipped],
                    norm_bool =   [False],
                    abs_bool  =   [False],
                    cmap_arr  =   ["inferno"],
                    alphas    =   [1.0],
                    name_to_save = os.path.join(p.path_to_save, "Gain_dB_scale"),
                    IMG_CLOSE =   p.IMG_CLOSE)
    
    np.savez(
        os.path.join(p.path_to_save, "data_enhancement.npz"),
        E_max_with=np.array(E_max_with),
        E_max_without=np.array(E_max_without),
        gain_clipped=gain_clipped,
        gain_db_clipped=gain_db_clipped
        )

    return gain_db_clipped