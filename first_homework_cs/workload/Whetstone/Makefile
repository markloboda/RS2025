CC = gcc
CFLAGS = -Wall -O2
LDFLAGS = -lm
TARGET = whetstone.bin

all: $(TARGET)

$(TARGET): whetstone.o
	$(CC) $(CFLAGS) -o $(TARGET) whetstone.o $(LDFLAGS)

whetstone.o: whetstone.c
	$(CC) $(CFLAGS) -c whetstone.c

clean:
	rm -f $(TARGET) whetstone.o

.PHONY: all clean