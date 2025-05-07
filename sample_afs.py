import argparse
import os
import random
import shutil
from pathlib import Path


def sample_frameworks(afs_dir, solutions_dir, output_dir, num_samples=50):
    """
    Randomly selects frameworks and their solutions, ensuring completeness.

    Args:
        afs_dir: Path to the directory containing framework files (e.g., .gml, .pddl, afinput).
        solutions_dir: Path to the directory containing solution files.
        output_dir: Path to the directory where the selected frameworks and solutions will be copied.
        num_samples: The number of frameworks to sample.
    """

    afs_path = Path(afs_dir)
    solutions_path = Path(solutions_dir)
    output_path = Path(output_dir)

    if not afs_path.is_dir():
        raise ValueError(f"AFS directory '{afs_dir}' does not exist or is not a directory.")
    if not solutions_path.is_dir():
        raise ValueError(f"Solutions directory '{solutions_dir}' does not exist or is not a directory.")
    output_path.mkdir(parents=True, exist_ok=True)

    eligible_frameworks = []
    for filename in os.listdir(afs_path):
        if ".gml" in filename or ".pddl" in filename or "afinput" in filename:
            solution_base_name = filename
            if not solution_base_name:
                continue # Should not happen, but for robustness

            # Check for corresponding solution files
            txt_exists = (solutions_path / f"{solution_base_name}.txt").exists()
            ee_co_exists = (solutions_path / f"{solution_base_name}.apx.EE-CO").exists()
            ee_st_exists = (solutions_path / f"{solution_base_name}.apx.EE-ST").exists()

            if txt_exists and ee_co_exists and ee_st_exists:
                eligible_frameworks.append(filename)

    if not eligible_frameworks:
        raise ValueError("No eligible frameworks found with complete solutions.")

    print(f"Found {len(eligible_frameworks)} eligible frameworks.")

    num_samples = min(num_samples, len(eligible_frameworks))
    selected_frameworks = random.sample(eligible_frameworks, num_samples)
    print(f"Selected {num_samples} frameworks.")

    copied_count = 0
    for framework_filename in selected_frameworks:
        framework_src = afs_path / framework_filename
        framework_dest = output_path / framework_filename
        shutil.copy2(framework_src, framework_dest)

        solution_base_name = framework_filename
        if not solution_base_name: # Safety check, should not happen
            continue

        for ext in [".txt", ".apx.EE-CO", ".apx.EE-ST"]:
            solution_src = solutions_path / f"{solution_base_name}{ext}"
            solution_dest = output_path / f"{solution_base_name}{ext}"
            if solution_src.exists():
                shutil.copy2(solution_src, solution_dest)
        copied_count += 1
    print(f"Copied {copied_count} frameworks and their solutions to '{output_dir}'.")


def main():
    parser = argparse.ArgumentParser(description="Randomly sample frameworks and their solutions.")
    parser.add_argument("afs_dir", help="Path to the directory containing framework files.")
    parser.add_argument("solutions_dir", help="Path to the directory containing solution files.")
    parser.add_argument("output_dir", help="Path to the output directory.")
    parser.add_argument("-n", "--num_samples", type=int, default=50, help="Number of frameworks to sample (default: 50).")
    args = parser.parse_args()

    try:
        sample_frameworks(args.afs_dir, args.solutions_dir, args.output_dir, args.num_samples)
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()