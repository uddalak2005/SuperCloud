import { DashboardSidebar } from "@/components/DashboardSidebar";
import { Navbar } from "@/components/Navbar";
import { MetricsChart } from "@/components/MetricsChart";
import { InfoPanel } from "@/components/InfoPanel";
import { LogsPanel } from "@/components/LogsPanel";
import { AlertsPanel } from "@/components/AlertsPanel";
import { FixPlan } from "@/components/InfoPanel";

const Index = () => {
  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <DashboardSidebar />
      <div className="flex flex-1 flex-col min-w-0">
        <Navbar />
        <main className="flex-1 p-4 overflow-auto">
          <div className="grid grid-cols-3 grid-rows-2 gap-4 h-full min-h-[500px]">
            {/* Row 1, Col 1-2: Metrics Chart */}
            <div className="col-span-2">
              <MetricsChart />
            </div>
            {/* Row 1, Col 3: Info Panel */}
            <div className="col-span-1">
              <FixPlan />
            </div>
            {/* Row 2, Col 1-2: Logs */}
            <div className="col-span-2">
              <LogsPanel />
            </div>
            {/* Row 2, Col 3: Alerts */}
            <div className="col-span-1">
              <AlertsPanel />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Index;
