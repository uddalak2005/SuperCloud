#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include "cpu.h"

static int first_call = 1;
static CPUStats prev_stats;

int read_CPU_stats(CPUStats *stats)
{

    FILE *fp = fopen("/proc/stat", "r");

    if (fp == NULL)
    {
        perror("Failed to open /proc/stat\n");
        return -1;
    }

    char line[256];

    if (fgets(line, sizeof(line), fp) == NULL)
    {
        fclose(fp);
        return -1;
    }

    int parsed = sscanf(line, "cpu %llu %llu %llu %llu %llu %llu %llu %llu",
                        &stats->user,
                        &stats->nice,
                        &stats->system,
                        &stats->idle,
                        &stats->iowait,
                        &stats->irq,
                        &stats->softirq,
                        &stats->steal);

    fclose(fp);

    if (parsed < 8)
    {
        fprintf(stderr, "Failed to parse /proc/stat\n");
        return -1;
    }

    return 0;
}

unsigned long long get_total_CPU_time(CPUStats *stats)
{
    return stats->user + stats->nice + stats->system +
           stats->idle + stats->iowait + stats->irq +
           stats->softirq + stats->steal;
}

unsigned long long get_idle_CPU_time(CPUStats *stats)
{
    return stats->idle + stats->iowait;
}

float calculate_CPU_usage(CPUStats *prev, CPUStats *curr)
{
    unsigned long long prev_total = get_total_CPU_time(prev);
    unsigned long long curr_total = get_total_CPU_time(curr);

    unsigned long long prev_idle = get_idle_CPU_time(prev);
    unsigned long long curr_idle = get_idle_CPU_time(curr);

    unsigned long long total_delta = curr_total - prev_total;
    unsigned long long total_idle = curr_idle - prev_idle;

    if (total_delta == 0)
    {
        return 0.0;
    }

    float usage = (float)(total_delta - total_idle) / (float)total_delta * 100.0;

    return usage;
}

void get_CPU_usage(int verbose, int count)
{
    CPUStats curr_stats;

    if (read_CPU_stats(&curr_stats) != 0)
    {
        fprintf(stderr, "Failed to read CPU stats\n");
        return;
    }

    if (first_call)
    {
        prev_stats = curr_stats;
        first_call = 0;
        if (verbose)
        {
            printf("[%d] CPU: Initial baseline established\n", count);
        }
        return;
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