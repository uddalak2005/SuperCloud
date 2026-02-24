import { AlertTriangle, CheckCircle, XCircle, Info } from "lucide-react";

const alerts = [
  {
    icon: XCircle,
    level: "error" as const,
    title: "Pod CrashLoopBackOff",
    detail: "data-pipeline-worker-3 restarted 5 times",
    time: "2m ago",
  },
  {
    icon: AlertTriangle,
    level: "warn" as const,
    title: "Disk Usage Warning",
    detail: "Node us-east-1b at 87% capacity",
    time: "8m ago",
  },
  {
    icon: CheckCircle,
    level: "ok" as const,
    title: "Deployment Complete",
    detail: "auth-svc v2.14.0 rolled out successfully",
    time: "15m ago",
  },
  {
    icon: Info,
    level: "info" as const,
    title: "Scaling Event",
    detail: "Auto-scaled api-gateway to 6 replicas",
    time: "22m ago",
  },
];

const levelStyles = {
  error: "text-chart-red bg-chart-red/10",
  warn: "text-chart-amber bg-chart-amber/10",
  ok: "text-chart-green bg-chart-green/10",
  info: "text-primary bg-primary/10",
};

export function AlertsPanel() {
  return (
    <div className="panel-gradient rounded-lg border border-border p-4 h-full flex flex-col glow-border">
      <h3 className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-3">
        Recent Alerts
      </h3>
      <div className="flex-1 flex flex-col gap-2 overflow-y-auto min-h-0">
        {alerts.map((a, i) => (
          <div
            key={i}
            className="flex items-start gap-3 rounded-md bg-secondary/40 px-3 py-2.5"
          >
            <div className={`flex items-center justify-center h-7 w-7 rounded shrink-0 ${levelStyles[a.level]}`}>
              <a.icon className="h-3.5 w-3.5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-display font-medium text-foreground">{a.title}</p>
              <p className="text-[10px] font-mono text-muted-foreground truncate">{a.detail}</p>
            </div>
            <span className="text-[10px] font-mono text-muted-foreground shrink-0">{a.time}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
