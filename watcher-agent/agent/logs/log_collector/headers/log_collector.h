#ifndef LOG_COLLECTOR_H
#define LOG_COLLECTOR_H

#include <stddef.h>
#include <sys/types.h>

#define FIFO_PATH "fifo/logs.fifo"
#define READ_CHUNK 4096
#define MAX_LINE 8192
#define MAX_OUTBUF (1024 * 1024)

typedef struct
{
    const char *path;
    const char *service;
    int fd;
    int wd;
    off_t offset;
    char *buf;
    size_t buf_len;
    size_t buf_cap;
} LogFile;

typedef struct
{
    char *data;
    size_t len;
    size_t sent;
    size_t cap;
} OutBuffer;

void safe_close(int *fd);

int open_log_file(LogFile *lf, int from_end);
int ensure_capacity(char **buf, size_t *cap, size_t needed);

int append_outbuf(OutBuffer *out, const char *data, size_t len);
int flush_outbuf(OutBuffer *out, int fifo_fd);
int ensure_fifo_open(int *fifo_fd);

void iso8601_now(char *buf, size_t len);
const char *detect_level(const char *line);
int extract_pid(const char *line);
void json_escape(const char *src, char *dst, size_t dst_len);
int build_json_line(const char *service, const char *line, char *out, size_t out_len);

int handle_line(LogFile *lf, const char *line, OutBuffer *out, int *fifo_fd);
int process_buffered_lines(LogFile *lf, OutBuffer *out, int *fifo_fd);
int read_new_data(LogFile *lf, OutBuffer *out, int *fifo_fd);

#endif
