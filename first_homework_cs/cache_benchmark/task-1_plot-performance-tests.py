from argparse import ArgumentParser
import datetime
import os
from pathlib import Path
from dataclasses import dataclass
import re
from typing import Dict, List, Optional, Self, Tuple
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



DIRECTORY_NAME_REGEX: re.Pattern = re.compile(r"L1-(.+)-(\d+)_L2-(.+)-(\d+)_(\d)")

@dataclass(frozen=True, kw_only=True)
class RunSetupParameters:
    l1_cache_size: BinaryUnitSize
    l2_cache_size: BinaryUnitSize

    l1_cache_associativity: int
    l2_cache_associativity: int

    multiplication_program_version: int

    @classmethod
    def from_directory_path(cls, run_results_directory_path: Path) -> Self:
        directory_name: str = run_results_directory_path.name
        matched_directory_name: Optional[re.Match] = DIRECTORY_NAME_REGEX.match(directory_name)
        if matched_directory_name is None:
            raise ValueError(f"Invalid run directory name: {directory_name}")

        
        l1_cache_size = BinaryUnitSize.parse_from_string(matched_directory_name.group(1))
        l1_cache_associativity: int = int(matched_directory_name.group(2))

        l2_cache_size = BinaryUnitSize.parse_from_string(matched_directory_name.group(3))
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



@dataclass(frozen=True, kw_only=True)
class Run:
    parameters: RunSetupParameters
    results: RunResults



def plot_ipc_against_cache_size_for_program_version(
    all_runs: List[Run],
    program_version: int,
    output_directory_path: Path
):
    figure: Figure = plt.figure(
        num=f"ipc-against-cache_mat_mult{program_version}",
        layout="constrained"
    )

    axes: Axes = figure.subplots(nrows=1, ncols=1)


    # Keyed by L2 cache size, then L1 cache size.
    ipc_per_cache_sizes: Dict[BinaryUnitSize, Dict[BinaryUnitSize, float]] = {}
    for run in all_runs:
        if run.parameters.multiplication_program_version != program_version:
            continue

        l1_size = run.parameters.l1_cache_size
        l2_size = run.parameters.l2_cache_size

        if l2_size not in ipc_per_cache_sizes:
            ipc_per_cache_sizes[l2_size] = {}

        assert l1_size not in ipc_per_cache_sizes[l2_size]
        ipc_per_cache_sizes[l2_size][l1_size] = run.results.instructions_per_cycle



    # This is the shared x axis (labels).
    sorted_l1_sizes: List[BinaryUnitSize] = sorted(
        ipc_per_cache_sizes[list(ipc_per_cache_sizes.keys())[0]].keys(),
        key=lambda size: size.number_of_bytes
    )

    sorted_l2_sizes: List[BinaryUnitSize] = sorted(
        ipc_per_cache_sizes.keys(),
        key=lambda size: size.number_of_bytes
    )

    l1_cache_size_x_axis = [value + 0.5 for value in range(0, len(sorted_l1_sizes))]


    maximum_ipc_value: float = 0


    for index, l2_size in enumerate(sorted_l2_sizes):
        data_for_given_l2_size: Dict[BinaryUnitSize, float] = ipc_per_cache_sizes[l2_size]

        # This is the y axis.
        ipc_values_with_ascending_l1_size: List[float] = [
            data_for_given_l2_size[l1_size]
            for l1_size in sorted_l1_sizes
        ]

        maximum_ipc_value = max(maximum_ipc_value, max(ipc_values_with_ascending_l1_size))


        x_axis_offset: float
        if index == 0:
            x_axis_offset = -0.07
        elif index == 1:
            x_axis_offset = 0.07
        else:
            raise ValueError()

        axes.stem(
            [x + x_axis_offset for x in l1_cache_size_x_axis],
            ipc_values_with_ascending_l1_size,
            label=l2_size.full_string,
            linefmt=f"C{index}-"
        )


    assert maximum_ipc_value is not None


    axes.legend(loc="upper left", reverse=True, title="L2 cache size")
    axes.set_title(
        f"Instructions per cycle (IPC) for mat_mult{program_version} across both L2 cache sizes",
        pad=14
    )
    axes.set_xlabel("L1 data cache size")
    axes.set_ylabel("Instructions per cycle (IPC)")

    axes.set_aspect("auto")

    axes.xaxis.minorticks_off()
    axes.set_xticks(
        ticks=l1_cache_size_x_axis,
        labels=[l1_size.full_string for l1_size in sorted_l1_sizes]
    )
    
    axes.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 5, 10]))
    axes.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(n="auto"))

    axes.set_autoscale_on(False)
    axes.set_ylim(ymin=0, ymax=maximum_ipc_value * 1.08)
    axes.set_xlim(
        xmin=0,
        xmax=len(sorted_l1_sizes)
    )

    figure.savefig(
        fname=output_directory_path.joinpath(
            f"ipc-against-cache_mat_mult{program_version}.svg"
            # f"ipc-against-cache_mat_mult{program_version}.png"
        ),
        format="svg",
        # format="png",
        # transparent=True,
        transparent=False,
        bbox_inches="tight"
    )


