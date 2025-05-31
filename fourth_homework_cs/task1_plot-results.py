from argparse import ArgumentParser
from dataclasses import dataclass
import datetime
import os
from pathlib import Path
import sys
from typing import Callable, List, Literal, Optional, Union

import matplotlib
import matplotlib.ticker
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure


SIMULATION_BEGIN_MARKER: str = "---------- Begin Simulation Statistics ----------"

def select_simulation_statistic(full_log_file: str, selected_nth_simulation: int) -> str:
    """
    Some stats.txt files contain more than one

    ---------- Begin Simulation Statistics ----------
    [...]
    ---------- End Simulation Statistics   ----------

    block, i.e. more than one set of simulation statistics.

    Given a full log file with one or more of those sections, this function returns 
    a matching subset of the log file (the `nth_simulation`, starting at index 0).
    """

    valid_selected_lines: List[str] = []

    current_simulation_index: Optional[int] = None
    for line in full_log_file.splitlines(keepends=True):
        if line.startswith(SIMULATION_BEGIN_MARKER):
            if current_simulation_index is None:
                current_simulation_index = 0
            else:
                current_simulation_index += 1
        
        if current_simulation_index == selected_nth_simulation:
            valid_selected_lines.append(line)

    # No need for manual newlines, as we used keepends=True when splitting lines.
    return "".join(valid_selected_lines)




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
class RunParameters:
    implementation: Union[Literal["naive"], Literal["optimized"]]
    number_of_compute_units: int

    @classmethod
    def load_from_log_file_path(
        cls,
        log_file_path: Path
    ) -> "RunParameters":
        implementation: Union[Literal["naive"], Literal["optimized"]]
        if "_naive_" in log_file_path.name:
            implementation = "naive"
        elif "_opt" in log_file_path.name:
            implementation = "optimized"
        else:
            raise RuntimeError("Unrecognized implementation.")


        compute_units_str = log_file_path.name.rsplit(".", maxsplit=1)[0].rsplit("_", maxsplit=1)[1]
        number_of_compute_units = int(compute_units_str.lstrip("CU"))

        return cls(
            implementation=implementation,
            number_of_compute_units=number_of_compute_units
        )

    def get_path_to_stats_txt(self, results_directory_path: Path) -> Path:
        impl_abbreviation: str
        if self.implementation == "naive":
            impl_abbreviation = "naive"
        elif self.implementation == "optimized":
            impl_abbreviation = "opt"
        else:
            raise RuntimeError()
        
        return results_directory_path.joinpath(f"{impl_abbreviation}_CU{self.number_of_compute_units}_stats").joinpath("stats.txt")


@dataclass(frozen=True, kw_only=True)
class RunTimings:
    mean_load_latency: float
    avg_executed_vector_alu_instructions: float
    avg_reads_to_shared_memory: float
    avg_writes_to_shared_memory: float
    avg_accesses_of_shared_memory: float
    avg_number_of_cycles: float
    avg_number_of_vectors_per_cycle: float

    @classmethod
    def from_stats_txt_file_path(cls, parameters: RunParameters, stats_txt_file_path: Path) -> "RunTimings":
        with stats_txt_file_path.open(mode="r", encoding="utf-8") as file:
            stats_contents: str = file.read()
        
        stats_contents = select_simulation_statistic(stats_contents, selected_nth_simulation=0)

        mean_load_latency = find_and_extract_float_statistic(stats_contents, "system.cpu3.loadLatencyDist::mean")


        executed_vector_alu_instructions: List[float] = []
        for compute_unit_index in range(parameters.number_of_compute_units):
            executed_vector_alu_instructions.append(
                find_and_extract_float_statistic(stats_contents, f"system.cpu3.CUs{compute_unit_index}.vALUInsts")
            )
        
        avg_executed_vector_alu_instructions: float = sum(executed_vector_alu_instructions) / len(executed_vector_alu_instructions)


        reads_to_shared_memory: List[float] = []
        for compute_unit_index in range(parameters.number_of_compute_units):
            reads_to_shared_memory.append(
                find_and_extract_float_statistic(stats_contents, f"system.cpu3.CUs{compute_unit_index}.groupReads")
            )
        
        avg_reads_to_shared_memory: float = sum(reads_to_shared_memory) / len(reads_to_shared_memory)


        writes_to_shared_memory: List[float] = []
        for compute_unit_index in range(parameters.number_of_compute_units):
            writes_to_shared_memory.append(
                find_and_extract_float_statistic(stats_contents, f"system.cpu3.CUs{compute_unit_index}.groupWrites")
            )
        
        avg_writes_to_shared_memory: float = sum(writes_to_shared_memory) / len(writes_to_shared_memory)


        accesses_of_shared_memory: List[float] = []
        for compute_unit_index in range(parameters.number_of_compute_units):
            accesses_of_shared_memory.append(
                find_and_extract_float_statistic(stats_contents, f"system.cpu3.CUs{compute_unit_index}.ldsBankAccesses")
            )
        
        avg_accesses_of_shared_memory: float = sum(accesses_of_shared_memory) / len(accesses_of_shared_memory)


        cycles: List[float] = []
        for compute_unit_index in range(parameters.number_of_compute_units):
            cycles.append(
                find_and_extract_float_statistic(stats_contents, f"system.cpu3.CUs{compute_unit_index}.totalCycles")
            )
        
        avg_number_of_cycles: float = sum(cycles) / len(cycles)


        vectors_per_cycle: List[float] = []
        for compute_unit_index in range(parameters.number_of_compute_units):
            vectors_per_cycle.append(
                find_and_extract_float_statistic(stats_contents, f"system.cpu3.CUs{compute_unit_index}.vpc")
            )
        
        avg_number_of_vectors_per_cycle: float = sum(vectors_per_cycle) / len(vectors_per_cycle)


        return cls(
            mean_load_latency=mean_load_latency,
            avg_executed_vector_alu_instructions=avg_executed_vector_alu_instructions,
            avg_reads_to_shared_memory=avg_reads_to_shared_memory,
            avg_writes_to_shared_memory=avg_writes_to_shared_memory,
            avg_accesses_of_shared_memory=avg_accesses_of_shared_memory,
            avg_number_of_cycles=avg_number_of_cycles,
            avg_number_of_vectors_per_cycle=avg_number_of_vectors_per_cycle,
        )



