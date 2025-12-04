import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.cm import get_cmap
import numpy as np

from mpl_toolkits.mplot3d import Axes3D

# Global settings for plotting

## Font
rcParams['font.family'] = 'Times New Roman'
rcParams['font.size'] = 14

## Lines
rcParams['lines.solid_joinstyle'] = 'miter'  # other options: 'round' or 'bevel'
rcParams['lines.antialiased'] = True  # turning on/off of antialiasing for sharper edges
rcParams['lines.linewidth'] = 1.25

## Legend
rcParams['legend.loc'] = 'upper left'
rcParams['legend.frameon'] = False

## Ticks
rcParams['xtick.direction'] = 'in'
rcParams['ytick.direction'] = 'in'
rcParams['xtick.top'] = True
rcParams['ytick.right'] = True

rcParams['xtick.minor.visible'] = True
rcParams['ytick.minor.visible'] = True

## Resolution
rcParams['figure.dpi'] = 150

## Global color
rcParams['image.cmap'] = "viridis"

## Colors
### cmaps
cm_inferno = get_cmap("inferno")
cm_viridis = get_cmap("viridis")
cm_seismic = get_cmap("seismic")
cm_jet = get_cmap("jet")
cm_tab10 = get_cmap("tab10")
### Palettes from color-hex.com/
c_google = ['#008744', '#0057e7', '#d62d20', '#ffa700'] # G, B, R, Y # https://www.color-hex.com/color-palette/1872
c_twilight = ['#363b74', '#673888', '#ef4f91', '#c79dd7', '#4d1b7b'] # https://www.color-hex.com/color-palette/809


# Get array of colors from cmap
def cm2c(cmap, c_numb, step=6):
    """
    Convert a colormap to a list of discrete colors.
    This function samples colors from a given colormap at regular intervals
    and returns them as a list of color values.
    Args:
        cmap: A matplotlib colormap object to sample colors from.
        c_numb (int): The number of colors to generate from the colormap.
        step (int, optional): The step size for sampling the colormap. 
            If c_numb is greater than step, step is adjusted to c_numb.
            Defaults to 6.
    Returns:
        list: A list of color tuples sampled from the colormap at regular intervals.
    """
    if c_numb > step:
        step = c_numb
    
    colors_arr = []
    for i in range(c_numb):
        colors_arr.append(cmap(i / step))
    
    return colors_arr

