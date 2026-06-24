import meep as mp
xm = 1000

def compute_bounds(volume):
    cx, cy, cz = volume.center.x, volume.center.y, volume.center.z
    sx, sy, sz = volume.size.x, volume.size.y, volume.size.z

    return {
        "xmin": cx - sx / 2,
        "xmax": cx + sx / 2,
        "ymin": cy - sy / 2,
        "ymax": cy + sy / 2,
        "zmin": cz - sz / 2,
        "zmax": cz + sz / 2,
    }

class VolumeSet:
    """
    Containers for all user volumes in stores.

    They are divided into:
        - volume (computational)
        - vis_volume (visualization)
    """

    def __init__(self, cell_size, antenna=None, top_z=None):

        self.volume = {}
        self.vis_volume = {}
        self.bounds = {}

        cx = cell_size.x
        cy = cell_size.y
        cz = cell_size.z

        # =====================================================
        # PLANES FOR CALCULATIONS
        # =====================================================
        self.volume["XY"] = mp.Volume(
            center=mp.Vector3(0, 0, 0),
            size=mp.Vector3(cx, cy, 0.0)
        )

        self.volume["XZ"] = mp.Volume(
            center=mp.Vector3(0, 0, 0),
            size=mp.Vector3(cx, 0.0, cz)
        )

        self.volume["YZ"] = mp.Volume(
            center=mp.Vector3(0, 0, 0),
            size=mp.Vector3(0.0, cy, cz)
        )

        if top_z is not None:
            top_shift_z = top_z
        elif antenna is not None and hasattr(antenna, "thickness"):
            top_shift_z = antenna.thickness / 2.0
        else:
            top_shift_z = 0.0

        self.volume["XY_TOP"] = mp.Volume(
            center=mp.Vector3(0, 0, top_shift_z),
            size=mp.Vector3(cx, cy, 0.0)
        )

        # =====================================================
        # VISUALIZATION PLANES
        # =====================================================
        self.vis_volume["XY"] = mp.Volume(
            center=mp.Vector3(0, 0, 0),
            size=mp.Vector3(cx, cy, 0.0)
        )

        self.vis_volume["XZ"] = mp.Volume(
            center=mp.Vector3(0, 0, 0),
            size=mp.Vector3(cx, 0.0, cz)
        )

        if antenna is not None and hasattr(antenna, "gap"):
            vis_shift_x = antenna.gap * 1.5
        else:
            vis_shift_x = 0.0

        self.vis_volume["YZ"] = mp.Volume(
            center=mp.Vector3(vis_shift_x, 0, 0),
            size=mp.Vector3(0.0, cy, cz)
        )
        
        # =====================================================
        # PLANES BOUNDS
        # =====================================================
        for name, vol in self.volume.items():
            self.bounds[name] = compute_bounds(vol)

class VolumeSetROI:
    """
    ROI volumes based strictly on antenna bounding box + padding.

    REQUIREMENT:
    ------------
    Antenna object MUST be provided.

    Uses:
        - antenna.bounding_box()
        - antenna.center
        - antenna.z_offset

    This ensures physically consistent ROI definition.
    """

    def __init__(
        self,
        cell_size,
        antenna=None,
        padding_xy=50.0,
        padding_z=20.0,
    ):

        # =====================================================
        # HARD CHECK: antenna is required
        # =====================================================
        if antenna is None:
            raise ValueError(
                "VolumeSetROI ERROR: 'antenna' must be provided.\n"
                "ROI definition requires antenna.bounding_box() and position.\n"
                "Use VolumeSet (full-cell) if you do not want ROI-based volumes."
            )

        if not hasattr(antenna, "bounding_box"):
            raise ValueError(
                "VolumeSetROI ERROR: Provided antenna does not implement 'bounding_box()'."
            )

        if not hasattr(antenna, "center"):
            raise ValueError(
                "VolumeSetROI ERROR: Provided antenna does not have 'center' attribute."
            )

        # =====================================================
        # INIT
        # =====================================================
        self.volume = {}
        self.vis_volume = {}
        self.bounds = {}

        # =====================================================
        # ROI FROM ANTENNA
        # =====================================================

        bx, by, bz = antenna.bounding_box()
        cx, cy = antenna.center
        cz = getattr(antenna, "z_offset", 0.0)
        padding_xy = padding_xy / xm
        padding_z = padding_z / xm

        roi_center = mp.Vector3(cx, cy, cz)

        roi_size = mp.Vector3(
            bx + 2 * padding_xy,
            by + 2 * padding_xy,
            bz + 2 * padding_z
        )

        # =====================================================
        # PLANES FOR CALCULATIONS (ROI LIMITED)
        # =====================================================
        self.volume["XY"] = mp.Volume(
            center=roi_center,
            size=mp.Vector3(roi_size.x, roi_size.y, 0.0)
        )

        self.volume["XZ"] = mp.Volume(
            center=roi_center,
            size=mp.Vector3(roi_size.x, 0.0, roi_size.z)
        )

        self.volume["YZ"] = mp.Volume(
            center=roi_center,
            size=mp.Vector3(0.0, roi_size.y, roi_size.z)
        )

        # =====================================================
        # TOP PLANE (antenna surface)
        # =====================================================
        if hasattr(antenna, "thickness"):
            top_z = cz + antenna.thickness / 2.0
        else:
            top_z = cz

        self.volume["XY_TOP"] = mp.Volume(
            center=mp.Vector3(cx, cy, top_z),
            size=mp.Vector3(roi_size.x, roi_size.y, 0.0)
        )

        # =====================================================
        # VISUALIZATION (FULL CELL)
        # =====================================================
        self.vis_volume["XY"] = mp.Volume(
            center=mp.Vector3(0, 0, 0),
            size=mp.Vector3(cell_size.x, cell_size.y, 0.0)
        )

        self.vis_volume["XZ"] = mp.Volume(
            center=mp.Vector3(0, 0, 0),
            size=mp.Vector3(cell_size.x, 0.0, cell_size.z)
        )

        if hasattr(antenna, "gap"):
            vis_shift_x = antenna.gap * 1.5
        else:
            vis_shift_x = 0.0

        self.vis_volume["YZ"] = mp.Volume(
            center=mp.Vector3(vis_shift_x, 0, 0),
            size=mp.Vector3(0.0, cell_size.y, cell_size.z)
        )

        # =====================================================
        # PLANES BOUNDS
        # =====================================================
        for name, vol in self.volume.items():
            self.bounds[name] = compute_bounds(vol)
