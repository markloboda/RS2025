from argparse import ArgumentParser
import os
from pathlib import Path
from dataclasses import dataclass
import re
from typing import List, Self, Tuple


def find_and_extract_int_statistic(
    stats_txt_content: str,
    statistic_name: str,
) -> int:
    for line in stats_txt_content.splitlines(keepends=False):
        if line.startswith(statistic_name):
            line_without_property_name: str = line.removeprefix(statistic_name).lstrip(" ").lstrip("\t")
            statistic_value_str = line_without_property_name.split(" ", maxsplit=1)[0]

            return int(statistic_value_str)


    raise ValueError(f"No such statistic: {statistic_name}")


def find_and_extract_float_statistic(
    stats_txt_content: str,
    statistic_name: str,
) -> float:
    for line in stats_txt_content.splitlines(keepends=False):
        if line.startswith(statistic_name):
            line_without_property_name: str = line.removeprefix(statistic_name).lstrip(" ").lstrip("\t")
            statistic_value_str = line_without_property_name.split(" ", maxsplit=1)[0]

            return float(statistic_value_str)


    raise ValueError(f"No such statistic: {statistic_name}")



@dataclass(frozen=True, kw_only=True)
class RunSetupParameters:
    width: str
    rob_size: str
    num_int_regs: str
    num_fp_regs: str

    @classmethod
    def from_directory_path(cls, run_results_directory_path: Path) -> Self:
        directory_name: list[str] = run_results_directory_path.name.split("_")

        if len(directory_name) != 5:
            raise ValueError(f"Invalid directory name: {run_results_directory_path.name}")

        width = directory_name[1]
        rob_size = directory_name[2]
        num_int_regs = directory_name[3]
        num_fp_regs = directory_name[4]

        return cls(
            width=width,
            rob_size=rob_size,
            num_int_regs=num_int_regs,
            num_fp_regs=num_fp_regs,
        )



@dataclass(frozen=True, kw_only=True)
class RunResults:
    # (board.processor.cores.core.cpi)
    cycles_per_instruction: float

    # (board.processor.cores.core.ipc)
    instructions_per_cycle: float

    # (board.processor.cores.core.numCycles)
    total_cycles: int

    @classmethod
    def from_directory_path(cls, directory_path: Path) -> Self:
        stats_txt_path = directory_path.joinpath("stats.txt")
        if not stats_txt_path.is_file():
            raise FileNotFoundError(f"No stats.txt in {directory_path}!")

        with stats_txt_path.open(mode="r", encoding="utf-8") as stats_file:
            stats_file_contents = stats_file.read()
            return cls.from_stats_txt(stats_file_contents)

    @classmethod
    def from_stats_txt(cls, stats_txt_content: str) -> Self:
        def extract_int(statistic_name: str) -> int:
            return find_and_extract_int_statistic(stats_txt_content, statistic_name)

        def extract_float(statistic_name: str) -> float:
            return find_and_extract_float_statistic(stats_txt_content, statistic_name)

        cycles_per_instruction = extract_float("board.processor.cores.core.cpi")
        instructions_per_cycle = extract_float("board.processor.cores.core.ipc")

        total_cycles = extract_int("board.processor.cores.core.numCycles")

        return cls(
            cycles_per_instruction=cycles_per_instruction,
            instructions_per_cycle=instructions_per_cycle,
            total_cycles=total_cycles
        )

def main():
    argument_parser = ArgumentParser()

    argument_parser.add_argument(
        "--run-directory-path",
        required=True,
        dest="run_directory_path"
    )

    argument_parser.add_argument(
        "--output-directory-path",
        dest="output_directory_path",
        required=True
    )

    arguments = argument_parser.parse_args()


    dir_path: Path = Path(str(arguments.run_directory_path))
    if not dir_path.is_dir():
        print(f"Invalid --run-directory-path, does not exist: {dir_path.as_posix()}")
        exit(1)

    output_directory_path = Path(str(arguments.output_directory_path))

    aggregated_results: List[Tuple[RunSetupParameters, RunResults]] = []

    for dir_entry in os.listdir(dir_path):
        dir_entry_path: Path = dir_path.joinpath(dir_entry)

        if dir_entry_path.is_dir():
            run_parameters = RunSetupParameters.from_directory_path(dir_entry_path)
            run_results = RunResults.from_directory_path(dir_entry_path)

            aggregated_results.append((run_parameters, run_results))

    print(f"Found {len(aggregated_results)} results in provided directory.")
    print()

    def extract_aggregated_result_key(value: Tuple[RunSetupParameters, RunResults]):
        run_setup, _ = value

        return (
            run_setup.width,
            run_setup.rob_size
        )

    sorted_aggregated_results = sorted(
        aggregated_results,
        key=extract_aggregated_result_key
    )

    output: str = ""

    for index, (run_parameters, run_results) in enumerate(sorted_aggregated_results):
        output += f"Run {index + 1}:\n"
        output += f"  Issue Width: {run_parameters.width}\n"
        output += f"  Reorder Buffer Size: {run_parameters.rob_size}\n\n"
        output += f"  > Instructions per cycle (IPC): {run_results.instructions_per_cycle:.3}\n"
        output += f"  > Cycles per instruction (CPI): {run_results.cycles_per_instruction:.3}\n"
        output += f"  > Total cycles: {run_results.total_cycles}\n\n"

    # Write file
    output_file_path: Path = output_directory_path.joinpath("aggregated_results.txt")
    with output_file_path.open(mode="w", encoding="utf-8") as output_file:
        output_file.write(output)

    print(output)
    print("DONE")



if __name__ == "__main__":
    main()
