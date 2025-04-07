import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { motion } from "framer-motion";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [listenerStatus, setListenerStatus] = useState({ running: false, port: 11112 });

  useEffect(() => {
    // Simulate polling the backend for listener status
    const fetchStatus = async () => {
      // Replace with real API call
      const status = await fakeStatusCheck();
      setListenerStatus(status);
    };
    fetchStatus();
  }, []);

  const toggleListener = async () => {
    // Replace with real API call
    const updatedStatus = await fakeToggleListener();
    setListenerStatus(updatedStatus);
  };

  return (
    <div className="flex h-screen">
      <Tabs orientation="vertical" value={activeTab} onValueChange={setActiveTab} className="w-1/5 p-4 border-r">
        <TabsList className="flex flex-col space-y-2">
          <TabsTrigger value="dashboard">Health Dashboard</TabsTrigger>
          <TabsTrigger value="rules">Rules Editor</TabsTrigger>
        </TabsList>
      </Tabs>

      <div className="flex-1 p-6">
        {activeTab === "dashboard" && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <h2 className="text-2xl font-bold mb-4">Health Dashboard</h2>
            <Card className="mb-4">
              <CardContent className="p-4">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-xl font-semibold">DICOM Listener</h3>
                    <p className="text-sm text-gray-500">
                      Status: <span className={listenerStatus.running ? "text-green-600" : "text-red-600"}>{listenerStatus.running ? "Running" : "Stopped"}</span>
                    </p>
                    <p className="text-sm text-gray-500">Port: {listenerStatus.port}</p>
                  </div>
                  <Button onClick={toggleListener} variant="outline">
                    {listenerStatus.running ? "Stop Listener" : "Start Listener"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {activeTab === "rules" && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <h2 className="text-2xl font-bold">Rules Editor</h2>
            <p className="text-gray-600">Coming soon...</p>
          </motion.div>
        )}
      </div>
    </div>
  );
}

// Mocked API
async function fakeStatusCheck() {
  return new Promise((resolve) => {
    setTimeout(() => resolve({ running: true, port: 11112 }), 300);
  });
}

async function fakeToggleListener() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve((prev => ({ running: !prev.running, port: 11112 }))({ running: true }));
    }, 300);
  });
}

