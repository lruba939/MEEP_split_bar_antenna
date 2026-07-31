import sys, os
import meep as mp
from meep.materials import *
from utils.sys_utils import *
from utils.meep_utils import *
from utils.geometry_utils import make_cell
from utils.logger import save_and_show_config, append_time_to_file
from src.antenna_geometries import *
from src.config import SimulationConfig
from src.sources import *
from src.volumes import *
from visualization.plotter import *

xm = 1000
mp.Simulation.eps_averaging = False

def bowtie_substrate_experiment(
    material_name,
    antenna_material="Au",
    COMMENT=None,
    empty_from_cache=None,
    substrate_from_cache=None,
    antenna_from_cache=None
    ):
    # =====================================================
    config = SimulationConfig()

    config.resolution = 500
    config.sim_time = 28000 / xm
    config.sim_time_step = 100 / xm

    config.lambda0 = 660 / xm
    config.frequency_width = 1.0

    config.pml = 350/xm
    pml_factor = 1.5
    
    gap = 6

    # =====================================================
    Top = BowTieEquilateral(
        gap=gap/xm,
        length=86.6/xm, # <- to have about 100 nm in width
        thickness=30/xm,
        radius=5/xm,
        material_name=antenna_material,
        z_offset=0.0
    )
    substrate = Bar(
        length=800/xm,
        width=800/xm,
        thickness=100/xm,
        material_name=material_name,
        z_offset=-(30/2.0+100/2.0)/xm,
        radius=0/xm,
    )

    geometry_substrate = substrate.build_geometry()
    geometry_antenna = Top.build_geometry() + substrate.build_geometry()

    config.pad = 80/xm
    config.cell_size = [
        substrate.length + config.pad*2 + config.pml*2,   # x
        substrate.width + config.pad*2 + config.pml*2,   # y
        substrate.thickness+Top.thickness + config.pad*2 + config.pml*2    # z
    ]
    cell = make_cell(config=config)

    config.src_size = [
        700 / xm,  # x
        700 / xm,  # y
        0.0 / xm    # z
    ]

    #!!!
    config.src_is_integrated = True
    
    config.src_center = [
        0.0,    # x
        0.0,    # y
        config.cell_size[2]/2.0-1.04*config.pml  # z
    ]

    config.nfreq = 500

    config.z_reflection = 70 / xm
    config.z_transmission = -60 / xm

    config.x_flux_monitor = 400 / xm
    config.y_flux_monitor = 400 / xm

    antenna_vols = VolumeSetROI(cell, antenna=Top)

    sim_empty = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=[],
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    sim_substrate = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=geometry_substrate,
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    sim_antenna = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=geometry_antenna,
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    # =====================================================
    SIM_NAME = build_folder_name(
        structure="bowtie",
        wavelength_nm=config.lambda0 * xm,
        gap_nm=Top.gap * xm,
        antenna_material=Top.material_name,
        substrate_material=substrate.material_name,
        L=Top.length * xm,
        T=Top.thickness * xm,
        R=Top.radius * xm
    )

    config.path_to_save = create_directory(SIM_NAME)

    ########################
    log_system_usage(
        config.path_to_save,
        "after_mp.Simulation",
    )
    #######################
    # =====================================================
    save_and_show_config(config, [Top, substrate], COMMENT=COMMENT, empty_cache=empty_from_cache, substrate_cache=substrate_from_cache, antenna_cache=antenna_from_cache)
    # =====================================================
    print_task(1, "2D projections.")
    for sim, name_prefix in {
        sim_empty: "empty",
        sim_antenna: "antenna",
        sim_substrate: "substrate",
    }.items():
        for plane in ["XY", "XZ", "YZ"]:
            Name2D = f"{name_prefix}_vis_{plane}.png"
            save_2D_plot(
                sim,
                antenna_vols.vis_volume[plane],
                save_name=Name2D,
                path_to_save=config.path_to_save,
                IMG_CLOSE=config.IMG_CLOSE,
                config=config
            )
        for plane in ["XY", "XZ", "YZ"]:
            Name2D = f"{name_prefix}_roi_{plane}.png"
            save_2D_plot(
                sim,
                antenna_vols.volume[plane],
                save_name=Name2D,
                path_to_save=config.path_to_save,
                IMG_CLOSE=config.IMG_CLOSE
            )
    # =====================================================
#     compute_fields_2(
#         sim_empty=sim_empty,
#         empty_from_cache=empty_from_cache,
#         
#         sim_substrate=sim_substrate,
#         substrate_from_cache=substrate_from_cache,
#         
#         sim_antenna=sim_antenna,
#         antenna_from_cache=antenna_from_cache,
#         
#         volumes=antenna_vols,
#         config=config,
# 
#         TRL=True,
#         TRL_X_size=config.x_flux_monitor,
#         TRL_Y_size=config.y_flux_monitor,
# 
#         scattering=True,
#         scattering_object=Top,
# 
#         dft_gap_spectrum=True,
#         dft_object=Top,
# 
#         calc_enh=True,
#     )
    # ########################
    # draw_params = {
    #     "XY": {"x_zoom": 1,
    #            "y_zoom": 1,
    #            "roi": {
    #                 "center": (0, 0),
    #                 "width": Top.gap * 1e3,
    #                 "height":Top.gap * 1e3,
    #             },
    #     },
    #     "XZ": {"x_zoom": 1,
    #            "y_zoom": 1,
    #            "roi": {
    #                 "center": (0, 0),
    #                 "width": Top.gap * 1e3,
    #                 "height": Top.thickness * 1e3,
    #             },
    #     },
    #     "YZ": {"x_zoom": 1,
    #            "y_zoom": 1,
    #            "roi": {
    #                 "center": (0, 0),
    #                 "width": Top.gap * 1e3,
    #                 "height": Top.thickness * 1e3,
    #             },
    #     },
    # }
    # enhancement_root = os.path.join(
    #     config.path_to_save,
    #     "cache",
    #     "enhancement",
    # )
    # for enhancement_name in (
    #     "substrate_over_empty",
    #     "antenna_over_empty",
    #     "antenna_over_substrate",
    # ):
    #     animate_enhancement_fields(
    #         enhancement_path=os.path.join(
    #             enhancement_root,
    #             enhancement_name,
    #         ),
    #     enhancement_name=enhancement_name,
    #     config=config,
    #     volumes=antenna_vols,
    #     draw_params=draw_params,
    #     field="E",
    #     animate=True,
    # )

    ########################    
    log_system_usage(
        config.path_to_save,
        "END",
    )
    #######################
    return 0

