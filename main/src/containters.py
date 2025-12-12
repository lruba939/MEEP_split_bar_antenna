## Singleton of data containers
import numpy as np

class SimContainers:
    _instance=None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance=object.__new__(cls)
            cls._instance._init_containers()
        return cls._instance
    
    def _init_containers(self):
        # SYSTEM
        self.eps_data_container     =   []
        self.E_comp_data_container  =   []
        self.empty_cell_E_comp_data_container =   []

    def reset_to_defaults(self):
        self._init_containers()
        
    def showContainers(self):
        print("\n\n#################################\nSimulation and System Parameters:\n")
        for k, v in self.__dict__.items():
            if not k.startswith('_'):
                if not isinstance(v, (list, dict, tuple, np.ndarray)): #
                    print(f"{k}={v}")
                else:
                    print(f"{k}={v[:5]}")
        print("#################################\n\n")