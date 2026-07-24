import meep as mp
import os
import sys
import platform

mp.Simulation.eps_averaging = False

xm = 1000
class SimulationConfig:
    """
    Globalne parametry symulacji.
    NIE zawiera geometrii.
    NIE zawiera typów anten.
    """

    def __init__(self):
        # =====================================================
        # SOFTWARE
        # =====================================================
        self.python_version = sys.version
        self.meep_version = mp.__version__
        self.is_single_precision = mp.is_single_precision()
        self.count_processors = mp.count_processors()
        self.omp_threads = os.environ.get("OMP_NUM_THREADS", "not set")
        self.platform = platform.platform()
        self.processor = platform.processor()
        
        # =====================================================
        # SYMULATION
        # =====================================================
        self.resolution = 500
        self.courant = 0.5
        self.sim_time = 15000 / xm  # w jednostkach Meep (µm)
        self.sim_time_step = 100 / xm

        self.symmetries = [
            mp.Mirror(direction=mp.X, phase=-1),
            mp.Mirror(direction=mp.Y, phase=+1)
        ]

        # =====================================================
        # PATHS
        # =====================================================
        self.path_to_save           =   "results/"
        self.empty_reference_path = os.path.join(self.path_to_save, "EMPTY_REFERENCE")

        # =====================================================
        # CELL
        # =====================================================
        self.pml = 100/xm
        self.pad = 100/xm

        self.cell_size = [
            180.0 / xm + 2*self.pad + 2*self.pml,   # x
            100.0 / xm + 2*self.pad + 2*self.pml,   # y
            50.0 / xm + 2*self.pad + 2*self.pml    # z
        ]

        # =====================================================
        # SOURCE
        # =====================================================
        self.src_type = "gaussian"  # "continuous" or "gaussian"
        self.src_is_integrated = True # if source overlaps with PML regions use True
        self.lambda0 = 8100 / xm
        self.frequency_width = 1
        self.src_width = 1000 / xm # ???
        self.src_amp = 1.0
        self.src_cutoff = 5.0 # number of widths used to smoothly turn on/off the source; reduces high-frequency artifacts
        self.component = mp.Ex
        self.src_center = [
            0.0,    # x
            0.0,    # y
            48.0 / xm  # z
        ]
        self.src_size = [
            200.0 / xm,  # x
            100.0 / xm,  # y
            0.0 / xm    # z
        ]

        # =====================================================
        # FLUX MONITORS OPTIONS
        # =====================================================
        self.nfreq = 500
        self.z_reflection = 35.0 / xm
        self.z_transmission = -15.0 / xm
        self.x_flux_monitor = self.cell_size[0]
        self.y_flux_monitor = self.cell_size[1]

        # =====================================================
        # PLOTS AND ANIMATIONS
        # =====================================================
        self.IMG_CLOSE = True
        self.animations_fps = 8


    # --------------------------------------------------------

    @property
    def frequency(self):
        return 1.0 / self.lambda0

    # @property
    # def frequency_width(self):
    #     return 1.0 / self.src_width
