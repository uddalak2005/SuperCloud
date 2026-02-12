#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <errno.h>
#include <unistd.h>
#include "headers/network.h"

static int first_call = 1;
static Network_Usage previous = {0, 0};

int read_network_stats(Network_Usage *stats)
{
    FILE *fp = fopen("/proc/net/dev", "r");
    if (!fp)
    {
        perror("Failed to open /proc/net/dev");
        return -1;
    }

    char line[256];
    stats->rx_bytes = 0;
    stats->tx_bytes = 0;

    // Skip the first two header lines
    fgets(line, sizeof(line), fp);
    fgets(line, sizeof(line), fp);

    while (fgets(line, sizeof(line), fp))
    {
        char iface[64];
        unsigned long long rx, tx;

        if (sscanf(line, " %[^:]: %llu %*s %*s %*s %*s %*s %*s %*s %llu",
                   iface, &rx, &tx) == 3)
        {
            // Skip loopback interface
            if (strcmp(iface, "lo") != 0)
            {
                stats->rx_bytes += rx;
                stats->tx_bytes += tx;
            }
        }
    }

    fclose(fp);
    return 0;
}

static void write_network_fifo(const char *fifo_path, const char *payload, int verbose)
{
    int fd = open(fifo_path, O_RDWR | O_NONBLOCK);
    if (fd < 0)
    {
        if (verbose && errno != ENXIO)
        {
            perror("network fifo open failed");
        }
        return;
    }

    size_t len = strlen(payload);
    if (write(fd, payload, len) < 0 && verbose)
    {
        perror("network fifo write failed");
    }
    close(fd);
}

void get_network_stats(int interval, int verbose, int count, const char *fifo_path)
{
    Network_Usage current;
    (void)count;

    // Read current stats
    if (read_network_stats(&current) != 0)
    {
        fprintf(stderr, "Error reading network stats\n");
        return;
    }

    unsigned long long rx_speed = 0;
    unsigned long long tx_speed = 0;
    int baseline = 0;

    if (first_call)
    {
        previous = current;
        first_call = 0;
        baseline = 1;
    }
    else
    {
        rx_speed = (current.rx_bytes - previous.rx_bytes) / interval;
        tx_speed = (current.tx_bytes - previous.tx_bytes) / interval;
        previous = current;
    }

    char buffer[256];
    snprintf(buffer, sizeof(buffer),
             "{\"rx_bytes_per_sec\":%llu,\"tx_bytes_per_sec\":%llu,\"baseline\":%s}\n",
             rx_speed,
             tx_speed,
             baseline ? "true" : "false");
    write_network_fifo(fifo_path, buffer, verbose);
}