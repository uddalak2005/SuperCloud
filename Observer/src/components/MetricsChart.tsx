import { useEffect, useState, useCallback } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";

function generatePoint(i: number) {
  return {
    time: new Date(Date.now() - (59 - i) * 2000).toLocaleTimeString([], {
      minute: "2-digit",
      second: "2-digit",
    }),
    latency: Math.floor(40 + Math.random() * 60 + Math.sin(i * 0.3) * 20),
    throughput: Math.floor(200 + Math.random() * 150 + Math.cos(i * 0.2) * 50),
  };
}

export function MetricsChart() {
  const [data, setData] = useState(() =>
    Array.from({ length: 60 }, (_, i) => generatePoint(i))
  );

  useEffect(() => {
    const interval = setInterval(() => {
      setData((prev) => {
        const next = [...prev.slice(1), generatePoint(60)];
        return next;
      });
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="panel-gradient rounded-lg border border-border p-4 h-full flex flex-col glow-border">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
          Request Latency & Throughput
        </h3>
        <span className="text-[10px] font-mono text-primary animate-pulse-glow">● LIVE</span>
      </div>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 5, bottom: 0, left: -20 }}>
            <defs>
              <linearGradient id="latencyGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(175, 80%, 50%)" stopOpacity={0.3} />
                <stop offset="100%" stopColor="hsl(175, 80%, 50%)" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="throughputGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(38, 90%, 55%)" stopOpacity={0.2} />
                <stop offset="100%" stopColor="hsl(38, 90%, 55%)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 14%)" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 10, fill: "hsl(215, 12%, 50%)", fontFamily: "JetBrains Mono" }}
              axisLine={{ stroke: "hsl(220, 14%, 18%)" }}
              tickLine={false}
              interval={14}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "hsl(215, 12%, 50%)", fontFamily: "JetBrains Mono" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(220, 18%, 10%)",
                border: "1px solid hsl(220, 14%, 18%)",
                borderRadius: "6px",
                fontFamily: "JetBrains Mono",
                fontSize: 11,
                color: "hsl(210, 20%, 90%)",
              }}
            />
            <Area
              type="monotone"
              dataKey="latency"
              stroke="hsl(175, 80%, 50%)"
              strokeWidth={2}
              fill="url(#latencyGrad)"
              dot={false}
              name="Latency (ms)"
            />
            <Area
              type="monotone"
              dataKey="throughput"
              stroke="hsl(38, 90%, 55%)"
              strokeWidth={1.5}
              fill="url(#throughputGrad)"
              dot={false}
              name="Throughput (rps)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
