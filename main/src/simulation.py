from . import params
import meep as mp

from . import geometry
from . import sources

# inicialize singleton of all parameters
p = params.SimParams()

def make_sim():
    sim = mp.Simulation(
        cell_size = geometry.make_cell(),
        boundary_layers = [mp.PML(p.pml)],
        geometry = geometry.make_medium(),
        sources = sources.make_source(),
        resolution = p.resolution,
        k_point = mp.Vector3()
    )
    return sim

def start_calc(sim):
    if not isinstance(sim, mp.Simulation):
        raise TypeError(f"Expected sim to be mp.Simulation, got {type(sim)} instead.")
    sim.run(until=p.sim_time)
