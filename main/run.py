import sys, os, meep
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.taskManager import *
from utils.sys_utils import *

def run():
    # #### Task 1
    # print_task(1, "Making medium - a split bar antenna.")
    # task_1()
    
    # #### Task 2
    # print_task(2, "Making medium - a split bar antenna.")
    # eps = task_2(plot=False)

    # #### Task 3
    # print_task(3, "Calculations of the scalar electric field Ey as result of continuous source radiation.")
    # task_3(plot=True, eps_data=eps, animation=True, animation_name="planewave_TEST")
    
    # #### Task 4
    # print_task(4, "Test different source components and sizes.")
    # task_4()
    
    #### Task 5
    print_task(5, "Magnitude of the electric field with and without antennas.")
    task_5(E_plot = True)
    
if __name__ == "__main__":
    run()