from argparse import ArgumentParser
from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import List, Optional, Self, Tuple


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

    def l1_miss_ratio_per_core(self) -> List[float]:
        assert len(self.l1_overall_misses_per_core) == len(self.l1_overall_hits_per_core)


        l1_miss_ratio_per_core: List[float] = []
        for index in range(len(self.l1_overall_misses_per_core)):
            l1_miss_count_for_core: int = self.l1_overall_misses_per_core[index]
            l1_hit_count_for_core: int = self.l1_overall_hits_per_core[index]

            l1_miss_ratio_per_core.append(l1_miss_count_for_core / (l1_miss_count_for_core + l1_hit_count_for_core))
        
        return l1_miss_ratio_per_core

    def average_l1_miss_ratio(self) -> float:
        l1_miss_ratio_per_core = self.l1_miss_ratio_per_core()

        return sum(l1_miss_ratio_per_core) / len(l1_miss_ratio_per_core)


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

        return run_parameters.number_of_processors

    sorted_aggregated_results = sorted(
        aggregated_results,
        key=extract_run_key
    )


    for index, (run_parameters, run_results) in enumerate(sorted_aggregated_results):
        print(f"Run {index + 1}:")
        print(f"  Number of processors: {run_parameters.number_of_processors}")
        print()


        average_cpi = run_results.average_cpi()
        print("  > cycles per instruction (CPI)")
        print(f"    | average: {average_cpi}")
        print(f"    | per-core: {', '.join(str(cpi) for cpi in run_results.cycles_per_instruction_per_core)}")


        average_l1_miss_rate = run_results.average_l1_miss_ratio()
        print("  > L1 overall miss ratio")
        print(f"    | average: {average_l1_miss_rate}")
        print(f"    | per-core: {', '.join(f"{ratio:.6f}" for ratio in run_results.l1_miss_ratio_per_core())}")
        print(f"  > L3 upgrade requests: {run_results.l3_upgrade_requests}")
        print(f"  > Snoop traffic: {run_results.snoop_traffic}")
        print()
        print()

    print("DONE")


if __name__ == "__main__":
    main()
