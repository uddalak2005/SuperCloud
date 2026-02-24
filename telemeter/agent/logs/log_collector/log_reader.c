#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>

#include "headers/log_collector.h"

int open_log_file(LogFile *lf, int from_end)
{
    int fd = open(lf->path, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
    if (fd < 0)
    {
        return -1;
    }

    if (from_end)
    {
        off_t end = lseek(fd, 0, SEEK_END);
        if (end >= 0)
        {
            lf->offset = end;
        }
        else
        {
            lf->offset = 0;
        }
    }
    else
    {
        lf->offset = 0;
    }

    lf->fd = fd;
    return 0;
}

int handle_line(LogFile *lf, const char *line, OutBuffer *out, int *fifo_fd)
{
    char json[MAX_LINE * 2];
    int n = build_json_line(lf->service, line, json, sizeof(json));
    if (n <= 0)
    {
        return -1;
    }

    if (ensure_fifo_open(fifo_fd) == 0)
    {
        (void)flush_outbuf(out, *fifo_fd);
    }

    if (append_outbuf(out, json, (size_t)n) != 0)
    {
        return -1;
    }

    if (*fifo_fd >= 0)
    {
        if (flush_outbuf(out, *fifo_fd) != 0)
        {
            safe_close(fifo_fd);
        }
    }

    return 0;
}

int process_buffered_lines(LogFile *lf, OutBuffer *out, int *fifo_fd)
{
    size_t start = 0;
    for (size_t i = 0; i < lf->buf_len; i++)
    {
        if (lf->buf[i] == '\n')
        {
            lf->buf[i] = '\0';
            if (handle_line(lf, lf->buf + start, out, fifo_fd) != 0)
            {
                return -1;
            }
            start = i + 1;
        }
    }

    if (start > 0)
    {
        size_t remaining = lf->buf_len - start;
        memmove(lf->buf, lf->buf + start, remaining);
        lf->buf_len = remaining;
    }

    return 0;
}

int read_new_data(LogFile *lf, OutBuffer *out, int *fifo_fd)
{
    if (lf->fd < 0)
    {
        return -1;
    }

    if (lseek(lf->fd, lf->offset, SEEK_SET) < 0)
    {
        return -1;
    }

    char tmp[READ_CHUNK];
    for (;;)
    {
        ssize_t n = read(lf->fd, tmp, sizeof(tmp));
        if (n < 0)
        {
            if (errno == EAGAIN || errno == EWOULDBLOCK)
            {
                break;
            }
            return -1;
        }
        if (n == 0)
        {
            break;
        }

        lf->offset += (off_t)n;
        if (ensure_capacity(&lf->buf, &lf->buf_cap, lf->buf_len + (size_t)n + 1) != 0)
        {
            return -1;
        }
        memcpy(lf->buf + lf->buf_len, tmp, (size_t)n);
        lf->buf_len += (size_t)n;
        lf->buf[lf->buf_len] = '\0';

        if (process_buffered_lines(lf, out, fifo_fd) != 0)
        {
            return -1;
        }
    }

    return 0;
}
