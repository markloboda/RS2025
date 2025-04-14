# Makefile to compile all C programs in the folder with OpenMP support

# Compiler
CC = gcc

# Compiler flags
CFLAGS = -fopenmp -Wall 

# Source files and object files
SRCS = $(wildcard *.c)
OBJS = $(SRCS:.c=.o)

# Executables with .bin extension
EXES = $(SRCS:.c=.bin)

# Default target
all: $(EXES)

# Rule to build each executable
%.bin: %.o
	$(CC) $(CFLAGS) -o $@ $<

# Rule to compile each source file
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Clean up
clean:
	rm -f $(OBJS) $(EXES)