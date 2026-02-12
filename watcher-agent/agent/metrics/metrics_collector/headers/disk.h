#ifndef DISK_H
#define DISK_H

typedef struct
{
    unsigned long long total_disk;
    unsigned long long disk_used;
    unsigned long long free_disk;
    float used_percent;
} Disk_usage;

int read_disk_usage(Disk_usage *stats);
void get_disk_usage(int verbose, int count, const char *fifo_path);

#endif