## Singleton of parameters
import os
import numpy as np
import meep as mp
from meep.materials import Au, Cr, W, SiO2, Ag

class SimParams:
    _instance=None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance=object.__new__(cls)
            cls._instance._init_parameters()
        return cls._instance
    
    def _init_parameters(self):
        # SYSTEM
        self.IMG_CLOSE =  True

        # Geometry
        self.material   =   Au
        
        self.x_width    =   0.7
        self.y_length   =   0.19
        self.z_height   =   0.0
        self.gap_size   =   0.05
        self.pad        =   2.0
        
        self.xyz_cell   =   [self.x_width+2*self.pad,
                            2*self.y_length + self.gap_size + 2*self.pad,
                            0]
        self.center     =   [mp.Vector3(0, self.y_length/2.0 + self.gap_size/2.0, 0), # upper bar
                            mp.Vector3(0, (-1)*(self.y_length/2.0 + self.gap_size/2.0), 0)] # lower bar
        # self.center     =   [mp.Vector3(0, 0, -10.), # upper bar
                            # mp.Vector3(0, 0, -10.)] # lower bar
        
        # Source
        self.lambda0    =   1.0 #um
        self.freq       =   1.0 / self.lambda0
        self.freq_width =   self.freq * 0.5
        self.component  =   mp.Ey
        self.xyz_src    =   [1.5, 0.0, 0.0]
        self.src_size   =   [0.0, 2.8, 0.0]
        
        ## Simulation settings
        self.Courant_factor         =   0.5
        self.pml                    =   0.25
        # self.pml                    =   (self.lambda0 + self.lambda0*0.5 ) / 2 #Should be: d_PML = lambda_max / 2
        self.resolution             =   50
        self.sim_time               =   20
        self.animations_step        =   self.Courant_factor * (1 / self.resolution) # From dt = S * dx / c, where c=1 in MEEP units
        self.animations_until       =   10
        self.animations_fps         =   20
        self.path_to_save           =   "results/"
        self.animations_folder_path =   os.path.join(self.path_to_save, "animations")

    def reset_to_defaults(self):
        dir_nam_con = self.path_to_save
        dir_ani_con = self.animations_folder_path
        
        self._init_parameters()
        
        self.path_to_save = dir_nam_con
        self.animations_folder_path = dir_ani_con
        
    def showParams(self):
        print("\n\n#################################\nSimulation and System Parameters:\n")
        for k, v in self.__dict__.items():
            if not k.startswith('_'):
                if not isinstance(v, (list, dict, tuple, np.ndarray)): #
                    print(f"{k}={v}")
                else:
                    print(f"{k}={v[:5]}")
        print("#################################\n\n")

    def saveParams(self, filename="results/simulation_params.txt"):
        """
        Saves simulation/system parameters to a file.

        Args:
            filename (str): Nazwa pliku, do którego zostaną zapisane parametry.
        """
        with open(filename, "w") as f:
            header = "\n\n#################################\nSimulation and System Parameters:\n"
            f.write(header)
            for k, v in self.__dict__.items():
                if not k.startswith('_'):
                    if not isinstance(v, (list, dict, tuple, np.ndarray)):
                        line = f"{k}={v}\n"
                        f.write(line)
                    else:
                        line = f"{k}={str(v[:5])}\n"
                        f.write(line)
            footer = "#################################\n\n"
            f.write(footer)