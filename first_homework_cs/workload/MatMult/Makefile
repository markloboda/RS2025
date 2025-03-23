CC = gcc
CFLAGS = -Wall -O2

SRCS = $(wildcard *.c)
TARGETS = $(SRCS:.c=.bin)

all: $(TARGETS)

%.bin: %.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f $(TARGETS)

.PHONY: all clean
