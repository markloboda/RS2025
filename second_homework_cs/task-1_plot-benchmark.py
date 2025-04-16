from argparse import ArgumentParser
from dataclasses import dataclass
import datetime
import os
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional, Self, Tuple

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.figure import Figure
from matplotlib.axes import Axes


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





DIRECTORY_NAME_REGEX: re.Pattern = re.compile(r"(.+)-cpus")

@dataclass(frozen=True, kw_only=True)
class RunParameters:
    number_of_processors: int

    @classmethod
    def from_directory_path(cls, run_results_directory_path: Path) -> Self:
        directory_name: str = run_results_directory_path.name
        matched_directory_name: re.Match = DIRECTORY_NAME_REGEX.match(directory_name)
        
        number_of_processors = int(matched_directory_name.group(1))

        return cls(
            number_of_processors=number_of_processors
        )


@dataclass(frozen=True, kw_only=True)
class RunResults:
    cycles_per_instruction_per_core: List[float]

    l1_overall_misses_per_core: List[int]

    l1_overall_hits_per_core: List[int]

    l3_upgrade_requests: int

    snoop_traffic: int

    @classmethod
    def from_directory_path(
        cls,
        run_results_directory_path: Path,
        number_of_cpus: int
    ) -> Self:
        stats_txt_path = run_results_directory_path.joinpath("stats.txt")
        if not stats_txt_path.is_file():
            raise FileNotFoundError(f"No stats.txt in {run_results_directory_path}!")

        with stats_txt_path.open(mode="r", encoding="utf-8") as stats_file:
            stats_file_contents = stats_file.read()
            return cls.from_stats_txt(
                stats_txt=stats_file_contents,
                number_of_cpus=number_of_cpus
            )
    
    @classmethod
    def from_stats_txt(cls, stats_txt: str, number_of_cpus: int) -> Self:
        selected_sim = select_simulation_statistic(stats_txt, selected_nth_simulation=0)


        cycles_per_instruction_per_core: List[float] = []
        for cpu_index in range(number_of_cpus):
            cpi_value: float = find_and_extract_float_statistic(
                selected_sim,
                f"board.processor.cores{cpu_index}.core.cpi"
            )

            cycles_per_instruction_per_core.append(cpi_value)


        l1_overall_misses_per_core: List[int] = []
        for cpu_index in range(number_of_cpus):
            l1_hit_value: int = find_and_extract_int_statistic(
                selected_sim,
                f"board.cache_hierarchy.clusters{cpu_index}.l1d_cache.overallMisses::total"
            )

            l1_overall_misses_per_core.append(l1_hit_value)
            
        l1_overall_hits_per_core: List[int] = []
        for cpu_index in range(number_of_cpus):
            l1_hit_value: int = find_and_extract_int_statistic(
                selected_sim,
                f"board.cache_hierarchy.clusters{cpu_index}.l1d_cache.overallHits::total"
            )

            l1_overall_hits_per_core.append(l1_hit_value)


        l3_upgrade_requests: int = find_and_extract_int_statistic(
            selected_sim,
            "board.cache_hierarchy.l3_bus.transDist::UpgradeReq"
        )

        snoop_traffic: int = find_and_extract_int_statistic(
            selected_sim,
            "board.cache_hierarchy.l3_bus.snoopTraffic"
        )
        
        return cls(
            cycles_per_instruction_per_core=cycles_per_instruction_per_core,
            l1_overall_misses_per_core=l1_overall_misses_per_core,
            l1_overall_hits_per_core=l1_overall_hits_per_core,
            l3_upgrade_requests=l3_upgrade_requests,
            snoop_traffic=snoop_traffic
        )


    def average_cpi(self) -> float:
        return sum(self.cycles_per_instruction_per_core) / len(self.cycles_per_instruction_per_core)

    def l1_miss_rate_per_core(self) -> List[float]:
        assert len(self.l1_overall_misses_per_core) == len(self.l1_overall_hits_per_core)


        l1_miss_ratio_per_core: List[float] = []
        for index in range(len(self.l1_overall_misses_per_core)):
            l1_miss_count_for_core: int = self.l1_overall_misses_per_core[index]
            l1_hit_count_for_core: int = self.l1_overall_hits_per_core[index]

            l1_miss_ratio_per_core.append(l1_miss_count_for_core / (l1_miss_count_for_core + l1_hit_count_for_core))
        
        return l1_miss_ratio_per_core

    def average_l1_miss_ratio(self) -> float:
        l1_miss_ratio_per_core = self.l1_miss_rate_per_core()

        return sum(l1_miss_ratio_per_core) / len(l1_miss_ratio_per_core)




