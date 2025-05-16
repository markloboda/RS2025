from argparse import ArgumentParser
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Literal, Optional, Set, Tuple, Union

import matplotlib
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib import pyplot as plt


RUN_NAME_REGEX: re.Pattern = re.compile(r"t1_implementation-(.+)_precision-(.+)_hidden-layers-(.+)_repetition-(.+)\.log")

@dataclass(frozen=True, kw_only=True)
class RunParameters:
    precision: Union[Literal["float"], Literal["double"]]
    implementation: Union[Literal["sca"], Literal["avx2"]]
    hidden_layer_size: int
    repetition_index: int

    @classmethod
    def load_from_log_file_path(
        cls,
        log_file_path: Path
    ) -> "RunParameters":
        assert log_file_path.name.startswith("t1_")

        re_matches = RUN_NAME_REGEX.match(log_file_path.name)

        implementation = re_matches.group(1)
        precision = re_matches.group(2)
        hidden_layer_size = int(re_matches.group(3))
        repetition_index = int(re_matches.group(4))

        return cls(
            precision=precision,
            implementation=implementation,
            hidden_layer_size=hidden_layer_size,
            repetition_index=repetition_index
        )


RUN_TIME_REGEX: re.Pattern = re.compile(r"Average time: (\d+\.\d+)")

@dataclass(frozen=True, kw_only=True)
class Run:
    parameters: RunParameters
    run_average_time: float

    @classmethod
    def from_log_file_path(cls, log_file_path: Path) -> "Run":
        assert log_file_path.is_file()

        parameters = RunParameters.load_from_log_file_path(log_file_path)

        with log_file_path.open(mode="r", encoding="utf-8") as log_file:
            log_file_contents = log_file.read()

            run_average_time = float(RUN_TIME_REGEX.findall(log_file_contents)[0])
        
        return cls(parameters=parameters, run_average_time=run_average_time)




def plot_avx2_speedup(
    runs: List[Run],
    output_directory_path: Path
) -> None:
    figure: Figure = plt.figure(
        num="avx speedup",
        layout="constrained"
    )

    axes: Axes = figure.subplots(nrows=1, ncols=1)


    float_scalar_impl_times_per_size: Dict[int, List[float]] = {}
    double_scalar_impl_times_per_size: Dict[int, List[float]] = {}
    float_avx2_impl_times_per_size: Dict[int, List[float]] = {}
    double_avx2_impl_times_per_size: Dict[int, List[float]] = {}

    for run in runs:
        size: int = run.parameters.hidden_layer_size

        if run.parameters.precision == "float":
            if run.parameters.implementation == "sca":
                if size not in float_scalar_impl_times_per_size:
                    float_scalar_impl_times_per_size[size] = [run.run_average_time]
                else:
                    float_scalar_impl_times_per_size[size].append(run.run_average_time)
            elif run.parameters.implementation == "avx2":
                if size not in float_avx2_impl_times_per_size:
                    float_avx2_impl_times_per_size[size] = [run.run_average_time]
                else:
                    float_avx2_impl_times_per_size[size].append(run.run_average_time)
            else:
                raise RuntimeError()
        elif run.parameters.precision == "double":
            if run.parameters.implementation == "sca":
                if size not in double_scalar_impl_times_per_size:
                    double_scalar_impl_times_per_size[size] = [run.run_average_time]
                else:
                    double_scalar_impl_times_per_size[size].append(run.run_average_time)
            elif run.parameters.implementation == "avx2":
                if size not in double_avx2_impl_times_per_size:
                    double_avx2_impl_times_per_size[size] = [run.run_average_time]
                else:
                    double_avx2_impl_times_per_size[size].append(run.run_average_time)
            else:
                raise RuntimeError()
        else:
            raise RuntimeError(f"unexpected precision: {run.parameters.precision}")


    def compute_averages(map_with_samples: Dict[int, List[float]]) -> Dict[int, float]:
        averaged_map: Dict[int, float] = {}
        for key, values in map_with_samples.items():
            averaged_map[key] = sum(values) / len(values)
        
        return averaged_map
    
    
    float_scalar_impl_avg_time_per_size: Dict[int, float] = compute_averages(float_scalar_impl_times_per_size)
    double_scalar_impl_avg_time_per_size: Dict[int, float] = compute_averages(double_scalar_impl_times_per_size)
    float_avx2_impl_avg_time_per_size: Dict[int, float] = compute_averages(float_avx2_impl_times_per_size)
    double_avx2_impl_avg_time_per_size: Dict[int, float] = compute_averages(double_avx2_impl_times_per_size)

    def compute_speedups(reference: Dict[int, float], optimized: Dict[int, float]) -> List[Tuple[int, float]]:
        speedups: Dict[int, float] = {}

        assert set(reference.keys()) == set(optimized.keys())

        for key in reference.keys():
            speedups[key] = reference[key] / optimized[key]

        return sorted(
            speedups.items(),
            key=lambda item: item[0]
        )


    float_speedups_per_size: List[Tuple[int, float]] = compute_speedups(float_scalar_impl_avg_time_per_size, float_avx2_impl_avg_time_per_size)
    double_speedups_per_size: List[Tuple[int, float]] = compute_speedups(double_scalar_impl_avg_time_per_size, double_avx2_impl_avg_time_per_size)


    axes.plot(
        list(size for size, _ in float_speedups_per_size),
        list(speedup for _, speedup in float_speedups_per_size),
        "C0",
        label="Single precision"
    )

    axes.plot(
        list(size for size, _ in double_speedups_per_size),
        list(speedup for _, speedup in double_speedups_per_size),
        "C1",
        label="Double precision"
    )

    axes.xaxis.set_major_locator(matplotlib.ticker.FixedLocator(locs=list(size for size, _ in double_speedups_per_size)))
    axes.xaxis.minorticks_off()

    axes.legend(loc="best", title="$\\bf{Implementation}$")
    
    axes.set_title("")

    axes.set_ylabel("Speedup of AVX2 over scalar implementation")
    axes.set_xlabel("Size of hidden layer")


    figure.savefig(
        fname=output_directory_path.joinpath("task-1_avx2-speedup.svg"),
        format="svg",
        transparent=False,
        bbox_inches="tight"
    )



def main() -> None:
    argument_parser = ArgumentParser()

    argument_parser.add_argument(
        "-d",
        "--benchmark-directory",
        required=True,
        dest="benchmark_directory"
    )

    argument_parser.add_argument(
        "-o",
        "--output-directory-path",
        required=True,
        dest="output_directory"
    )

    arguments = argument_parser.parse_args()

    benchmark_directory = Path(arguments.benchmark_directory)
    output_directory = Path(arguments.output_directory)


    runs: List[Run] = []

    for file_name in os.listdir(benchmark_directory):
        full_file_path = benchmark_directory.joinpath(file_name)
        
        if full_file_path.suffix != ".log":
            continue

        runs.append(Run.from_log_file_path(full_file_path))

    print(f"Parsed {len(runs)} runs.")

    plot_avx2_speedup(runs=runs, output_directory_path=output_directory)

    print("DONE")


if __name__ == "__main__":
    main()
