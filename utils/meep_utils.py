import meep as mp
import numpy as np
import os

from visualization.plotter import *
from main.src.simulation import *

# inicialize singleton of all parameters

def show_data_img(datas_arr, norm_bool, cmap_arr, alphas):
    """
    Displays a series of images from a given array of data.

    Parameters:
    datas_arr (list of np.ndarray): A list of 2D arrays containing the data to be visualized.
    norm_bool (list of bool): A list of boolean values indicating whether to normalize each corresponding data array.
    cmap_arr (list of str): A list of colormap names to be used for each corresponding data array.
    alphas (list of float): A list of alpha values for transparency for each corresponding data array.

    The function iterates through the provided data arrays, normalizes them if specified, 
    and displays each image using matplotlib's imshow function with the specified colormap 
    and transparency settings. The x and y axis ticks are turned off for a cleaner visualization.
    """
    for idx, data in enumerate(datas_arr):
        if norm_bool[idx]:
            data = np.abs(data) # complex -> real
        plt.imshow(data.transpose(), interpolation="spline36", cmap=cmap_arr[idx], alpha=alphas[idx])
        plt.xticks([])  # Turn off x-axis numbers
        plt.yticks([])  # Turn off y-axis numbers
    plt.show()
    
def make_animation(singleton_params, sim, animation_name):
    """
    Generates an animation of the simulation fields and saves it as an MP4 file.

    Parameters:
        singleton_params (object): An object containing parameters for the animation, 
                                    including component, animations_step, animations_until, 
                                    animations_folder_path, and animations_fps.
        sim (object): The simulation object that is being animated.
        animation_name (str): The name of the animation file (without extension).

    Returns:
        None: This function does not return a value. It saves the animation to the specified path.
    """
    animation_name = animation_name + ".mp4"
    sim.reset_meep()
    animate = mp.Animate2D(sim, fields=singleton_params.component, normalize = True)
    sim.run(mp.at_every(singleton_params.animations_step, animate), until=singleton_params.animations_until)
    animate.to_mp4(filename = os.path.join(singleton_params.animations_folder_path, animation_name), fps = singleton_params.animations_fps)

def collect_e_line(singleton_params, delta_t=1.0, width=1, plot_3d=False):
    """
    Collect E component along center line (x_0:x_end, 0, 0) at intervals of delta_t.
    The returned ey_line is the mean across a vertical "width":
      - width=1 -> only the center row
      - width=2 -> center row plus rows at +/-1 (3 rows total)
      - width=N -> rows at offsets - (N-1) .. + (N-1)
    Args:
        delta_t: Time interval between data collections
        width: integer >=1 controlling how many rows (orders) to include
        plot_3d: Whether to plot the collected data in 3D
    Returns:
        collected_data: List (time) of 1D arrays (x) with mean Ey
        time_steps: List of time values
        x_coords: Array of x coordinates along the line
    """
    sim = make_sim()
    start_calc(sim)

    collected_data = []
    time_steps = []
    x_coords = None

    def collect_data(sim):
        nonlocal x_coords
        E_data = sim.get_array(center=mp.Vector3(), size=singleton_params.xyz_cell, component=singleton_params.component)
        # E_data shape: (nx, ny)  (may be 2D)
        nx = E_data.shape[0]
        ny = E_data.shape[1]
        center_j = ny // 2

        # compute offsets: for width=1 -> [0], width=2 -> [-1,0,1], etc.
        max_order = max(0, width - 1)
        offsets = [o for o in range(-max_order, max_order + 1)
                   if 0 <= center_j + o < ny]

        # select the rows and average across them (axis=1 -> per-x mean)
        rows = E_data[:, [center_j + o for o in offsets]]
        if rows.ndim == 1:
            e_line = rows.copy()
        else:
            e_line = np.mean(rows, axis=1)

        collected_data.append(e_line)
        time_steps.append(sim.meep_time())

        if x_coords is None:
            # use actual simulation cell x-extent
            x_extent = singleton_params.xyz_cell[0]
            x_coords = np.linspace(-x_extent/2, x_extent/2, e_line.shape[0])

    sim.run(mp.at_every(delta_t, collect_data), until=singleton_params.animations_until)

    if len(collected_data) == 0:
        return collected_data, time_steps, None

    if plot_3d:
        plot_e_3d(collected_data, x_coords, time_steps)

    return collected_data, time_steps, x_coords

def plot_e_3d(collected_data, x_coords, time_steps):
    """
    Plot E component in 3D: x axis, time axis, z axis (E magnitude)
    
    Args:
        collected_data: List of E field arrays at each time step
        x_coords: Array of x coordinates
        time_steps: List of time values
    """   
    # Create meshgrid for 3D plot
    X, T = np.meshgrid(x_coords, time_steps)
    Z = np.abs(np.array(collected_data))
    
    fig = plt.figure(figsize=(14, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot surface
    surf = ax.plot_surface(X, T, Z, cmap='viridis', alpha=0.9, edgecolor='none')
    
    ax.set_xlabel('x coordinate')
    ax.set_ylabel('time')
    ax.set_zlabel('|Ey|')
    ax.set_title('Ey Component vs Time')
    
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
    
    # Adjust viewpoint: elev controls vertical angle, azim controls horizontal angle
    ax.view_init(elev=20, azim=45)
    
    
    plt.show()