def plot_total_cycles_against_cache_size_for_program_version(
    all_runs: List[Run],
    program_version: int,
    output_directory_path: Path
):
    figure: Figure = plt.figure(
        num=f"total-cycles-against-cache_mat_mult{program_version}",
        layout="constrained"
    )

    axes: Axes = figure.subplots(nrows=1, ncols=1)


    # Keyed by L2 cache size, then L1 cache size.
    total_cycles_per_cache_sizes: Dict[BinaryUnitSize, Dict[BinaryUnitSize, int]] = {}
    for run in all_runs:
        if run.parameters.multiplication_program_version != program_version:
            continue

        l1_size = run.parameters.l1_cache_size
        l2_size = run.parameters.l2_cache_size

        if l2_size not in total_cycles_per_cache_sizes:
            total_cycles_per_cache_sizes[l2_size] = {}

        assert l1_size not in total_cycles_per_cache_sizes[l2_size]
        total_cycles_per_cache_sizes[l2_size][l1_size] = run.results.total_cycles



    # This is the shared x axis (labels).
    sorted_l1_sizes: List[BinaryUnitSize] = sorted(
        total_cycles_per_cache_sizes[list(total_cycles_per_cache_sizes.keys())[0]].keys(),
        key=lambda size: size.number_of_bytes
    )

    sorted_l2_sizes: List[BinaryUnitSize] = sorted(
        total_cycles_per_cache_sizes.keys(),
        key=lambda size: size.number_of_bytes
    )

    l1_cache_size_x_axis = [value + 0.5 for value in range(0, len(sorted_l1_sizes))]


    maximum_total_cycles: int = 0


    for index, l2_size in enumerate(sorted_l2_sizes):
        data_for_given_l2_size: Dict[BinaryUnitSize, int] = total_cycles_per_cache_sizes[l2_size]

        # This is the y axis.
        total_cycles_for_given_l2_size_with_ascending_l1_size: List[int] = [
            data_for_given_l2_size[l1_size]
            for l1_size in sorted_l1_sizes
        ]

        maximum_total_cycles = max(maximum_total_cycles, max(total_cycles_for_given_l2_size_with_ascending_l1_size))

        x_axis_offset: float
        if index == 0:
            x_axis_offset = -0.07
        elif index == 1:
            x_axis_offset = 0.07
        else:
            raise ValueError()

        axes.stem(
            [x + x_axis_offset for x in l1_cache_size_x_axis],
            total_cycles_for_given_l2_size_with_ascending_l1_size,
            label=l2_size.full_string,
            linefmt=f"C{index}-"
        )


    axes.legend(loc="upper right", reverse=True, title="L2 cache size")
    axes.set_title(
        f"Total cycles executed for mat_mult{program_version}",
        pad=14
    )
    axes.set_xlabel("L1 data cache size")
    axes.set_ylabel("Total cycles")

    axes.set_aspect("auto")

    axes.xaxis.minorticks_off()
    axes.set_xticks(
        ticks=l1_cache_size_x_axis,
        labels=[l1_size.full_string for l1_size in sorted_l1_sizes]
    )
    
    axes.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 5, 10]))
    axes.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(n="auto"))

    axes.set_autoscale_on(False)
    axes.set_ylim(ymin=0, ymax=maximum_total_cycles * 1.08)
    axes.set_xlim(
        xmin=0,
        xmax=len(sorted_l1_sizes)
    )

    figure.savefig(
        fname=output_directory_path.joinpath(
            f"total-cycles-against-cache_mat_mult{program_version}.svg"
            # f"total-cycles-against-cache_mat_mult{program_version}.png"
        ),
        format="svg",
        # format="png",
        # transparent=True,
        transparent=False,
        bbox_inches="tight"
    )



