import React, { useState, useEffect, useCallback } from 'react';
import { Button } from "@/components/ui/button"; // Assuming shadcn/ui setup
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label"; // Import Label if using

function CStoreSCPSettingsTab() { // Or CStoreSCPWidget
  // State for existing and new fields
  const [aeTitle, setAeTitle] = useState('');
  const [port, setPort] = useState('');
  const [bindAddress, setBindAddress] = useState(''); // <-- NEW STATE
  const [maxPduSize, setMaxPduSize] = useState('');   // <-- NEW STATE
  const [storageDirectory, setStorageDirectory] = useState(''); // <-- NEW STATE

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');

  // Fetch current config on component mount
  const fetchConfig = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/cstore/config'); // Adjust API endpoint if needed
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const config = await response.json();
      setAeTitle(config.ae_title || '');
      setPort(config.port || '');
      setBindAddress(config.bind_address || '0.0.0.0'); // Set default if not present
      setMaxPduSize(config.max_pdu_size || '116794'); // Set default
      setStorageDirectory(config.storage_dir || '/data/dicom_storage'); // Set default
    } catch (e) {
      console.error("Failed to fetch C-STORE config:", e);
      setError(`Failed to load configuration: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  }, []); // Empty dependency array means run once on mount

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]); // Include fetchConfig in dependency array

  // Handle saving the updated config
  const handleSave = async () => {
    setError(null);
    setSuccessMessage('');
    // Basic validation
    const portNum = parseInt(port, 10);
    const pduSizeNum = parseInt(maxPduSize, 10);
    if (isNaN(portNum) || portNum <= 0 || portNum > 65535) {
        setError("Port must be a number between 1 and 65535.");
        return;
    }
     if (isNaN(pduSizeNum) || pduSizeNum <= 0) {
        setError("Max PDU Size must be a positive number.");
        return;
    }
     if (!storageDirectory.trim()) {
         setError("Storage Directory cannot be empty.");
         return;
     }
     if (!bindAddress.trim()) { // Basic check, IP validation could be added
         setError("Bind Address cannot be empty.");
         return;
     }

    const configData = {
      ae_title: aeTitle,
      port: portNum,
      bind_address: bindAddress,       // <-- ADDED
      max_pdu_size: pduSizeNum,        // <-- ADDED
      storage_dir: storageDirectory // <-- ADDED
    };

    try {
      const response = await fetch('/api/cstore/config', { // Adjust API endpoint
        method: 'PUT', // Or POST
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(configData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setSuccessMessage(result.message || "Configuration saved successfully!");
      // Optionally re-fetch config to confirm changes, though not strictly needed
      // fetchConfig();
    } catch (e) {
      console.error("Failed to save C-STORE config:", e);
      setError(`Failed to save configuration: ${e.message}`);
    }
  };

  if (isLoading) return <div>Loading configuration...</div>;
  // Note: No separate error display here, but setError is called.
  // You might want a dedicated error display area.

  return (
    <Card>
      <CardHeader>
        <CardTitle>C-STORE SCP Settings</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
         {error && <p className="text-red-500">{error}</p>}
         {successMessage && <p className="text-green-500">{successMessage}</p>}

        {/* AE Title */}
        <div className="space-y-1">
          <Label htmlFor="aeTitle">AE Title</Label>
          <Input id="aeTitle" value={aeTitle} onChange={(e) => setAeTitle(e.target.value)} />
        </div>

        {/* Port */}
        <div className="space-y-1">
          <Label htmlFor="port">Port</Label>
          <Input id="port" type="number" value={port} onChange={(e) => setPort(e.target.value)} />
        </div>

        {/* Bind Address - NEW FIELD */}
        <div className="space-y-1">
          <Label htmlFor="bindAddress">Bind Address</Label>
          <Input id="bindAddress" value={bindAddress} onChange={(e) => setBindAddress(e.target.value)} placeholder="e.g., 0.0.0.0 or 192.168.1.100" />
          <p className="text-sm text-muted-foreground">
            IP address to listen on. Use '0.0.0.0' to listen on all interfaces.
          </p>
        </div>

        {/* Max PDU Size - NEW FIELD */}
        <div className="space-y-1">
          <Label htmlFor="maxPduSize">Max PDU Size (bytes)</Label>
          <Input id="maxPduSize" type="number" value={maxPduSize} onChange={(e) => setMaxPduSize(e.target.value)} />
           <p className="text-sm text-muted-foreground">
            Maximum data unit size for DICOM communication.
          </p>
        </div>

         {/* Storage Directory - NEW FIELD */}
        <div className="space-y-1">
          <Label htmlFor="storageDirectory">Storage Directory</Label>
          <Input id="storageDirectory" value={storageDirectory} onChange={(e) => setStorageDirectory(e.target.value)} placeholder="/path/on/server/to/save/files" />
           <p className="text-sm text-muted-foreground">
            Server path where received DICOM files will be stored. Ensure this path exists and is writable by the service.
          </p>
        </div>

      </CardContent>
      <CardFooter>
        <Button onClick={handleSave}>Save Configuration</Button>
      </CardFooter>
    </Card>
  );
}

export default CStoreSCPSettingsTab; // Or CStoreSCPWidget
