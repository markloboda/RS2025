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




DIRECTORY_NAME_REGEX: re.Pattern = re.compile(r"L1-(.+)-(\d+)_L2-(.+)-(\d+)_(\d)")

@dataclass(frozen=True, kw_only=True)
class RunSetupParameters:
    l1_cache_size: str
    l2_cache_size: str

    l1_cache_associativity: int
    l2_cache_associativity: int

    multiplication_program_version: int

    @classmethod
    def from_directory_path(cls, run_results_directory_path: Path) -> Self:
        directory_name: str = run_results_directory_path.name
        matched_directory_name: re.Match = DIRECTORY_NAME_REGEX.match(directory_name)

        
        l1_cache_size = matched_directory_name.group(1)
        l1_cache_associativity: int = int(matched_directory_name.group(2))

        l2_cache_size = matched_directory_name.group(3)
        l2_cache_associativity: int = int(matched_directory_name.group(4))

        multiplication_program_version: int = int(matched_directory_name.group(5))


        return cls(
            l1_cache_size=l1_cache_size,
            l2_cache_size=l2_cache_size,
            l1_cache_associativity=l1_cache_associativity,
            l2_cache_associativity=l2_cache_associativity,
            multiplication_program_version=multiplication_program_version
        )





@dataclass(frozen=True, kw_only=True)
class RunResults:
    # (board.cache_hierarchy.l1_dcache.WriteReq.misses::total)
    l1_data_cache_write_misses: int

    # (board.cache_hierarchy.l1_dcache.ReadReq.misses::total)
    l1_data_cache_read_misses: int

    # (board.cache_hierarchy.l1_dcache.WriteReq.hits::total)
    l1_data_cache_write_hits: int

    # (board.cache_hierarchy.l1_dcache.ReadReq.hits::total)
    l1_data_cache_read_hits: int

    # (board.cache_hierarchy.l2_cache.overallHits::total)
    l2_cache_hits: int

    # (board.cache_hierarchy.l2_cache.overallMisses::total)
    l2_cache_misses: int

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
        
        l1_data_cache_write_misses = extract_int("board.cache_hierarchy.l1_dcache.WriteReq.misses::total")
        l1_data_cache_read_misses = extract_int("board.cache_hierarchy.l1_dcache.ReadReq.misses::total")

        l1_data_cache_write_hits = extract_int("board.cache_hierarchy.l1_dcache.WriteReq.hits::total")
        l1_data_cache_read_hits = extract_int("board.cache_hierarchy.l1_dcache.ReadReq.hits::total")

        l2_cache_hits = extract_int("board.cache_hierarchy.l2_cache.overallHits::total")
        l2_cache_misses = extract_int("board.cache_hierarchy.l2_cache.overallMisses::total")

        cycles_per_instruction = extract_float("board.processor.cores.core.cpi")
        instructions_per_cycle = extract_float("board.processor.cores.core.ipc")

        total_cycles = extract_int("board.processor.cores.core.numCycles")

        return cls(
            l1_data_cache_write_misses=l1_data_cache_write_misses,
            l1_data_cache_read_misses=l1_data_cache_read_misses,
            l1_data_cache_write_hits=l1_data_cache_write_hits,
            l1_data_cache_read_hits=l1_data_cache_read_hits,
            l2_cache_hits=l2_cache_hits,
            l2_cache_misses=l2_cache_misses,
            cycles_per_instruction=cycles_per_instruction,
            instructions_per_cycle=instructions_per_cycle,
            total_cycles=total_cycles
        )

    def l1_cache_read_miss_rate(self) -> float:
        return self.l1_data_cache_read_misses / (self.l1_data_cache_read_misses + self.l1_data_cache_read_hits)

    def l1_cache_write_miss_rate(self) -> float:
        return self.l1_data_cache_write_misses / (self.l1_data_cache_write_misses + self.l1_data_cache_write_hits)

    def l2_cache_miss_rate(self) -> float:
        return self.l2_cache_misses / (self.l2_cache_misses + self.l2_cache_hits)



def main():
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

    
    benchmarks_directory_path: Path = run_directory_path.joinpath("benchmarks")
    if not run_directory_path.is_dir():
        print(f"Invalid --run-directory-path, \"benchmarks\" subdirectory does not exist: {run_directory_path.as_posix()}")
        exit(1)

    
    aggregated_results: List[Tuple[RunSetupParameters, RunResults]] = []

    for dir_entry in os.listdir(benchmarks_directory_path):
        dir_entry_path: Path = benchmarks_directory_path.joinpath(dir_entry)

        if dir_entry_path.is_dir():
            run_parameters = RunSetupParameters.from_directory_path(dir_entry_path)
            run_results = RunResults.from_directory_path(dir_entry_path)

            aggregated_results.append((run_parameters, run_results))
    
    print(f"Found {len(aggregated_results)} results in provided directory.")
    print()

    def extract_aggregated_result_key(value: Tuple[RunSetupParameters, RunResults]):
        run_setup, _ = value

        return (
            run_setup.l1_cache_size,
            run_setup.l2_cache_size,
            run_setup.l1_cache_associativity,
            run_setup.l2_cache_associativity,
            run_setup.multiplication_program_version
        )

    sorted_aggregated_results = sorted(
        aggregated_results,
        key=extract_aggregated_result_key
    )


    for index, (run_parameters, run_results) in enumerate(sorted_aggregated_results):
        print(f"Run {index + 1}:")
        print(f"  L1: {run_parameters.l1_cache_size} (associativity: {run_parameters.l1_cache_associativity})")
        print(f"  L2: {run_parameters.l2_cache_size} (associativity: {run_parameters.l2_cache_associativity})")
        print(f"  Program implementation: mat_mult{run_parameters.multiplication_program_version}.bin")
        print()
        print(f"  > Instructions per cycle (IPC): {run_results.instructions_per_cycle:.3}")
        print(f"  > Total cycles: {run_results.total_cycles}")
        print(f"  > L1 Data Cache Miss Rate (Read): {run_results.l1_cache_read_miss_rate():.3}")
        print(f"  > L1 Data Cache Miss Rate (Write): {run_results.l1_cache_write_miss_rate():.3}")
        print(f"  > L2 Cache Miss Rate (Overall): {run_results.l2_cache_miss_rate():.3}")
        print()
    
    print("DONE")
    


if __name__ == "__main__":
    main()