def plot_l1_read_miss_rate_against_l1_sizes(
    all_runs: List[Run],
    selected_l2_size: str,
    output_directory_path: Path,
):
    figure: Figure = plt.figure(
        num=f"l1-read-miss-rate-against-l1-size_for-L2-{selected_l2_size}",
        layout="constrained"
    )

    axes: Axes = figure.subplots(nrows=1, ncols=1)


    # Keyed by L1 cache size, then program version.
    l1_miss_rate_per_program_and_cache: Dict[BinaryUnitSize, Dict[int, float]] = {}
    for run in all_runs:
        if run.parameters.l2_cache_size.full_string != selected_l2_size:
            continue

        l1_size = run.parameters.l1_cache_size
        program_version = run.parameters.multiplication_program_version

        if l1_size not in l1_miss_rate_per_program_and_cache:
            l1_miss_rate_per_program_and_cache[l1_size] = {}

        assert program_version not in l1_miss_rate_per_program_and_cache[l1_size]
        l1_miss_rate_per_program_and_cache[l1_size][program_version] = run.results.l1_cache_read_miss_rate()


    # This is the shared x axis (labels).
    sorted_l1_sizes: List[BinaryUnitSize] = sorted(
        l1_miss_rate_per_program_and_cache.keys(),
        key=lambda size: size.number_of_bytes
    )

    l1_cache_size_x_axis = [value + 0.5 for value in range(0, len(sorted_l1_sizes))]


    maximum_l1_miss_rate: float = 0.0

    for program_version in [1, 2, 3]:
        l1_read_miss_rate_for_program: List[float] = []
        for l1_size in sorted_l1_sizes:
            l1_read_miss_rate_for_program.append(
                l1_miss_rate_per_program_and_cache[l1_size][program_version]
            )
        
        maximum_l1_miss_rate = max(maximum_l1_miss_rate, max(l1_read_miss_rate_for_program))

        x_axis_offset: float
        if program_version == 1:
            x_axis_offset = -0.09
        elif program_version == 2:
            x_axis_offset = 0
        elif program_version == 3:
            x_axis_offset = 0.09
        else:
            raise ValueError()
        

        axes.stem(
            [x + x_axis_offset for x in l1_cache_size_x_axis],
            l1_read_miss_rate_for_program,
            label=f"mat_mult{program_version}",
            linefmt=f"C{program_version - 1}-"
        )
    

    axes.legend(loc="upper right", reverse=True, title="Program version")
    axes.set_title(
        f"L1 data cache read miss rate (with L2 size = {selected_l2_size})",
        pad=14
    )
    axes.set_xlabel("L1 data cache size")
    axes.set_ylabel("L1 read miss rate")

    axes.set_aspect("auto")


    axes.xaxis.minorticks_off()
    axes.set_xticks(
        ticks=l1_cache_size_x_axis,
        labels=[l1_size.full_string for l1_size in sorted_l1_sizes]
    )

    axes.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 5, 10]))
    axes.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(n="auto"))

    axes.set_autoscale_on(False)
    axes.set_ylim(ymin=0, ymax=1.0)
    axes.set_xlim(
        xmin=0,
        xmax=len(sorted_l1_sizes)
    )

    figure.savefig(
        fname=output_directory_path.joinpath(
            f"l1-read-miss-rate-against-l1-size_for-L2-{selected_l2_size}.svg"
            # f"l1-read-miss-rate-against-l1-size_for-L2-{selected_l2_size}.png"
        ),
        format="svg",
        # format="png",
        # transparent=True,
        transparent=False,
        bbox_inches="tight"
    )


