import meep as mp
import numpy as np
import os

from utils.sys_utils import *

def enhancement_divided_by_maxes_arr(
    h5_target,
    h5_reference,
    load_path_target,
    load_path_reference,
    save_path,
    save_to=None,
    dataset_target=None,
    dataset_reference=None,
    z_index=None,
    xzeros=0,
    yzeros=None,
    eps=1e-12,
    out_dataset_name="enhancement",
):
    """
    Compute time-dependent enhancement normalized by the time-maximum
    of a reference field.

    MATHEMATICAL DEFINITION
    -----------------------
    For each spatial point (x, y) and time t:

        enhancement[x, y, t] = A[x, y, t] / max_t(B[x, y, t])

    where:
        A[x,y,t] = sum_i (A_i[x,y,t]^2)
        B[x,y,t] = sum_i (B_i[x,y,t]^2)

    The summation index i runs over the provided field components
    (e.g. Ex, Ey, Ez). Any subset of components is allowed, but
    h5_target and h5_reference MUST have identical structure.

    FIXED DATA ASSUMPTIONS
    ---------------------
    * All datasets are stored as:
          data[x, y, time]
    * No axis reordering or transposition is performed.
    * Any Z slicing is applied BEFORE computations.

    PARAMETERS
    ----------
    h5_target : str or list[str]
        HDF5 filename(s) of the target field components.
        Can be:
            - single string (one field component)
            - list/tuple of strings (multiple components)

    h5_reference : str or list[str]
        HDF5 filename(s) of the reference field components.
        MUST mirror the structure of h5_target exactly
        (same type and same list length).

    dataset_target : str or None, optional
        Dataset name inside the target HDF5 files.
        If None, the first dataset in each file is used.

    dataset_reference : str or None, optional
        Dataset name inside the reference HDF5 files.
        If None, the first dataset in each file is used.

    z_index : int or None, optional
        Index of the Z slice to extract if the dataset has shape:
            data[x, y, z, time]
        If such a Z axis exists and z_index is None, an error is raised.

    xzeros : int, optional
        Number of grid points to overwrite at left/right boundaries
        of the reference field (PML cleanup).

    yzeros : int or None, optional
        Number of grid points to overwrite at bottom/top boundaries.
        If None, defaults to xzeros.

    eps : float, optional
        Small regularization constant added to the denominator to
        avoid division by zero.

    load_path_* : str or None, optional
        Directory in which all input HDF5 files are searched.

    cave_path : str or None, optional
        Directory in which the output file is written.

    save_to : str or None, optional
        Name of the output HDF5 file (written inside `path`).
        If None, no file is saved.

    out_dataset_name : str, optional
        Dataset name under which the enhancement array is stored
        in the output HDF5 file.

    RETURNS
    -------
    enhancement : np.ndarray
        Array of shape (x, y, time) containing the enhancement field.

    B_max : np.ndarray
        Array of shape (x, y) containing max_t(B[x,y,t]).
    """
    if not mp.am_master():
            return
    
    # ---------------------------
    # Helpers
    # ---------------------------
    def _open_all(h5_input, dataset_name, load_path):
        if isinstance(h5_input, (list, tuple)):
            files = []
            dsets = []
            for h5f in h5_input:
                filename = (os.path.join(load_path, h5f) if load_path is not None else h5f)
                f = h5py.File(filename, "r")
                name = dataset_name or next(iter(f.keys()))
                files.append(f)
                dsets.append(f[name])
            return files, dsets

        filename = (
            os.path.join(load_path, h5_input)
            if load_path is not None else h5_input
        )

        f = h5py.File(filename, "r")
        name = dataset_name or next(iter(f.keys()))

        return [f], [f[name]]
    
    def _get_frame_sum_sq(dsets, t):
        acc = None
        for d in dsets:
            if d.ndim == 4:
                if z_index is None:
                    raise ValueError("Z axis detected but z_index not provided")
                frame = d[:, :, z_index, t]
            else:
                frame = d[:, :, t]

            if acc is None:
                acc = np.square(frame)
            else:
                acc += np.square(frame)
        return acc

    # ---------------------------
    # Open files
    # ---------------------------
    fA, dA = _open_all(h5_target, dataset_target, load_path_target)
    fB, dB = _open_all(h5_reference, dataset_reference, load_path_reference)

    # ---------------------------
    # Shape
    # ---------------------------
    for da, db in zip(dA, dB):
        if da.shape != db.shape:
            raise RuntimeError(
                "Enhancement ERROR: target and reference datasets have different shapes.\n"
                f"Target: {da.shape}, Reference: {db.shape}"
            )

    sample = dA[0]
    if sample.ndim == 4:
        Nx, Ny, Nz, Nt = sample.shape
    else:
        Nx, Ny, Nt = sample.shape

    if yzeros is None:
        yzeros = xzeros

    xzeros = max(0, min(xzeros, Nx // 2))
    yzeros = max(0, min(yzeros, Ny // 2))

    # ---------------------------
    # PASS 1: compute B_max
    # ---------------------------
    B_max = np.zeros((Nx, Ny), dtype=float)

    for t in range(Nt):
        B_frame = _get_frame_sum_sq(dB, t)

        # PML cleanup (on-the-fly)
        if xzeros > 0 or yzeros > 0:
            B_frame[:xzeros, :] = 1.0
            B_frame[-xzeros:, :] = 1.0
            B_frame[:, :yzeros] = 1.0
            B_frame[:, -yzeros:] = 1.0

        np.maximum(B_max, B_frame, out=B_max)

    # ---------------------------
    # PASS 2: compute enhancement
    # ---------------------------
    enhancement = np.empty((Nx, Ny, Nt), dtype=float)

    denom = B_max + eps

    for t in range(Nt):
        A_frame = _get_frame_sum_sq(dA, t)
        enhancement[:, :, t] = A_frame / denom

    # ---------------------------
    # Save
    # ---------------------------
    if save_to is not None:
        save_file = os.path.join(save_path, save_to) if save_path else save_to
        if save_path is not None:
            os.makedirs(save_path, exist_ok=True)
        with h5py.File(save_file, "w") as f:
            f.create_dataset(out_dataset_name, data=enhancement)
            f.create_dataset("reference_max", data=B_max)

    # ---------------------------
    # Cleanup
    # ---------------------------
    for f in fA + fB:
        f.close()
    gc.collect()
    
    return enhancement, B_max

def compute_enhancement_maps(
    empty_path,
    substrate_path=None,
    antenna_path=None,
    save_path=None,
    calc_E=True,
    calc_H=False,
):
    """
    Compute enhancement maps from cached field recordings.

    Parameters
    ----------
    empty_path : str
        Cache directory containing empty simulation fields.

    substrate_path : str or None
        Cache directory containing substrate simulation fields.

    antenna_path : str or None
        Cache directory containing antenna simulation fields.

    save_path : str
        Directory where enhancement maps will be stored.

    calc_E : bool

    calc_H : bool
    """

    if not mp.am_master():
        return

    os.makedirs(save_path, exist_ok=True)

    planes = (
        "xyplanar",
        "xyplanarTOP",
        "xzplanar",
        "yzplanar",
    )

    field_sets = []

    if calc_E:
        field_sets.append((("ex", "ey", "ez"),"e2"))

    if calc_H:
        field_sets.append((("hx", "hy", "hz"),"h2"))

    for components, suffix in field_sets:
        for plane in planes:
            # =====================================================
            # substrate / empty
            # =====================================================
            if substrate_path is not None:
                enhancement_divided_by_maxes_arr(
                    h5_target=[
                        f"{plane}_{c}.h5"
                        for c in components
                    ],
                    h5_reference=[
                        f"{plane}_{c}.h5"
                        for c in components
                    ],
                    load_path_target=substrate_path,
                    load_path_reference=empty_path,
                    save_path=os.path.join(save_path, "substrate_over_empty"),
                    save_to=f"enhancement_{plane}_{suffix}.h5",
                )

            # =====================================================
            # antenna / empty
            # =====================================================
            if antenna_path is not None:
                enhancement_divided_by_maxes_arr(
                    h5_target=[
                        f"{plane}_{c}.h5"
                        for c in components
                    ],
                    h5_reference=[
                        f"{plane}_{c}.h5"
                        for c in components
                    ],
                    load_path_target=antenna_path,
                    load_path_reference=empty_path,
                    save_path=os.path.join(save_path, "antenna_over_empty"),
                    save_to=f"enhancement_{plane}_{suffix}.h5",
                )

            # =====================================================
            # antenna / substrate
            # =====================================================
            if (antenna_path is not None and substrate_path is not None):
                enhancement_divided_by_maxes_arr(
                    h5_target=[
                        f"{plane}_{c}.h5"
                        for c in components
                    ],
                    h5_reference=[
                        f"{plane}_{c}.h5"
                        for c in components
                    ],
                    load_path_target=antenna_path,
                    load_path_reference=substrate_path,
                    save_path=os.path.join(save_path, "antenna_over_substrate"),
                    save_to=f"enhancement_{plane}_{suffix}.h5",
                )

def get_phys_ranges(bounds, plane):
    if plane == "XY":
        return [bounds["xmin"], bounds["xmax"]], [bounds["ymin"], bounds["ymax"]]

    elif plane == "XZ":
        return [bounds["xmin"], bounds["xmax"]], [bounds["zmin"], bounds["zmax"]]

    elif plane == "YZ":
        return [bounds["ymin"], bounds["ymax"]], [bounds["zmin"], bounds["zmax"]]

    else:
        raise ValueError(f"Unknown plane: {plane}")

def animate_enhancement_fields(
    enhancement_path,
    enhancement_name,
    config,
    volumes,
    draw_params,
    field="E",
    animate=True,
):
    """
    Animate and analyze enhancement maps stored in a selected enhancement folder.

    Parameters
    ----------
    enhancement_path : str
        Path to a specific enhancement directory, e.g.
        cache/enhancement/antenna_over_empty

    enhancement_name : str
        Name used as prefix for saved animations and plots.
        Example:
            antenna_over_empty
            antenna_over_substrate
            substrate_over_empty
    """
    if not mp.am_master():
        return 0

    animation_path = os.path.join(
        config.path_to_save,
        "ENHANCEMENT",
        "animations",
    )
    map_path = os.path.join(
        config.path_to_save,
        "ENHANCEMENT",
        "maps",
    )
    os.makedirs(animation_path, exist_ok=True)
    os.makedirs(map_path, exist_ok=True)

    valid_field = ["E", "H"]

    if field not in valid_field:
        raise ValueError(f"field must be one of {valid_field}")

    field = field.lower()

    # ============================================================
    # Bounds of planes configuration
    # ============================================================
    b_xy = volumes.bounds["XY"]
    b_xy_top = volumes.bounds["XY_TOP"]
    b_xz = volumes.bounds["XZ"]
    b_yz = volumes.bounds["YZ"]

    xy_x, xy_y = get_phys_ranges(b_xy, "XY")
    xy_top_x, xy_top_y = get_phys_ranges(b_xy_top, "XY")
    xz_x, xz_y = get_phys_ranges(b_xz, "XZ")
    yz_x, yz_y = get_phys_ranges(b_yz, "YZ")

    xy_x = [v * 1e3 for v in xy_x]
    xy_y = [v * 1e3 for v in xy_y]

    xy_top_x = [v * 1e3 for v in xy_top_x]
    xy_top_y = [v * 1e3 for v in xy_top_y]

    xz_x = [v * 1e3 for v in xz_x]
    xz_y = [v * 1e3 for v in xz_y]

    yz_x = [v * 1e3 for v in yz_x]
    yz_y = [v * 1e3 for v in yz_y]

    # ============================================================
    # Plane configuration
    # ============================================================
    planes = {
        "XY": {
            "filename": f"enhancement_xyplanar_{field}2.h5",
            "save_anim": f"{enhancement_name}_enh_xy_{field}2.mp4",
            "save_map": f"{enhancement_name}_MAP_XY.png",
            "x_phys_range": xy_x,
            "y_phys_range": xy_y,
            "x_zoom": draw_params["XY"]["x_zoom"],
            "y_zoom": draw_params["XY"]["y_zoom"],
            "xlabel": "X [nm]",
            "ylabel": "Y [nm]",
            "roi": {
                "type": "rectangle",
                "center": draw_params["XY"]["roi"]["center"],
                "width": draw_params["XY"]["roi"]["width"],
                "height": draw_params["XY"]["roi"]["height"],
            },
        },

        "XYTop": {
            "filename": f"enhancement_xyplanarTOP_{field}2.h5",
            "save_anim": f"{enhancement_name}_enh_xy_TOP_{field}2.mp4",
            "save_map": f"{enhancement_name}_MAP_XY_TOP.png",
            "x_phys_range": xy_top_x,
            "y_phys_range": xy_top_y,
            "x_zoom": draw_params["XY"]["x_zoom"],
            "y_zoom": draw_params["XY"]["y_zoom"],
            "xlabel": "X [nm]",
            "ylabel": "Y [nm]",
            "roi": {
                "type": "rectangle",
                "center": draw_params["XY"]["roi"]["center"],
                "width": draw_params["XY"]["roi"]["width"],
                "height": draw_params["XY"]["roi"]["height"],
            },
        },

        "XZ": {
            "filename": f"enhancement_xzplanar_{field}2.h5",
            "save_anim": f"{enhancement_name}_enh_xz_{field}2.mp4",
            "save_map": f"{enhancement_name}_MAP_XZ.png",
            "x_phys_range": xz_x,
            "y_phys_range": xz_y,
            "x_zoom": draw_params["XZ"]["x_zoom"],
            "y_zoom": draw_params["XZ"]["y_zoom"],
            "xlabel": "X [nm]",
            "ylabel": "Z [nm]",
            "roi": {
                "type": "rectangle",
                "center": draw_params["XZ"]["roi"]["center"],
                "width": draw_params["XZ"]["roi"]["width"],
                "height": draw_params["XZ"]["roi"]["height"],
            },
        },

        "YZ": {
            "filename": f"enhancement_yzplanar_{field}2.h5",
            "save_anim": f"{enhancement_name}_enh_yz_{field}2.mp4",
            "save_map": f"{enhancement_name}_MAP_YZ.png",
            "x_phys_range": yz_x,
            "y_phys_range": yz_y,
            "x_zoom": draw_params["YZ"]["x_zoom"],
            "y_zoom": draw_params["YZ"]["y_zoom"],
            "xlabel": "Y [nm]",
            "ylabel": "Z [nm]",
            "roi": {
                "type": "rectangle",
                "center": draw_params["YZ"]["roi"]["center"],
                "width": draw_params["YZ"]["roi"]["width"],
                "height": draw_params["YZ"]["roi"]["height"],
            },
        },
    }

    # ============================================================
    # Containers for line plots
    # ============================================================
    line_xdata = []
    line_ydata = []
    line_labels = []

    # ============================================================
    # Main loop
    # ============================================================
    for plane, cfg in planes.items():

        print(f"Processing {enhancement_name} : {plane}")

        if animate:
            animate_field_from_h5_physical(
                h5_filename=cfg["filename"],
                load_h5data_path=enhancement_path,
                save_name=cfg["save_anim"],
                save_path=animation_path,
                interval=50,
                cmap="inferno",
                transpose_xy=True,
                IMG_CLOSE=config.IMG_CLOSE,
                x_phys_range=cfg["x_phys_range"],
                y_phys_range=cfg["y_phys_range"],
                x_zoom=cfg["x_zoom"],
                y_zoom=cfg["y_zoom"],
                mask_left=0,
                mask_right=0,
                mask_bottom=0,
                mask_top=0,
                title=f"{enhancement_name}\nField enhancement |{field.upper()}|²",
                xlabel=cfg["xlabel"],
                ylabel=cfg["ylabel"],
            )

        frame_mean, frame_max = analyze_roi_from_h5_physical(
            h5_filename=cfg["filename"],
            load_h5data_path=enhancement_path,
            roi=cfg["roi"],
            x_phys_range=cfg["x_phys_range"],
            y_phys_range=cfg["y_phys_range"],
        )

        print(
            f"Max mean enhancement in ROI for {plane}: "
            f"{frame_max[1]:.2f} at frame {frame_max[0]}"
        )

        plot_field_frame_from_h5_physical(
            frame_index=int(frame_max[0]),
            h5_filename=cfg["filename"],
            load_h5data_path=enhancement_path,
            cmap="inferno",
            transpose_xy=True,
            IMG_CLOSE=config.IMG_CLOSE,
            x_phys_range=cfg["x_phys_range"],
            y_phys_range=cfg["y_phys_range"],
            x_zoom=cfg["x_zoom"],
            y_zoom=cfg["y_zoom"],
            mask_left=0,
            mask_right=0,
            mask_bottom=0,
            mask_top=0,
            roi=cfg["roi"],
            title=f"{enhancement_name}\nField enhancement |{field.upper()}|²",
            xlabel=cfg["xlabel"],
            ylabel=cfg["ylabel"],
            save_path=map_path,
            save_name=cfg["save_map"],
        )

        line_xdata.append(frame_mean[:, 0])
        line_ydata.append(frame_mean[:, 1])
        line_labels.append(plane)

    # ============================================================
    # Joint plot
    # ============================================================
    colors = cm2c(cm_inferno, 14)

    multi_line_plotter_same_axes(
        xdata_list=line_xdata,
        ydata_list=line_ydata,
        labels=line_labels,
        colors=[colors[0], colors[5], colors[7], colors[9]],
        linestyles=["-", "--", "-.", ":"],
        grid=True,
        xlabel="Time step",
        ylabel=f"|{field.upper()}|² enhancement",
        title=f"{enhancement_name}\nMean enhancement in ROI",
        legend=True,
        save_path=map_path,
        save_name=f"{enhancement_name}_MEAN_ENHANCEMENT_ALL_PLANES.png",
        IMG_CLOSE=config.IMG_CLOSE,
    )

    return 0

def analyze_roi_from_h5_physical(
    h5_filename,
    roi,
    load_h5data_path=None,
    dataset_name=None,

    # --- physical axis definition ---
    x_phys_range=None,   # (xmin, xmax)
    y_phys_range=None,   # (ymin, ymax)

    # --- PML / border crop ---
    xzeros=0,
    yzeros=None,
):
    """
    Analyze mean field value inside a physical ROI over time
    using the FULL simulation domain (no zoom).

    Parameters
    ----------
    h5_filename : str
        Name of HDF5 file with data[x,y,time].

    roi : dict
        ROI definition:
        {
            "type": "rectangle",
            "center": (x, y),
            "width": w,
            "height": h,
        }

    Returns
    -------
    frame_mean : ndarray (Nt, 2)
        [[frame_index, mean_value], ...]

    frame_max : ndarray (2,)
        [frame_index_of_max, max_mean_value]
    """
    # ---------------------------
    # Sanity
    # ---------------------------
    if x_phys_range is None or y_phys_range is None:
        raise ValueError("Provide x_phys_range and y_phys_range")

    if roi["type"] != "rectangle":
        raise NotImplementedError("Only rectangular ROI supported")

    h5_path = (
        os.path.join(load_h5data_path, h5_filename)
        if load_h5data_path is not None
        else h5_filename
    )

    # ---------------------------
    # OPEN FILE (lazy!)
    # ---------------------------
    f = h5py.File(h5_path, "r")

    if dataset_name is None:
        dataset_name = list(f.keys())[0]

    dset = f[dataset_name]

    if dset.ndim != 3:
        raise ValueError(f"Expected data[x,y,time], got {dset.shape}")

    Nx0, Ny0, Nt = dset.shape

    if yzeros is None:
        yzeros = xzeros

    # ---------------------------
    # CROPPING
    # ---------------------------
    xzeros = min(xzeros, Nx0 // 2)
    yzeros = min(yzeros, Ny0 // 2)

    xs = slice(xzeros, Nx0 - xzeros)
    ys = slice(yzeros, Ny0 - yzeros)

    Nx = Nx0 - 2 * xzeros
    Ny = Ny0 - 2 * yzeros

    # ---------------------------
    # PHYSICAL AXES
    # ---------------------------
    x_min0, x_max0 = x_phys_range
    y_min0, y_max0 = y_phys_range

    x_phys = np.linspace(x_min0, x_max0, Nx)
    y_phys = np.linspace(y_min0, y_max0, Ny)

    # ---------------------------
    # ROI mask
    # ---------------------------
    roi_mask = roi_mask_from_rectangle(
        x_phys,
        y_phys,
        center=roi["center"],
        width=roi["width"],
        height=roi["height"],
    )

    if roi_mask.shape != (Nx, Ny):
        raise ValueError(
            f"ROI mask shape {roi_mask.shape} != {(Nx, Ny)}"
        )

    # ---------------------------
    # PRECOMPUTE indices
    # ---------------------------
    roi_idx = np.where(roi_mask)

    # ---------------------------
    # LOOP over time (STREAMING)
    # ---------------------------
    mean_vals = np.empty(Nt, dtype=float)

    for t in range(Nt):
        frame = dset[xs, ys, t]
        mean_vals[t] = frame[roi_idx].mean()

    # ---------------------------
    # RESULTS
    # ---------------------------
    frames = np.arange(Nt)
    frame_mean = np.column_stack((frames, mean_vals))

    t_max = int(np.argmax(mean_vals))
    frame_max = np.array([t_max, mean_vals[t_max]])

    # ---------------------------
    # CLEANUP
    # ---------------------------
    f.close()
    gc.collect()

    return frame_mean, frame_max
