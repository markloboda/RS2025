# Copyright (c) 2022 The Regents of the University of California
# All rights reserved.


from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_cache_hierarchy import PrivateL1CacheHierarchy
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
from cpuO3_model import O3CPU
from gem5.resources.resource import CustomResource
import argparse

parser = argparse.ArgumentParser(description="CPU Benchmarking Script")
parser.add_argument("--width", type=int, required=True, help="Width of the CPU")
parser.add_argument("--rob_size", type=int, required=True, help="Reorder Buffer size")
parser.add_argument("--num_int_regs", type=int, default=60, help="Number of integer registers")
parser.add_argument("--num_fp_regs", type=int, default=60, help="Number of floating point registers")

args = parser.parse_args()

processorO3 = O3CPU(
    width=args.width,
    rob_size=args.rob_size,
    num_int_regs=args.num_int_regs,
    num_fp_regs=args.num_fp_regs
)


cache_hierarchy = PrivateL1CacheHierarchy(l1d_size="32KiB", l1i_size="32KiB")

memory = SingleChannelDDR3_1600("1GiB")


board = SimpleBoard(
    clk_freq="3GHz",
    processor=processorO3,
    memory=memory,
    cache_hierarchy=cache_hierarchy
)

# Resources can be found at
    # https://resources.gem5.org/
# x86-matrix-multiply is obtained from
    # https://resources.gem5.org/resources/x86-matrix-multiply-run?version=1.0.0



# Set the workload.
binary = CustomResource("../workload/whetstone.bin")
board.set_se_binary_workload(binary)

simulator = Simulator(board=board)
simulator.run()