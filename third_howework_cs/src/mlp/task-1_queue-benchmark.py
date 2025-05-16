from argparse import ArgumentParser
import base64
from dataclasses import dataclass
import datetime
import hashlib
from pathlib import Path
import subprocess
import sys
from typing import List, Literal, Union


def hash_job_parameters(precision: Union[Literal["float"], Literal["double"]], hidden_layer_size: int) -> str:
    job_param_hash = hashlib.new("md5")

    job_param_hash.update(precision.encode("utf8"))
    job_param_hash.update(str(hidden_layer_size).encode("utf8"))

    full_hash: str = base64.b64encode(job_param_hash.digest()).decode("utf-8")
    alphanumeric_hash: str = "".join(character for character in full_hash if character.isalnum())

    return alphanumeric_hash[:12]



def prepare_and_save_job_script(
    precision: Union[Literal["float"], Literal["double"]],
    implementation: Union[Literal["sca"], Literal["avx2"]],
    hidden_layer_size: int,
    repetition_index: int,
    mlp_src_directory_path: Path,
    job_output_directory_path: Path,
) -> Path:
    print("  > generating job details")

    job_parameter_hash = hash_job_parameters(
        precision=precision,
        hidden_layer_size=hidden_layer_size
    )

    job_file_name: str = \
        "t1" \
        f"_implementation-{implementation}" \
        f"_precision-{precision}" \
        f"_hidden-layers-{hidden_layer_size}" \
        f"_repetition-{repetition_index}"
    
    job_log_file_path: Path = job_output_directory_path.joinpath(f"{job_file_name}.log")
    job_script_file_path = job_output_directory_path.joinpath(f"{job_file_name}.sh")


    job_script = f"""#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --reservation=fri
#SBATCH --job-name=rs-hw3_t1-{job_parameter_hash}
#SBATCH --output=\"{job_log_file_path.as_posix()}\"
#SBATCH --time=00:20:00

set -e
cd "{mlp_src_directory_path.resolve().as_posix()}"

echo "Running main_test_{precision}_{implementation}.c"
./main_test_{precision}_{implementation} {hidden_layer_size}

echo "Done!"
"""

    assert not job_script_file_path.exists()

    print("  > saving script to temporary file")

    with job_script_file_path.open(mode="w", encoding="utf8") as script_file:
        script_file.write(job_script)
    
    return job_script_file_path


def prepare_and_queue_job(
    precision: Union[Literal["float"], Literal["double"]],
    implementation: Union[Literal["sca"], Literal["avx2"]],
    hidden_layer_size: int,
    repetition_index: int,
    mlp_src_directory_path: Path,
    job_output_directory_path: Path,
) -> None:
    print("Preparing job:")
    print(f"  > precision: {precision}")
    print(f"  > implementation: {implementation}")
    print(f"  > hidden layers: {hidden_layer_size}")
    print(f"  > repetition: {repetition_index}")

    job_script_file_path = prepare_and_save_job_script(
        precision=precision,
        implementation=implementation,
        hidden_layer_size=hidden_layer_size,
        repetition_index=repetition_index,
        mlp_src_directory_path=mlp_src_directory_path,
        job_output_directory_path=job_output_directory_path
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
    mlp_src_directory_path: Path
    output_directory_path: Path

def parse_cli_arguments() -> CLIArguments:
    argument_parser = ArgumentParser()
    
    argument_parser.add_argument(
        "--output-directory-path",
        required=True,
        dest="output_directory_path"
    )

    argument_parser.add_argument(
        "--mlp-src-directory-path",
        required=True,
        dest="mlp_src_directory_path"
    )

    arguments = argument_parser.parse_args()

    output_directory_path: Path = Path(str(arguments.output_directory_path))
    mlp_src_directory_path: Path = Path(str(arguments.mlp_src_directory_path))

    return CLIArguments(
        output_directory_path=output_directory_path,
        mlp_src_directory_path=mlp_src_directory_path
    )


def prepare_timestamped_output_directory(base_output_directory_path: Path) -> Path:
    formatted_timestamp: str = datetime.datetime.now().strftime(r"%Y-%m-%d_%H-%M-%S")
    timestamped_output_directory_path = base_output_directory_path.joinpath(f"benchmark_{formatted_timestamp}")

    if timestamped_output_directory_path.exists():
        print(
            "Output directory already exists (you ran the tool twice in a second, retry in one second.",
            file=sys.stderr
        )
        
        exit(1)

    timestamped_output_directory_path.mkdir(parents=True, exist_ok=False)

    return timestamped_output_directory_path



def main() -> None:
    cli_arguments = parse_cli_arguments()

    timestamped_output_directory = prepare_timestamped_output_directory(cli_arguments.output_directory_path)


    HIDDEN_LAYER_SIZES: List[int] = [
        128,
        256,
        512,
        1024
    ]

    for precision in ["float", "double"]:
        for implementation in ["sca", "avx2"]:
            for hidden_layer_size in HIDDEN_LAYER_SIZES:
                for repetition_index in range(10):
                    prepare_and_queue_job(
                        precision=precision,
                        implementation=implementation,
                        hidden_layer_size=hidden_layer_size,
                        repetition_index=repetition_index,
                        mlp_src_directory_path=cli_arguments.mlp_src_directory_path,
                        job_output_directory_path=timestamped_output_directory
                    )

    print("DONE!")


if __name__ == "__main__":
    main()
