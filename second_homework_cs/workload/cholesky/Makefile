GEM5_PATH = /d/hpc/projects/FRI/GEM5/gem5_workspace/gem5/
ISA = x86
GXX = gcc

TARGET = cholesky
SRC = $(TARGET).c
BIN = $(TARGET).bin

all: $(BIN)

$(BIN): $(SRC)
	$(GXX) -o $(BIN) $(SRC) -O2 -lm -fopenmp -lpthread -I$(GEM5_PATH)/include -L$(GEM5_PATH)/util/m5/build/$(ISA)/out -I$(GEM5_PATH)/util/m5/src -lm5 -DGEM5

clean:
	rm -f $(BIN)