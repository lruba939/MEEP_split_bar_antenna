from . import params
import meep as mp
import cmath
import math

# inicialize singleton of all parameters
p = params.SimParams()

def pw_amp(k, x0):
    def _pw_amp(x):
        return cmath.exp(1j * 2 * math.pi * k.dot(x + x0))
    return _pw_amp

def make_source():
    sources = [
        mp.Source(
            src=mp.ContinuousSource(frequency=p.freq, is_integrated=True),
            component=p.component,
            center=mp.Vector3(p.xyz_src[0], p.xyz_src[1], p.xyz_src[2]),
            size = mp.Vector3(p.src_size[0], p.src_size[1], p.src_size[2]),
            amplitude=1.0
        )
    ]
    
    # sources = [mp.EigenModeSource(mp.ContinuousSource(p.freq),
    #                               center=mp.Vector3(p.xyz_src[0], p.xyz_src[1], p.xyz_src[2]),
    #                               size=mp.Vector3(2.0, 2.0, 0.0),
    #                               direction=mp.Z,
    #                               eig_kpoint=mp.Vector3(z=-1),
    #                               eig_band=1,
    #                               eig_parity=mp.EVEN_Y + mp.ODD_Z,
    #                               eig_match_freq=True,
    #                               )]
    
    # k = mp.Vector3(z=1)
    # src_center=mp.Vector3(p.xyz_src[0], p.xyz_src[1], p.xyz_src[2])
       
    # sources = [mp.Source(
    #             mp.GaussianSource(p.freq, fwidth=p.freq_width, is_integrated=True),
    #             component=mp.Ey,
    #             center=src_center,
    #             size=mp.Vector3(4.0, 4.0, 0.0),
    #             amp_func=pw_amp(k, src_center),
    #         )
    #     ]

    
    return sources