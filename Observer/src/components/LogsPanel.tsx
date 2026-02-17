import { useEffect, useState, useRef } from "react";
import { cn } from "@/lib/utils";

type LogLevel = "INFO" | "WARN" | "ERROR" | "DEBUG";

interface LogEntry {
  id: number;
  timestamp: string;
  level: LogLevel;
  service: string;
  message: string;
}

const services = [
  "api-gateway",
  "auth-svc",
  "data-pipeline",
  "scheduler",
  "cdn-edge",
];
const messages: Record<LogLevel, string[]> = {
  INFO: [
    "Request processed successfully",
    "Health check passed",
    "Cache refreshed",
    "Connection pool stable",
    "Metrics flushed to store",
  ],
  WARN: [
    "High memory usage detected (82%)",
    "Slow query detected (>200ms)",
    "Rate limit approaching threshold",
    "Certificate renewal in 7 days",
  ],
  ERROR: [
    "Connection timeout after 30s",
    "Failed to parse response body",
    "Upstream service unavailable",
  ],
  DEBUG: [
    "Resolving DNS for endpoint",
    "TLS handshake completed",
    "Worker thread spawned",
  ],
};

const levelColors: Record<LogLevel, string> = {
  INFO: "text-chart-cyan",
  WARN: "text-chart-amber",
  ERROR: "text-chart-red",
  DEBUG: "text-muted-foreground",
};

let logId = 0;

function randomLog(): LogEntry {
  const levels: LogLevel[] = [
    "INFO",
    "INFO",
    "INFO",
    "INFO",
    "WARN",
    "DEBUG",
    "DEBUG",
    "ERROR",
  ];
  const level = levels[Math.floor(Math.random() * levels.length)];
  const msgs = messages[level];
  return {
    id: logId++,
    timestamp: new Date().toISOString().slice(11, 23),
    level,
    service: services[Math.floor(Math.random() * services.length)],
    message: msgs[Math.floor(Math.random() * msgs.length)],
  };
}

export function LogsPanel() {
  const [logs, setLogs] = useState<LogEntry[]>(() =>
    Array.from({ length: 12 }, () => randomLog()),
  );
  const scrollRef = useRef<HTMLDivElement>(null);

  // Random logs
  useEffect(() => {
    const interval = setInterval(() => {
      setLogs((prev) => [...prev.slice(-30), randomLog()]);
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  // WebSocket - Actual logs
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      ws = new WebSocket("ws://localhost:8000/ws");

      ws.onopen = () => {
        console.log("[WS] Connected");
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);

          if (msg.type === "log") {
            setLogs((prev) => [...prev.slice(-29), msg.data]);
          }
        } catch (err) {
          console.error("[WS] Invalid message", err);
        }
      };

      ws.onclose = () => {
        console.warn("[WS] Disconnected, retrying...");
        reconnectTimeout = setTimeout(connect, 2000);
      };

      ws.onerror = (err) => {
        console.error("[WS] Error", err);
        ws?.close();
      };
    };

    connect();

    return () => {
      ws?.close();
      clearTimeout(reconnectTimeout);
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="panel-gradient rounded-lg border border-border p-4 h-full flex flex-col glow-border">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
          Live Logs
        </h3>
        <span className="text-[10px] font-mono text-primary animate-pulse-glow">
          ● STREAMING
        </span>
      </div>
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto min-h-0 space-y-0.5"
      >
        {logs.map((log) => (
          <div
            key={log.id}
            className="flex gap-2 text-[11px] font-mono py-0.5 animate-slide-in-log"
          >
            <span className="text-muted-foreground shrink-0">
              {log.timestamp}
            </span>
            <span
              className={cn(
                "w-12 shrink-0 font-semibold",
                levelColors[log.level],
              )}
            >
              {log.level}
            </span>
            <span className="text-primary/70 shrink-0 w-28 truncate">
              {log.service}
            </span>
            <span className="text-foreground/80 truncate">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
