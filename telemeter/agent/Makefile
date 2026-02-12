CC = gcc
BUILD_DIR = build
TARGET = $(BUILD_DIR)/metrics_collector.o
LOGS_TARGET = $(BUILD_DIR)/log_collector.o
COMBINED_TARGET = $(BUILD_DIR)/watcher_agent_all.o

SRC_DIR = metrics
COLLECTOR_DIR = $(SRC_DIR)/metrics_collector
INCLUDES = -I$(COLLECTOR_DIR)/headers

LOGS_INCLUDES = -Ilogs/log_collector/headers
LOGS_SRCS = logs/main.c \
	logs/log_collector/util.c \
	logs/log_collector/fifo_writer.c \
	logs/log_collector/json_format.c \
	logs/log_collector/log_reader.c

OBJS = $(BUILD_DIR)/main.o \
	$(BUILD_DIR)/cpu.o \
	$(BUILD_DIR)/memory.o \
	$(BUILD_DIR)/disk.o \
	$(BUILD_DIR)/network.o

COMBINED_INCLUDES = $(INCLUDES) $(LOGS_INCLUDES)
COMBINED_SRCS = combined_main.c \
	metrics/main.c \
	metrics/metrics_collector/cpu.c \
	metrics/metrics_collector/memory.c \
	metrics/metrics_collector/disk.c \
	metrics/metrics_collector/network.c \
	logs/main.c \
	logs/log_collector/util.c \
	logs/log_collector/fifo_writer.c \
	logs/log_collector/json_format.c \
	logs/log_collector/log_reader.c

all: $(BUILD_DIR) $(TARGET) $(LOGS_TARGET) $(COMBINED_TARGET)

$(TARGET): $(OBJS)
	$(CC) $(OBJS) -o $(TARGET)

$(BUILD_DIR)/main.o: $(SRC_DIR)/main.c
	$(CC) -c $(SRC_DIR)/main.c -o $(BUILD_DIR)/main.o $(INCLUDES)

$(BUILD_DIR)/cpu.o: $(COLLECTOR_DIR)/cpu.c
	$(CC) -c $(COLLECTOR_DIR)/cpu.c -o $(BUILD_DIR)/cpu.o $(INCLUDES)

$(BUILD_DIR)/memory.o: $(COLLECTOR_DIR)/memory.c
	$(CC) -c $(COLLECTOR_DIR)/memory.c -o $(BUILD_DIR)/memory.o $(INCLUDES)

$(BUILD_DIR)/disk.o : $(COLLECTOR_DIR)/disk.c
	$(CC) -c $(COLLECTOR_DIR)/disk.c -o $(BUILD_DIR)/disk.o $(INCLUDES)

$(BUILD_DIR)/network.o : $(COLLECTOR_DIR)/network.c
	$(CC) -c $(COLLECTOR_DIR)/network.c -o $(BUILD_DIR)/network.o $(INCLUDES)

$(BUILD_DIR) :
	mkdir -p $(BUILD_DIR)

logs: $(LOGS_TARGET)

$(LOGS_TARGET): $(LOGS_SRCS)
	$(CC) $(LOGS_SRCS) -o $(LOGS_TARGET) $(LOGS_INCLUDES)

$(COMBINED_TARGET): $(COMBINED_SRCS)
	$(CC) $(COMBINED_SRCS) -o $(COMBINED_TARGET) $(COMBINED_INCLUDES) -DCOMBINED_BUILD -pthread

run-logs: $(LOGS_TARGET)
	./$(LOGS_TARGET)

run-all: $(COMBINED_TARGET)
	./$(COMBINED_TARGET)

setup-test-logs:
	mkdir -p /var/log/node /var/log/redis /var/log/mysql
	touch /var/log/node/app.log /var/log/redis/redis.log /var/log/mysql/mysql.log
	mkdir -p fifo
# 	rm -f fifo/logs.fifo
# 	mkfifo fifo/logs.fifo

write-test-logs:
	@echo "INFO pid=123 startup complete" >> /var/log/node/app.log
	@echo "WARN cache miss" >> /var/log/redis/redis.log
	@echo "ERROR pid=999 query failed" >> /var/log/mysql/mysql.log

clean:
	rm -f $(BUILD_DIR)/*.o $(TARGET) $(LOGS_TARGET) $(COMBINED_TARGET)
	rm -rf fifo