@dataclass(frozen=True, kw_only=True)
class Run:
    parameters: RunParameters
    timings: RunTimings


def filter_runs_by_implementation(runs: List[Run], implementation: Union[Literal["naive"], Literal["optimized"]]) -> List[Run]:
    return [
        run for run in runs
        if run.parameters.implementation == implementation
    ]

def filter_runs_by_compute_units(runs: List[Run], num_compute_units: int) -> List[Run]:
    return [
        run for run in runs
        if run.parameters.number_of_compute_units == num_compute_units
    ]

def get_run_by_compute_units(runs: List[Run], num_compute_units: int) -> Run:
    for run in runs:
        if run.parameters.number_of_compute_units == num_compute_units:
            return run
    
    raise RuntimeError()

def get_run_by_implementation(runs: List[Run], implementation: Union[Literal["naive"], Literal["optimized"]]) -> Run:
    for run in runs:
        if run.parameters.implementation == implementation:
            return run
    
    raise RuntimeError()


def generate_bar_plot(
    runs: List[Run],
    output_directory_path: Path,
    output_file_name: str,
    plot_title: Optional[str],
    plot_x_axis_label: str,
    plot_y_axis_label: str,
    timing_extractor: Callable[[RunTimings], float],
) -> None:
    figure: Figure = plt.figure(
        num=output_file_name,
        layout="constrained"
    )

    axes: Axes = figure.subplots(nrows=1, ncols=1)


    TESTED_COMPUTE_UNITS: List[int] = [2, 4, 8]

    # Naive runs
    naive_runs = filter_runs_by_implementation(runs, implementation="naive")
    assert len(naive_runs) == 3

    axes.plot(
        TESTED_COMPUTE_UNITS,
        [
            timing_extractor(get_run_by_compute_units(naive_runs, num_compute_units=2).timings),
            timing_extractor(get_run_by_compute_units(naive_runs, num_compute_units=4).timings),
            timing_extractor(get_run_by_compute_units(naive_runs, num_compute_units=8).timings)
        ],
        label="Naive"
    )



    # Optimized runs
    optimized_runs = filter_runs_by_implementation(runs, implementation="optimized")
    assert len(optimized_runs) == 3
    
    axes.plot(
        TESTED_COMPUTE_UNITS,
        [
            timing_extractor(get_run_by_compute_units(optimized_runs, num_compute_units=2).timings),
            timing_extractor(get_run_by_compute_units(optimized_runs, num_compute_units=4).timings),
            timing_extractor(get_run_by_compute_units(optimized_runs, num_compute_units=8).timings)
        ],
        label="Optimized"
    )


    if plot_title is not None:
        axes.set_title(label=plot_title)

    axes.set_xlabel(xlabel=plot_x_axis_label)
    axes.set_ylabel(ylabel=plot_y_axis_label)

    axes.legend(loc="best", title="Implementation")
    
    axes.xaxis.minorticks_off()
    axes.set_xticks(ticks=TESTED_COMPUTE_UNITS, labels=[str(label) for label in TESTED_COMPUTE_UNITS])
    
    axes.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 5, 10]))
    axes.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(n="auto")) # type: ignore


    figure.savefig(
        fname=output_directory_path.joinpath(output_file_name),
        format="svg",
        transparent=False,
        bbox_inches="tight"
    )

    