def plot_l1_write_miss_rate_against_l1_sizes(
    all_runs: List[Run],
    selected_l2_size: str,
    output_directory_path: Path,
):
    figure: Figure = plt.figure(
        num=f"l1-write-miss-rate-against-l1-size_for-L2-{selected_l2_size}",
        layout="constrained"
    )

    axes: Axes = figure.subplots(nrows=1, ncols=1)


    # Keyed by L1 cache size, then program version.
    l1_miss_rate_per_program_and_cache: Dict[BinaryUnitSize, Dict[int, float]] = {}
    for run in all_runs:
        if run.parameters.l2_cache_size.full_string != selected_l2_size:
            continue

        l1_size = run.parameters.l1_cache_size
        program_version = run.parameters.multiplication_program_version

        if l1_size not in l1_miss_rate_per_program_and_cache:
            l1_miss_rate_per_program_and_cache[l1_size] = {}

        assert program_version not in l1_miss_rate_per_program_and_cache[l1_size]
        l1_miss_rate_per_program_and_cache[l1_size][program_version] = run.results.l1_cache_write_miss_rate()


    # This is the shared x axis (labels).
    sorted_l1_sizes: List[BinaryUnitSize] = sorted(
        l1_miss_rate_per_program_and_cache.keys(),
        key=lambda size: size.number_of_bytes
    )

    l1_cache_size_x_axis = [value + 0.5 for value in range(0, len(sorted_l1_sizes))]


    maximum_l1_miss_rate: float = 0.0

    for program_version in [1, 2, 3]:
        l1_read_miss_rate_for_program: List[float] = []
        for l1_size in sorted_l1_sizes:
            l1_read_miss_rate_for_program.append(
                l1_miss_rate_per_program_and_cache[l1_size][program_version]
            )
        
        maximum_l1_miss_rate = max(maximum_l1_miss_rate, max(l1_read_miss_rate_for_program))

        x_axis_offset: float
        if program_version == 1:
            x_axis_offset = -0.09
        elif program_version == 2:
            x_axis_offset = 0
        elif program_version == 3:
            x_axis_offset = 0.09
        else:
            raise ValueError()
        

        axes.stem(
            [x + x_axis_offset for x in l1_cache_size_x_axis],
            l1_read_miss_rate_for_program,
            label=f"mat_mult{program_version}",
            linefmt=f"C{program_version - 1}-"
        )
    

    axes.legend(loc="upper right", reverse=True, title="Program version")
    axes.set_title(
        f"L1 data cache write miss rate (with L2 size = {selected_l2_size})",
        pad=14
    )
    axes.set_xlabel("L1 data cache size")
    axes.set_ylabel("L1 write miss rate")

    axes.set_aspect("auto")


    axes.xaxis.minorticks_off()
    axes.set_xticks(
        ticks=l1_cache_size_x_axis,
        labels=[l1_size.full_string for l1_size in sorted_l1_sizes]
    )

    axes.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 5, 10]))
    axes.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(n="auto"))

    axes.set_autoscale_on(False)
    axes.set_ylim(ymin=0, ymax=max(maximum_l1_miss_rate*1.05, 0.0008))
    axes.set_xlim(
        xmin=0,
        xmax=len(sorted_l1_sizes)
    )

    figure.savefig(
        fname=output_directory_path.joinpath(
            f"l1-write-miss-rate-against-l1-size_for-L2-{selected_l2_size}.svg"
            # f"l1-write-miss-rate-against-l1-size_for-L2-{selected_l2_size}.png"
        ),
        format="svg",
        # format="png",
        # transparent=True,
        transparent=False,
        bbox_inches="tight"
    )



def plot_l2_miss_rate_against_l2_sizes(
    all_runs: List[Run],
    selected_l1_size: str,
    output_directory_path: Path,
):
    figure: Figure = plt.figure(
        num=f"l2-miss-rate-against-l2-size_for-L1-{selected_l1_size}",
        layout="constrained"
    )

    axes: Axes = figure.subplots(nrows=1, ncols=1)


    # Keyed by L2 cache size, then program version.
    l2_miss_rate_per_program_and_cache: Dict[BinaryUnitSize, Dict[int, float]] = {}
    for run in all_runs:
        if run.parameters.l1_cache_size.full_string != selected_l1_size:
            continue

        l2_size = run.parameters.l2_cache_size
        program_version = run.parameters.multiplication_program_version

        if l2_size not in l2_miss_rate_per_program_and_cache:
            l2_miss_rate_per_program_and_cache[l2_size] = {}

        assert program_version not in l2_miss_rate_per_program_and_cache[l2_size]
        l2_miss_rate_per_program_and_cache[l2_size][program_version] = run.results.l2_cache_miss_rate()


    # This is the shared x axis (labels).
    sorted_l1_sizes: List[BinaryUnitSize] = sorted(
        l2_miss_rate_per_program_and_cache.keys(),
        key=lambda size: size.number_of_bytes
    )

    l1_cache_size_x_axis = [value + 0.5 for value in range(0, len(sorted_l1_sizes))]


    maximum_l2_miss_rate: float = 0.0

    for program_version in [1, 2, 3]:
        l2_read_miss_rate_for_program: List[float] = []
        for l2_size in sorted_l1_sizes:
            l2_read_miss_rate_for_program.append(
                l2_miss_rate_per_program_and_cache[l2_size][program_version]
            )
        
        maximum_l2_miss_rate = max(maximum_l2_miss_rate, max(l2_read_miss_rate_for_program))

        x_axis_offset: float
        if program_version == 1:
            x_axis_offset = -0.09
        elif program_version == 2:
            x_axis_offset = 0
        elif program_version == 3:
            x_axis_offset = 0.09
        else:
            raise ValueError()
        

        axes.stem(
            [x + x_axis_offset for x in l1_cache_size_x_axis],
            l2_read_miss_rate_for_program,
            label=f"mat_mult{program_version}",
            linefmt=f"C{program_version - 1}-"
        )
    

    axes.legend(loc="lower right", reverse=True, title="Program version")
    axes.set_title(
        f"L2 cache miss rate (with L1 size = {selected_l1_size})",
        pad=14
    )
    axes.set_xlabel("L2 cache size")
    axes.set_ylabel("L2 miss rate")

    axes.set_aspect("auto")


    axes.xaxis.minorticks_off()
    axes.set_xticks(
        ticks=l1_cache_size_x_axis,
        labels=[l1_size.full_string for l1_size in sorted_l1_sizes]
    )

    axes.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 5, 10]))
    axes.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(n="auto"))

    axes.set_autoscale_on(False)
    axes.set_ylim(ymin=0, ymax=max(maximum_l2_miss_rate*1.05, 0.06))
    axes.set_xlim(
        xmin=0,
        xmax=len(sorted_l1_sizes)
    )

    figure.savefig(
        fname=output_directory_path.joinpath(
            f"l2-miss-rate-against-l2-size_for-L1-{selected_l1_size}.svg"
            # f"l2-miss-rate-against-l2-size_for-L1-{selected_l1_size}.png"
        ),
        format="svg",
        # format="png",
        # transparent=True,
        transparent=False,
        bbox_inches="tight"
    )


