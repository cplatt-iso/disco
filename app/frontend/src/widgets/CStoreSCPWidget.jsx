// app/frontend/src/widgets/CStoreSCPWidget.jsx
import { useState, useEffect } from "react";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";

export default function CStoreSCPWidget() {
  const [listenerStatus, setListenerStatus] = useState({
    running: false,
    port: null,
    aeTitle: null,
  });

  const fetchStatus = () => {
    fetch("/api/cstore/status")
      .then((res) => res.json())
      .then((data) => setListenerStatus(data))
      .catch(() => setListenerStatus({ running: false, port: null, aeTitle: null }));
  };

  const handleToggleListener = () => {
    const endpoint = listenerStatus.running ? "/api/cstore/stop" : "/api/cstore/start";
    fetch(endpoint, { method: "POST" })
      .then((res) => res.json())
      .then(() => fetchStatus());
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <Card className="w-full max-w-4xl mb-6">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-2">
          <div>
            <p className="text-sm text-muted-foreground">C-STORE SCP</p>
            <p className="text-lg font-medium">
              {listenerStatus.running ? (
                <span className="text-green-600">Running</span>
              ) : (
                <span className="text-red-600">Stopped</span>
              )}
            </p>
            {listenerStatus.port && (
              <p className="text-sm text-muted-foreground">Port: {listenerStatus.port}</p>
            )}
            {listenerStatus.aeTitle && (
              <p className="text-sm text-muted-foreground">AE Title: {listenerStatus.aeTitle}</p>
            )}
          </div>
          <Button onClick={handleToggleListener}>
            {listenerStatus.running ? "Stop" : "Start"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

