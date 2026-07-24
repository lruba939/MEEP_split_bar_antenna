import meep as mp
import cmath
import math

def pw_amp(k, x0):
    def _pw_amp(x):
        return cmath.exp(1j * 2 * math.pi * k.dot(x + x0))
    return _pw_amp

def make_source(config):
    if config.src_type == "continuous":
        return [
            mp.Source(
                src=mp.ContinuousSource(frequency=config.frequency, is_integrated=config.src_is_integrated),
                component=config.component,
                center=mp.Vector3(config.src_center[0], config.src_center[1], config.src_center[2]),
                size = mp.Vector3(config.src_size[0], config.src_size[1], config.src_size[2]),
                amplitude=config.src_amp
            )
        ]

    # k = mp.Vector3(z=1)
    # src_center=mp.Vector3(config.xyz_src[0], config.xyz_src[1], config.xyz_src[2])

    elif config.src_type == "gaussian":
        return [mp.Source(
                mp.GaussianSource(config.frequency, fwidth=config.frequency_width, is_integrated=True),
                component=config.component,
                center=mp.Vector3(config.src_center[0], config.src_center[1], config.src_center[2]),
                size = mp.Vector3(config.src_size[0], config.src_size[1], config.src_size[2]),
                amplitude=config.src_amp
            )
        ]
    else:
        raise ValueError(f"Unknown source type: {config.src_type}")
