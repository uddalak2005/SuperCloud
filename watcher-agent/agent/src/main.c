// src/main.c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include "metrics/cpu.h"

int running = 1;

void stop_program(int sig)
{
    printf("\nStopping...\n");
    running = 0;
}

int main(int argc, char *argv[])
{
    char *config_file = "default.yaml";
    int verbose = 0;
    int interval = 2;

    signal(SIGINT, stop_program);

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

    printf("=== CPU Monitor ===\n");
    printf("Config: %s\n", config_file);
    printf("Verbose: %s\n", verbose ? "yes" : "no");
    printf("Interval: %d seconds\n\n", interval);
    printf("Press Ctrl+C to stop\n\n");

    CPUStats prev_stats, curr_stats;

    if (read_CPU_stats(&prev_stats) != 0)
    {
        fprintf(stderr, "Failed to read initial CPU stats\n");
        return 1;
    }

    if (verbose)
    {
        printf("Initial reading complete\n");
    }

    int count = 0;
    while (running)
    {
        count++;
        sleep(interval);

        if (read_CPU_stats(&curr_stats) != 0)
        {
            fprintf(stderr, "Failed to read CPU stats\n");
            continue;
        }

        float cpu_usage = calculate_CPU_usage(&prev_stats, &curr_stats);

        printf("[%d] CPU: %.2f%%\n", count, cpu_usage);

        if (verbose)
        {
            printf("    Total: %llu, Idle: %llu\n",
                   get_total_CPU_time(&curr_stats),
                   get_idle_CPU_time(&curr_stats));
        }

        prev_stats = curr_stats;
    }

    printf("\nStopped after %d readings\n", count);
    return 0;
}