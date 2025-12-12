import meep as mp
import numpy as np
import os

from visualization.plotter import *
# !!!!!!!!! ---> from main.src.simulation import * # CANT IMPORT DUE TO CIRCULAR DEPENDENCY

def show_data_img(datas_arr, abs_bool, norm_bool, cmap_arr, alphas, name_to_save=None, IMG_CLOSE=False):
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
        if abs_bool[idx]:
            data = np.abs(data) # complex -> real
        if norm_bool[idx]:
            max_data = np.max(data)
            data = data / max_data # complex -> real
        plt.imshow(data.transpose(), interpolation="spline36", cmap=cmap_arr[idx], alpha=alphas[idx])
        plt.xticks([])  # Turn off x-axis numbers
        plt.yticks([])  # Turn off y-axis numbers
        plt.colorbar(shrink=0.6)  # Show color scale
    if name_to_save is not None:
        plt.savefig(f"{name_to_save}.png", dpi=300, bbox_inches="tight", format="png")
    if IMG_CLOSE:
        plt.show(block=False)
        plt.pause(2)
        plt.close("all")
    else:
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
    sim.run(mp.at_every(singleton_params.animations_step*10, animate), until=singleton_params.animations_until)
    animate.to_mp4(filename = os.path.join(singleton_params.animations_folder_path, animation_name), fps = singleton_params.animations_fps)
    plt.show(block=False)
    plt.pause(2)
    plt.close("all")

def collect_e_line(singleton_params, sim, delta_t, width=1, plot_3d=False, name=None):
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
    
    sim.reset_meep()
    sim.run(mp.at_every(delta_t, collect_data), until=singleton_params.animations_until)

    if len(collected_data) == 0:
        return collected_data, time_steps, None

    if plot_3d: 
        save_name = os.path.join(singleton_params.path_to_save, f"3Dplot_profile_{name}.png")
        plot_e_3d(collected_data, x_coords, time_steps, name=save_name, IMG_CLOSE=singleton_params.IMG_CLOSE)

    return collected_data, time_steps, x_coords

def plot_e_3d(collected_data, x_coords, time_steps, name=None, IMG_CLOSE=False):
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
    plt.savefig(name, dpi=300, bbox_inches="tight", format="png")
    if IMG_CLOSE:
        plt.show(block=False)
        plt.pause(2)
        plt.close("all")
    else:
        plt.show()
    
def collect_max_field(singleton_params, sim, delta_t, skip_fraction=0.5, optional_name="NAME"):
    """
    Collects the maximum value of the component field at each spatial point 
    across the simulation duration, skipping the first skip_fraction of time.

    Parameters:
        singleton_params (object): Singleton with component, xyz_cell, animations_until
        sim (object): MEEP simulation object
        skip_fraction (float): Fraction of simulation time to skip (default 0.25 = 25%)
        delta_t (float): Time interval between data collections

    Returns:
        E_max (np.ndarray): 2D array with maximum field magnitude at each point
    """
    collected_data = []
    skip_time = singleton_params.animations_until * skip_fraction

    def collect_data(sim):
        current_time = sim.meep_time()
        
        if current_time >= skip_time:
            E_data = sim.get_array(center=mp.Vector3(), 
                                   size=singleton_params.xyz_cell, 
                                   component=singleton_params.component)
            collected_data.append(np.abs(E_data))

    sim.reset_meep()
    sim.run(mp.at_every(delta_t, collect_data), until=singleton_params.animations_until)

    if len(collected_data) == 0:
        print("Warning: No data collected after skipping initial time!")
        return None

    # Initialize E_maxes as a zero array with the same shape as collected_data[0]
    E_maxes = np.zeros_like(collected_data[0], dtype=float)

    np.savez(
        os.path.join(singleton_params.path_to_save, "anim_collected_data_f{optional_name}.npz"),
        current_data = collected_data
        )
    
    # For each time step, update E_maxes if the current value is greater
    for i in range(len(collected_data)):
        current_data = collected_data[i]
        # print(f"CURRENT DATA: {current_data[100,100]}")
        # print(f"CURRENT MAXES: {E_maxes[100,100]}")
        E_maxes = np.maximum(E_maxes, current_data)
    
    # Zero the frame of width `frame_width` from each edge
    frame_width = 20
    if frame_width > 0:
        # Top and bottom edges
        E_maxes[:frame_width, :] = 0
        E_maxes[-frame_width:, :] = 0
        # Left and right edges
        E_maxes[:, :frame_width] = 0
        E_maxes[:, -frame_width:] = 0

    return E_maxes