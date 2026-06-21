import sys, os, meep
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.experiments import *

def run():
    meep.Simulation.eps_averaging = False
    
    # default values
    mode = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    material_name = sys.argv[2] if len(sys.argv) > 2 else "air"

    if mode == 1:
        bowtie_substrate_experiment(material_name)

    elif mode == 2:
        bowtie_substrate_experiment_LT(material_name)

    elif mode == 3:
        bowtie_substrate_experiment_MIR(material_name)

    elif mode == 4:
        bowtie_substrate_ONLY_experiment(material_name)

    elif mode == 5:
        after_hpc_redraw(material_name)

    elif mode == 6:
        bowtie_big_substrate_experiment(material_name)
    
    else:
        print("Invalid mode. Please choose a mode between 1 and 6.")

if __name__ == "__main__":
    run()