#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "headers/log_collector.h"

void iso8601_now(char *buf, size_t len)
{
    struct timespec ts;
    struct tm tm_val;
    if (clock_gettime(CLOCK_REALTIME, &ts) != 0)
    {
        buf[0] = '\0';
        return;
    }
    if (!localtime_r(&ts.tv_sec, &tm_val))
    {
        buf[0] = '\0';
        return;
    }

    char tz[8];
    strftime(tz, sizeof(tz), "%z", &tm_val);

    char ts_base[32];
    strftime(ts_base, sizeof(ts_base), "%Y-%m-%dT%H:%M:%S", &tm_val);

    if (strlen(tz) == 5)
    {
        snprintf(buf, len, "%s%c%c%c:%c%c", ts_base, tz[0], tz[1], tz[2], tz[3], tz[4]);
    }
    else
    {
        snprintf(buf, len, "%s", ts_base);
    }
}

const char *detect_level(const char *line)
{
    if (strstr(line, "ERROR") || strstr(line, "Error") || strstr(line, "error"))
    {
        return "ERROR";
    }
    if (strstr(line, "WARN") || strstr(line, "Warning") || strstr(line, "warning"))
    {
        return "WARN";
    }
    if (strstr(line, "INFO") || strstr(line, "Info") || strstr(line, "info"))
    {
        return "INFO";
    }
    return "UNKNOWN";
}

int extract_pid(const char *line)
{
    const char *p = strstr(line, "pid=");
    if (!p)
    {
        p = strstr(line, "pid:");
    }
    if (p)
    {
        p += 4;
        return atoi(p);
    }

    if (line[0] == '[')
    {
        char *end = NULL;
        long val = strtol(line + 1, &end, 10);
        if (end && *end == ']')
        {
            return (int)val;
        }
    }

    return -1;
}

void json_escape(const char *src, char *dst, size_t dst_len)
{
    size_t di = 0;
    for (size_t i = 0; src[i] != '\0' && di + 2 < dst_len; i++)
    {
        unsigned char c = (unsigned char)src[i];
        if (c == '"' || c == '\\')
        {
            if (di + 2 >= dst_len)
            {
                break;
            }
            dst[di++] = '\\';
            dst[di++] = (char)c;
        }
        else if (c == '\n')
        {
            dst[di++] = '\\';
            dst[di++] = 'n';
        }
        else if (c == '\r')
        {
            dst[di++] = '\\';
            dst[di++] = 'r';
        }
        else if (c == '\t')
        {
            dst[di++] = '\\';
            dst[di++] = 't';
        }
        else if (c < 0x20)
        {
            continue;
        }
        else
        {
            dst[di++] = (char)c;
        }
    }
    dst[di] = '\0';
}

int build_json_line(const char *service, const char *line, char *out, size_t out_len)
{
    char ts[64];
    char host[256];
    char msg[MAX_LINE];

    iso8601_now(ts, sizeof(ts));
    if (gethostname(host, sizeof(host)) != 0)
    {
        strncpy(host, "unknown", sizeof(host));
        host[sizeof(host) - 1] = '\0';
    }

    json_escape(line, msg, sizeof(msg));

    const char *level = detect_level(line);
    int pid = extract_pid(line);

    if (pid >= 0)
    {
        return snprintf(out, out_len,
                        "{\"timestamp\":\"%s\",\"service\":\"%s\",\"level\":\"%s\",\"message\":\"%s\",\"pid\":%d,\"host\":\"%s\"}\n",
                        ts, service, level, msg, pid, host);
    }

    return snprintf(out, out_len,
                    "{\"timestamp\":\"%s\",\"service\":\"%s\",\"level\":\"%s\",\"message\":\"%s\",\"host\":\"%s\"}\n",
                    ts, service, level, msg, host);
}