def map_plotter(data, ax=None, cm=cm_inferno, xlabel=r"x [nm]", ylabel=r"y [nm]", 
                xborder=None, yborder=None, ticks_step=2, vmin=None, vmax=None, 
                equal_aspect=True, title=None, show_colorbar=True):
    """
    Plot a 2D data map with customizable axes, colormap, and formatting options.
    Parameters
    ----------
    data : array-like
        2D array of data to be plotted.
    ax : matplotlib.axes.Axes, optional
        Axes object to plot on. If None, a new figure and axes are created.
        Default is None.
    cm : matplotlib.colors.Colormap, optional
        Colormap to use for the plot. Default is cm_inferno.
    xlabel : str, optional
        Label for the x-axis. Default is r"x [nm]".
    ylabel : str, optional
        Label for the y-axis. Default is r"y [nm]".
    xborder : float, optional
        Half-width of the x-axis limits (symmetric around origin).
        Must be provided together with yborder. Default is None.
    yborder : float, optional
        Half-width of the y-axis limits (symmetric around origin).
        Must be provided together with xborder. Default is None.
    ticks_step : int, optional
        Step size for tick placement. Automatically adjusted if it doesn't
        divide evenly into borders. Default is 2.
    vmin : float, optional
        Minimum value for colormap normalization. Default is None.
    vmax : float, optional
        Maximum value for colormap normalization. Default is None.
    equal_aspect : bool, optional
        If True, set equal aspect ratio for the plot. Default is True.
    title : str, optional
        Title for the plot. Default is None.
    show_colorbar : bool, optional
        If True, display a colorbar. Default is True.
    Returns
    -------
    matplotlib.axes.Axes
        The axes object containing the plotted data.
    Raises
    ------
    ValueError
        If only one of xborder or yborder is provided (both must be given together).
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 3.2))
    
    if equal_aspect:
        ax.set_aspect('equal')

    extent = None
    if xborder is not None and yborder is not None:
        ax.set_xlim(-xborder, xborder)
        ax.set_ylim(-yborder, yborder)

        while (xborder % ticks_step != 0 and yborder % ticks_step != 0):
            ticks_step += 1
            if ticks_step > 5:
                ticks_step = 1
                break

        ax.set_xticks(np.linspace(-xborder, xborder, round(ticks_step * 2) + 1))
        ax.set_yticks(np.linspace(-yborder, yborder, round(ticks_step * 2) + 1))

        extent = [-xborder, xborder, -yborder, yborder]
    elif xborder is not None or yborder is not None:
        print("\n\nPlotting error!\nBoth 'xborder' and 'yborder' must be provided.\n")

    im = ax.imshow(data, interpolation='none', origin='lower', extent=extent, cmap=cm, vmin=vmin, vmax=vmax)
    ax.tick_params(direction="out", which="both")

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if title is not None:
        ax.set_title(title)

    if show_colorbar:
        plt.colorbar(im, ax=ax, orientation='vertical')

    return ax

def map_grid_plotter(data_list, n, m, **kwargs):
    """
    Displays a grid of map plots from a list of data arrays.
    This function creates a subplot grid of size n x m and plots each data array
    from data_list using the map_plotter function. If there are fewer data arrays
    than subplots, the empty subplots are hidden. The colorbar is disabled for
    individual plots to save space in the grid layout.
    Parameters
    ----------
    data_list : list
        List of data arrays to be plotted. Each element will be plotted in a
        separate subplot using map_plotter.
    n : int
        Number of rows in the subplot grid.
    m : int
        Number of columns in the subplot grid.
    **kwargs : dict
        Additional keyword arguments to pass to map_plotter function.
    Returns
    -------
    None
        Displays the figure using plt.show().
    Notes
    -----
    - If len(data_list) < n*m, empty subplots will have their axes turned off.
    - Colorbars are disabled for individual subplots to maintain clean layout.
    - The figure is automatically adjusted using tight_layout.
    Examples
    --------
    >>> data1 = np.random.rand(10, 10)
    >>> data2 = np.random.rand(10, 10)
    >>> map_grid_plotter([data1, data2], n=1, m=2)
    """
    fig, axes = plt.subplots(n, m, figsize=(4*m, 4*n))
    
    axes = np.atleast_2d(axes).reshape(-1)

    for i, data in enumerate(data_list):
        if i >= len(axes):
            break
        map_plotter(data, ax=axes[i], show_colorbar=False, **kwargs)

    for j in range(len(data_list), len(axes)): # empty subplots if no data
        axes[j].axis("off")

    plt.tight_layout()
    plt.show()
    
def line_plotter(xdata, ydata, ax=None, xlabel=r"x [-]", ylabel=r"y [-]", color="black",
                    linestyle="-", xlim=None, ylim=None, equal_aspect=False, title=None, label=None):
    """
    Plot a line graph with customizable axes, limits, and styling.
    Parameters
    ----------
    xdata : array-like
        X-axis data points.
    ydata : array-like
        Y-axis data points.
    ax : matplotlib.axes.Axes, optional
        Matplotlib axes object. If None, a new figure and axes are created.
        Default is None.
    xlabel : str, optional
        Label for the x-axis. Default is "x [-]".
    ylabel : str, optional
        Label for the y-axis. Default is "y [-]".
    color : str, optional
        Line color. Default is "black".
    linestyle : str, optional
        Line style (e.g., "-", "--", "-.", ":"). Default is "-".
    xlim : tuple, list, or array-like, optional
        X-axis limits as [min, max]. If None, limits are set to data range.
        Default is None.
    ylim : tuple, list, or array-like, optional
        Y-axis limits as [min, max]. If None, axis auto-scales.
        Default is None.
    equal_aspect : bool, optional
        If True, sets equal aspect ratio for the plot. Default is False.
    title : str, optional
        Title for the plot. If None, no title is set. Default is None.
    label : str, optional
        Label for the line (used in legend). Default is None.
    Returns
    -------
    matplotlib.axes.Axes
        The axes object containing the plot.
    Raises
    ------
    ValueError
        If xlim or ylim are not in the correct format (list, dict, tuple, or numpy array).
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 3.2))
    
    if equal_aspect:
        ax.set_aspect('equal')

    if xlim is not None:
        if isinstance(xlim, (list, dict, tuple, np.ndarray)):
            ax.set_xlim(xlim[0], xlim[1])
        else:
            print("\n\nWrong format of 'xlim'!\n")
    else:
        ax.set_xlim(min(xdata), max(xdata))

    if ylim is not None:
        if isinstance(ylim, (list, dict, tuple, np.ndarray)):
            ax.set_ylim(ylim[0], ylim[1])
        else:
            print("\n\nWrong format of 'ylim'!\n")

    ax.plot(xdata, ydata, color=color, linestyle=linestyle, label=label)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if title is not None:
        ax.set_title(title)

    return ax

