from argparse import ArgumentParser
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Self
import matplotlib.pyplot as plt
import numpy as np


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


@dataclass(frozen=True, kw_only=True, eq=True)
class BinaryUnitSize:
    # E.g. "128 KiB".
    full_string: str

    # E.g. 131072.
    number_of_bytes: int

    @classmethod
    def parse_from_string(cls, string: str) -> Self:
        value, unit = string.split(" ", maxsplit=1)

        if unit == "KiB":
            return cls(
                full_string=string,
                number_of_bytes=int(value) * 1024
            )
        else:
            raise ValueError(f"unexpected unit (expected KiB): {unit}")


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

@dataclass(frozen=True, kw_only=True)
class Run:
    parameters: RunSetupParameters
    results: RunResults

def plot_ipc_against_issue_width(
    results: List[Run],
    output_directory_path: Path
) -> None:
    # Group results by ROB size.
    grouped_results = {}
    for run in results:
        grouped_results.setdefault(run.parameters.rob_size, []).append(run)

    # Sort each group by Issue Width.
    for group in grouped_results.values():
        group.sort(key=lambda x: int(x.parameters.width))

    # Get sorted ROB sizes.
    rob_sizes = sorted(grouped_results.keys(), key=lambda x: int(x))

    # Plot each group as a separate line, sorted by ROB size (ascending).
    plt.figure(figsize=(8, 6))
    for rob_size in rob_sizes:
        runs = grouped_results[rob_size]
        # Extract issue widths and IPC values in sorted order.
        issue_widths = [run.parameters.width for run in runs]
        ipcs = [run.results.instructions_per_cycle for run in runs]
        plt.plot(issue_widths, ipcs, marker='o', label=f"ROB Size {rob_size}")

    plt.xlabel("Issue Width")
    plt.ylabel("IPC (Instructions Per Cycle)")
    plt.title("IPC vs. Issue Width for Various ROB Sizes")
    plt.legend(title="ROB Size", loc="upper left")
    plt.grid(True)

    # Ensure the output directory exists.
    output_directory_path.mkdir(parents=True, exist_ok=True)
    output_file = output_directory_path / "ipc_vs_issue_width.png"
    plt.savefig(output_file)
    plt.close()

def plot_cpi_against_issue_width(
    results: List[Run],
    output_directory_path: Path
) -> None:
    # Group results by ROB size.
    grouped_results = {}
    for run in results:
        grouped_results.setdefault(run.parameters.rob_size, []).append(run)

    # Sort each group by Issue Width.
    for group in grouped_results.values():
        group.sort(key=lambda x: int(x.parameters.width))

    # Get sorted ROB sizes.
    rob_sizes = sorted(grouped_results.keys(), key=lambda x: int(x))

    # Plot each group as a separate line, sorted by ROB size (ascending).
    plt.figure(figsize=(8, 6))
    for rob_size in rob_sizes:
        runs = grouped_results[rob_size]
        # Extract issue widths and CPI values in sorted order.
        issue_widths = [run.parameters.width for run in runs]
        cpis = [run.results.cycles_per_instruction for run in runs]
        plt.plot(issue_widths, cpis, marker='o', label=f"ROB Size {rob_size}")

    plt.xlabel("Issue Width")
    plt.ylabel("CPI (Cycles Per Instruction)")
    plt.title("CPI vs. Issue Width for Various ROB Sizes")
    plt.legend(title="ROB Size", loc="upper left")
    plt.grid(True)

    # Ensure the output directory exists.
    output_directory_path.mkdir(parents=True, exist_ok=True)
    output_file = output_directory_path / "cpi_vs_issue_width.png"
    plt.savefig(output_file)
    plt.close()

