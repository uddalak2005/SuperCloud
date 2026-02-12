#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "network.h"

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

void get_network_stats(int interval, int verbose, int count)
{
    Network_Usage current;

    // Read current stats
    if (read_network_stats(&current) != 0)
    {
        fprintf(stderr, "Error reading network stats\n");
        return;
    }

    if (first_call)
    {
        previous = current;
        first_call = 0;
        if (verbose)
        {
            printf("[%d] Network: Initial baseline established\n", count);
        }
        return;
    }

    unsigned long long rx_speed = (current.rx_bytes - previous.rx_bytes) / interval;
    unsigned long long tx_speed = (current.tx_bytes - previous.tx_bytes) / interval;

    printf("[%d] Current Transfer Rates: Download - %llu\t|\tUpload - %llu\n", count, rx_speed, tx_speed);

    previous = current;

    return;
}