def multi_line_plotter_same_axes(xdata_list, ydata_list, colors=None, linestyles=None, labels=None, 
                                  xlabel=r"x [-]", ylabel=r"y [-]",
                                  xlim=None, ylim=None, equal_aspect=False, title=None,
                                  legend=True):
    """
    Plot multiple lines on the same axes with customizable styling.
    This function creates a single matplotlib figure with multiple line plots overlaid
    on the same axes. It supports customization of colors, line styles, labels, axis
    limits, and other plot properties.
    Parameters
    ----------
    xdata_list : list of array-like
        List of x-axis data arrays for each curve.
    xdata_list : list of array-like
        List of y-axis data arrays for each curve. Must have the same length as xdata_list.
    colors : list of str, optional
        List of color specifications for each line. If None, defaults to "black".
    linestyles : list of str, optional
        List of line style specifications for each line (e.g., "-", "--", "-.").
        If None, defaults to "-" (solid line).
    labels : list of str, optional
        List of labels for each line to be displayed in the legend. If None, no labels
        are shown.
    xlabel : str, optional
        Label for the x-axis. Default is "x [-]".
    ylabel : str, optional
        Label for the y-axis. Default is "y [-]".
    xlim : tuple of float, optional
        Limits for the x-axis as (min, max). If None, limits are determined automatically.
    ylim : tuple of float, optional
        Limits for the y-axis as (min, max). If None, limits are determined automatically.
    equal_aspect : bool, optional
        If True, sets equal aspect ratio for x and y axes. Default is False.
    title : str, optional
        Title for the plot. If None, no title is displayed. Default is None.
    legend : bool, optional
        If True and labels are provided, display a legend. Default is True.
    Returns
    -------
    None
        Displays the plot using plt.show().
    """    
    fig, ax = plt.subplots(figsize=(6, 4))
    
    num_curves = len(xdata_list)
    
    for i in range(num_curves):
        color = colors[i] if colors is not None and i < len(colors) else "black"
        linestyle = linestyles[i] if linestyles is not None and i < len(linestyles) else "-"
        label = labels[i] if labels is not None and i < len(labels) else None

        line_plotter(xdata_list[i], ydata_list[i], ax=ax,
                       xlabel=xlabel, ylabel=ylabel,
                       color=color, linestyle=linestyle,
                       xlim=xlim, ylim=ylim,
                       equal_aspect=equal_aspect, title=title)
        
        # Dodaj label tylko, jeśli jest
        if label is not None:
            ax.plot(xdata_list[i], ydata_list[i], label=label, color=color, linestyle=linestyle)

    if legend and labels is not None:
        ax.legend()

    plt.tight_layout()
    plt.show()