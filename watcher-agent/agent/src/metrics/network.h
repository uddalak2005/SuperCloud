#ifndef NETWROK_H
#define NETWORK_H

typedef struct
{
    unsigned long long rx_bytes;
    unsigned long long tx_bytes;
} Network_Usage;

int read_network_stats(Network_Usage *stats);
void get_network_stats(int interval, int verbose, int count);

#endif