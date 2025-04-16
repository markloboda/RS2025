from argparse import ArgumentParser
import base64
from dataclasses import dataclass
import datetime
import hashlib
from pathlib import Path
import subprocess
import sys
from typing import List


def hash_job_parameters(
    number_of_processors: int,
    # One of: "crossbar", "ring", "point-to-point".
    interconnection_network_type: str,
) -> str:
    job_param_hash = hashlib.new("md5")

    job_param_hash.update(str(number_of_processors).encode("utf8"))
    job_param_hash.update(interconnection_network_type.encode("utf8"))

    return base64.b64encode(job_param_hash.digest()).decode("utf-8")[:6]



def prepare_and_save_job_script(
    number_of_processors: int,
    # One of: "crossbar", "ring", "point-to-point".
    interconnection_network_type: str,
    job_script_output_directory_path: Path,
    job_log_output_directory_path: Path,
    benchmark_output_base_directory_path: Path
) -> Path:
    print("  > generating job details")

    job_parameter_hash = hash_job_parameters(
        number_of_processors=number_of_processors,
        interconnection_network_type=interconnection_network_type
    )

    job_file_name: str = \
        f"t3-interconnection_{number_of_processors}-cpus_{interconnection_network_type}-network"
    
    job_log_file_path: Path = job_log_output_directory_path.joinpath(
        f"{job_file_name}.log"
    )

    job_script_file_path = job_script_output_directory_path.joinpath(
        f"{job_file_name}.sh"
    )

    benchmark_output_concrete_directory_path: Path = benchmark_output_base_directory_path.joinpath(
        f"{number_of_processors}-cpus_{interconnection_network_type}-network"
    )

    benchmark_output_concrete_directory_path.mkdir(parents=True)


    job_script = f"""#!/bin/bash
#SBATCH --reservation=fri
#SBATCH --job-name=rs-hw2_t3-{job_parameter_hash}
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=\"{job_log_file_path.as_posix()}\"
#SBATCH --time=01:00:00

GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_ROOT=$GEM5_WORKSPACE/gem5
GEM_PATH=$GEM5_ROOT/build/X86

echo "Running network_benchmark.py"
srun apptainer exec $GEM5_WORKSPACE/gem5.sif $GEM_PATH/gem5.opt \\
    --outdir=\"{benchmark_output_concrete_directory_path.as_posix()}\" ./network/network_benchmark.py \\
        --num_cores=\"{number_of_processors}\" \\
        --interconnection-network=\"{interconnection_network_type}\"

"""

    assert not job_script_file_path.exists()

    print("  > saving script to temporary file")

    with job_script_file_path.open(mode="w", encoding="utf8") as script_file:
        script_file.write(job_script)
    
    return job_script_file_path


def prepare_and_queue_job(
    number_of_processors: int,
    # One of: "crossbar", "ring", "point-to-point".
    interconnection_network_type: str,
    job_script_output_directory_path: Path,
    job_log_output_directory_path: Path,
    benchmark_output_base_directory_path: Path
) -> None:
    print("Preparing job:")
    print(f"  > CPUs: {number_of_processors}")

    job_script_file_path = prepare_and_save_job_script(
        number_of_processors=number_of_processors,
        interconnection_network_type=interconnection_network_type,
        job_script_output_directory_path=job_script_output_directory_path,
        job_log_output_directory_path=job_log_output_directory_path,
        benchmark_output_base_directory_path=benchmark_output_base_directory_path
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


@dataclass(frozen=True, kw_only=True)
class CLIArguments:
    output_directory_path: Path

def parse_cli_arguments() -> CLIArguments:
    argument_parser = ArgumentParser()
    
    argument_parser.add_argument(
        "--output-directory-path",
        required=True,
        dest="output_directory_path"
    )

    arguments = argument_parser.parse_args()

    output_directory_path: Path = Path(str(arguments.output_directory_path))

    return CLIArguments(
        output_directory_path=output_directory_path
    )


def prepare_timestamped_output_directory(base_output_directory_path: Path) -> Path:
    formatted_timestamp: str = datetime.datetime.now().strftime(r"%Y-%m-%d_%H-%M-%S")
    timestamped_output_directory_path = base_output_directory_path.joinpath(f"run_{formatted_timestamp}")

    if timestamped_output_directory_path.exists():
        print(
            "Output directory already exists (you ran the tool twice in a second, retry in one second.",
            file=sys.stderr
        )
        
        exit(1)

    timestamped_output_directory_path.mkdir(parents=True, exist_ok=False)

    return timestamped_output_directory_path


@dataclass(frozen=True, kw_only=True)
class OutputPaths:
    job_script_output_directory_path: Path
    job_log_output_directory_path: Path
    benchmark_output_base_directory_path: Path

def prepare_individual_output_paths(timestamped_output_directory_path: Path) -> OutputPaths:
    job_script_output_directory_path: Path = timestamped_output_directory_path.joinpath("scripts")
    job_script_output_directory_path.mkdir(parents=True, exist_ok=False)

    job_log_output_directory_path: Path = timestamped_output_directory_path.joinpath("logs")
    job_log_output_directory_path.mkdir(parents=True, exist_ok=False)

    benchmark_output_base_directory_path: Path = timestamped_output_directory_path.joinpath("results")
    benchmark_output_base_directory_path.mkdir(parents=True, exist_ok=False)

    return OutputPaths(
        job_script_output_directory_path=job_script_output_directory_path,
        job_log_output_directory_path=job_log_output_directory_path,
        benchmark_output_base_directory_path=benchmark_output_base_directory_path
    )


def main() -> None:
    cli_arguments = parse_cli_arguments()

    timestamped_output_directory = prepare_timestamped_output_directory(cli_arguments.output_directory_path)
    output_paths = prepare_individual_output_paths(timestamped_output_directory)


    NUMBER_OF_PROCESSORS_TO_TEST: List[int] = [
        2,
        4,
        8,
        16
    ]

    INTERCONNECTION_NETWORKS_TO_TEST: List[str] = [
        "crossbar",
        "ring",
        "point-to-point"
    ]

    for processor_count in NUMBER_OF_PROCESSORS_TO_TEST:
        for interconnection_network in INTERCONNECTION_NETWORKS_TO_TEST:
            prepare_and_queue_job(
                number_of_processors=processor_count,
                interconnection_network_type=interconnection_network,
                job_script_output_directory_path=output_paths.job_script_output_directory_path,
                job_log_output_directory_path=output_paths.job_log_output_directory_path,
                benchmark_output_base_directory_path=output_paths.benchmark_output_base_directory_path
            )

    print("DONE!")


if __name__ == "__main__":
    main()