@dataclass(frozen=True, kw_only=True)
class CLIArguments:
    results_directory_path: Path
    output_directory_path: Path


def parse_cli_arguments() -> CLIArguments:
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


    output_directory_path: Path = Path(str(arguments.output_directory_path))
    if not output_directory_path.exists():
        output_directory_path.mkdir(parents=True)
    
    if not output_directory_path.is_dir():
        raise RuntimeError("Invalid output directory path, not a directory.")

    
    return CLIArguments(
        results_directory_path=run_directory_path,
        output_directory_path=output_directory_path
    )



def prepare_timestamped_output_directory(base_output_directory_path: Path) -> Path:
    formatted_timestamp: str = datetime.datetime.now().strftime(r"%Y-%m-%d_%H-%M-%S")
    timestamped_output_directory_path = base_output_directory_path.joinpath(f"plots_{formatted_timestamp}")

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
    timestamped_output_directory_path = prepare_timestamped_output_directory(cli_arguments.output_directory_path)

    runs: List[Run] = []

    for dir_entry in os.listdir(cli_arguments.results_directory_path):
        dir_entry_path: Path = cli_arguments.results_directory_path.joinpath(dir_entry)

        if not (dir_entry_path.is_file() and dir_entry_path.name.endswith(".txt")):
            continue

        run_parameters = RunParameters.load_from_log_file_path(dir_entry_path)

        stats_txt_file_path = run_parameters.get_path_to_stats_txt(cli_arguments.results_directory_path)
        run_results = RunTimings.from_stats_txt_file_path(run_parameters, stats_txt_file_path)

        runs.append(
            Run(
                parameters=run_parameters,
                timings=run_results
            )
        )

    print(f"Found {len(runs)} results in provided directory, plotting.")
    print()

    # print(aggregated_results)

    generate_bar_plot(
        runs=runs,
        output_directory_path=timestamped_output_directory_path,
        output_file_name="rs4-t1-mean-load-latency.svg",
        plot_title=None,
        plot_x_axis_label="Number of compute units",
        plot_y_axis_label="Mean load latency",
        timing_extractor=lambda timings: timings.mean_load_latency
    )

    generate_bar_plot(
        runs=runs,
        output_directory_path=timestamped_output_directory_path,
        output_file_name="rs4-t1-avg-executed-vector-alu-instructions.svg",
        plot_title=None,
        plot_x_axis_label="Number of compute units",
        plot_y_axis_label="Average number of executed vector ALU instructions",
        timing_extractor=lambda timings: timings.avg_executed_vector_alu_instructions
    )

    generate_bar_plot(
        runs=runs,
        output_directory_path=timestamped_output_directory_path,
        output_file_name="rs4-t1-avg-reads-from-shared-memory.svg",
        plot_title=None,
        plot_x_axis_label="Number of compute units",
        plot_y_axis_label="Average number of reads from shared memory",
        timing_extractor=lambda timings: timings.avg_reads_to_shared_memory
    )

    generate_bar_plot(
        runs=runs,
        output_directory_path=timestamped_output_directory_path,
        output_file_name="rs4-t1-avg-writes-to-shared-memory.svg",
        plot_title=None,
        plot_x_axis_label="Number of compute units",
        plot_y_axis_label="Average number of writes to shared memory",
        timing_extractor=lambda timings: timings.avg_writes_to_shared_memory
    )

    generate_bar_plot(
        runs=runs,
        output_directory_path=timestamped_output_directory_path,
        output_file_name="rs4-t1-avg-accesses-of-shared-memory.svg",
        plot_title=None,
        plot_x_axis_label="Number of compute units",
        plot_y_axis_label="Average number of accesses of shared memory",
        timing_extractor=lambda timings: timings.avg_accesses_of_shared_memory
    )

    generate_bar_plot(
        runs=runs,
        output_directory_path=timestamped_output_directory_path,
        output_file_name="rs4-t1-avg-cycles.svg",
        plot_title=None,
        plot_x_axis_label="Number of compute units",
        plot_y_axis_label="Average number of cycles",
        timing_extractor=lambda timings: timings.avg_number_of_cycles
    )

    generate_bar_plot(
        runs=runs,
        output_directory_path=timestamped_output_directory_path,
        output_file_name="rs4-t1-avg-vectors-per-cycle.svg",
        plot_title=None,
        plot_x_axis_label="Number of compute units",
        plot_y_axis_label="Average number of vectors per cycle",
        timing_extractor=lambda timings: timings.avg_number_of_vectors_per_cycle
    )

    print("DONE")


if __name__ == "__main__":
    main()