L1_CACHE_SIZES: List[str] = [
    "1 KiB",
    "2 KiB",
    "4 KiB",
    "8 KiB"
]

L2_CACHE_SIZES: List[str] = [
    "32 KiB",
    "64 KiB"
] 


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

    
    benchmarks_directory_path: Path = run_directory_path.joinpath("benchmarks")
    if not run_directory_path.is_dir():
        print(f"Invalid --run-directory-path, \"benchmarks\" subdirectory does not exist: {run_directory_path.as_posix()}")
        exit(1)


    output_directory_path = Path(str(arguments.output_directory_path))
    
    formatted_timestamp: str = datetime.datetime.now().strftime(r"%Y-%m-%d_%H-%M-%S")
    timestamped_output_directory_path = output_directory_path.joinpath(
        f"analysis_{formatted_timestamp}"
    )

    if timestamped_output_directory_path.exists():
        print("Output directory already exists (you ran the tool twice in a second), retry in one second.")
        exit(1)

    timestamped_output_directory_path.mkdir(parents=True, exist_ok=False)


    
    aggregated_results: List[Run] = []

    for dir_entry in os.listdir(benchmarks_directory_path):
        dir_entry_path: Path = benchmarks_directory_path.joinpath(dir_entry)

        if dir_entry_path.is_dir():
            run_parameters = RunSetupParameters.from_directory_path(dir_entry_path)
            run_results = RunResults.from_directory_path(dir_entry_path)

            aggregated_results.append(Run(parameters=run_parameters, results=run_results))
    
    print(f"Found {len(aggregated_results)} results in provided directory.")
    print()

    plt.style.use("ggplot")

    for program_version in [1, 2, 3]:
        plot_ipc_against_cache_size_for_program_version(
            all_runs=aggregated_results,
            program_version=program_version,
            output_directory_path=timestamped_output_directory_path
        )

        plot_total_cycles_against_cache_size_for_program_version(
            all_runs=aggregated_results,
            program_version=program_version,
            output_directory_path=timestamped_output_directory_path
        )
    
    for l2_size in L2_CACHE_SIZES:
        plot_l1_read_miss_rate_against_l1_sizes(
            all_runs=aggregated_results,
            selected_l2_size=l2_size,
            output_directory_path=timestamped_output_directory_path
        )

        plot_l1_write_miss_rate_against_l1_sizes(
            all_runs=aggregated_results,
            selected_l2_size=l2_size,
            output_directory_path=timestamped_output_directory_path
        )
    
    for l1_size in L1_CACHE_SIZES:
        plot_l2_miss_rate_against_l2_sizes(
            all_runs=aggregated_results,
            selected_l1_size=l1_size,
            output_directory_path=timestamped_output_directory_path
        )
    
    print("DONE")
    


if __name__ == "__main__":
    main()
