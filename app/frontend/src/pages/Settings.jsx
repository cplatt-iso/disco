// src/pages/Settings.jsx
import { useState, useMemo } from "react";
import SidebarTabButton from "../components/SidebarTabButton";

export default function Settings() {
  const [activeSettingTab, setActiveSettingTab] = useState(null);

  const tabs = useMemo(() => {
    const modules = import.meta.glob("../settings_tabs/*.jsx", { eager: true });
    return Object.entries(modules).map(([path, mod]) => ({
      name: mod.tabName || path.split("/").pop().replace(".jsx", ""),
      Component: mod.default,
    }));
  }, []);

  const ActiveComponent = tabs.find(t => t.name === activeSettingTab)?.Component || null;

  return (
    <div className="flex">
      {/* Settings sidebar */}
      <div className="w-48 bg-gray-100 dark:bg-gray-800 p-3 space-y-2 rounded-lg shadow-md">
        {tabs.map(({ name }) => (
          <SidebarTabButton
            key={name}
            isActive={activeSettingTab === name}
            onClick={() => setActiveSettingTab(name)}
          >
            {name}
          </SidebarTabButton>
        ))}
      </div>

      {/* Settings content */}
      <div className="ml-6 flex-1">
        {ActiveComponent ? (
          <ActiveComponent />
        ) : (
          <p className="text-muted-foreground">Select a settings tab...</p>
        )}
      </div>
    </div>
  );
}

