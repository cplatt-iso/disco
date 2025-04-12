// app/frontend/src/pages/RulesEditor.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, PlusCircle, Trash2 } from "lucide-react";
import { format } from 'date-fns'; // Import date-fns for formatting

// --- Reusable Form Components (can be moved to separate files later) ---

function RulesetForm({ open, onOpenChange, onSubmit, initialData = {}, isLoading }) {
    const [name, setName] = useState(initialData.name || '');
    const [description, setDescription] = useState(initialData.description || '');
    const [error, setError] = useState('');

    useEffect(() => {
        // Reset form when dialog opens/closes or initialData changes
        setName(initialData.name || '');
        setDescription(initialData.description || '');
        setError('');
    }, [open, initialData]);

    const handleSubmit = (e) => {
        e.preventDefault();
        setError('');
        if (!name.trim()) {
            setError("Ruleset name cannot be empty.");
            return;
        }
        onSubmit({ name, description });
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>{initialData.id ? 'Edit Ruleset' : 'Create New Ruleset'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 py-4">
                    {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
                    <div className="space-y-1">
                        <Label htmlFor="rulesetName">Name</Label>
                        <Input id="rulesetName" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g., Default Routing" />
                    </div>
                    <div className="space-y-1">
                        <Label htmlFor="rulesetDescription">Description (Optional)</Label>
                        <Input id="rulesetDescription" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Describe the purpose of this ruleset" />
                    </div>
                    <DialogFooter>
                        <DialogClose asChild>
                             <Button type="button" variant="outline">Cancel</Button>
                         </DialogClose>
                         <Button type="submit" disabled={isLoading}>
                              {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                              {initialData.id ? 'Save Changes' : 'Create Ruleset'}
                          </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

function RuleForm({ open, onOpenChange, onSubmit, rulesetId, isLoading }) {
    // Basic rule fields
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [logicOperator, setLogicOperator] = useState('ALL');
    const [priority, setPriority] = useState(0);
    // Conditions & Actions state
    const [conditions, setConditions] = useState([]);
    const [actions, setActions] = useState([]);
    const [error, setError] = useState('');

     // Reset form when dialog opens
     useEffect(() => {
        if (open) {
            setName('');
            setDescription('');
            setLogicOperator('ALL');
            setPriority(0);
            setConditions([]);
            setActions([]);
            setError('');
        }
    }, [open]);

    // --- Condition Management ---
    const addCondition = () => {
        setConditions([...conditions, { attribute: '', operator: 'equals', value: '' }]);
    };
    const updateCondition = (index, field, value) => {
        const newConditions = [...conditions];
        newConditions[index][field] = value;
        setConditions(newConditions);
    };
    const removeCondition = (index) => {
        setConditions(conditions.filter((_, i) => i !== index));
    };

    // --- Action Management ---
    const addAction = () => {
        setActions([...actions, { action_type: 'log', target: '', parameters: '' }]);
    };
    const updateAction = (index, field, value) => {
        const newActions = [...actions];
        newActions[index][field] = value;
        setActions(newActions);
    };
    const removeAction = (index) => {
        setActions(actions.filter((_, i) => i !== index));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        setError('');
        // Basic validation
        if (!name.trim()) { setError("Rule name is required."); return; }
        const priorityNum = parseInt(priority, 10);
        if (isNaN(priorityNum)) { setError("Priority must be a number."); return; }

        // Advanced validation
        for (const cond of conditions) {
            if (!cond.attribute || !cond.operator) { setError("All condition fields (Attribute, Operator, Value) are required."); return; }
        }
        for (const act of actions) {
             if (!act.action_type) { setError("Action Type is required for all actions."); return; }
             if (act.parameters) {
                 try {
                      if (act.parameters.trim()) { JSON.parse(act.parameters); }
                 } catch (jsonError) {
                      setError(`Invalid JSON in parameters for action type ${act.action_type}: ${jsonError.message}`);
                      return;
                 }
             }
        }

        onSubmit({
            name, description, logic_operator: logicOperator, priority: priorityNum,
            conditions: conditions.map(c => ({ attribute: c.attribute, operator: c.operator, value: c.value })),
            actions: actions.map(a => ({
                action_type: a.action_type,
                target: a.target || null,
                parameters: a.parameters.trim() ? a.parameters : null
            })),
        });
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
             <DialogContent className="max-w-3xl">
                <DialogHeader>
                    <DialogTitle>Create New Rule in Ruleset {rulesetId}</DialogTitle>
                </DialogHeader>
                <div className="max-h-[75vh] overflow-y-auto pr-6 pl-2 py-4">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}

                        {/* Basic Rule Details */}
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-lg">Rule Details</CardTitle>
                            </CardHeader>
                            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                                <div className="space-y-1">
                                    <Label htmlFor="ruleName">Rule Name</Label>
                                    <Input id="ruleName" value={name} onChange={e => setName(e.target.value)} placeholder="e.g., Route CT Studies" />
                                </div>
                                <div className="space-y-1">
                                    <Label htmlFor="ruleDescription">Description</Label>
                                    <Input id="ruleDescription" value={description} onChange={e => setDescription(e.target.value)} placeholder="Optional: Describe what this rule does" />
                                </div>
                                <div className="space-y-1">
                                    <Label htmlFor="logicOperator">Logic Operator (Conditions)</Label>
                                    <Select value={logicOperator} onValueChange={setLogicOperator}>
                                        <SelectTrigger id="logicOperator"> <SelectValue /> </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="ALL">ALL conditions must match</SelectItem>
                                            <SelectItem value="ANY">ANY condition can match</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-1">
                                    <Label htmlFor="priority">Priority</Label>
                                    <Input id="priority" type="number" value={priority} onChange={e => setPriority(e.target.value)} />
                                    <p className="text-sm text-muted-foreground">Lower numbers usually execute first.</p>
                                </div>
                            </CardContent>
                        </Card>


                         {/* Conditions Section */}
                         <Card>
                             <CardHeader>
                                 <CardTitle className="text-lg">Conditions</CardTitle>
                                 <CardDescription>Define criteria that must be met for this rule to apply.</CardDescription>
                             </CardHeader>
                             <CardContent className="space-y-4">
                                {conditions.map((cond, index) => (
                                    <div key={index} className="flex items-start gap-2 border p-3 rounded">
                                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 flex-1">
                                             <Input placeholder="Attribute (e.g., calling_ae_title)" value={cond.attribute} onChange={e => updateCondition(index, 'attribute', e.target.value)} />
                                             <Select value={cond.operator} onValueChange={val => updateCondition(index, 'operator', val)}>
                                                 <SelectTrigger><SelectValue placeholder="Operator" /></SelectTrigger>
                                                 <SelectContent>
                                                     <SelectItem value="equals">equals</SelectItem>
                                                     <SelectItem value="not_equals">not equals</SelectItem>
                                                     <SelectItem value="starts_with">starts with</SelectItem>
                                                     <SelectItem value="ends_with">ends with</SelectItem>
                                                     <SelectItem value="contains">contains</SelectItem>
                                                     <SelectItem value="regex">regex matches</SelectItem>
                                                     <SelectItem value="exists">exists</SelectItem>
                                                     <SelectItem value="in">in list (comma-sep)</SelectItem>
                                                     <SelectItem value="not_in">not in list (comma-sep)</SelectItem>
                                                 </SelectContent>
                                             </Select>
                                             <Input placeholder="Value" value={cond.value} onChange={e => updateCondition(index, 'value', e.target.value)} />
                                         </div>
                                         <Button type="button" variant="ghost" size="icon" className="flex-shrink-0" onClick={() => removeCondition(index)} aria-label="Remove condition">
                                             <Trash2 className="h-4 w-4 text-destructive" />
                                         </Button>
                                     </div>
                                 ))}
                                <Button type="button" variant="outline" size="sm" onClick={addCondition}>
                                    <PlusCircle className="mr-2 h-4 w-4" /> Add Condition
                                </Button>
                             </CardContent>
                         </Card>

                          {/* Actions Section */}
                         <Card>
                             <CardHeader>
                                 <CardTitle className="text-lg">Actions</CardTitle>
                                 <CardDescription>Define what happens when all conditions (based on Logic Operator) are met.</CardDescription>
                             </CardHeader>
                             <CardContent className="space-y-4">
                                 {actions.map((act, index) => (
                                    <div key={index} className="flex items-start gap-2 border p-3 rounded">
                                         <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 flex-1">
                                             <Select value={act.action_type} onValueChange={val => updateAction(index, 'action_type', val)}>
                                                  <SelectTrigger><SelectValue placeholder="Action Type" /></SelectTrigger>
                                                 <SelectContent>
                                                     <SelectItem value="log">Log Message</SelectItem>
                                                     <SelectItem value="modify">Modify DICOM Tag</SelectItem>
                                                     <SelectItem value="delete_tag">Delete DICOM Tag</SelectItem>
                                                     <SelectItem value="route_to_aet">Route to AE Title</SelectItem>
                                                     <SelectItem value="discard">Discard Data</SelectItem>
                                                     {/* Add more action types */}
                                                 </SelectContent>
                                             </Select>
                                              <Input placeholder="Target (Optional, depends on type)" value={act.target} onChange={e => updateAction(index, 'target', e.target.value)} />
                                              <Input placeholder="Parameters (Optional JSON String)" value={act.parameters} onChange={e => updateAction(index, 'parameters', e.target.value)} />
                                          </div>
                                         <Button type="button" variant="ghost" size="icon" className="flex-shrink-0" onClick={() => removeAction(index)} aria-label="Remove action">
                                             <Trash2 className="h-4 w-4 text-destructive" />
                                         </Button>
                                     </div>
                                 ))}
                                  <Button type="button" variant="outline" size="sm" onClick={addAction}>
                                     <PlusCircle className="mr-2 h-4 w-4" /> Add Action
                                 </Button>
                             </CardContent>
                         </Card>

                        <DialogFooter className="pt-4 sticky bottom-0 bg-background py-4 border-t -mx-2 px-6">
                             <DialogClose asChild>
                                 <Button type="button" variant="outline">Cancel</Button>
                             </DialogClose>
                             <Button type="submit" disabled={isLoading}>
                                  {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                  Create Rule
                              </Button>
                        </DialogFooter>
                    </form>
                </div>
            </DialogContent>
        </Dialog>
    );
}


// --- Main Rules Editor Component ---

export default function RulesEditor() {
    const [rulesets, setRulesets] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [generalMessage, setGeneralMessage] = useState('');

    const [isCreateRulesetOpen, setIsCreateRulesetOpen] = useState(false);
    const [isSavingRuleset, setIsSavingRuleset] = useState(false);
    const [isCreateRuleOpen, setIsCreateRuleOpen] = useState(false);
    const [selectedRulesetIdForRule, setSelectedRulesetIdForRule] = useState(null);
    const [isSavingRule, setIsSavingRule] = useState(false);

    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        try {
            return format(new Date(dateString), 'PPpp');
        } catch { return dateString; }
    };

    const fetchRulesets = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/rulesets');
            if (!response.ok) {
                let errMsg = `HTTP error ${response.status}`;
                try { const errData = await response.json(); errMsg = errData.detail || errMsg; } catch {}
                throw new Error(errMsg);
            }
            const data = await response.json();
            setRulesets(data);
        } catch (e) {
            console.error("Failed to fetch rulesets:", e);
            setError(`Failed to load rulesets: ${e.message}`);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchRulesets();
    }, [fetchRulesets]);

    const handleCreateRuleset = async (formData) => {
        setIsSavingRuleset(true);
        setError(null); setGeneralMessage('');
        try {
            const response = await fetch('/api/rulesets', {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData),
            });
            const result = await response.json();
             if (!response.ok) throw new Error(result.detail || `HTTP error ${response.status}`);
            setGeneralMessage(`Ruleset "${result.name}" created successfully!`);
            setIsCreateRulesetOpen(false); fetchRulesets();
        } catch (e) {
            console.error("Failed to create ruleset:", e); setError(`Failed to create ruleset: ${e.message}`);
        } finally { setIsSavingRuleset(false); }
    };

    const handleDeleteRuleset = async (rulesetId, rulesetName) => {
        if (!confirm(`Are you sure you want to delete the ruleset "${rulesetName}" and ALL its rules? This cannot be undone.`)) return;
        setError(null); setGeneralMessage('');
        try {
            const response = await fetch(`/api/rulesets/${rulesetId}`, { method: 'DELETE' });
            if (response.status === 204) {
                 setGeneralMessage(`Ruleset "${rulesetName}" deleted successfully.`); fetchRulesets();
            } else {
                let errMsg = `HTTP error ${response.status}`;
                try { const errData = await response.json(); errMsg = errData.detail || errMsg; } catch {}
                throw new Error(errMsg);
            }
        } catch (e) {
            console.error("Failed to delete ruleset:", e); setError(`Failed to delete ruleset: ${e.message}`);
        }
    };

     const handleOpenCreateRuleModal = (rulesetId) => {
         setSelectedRulesetIdForRule(rulesetId); setIsCreateRuleOpen(true);
     };

     const handleCreateRule = async (formData) => {
         setIsSavingRule(true); setError(null); setGeneralMessage('');
          if (!selectedRulesetIdForRule) {
             setError("Cannot create rule: No ruleset selected."); setIsSavingRule(false); return;
         }
         try {
            const response = await fetch(`/api/rulesets/${selectedRulesetIdForRule}/rules/`, {
                 method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData),
             });
             const result = await response.json();
             if (!response.ok) throw new Error(result.detail || `HTTP error ${response.status}`);
             setGeneralMessage(`Rule "${result.name}" added successfully to ruleset ${selectedRulesetIdForRule}.`);
             setIsCreateRuleOpen(false); fetchRulesets();
         } catch (e) {
             console.error("Failed to create rule:", e); alert(`Failed to create rule: ${e.message}`);
         } finally { setIsSavingRule(false); }
     };

     const handleDeleteRule = async (ruleId, ruleName, rulesetName) => {
         alert(`Delete functionality for rule "${ruleName}" (ID: ${ruleId}) in ruleset "${rulesetName}" is not implemented yet.`);
     };

    if (isLoading) {
        return <div className="flex justify-center items-center h-full"><Loader2 className="h-16 w-16 animate-spin" /></div>;
    }

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                 <h1 className="text-2xl font-semibold">Rules Editor</h1>
                 <Dialog open={isCreateRulesetOpen} onOpenChange={setIsCreateRulesetOpen}>
                    <DialogTrigger asChild>
                         <Button><PlusCircle className="mr-2 h-4 w-4" /> Add Ruleset</Button>
                     </DialogTrigger>
                     <RulesetForm
                         open={isCreateRulesetOpen}
                         onOpenChange={setIsCreateRulesetOpen}
                         onSubmit={handleCreateRuleset}
                         isLoading={isSavingRuleset}
                     />
                 </Dialog>
             </div>

             {error && <Alert variant="destructive" className="mb-4"><AlertTitle>Error</AlertTitle><AlertDescription>{error}</AlertDescription></Alert>}
             {generalMessage && <Alert variant="success" className="mb-4"><AlertTitle>Success</AlertTitle><AlertDescription>{generalMessage}</AlertDescription></Alert>}

             <Accordion type="single" collapsible className="w-full space-y-4">
                 {rulesets.length === 0 && !isLoading && <p className="text-center text-muted-foreground py-4">No rulesets found. Click 'Add Ruleset' to create one.</p>}
                 {rulesets.map((ruleset) => (
                     <AccordionItem value={`ruleset-${ruleset.id}`} key={ruleset.id} className="border rounded-md px-4 bg-card shadow-sm">
                         <AccordionTrigger className="hover:no-underline py-4 w-full">
                             <div className="flex justify-between items-center">
                                 <div className="text-left mr-4 overflow-hidden">
                                     <span className="font-medium text-lg truncate" title={ruleset.name}>{ruleset.name}</span>
                                     {ruleset.description && <p className="text-sm text-muted-foreground truncate" title={ruleset.description}>{ruleset.description}</p>}
                                     <p className="text-xs text-muted-foreground">
                                         ID: {ruleset.id} | Rules: {ruleset.rules?.length || 0} | Updated: {formatDate(ruleset.updated_at)}
                                     </p>
                                 </div>
                                 <div className="flex items-center gap-2 flex-shrink-0"> {/* This div needs closing */}
                                     {/* TODO: Add Edit Ruleset Button */}
                                     {/* <Button variant="ghost" size="sm" onClick={(e) => {e.stopPropagation(); handleEditRuleset(ruleset); }}>Edit</Button> */}
                                     <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive hover:bg-destructive/10" onClick={(e) => { e.stopPropagation(); handleDeleteRuleset(ruleset.id, ruleset.name); }} aria-label={`Delete ruleset ${ruleset.name}`}>
                                         <Trash2 className="h-4 w-4" />
                                     </Button>
                                 </div> {/* <<<--------- CORRECT CLOSING TAG HERE */}
                             </div>
                         </AccordionTrigger>
                         <AccordionContent className="pt-2 pb-4 space-y-3">
                             <Button variant="outline" size="sm" className="mb-2" onClick={() => handleOpenCreateRuleModal(ruleset.id)}>
                                 <PlusCircle className="mr-2 h-4 w-4" /> Add Rule to this Ruleset
                             </Button>
                             {ruleset.rules && ruleset.rules.length > 0 ? (
                                ruleset.rules.sort((a, b) => a.priority - b.priority).map((rule) => (
                                     <Card key={rule.id} className="bg-background/50 border">
                                         <CardHeader className="pb-2 pt-3 px-4">
                                             <div className="flex justify-between items-start">
                                                 <div>
                                                     <CardTitle className="text-base">{rule.name || `Rule ID: ${rule.id}`}</CardTitle>
                                                     <CardDescription className="text-xs">
                                                         Priority: {rule.priority} | Logic: {rule.logic_operator} | Conditions: {rule.conditions?.length || 0} | Actions: {rule.actions?.length || 0}
                                                     </CardDescription>
                                                     {rule.description && <p className="text-sm text-muted-foreground mt-1">{rule.description}</p>}
                                                 </div>
                                                 <div className="flex items-center gap-1">
                                                       <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10" onClick={(e) => { e.stopPropagation(); handleDeleteRule(rule.id, rule.name, ruleset.name); }} aria-label={`Delete rule ${rule.name}`}>
                                                         <Trash2 className="h-4 w-4" />
                                                     </Button>
                                                 </div>
                                             </div>
                                         </CardHeader>
                                         <CardContent className="px-4 pb-3 text-sm">
                                             {rule.conditions && rule.conditions.length > 0 && (
                                                 <div className="mt-2">
                                                      <strong className="text-xs uppercase text-muted-foreground">Conditions ({rule.logic_operator}):</strong>
                                                      <ul className="list-disc list-inside pl-2 mt-1 space-y-0.5">
                                                         {rule.conditions.map(cond => (
                                                             <li key={cond.id} className="text-xs">
                                                                <code className="bg-muted px-1 py-0.5 rounded">{cond.attribute}</code> {cond.operator} <code className="bg-muted px-1 py-0.5 rounded">{cond.value}</code>
                                                            </li>
                                                         ))}
                                                     </ul>
                                                 </div>
                                             )}
                                              {rule.actions && rule.actions.length > 0 && (
                                                 <div className="mt-2">
                                                     <strong className="text-xs uppercase text-muted-foreground">Actions:</strong>
                                                      <ul className="list-disc list-inside pl-2 mt-1 space-y-0.5">
                                                          {rule.actions.map(act => (
                                                             <li key={act.id} className="text-xs">
                                                                {act.action_type}
                                                                {act.target && <> Target: <code className="bg-muted px-1 py-0.5 rounded">{act.target}</code></>}
                                                                {act.parameters && <> Params: <code className="bg-muted px-1 py-0.5 rounded">{act.parameters}</code></>}
                                                             </li>
                                                         ))}
                                                      </ul>
                                                  </div>
                                             )}
                                             {(rule.conditions?.length === 0 && rule.actions?.length === 0) && <p className="text-xs text-muted-foreground mt-1">This rule has no conditions or actions defined.</p>}
                                         </CardContent>
                                     </Card>
                                 ))
                             ) : (
                                 <p className="text-sm text-muted-foreground pl-1">This ruleset has no rules defined.</p>
                             )}
                         </AccordionContent>
                     </AccordionItem>
                 ))}
             </Accordion>

             <RuleForm
                 open={isCreateRuleOpen}
                 onOpenChange={setIsCreateRuleOpen}
                 onSubmit={handleCreateRule}
                 rulesetId={selectedRulesetIdForRule}
                 isLoading={isSavingRule}
             />

        </div>
    );
}
