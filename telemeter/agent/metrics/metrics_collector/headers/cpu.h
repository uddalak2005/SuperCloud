#ifndef CPU_H
#define CPU_H

typedef struct
{
    /* data */
    unsigned long long user;
    unsigned long long nice;
    unsigned long long system;
    unsigned long long idle;
    unsigned long long iowait;
    unsigned long long irq;
    unsigned long long softirq;
    unsigned long long steal;
} CPUStats;

int read_CPU_stats(CPUStats *stats);
unsigned long long get_total_CPU_time(CPUStats *stats);
unsigned long long get_idle_CPU_time(CPUStats *stats);
float calculate_CPU_usage(CPUStats *prev, CPUStats *curr);
void get_CPU_usage(int verbose, int count, const char *fifo_path);

#endif