import { ArrowUp, Zap, Clock, Server } from "lucide-react";

const stats = [
  { label: "Uptime", value: "99.97%", icon: ArrowUp, trend: "+0.02%" },
  { label: "Avg Latency", value: "42ms", icon: Clock, trend: "-3ms" },
  { label: "Active Nodes", value: "12", icon: Server, trend: "+1" },
  { label: "Events/s", value: "2.4k", icon: Zap, trend: "+180" },
];

export function InfoPanel() {
  return (
    <div className="panel-gradient rounded-lg border border-border p-4 h-full flex flex-col glow-border">
      <h3 className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-4">
        System Overview
      </h3>
      <div className="flex-1 flex flex-col gap-3">
        {stats.map((s) => (
          <div
            key={s.label}
            className="flex items-center gap-3 rounded-md bg-secondary/50 px-3 py-2.5"
          >
            <div className="flex items-center justify-center h-8 w-8 rounded bg-primary/10">
              <s.icon className="h-4 w-4 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[10px] font-mono text-muted-foreground uppercase">
                {s.label}
              </p>
              <p className="text-lg font-semibold font-mono text-foreground leading-tight">
                {s.value}
              </p>
            </div>
            <span className="text-[10px] font-mono text-chart-green">
              {s.trend}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function FixPlan() {
  return (
    <div className="panel-gradient rounded-lg border border-border p-4 h-full flex flex-col glow-border">
      <h3 className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-4">
        Healing agent window
      </h3>
      <div
        className="flex-1 flex flex-col 
      items-center justify-center gap-3"
      >
        <p className="text-sm font-mono text-center text-muted-foreground uppercase">
          System fixing plans will turn up here when anomalies are detected.
        </p>
      </div>
    </div>
  );
}
