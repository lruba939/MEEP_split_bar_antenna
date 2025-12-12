import sys, os, meep
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.taskManager import *
from utils.sys_utils import *

def run():
    
    ### Set paths to save results
    SIM_NAME = "Au_src_c.200_s.040_res.50_wl.1000nm"
    #############################
    
    p.path_to_save = os.path.join("results", SIM_NAME)
    p.animations_folder_path = os.path.join(p.path_to_save, "animations")

    #--- Task 0 ---
    print_task(0, "Triggering calculations and saving the most general results.")
    sim = task_0()

    # #--- Task 1 ---
    # print_task(1, "Making medium - a split bar antenna.")
    # task_1()
    
    # #--- Task 2 ---
    # print_task(2, "Plotting the dielectric constant of a system.")
    # task_2(plot=False)

    # #--- Task 3 ---
    # print_task(3, "Plotting the scalar electric field E component.")
    # task_3(plot=True, animation=True, animation_name="with_antennas", plot_3D=True, sim=sim)

    # #--- Task 3 ---
    # print_task(3, "WITHOUT ANTENNAS; Plotting the scalar electric field E component.")
    # p.center = [mp.Vector3(-9999, -9999, -9999), # upper bar
    #             mp.Vector3(-9999, -9999, -9999)] # lower bar
    # task_3(plot=False, animation=True, animation_name="without_antennas", plot_3D=True, recalculate=True)
    # p.reset_to_defaults()
    
    #--- Task 4 ---
    print_task(4, "Magnitude of the electric field with and without antennas.")
    task_4(E_plot = True)
    
if __name__ == "__main__":
    run()