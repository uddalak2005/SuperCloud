#include <stdlib.h>
#include <unistd.h>

#include "headers/log_collector.h"

void safe_close(int *fd)
{
    if (*fd >= 0)
    {
        close(*fd);
        *fd = -1;
    }
}

int ensure_capacity(char **buf, size_t *cap, size_t needed)
{
    if (*cap >= needed)
    {
        return 0;
    }

    size_t new_cap = (*cap == 0) ? 1024 : *cap;
    while (new_cap < needed)
    {
        new_cap *= 2;
    }

    char *tmp = realloc(*buf, new_cap);
    if (!tmp)
    {
        return -1;
    }
    *buf = tmp;
    *cap = new_cap;
    return 0;
}