def bowtie_substrate_in_PML_experiment(
    material_name,
    COMMENT=None,
    empty_from_cache=None,
    substrate_from_cache=None,
    antenna_from_cache=None
    ):
    # =====================================================
    config = SimulationConfig()

    config.resolution = 500
    config.sim_time = 20000 / xm
    config.sim_time_step = 100 / xm

    config.lambda0 = 660 / xm
    config.frequency_width = 1.0

    config.pml = 350/xm
    pml_factor = 1.5
    
    gap = 6

    # =====================================================
    Top = BowTieEquilateral(
        gap=gap/xm,
        length=86.6/xm, # <- to have about 100 nm in width
        thickness=30/xm,
        radius=5/xm,
        material_name="Au",
        z_offset=0.0
    )
    substrate = Bar(
        length=1200/xm,
        width=1200/xm,
        thickness=config.pml*pml_factor,
        material_name=material_name,
        z_offset=-(30/2.0+config.pml*1e3*pml_factor/2.0)/xm,
        radius=10/xm,
    )

    geometry_substrate = substrate.build_geometry()
    geometry_antenna = Top.build_geometry() + substrate.build_geometry()

    # config.pad = 0
    config.pad = 80/xm
    config.cell_size = [
        substrate.length,   # x
        substrate.width,   # y
        substrate.thickness+Top.thickness + pml_factor*config.pml    # z
    ]
    cell = make_cell(config=config)

    # config.src_size = [
    #     Top.length*3,  # x
    #     Top.length*3,  # y
    #     0.0 / xm    # z
    # ]
    config.src_size = [
        1200 / xm,  # x
        1200 / xm,  # y
        0.0 / xm    # z
    ]
    # config.src_size = [
    #     config.cell_size[0],  # x
    #     config.cell_size[1],  # y
    #     0.0 / xm    # z
    # ]
    # config.src_size = [
    #     700/xm,  # x
    #     700/xm,  # y
    #     0.0 / xm    # z
    # ]

    #!!!
    config.src_is_integrated = True
    
    config.src_center = [
        0.0,    # x
        0.0,    # y
        config.cell_size[2]/2.0-1.1*config.pml  # z
    ]

    config.nfreq = 500
    # config.z_reflection = config.cell_size[2]/2.0-1.20*config.pml
    # config.z_transmission = -config.cell_size[2]/2.0+config.pml+15/xm

    config.z_reflection = 120 / xm
    config.z_transmission = -120 / xm
    # config.x_flux_monitor = 400 / xm
    # config.y_flux_monitor = 400 / xm
    config.x_flux_monitor = 260 / xm
    config.y_flux_monitor = 260 / xm

    antenna_vols = VolumeSetROI(cell, antenna=Top)

    sim_empty = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=[],
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    sim_substrate = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=geometry_substrate,
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    sim_antenna = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=geometry_antenna,
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    # =====================================================
    SIM_NAME = build_folder_name(
        structure="bowtie",
        wavelength_nm=config.lambda0 * xm,
        gap_nm=Top.gap * xm,
        antenna_material=Top.material_name,
        substrate_material=substrate.material_name,
        L=Top.length * xm,
        T=Top.thickness * xm,
        R=Top.radius * xm
    )

    config.path_to_save = create_directory(SIM_NAME)

    ########################
    log_system_usage(
        config.path_to_save,
        "after_mp.Simulation",
    )
    #######################
    # =====================================================
    save_and_show_config(config, [Top, substrate], COMMENT=COMMENT, empty_cache=empty_from_cache, substrate_cache=substrate_from_cache, antenna_cache=antenna_from_cache)
    # =====================================================
    print_task(1, "2D projections.")
    for sim, name_prefix in {
        sim_empty: "empty",
        sim_antenna: "antenna",
        sim_substrate: "substrate",
    }.items():
        for plane in ["XY", "XZ", "YZ"]:
            Name2D = f"{name_prefix}_vis_{plane}.png"
            save_2D_plot(
                sim,
                antenna_vols.vis_volume[plane],
                save_name=Name2D,
                path_to_save=config.path_to_save,
                IMG_CLOSE=config.IMG_CLOSE,
                config=config
            )
        for plane in ["XY", "XZ", "YZ"]:
            Name2D = f"{name_prefix}_roi_{plane}.png"
            save_2D_plot(
                sim,
                antenna_vols.volume[plane],
                save_name=Name2D,
                path_to_save=config.path_to_save,
                IMG_CLOSE=config.IMG_CLOSE
            )
    # =====================================================
    compute_fields_2(
        sim_empty=sim_empty,
        empty_from_cache=empty_from_cache,
        
        sim_substrate=sim_substrate,
        substrate_from_cache=substrate_from_cache,
        
        sim_antenna=sim_antenna,
        antenna_from_cache=antenna_from_cache,
        
        volumes=antenna_vols,
        config=config,

        TRL=True,
        # TRL_X_size=config.cell_size[0],
        # TRL_Y_size=config.cell_size[1],
        TRL_X_size=config.x_flux_monitor,
        TRL_Y_size=config.y_flux_monitor,

        scattering=True,
        scattering_object=Top,

        dft_gap_spectrum=True,
        dft_object=Top,

        # harminv=True,

        calc_enh=True,
    )
    # ########################
    # draw_params = {
    #     "XY": {"x_zoom": 1,
    #            "y_zoom": 1,
    #            "roi": {
    #                 "center": (0, 0),
    #                 "width": Top.gap * 1e3,
    #                 "height":Top.gap * 1e3,
    #             },
    #     },
    #     "XZ": {"x_zoom": 1,
    #            "y_zoom": 1,
    #            "roi": {
    #                 "center": (0, 0),
    #                 "width": Top.gap * 1e3,
    #                 "height": Top.thickness * 1e3,
    #             },
    #     },
    #     "YZ": {"x_zoom": 1,
    #            "y_zoom": 1,
    #            "roi": {
    #                 "center": (0, 0),
    #                 "width": Top.gap * 1e3,
    #                 "height": Top.thickness * 1e3,
    #             },
    #     },
    # }
    # enhancement_root = os.path.join(
    #     config.path_to_save,
    #     "cache",
    #     "enhancement",
    # )
    # for enhancement_name in (
    #     "substrate_over_empty",
    #     "antenna_over_empty",
    #     "antenna_over_substrate",
    # ):
    #     animate_enhancement_fields(
    #         enhancement_path=os.path.join(
    #             enhancement_root,
    #             enhancement_name,
    #         ),
    #     enhancement_name=enhancement_name,
    #     config=config,
    #     volumes=antenna_vols,
    #     draw_params=draw_params,
    #     field="E",
    #     animate=True,
    # )

    ########################    
    log_system_usage(
        config.path_to_save,
        "END",
    )
    #######################
    return 0

