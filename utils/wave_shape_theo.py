import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from visualization.plotter import *

xm = 1000

def gaussian_wave_meep(t, f0, fwidth, distance,
                    start_time=0.0, cutoff=3.0, amplitude=1.0):
    w = 1.0 / fwidth
    t0 = start_time + cutoff * w
    t_eff = t - distance
    x = t_eff - t0
    envelope = np.exp(-(x**2) / (2 * w**2))
    carrier = np.cos(-2 * np.pi * f0 * t_eff)
    A = amplitude * fwidth**2

    return A * envelope * carrier
        
def main():
    cutoff = 5
    wavelength = 1700/xm
    f0 = 1 / wavelength

    fw = 0.4

    wstart = 1/(f0 + fw)
    wstop = 1/(f0 - fw)
    
    distance = (420/2.0 - 100*1.05)/xm

    t = np.linspace(0, 40, 2000)

    plt.figure(figsize=(10, 6))

    E_meep = gaussian_wave_meep(t, f0, fw, distance, start_time=0, cutoff=cutoff)
    plt.plot(t, E_meep, "k-", label=f"Meep fwidth={fw}")
    plt.xlabel("Time")
    plt.ylabel("E(t)")
    plt.title(f"Gaussian-modulated wave={wavelength:.3f} um  ({wstart:.3f} um - {wstop:.3f} um)")
    plt.legend()
    plt.grid()
    plt.show()
    return 0

if __name__ == "__main__":
    main()
