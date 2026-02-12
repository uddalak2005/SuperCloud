CC = gcc
TARGET = watcher_agent
BUILD_DIR = build

OBJS = $(BUILD_DIR)/main.o $(BUILD_DIR)/cpu.o $(BUILD_DIR)/memory.o $(BUILD_DIR)/disk.o $(BUILD_DIR)/network.o $(BUILD_DIR)/logs.o

all: $(BUILD_DIR) $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(OBJS) -o $(TARGET)

$(BUILD_DIR)/main.o: src/main.c
	$(CC) -c src/main.c -o $(BUILD_DIR)/main.o -I./src

$(BUILD_DIR)/cpu.o: src/metrics/cpu.c
	$(CC) -c src/metrics/cpu.c -o $(BUILD_DIR)/cpu.o

$(BUILD_DIR)/memory.o: src/metrics/memory.c
	$(CC) -c src/metrics/memory.c -o $(BUILD_DIR)/memory.o

$(BUILD_DIR)/disk.o : src/metrics/disk.c
	$(CC) -c src/metrics/disk.c -o $(BUILD_DIR)/disk.o

$(BUILD_DIR)/network.o : src/metrics/network.c
	$(CC) -c src/metrics/network.c -o $(BUILD_DIR)/network.o

$(BUILD_DIR)/logs.o : src/logs/logs.c
	$(CC) -c src/logs/logs.c -o $(BUILD_DIR)/logs.o

$(BUILD_DIR) :
	mkdir -p $(BUILD_DIR)

clean:
	rm -f *.o $(TARGET)