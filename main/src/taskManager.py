from . import params
from . import simulation

import meep as mp
import matplotlib.pyplot as plt
import numpy as np

# inicialize singleton of all parameters
p = params.SimParams()

# TASK 1 -------------------------------

def task_1():
    p.xyz_src=[0.0, 0.0, 0.0] # z is set to 0.0 for visualization purposes only !!!
    p.showParams()
    sim = simulation.make_sim()
    sim.plot2D()
    plt.show()

# TASK 2 -------------------------------

    ###########################
    # task 2 not working .... #
    ###########################

def task_2(plot=False):
    
    p.reset_to_defaults()
    
    p.xyz_src = [0.0, 0.0, 5.0]
    
    p.showParams()
    
    sim = simulation.make_sim()
    simulation.start_calc(sim)
    
    eps_data = sim.get_array(
            center=p.center[0],
            size=p.xyz_cell,
            component=mp.Dielectric)
    
    if plot:
        plt.figure()
        plt.imshow(eps_data.transpose(), interpolation="spline36", cmap="binary")
        plt.axis("on")
        plt.show()

    return eps_data

# TASK 3 -------------------------------

def task_3(eps_data, plot=False, animation=False):
    p.showParams()
    
    sim = simulation.make_sim()
    simulation.start_calc(sim)
    
    ez_data = sim.get_array(center=mp.Vector3(), size=p.xyz_cell, component=p.component)

    if plot:
        plt.figure()
        plt.imshow(eps_data.transpose(), interpolation="spline36", cmap="binary")
        plt.imshow(ez_data.transpose(), interpolation="spline36", cmap="RdBu", alpha=0.9)
        plt.axis("off")
        plt.show()
        
    if animation:
        animate = mp.Animate2D(sim, fields=p.component, normalize = True)
        sim.run(mp.at_every(3, animate), until=200)
        animate.to_mp4(filename = "dupa.mp4", fps = 20)

    return ez_data