from argparse import ArgumentParser
from pathlib import Path
from dataclasses import dataclass
from typing import List
import matplotlib.pyplot as plt
import numpy as np

@dataclass(frozen=True, kw_only=True)
class RunSetupParameters:
    width: str
    rob_size: str
    predictor: str

@dataclass(frozen=True, kw_only=True)
class RunResults:
    cycles_per_instruction: float
    instructions_per_cycle: float
    branch_mispredicts: int

@dataclass(frozen=True, kw_only=True)
class Run:
    parameters: RunSetupParameters
    results: RunResults

def parse_aggregated_results(file_path: Path) -> List[Run]:
    runs = []
    current_run = {}

    # Read all non-empty stripped lines.
    with file_path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    for line in lines:
        if line.startswith("Run "):
            # If there is a previous run collected, process it.
            if current_run:
                runs.append(create_run_from_dict(current_run))
                current_run = {}
        else:
            # Remove any leading '>' if present.
            if line.startswith(">"):
                line = line.lstrip(">").strip()
            if ":" in line:
                key, value = line.split(":", 1)
                current_run[key.strip()] = value.strip()

    if current_run:
        runs.append(create_run_from_dict(current_run))

    return runs

def create_run_from_dict(data: dict) -> Run:
    params = RunSetupParameters(
        width=data["Issue Width"],
        rob_size=data["Reorder Buffer Size"],
        predictor=data["Predictor"]
    )

    results = RunResults(
        instructions_per_cycle=float(data["Instructions per cycle (IPC)"]),
        cycles_per_instruction=float(data["Cycles per instruction (CPI)"]),
        branch_mispredicts=int(data["Branch Mispredicts"])
    )

    return Run(parameters=params, results=results)

def plot_cpi_vs_rob(results: List[Run], output_directory_path: Path):
    predictors = sorted(set(run.parameters.predictor for run in results))
    rob_sizes = sorted(set(run.parameters.rob_size for run in results))

    predictor_cpi = {predictor: [] for predictor in predictors}
    for rob_size in rob_sizes:
        for predictor in predictors:
            cpi_value = next((run.results.cycles_per_instruction for run in results if run.parameters.rob_size == rob_size and run.parameters.predictor == predictor), None)
            predictor_cpi[predictor].append(cpi_value)

    plt.figure(figsize=(8, 5))
    for predictor in predictors:
        plt.plot(rob_sizes, predictor_cpi[predictor], marker='o', linestyle='-', label=predictor)

    plt.xlabel("ROB Size")
    plt.ylabel("CPI")
    plt.title("CPI vs. ROB Size for Different Branch Predictors")
    plt.legend()
    plt.grid(True)

    output_directory_path.mkdir(parents=True, exist_ok=True)
    output_path = output_directory_path / "cpi_vs_rob.png"
    plt.savefig(output_path)
    plt.close()

def plot_branch_mispredictions_vs_rob(results: List[Run], output_directory_path: Path):
    predictors = sorted(set(run.parameters.predictor for run in results))
    rob_sizes = sorted(set(run.parameters.rob_size for run in results))

    predictor_mispredictions = {predictor: [] for predictor in predictors}
    for rob_size in rob_sizes:
        for predictor in predictors:
            misprediction_value = next((run.results.branch_mispredicts for run in results if run.parameters.rob_size == rob_size and run.parameters.predictor == predictor), None)
            predictor_mispredictions[predictor].append(misprediction_value)

    plt.figure(figsize=(8, 5))
    for predictor in predictors:
        plt.plot(rob_sizes, predictor_mispredictions[predictor], marker='o', linestyle='-', label=predictor)

    plt.xlabel("ROB Size")
    plt.ylabel("Branch Mispredictions")
    plt.title("Branch Mispredictions vs. ROB Size for Different Branch Predictors")
    plt.legend()
    plt.grid(True)

    output_directory_path.mkdir(parents=True, exist_ok=True)
    output_path = output_directory_path / "branch_mispredictions_vs_rob.png"
    plt.savefig(output_path)
    plt.close()


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--aggregated-results-file",
        required=True,
        help="Path to the aggregated results file."
    )
    parser.add_argument(
        "--output-directory-path",
        required=True,
        help="Directory to save the plots."
    )
    args = parser.parse_args()

    results_file = Path(args.aggregated_results_file)
    if not results_file.is_file():
        print(f"File does not exist: {results_file}")
        exit(1)

    output_directory_path = Path(args.output_directory_path)

    aggregated_results: List[Run] = parse_aggregated_results(results_file)
    print(f"Found {len(aggregated_results)} runs in the aggregated results file.")

    plt.style.use("ggplot")

    plot_cpi_vs_rob(
        results=aggregated_results,
        output_directory_path=output_directory_path
    )

    plot_branch_mispredictions_vs_rob(
        results=aggregated_results,
        output_directory_path=output_directory_path
    )

    print("Plots saved in:", output_directory_path.as_posix())

if __name__ == "__main__":
    main()
