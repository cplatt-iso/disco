// app/frontend/src/pages/Dashboard.jsx
import { useState, useMemo, Suspense } from "react";
import SidebarTabButton from "../components/SidebarTabButton";
import Settings from "./Settings";

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
      <div className="flex-1 p-6 overflow-auto">
        {activeTab === "Health" && (
          <div>
            <h1 className="text-2xl font-semibold mb-4">Health Dashboard</h1>
            <Suspense fallback={<div>Loading widgets...</div>}>{widgets}</Suspense>
          </div>
        )}

        {activeTab === "Rules Editor" && (
          <div>
            <h1 className="text-2xl font-semibold">Rules Editor</h1>
            <p className="text-muted-foreground mt-2">Coming soon...</p>
          </div>
        )}

        {activeTab === "Settings" && (
          <div>
            <h1 className="text-2xl font-semibold mb-4">Settings</h1>
            <Settings />
          </div>
        )}
      </div>
    </div>
  );
}

