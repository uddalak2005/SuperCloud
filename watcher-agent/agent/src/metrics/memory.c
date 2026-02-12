#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include "memory.h"

#define BUFFER_SIZE 4096

int read_memory_stats(Memory_Usage *stats)
{
    int fd = open("/proc/meminfo", O_RDONLY);
    if (fd < 0)
    {
        perror("Failed to open file");
        return -1;
    }

    char buffer[BUFFER_SIZE];
    size_t size = read(fd, buffer, sizeof(buffer) - 1);
    buffer[size] = '\0';

    unsigned long long mem_total = 0;
    unsigned long long mem_available = 0;
    unsigned long long swap_total = 0;
    unsigned long long swap_available = 0;

    int found = 0;

    // Breaking buffer to lines
    char *line = strtok(buffer, "\n"); // Breaks into first line and replaces the \n with \0 after the end of first line

    while (line != NULL)
    {
        if (sscanf(line, "MemTotal: %llu kB", &mem_total) == 1)
        {
            found++;
        }
        else if (sscanf(line, "MemAvailable: %llu kB", &mem_available) == 1)
        {
            found++;
        }
        else if (sscanf(line, "SwapTotal: %llu kB", &swap_total) == 1)
        {
            found++;
        }
        else if (sscanf(line, "SwapFree: %llu kB", &swap_available) == 1)
        {
            found++;
        }

        line = strtok(NULL, "\n"); // Starts frm where it left \0 then continues tokenization
    }

    if (found < 4)
    {
        fprintf(stderr, "Failed to parse /proc/meminfo (found %d/4 fields)\n", found);
        return -1;
    }

    close(fd);

    stats->total_kb = mem_total;
    stats->available_kb = mem_available;
    stats->used_kb = mem_total - mem_available;
    if (mem_total > 0)
    {
        stats->used_percent = (float)(mem_total - mem_available) / (float)mem_total * 100.00;
    }
    else
    {
        stats->used_percent = 0.0;
    }

    stats->swap_total = swap_total;
    stats->swap_free = swap_available;
    stats->swap_used = swap_total - swap_available;

    if (swap_total > 0)
    {
        stats->swap_used_percent = (float)stats->swap_used / (float)swap_total * 100.0;
    }
    else
    {
        stats->swap_used_percent = 0.0;
    }

    return 0;
}

void get_memory_stats(int verbose, int count)
{
    Memory_Usage memory;
    if (read_memory_stats(&memory) != 0)
    {
        fprintf(stderr, "Error reading memory stats\n");
        return;
    }

    fflush(stdout);

    printf("[%d] Memory: %.2f%% (%.2f GB / %.2f GB)\n",
           count,

           memory.used_percent,
           memory.used_kb / 1024.0 / 1024.0, // Convert KB to GB
           memory.total_kb / 1024.0 / 1024.0);

    if (verbose)
    {
        printf("    Memory Available: %.2f GB\n",
               memory.available_kb / 1024.0 / 1024.0);
        printf("    Swap: %.2f%% (%.2f GB / %.2f GB)\n",
               memory.swap_used_percent,
               memory.swap_used / 1024.0 / 1024.0,
               memory.swap_total / 1024.0 / 1024.0);
    }

    return;
}