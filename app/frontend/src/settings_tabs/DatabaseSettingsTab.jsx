// app/frontend/src/settings_tabs/DatabaseSettingsTab.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"; // For messages
import { Loader2 } from "lucide-react"; // Loading spinner


function DatabaseSettingsTab() {
    const [dbType, setDbType] = useState('sqlite');
    const [dbPath, setDbPath] = useState('');
    const [dbHost, setDbHost] = useState('');
    const [dbPort, setDbPort] = useState('');
    const [dbName, setDbName] = useState('');
    const [dbUser, setDbUser] = useState('');
    const [dbPassword, setDbPassword] = useState(''); // ** See Password Note Below **

    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [isInitializing, setIsInitializing] = useState(false);

    const [saveError, setSaveError] = useState(null);
    const [saveSuccess, setSaveSuccess] = useState(null);
    const [initError, setInitError] = useState(null);
    const [initSuccess, setInitSuccess] = useState(null);

    // --- Password Note ---
    // Displaying/saving passwords this way is insecure.
    // In production, prefer environment variables. You might:
    // 1. Show "****" and require re-entry to change (don't fetch the actual password).
    // 2. Have a note saying "Managed via DATABASE_PASSWORD environment variable".
    // 3. Use a dedicated secrets management system.
    // This example fetches/saves for simplicity, but DO NOT use in production as-is.

    const fetchConfig = useCallback(async () => {
        setIsLoading(true);
        setSaveError(null); setSaveSuccess(null); setInitError(null); setInitSuccess(null);
        try {
            const response = await fetch('/api/database/config');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const config = await response.json();
            setDbType(config.db_type || 'sqlite');
            setDbPath(config.db_path || '');
            setDbHost(config.db_host || '');
            setDbPort(config.db_port || '');
            setDbName(config.db_name || '');
            setDbUser(config.db_user || '');
            setDbPassword(config.db_password || ''); // Fetching password - insecure!
        } catch (e) {
            console.error("Failed to fetch DB config:", e);
            setSaveError(`Failed to load configuration: ${e.message}`); // Use saveError for load errors too
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchConfig();
    }, [fetchConfig]);

    const handleSave = async () => {
        setIsSaving(true);
        setSaveError(null); setSaveSuccess(null); setInitError(null); setInitSuccess(null);

        let configData = { db_type: dbType };

        // Collect data based on type
        if (dbType === 'sqlite') {
            if (!dbPath) { setSaveError("Database File Path is required for SQLite."); setIsSaving(false); return; }
            configData = { ...configData, db_path: dbPath };
        } else { // postgresql or mysql
             const portNum = dbPort ? parseInt(dbPort, 10) : null;
             if (dbPort && (isNaN(portNum) || portNum <= 0 || portNum > 65535)) {
                 setSaveError("Port must be a valid number (1-65535)."); setIsSaving(false); return;
             }
             if (!dbHost) { setSaveError("Hostname is required."); setIsSaving(false); return; }
             // Add checks for dbName, dbUser if they are strictly required

            configData = {
                ...configData,
                db_host: dbHost,
                db_port: portNum,
                db_name: dbName,
                db_user: dbUser,
                db_password: dbPassword // Saving password - insecure!
            };
        }

        try {
            const response = await fetch('/api/database/config', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(configData),
            });
            const result = await response.json();
            if (!response.ok) {
                 throw new Error(result.detail || `HTTP error! status: ${response.status}`);
            }
            setSaveSuccess(result.message || "Configuration saved successfully. Restart required.");
             // Optionally re-fetch config after save?
             // fetchConfig();
        } catch (e) {
            console.error("Failed to save DB config:", e);
            setSaveError(`Failed to save configuration: ${e.message}`);
        } finally {
            setIsSaving(false);
        }
    };

    const handleInitialize = async () => {
        setIsInitializing(true);
        setInitError(null); setInitSuccess(null); setSaveError(null); setSaveSuccess(null);
         // Optional: Add a confirmation dialog here?
         // if (!confirm("This will attempt to connect and initialize the database schema using the *currently saved* settings. Continue?")) {
         //    setIsInitializing(false);
         //    return;
         // }

        try {
             const response = await fetch('/api/database/initialize', { method: 'POST' });
             const result = await response.json();
            if (!response.ok) {
                 throw new Error(result.detail || `HTTP error! status: ${response.status}`);
            }
             setInitSuccess(result.message || result.status || "Database initialized successfully.");
        } catch (e) {
            console.error("Failed to initialize DB:", e);
             setInitError(`Initialization failed: ${e.message}`);
        } finally {
            setIsInitializing(false);
        }
    };

    const renderCommonFields = () => (
        <>
            <div className="space-y-1">
                <Label htmlFor="dbHost">Hostname / Server</Label>
                <Input id="dbHost" value={dbHost} onChange={(e) => setDbHost(e.target.value)} placeholder="e.g., localhost or db.example.com" />
            </div>
            <div className="space-y-1">
                <Label htmlFor="dbPort">Port</Label>
                <Input id="dbPort" type="number" value={dbPort} onChange={(e) => setDbPort(e.target.value)} placeholder={dbType === 'postgresql' ? '5432' : '3306'} />
            </div>
            <div className="space-y-1">
                <Label htmlFor="dbName">Database Name</Label>
                <Input id="dbName" value={dbName} onChange={(e) => setDbName(e.target.value)} placeholder="e.g., disco_db" />
            </div>
            <div className="space-y-1">
                <Label htmlFor="dbUser">Username</Label>
                <Input id="dbUser" value={dbUser} onChange={(e) => setDbUser(e.target.value)} />
            </div>
            <div className="space-y-1">
                 <Label htmlFor="dbPassword">Password</Label>
                 <Input id="dbPassword" type="password" value={dbPassword} onChange={(e) => setDbPassword(e.target.value)} />
                 <p className="text-sm text-destructive">Warning: Storing passwords via UI is insecure. Use environment variables (DATABASE_PASSWORD) for production.</p>
            </div>
        </>
    );

    if (isLoading) return <div className="flex justify-center items-center p-10"><Loader2 className="h-8 w-8 animate-spin" /></div>;

    return (
        <Card>
            <CardHeader>
                <CardTitle>Database Configuration</CardTitle>
                <CardDescription>Configure the connection to the application database. Changes require an application restart.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                 {/* Global Messages */}
                 {saveSuccess && <Alert variant="success"><AlertTitle>Success</AlertTitle><AlertDescription>{saveSuccess}</AlertDescription></Alert>}
                 {saveError && <Alert variant="destructive"><AlertTitle>Save Error</AlertTitle><AlertDescription>{saveError}</AlertDescription></Alert>}
                 {initSuccess && <Alert variant="success"><AlertTitle>Initialization Success</AlertTitle><AlertDescription>{initSuccess}</AlertDescription></Alert>}
                 {initError && <Alert variant="destructive"><AlertTitle>Initialization Error</AlertTitle><AlertDescription>{initError}</AlertDescription></Alert>}


                {/* DB Type Selector */}
                <div className="space-y-1">
                    <Label htmlFor="dbType">Database Type</Label>
                    <Select value={dbType} onValueChange={(value) => setDbType(value)}>
                        <SelectTrigger id="dbType">
                            <SelectValue placeholder="Select database type" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="sqlite">SQLite</SelectItem>
                            <SelectItem value="postgresql">PostgreSQL</SelectItem>
                            <SelectItem value="mysql">MySQL</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                {/* Conditional Fields */}
                {dbType === 'sqlite' && (
                    <div className="space-y-1">
                        <Label htmlFor="dbPath">Database File Path</Label>
                        <Input id="dbPath" value={dbPath} onChange={(e) => setDbPath(e.target.value)} placeholder="e.g., disco.db or /data/disco.db" />
                         <p className="text-sm text-muted-foreground">
                           Path relative to the application's running directory or an absolute path.
                         </p>
                    </div>
                )}

                {dbType === 'postgresql' && renderCommonFields()}
                {dbType === 'mysql' && renderCommonFields()}

            </CardContent>
            <CardFooter className="flex justify-between">
                 <Button onClick={handleSave} disabled={isSaving || isInitializing}>
                     {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                     Save Configuration
                 </Button>
                 <Button variant="outline" onClick={handleInitialize} disabled={isSaving || isInitializing}>
                      {isInitializing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                      Test Connection & Initialize Schema
                 </Button>
            </CardFooter>
        </Card>
    );
}

export default DatabaseSettingsTab;