@dataclass(frozen=True, kw_only=True)
class Run:
    parameters: RunParameters
    results: RunResults


@dataclass(frozen=True, kw_only=True)
class CLIArguments:
    run_results_directory_path: Path
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

    
    run_results_directory_path: Path = run_directory_path.joinpath("results")
    if not run_directory_path.is_dir():
        print(f"Invalid --run-directory-path, \"results\" subdirectory does not exist: {run_directory_path.as_posix()}")
        exit(1)


    output_directory_path: Path = Path(str(arguments.output_directory_path))
    if not output_directory_path.exists():
        output_directory_path.mkdir(parents=True)
    
    if not output_directory_path.is_dir():
        raise RuntimeError("Invalid output directory path, not a directory.")

    
    return CLIArguments(
        run_results_directory_path=run_results_directory_path,
        output_directory_path=output_directory_path
    )


def plot_overlayed_per_core_cpi_against_number_of_processors(
    all_runs: List[Run],
    output_directory_path: Path
) -> None:
    figure: Figure = plt.figure(
        num="per-core-cpi-against-number-of-cpu",
        layout="constrained"
    )

    axes: Axes = figure.subplots(nrows=1, ncols=1)


    maximum_cpi_value: float = 0
    maximum_cpu_count: int = 0

    # Indexed by CPU count.
    per_core_cpi_across_cpu_count: Dict[int, List[float]] = {}
    for run in all_runs:
        cpu_count = run.parameters.number_of_processors
        assert cpu_count not in per_core_cpi_across_cpu_count

        maximum_cpi_value = max(maximum_cpi_value, max(run.results.cycles_per_instruction_per_core))
        maximum_cpu_count = max(maximum_cpu_count, cpu_count)

        per_core_cpi_across_cpu_count[cpu_count] = run.results.cycles_per_instruction_per_core.copy()
    

    per_core_cpi_across_sorted_cpu_count: List[Tuple[int, List[float]]] = sorted(
        per_core_cpi_across_cpu_count.items(),
        key=lambda item: item[0]
    )


    for index, (cpu_count, per_core_cpi_values) in enumerate(per_core_cpi_across_sorted_cpu_count):
        x_axis = list(
            a + (index - 2) * 0.2
            for a in range(len(per_core_cpi_values))
        )

        axes.stem(
            x_axis,
            per_core_cpi_values,
            linefmt=f"C{index}-",
            markerfmt=f"C{index}o",
            basefmt=f"C{index}-",
            label=f"{cpu_count} CPUs"
        )
    
    
    axes.legend(loc="lower right", reverse=False, title="CPU count")
    axes.set_title(
        "Individual core CPI across different CPU counts",
        pad=14,
    )

    axes.set_xlabel("Core on system")
    axes.set_ylabel("Cycles per instruction (CPI)")


    axes.xaxis.minorticks_off()
    axes.set_xticks(
        ticks=list(range(maximum_cpu_count)),
        labels=list(count + 1 for count in range(maximum_cpu_count))
    )
    
    axes.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 5, 10]))
    axes.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(n="auto"))


    axes.set_autoscale_on(False)
    axes.set_ylim(ymin=0, ymax=maximum_cpi_value * 1.08)
    axes.set_xlim(
        xmin=-1,
        xmax=maximum_cpu_count + 1
    )


    figure.savefig(
        fname=output_directory_path.joinpath(
            "per-core-cpi-against-number-of-cpu.svg"
            # "per-core-cpi-against-number-of-cpu.png"
        ),
        format="svg",
        # format="png",
        # transparent=True,
        transparent=False,
        bbox_inches="tight"
    )


