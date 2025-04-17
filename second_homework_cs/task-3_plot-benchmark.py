from argparse import ArgumentParser
from dataclasses import dataclass
import datetime
import os
from pathlib import Path
import re
import sys
from typing import Dict, List, Self, Tuple

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.figure import Figure
from matplotlib.axes import Axes

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




DIRECTORY_NAME_REGEX: re.Pattern = re.compile(r"(.+)-cpus_(.+)-network")

@dataclass(frozen=True, kw_only=True)
class RunParameters:
    number_of_processors: int
    # One of: "crossbar", "ring", "point-to-point".
    interconnection_network_type: str

    @classmethod
    def from_directory_path(cls, run_results_directory_path: Path) -> Self:
        directory_name: str = run_results_directory_path.name
        matched_directory_name: re.Match = DIRECTORY_NAME_REGEX.match(directory_name)
        
        number_of_processors = int(matched_directory_name.group(1))
        interconnection_network_type: str = matched_directory_name.group(2)

        assert interconnection_network_type in ["crossbar", "ring", "point-to-point"]

        return cls(
            number_of_processors=number_of_processors,
            interconnection_network_type=interconnection_network_type
        )


@dataclass(frozen=True, kw_only=True)
class RunResults:
    # board.cache_hierarchy.ruby_system.network.msg_count.Request_Control
    request_control_messages: int

    # board.cache_hierarchy.ruby_system.network.msg_count.Response_Data
    response_data_messages: int

    # board.cache_hierarchy.ruby_system.network.msg_count.Writeback_Data
    writeback_data_messages: int

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
        # TODO

        request_control_messages: int = find_and_extract_int_statistic(
            stats_txt, 
            "board.cache_hierarchy.ruby_system.network.msg_count.Request_Control"
        )

        response_data_messages: int = find_and_extract_int_statistic(
            stats_txt, 
            "board.cache_hierarchy.ruby_system.network.msg_count.Response_Data"
        )

        writeback_data_messages: int = find_and_extract_int_statistic(
            stats_txt, 
            "board.cache_hierarchy.ruby_system.network.msg_count.Writeback_Data"
        )
        
        return cls(
            request_control_messages=request_control_messages,
            response_data_messages=response_data_messages,
            writeback_data_messages=writeback_data_messages,
        )


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


@dataclass(frozen=True, kw_only=True)
class Run:
    parameters: RunParameters
    results: RunResults


def plot_message_counts_across_number_of_processors_for_given_network_type(
    all_runs: List[Run],
    # One of: "crossbar", "ring", "point-to-point".
    interconnection_network_type: str,
    output_directory_path: Path,
) -> None:
    figure: Figure = plt.figure(
        num=f"message-counts-against-number-of-cpu-for-{interconnection_network_type}",
        layout="constrained"
    )

    axes: Axes = figure.subplots(nrows=1, ncols=1)


    request_control_count_by_cpu_count: Dict[int, int] = {}
    response_data_count_by_cpu_count: Dict[int, int] = {}
    writeback_data_count_by_cpu_count: Dict[int, int] = {}

    max_any_count: int = 0

    for run in all_runs:
        if run.parameters.interconnection_network_type != interconnection_network_type:
            continue
        
        cpu_count = run.parameters.number_of_processors

        assert cpu_count not in request_control_count_by_cpu_count
        assert cpu_count not in response_data_count_by_cpu_count
        assert cpu_count not in writeback_data_count_by_cpu_count

        max_any_count = max(
            max_any_count,
            run.results.request_control_messages,
            run.results.response_data_messages,
            run.results.writeback_data_messages,
        )

        request_control_count_by_cpu_count[cpu_count] = run.results.request_control_messages
        response_data_count_by_cpu_count[cpu_count] = run.results.response_data_messages
        writeback_data_count_by_cpu_count[cpu_count] = run.results.writeback_data_messages


    request_control_count_sorted_by_cpu_count = sorted(
        request_control_count_by_cpu_count.items(),
        key=lambda item: item[0]
    )

    axes.plot(
        [key for key, _ in request_control_count_sorted_by_cpu_count],
        [value for _, value in request_control_count_sorted_by_cpu_count],
        label="Request_Control messages",
        color="C0"
    )


    response_data_count_sorted_by_cpu_count = sorted(
        response_data_count_by_cpu_count.items(),
        key=lambda item: item[0]
    )

    axes.plot(
        [key for key, _ in response_data_count_sorted_by_cpu_count],
        [value for _, value in response_data_count_sorted_by_cpu_count],
        label="Response_Data messages",
        color="C1"
    )


    writeback_data_count_sorted_by_cpu_count = sorted(
        writeback_data_count_by_cpu_count.items(),
        key=lambda item: item[0]
    )

    axes.plot(
        [key for key, _ in writeback_data_count_sorted_by_cpu_count],
        [value for _, value in writeback_data_count_sorted_by_cpu_count],
        label="Writeback_Data messages",
        color="C2"
    )


    axes.legend(loc="center right", reverse=False, title="Message type")
    axes.set_title(
        f"Per-type message count across number of processors (using {interconnection_network_type})",
        pad=14,
    )

    axes.set_xlabel("Total cores in system")
    axes.set_ylabel("Number of messages")


    x_axis_cpu_counts = sorted(request_control_count_by_cpu_count.keys())

    axes.xaxis.minorticks_off()
    axes.set_xticks(
        ticks=x_axis_cpu_counts,
        labels=x_axis_cpu_counts
    )

    axes.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 5, 10]))
    axes.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(n="auto"))

    axes.set_autoscale_on(False)
    axes.set_ylim(ymin=0, ymax=max_any_count * 1.08)
    axes.set_xlim(
        xmin=2,
        xmax=max(x_axis_cpu_counts)
    )


    figure.savefig(
        fname=output_directory_path.joinpath(
            f"message-counts-against-number-of-cpu-for-{interconnection_network_type}.svg"
            # f"message-counts-against-number-of-cpu-for-{interconnection_network_type}.png"
        ),
        format="svg",
        # format="png",
        # transparent=True,
        transparent=False,
        bbox_inches="tight"
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

    aggregated_results: List[Tuple[RunParameters, RunResults]] = []

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

    print(f"Found {len(aggregated_results)} results in provided directory.")
    print()

    INTERCONNECTION_NETWORK_TYPES: List[str] = [
        "crossbar",
        "ring",
        "point-to-point"
    ]

    for network in INTERCONNECTION_NETWORK_TYPES:
        plot_message_counts_across_number_of_processors_for_given_network_type(
            all_runs=aggregated_results,
            interconnection_network_type=network,
            output_directory_path=timestamped_output_directory_path
        )

    print("DONE")


if __name__ == "__main__":
    main()
