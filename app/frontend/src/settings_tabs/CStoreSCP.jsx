// src/settings_tabs/CStoreSCP.jsx
import { useEffect, useState } from "react";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";

export const tabName = "C-STORE SCP";

export default function CStoreSCP() {
  const [config, setConfig] = useState({ ae_title: "", port: 11112 });
  const [status, setStatus] = useState("idle");

  useEffect(() => {
    fetch("/api/cstore/config")
      .then((res) => res.json())
      .then(setConfig)
      .catch(() => setStatus("error"));
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setConfig((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = () => {
    setStatus("saving");
    fetch("/api/cstore/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    })
      .then((res) => res.ok ? setStatus("saved") : setStatus("error"))
      .catch(() => setStatus("error"));
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">C-STORE SCP Configuration</h2>

      <div className="space-y-4 max-w-md">
        <label className="block">
          <span className="text-sm font-medium">AE Title</span>
          <Input
            type="text"
            name="ae_title"
            value={config.ae_title}
            onChange={handleChange}
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium">Port</span>
          <Input
            type="number"
            name="port"
            value={config.port}
            onChange={handleChange}
          />
        </label>

        <Button onClick={handleSave} disabled={status === "saving"}>
          {status === "saving" ? "Saving..." : "Save Settings"}
        </Button>
        {status === "saved" && <p className="text-green-600">Saved!</p>}
        {status === "error" && <p className="text-red-600">Error saving config</p>}
      </div>
    </div>
  );
}

