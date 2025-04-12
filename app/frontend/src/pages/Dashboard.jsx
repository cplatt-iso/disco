// app/frontend/src/pages/Dashboard.jsx
import { useState, useMemo, Suspense, lazy } from "react";
// --- Import Loader2 ---
import { Loader2 } from "lucide-react";
// --- End Import ---
import SidebarTabButton from "../components/SidebarTabButton";
import Settings from "./Settings";

// Lazily load RulesEditor for potentially better initial load
const RulesEditor = lazy(() => import("./RulesEditor"));

const tabs = ["Health", "Rules Editor", "Settings"];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("Health");

  const widgets = useMemo(() => {
    const modules = import.meta.glob("../widgets/*.jsx", { eager: true });
    return Object.entries(modules).map(([path, mod], i) => {
      const Widget = mod.default;
      const widgetProps = mod.widgetProps || {}; // optional export for props
      return (
        <div key={i} className="max-w-4xl w-full">
          <Widget {...widgetProps} />
        </div>
      );
    });
  }, []);


  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-64 bg-gray-900 text-white p-4 space-y-2">
        <h2 className="text-2xl font-bold mb-6">DISCO</h2>
        {tabs.map((tab) => (
          <SidebarTabButton
            key={tab}
            isActive={activeTab === tab}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </SidebarTabButton>
        ))}
      </div>

      {/* Content Area */}
      <div className="flex-1 p-6 overflow-auto bg-background text-foreground">
        {/* Wrap content in Suspense for lazy loading */}
        {/* Use the imported Loader2 in the fallback */}
        <Suspense fallback={<div className="flex justify-center items-center h-full"><Loader2 className="h-16 w-16 animate-spin text-primary" /></div>}>
          {activeTab === "Health" && (
            <div>
              <h1 className="text-2xl font-semibold mb-4">Health Dashboard</h1>
              {widgets}
            </div>
          )}

          {activeTab === "Rules Editor" && (
            <RulesEditor />
          )}

          {activeTab === "Settings" && (
            <div>
              <h1 className="text-2xl font-semibold mb-4">Settings</h1>
              <Settings />
            </div>
          )}
        </Suspense>
      </div>
    </div>
  );
}
