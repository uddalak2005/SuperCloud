import { useState } from "react";
import {
  LayoutDashboard,
  Settings,
  ChevronLeft,
  ChevronRight,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", active: true },
  { icon: Settings, label: "Settings", active: false },
];

export function DashboardSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [approved, setApproved] = useState(false);

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-border bg-sidebar transition-all duration-300",
        collapsed ? "w-16" : "w-56",
      )}
    >
      <div className="flex-1 pt-4">
        {navItems.map((item) => (
          <button
            key={item.label}
            className={cn(
              "flex w-full items-center gap-3 px-4 py-3 text-sm transition-colors",
              item.active
                ? "text-primary bg-sidebar-accent border-r-2 border-primary"
                : "text-sidebar-foreground hover:text-sidebar-accent-foreground hover:bg-sidebar-accent",
            )}
          >
            <item.icon className="h-5 w-5 shrink-0" />
            {!collapsed && <span className="font-display">{item.label}</span>}
          </button>
        ))}
      </div>

      {!approved && (
        <div className="flex flex-col w-full p-4 border-t border-border">
          <h3
            className="text-xs font-mono uppercase 
        tracking-wider text-red-500 mb-4"
          >
            Kernel access user discretion
          </h3>
          <p className="text-xs font-mono text-muted-foreground mb-4">
            This is for you to approve this tool to access kernel level
            resources for anomaly detection and fixing. The system is completely
            secure and is protected by advanced encryption and access controls.
          </p>
          <div className="w-full flex gap-2 items-start justify-start">
            <button
              className="flex-1 btn btn-primary p-2 
          bg-red-500 text-white font-mono rounded-md"
              onClick={() => setApproved(true)}
            >
              Approve
            </button>
            <button
              className="flex-1 btn btn-primary p-2 
          bg-gray-400 text-white font-mono rounded-md"
              onClick={() => setApproved(false)}
            >
              Deny
            </button>
          </div>
        </div>
      )}

      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center border-t border-border p-3 text-muted-foreground hover:text-foreground transition-colors"
      >
        {collapsed ? (
          <ChevronRight className="h-4 w-4" />
        ) : (
          <ChevronLeft className="h-4 w-4" />
        )}
      </button>
    </aside>
  );
}
