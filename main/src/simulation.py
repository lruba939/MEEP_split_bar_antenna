import meep as mp

from . import params
from . import containters
from . import geometry
from . import sources

# inicialize singleton of all parameters
p = params.SimParams()
con = containters.SimContainers()

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
    sim.reset_meep()
    if not isinstance(sim, mp.Simulation):
        raise TypeError(f"Expected sim to be mp.Simulation, got {type(sim)} instead.")
    sim.run(until=p.sim_time)

    eps_data = sim.get_epsilon(frequency=p.freq)
    con.eps_data_container = eps_data

    E_data = sim.get_array(center=mp.Vector3(), size=p.xyz_cell, component=p.component)
    con.E_comp_data_container = E_data

def start_empty_cell_calc():
    p.center = [mp.Vector3(-9999, -9999, -9999), # upper bar
                mp.Vector3(-9999, -9999, -9999)] # lower bar
    
    sim = make_sim()
    
    sim.run(until=p.sim_time)

    E_data = sim.get_array(center=mp.Vector3(), size=p.xyz_cell, component=p.component)
    con.empty_cell_E_comp_data_container = E_data

    p.center = [mp.Vector3(0, p.y_length/2.0 + p.gap_size/2.0, 0), # upper bar
                mp.Vector3(0, (-1)*(p.y_length/2.0 + p.gap_size/2.0), 0)] # lower bar
    sim.reset_meep()

    return 0