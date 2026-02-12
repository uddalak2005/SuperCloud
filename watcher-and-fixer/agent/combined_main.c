#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>

int run_logs_collector(void);
int run_metrics_collector(int argc, char *argv[]);
void request_logs_stop(void);
void request_metrics_stop(void);

static void handle_signal(int signo)
{
    (void)signo;
    request_logs_stop();
    request_metrics_stop();
}

typedef struct
{
    int argc;
    char **argv;
    int result;
} MetricsArgs;

static void *logs_thread(void *arg)
{
    (void)arg;
    (void)run_logs_collector();
    return NULL;
}

static void *metrics_thread(void *arg)
{
    MetricsArgs *args = (MetricsArgs *)arg;
    args->result = run_metrics_collector(args->argc, args->argv);
    return NULL;
}

int main(int argc, char *argv[])
{
    struct sigaction sa;
    sigemptyset(&sa.sa_mask);
    sa.sa_handler = handle_signal;
    sa.sa_flags = 0;
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);

    pthread_t logs_tid;
    pthread_t metrics_tid;
    MetricsArgs metrics_args = {argc, argv, 0};

    if (pthread_create(&logs_tid, NULL, logs_thread, NULL) != 0)
    {
        perror("pthread_create logs");
        return 1;
    }

    if (pthread_create(&metrics_tid, NULL, metrics_thread, &metrics_args) != 0)
    {
        perror("pthread_create metrics");
        request_logs_stop();
        pthread_join(logs_tid, NULL);
        return 1;
    }

    pthread_join(metrics_tid, NULL);
    pthread_join(logs_tid, NULL);

    return metrics_args.result;
}
