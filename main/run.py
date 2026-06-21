import os
import sys
import argparse
import meep

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

from src.experiments import *


def run():

    meep.Simulation.eps_averaging = False

    # =====================================================
    # CLI arguments
    # =====================================================

    parser = argparse.ArgumentParser(
    description="Run MEEP plasmonic antenna experiments.",
    epilog="""
    Examples:

        python main/run.py --experiment=bowtie_substrate --substrate=Au

        mpirun -np 24 python main/run.py --experiment=bowtie_substrate --substrate=SiO2 --comment="Testing new source position"

        mpirun -np 48 python main/run.py --experiment=bowtie_mir --substrate=Au
        """,
    formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--experiment",
        required=True,
        help="Experiment name"
    )

    parser.add_argument(
        "--substrate",
        default="air",
        help="Substrate material"
    )

    parser.add_argument(
        "--comment",
        default=None,
        help="Optional comment stored in experiment.txt"
    )

    args = parser.parse_args()

    # =====================================================
    # Available experiments
    # =====================================================

    experiments = {
        "bowtie_substrate": bowtie_substrate_experiment,
        "bowtie_lt": bowtie_substrate_experiment_LT,
        "bowtie_mir": bowtie_substrate_experiment_MIR,
        "bowtie_only": bowtie_substrate_ONLY_experiment,
        "redraw": after_hpc_redraw,
        "bowtie_big_substrate": bowtie_big_substrate_experiment,
    }

    if args.experiment not in experiments:

        print("\nAvailable experiments:\n")

        for name in experiments:
            print(f"  {name}")

        raise ValueError(
            f"\nUnknown experiment: {args.experiment}"
        )

    print("=" * 60)
    print(f"Experiment : {args.experiment}")
    print(f"Substrate  : {args.substrate}")
    print(f"Comment    : {args.comment}")
    print("=" * 60)

    experiments[args.experiment](
        args.substrate,
        COMMENT=args.comment
    )


if __name__ == "__main__":
    run()