def plot_overlayed_per_core_l1_miss_rate_against_number_of_processors(
    all_runs: List[Run],
    output_directory_path: Path
) -> None:
    figure: Figure = plt.figure(
        num="per-core-l1-miss-rate-against-number-of-cpu",
        layout="constrained"
    )

    axes: Axes = figure.subplots(nrows=1, ncols=1)


    # Indexed by CPU count.
    maximum_l1_miss_rate_value: float = 0
    maximum_cpu_count: int = 0

    per_core_l1_miss_rate_across_cpu_count: Dict[int, List[float]] = {}
    for run in all_runs:
        cpu_count = run.parameters.number_of_processors
        assert cpu_count not in per_core_l1_miss_rate_across_cpu_count

        maximum_l1_miss_rate_value = max(maximum_l1_miss_rate_value, max(run.results.l1_miss_rate_per_core()))
        maximum_cpu_count = max(maximum_cpu_count, cpu_count)

        per_core_l1_miss_rate_across_cpu_count[cpu_count] = run.results.l1_miss_rate_per_core()
    

    per_core_cpi_across_sorted_cpu_count: List[Tuple[int, List[float]]] = sorted(
        per_core_l1_miss_rate_across_cpu_count.items(),
        key=lambda item: item[0]
    )


    for index, (cpu_count, per_core_cpi_values) in enumerate(per_core_cpi_across_sorted_cpu_count):
        x_axis = list(
            a + (index - 2) * 0.2
            for a in range(len(per_core_cpi_values))
        )

        axes.stem(
            x_axis,
            per_core_cpi_values,
            linefmt=f"C{index}-",
            markerfmt=f"C{index}o",
            basefmt=f"C{index}-",
            label=f"{cpu_count} CPUs"
        )
    
    
    axes.legend(loc="upper right", reverse=False, title="CPU count")
    axes.set_title(
        "L1 miss rates for individual cores across different CPU counts",
        pad=14,
    )

    axes.set_xlabel("Core on system")
    axes.set_ylabel("L1 miss rate")


    axes.xaxis.minorticks_off()
    axes.set_xticks(
        ticks=list(range(maximum_cpu_count)),
        labels=list(count + 1 for count in range(maximum_cpu_count))
    )
    
    axes.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 5, 10]))
    axes.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(n="auto"))


    axes.set_autoscale_on(False)
    axes.set_ylim(ymin=0, ymax=maximum_l1_miss_rate_value * 1.08)
    axes.set_xlim(
        xmin=-1,
        xmax=maximum_cpu_count + 1
    )


    figure.savefig(
        fname=output_directory_path.joinpath(
            "per-core-l1-miss-rate-against-number-of-cpu.svg"
            # "per-core-l1-miss-rate-against-number-of-cpu.png"
        ),
        format="svg",
        # format="png",
        # transparent=True,
        transparent=False,
        bbox_inches="tight"
    )


def plot_l3_upgrade_request_count_against_number_of_processors(
    all_runs: List[Run],
    output_directory_path: Path
) -> None:
    figure: Figure = plt.figure(
        num="l3-upgrade-request-count-against-number-of-cpus",
        layout="constrained"
    )

    axes: Axes = figure.subplots(nrows=1, ncols=1)


    # Indexed by CPU count.
    l3_upgrade_count_across_cpu_count: Dict[int, int] = {}
    for run in all_runs:
        cpu_count = run.parameters.number_of_processors
        assert cpu_count not in l3_upgrade_count_across_cpu_count

        l3_upgrade_count_across_cpu_count[cpu_count] = run.results.l3_upgrade_requests

    maximum_l3_upgrade_count: int = max(l3_upgrade_count_across_cpu_count.values())
    maximum_cpu_count: int = max(l3_upgrade_count_across_cpu_count.keys())


    l3_upgrade_count_across_sorted_cpu_count: List[Tuple[int, int]] = sorted(
        l3_upgrade_count_across_cpu_count.items(),
        key=lambda item: item[0]
    )


    axes.bar(
        [key for key, _ in l3_upgrade_count_across_sorted_cpu_count],
        [value for _, value in l3_upgrade_count_across_sorted_cpu_count],
        width=0.75,
        align="center",
    )

    axes.set_title(
        "L3 upgrade requests across different CPU counts",
        pad=14,
    )

    axes.set_xlabel("Number of CPUs present on system")
    axes.set_ylabel("Number of L3 upgrade requests")

    axes.xaxis.minorticks_off()
    axes.set_xticks(
        ticks=[key for key, _ in l3_upgrade_count_across_sorted_cpu_count],
        labels=[key for key, _ in l3_upgrade_count_across_sorted_cpu_count]
    )
    
    axes.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 5, 10]))
    axes.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(n="auto"))

    axes.set_autoscale_on(False)
    axes.set_ylim(ymin=0, ymax=maximum_l3_upgrade_count * 1.08)
    axes.set_xlim(
        xmin=1,
        xmax=maximum_cpu_count + 1
    )



    figure.savefig(
        fname=output_directory_path.joinpath(
            "l3-upgrade-requests-against-number-of-cpus.svg"
            # "l3-upgrade-requests-against-number-of-cpus.png"
        ),
        format="svg",
        # format="png",
        # transparent=True,
        transparent=False,
        bbox_inches="tight"
    )


