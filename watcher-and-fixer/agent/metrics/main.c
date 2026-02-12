#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <sys/stat.h>
#include <sys/select.h>
#include <fcntl.h>
#include <errno.h>
#include <time.h>
#include "metrics_collector/headers/cpu.h"
#include "metrics_collector/headers/memory.h"
#include "metrics_collector/headers/disk.h"
#include "metrics_collector/headers/network.h"

int running = 1;

static const char *fifo_dir = "./fifo";
static const char *cpu_fifo = "./fifo/cpu.fifo";
static const char *memory_fifo = "./fifo/memory.fifo";
static const char *disk_fifo = "./fifo/disk.fifo";
static const char *network_fifo = "./fifo/network.fifo";
static const char *primary_fifo = "./fifo/primary.fifo";

void stop_program(int sig)
{
    printf("\nStopping...\n");
    running = 0;
}

void request_metrics_stop(void)
{
    running = 0;
}

static int ensure_directory(const char *path)
{
    struct stat st;
    if (stat(path, &st) == 0)
    {
        if (S_ISDIR(st.st_mode))
        {
            return 0;
        }
        fprintf(stderr, "Path exists but is not a directory: %s\n", path);
        return -1;
    }

    if (mkdir(path, 0755) != 0 && errno != EEXIST)
    {
        perror("Failed to create metrics directory");
        return -1;
    }

    return 0;
}

static int ensure_fifo(const char *path)
{
    struct stat st;
    if (stat(path, &st) == 0)
    {
        if (S_ISFIFO(st.st_mode))
        {
            return 0;
        }
        fprintf(stderr, "Path exists but is not a FIFO: %s\n", path);
        return -1;
    }

    if (mkfifo(path, 0666) != 0)
    {
        perror("Failed to create FIFO");
        return -1;
    }

    return 0;
}

static int open_fifo_reader(const char *path)
{
    int fd = open(path, O_RDONLY | O_NONBLOCK);
    if (fd < 0)
    {
        perror("Failed to open FIFO for reading");
    }
    return fd;
}

static int read_fifo_line(int fd, char *buffer, size_t size, int timeout_ms)
{
    if (fd < 0 || size == 0)
    {
        return 0;
    }

    fd_set read_set;
    struct timeval tv;
    FD_ZERO(&read_set);
    FD_SET(fd, &read_set);

    tv.tv_sec = timeout_ms / 1000;
    tv.tv_usec = (timeout_ms % 1000) * 1000;

    int ready = select(fd + 1, &read_set, NULL, NULL, &tv);
    if (ready <= 0)
    {
        return 0;
    }

    ssize_t nbytes = read(fd, buffer, size - 1);
    if (nbytes <= 0)
    {
        return 0;
    }

    buffer[nbytes] = '\0';

    char *newline = strchr(buffer, '\n');
    if (newline)
    {
        *newline = '\0';
    }

    return 1;
}

static void write_primary_fifo(const char *path, const char *payload, int verbose)
{
    int fd = open(path, O_RDWR | O_NONBLOCK);
    if (fd < 0)
    {
        if (verbose && errno != ENXIO)
        {
            perror("primary fifo open failed");
        }
        return;
    }

    size_t len = strlen(payload);
    if (write(fd, payload, len) < 0 && verbose)
    {
        perror("primary fifo write failed");
    }
    close(fd);
}

int run_metrics_collector(int argc, char *argv[])
{
    char *config_file = "default.yaml";
    int verbose = 0;
    int interval = 2;

#ifndef COMBINED_BUILD
    signal(SIGINT, stop_program);
#endif

    for (int i = 1; i < argc; i++)
    {
        if (strcmp(argv[i], "--config") == 0)
        {
            if (i + 1 < argc)
            {
                config_file = argv[i + 1];
                i++;
            }
        }
        else if (strcmp(argv[i], "--verbose") == 0)
        {
            verbose = 1;
        }
    }

    printf("Config: %s\n", config_file);
    printf("Verbose: %s\n", verbose ? "yes" : "no");
    printf("Interval: %d seconds\n\n", interval);
    printf("Press Ctrl+C to stop\n\n");

    if (ensure_directory(fifo_dir) != 0)
    {
        return 1;
    }

    if (ensure_fifo(cpu_fifo) != 0 ||
        ensure_fifo(memory_fifo) != 0 ||
        ensure_fifo(disk_fifo) != 0 ||
        ensure_fifo(network_fifo) != 0 ||
        ensure_fifo(primary_fifo) != 0)
    {
        fprintf(stderr, "Failed to ensure FIFOs\n");
        return 1;
    }

    int cpu_fd = open_fifo_reader(cpu_fifo);
    int memory_fd = open_fifo_reader(memory_fifo);
    int disk_fd = open_fifo_reader(disk_fifo);
    int network_fd = open_fifo_reader(network_fifo);

    if (cpu_fd < 0)
        fprintf(stderr, "Warning: Failed to open cpu_fd\n");
    if (memory_fd < 0)
        fprintf(stderr, "Warning: Failed to open memory_fd\n");
    if (disk_fd < 0)
        fprintf(stderr, "Warning: Failed to open disk_fd\n");
    if (network_fd < 0)
        fprintf(stderr, "Warning: Failed to open network_fd\n");

    int count = 0;
    while (running)
    {
        // CPU Metrics
        get_CPU_usage(verbose, count, cpu_fifo);
        get_memory_stats(verbose, count, memory_fifo);
        get_disk_usage(verbose, count, disk_fifo);
        get_network_stats(interval, verbose, count, network_fifo);

        char cpu_json[256] = "{}";
        char memory_json[320] = "{}";
        char disk_json[256] = "{}";
        char network_json[256] = "{}";

        read_fifo_line(cpu_fd, cpu_json, sizeof(cpu_json), 500);
        read_fifo_line(memory_fd, memory_json, sizeof(memory_json), 500);
        read_fifo_line(disk_fd, disk_json, sizeof(disk_json), 500);
        read_fifo_line(network_fd, network_json, sizeof(network_json), 500);

        char output_json[1280];
        time_t now = time(NULL);
        snprintf(output_json, sizeof(output_json),
                 "{\"timestamp\":%ld,\"count\":%d,\"cpu\":%s,\"memory\":%s,\"disk\":%s,\"network\":%s}\n",
                 (long)now,
                 count,
                 cpu_json,
                 memory_json,
                 disk_json,
                 network_json);
        write_primary_fifo(primary_fifo, output_json, verbose);

        count++;
        sleep(interval);
    }

    close(cpu_fd);
    close(memory_fd);
    close(disk_fd);
    close(network_fd);

    printf("\nStopped after %d readings\n", count);
    return 0;
}

#ifndef COMBINED_BUILD
int main(int argc, char *argv[])
{
    return run_metrics_collector(argc, argv);
}
#endif