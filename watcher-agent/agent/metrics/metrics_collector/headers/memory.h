#ifndef MEMORY_H
#define MEMORY_H

typedef struct
{
    unsigned long long total_kb;
    unsigned long long available_kb;
    unsigned long long used_kb;
    float used_percent;

    unsigned long long swap_total;
    unsigned long long swap_free;
    unsigned long long swap_used;
    float swap_used_percent;

} Memory_Usage;

int read_memory_stats(Memory_Usage *stats);
void get_memory_stats(int verbose, int count, const char *fifo_path);

#endif