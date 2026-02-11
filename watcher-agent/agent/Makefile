CC = gcc
TARGET = cpu_monitor

all: $(TARGET)

$(TARGET): main.o cpu.o
	$(CC) main.o cpu.o -o $(TARGET)

main.o: src/main.c
	$(CC) -c src/main.c -o main.o -I./src

cpu.o: src/metrics/cpu.c
	$(CC) -c src/metrics/cpu.c -o cpu.o

clean:
	rm -f *.o $(TARGET)
