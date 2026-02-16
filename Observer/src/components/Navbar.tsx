import { Activity, User } from "lucide-react";

export function Navbar() {
  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-6">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center h-8 w-8 rounded-md bg-primary/10 glow-border">
          <Activity className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="text-sm font-semibold font-display text-foreground tracking-wide">
            Supercloud
          </h1>
          <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">
            Observability Dashboard
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-md border border-border bg-secondary px-3 py-1.5">
          <div className="h-2 w-2 rounded-full bg-chart-green animate-pulse-glow" />
          <span className="text-xs font-mono text-secondary-foreground">All Systems OK</span>
        </div>
        <button className="flex items-center gap-2 rounded-md border border-border bg-secondary px-3 py-1.5 hover:bg-muted transition-colors">
          <User className="h-4 w-4 text-muted-foreground" />
          <span className="text-xs font-display text-secondary-foreground">Admin</span>
        </button>
      </div>
    </header>
  );
}
