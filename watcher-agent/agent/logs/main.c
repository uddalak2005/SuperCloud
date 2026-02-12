#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include "log_collector/headers/log_collector.h"

static volatile sig_atomic_t g_stop = 0;

static void handle_signal(int signo)
{
    (void)signo;
    g_stop = 1;
}

static void setup_signal_handlers(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = handle_signal;
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);
}

void request_logs_stop(void)
{
    g_stop = 1;
}

static void cleanup_files(LogFile *files, size_t count)
{
    for (size_t i = 0; i < count; i++)
    {
        safe_close(&files[i].fd);
        free(files[i].buf);
        files[i].buf = NULL;
        files[i].buf_len = 0;
        files[i].buf_cap = 0;
    }
}

static void check_rotation(LogFile *lf)
{
    struct stat st;
    if (stat(lf->path, &st) != 0)
    {
        return;
    }

    if (lf->offset > st.st_size)
    {
        safe_close(&lf->fd);
        (void)open_log_file(lf, 0);
    }
}

int run_logs_collector(void)
{
    LogFile files[] = {
        {"/var/log/node/app.log", "node", -1, -1, 0, NULL, 0, 0},
        {"/var/log/redis/redis.log", "redis", -1, -1, 0, NULL, 0, 0},
        {"/var/log/mysql/mysql.log", "mysql", -1, -1, 0, NULL, 0, 0},
    };
    const size_t file_count = sizeof(files) / sizeof(files[0]);

#ifndef COMBINED_BUILD
    setup_signal_handlers();
#endif

    for (size_t i = 0; i < file_count; i++)
    {
        if (open_log_file(&files[i], 1) != 0)
        {
            continue;
        }
    }

    OutBuffer out = {0};
    int fifo_fd = -1;
    time_t last_fifo_attempt = 0;

    (void)ensure_fifo_open(&fifo_fd);

    while (!g_stop)
    {
        time_t now = time(NULL);
        if (now != (time_t)-1 && now - last_fifo_attempt >= 2)
        {
            (void)ensure_fifo_open(&fifo_fd);
            last_fifo_attempt = now;
        }

        for (size_t i = 0; i < file_count; i++)
        {
            if (files[i].fd < 0)
            {
                (void)open_log_file(&files[i], 0);
                continue;
            }

            check_rotation(&files[i]);
            (void)read_new_data(&files[i], &out, &fifo_fd);
        }

        if (fifo_fd >= 0)
        {
            if (flush_outbuf(&out, fifo_fd) != 0)
            {
                safe_close(&fifo_fd);
            }
        }

        sleep(2);
    }

    safe_close(&fifo_fd);
    cleanup_files(files, file_count);
    free(out.data);

    return EXIT_SUCCESS;
}

#ifndef COMBINED_BUILD
int main(void)
{
    return run_logs_collector();
}
#endif
