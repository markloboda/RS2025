import re
import os
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import Dict, Optional, List

@dataclass
class BenchmarkData:
    name: str
    mode: str
    processors: int
    metrics: Dict[str, Optional[float]] = field(default_factory=dict)

def parse_value(value: str) -> Optional[float]:
    try:
        return float(value)
    except ValueError:
        return None

def parse_benchmark_file(file_path: str) -> List[BenchmarkData]:
    with open(file_path, 'r') as f:
        lines = f.readlines()

    results = []
    current_benchmark = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        header_match = re.match(r"\[(out_pi_(\w+)\.bin_(\d+))\]", line)
        if header_match:
            full_name = header_match.group(1)
            mode = header_match.group(2)
            processors = int(header_match.group(3))
            current_benchmark = BenchmarkData(name=full_name, mode=mode, processors=processors)
            results.append(current_benchmark)
        elif current_benchmark and ": " in line:
            key, value = map(str.strip, line.split(": "))
            current_benchmark.metrics[key] = parse_value(value)

    return results

def plot_cpi(benchmarks: List[BenchmarkData], out_file: str="plots/cpi_plot.png"):
    cpi_data: Dict[str, Dict[int, float]] = {}

    for bm in benchmarks:
        mode = bm.mode.lower()
        num_processors = bm.processors
        cpi_values = []

        for key, value in bm.metrics.items():
            if re.match(r"board\.processor\.cores\d+\.core\.cpi", key) and value is not None:
                cpi_values.append(value)

        if cpi_values:
            avg_cpi = sum(cpi_values) / len(cpi_values)
            if mode not in cpi_data:
                cpi_data[mode] = {}
            cpi_data[mode][num_processors] = avg_cpi

    plt.figure(figsize=(8, 6))
    for mode, proc_dict in cpi_data.items():
        sorted_processors = sorted(proc_dict.keys())
        avg_cpis = [proc_dict[p] for p in sorted_processors]

        if mode == "falsesharing":
            label = "False Sharing"
            color = 'red'
            marker = 'o'
        elif mode == "optimized":
            label = "Optimized"
            color = 'blue'
            marker = 's'
        else:
            label = mode
            color = 'black'
            marker = 'x'

        plt.plot(sorted_processors, avg_cpis, marker=marker, linestyle='-', color=color, label=label)

    plt.xlabel("Number of Processors")
    plt.ylabel("Average CPI")
    plt.title("Average CPI vs. Number of Processors")
    plt.xticks(sorted({bm.processors for bm in benchmarks}))
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_file)
    plt.close()
    print(f"CPI plot saved to {out_file}")

