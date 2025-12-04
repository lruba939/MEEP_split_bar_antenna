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

def task_3(plot=False, eps_data=[], animation=False, animation_name="dupa"):
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
        
    collected_data, time_steps, x_coords = collect_e_line(p, delta_t=0.5, width=5, plot_3d=True)

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
        mp.Ex,
        mp.Ey,
        mp.Ez
    ]
    
    comp_names = ["Ex", "Ey", "Ez"]
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
            task_3(plot=False, animation=True, animation_name=name)

            p.center = [mp.Vector3(0, 0, -10.), # upper bar
                        mp.Vector3(0, 0, -10.)] # lower bar
            name = "without_antennas" + comp_name + size_name
            task_3(plot=False, animation=True, animation_name=name)