import datetime
from typing import List
import subprocess
from pathlib import Path
from argparse import ArgumentParser
import hashlib
import base64


def hash_job_parameters(
    l1_cache_size: str,
    l2_cache_size: str,
    l1_cache_associativity: int,
    l2_cache_associativity: int,
    # Must be: 1, 2 or 3.
    multiplication_program_version: int,
):
    job_param_hash = hashlib.new("md5")

    job_param_hash.update(l1_cache_size.encode("utf8"))
    job_param_hash.update(l2_cache_size.encode("utf8"))
    job_param_hash.update(str(l1_cache_associativity).encode("utf8"))
    job_param_hash.update(str(l2_cache_associativity).encode("utf8"))
    job_param_hash.update(str(multiplication_program_version).encode("utf8"))

    return base64.b64encode(job_param_hash.digest()).decode("utf-8")[:6]


def prepare_and_save_job_script(
    l1_cache_size: str,
    l2_cache_size: str,
    l1_cache_associativity: int,
    l2_cache_associativity: int,
    # Must be: 1, 2 or 3.
    multiplication_program_version: int,
    job_script_output_base_directory_path: Path,
    benchmark_output_base_directory_path: Path
) -> Path:
    assert multiplication_program_version in [1, 2, 3]

    print("  > generating job details")

    job_parameter_hash = hash_job_parameters(
        l1_cache_size=l1_cache_size,
        l2_cache_size=l2_cache_size,
        l1_cache_associativity=l1_cache_associativity,
        l2_cache_associativity=l2_cache_associativity,
        multiplication_program_version=multiplication_program_version
    )

    job_script_file_name: str = \
        f"cache-benchmark_L1-{l1_cache_size}-{l1_cache_associativity}" \
        f"_L2-{l2_cache_size}-{l2_cache_associativity}" \
        f"_{multiplication_program_version}"

    job_log_file_path = job_script_output_base_directory_path.resolve().joinpath(f"{job_script_file_name}.log")
    
    job_script_file_path = job_script_output_base_directory_path.joinpath(f"{job_script_file_name}.sh")


    benchmark_output_concrete_directory_path = benchmark_output_base_directory_path.resolve().joinpath(
        f"L1-{l1_cache_size}-{l1_cache_associativity}" \
        f"_L2-{l2_cache_size}-{l2_cache_associativity}" \
        f"_{multiplication_program_version}"
    )

    benchmark_output_concrete_directory_path.mkdir(parents=True)


    job_script = f"""#!/bin/bash
#SBATCH --reservation=fri
#SBATCH --job-name=rs-cache-perf_{job_parameter_hash}
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=\"{job_log_file_path.as_posix()}\"
#SBATCH --time=00:18:00

GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_ROOT=$GEM5_WORKSPACE/gem5
GEM_PATH=$GEM5_ROOT/build/X86

srun apptainer exec $GEM5_WORKSPACE/gem5.sif $GEM_PATH/gem5.opt \\
    --outdir=\"{benchmark_output_concrete_directory_path.as_posix()}\" cache_benchmark.py \\
        --l1_size=\"{l1_cache_size}\" --l2_size=\"{l2_cache_size}\" \\
        --l1_assoc=\"{l1_cache_associativity}\" --l2_assoc=\"{l2_cache_associativity}\" \\
        --mult_version=\"{multiplication_program_version}\"

"""

    assert not job_script_file_path.exists()

    print("  > saving script to temporary file")

    with job_script_file_path.open(mode="w", encoding="utf8") as script_file:
        script_file.write(job_script)
    
    return job_script_file_path


def prepare_and_queue_job(
    l1_cache_size: str,
    l2_cache_size: str,
    l1_cache_associativity: int,
    l2_cache_associativity: int,
    # Must be: 1, 2 or 3.
    multiplication_program_version: int,
    job_script_output_directory_path: Path,
    benchmark_output_directory_path: Path
):
    print("Preparing job:")
    print(f"  L1: {l1_cache_size} ({l1_cache_associativity} associativity)")
    print(f"  L2: {l2_cache_size} ({l2_cache_associativity} associativity)")
    print(f"  Workload: mat_mult{multiplication_program_version}.bin")

    job_script_file_path = prepare_and_save_job_script(
        l1_cache_size=l1_cache_size,
        l2_cache_size=l2_cache_size,
        l1_cache_associativity=l1_cache_associativity,
        l2_cache_associativity=l2_cache_associativity,
        multiplication_program_version=multiplication_program_version,
        job_script_output_base_directory_path=job_script_output_directory_path,
        benchmark_output_base_directory_path=benchmark_output_directory_path
    )

    print("  > submitting via sbatch")

    submission_process = subprocess.run(
        args=["sbatch", job_script_file_path.resolve().as_posix()],
        capture_output=True,
        encoding="utf-8"
    )

    submission_process_stdout = str(submission_process.stdout)
    if not submission_process_stdout.startswith("Submitted batch job") or submission_process.returncode != 0:
        raise RuntimeError(f"failed to submit (code {submission_process.returncode}): {submission_process_stdout}")
    
    job_id = int(submission_process_stdout.rsplit(" ", maxsplit=1)[1])

    print(f"  > submitted as job {job_id}")
    print()




L1_CACHE_SIZES: List[str] = [
    "1 KiB",
    "2 KiB",
    "4 KiB",
    "8 KiB"
]

L2_CACHE_SIZES: List[str] = [
    "32 KiB",
    "64 KiB"
]

MAT_MULT_PROGRAM_VERSIONS: List[int] = [
    1,
    2,
    3
]


def main():
    argument_parser = ArgumentParser()
    
    argument_parser.add_argument(
        "--output-directory-path",
        required=True,
        dest="output_directory_path"
    )

    arguments = argument_parser.parse_args()

    output_directory_path: Path = Path(str(arguments.output_directory_path))

    formatted_timestamp: str = datetime.datetime.now().strftime(r"%Y-%m-%d_%H-%M-%S")
    timestamped_output_directory_path = output_directory_path.joinpath(f"run_{formatted_timestamp}")

    if timestamped_output_directory_path.exists():
        print("Output directory already exists (you ran the tool twice in a second), retry in one second.")
        exit(1)

    timestamped_output_directory_path.mkdir(parents=True, exist_ok=False)


    job_scripts_base_directory_path: Path = timestamped_output_directory_path.joinpath("scripts")
    job_scripts_base_directory_path.mkdir(parents=True, exist_ok=False)

    benchmark_results_base_directory_path: Path = timestamped_output_directory_path.joinpath("benchmarks")
    benchmark_results_base_directory_path.mkdir(parents=True, exist_ok=False)

    for l1_cache_size in L1_CACHE_SIZES:
        for l2_cache_size in L2_CACHE_SIZES:
            for program_version in MAT_MULT_PROGRAM_VERSIONS:
                prepare_and_queue_job(
                    l1_cache_size=l1_cache_size,
                    l2_cache_size=l2_cache_size,
                    l1_cache_associativity=16,
                    l2_cache_associativity=16,
                    multiplication_program_version=program_version,
                    job_script_output_directory_path=job_scripts_base_directory_path,
                    benchmark_output_directory_path=benchmark_results_base_directory_path
                )

    print("DONE")

if __name__ == "__main__":
    main()
