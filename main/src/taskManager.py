from . import params
from . import simulation

import meep as mp
from visualization.plotter import *
import numpy as np
import os

from utils.meep_utils import *

# inicialize singleton of all parameters
p = params.SimParams()

# TASK 1 -------------------------------

def task_1():
    p.showParams()
    sim = simulation.make_sim()
    sim.plot2D()
    plt.show()

# TASK 2 -------------------------------

def task_2(plot=False):
    
    p.showParams()
    
    sim = simulation.make_sim()
    simulation.start_calc(sim)
    
    eps_data = sim.get_epsilon(frequency=p.freq)
    
    if plot:
        show_data_img(datas_arr =   [eps_data],
                      norm_bool =   [True],
                      cmap_arr  =   ["binary"],
                      alphas    =   [1.0])
        
    return eps_data

# TASK 3 -------------------------------

def task_3(plot=False, eps_data=[], animation=False, animation_name="dupa", plot_3D=False):
    p.showParams()
    
    sim = simulation.make_sim()
    simulation.start_calc(sim)
    
    E_data = sim.get_array(center=mp.Vector3(), size=p.xyz_cell, component=p.component)

    if plot:
        show_data_img(datas_arr =   [eps_data, E_data],
                      norm_bool =   [True, False],
                      cmap_arr  =   ["binary", "RdBu"],
                      alphas    =   [1.0, 0.9])
        
    if animation:
        make_animation(p, sim, animation_name)
        
    collected_data, time_steps, x_coords = collect_e_line(p, sim, delta_t=0.5, width=5, plot_3d=plot_3D)

    return E_data

# TASK 4 -------------------------------

def task_4():
    size_params = [
        [0.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [4.0, 0.0, 0.0],
        [2.0, 2.0, 0.0],
        [4.0, 4.0, 0.0]        
    ]
    
    compontets = [
        mp.Ey,
        mp.Ez
    ]
    
    comp_names = ["Ey", "Ez"]
    size_names = ["000", "200", "400", "220", "440"]
    
    for comp_pos, comp in enumerate(compontets):
        comp_name = comp_names[comp_pos]
        for size_pos, new_size in enumerate(size_params):
            size_name = size_names[size_pos]
            print("SET: ", comp_name, "; ", size_name, "\n")        
            p.reset_to_defaults()
            p.component = comp
            p.src_size = new_size
            
            name = "antennas" + comp_name + size_name
            eps = task_2(plot=False)
            task_3(plot=True, eps_data=eps, animation=False, animation_name=name)

            p.center = [mp.Vector3(0, 0, -10.), # upper bar
                        mp.Vector3(0, 0, -10.)] # lower bar
            name = "without_antennas" + comp_name + size_name
            eps = task_2(plot=False)
            task_3(plot=True, eps_data=eps, animation=False, animation_name=name)
            
# TASK 5 -------------------------------

def task_5(skip_fraction=0.25, E_plot=False, threshold=None):
    size_name = "000"
    print("Size of source: ", size_name, "\n")        
    p.reset_to_defaults()
    
    # --- Z antenami ---
    name = "antennas" + size_name
    eps = task_2(plot=False)
    sim = simulation.make_sim()
    simulation.start_calc(sim)
    E_max_with = collect_max_field(p, sim, skip_fraction=skip_fraction)
    show_data_img(datas_arr =   [E_max_with],
                  norm_bool =   [False],
                  cmap_arr  =   ["inferno"],
                  alphas    =   [1.0])
    
    # --- Bez anten ---
    # p.center = [mp.Vector3(0, 0, -10.), 
    #             mp.Vector3(0, 0, -10.)]
    p.material = mp.materials.SiO2
    name = "without_antennas" + size_name
    eps = task_2(plot=False)
    sim = simulation.make_sim()
    simulation.start_calc(sim)
    E_max_without = collect_max_field(p, sim, skip_fraction=skip_fraction)
    show_data_img(datas_arr =   [E_max_without],
                norm_bool =   [False],
                cmap_arr  =   ["inferno"],
                alphas    =   [1.0])
    
    # # Ustal próg automatycznie jeśli nie podany
    # if threshold is None:
    #     threshold = np.percentile(E_max_without[E_max_without > 0], 10)  # dolny 10 percentyl
    
    # print(f"Próg pola: {threshold}")
    
    # # --- Wzmocnienie ---
    # # Maskuj punkty gdzie OBIE wartości są poniżej progu
    # mask_with = E_max_with < threshold
    # mask_without = E_max_without < threshold
    # mask = mask_with | mask_without  # LUB - zamaskuj jeśli którekolwiek poniżej progu
    
    # gain = np.zeros_like(E_max_with, dtype=float)
    # gain[~mask] = E_max_with[~mask] / E_max_without[~mask]
    # gain[mask] = np.nan
    
    gain = E_max_with / E_max_without

    # Konwersja do dB
    gain_db = 20.0 * np.log10(gain + 1e-12)
    
    # Clipowanie outlierów
    vmin = np.nanpercentile(gain, 1)
    vmax = np.nanpercentile(gain, 99)
    gain_db_clipped = np.clip(gain, vmin, vmax)
    
    show_data_img(datas_arr =   [gain_db_clipped],
                  norm_bool =   [False],
                  cmap_arr  =   ["inferno"],
                  alphas    =   [1.0])
    
    return gain_db_clipped