from . import params
import meep as mp

# inicialize singleton of all parameters
p = params.SimParams()

# cell is the whole sim box
def make_cell():
    cell = mp.Vector3(p.xyz_cell[0], p.xyz_cell[1], p.xyz_cell[2])
    return cell

# waveguide geometry
def make_medium():
    geometry = [
        mp.Block(
            mp.Vector3(p.x_width, p.y_length, p.z_height),
            center = p.center[0], # upper bar
            material = p.material,
        ),
        
        mp.Block(
            mp.Vector3(p.x_width, p.y_length, p.z_height),
            center = p.center[1], # lower bar
            material = p.material,
        )
    ]
    return geometry