#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <string.h>
#include <fcntl.h>
#include <errno.h>
#include "headers/disk.h"

#define BUFFER_SIZE 1024

int read_disk_usage(Disk_usage *stats)
{
    int fd[2];
    pid_t pid;
    char buffer[BUFFER_SIZE];

    if (pipe(fd) == -1)
    {
        perror("pipe failed");
        return -1;
    }

    pid = fork();
    if (pid == -1)
    {
        perror("fork failed");
        return -1;
    }

    if (pid == 0)
    {
        // Child process
        close(fd[0]); // Close read end

        if (dup2(fd[1], STDOUT_FILENO) == -1)
        {
            perror("dup2 failed");
            exit(1);
        }
        close(fd[1]);

        execlp("df", "df", "-h", NULL);
        perror("execlp failed");
        exit(1);
    }
    else
    {
        // Parent process
        close(fd[1]); // Close write end

        ssize_t nbytes = read(fd[0], buffer, sizeof(buffer) - 1);
        if (nbytes < 0)
        {
            perror("read failed");
            close(fd[0]);
            wait(NULL);
            return -1;
        }

        buffer[nbytes] = '\0';

        char *line = strtok(buffer, "\n");
        line = strtok(NULL, "\n");

        char filesystem[256], size[64], used[64], avail[64], percent[64], mount[256];

        int parsed = 0;

        if (line != NULL)
        {
            parsed = sscanf(line, "%s %s %s %s %s %s",
                            filesystem, size, used, avail, percent, mount);
        }

        if (parsed == 6)
        {
            if (size[strlen(size) - 1] == 'G')
            {
                size[strlen(size) - 1] = '\0';
                stats->total_disk = atoll(size);
            }

            if (used[strlen(used) - 1] == 'G')
            {
                used[strlen(used) - 1] = '\0';
                stats->disk_used = atoll(used);
            }

            if (avail[strlen(avail) - 1] == 'G')
            {
                avail[strlen(avail) - 1] = '\0';
                stats->free_disk = atoll(avail);
            }
        }

        stats->used_percent = (float)(stats->disk_used) / (float)(stats->total_disk) * 100.0;

        close(fd[0]);
        wait(NULL);
    }

    return 0;
}

static void write_disk_fifo(const char *fifo_path, const char *payload, int verbose)
{
    int fd = open(fifo_path, O_WRONLY | O_NONBLOCK);
    if (fd < 0)
    {
        if (verbose && errno != ENXIO)
        {
            perror("disk fifo open failed");
        }
        return;
    }

    size_t len = strlen(payload);
    if (write(fd, payload, len) < 0 && verbose)
    {
        perror("disk fifo write failed");
    }
    close(fd);
}

void get_disk_usage(int verbose, int count, const char *fifo_path)
{
    Disk_usage disk;
    (void)count;
    if (read_disk_usage(&disk) != 0)
    {
        fprintf(stderr, "Error reading memory stats\n");
        return;
    }

    char buffer[256];
    snprintf(buffer, sizeof(buffer),
             "{\"used_percent\":%.2f,\"used_gb\":%llu,\"total_gb\":%llu,\"free_gb\":%llu}\n",
             disk.used_percent,
             disk.disk_used,
             disk.total_disk,
             disk.free_disk);
    write_disk_fifo(fifo_path, buffer, verbose);
}