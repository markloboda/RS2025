from argparse import ArgumentParser
from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import List, Optional, Self, Tuple


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

def parse_cli_arguments() -> CLIArguments:
    argument_parser = ArgumentParser()
    
    argument_parser.add_argument(
        "--run-directory-path",
        required=True,
        dest="run_directory_path"
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

    
    return CLIArguments(
        run_results_directory_path=run_results_directory_path
    )


def main() -> None:
    cli_arguments = parse_cli_arguments()

    aggregated_results: List[Tuple[RunParameters, RunResults]] = []

    for dir_entry in os.listdir(cli_arguments.run_results_directory_path):
        dir_entry_path: Path = cli_arguments.run_results_directory_path.joinpath(dir_entry)

        if dir_entry_path.is_dir():
            run_parameters = RunParameters.from_directory_path(dir_entry_path)
            run_results = RunResults.from_directory_path(
                dir_entry_path,
                number_of_cpus=run_parameters.number_of_processors
            )

            aggregated_results.append((run_parameters, run_results))

    print(f"Found {len(aggregated_results)} results in provided directory.")
    print()

    def extract_run_key(run: Tuple[RunParameters, RunResults]):
        run_parameters, _ = run

        return (
            run_parameters.number_of_processors,
            run_parameters.interconnection_network_type
        )

    sorted_aggregated_results = sorted(
        aggregated_results,
        key=extract_run_key
    )


    for index, (run_parameters, run_results) in enumerate(sorted_aggregated_results):
        print(f"Run {index + 1}:")
        print(f"  Number of processors: {run_parameters.number_of_processors}")
        print(f"  Interconnection network type: {run_parameters.interconnection_network_type}")
        print()

        print(f"  > Request_Control messages: {run_results.request_control_messages}")
        print(f"  > Response_Data messages: {run_results.response_data_messages}")
        print(f"  > Writeback_Data messages: {run_results.writeback_data_messages}")

        print()
        print()

    print("DONE")


if __name__ == "__main__":
    main()
