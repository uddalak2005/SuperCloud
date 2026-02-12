#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "headers/log_collector.h"

int append_outbuf(OutBuffer *out, const char *data, size_t len)
{
    if (len == 0)
    {
        return 0;
    }
    if (out->len + len > MAX_OUTBUF)
    {
        return -1;
    }
    if (ensure_capacity(&out->data, &out->cap, out->len + len) != 0)
    {
        return -1;
    }
    memcpy(out->data + out->len, data, len);
    out->len += len;
    return 0;
}

int flush_outbuf(OutBuffer *out, int fifo_fd)
{
    if (fifo_fd < 0 || out->len == 0)
    {
        return 0;
    }

    while (out->sent < out->len)
    {
        ssize_t n = write(fifo_fd, out->data + out->sent, out->len - out->sent);
        if (n < 0)
        {
            if (errno == EAGAIN || errno == EWOULDBLOCK)
            {
                return 0;
            }
            return -1;
        }
        out->sent += (size_t)n;
    }

    out->len = 0;
    out->sent = 0;
    return 0;
}

static int ensure_fifo_exists(void)
{
    struct stat st;
    if (stat(FIFO_PATH, &st) == 0)
    {
        return S_ISFIFO(st.st_mode) ? 0 : -1;
    }

    if (errno != ENOENT)
    {
        return -1;
    }

    if (mkdir("fifo", 0755) != 0 && errno != EEXIST)
    {
        return -1;
    }

    if (mkfifo(FIFO_PATH, 0644) != 0 && errno != EEXIST)
    {
        return -1;
    }

    return 0;
}

int ensure_fifo_open(int *fifo_fd)
{
    if (*fifo_fd >= 0)
    {
        return 0;
    }

    if (ensure_fifo_exists() != 0)
    {
        return -1;
    }

    int fd = open(FIFO_PATH, O_RDWR | O_NONBLOCK | O_CLOEXEC);
    if (fd < 0)
    {
        return -1;
    }

    *fifo_fd = fd;
    return 0;
}