def plot_cache_invalidations(benchmarks: List[BenchmarkData], out_file: str="plots/cache_invalidation_plot.png"):
    inv_data: Dict[str, Dict[int, float]] = {}
    metric_key = "board.cache_hierarchy.ruby_system.L1Cache_Controller.Inv::total"

    for bm in benchmarks:
        mode = bm.mode.lower()
        num_processors = bm.processors
        value = bm.metrics.get(metric_key)
        if value is not None:
            if mode not in inv_data:
                inv_data[mode] = {}
            inv_data[mode][num_processors] = value

    plt.figure(figsize=(8, 6))
    for mode, proc_dict in inv_data.items():
        sorted_processors = sorted(proc_dict.keys())
        inv_values = [proc_dict[p] for p in sorted_processors]

        if mode == "falsesharing":
            label = "False Sharing"
            color = 'red'
            marker = 'o'
        elif mode == "optimized":
            label = "Optimized"
            color = 'blue'
            marker = 's'
        else:
            label = mode
            color = 'black'
            marker = 'x'

        plt.plot(sorted_processors, inv_values, marker=marker, linestyle='-', color=color, label=label)

    plt.xlabel("Number of Processors")
    plt.ylabel("Cache Invalidations")
    plt.title("Cache Invalidations vs. Number of Processors")
    plt.xticks(sorted({bm.processors for bm in benchmarks}))
    plt.yscale("log")
    plt.legend()
    plt.grid(True, which="both", linestyle=":", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(out_file)
    plt.close()
    print(f"Cache invalidation plot saved to {out_file}")

def plot_load_states(benchmarks: List[BenchmarkData], output_dir: str = "plots"):
    load_keys = {
        "I": "board.cache_hierarchy.ruby_system.L1Cache_Controller.I.Load::total",
        "S": "board.cache_hierarchy.ruby_system.L1Cache_Controller.S.Load::total",
        "E": "board.cache_hierarchy.ruby_system.L1Cache_Controller.E.Load::total",
        "M": "board.cache_hierarchy.ruby_system.L1Cache_Controller.M.Load::total"
    }

    os.makedirs(output_dir, exist_ok=True)
    
    for state, key in load_keys.items():
        state_data: Dict[str, Dict[int, float]] = {}

        for bm in benchmarks:
            mode = bm.mode.lower()
            procs = bm.processors
            value = bm.metrics.get(key)
            if value is not None:
                if mode not in state_data:
                    state_data[mode] = {}
                state_data[mode][procs] = value

        # Plotting
        plt.figure(figsize=(8, 6))
        for mode, color, marker in [("falsesharing", "red", "o"), ("optimized", "blue", "s")]:
            mode_data = state_data.get(mode, {})
            if mode_data:
                sorted_procs = sorted(mode_data.keys())
                values = [mode_data[p] for p in sorted_procs]
                label = "False Sharing" if mode == "falsesharing" else "Optimized"
                plt.plot(sorted_procs, values, marker=marker, linestyle='-', color=color, label=label)

        plt.xlabel("Number of Processors")
        plt.ylabel(f"{state}.Load (total)")
        plt.title(f"L1 {state} Load vs. Number of Processors")
        plt.xticks(sorted({bm.processors for bm in benchmarks}))
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        
        out_file = os.path.join(output_dir, f"load_{state}_plot.png")
        plt.savefig(out_file)
        plt.close()
        print(f"{state} load plot saved to {out_file}")

def plot_l2_requests(benchmarks: List[BenchmarkData], out_file: str="plots/l2_requests_plot.png"):
    # Define L2 request keys.
    key_gets = "board.cache_hierarchy.ruby_system.L2Cache_Controller.L1_GETS"
    key_getx = "board.cache_hierarchy.ruby_system.L2Cache_Controller.L1_GETX"
    
    # Group data by mode.
    l2_data = {"falsesharing": {}, "optimized": {}}
    
    for bm in benchmarks:
        mode = bm.mode.lower()
        if mode not in l2_data:
            continue
        procs = bm.processors
        gets = bm.metrics.get(key_gets)
        getx = bm.metrics.get(key_getx)
        if gets is not None and getx is not None:
            l2_data[mode][procs] = {"gets": gets, "getx": getx}
    
    # Create two subplots: one for false sharing and one for optimized.
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    for i, mode in enumerate(["falsesharing", "optimized"]):
        mode_data = l2_data.get(mode, {})
        sorted_procs = sorted(mode_data.keys())
        gets_values = [mode_data[p]["gets"] for p in sorted_procs]
        getx_values = [mode_data[p]["getx"] for p in sorted_procs]
        ax = axes[i]
        
        # Use a logarithmic scale for false sharing; for optimized, linear scale works well.
        if mode == "falsesharing":
            ax.set_yscale("log")
        
        ax.plot(sorted_procs, gets_values, marker='o', linestyle='-', color='red', label="L1_GETS")
        ax.plot(sorted_procs, getx_values, marker='s', linestyle='--', color='blue', label="L1_GETX")
        ax.set_xlabel("Number of Processors")
        ax.set_ylabel("L2 Request Count")
        title_mode = "False Sharing" if mode == "falsesharing" else "Optimized"
        ax.set_title(f"L2 Cache Requests – {title_mode}")
        ax.set_xticks(sorted_procs)
        ax.legend()
        ax.grid(True, which="both", linestyle=":", linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(out_file)
    plt.close()
    print(f"L2 requests plot saved to {out_file}")

def plot_execution_times(benchmarks: List[BenchmarkData], out_file: str="plots/execution_times_plot.png"):
    exec_data: Dict[str, Dict[int, float]] = {}
    metric_key = "simSeconds"
    
    for bm in benchmarks:
        mode = bm.mode.lower()
        procs = bm.processors
        sim_time = bm.metrics.get(metric_key)
        if sim_time is not None:
            if mode not in exec_data:
                exec_data[mode] = {}
            exec_data[mode][procs] = sim_time

    plt.figure(figsize=(8, 6))
    for mode, proc_dict in exec_data.items():
        sorted_processors = sorted(proc_dict.keys())
        times = [proc_dict[p] for p in sorted_processors]
        
        if mode == "falsesharing":
            label = "False Sharing"
            color = 'red'
            marker = 'o'
        elif mode == "optimized":
            label = "Optimized"
            color = 'blue'
            marker = 's'
        else:
            label = mode
            color = 'black'
            marker = 'x'
            
        plt.plot(sorted_processors, times, marker=marker, linestyle='-', color=color, label=label)
    
    plt.xlabel("Number of Processors")
    plt.ylabel("Execution Time (seconds)")
    plt.title("Execution Time vs. Number of Processors")
    plt.xticks(sorted({bm.processors for bm in benchmarks}))
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_file)
    plt.close()
    print(f"Execution time plot saved to {out_file}")


if __name__ == "__main__":
    # Change the file path if necessary
    data_file = "out/data.txt"
    benchmarks = parse_benchmark_file(data_file)
    
    if not benchmarks:
        print("No benchmark data found.")
    
    # Create plots folder if it doesn't exist
    os.makedirs("plots", exist_ok=True)
    
    # Plot CPI and cache invalidations
    plot_cpi(benchmarks, out_file="plots/cpi_plot.png")
    plot_cache_invalidations(benchmarks, out_file="plots/cache_invalidation_plot.png")
    plot_load_states(benchmarks, output_dir="plots/")
    plot_l2_requests(benchmarks, out_file="plots/l2_requests_plot.png")
    plot_execution_times(benchmarks, out_file="plots/execution_times_plot.png")