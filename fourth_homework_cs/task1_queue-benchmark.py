from argparse import ArgumentParser
import base64
from dataclasses import dataclass
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Dict, List, Literal, Union


@dataclass(frozen=True, kw_only=True)
class JobParameters:
    implementation: Union[Literal["naive"], Literal["optimized"]]
    number_of_compute_units: int

    def to_dict(self) -> Dict[str, Union[str, int, float]]:
        return {
            "number_of_compute_units": self.number_of_compute_units,
            "implementation": self.implementation,
        }

    def write_to_file(self, file_path: Path):
        if file_path.exists():
            raise FileExistsError("File already exists.")

        with file_path.open(mode="w", encoding="utf8") as file:
            file.write(json.dumps(self.to_dict(), indent=4))

    def hash_to_str(self) -> str:
        job_param_hash = hashlib.new("md5")

        job_param_hash.update(str(self.implementation).encode("utf8"))
        job_param_hash.update(str(self.number_of_compute_units).encode("utf8"))

        full_hash: str = base64.b64encode(job_param_hash.digest()).decode("utf-8")
        alphanumeric_hash: str = "".join(character for character in full_hash if character.isalnum())

        return alphanumeric_hash[:12]


def prepare_and_save_job_script(
    job_parameters: JobParameters,
    base_directory_path: Path,
    job_script_output_directory_path: Path,
    job_output_directory_path: Path
) -> Path:
    print("  > generating job script")

    job_hash = job_parameters.hash_to_str()

    job_full_name = f"t1-gpukernels_{job_hash}"

    job_output_directory: Path = job_output_directory_path.resolve().joinpath(job_full_name)

    assert not job_output_directory.exists()
    job_output_directory.mkdir(parents=True, exist_ok=False)

    job_script_file_path: Path = job_script_output_directory_path.joinpath(f"{job_full_name}.sh")
    job_log_file_path: Path = job_output_directory.joinpath(f"{job_full_name}.log")
    job_err_file_path: Path = job_output_directory.joinpath(f"{job_full_name}.err")
    job_metadata_file_path: Path = job_output_directory.joinpath(f"{job_full_name}.json")

    job_parameters.write_to_file(job_metadata_file_path)

    path_to_binary: Path
    if job_parameters.implementation == "naive":
        path_to_binary = base_directory_path.resolve().joinpath("task1/histogram/bin/histogram_naive")
    elif job_parameters.implementation == "optimized":
        path_to_binary = base_directory_path.resolve().joinpath("task1/histogram/bin/histogram_opt")
    else:
        raise RuntimeError(f"unexpected implementation: {job_parameters.implementation}")


    job_script = f"""#!/bin/bash
#SBATCH --reservation=fri
#SBATCH --job-name=rs-hw4_t1-{job_hash}
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output="{job_log_file_path.as_posix()}"
#SBATCH --error="{job_err_file_path.as_posix()}"
#SBATCH --time=01:00:00

set -e
set -x

GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_ROOT=$GEM5_WORKSPACE/gem5
GEM5_PATH=$GEM5_ROOT/build/VEGA_X86/

APPTAINER_LOC=/d/hpc/projects/FRI/GEM5/gem5_workspace
APPTAINER_IMG=$APPTAINER_LOC/gcn-gpu_v24-0.sif

echo "Running smp_benchmark.py"
srun apptainer exec $APPTAINER_IMG $GEM5_PATH/gem5.opt \\
    --outdir="{job_output_directory.as_posix()}" \\
        $GEM5_ROOT/configs/example/apu_se.py \\
            -n 3 --num-compute-units {job_parameters.number_of_compute_units} \\
            --gfx-version="gfx902" \\
            -c "{path_to_binary.as_posix()}"
"""


    assert not job_script_file_path.exists()

    print("  > saving script to file")

    with job_script_file_path.open(mode="w", encoding="utf8") as script_file:
        script_file.write(job_script)

    return job_script_file_path


def prepare_and_queue_job(
    job_parameters: JobParameters,
    base_directory_path: Path,
    job_script_output_directory_path: Path,
    job_log_output_directory_path: Path
) -> None:
    print("Preparing job:")
    print(f"  | compute units: {job_parameters.number_of_compute_units}")
    print("  |")
    print("  > preparing script")

    job_script_file_path = prepare_and_save_job_script(
        job_parameters=job_parameters,
        base_directory_path=base_directory_path,
        job_script_output_directory_path=job_script_output_directory_path,
        job_output_directory_path=job_log_output_directory_path
    )

    print("  > submitting task with sbatch")

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
    base_directory_path: Path
    output_directory_path: Path

def parse_cli_arguments() -> CLIArguments:
    argument_parser = ArgumentParser()

    argument_parser.add_argument(
        "--base-directory-path",
        required=False,
        default=".",
        dest="base_directory_path"
    )

    argument_parser.add_argument(
        "--output-directory-path",
        required=True,
        dest="output_directory_path"
    )

    arguments = argument_parser.parse_args()

    base_directory_path: Path = Path(str(arguments.base_directory_path)).resolve()
    output_directory_path: Path = Path(str(arguments.output_directory_path))

    return CLIArguments(
        base_directory_path=base_directory_path,
        output_directory_path=output_directory_path
    )


def prepare_timestamped_output_directory(output_directory_path: Path) -> Path:
    formatted_timestamp: str = datetime.datetime.now().strftime(r"%Y-%m-%d_%H-%M-%S")
    timestamped_output_directory_path = output_directory_path.joinpath(f"run_{formatted_timestamp}")

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


def prepare_individual_output_paths(timestamped_output_directory_path: Path) -> OutputPaths:
    job_script_output_directory_path: Path = timestamped_output_directory_path.joinpath("scripts")
    job_script_output_directory_path.mkdir(parents=True, exist_ok=False)

    job_log_output_directory_path: Path = timestamped_output_directory_path.joinpath("logs")
    job_log_output_directory_path.mkdir(parents=True, exist_ok=False)

    return OutputPaths(
        job_script_output_directory_path=job_script_output_directory_path,
        job_log_output_directory_path=job_log_output_directory_path,
    )


def main() -> None:
    cli_arguments = parse_cli_arguments()

    timestamped_output_directory = prepare_timestamped_output_directory(cli_arguments.output_directory_path)
    output_paths = prepare_individual_output_paths(timestamped_output_directory)

    IMPLEMENTATIONS_TO_TEST: List[str] = ["naive", "optimized"]

    NUMBER_OF_COMPUTE_UNITS_TO_TEST: List[int] = [
        2,
        4,
        8,
    ]

    for implementation in IMPLEMENTATIONS_TO_TEST:
        for num_compute_units in NUMBER_OF_COMPUTE_UNITS_TO_TEST:
            prepare_and_queue_job(
                job_parameters=JobParameters(
                    implementation=implementation, # type: ignore
                    number_of_compute_units=num_compute_units
                ),
                base_directory_path=cli_arguments.base_directory_path,
                job_script_output_directory_path=output_paths.job_script_output_directory_path,
                job_log_output_directory_path=output_paths.job_log_output_directory_path,
            )

    print("DONE!")


if __name__ == "__main__":
    main()