def plot_ipc_heatmap(
    results: List[Run],
    output_directory_path: Path
) -> None:
    # Get unique sorted lists of issue widths and ROB sizes.
    issue_widths = sorted({int(run.parameters.width) for run in results})
    rob_sizes = sorted({int(run.parameters.rob_size) for run in results})

    # Initialize a matrix for IPC values.
    ipc_matrix = np.empty((len(rob_sizes), len(issue_widths)))
    ipc_matrix[:] = np.nan  # In case some combinations are missing

    # Populate the matrix.
    for run in results:
        i = rob_sizes.index(int(run.parameters.rob_size))
        j = issue_widths.index(int(run.parameters.width))
        ipc_matrix[i, j] = run.results.instructions_per_cycle

    # Create the heatmap.
    plt.figure(figsize=(8, 6))
    im = plt.imshow(ipc_matrix, aspect='auto', cmap='viridis', origin='lower')
    plt.colorbar(im, label="IPC (Instructions Per Cycle)")

    # Set tick marks and labels.
    plt.xticks(ticks=np.arange(len(issue_widths)), labels=issue_widths)
    plt.yticks(ticks=np.arange(len(rob_sizes)), labels=rob_sizes)
    plt.xlabel("Issue Width")
    plt.ylabel("ROB Size")
    plt.title("Heatmap of IPC across Issue Width and ROB Size")

    # Optionally, annotate each cell with its IPC value.
    for i in range(len(rob_sizes)):
        for j in range(len(issue_widths)):
            value = ipc_matrix[i, j]
            if not np.isnan(value):
                plt.text(j, i, f"{value:.2f}", ha='center', va='center', color='white')

    # Ensure the output directory exists.
    output_directory_path.mkdir(parents=True, exist_ok=True)
    output_file = output_directory_path / "ipc_heatmap.png"
    plt.savefig(output_file)
    plt.close()

def plot_cpi_heatmap(
    results: List[Run],
    output_directory_path: Path
) -> None:
    # Get unique sorted lists of issue widths and ROB sizes.
    issue_widths = sorted({int(run.parameters.width) for run in results})
    rob_sizes = sorted({int(run.parameters.rob_size) for run in results})

    # Initialize a matrix for IPC values.
    ipc_matrix = np.empty((len(rob_sizes), len(issue_widths)))
    ipc_matrix[:] = np.nan  # In case some combinations are missing

    # Populate the matrix.
    for run in results:
        i = rob_sizes.index(int(run.parameters.rob_size))
        j = issue_widths.index(int(run.parameters.width))
        ipc_matrix[i, j] = run.results.cycles_per_instruction

    # Create the heatmap.
    plt.figure(figsize=(8, 6))
    im = plt.imshow(ipc_matrix, aspect='auto', cmap='viridis', origin='lower')
    plt.colorbar(im, label="CPI (Cycles Per Instruction)")

    # Set tick marks and labels.
    plt.xticks(ticks=np.arange(len(issue_widths)), labels=issue_widths)
    plt.yticks(ticks=np.arange(len(rob_sizes)), labels=rob_sizes)
    plt.xlabel("Issue Width")
    plt.ylabel("ROB Size")
    plt.title("Heatmap of CPI across Issue Width and ROB Size")

    # Optionally, annotate each cell with its IPC value.
    for i in range(len(rob_sizes)):
        for j in range(len(issue_widths)):
            value = ipc_matrix[i, j]
            if not np.isnan(value):
                plt.text(j, i, f"{value:.2f}", ha='center', va='center', color='white')

    # Ensure the output directory exists.
    output_directory_path.mkdir(parents=True, exist_ok=True)
    output_file = output_directory_path / "cpi_heatmap.png"
    plt.savefig(output_file)
    plt.close()




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


    run_directory_path: Path = Path(str(arguments.run_directory_path))
    if not run_directory_path.is_dir():
        print(f"Invalid --run-directory-path, does not exist: {run_directory_path.as_posix()}")
        exit(1)

    output_directory_path = Path(str(arguments.output_directory_path))

    aggregated_results: List[Run] = []

    for dir_entry in os.listdir(run_directory_path):
        dir_entry_path: Path = run_directory_path.joinpath(dir_entry)

        if dir_entry_path.is_dir():
            run_parameters = RunSetupParameters.from_directory_path(dir_entry_path)
            run_results = RunResults.from_directory_path(dir_entry_path)

            aggregated_results.append(Run(parameters=run_parameters, results=run_results))

    print(f"Found {len(aggregated_results)} results in provided directory.")
    print()

    plt.style.use("ggplot")

    plot_ipc_against_issue_width(
        results=aggregated_results,
        output_directory_path=output_directory_path
    )

    plot_cpi_against_issue_width(
        results=aggregated_results,
        output_directory_path=output_directory_path
    )

    plot_ipc_heatmap(
        results=aggregated_results,
        output_directory_path=output_directory_path
    )

    plot_cpi_heatmap(
        results=aggregated_results,
        output_directory_path=output_directory_path
    )

    print("DONE")



if __name__ == "__main__":
    main()