def plot_snoop_traffic_against_number_of_processors(
    all_runs: List[Run],
    output_directory_path: Path
) -> None:
    figure: Figure = plt.figure(
        num="snoop-traffic-against-number-of-cpus",
        layout="constrained"
    )

    axes: Axes = figure.subplots(nrows=1, ncols=1)


    # Indexed by CPU count.
    snoop_traffic_across_cpu_count: Dict[int, int] = {}
    for run in all_runs:
        cpu_count = run.parameters.number_of_processors
        assert cpu_count not in snoop_traffic_across_cpu_count

        snoop_traffic_across_cpu_count[cpu_count] = run.results.snoop_traffic

    maximum_snoop_traffic: int = max(snoop_traffic_across_cpu_count.values())
    maximum_cpu_count: int = max(snoop_traffic_across_cpu_count.keys())


    snoop_traffic_across_sorted_cpu_count: List[Tuple[int, int]] = sorted(
        snoop_traffic_across_cpu_count.items(),
        key=lambda item: item[0]
    )


    axes.bar(
        [key for key, _ in snoop_traffic_across_sorted_cpu_count],
        [value for _, value in snoop_traffic_across_sorted_cpu_count],
        width=0.75,
        align="center",
    )

    axes.set_title(
        "Snoop traffic across different CPU counts",
        pad=14,
    )

    axes.set_xlabel("Number of CPUs present on system")
    axes.set_ylabel("Snoop traffic")

    axes.xaxis.minorticks_off()
    axes.set_xticks(
        ticks=[key for key, _ in snoop_traffic_across_sorted_cpu_count],
        labels=[key for key, _ in snoop_traffic_across_sorted_cpu_count]
    )
    
    axes.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 5, 10]))
    axes.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(n="auto"))

    axes.set_autoscale_on(False)
    axes.set_ylim(ymin=0, ymax=maximum_snoop_traffic * 1.08)
    axes.set_xlim(
        xmin=1,
        xmax=maximum_cpu_count + 1
    )



    figure.savefig(
        fname=output_directory_path.joinpath(
            "snoop-traffic-against-number-of-cpus.svg"
            # "snoop-traffic-against-number-of-cpus.png"
        ),
        format="svg",
        # format="png",
        # transparent=True,
        transparent=False,
        bbox_inches="tight"
    )

    # TODO
    pass




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

    aggregated_results: List[Run] = []

    for dir_entry in os.listdir(cli_arguments.run_results_directory_path):
        dir_entry_path: Path = cli_arguments.run_results_directory_path.joinpath(dir_entry)

        if dir_entry_path.is_dir():
            run_parameters = RunParameters.from_directory_path(dir_entry_path)
            run_results = RunResults.from_directory_path(
                dir_entry_path,
                number_of_cpus=run_parameters.number_of_processors
            )

            aggregated_results.append(Run(
                parameters=run_parameters,
                results=run_results
            ))

    print(f"Found {len(aggregated_results)} results in provided directory, plotting.")
    print()

    plot_overlayed_per_core_cpi_against_number_of_processors(
        all_runs=aggregated_results,
        output_directory_path=timestamped_output_directory_path
    )

    plot_overlayed_per_core_l1_miss_rate_against_number_of_processors(
        all_runs=aggregated_results,
        output_directory_path=timestamped_output_directory_path
    )

    plot_l3_upgrade_request_count_against_number_of_processors(
        all_runs=aggregated_results,
        output_directory_path=timestamped_output_directory_path
    )

    plot_snoop_traffic_against_number_of_processors(
        all_runs=aggregated_results,
        output_directory_path=timestamped_output_directory_path
    )

    print("DONE")


if __name__ == "__main__":
    main()