def bowtie_substrate_Z_in_absorber_experiment(
    material_name,
    COMMENT=None,
    empty_from_cache=None,
    substrate_from_cache=None,
    antenna_from_cache=None
    ):
    # =====================================================
    config = SimulationConfig()

    config.resolution = 500
    config.sim_time = 20000 / xm
    config.sim_time_step = 100 / xm

    config.lambda0 = 660 / xm
    config.frequency_width = 1.0

    config.pml = 350/xm
    pml_factor = 1.5
    
    gap = 6

    # =====================================================
    Top = BowTieEquilateral(
        gap=gap/xm,
        length=86.6/xm, # <- to have about 100 nm in width
        thickness=30/xm,
        radius=5/xm,
        material_name="Au",
        z_offset=0.0
    )
    substrate = Bar(
        length=800/xm,
        width=800/xm,
        thickness=config.pml*pml_factor,
        material_name=material_name,
        z_offset=-(30/2.0+config.pml*1e3*pml_factor/2.0)/xm,
        radius=10/xm,
    )

    geometry_substrate = substrate.build_geometry()
    geometry_antenna = Top.build_geometry() + substrate.build_geometry()

    # config.pad = 0
    config.pad = 80/xm
    config.cell_size = [
        substrate.length+config.pad*2+config.pml*2,   # x
        substrate.width+config.pad*2+config.pml*2,   # y
        substrate.thickness+Top.thickness + pml_factor*config.pml    # z
    ]
    cell = make_cell(config=config)

    # config.src_size = [
    #     Top.length*3,  # x
    #     Top.length*3,  # y
    #     0.0 / xm    # z
    # ]
    config.src_size = [
        750 / xm,  # x
        750 / xm,  # y
        0.0 / xm    # z
    ]
    # config.src_size = [
    #     config.cell_size[0],  # x
    #     config.cell_size[1],  # y
    #     0.0 / xm    # z
    # ]
    # config.src_size = [
    #     700/xm,  # x
    #     700/xm,  # y
    #     0.0 / xm    # z
    # ]

    #!!!
    config.src_is_integrated = True
    
    config.src_center = [
        0.0,    # x
        0.0,    # y
        config.cell_size[2]/2.0-1.1*config.pml  # z
    ]

    config.nfreq = 500
    # config.z_reflection = config.cell_size[2]/2.0-1.20*config.pml
    # config.z_transmission = -config.cell_size[2]/2.0+config.pml+15/xm

    config.z_reflection = 120 / xm
    config.z_transmission = -120 / xm
    # config.x_flux_monitor = 400 / xm
    # config.y_flux_monitor = 400 / xm
    config.x_flux_monitor = 400 / xm
    config.y_flux_monitor = 400 / xm

    antenna_vols = VolumeSetROI(cell, antenna=Top)

    sim_empty = mp.Simulation(
        cell_size=cell,
        boundary_layers=[
            mp.PML(config.pml, direction=mp.X),
            mp.PML(config.pml, direction=mp.Y),
            mp.PML(config.pml, direction=mp.Z, side=mp.High),
            mp.Absorber(config.pml, direction=mp.Z, side=mp.Low),
        ],
        geometry=[],
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    sim_substrate = mp.Simulation(
        cell_size=cell,
        boundary_layers=[
            mp.PML(config.pml, direction=mp.X),
            mp.PML(config.pml, direction=mp.Y),
            mp.PML(config.pml, direction=mp.Z, side=mp.High),
            mp.Absorber(config.pml, direction=mp.Z, side=mp.Low),
        ],
        geometry=geometry_substrate,
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    sim_antenna = mp.Simulation(
        cell_size=cell,
        boundary_layers=[
            mp.PML(config.pml, direction=mp.X),
            mp.PML(config.pml, direction=mp.Y),
            mp.PML(config.pml, direction=mp.Z, side=mp.High),
            mp.Absorber(config.pml, direction=mp.Z, side=mp.Low),
        ],
        geometry=geometry_antenna,
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    # =====================================================
    SIM_NAME = build_folder_name(
        structure="bowtie",
        wavelength_nm=config.lambda0 * xm,
        gap_nm=Top.gap * xm,
        antenna_material=Top.material_name,
        substrate_material=substrate.material_name,
        L=Top.length * xm,
        T=Top.thickness * xm,
        R=Top.radius * xm
    )

    config.path_to_save = create_directory(SIM_NAME)

    ########################
    log_system_usage(
        config.path_to_save,
        "after_mp.Simulation",
    )
    #######################
    # =====================================================
    save_and_show_config(config, [Top, substrate], COMMENT=COMMENT, empty_cache=empty_from_cache, substrate_cache=substrate_from_cache, antenna_cache=antenna_from_cache)
    # =====================================================
    print_task(1, "2D projections.")
    for sim, name_prefix in {
        sim_empty: "empty",
        sim_antenna: "antenna",
        sim_substrate: "substrate",
    }.items():
        for plane in ["XY", "XZ", "YZ"]:
            Name2D = f"{name_prefix}_vis_{plane}.png"
            save_2D_plot(
                sim,
                antenna_vols.vis_volume[plane],
                save_name=Name2D,
                path_to_save=config.path_to_save,
                IMG_CLOSE=config.IMG_CLOSE,
                config=config
            )
        for plane in ["XY", "XZ", "YZ"]:
            Name2D = f"{name_prefix}_roi_{plane}.png"
            save_2D_plot(
                sim,
                antenna_vols.volume[plane],
                save_name=Name2D,
                path_to_save=config.path_to_save,
                IMG_CLOSE=config.IMG_CLOSE
            )
    # =====================================================
    compute_fields_2(
        sim_empty=sim_empty,
        empty_from_cache=empty_from_cache,
        
        sim_substrate=sim_substrate,
        substrate_from_cache=substrate_from_cache,
        
        sim_antenna=sim_antenna,
        antenna_from_cache=antenna_from_cache,
        
        volumes=antenna_vols,
        config=config,

        TRL=True,
        # TRL_X_size=config.cell_size[0],
        # TRL_Y_size=config.cell_size[1],
        TRL_X_size=config.x_flux_monitor,
        TRL_Y_size=config.y_flux_monitor,

        scattering=True,
        scattering_object=Top,

        dft_gap_spectrum=True,
        dft_object=Top,

        # harminv=True,

        calc_enh=True,
    )
    # ########################
    # draw_params = {
    #     "XY": {"x_zoom": 1,
    #            "y_zoom": 1,
    #            "roi": {
    #                 "center": (0, 0),
    #                 "width": Top.gap * 1e3,
    #                 "height":Top.gap * 1e3,
    #             },
    #     },
    #     "XZ": {"x_zoom": 1,
    #            "y_zoom": 1,
    #            "roi": {
    #                 "center": (0, 0),
    #                 "width": Top.gap * 1e3,
    #                 "height": Top.thickness * 1e3,
    #             },
    #     },
    #     "YZ": {"x_zoom": 1,
    #            "y_zoom": 1,
    #            "roi": {
    #                 "center": (0, 0),
    #                 "width": Top.gap * 1e3,
    #                 "height": Top.thickness * 1e3,
    #             },
    #     },
    # }
    # enhancement_root = os.path.join(
    #     config.path_to_save,
    #     "cache",
    #     "enhancement",
    # )
    # for enhancement_name in (
    #     "substrate_over_empty",
    #     "antenna_over_empty",
    #     "antenna_over_substrate",
    # ):
    #     animate_enhancement_fields(
    #         enhancement_path=os.path.join(
    #             enhancement_root,
    #             enhancement_name,
    #         ),
    #     enhancement_name=enhancement_name,
    #     config=config,
    #     volumes=antenna_vols,
    #     draw_params=draw_params,
    #     field="E",
    #     animate=True,
    # )

    ########################    
    log_system_usage(
        config.path_to_save,
        "END",
    )
    #######################
    return 0

def bowtie_big_substrate_experiment(material_name):
    # =====================================================
    config = SimulationConfig()

    config.resolution = 500
    config.sim_time = 18000 / xm
    config.sim_time_step = 50 / xm
    config.lambda0 = 660 / xm
    config.frequency_width = 1.0
    gap = 6

    X_material = get_materials_dict(material_name)
    X_material_name = material_name
    
    SIM_NAME = f"NGeo_smallsrc_bigdet_F_BSE_Au_on_{X_material_name}_wavleng_{config.lambda0}_gap_{gap}"
    config.path_to_save, config.animations_folder_path = create_directory(SIM_NAME)
    # =====================================================
    AuTop = BowTieEquilateral(
        gap=gap/xm,
        length=86.6/xm, # <- to have about 100 nm in width
        thickness=30/xm,
        radius=5/xm,
        material=Au,
        z_offset=0.0
    )
    substrate = Bar(
        length=1000/xm,
        width=1000/xm,
        thickness=520/xm,
        material=X_material,
        z_offset=-(30/2.0+520/2.0)/xm,
        radius=0/xm,
    )

    geometry = AuTop.build_geometry() + substrate.build_geometry()
    geometry_empty = substrate.build_geometry()

    config.pad = 0
    # config.pad = 80/xm
    config.pml = 350/xm
    config.cell_size = [
        substrate.length,   # x
        substrate.width,   # y
        substrate.thickness+AuTop.thickness + 1.5*config.pml    # z
    ]
    cell = make_cell(config=config)

    config.src_size = [
        AuTop.length*3,  # x
        AuTop.length*3,  # y
        0.0 / xm    # z
    ]

    #!!!
    config.src_is_integrated = True
    
    config.src_center = [
        0.0,    # x
        0.0,    # y
        config.cell_size[2]/2.0-1.05*config.pml  # z
    ]

    config.nfreq = 500
    config.z_reflection = config.cell_size[2]/2.0-1.20*config.pml
    config.z_transmission = -config.cell_size[2]/2.0+config.pml+15/xm

    antenna_vols = VolumeSetROI(cell, antenna=AuTop)
    sim = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=geometry,
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    sim_empty = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=geometry_empty,
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    # =====================================================
    save_and_show_config(config, [AuTop, substrate])
    # =====================================================
    print_task(1, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"antenna_vis_{plane}.png"
        save_2D_plot(
            sim,
            antenna_vols.vis_volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE,
            config=config
        )
    print_task(2, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"antenna_roi_{plane}.png"
        save_2D_plot(
            sim,
            antenna_vols.volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE
        )
    # =====================================================
    print_task(1, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"empty_vis_{plane}.png"
        save_2D_plot(
            sim_empty,
            antenna_vols.vis_volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE,
            config=config
        )
    print_task(2, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"empty_roi_{plane}.png"
        save_2D_plot(
            sim_empty,
            antenna_vols.volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE
        )
    # # =====================================================
    # print_task(3, "3D calculations.")
    # compute_fields(
    #     sim,
    #     sim_empty,
    #     antenna_vols,
    #     config,
    #     fluxes=True,
    #     # fluxes_X_size=substrate.length/2.0,
    #     # fluxes_Y_size=substrate.width/2.0,
    #     fluxes_X_size=config.cell_size[0],
    #     fluxes_Y_size=config.cell_size[1],
    #     scattering=True,
    #     dft_gap_spectrum=True,
    #     harminv=True,
    #     scattering_antenna=AuTop
    # )
    return 0

def bowtie_substrate_experiment_LT(material_name):
    # =====================================================
    config = SimulationConfig()

    config.resolution = 500
    config.sim_time = 25000 / xm
    config.sim_time_step = 50 / xm
    config.lambda0 = 660 / xm
    config.frequency_width = 1.0
    gap = 6

    X_material = get_materials_dict(material_name)
    X_material_name = material_name
    
    SIM_NAME = f"BSELT_Au{X_material_name}_wavleng_{config.lambda0}_gap_{gap}"
    config.path_to_save, config.animations_folder_path = create_directory(SIM_NAME)
    # =====================================================
    AuTop = BowTieEquilateral(
        gap=gap/xm,
        length=86.6/xm, # <- to have about 100 nm in width
        thickness=30/xm,
        radius=5/xm,
        material=Au,
        z_offset=0.0
    )
    substrate = Bar(
        length=800/xm,
        width=800/xm,
        thickness=100/xm,
        material=X_material,
        z_offset=-(30/2.0+100/2.0)/xm,
        radius=12/xm,
    )

    geometry = AuTop.build_geometry() + substrate.build_geometry()

    config.pad = 80/xm
    config.pml = 350/xm
    config.cell_size = [
        substrate.length + 2*config.pad + 2*config.pml,   # x
        substrate.width + 2*config.pad + 2*config.pml,   # y
        substrate.thickness+AuTop.thickness + 2*config.pad + 2*config.pml    # z
    ]
    cell = make_cell(config=config)

    config.src_size = [
        substrate.length,  # x
        substrate.width,  # y
        0.0 / xm    # z
    ]
    config.src_center = [
        0.0,    # x
        0.0,    # y
        config.cell_size[2]/2.0-1.15*config.pml  # z
    ]

    config.nfreq = 500
    config.z_reflection = config.cell_size[2]/2.0-1.20*config.pml
    config.z_transmission = -config.cell_size[2]/2.0+config.pml+15/xm

    antenna_vols = VolumeSetROI(cell, antenna=AuTop)

    sim = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=geometry,
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    sim_empty = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=[],
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    # =====================================================
    save_and_show_config(config, [AuTop, substrate])
    # =====================================================
    print_task(1, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"antenna_vis_{plane}.png"
        save_2D_plot(
            sim,
            antenna_vols.vis_volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE,
            config=config
        )
    print_task(2, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"antenna_roi_{plane}.png"
        save_2D_plot(
            sim,
            antenna_vols.volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE
        )
    # =====================================================
    print_task(1, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"empty_vis_{plane}.png"
        save_2D_plot(
            sim_empty,
            antenna_vols.vis_volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE,
            config=config
        )
    print_task(2, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"empty_roi_{plane}.png"
        save_2D_plot(
            sim_empty,
            antenna_vols.volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE
        )
    # =====================================================
    print_task(3, "3D calculations.")
    compute_fields(
        sim,
        sim_empty,
        antenna_vols,
        config,
        fluxes=True,
        scattering=True,
        dft_gap_spectrum=True,
        harminv=True,
        scattering_antenna=AuTop
    )
    return 0

def bowtie_substrate_experiment_MIR(material_name):
    # =====================================================
    config = SimulationConfig()

    config.resolution = 500
    config.sim_time = 40000 / xm
    config.sim_time_step = 50 / xm
    config.lambda0 = 1700 / xm
    config.frequency_width = 0.4
    gap = 6

    X_material = get_materials_dict(material_name)
    X_material_name = material_name
    
    SIM_NAME = f"BSEMIR_Au{X_material_name}_wavleng_{config.lambda0}_gap_{gap}"
    config.path_to_save, config.animations_folder_path = create_directory(SIM_NAME)
    # =====================================================
    AuTop = BowTie(
        gap=gap/xm,
        length=86.6/xm*2.5, # <- to have about 100 nm in width
        width=100/xm,
        thickness=30/xm,
        radius=5/xm,
        material=Au,
        z_offset=0.0
    )
    hole_fix_1 = mp.Block(
        mp.Vector3(26/xm, 6/xm, 30/xm),
        center=mp.Vector3(24/xm, 0, 0),
        material=Au,
    )
    hole_fix_2 = mp.Block(
        mp.Vector3(26/xm, 6/xm, 30/xm),
        center=mp.Vector3(-24/xm, 0, 0),
        material=Au,
    )
    substrate = Bar(
        length=800/xm,
        width=800/xm,
        thickness=100/xm,
        material=X_material,
        z_offset=-(30/2.0+100/2.0)/xm,
        radius=12/xm,
    )

    geometry = AuTop.build_geometry() + substrate.build_geometry() + [hole_fix_1, hole_fix_2]

    config.pad = 80/xm
    config.pml = 700/xm
    config.cell_size = [
        substrate.length + 2*config.pad + 2*config.pml,   # x
        substrate.width + 2*config.pad + 2*config.pml,   # y
        substrate.thickness+AuTop.thickness + 2*config.pad + 2*config.pml    # z
    ]
    cell = make_cell(config=config)

    config.src_size = [
        substrate.length,  # x
        substrate.width,  # y
        0.0 / xm    # z
    ]
    config.src_center = [
        0.0,    # x
        0.0,    # y
        config.cell_size[2]/2.0-1.15*config.pml  # z
    ]

    config.nfreq = 500
    config.z_reflection = config.cell_size[2]/2.0-1.20*config.pml
    config.z_transmission = -config.cell_size[2]/2.0+config.pml+15/xm

    antenna_vols = VolumeSetROI(cell, antenna=AuTop)

    sim = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=geometry,
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    sim_empty = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=[],
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    # =====================================================
    save_and_show_config(config, [AuTop, substrate])
    # =====================================================
    print_task(1, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"antenna_vis_{plane}.png"
        save_2D_plot(
            sim,
            antenna_vols.vis_volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE,
            config=config
        )
    print_task(2, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"antenna_roi_{plane}.png"
        save_2D_plot(
            sim,
            antenna_vols.volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE
        )
    # =====================================================
    print_task(1, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"empty_vis_{plane}.png"
        save_2D_plot(
            sim_empty,
            antenna_vols.vis_volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE,
            config=config
        )
    print_task(2, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"empty_roi_{plane}.png"
        save_2D_plot(
            sim_empty,
            antenna_vols.volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE
        )
    # =====================================================
    print_task(3, "3D calculations.")
    compute_fields(
        sim,
        sim_empty,
        antenna_vols,
        config,
        fluxes=True,
        scattering=True,
        dft_gap_spectrum=True,
        harminv=True,
        scattering_antenna=AuTop
    )
    return 0

def bowtie_substrate_ONLY_experiment(material_name):
    # =====================================================
    config = SimulationConfig()

    config.resolution = 500
    config.sim_time = 18000 / xm
    config.sim_time_step = 50 / xm
    config.lambda0 = 660 / xm
    config.frequency_width = 1.0
    gap = 6

    X_material = get_materials_dict(material_name)
    X_material_name = material_name
    
    SIM_NAME = f"BSOE_AIR{X_material_name}_wavleng_{config.lambda0}_gap_{gap}"
    config.path_to_save, config.animations_folder_path = create_directory(SIM_NAME)
    # =====================================================
    AuTop = BowTieEquilateral(
        gap=gap/xm,
        length=86.6/xm, # <- to have about 100 nm in width
        thickness=30/xm,
        radius=5/xm,
        material=mp.air,
        z_offset=0.0
    )
    substrate = Bar(
        length=800/xm,
        width=800/xm,
        thickness=100/xm,
        material=X_material,
        z_offset=-(30/2.0+100/2.0)/xm,
        radius=12/xm,
    )

    geometry = AuTop.build_geometry() + substrate.build_geometry()

    config.pad = 80/xm
    config.pml = 350/xm
    config.cell_size = [
        substrate.length + 2*config.pad + 2*config.pml,   # x
        substrate.width + 2*config.pad + 2*config.pml,   # y
        substrate.thickness+AuTop.thickness + 2*config.pad + 2*config.pml    # z
    ]
    cell = make_cell(config=config)

    config.src_size = [
        substrate.length,  # x
        substrate.width,  # y
        0.0 / xm    # z
    ]
    config.src_center = [
        0.0,    # x
        0.0,    # y
        config.cell_size[2]/2.0-1.15*config.pml  # z
    ]

    config.nfreq = 500
    config.z_reflection = config.cell_size[2]/2.0-1.20*config.pml
    config.z_transmission = -config.cell_size[2]/2.0+config.pml+15/xm

    antenna_vols = VolumeSetROI(cell, antenna=AuTop)

    sim = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=geometry,
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    sim_empty = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=[],
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    # =====================================================
    save_and_show_config(config, [AuTop, substrate])
    # =====================================================
    print_task(1, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"antenna_vis_{plane}.png"
        save_2D_plot(
            sim,
            antenna_vols.vis_volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE,
            config=config
        )
    print_task(2, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"antenna_roi_{plane}.png"
        save_2D_plot(
            sim,
            antenna_vols.volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE
        )
    # =====================================================
    print_task(1, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"empty_vis_{plane}.png"
        save_2D_plot(
            sim_empty,
            antenna_vols.vis_volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE,
            config=config
        )
    print_task(2, "2D projections.")
    for plane in ["XY", "XZ", "YZ"]:
        Name2D = f"empty_roi_{plane}.png"
        save_2D_plot(
            sim_empty,
            antenna_vols.volume[plane],
            save_name=Name2D,
            path_to_save=config.path_to_save,
            IMG_CLOSE=config.IMG_CLOSE
        )
    # =====================================================
    print_task(3, "3D calculations.")
    compute_fields(
        sim,
        sim_empty,
        antenna_vols,
        config,
        fluxes=True,
        scattering=True,
        dft_gap_spectrum=True,
        harminv=True,
        scattering_antenna=AuTop
    )
    return 0

def after_hpc_redraw(material_name):
    # =====================================================
    config = SimulationConfig()

    config.resolution = 500
    config.sim_time = 18000 / xm
    config.sim_time_step = 50 / xm
    config.lambda0 = 660 / xm
    config.frequency_width = 1.0
    gap = 6

    X_material = get_materials_dict(material_name)
    X_material_name = material_name
    
    SIM_NAME = f"BSE_Au{X_material_name}_wavleng_{config.lambda0}_gap_{gap}"
    config.path_to_save, config.animations_folder_path = create_directory(SIM_NAME)
    # =====================================================
    AuTop = BowTieEquilateral(
        gap=gap/xm,
        length=86.6/xm, # <- to have about 100 nm in width
        thickness=30/xm,
        radius=5/xm,
        material=Au,
        z_offset=0.0
    )
    substrate = Bar(
        length=800/xm,
        width=800/xm,
        thickness=100/xm,
        material=X_material,
        z_offset=-(30/2.0+100/2.0)/xm,
        radius=12/xm,
    )

    geometry = AuTop.build_geometry() + substrate.build_geometry()

    config.pad = 80/xm
    config.pml = 350/xm
    config.cell_size = [
        substrate.length + 2*config.pad + 2*config.pml,   # x
        substrate.width + 2*config.pad + 2*config.pml,   # y
        substrate.thickness+AuTop.thickness + 2*config.pad + 2*config.pml    # z
    ]
    cell = make_cell(config=config)

    config.src_size = [
        substrate.length,  # x
        substrate.width,  # y
        0.0 / xm    # z
    ]
    config.src_center = [
        0.0,    # x
        0.0,    # y
        config.cell_size[2]/2.0-1.15*config.pml  # z
    ]

    config.nfreq = 500
    config.z_reflection = config.cell_size[2]/2.0-1.20*config.pml
    config.z_transmission = -(config.cell_size[2]/2.0-1.15*config.pml)

    antenna_vols = VolumeSetROI(cell, antenna=AuTop)

    sim = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=geometry,
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )
    sim_empty = mp.Simulation(
        cell_size=cell,
        boundary_layers=[mp.PML(config.pml)],
        geometry=[],
        sources=make_source(config),
        resolution = config.resolution,
        k_point = mp.Vector3(),
        symmetries=config.symmetries,
        dimensions=3
        )

    # =====================================================
    print_task(4, "Postprocesing - raw animations for X.")
    animate_raw_fields(config=config, mode="BOTH", component="X")
    # =====================================================
    print_task(4, "Postprocesing - raw animations for Y.")
    animate_raw_fields(config=config, mode="BOTH", component="Y")
    # =====================================================
    print_task(4, "Postprocesing - raw animations for Z.")
    animate_raw_fields(config=config, mode="BOTH", component="Z")
    # =====================================================
    print_task(3, "3D calculations.")
    compute_fields(
        sim,
        sim_empty,
        antenna_vols,
        config,
        fluxes=False,
        scattering=False,
        dft_gap_spectrum=False,
        harminv=False,
        scattering_antenna=AuTop,
        mode="ENH_ONLY"
    )
    # =====================================================
    draw_params = {
        "XY": {"x_zoom": 1,
                "y_zoom": 1,
                "roi": {
                    "center": (0, 0),
                    "width": AuTop.gap * 1.05 * 1e3,
                    "height": AuTop.radius * 2.1 * 1e3,
                },
        },
        "XZ": {"x_zoom": 1,
                "y_zoom": 1,
                "roi": {
                    "center": (0, 0),
                    "width": AuTop.gap * 1.05 * 1e3,
                    "height": AuTop.thickness * 1e3,
                },
        },
        "YZ": {"x_zoom": 0.25,
                "y_zoom": 1,
                "roi": {
                    "center": (0, 0),
                    "width": AuTop.radius * 2.1 * 1e3,
                    "height": AuTop.thickness * 1e3,
                },
        },
    }
    print_task(5, "Postprocesing - animations and plots.")
    animate_enhancement_fields(config=config, volumes=antenna_vols, draw_params=draw_params, animate=True)
    # =====================================================
    plot_signal_amplitude_vs_time_from_h5(
        "xyplanar-empty_ex.h5",
        load_h5data_path=config.path_to_save,
        xzeros=0,
        time_step=config.sim_time_step,
        save_name=f"source_prof_empty"
    )
    plot_signal_amplitude_vs_time_from_h5(
        "xyplanar_ex.h5",
        load_h5data_path=config.path_to_save,
        xzeros=0,
        time_step=config.sim_time_step,
        save_name=f"source_prof_antenna"
    ) 
    return 0

def split_bar_AuTiX():
    # =====================================================
    config = SimulationConfig()

    config.resolution = 400
    config.sim_time = 25000 / xm
    config.sim_time_step = 50 / xm
    config.lambda0 = 1200 / xm
    config.frequency_width = 0.6

    gap = 30

    X_materials = [Cu, Be, Cr, Pt, W] #SiO2, mp.air, Au,
    X_material_names = ["Cu", "Be", "Cr", "Pt", "W"] #"SiO2","Air", "Au",
    for X_material, X_material_name in zip(X_materials, X_material_names):
        SIM_NAME = f"split_bar_antenna_AuTi{X_material_name}_res{config.resolution}"
        config.path_to_save, config.animations_folder_path = create_directory(SIM_NAME)
        # =====================================================
        AuTop = SplitBar(
            gap=gap/xm,
            length=300/xm,
            width=50/xm,
            thickness=30/xm,
            material=Au,
            z_offset=0.0/xm,
            radius=0/xm,
        )
        TiBetween = SplitBar(
            gap=gap/xm,
            length=300/xm,
            width=50/xm,
            thickness=5/xm,
            material=Ti,
            z_offset=-(30+5)/2.0/xm,
            radius=0/xm,
        )
        substrate = Bar(
            length=1000/xm,
            width=200/xm,
            thickness=70/xm,
            material=X_material,
            z_offset=-(30/2.0+5+70/2.0)/xm,
            radius=12/xm,
        )

        geometry = AuTop.build_geometry() + TiBetween.build_geometry() + substrate.build_geometry()

        config.pad = 100/xm
        config.pml = 350/xm
        config.cell_size = [
            substrate.length + 2*config.pad + 2*config.pml,   # x
            substrate.width + 2*config.pad + 2*config.pml,   # y
            substrate.thickness+AuTop.thickness+TiBetween.thickness + 2*config.pad + 2*config.pml    # z
        ]
        cell = make_cell(config=config)

        config.src_size = [
            substrate.length,  # x
            substrate.width,  # y
            0.0 / xm    # z
        ]
        config.src_center = [
            0.0,    # x
            0.0,    # y
            config.cell_size[2]/2.0-1.15*config.pml  # z
        ]

        config.nfreq = 500
        config.z_reflection = config.cell_size[2]/2.0-1.20*config.pml
        config.z_transmission = -(config.cell_size[2]/2.0-1.15*config.pml)


        antenna_vols = VolumeSet(cell, antenna=AuTop, top_z=AuTop.thickness, extra_vols_in_gap=False)

        # save_and_show_config(config, [AuTop, TiBetween, substrate])

        sim = mp.Simulation(
            cell_size=cell,
            boundary_layers=[mp.PML(config.pml)],
            geometry=geometry,
            sources=make_source(config),
            resolution = config.resolution,
            k_point = mp.Vector3(),
            symmetries=config.symmetries,
            dimensions=3
            )
        sim_empty = mp.Simulation(
            cell_size=cell,
            boundary_layers=[mp.PML(config.pml)],
            geometry=[],
            sources=make_source(config),
            resolution = config.resolution,
            k_point = mp.Vector3(),
            symmetries=config.symmetries,
            dimensions=3
            )
        # # =====================================================
        # print_task(1, "2D projections.")
        # for plane in ["XY", "XZ", "YZ"]:
        #     Name2D = f"antenna_{plane}.png"
        #     save_2D_plot(
        #         sim,
        #         antenna_vols.vis_volume[plane],
        #         save_name=Name2D,
        #         path_to_save=config.path_to_save,
        #         IMG_CLOSE=config.IMG_CLOSE
        #     )
        # =====================================================
        print_task(3, "3D calculations.")
        compute_fields(sim, sim_empty, antenna_vols, config)
        # =====================================================
        print_task(4, "Postprocesing - raw animations.")
        animate_raw_fields(config=config, mode="BOTH")
        # =====================================================
        draw_params = {
            "XY": {"x_zoom": 0.10,
                    "y_zoom": 0.3,
                    "roi": {
                        "center": (0, 0),
                        "width": AuTop.gap * 1e3,
                        "height": AuTop.width * 1e3,
                    },
            },
            "XZ": {"x_zoom": 0.1,
                    "y_zoom": 0.2,
                    "roi": {
                        "center": (0, -1e3*TiBetween.thickness/2.0),
                        "width": AuTop.gap * 1e3,
                        "height": (AuTop.thickness + TiBetween.thickness) * 1e3,
                    },
            },
            "YZ": {"x_zoom": 0.4,
                    "y_zoom": 0.2,
                    "roi": {
                        "center": (0, -1e3*TiBetween.thickness/2.0),
                        "width": AuTop.width * 1e3,
                        "height": (AuTop.thickness + TiBetween.thickness) * 1e3,
                    },
            },
        }
        print_task(5, "Postprocesing - animations and plots.")
        animate_enhancement_fields(config=config, draw_params=draw_params)
        # =====================================================
        plot_signal_amplitude_vs_time_from_h5(
            "xyplanar-empty_ex.h5",
            load_h5data_path=config.path_to_save,
            xzeros=int(100),
            time_step=config.sim_time_step,
            save_name=f"source_prof_empty"
        )
        plot_signal_amplitude_vs_time_from_h5(
            "xyplanar_ex.h5",
            load_h5data_path=config.path_to_save,
            xzeros=int(100),
            time_step=config.sim_time_step,
            save_name=f"source_prof_antenna"
        ) 
    return 0

def split_bar_AuTiSiO2():
    # =====================================================
    config = SimulationConfig()
    config.resolution = 500
    config.sim_time = 8000 / xm
    config.sim_time_step = 100 / xm
    config.lambda0 = 8100 / xm
    config.frequency_width = 1

    for gap in [10]:
        for T in [20, 25, 30, 35, 40]: #, 40
            SIM_NAME = f"T_{T}_split_bar_antenna_gap_{gap}nm_AuTiSiO2_test"
            config.path_to_save, config.animations_folder_path = create_directory(SIM_NAME)
            # =====================================================
            AuTop = SplitBar(
                gap=gap/xm,
                length=1800/xm,
                width=240/xm,
                thickness=T/xm,
                material=Au,
                z_offset=0.0/xm,
                radius=0/xm,
            )
            TiBetween = SplitBar(
                gap=gap/xm,
                length=1800/xm,
                width=240/xm,
                thickness=5/xm,
                material=Ti,
                # material=Pd,
                z_offset=-(T+5)/2.0/xm,
                radius=0/xm,
            )
    # 
    #         # !! PADS !! #########
    #         AuTopPAD = SplitBar(
    #             gap=(gap+1700*2)/xm,
    #             length=100/xm,
    #             width=40/xm,
    #             thickness=30/xm,
    #             material=Au,
    #             z_offset=0.0/xm,
    #             radius=0/xm,
    #             center=(0.0, (20+240/2.0)/xm)
    #         )
    #         TiBetweenPAD = SplitBar(
    #             gap=(gap+1700*2)/xm,
    #             length=100/xm,
    #             width=40/xm,
    #             thickness=5/xm,
    #             material=Ti,
    #             # material=Pd,
    #             z_offset=-(30+5)/2.0/xm,
    #             radius=0/xm,
    #             center=(0.0, (20+240/2.0)/xm)
    #         )
            #########################
            
            substrate = Bar(
                length=4000/xm,
                width=320/xm,
                thickness=70/xm,
                material=SiO2,
                z_offset=-(T/2.0+5+70/2.0)/xm,
                radius=12/xm,
            )

            # geometry = AuTop.build_geometry() + TiBetween.build_geometry() + AuTopPAD.build_geometry() + TiBetweenPAD.build_geometry() + substrate.build_geometry()
            geometry = AuTop.build_geometry() + TiBetween.build_geometry() + substrate.build_geometry()

            config.pad = 100/xm
            config.pml = 100/xm
            config.cell_size = [
                substrate.length + 2*config.pad + 2*config.pml,   # x
                substrate.width + 2*config.pad + 2*config.pml,   # y
                substrate.thickness+AuTop.thickness+TiBetween.thickness + 2*config.pad + 2*config.pml    # z
            ]
            cell = make_cell(config=config)

            config.src_size = [
                substrate.length,  # x
                substrate.width,  # y
                0.0 / xm    # z
            ]
            config.src_center = [
                0.0,    # x
                0.0,    # y
                config.cell_size[2]/2.0-1.15*config.pml  # z
            ]

            antenna_vols = VolumeSet(cell, antenna=AuTop, top_z=AuTop.thickness)


            sim = mp.Simulation(
                cell_size=cell,
                boundary_layers=[mp.PML(config.pml)],
                geometry=geometry,
                sources=make_source(config),
                resolution = config.resolution,
                k_point = mp.Vector3(),
                symmetries=config.symmetries,
                dimensions=3
                )
            sim_empty = mp.Simulation(
                cell_size=cell,
                boundary_layers=[mp.PML(config.pml)],
                geometry=[],
                sources=make_source(config),
                resolution = config.resolution,
                k_point = mp.Vector3(),
                symmetries=config.symmetries,
                dimensions=3
                )
                
            # # =====================================================                
            # save_and_show_config(config, [AuTop, TiBetween, substrate])
            # # =====================================================
            # print_task(1, "2D projections.")
            # for plane in ["XY", "XZ", "YZ"]:
            #     Name2D = f"antenna_{plane}.png"
            #     save_2D_plot(
            #         sim,
            #         antenna_vols.vis_volume[plane],
            #         save_name=Name2D,
            #         path_to_save=config.path_to_save,
            #         IMG_CLOSE=config.IMG_CLOSE
            #     )
            # # =====================================================
            # print_task(3, "3D calculations.")
            # compute_fields(
            #     sim,
            #     sim_empty,
            #     antenna_vols,
            #     config,
            #     fluxes=False,
            #     scattering=False,
            # )
            # # =====================================================
            # print_task(4, "Postprocesing - raw animations.")
            # animate_raw_fields(config=config, mode="BOTH")
            # # =====================================================
            draw_params = {
                "XY": {"x_zoom": 0.045,
                       "y_zoom": 0.6,
                       "roi": {
                            "center": (0, 0),
                            "width": AuTop.gap * 1e3,
                            "height": AuTop.width * 1e3,
                        },
                },
                "XZ": {"x_zoom": 0.045,
                       "y_zoom": 0.2,
                       "roi": {
                            "center": (0, -1e3*TiBetween.thickness/2.0),
                            "width": AuTop.gap * 1e3,
                            "height": (AuTop.thickness + TiBetween.thickness) * 1e3,
                        },
                },
                "YZ": {"x_zoom": 0.4,
                       "y_zoom": 0.2,
                       "roi": {
                            "center": (0, -1e3*TiBetween.thickness/2.0),
                            "width": AuTop.width * 1e3,
                            "height": (AuTop.thickness + TiBetween.thickness) * 1e3,
                        },
                },
            }
            print_task(5, "Postprocesing - animations and plots.")
            animate_enhancement_fields(config=config, volumes=antenna_vols, draw_params=draw_params, animate=False)
            # # =====================================================
            # plot_signal_amplitude_vs_time_from_h5(
            #     "xyplanar-empty_ex.h5",
            #     load_h5data_path=config.path_to_save,
            #     xzeros=int(100),
            #     time_step=config.sim_time_step,
            #     save_name=f"source_prof_empty"
            # )
            # plot_signal_amplitude_vs_time_from_h5(
            #     "xyplanar_ex.h5",
            #     load_h5data_path=config.path_to_save,
            #     xzeros=int(100),
            #     time_step=config.sim_time_step,
            #     save_name=f"source_prof_antenna"
            # )
                
    return 0
