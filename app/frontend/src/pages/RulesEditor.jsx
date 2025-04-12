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
import { Loader2, PlusCircle, Trash2, Pencil } from "lucide-react"; // Added Pencil
import { format } from 'date-fns';

// --- Reusable Form Components ---

function RulesetForm({ open, onOpenChange, onSubmit, initialData = {}, isLoading }) {
    const [name, setName] = useState(initialData.name || '');
    const [description, setDescription] = useState(initialData.description || '');
    const [error, setError] = useState('');

    useEffect(() => {
        // Reset form based on initialData when dialog opens
        if (open) {
            setName(initialData?.name || '');
            setDescription(initialData?.description || '');
            setError('');
        }
    }, [open, initialData]);

    const handleSubmit = (e) => {
        e.preventDefault();
        setError('');
        if (!name.trim()) {
            setError("Ruleset name cannot be empty.");
            return;
        }
        // Pass description even if empty, backend handles nullability
        onSubmit({ name, description: description || null });
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>{initialData?.id ? 'Edit Ruleset' : 'Create New Ruleset'}</DialogTitle>
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
                              {initialData?.id ? 'Save Changes' : 'Create Ruleset'}
                          </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

// --- Updated RuleForm to handle initialData for editing ---
function RuleForm({ open, onOpenChange, onSubmit, rulesetId, initialData = null, isLoading }) {
    const isEditing = !!initialData?.id;

    // Basic rule fields state
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [logicOperator, setLogicOperator] = useState('ALL');
    const [priority, setPriority] = useState(0);
    // Conditions & Actions state
    const [conditions, setConditions] = useState([]);
    const [actions, setActions] = useState([]);
    const [error, setError] = useState('');

     // Effect to populate form when opening for edit, or reset for create/close
     useEffect(() => {
        if (open) {
            if (isEditing && initialData) {
                // Populate state from initialData for editing
                setName(initialData.name || '');
                setDescription(initialData.description || '');
                setLogicOperator(initialData.logic_operator || 'ALL');
                setPriority(initialData.priority || 0);
                // IMPORTANT: Ensure initialData.conditions/actions are arrays
                // Map to ensure we only take needed fields for state (optional but safer)
                setConditions(initialData.conditions?.map(c => ({ attribute: c.attribute, operator: c.operator, value: c.value })) || []);
                setActions(initialData.actions?.map(a => ({ action_type: a.action_type, target: a.target || '', parameters: a.parameters || '' })) || []);
                setError('');
            } else {
                // Reset state for creating a new rule
                setName('');
                setDescription('');
                setLogicOperator('ALL');
                setPriority(0);
                setConditions([]);
                setActions([]);
                setError('');
            }
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [open, initialData, isEditing]); // Depend on open and initialData


    // --- Condition Management --- (no changes needed here)
    const addCondition = () => setConditions([...conditions, { attribute: '', operator: 'equals', value: '' }]);
    const updateCondition = (index, field, value) => {
        const newConditions = [...conditions];
        newConditions[index][field] = value;
        setConditions(newConditions);
    };
    const removeCondition = (index) => setConditions(conditions.filter((_, i) => i !== index));

    // --- Action Management --- (no changes needed here)
    const addAction = () => setActions([...actions, { action_type: 'log', target: '', parameters: '' }]);
    const updateAction = (index, field, value) => {
        const newActions = [...actions];
        newActions[index][field] = value;
        setActions(newActions);
    };
    const removeAction = (index) => setActions(actions.filter((_, i) => i !== index));

    // --- Form Submission ---
    const handleSubmit = (e) => {
        e.preventDefault();
        setError('');
        // Validation
        if (!name.trim()) { setError("Rule name is required."); return; }
        const priorityNum = parseInt(priority, 10);
        if (isNaN(priorityNum)) { setError("Priority must be a number."); return; }
        for (const cond of conditions) { if (!cond.attribute || !cond.operator) { setError("Condition fields are required."); return; } }
        for (const act of actions) {
             if (!act.action_type) { setError("Action Type is required."); return; }
             if (act.parameters) { try { if (act.parameters.trim()) JSON.parse(act.parameters); } catch (err) { setError(`Invalid JSON in parameters: ${err.message}`); return; } }
        }

        // Submit data matching RuleCreate/RuleUpdate schema structure
        onSubmit({
            name, description: description || null, // Ensure null if empty
            logic_operator: logicOperator, priority: priorityNum,
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
                    {/* --- Conditional Title --- */}
                    <DialogTitle>{isEditing ? `Edit Rule (ID: ${initialData.id})` : `Create New Rule in Ruleset ${rulesetId}`}</DialogTitle>
                </DialogHeader>
                <div className="max-h-[75vh] overflow-y-auto pr-6 pl-2 py-4">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}

                        {/* Basic Rule Details */}
                        <Card>
                            <CardHeader className="pb-2"><CardTitle className="text-lg">Rule Details</CardTitle></CardHeader>
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
                                    <Label htmlFor="logicOperator">Logic Operator</Label>
                                    <Select value={logicOperator} onValueChange={setLogicOperator}>
                                        <SelectTrigger id="logicOperator"><SelectValue /></SelectTrigger>
                                        <SelectContent><SelectItem value="ALL">ALL conditions must match</SelectItem><SelectItem value="ANY">ANY condition can match</SelectItem></SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-1">
                                    <Label htmlFor="priority">Priority</Label>
                                    <Input id="priority" type="number" value={priority} onChange={e => setPriority(e.target.value)} />
                                    <p className="text-sm text-muted-foreground">Lower numbers execute first.</p>
                                </div>
                            </CardContent>
                        </Card>

                         {/* Conditions Section */}
                         <Card>
                             <CardHeader><CardTitle className="text-lg">Conditions</CardTitle><CardDescription>Criteria that must be met.</CardDescription></CardHeader>
                             <CardContent className="space-y-4">
                                {conditions.map((cond, index) => (
                                    <div key={`cond-${index}`} className="flex items-start gap-2 border p-3 rounded"> {/* Changed key for potential stability */}
                                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 flex-1">
                                             <Input placeholder="Attribute" value={cond.attribute} onChange={e => updateCondition(index, 'attribute', e.target.value)} />
                                             <Select value={cond.operator} onValueChange={val => updateCondition(index, 'operator', val)}>
                                                 <SelectTrigger><SelectValue placeholder="Operator" /></SelectTrigger>
                                                 <SelectContent> {/* Add more operators */}
                                                     <SelectItem value="equals">equals</SelectItem><SelectItem value="not_equals">not equals</SelectItem><SelectItem value="starts_with">starts with</SelectItem><SelectItem value="ends_with">ends with</SelectItem><SelectItem value="contains">contains</SelectItem><SelectItem value="regex">regex matches</SelectItem><SelectItem value="exists">exists</SelectItem><SelectItem value="in">in list</SelectItem><SelectItem value="not_in">not in list</SelectItem>
                                                 </SelectContent>
                                             </Select>
                                             <Input placeholder="Value" value={cond.value} onChange={e => updateCondition(index, 'value', e.target.value)} />
                                         </div>
                                         <Button type="button" variant="ghost" size="icon" className="flex-shrink-0" onClick={() => removeCondition(index)} aria-label="Remove condition"><Trash2 className="h-4 w-4 text-destructive" /></Button>
                                     </div>
                                 ))}
                                <Button type="button" variant="outline" size="sm" onClick={addCondition}><PlusCircle className="mr-2 h-4 w-4" /> Add Condition</Button>
                             </CardContent>
                         </Card>

                          {/* Actions Section */}
                         <Card>
                             <CardHeader><CardTitle className="text-lg">Actions</CardTitle><CardDescription>What happens if conditions match.</CardDescription></CardHeader>
                             <CardContent className="space-y-4">
                                 {actions.map((act, index) => (
                                    <div key={`act-${index}`} className="flex items-start gap-2 border p-3 rounded"> {/* Changed key */}
                                         <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 flex-1">
                                             <Select value={act.action_type} onValueChange={val => updateAction(index, 'action_type', val)}>
                                                  <SelectTrigger><SelectValue placeholder="Action Type" /></SelectTrigger>
                                                 <SelectContent> {/* Add more action types */}
                                                     <SelectItem value="log">Log Message</SelectItem><SelectItem value="modify">Modify Tag</SelectItem><SelectItem value="delete_tag">Delete Tag</SelectItem><SelectItem value="route_to_aet">Route to AE</SelectItem><SelectItem value="discard">Discard</SelectItem>
                                                 </SelectContent>
                                             </Select>
                                              <Input placeholder="Target (Optional)" value={act.target} onChange={e => updateAction(index, 'target', e.target.value)} />
                                              <Input placeholder="Parameters (Optional JSON)" value={act.parameters} onChange={e => updateAction(index, 'parameters', e.target.value)} />
                                          </div>
                                         <Button type="button" variant="ghost" size="icon" className="flex-shrink-0" onClick={() => removeAction(index)} aria-label="Remove action"><Trash2 className="h-4 w-4 text-destructive" /></Button>
                                     </div>
                                 ))}
                                  <Button type="button" variant="outline" size="sm" onClick={addAction}><PlusCircle className="mr-2 h-4 w-4" /> Add Action</Button>
                             </CardContent>
                         </Card>

                        <DialogFooter className="pt-4 sticky bottom-0 bg-background py-4 border-t -mx-2 px-6">
                             <DialogClose asChild><Button type="button" variant="outline">Cancel</Button></DialogClose>
                             {/* --- Conditional Button Text --- */}
                             <Button type="submit" disabled={isLoading}>
                                  {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                  {isEditing ? 'Update Rule' : 'Create Rule'}
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

    // State for Ruleset Form Modal (Unified Create/Edit)
    const [isRulesetFormOpen, setIsRulesetFormOpen] = useState(false);
    const [editingRuleset, setEditingRuleset] = useState(null); // Ruleset object or null
    const [isSavingRuleset, setIsSavingRuleset] = useState(false); // Single saving state for ruleset form

    // State for Rule Form Modal (Unified Create/Edit)
    const [isRuleFormOpen, setIsRuleFormOpen] = useState(false);
    const [editingRule, setEditingRule] = useState(null); // Rule object or null
    const [selectedRulesetIdForForm, setSelectedRulesetIdForForm] = useState(null); // Parent ID needed for create
    const [isSavingRule, setIsSavingRule] = useState(false); // Single saving state for rule form

    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        try { return format(new Date(dateString), 'PPpp'); } catch { return dateString; }
    };

    const fetchRulesets = useCallback(async () => {
        setIsLoading(true); setError(null);
        try {
            const response = await fetch('/api/rulesets');
            if (!response.ok) {
                let errMsg = `HTTP error ${response.status}`;
                try { const errData = await response.json(); errMsg = errData.detail || errMsg; } catch {}
                throw new Error(errMsg);
            }
            setRulesets(await response.json());
        } catch (e) {
            console.error("Failed to fetch rulesets:", e); setError(`Failed to load rulesets: ${e.message}`);
        } finally { setIsLoading(false); }
    }, []);

    useEffect(() => { fetchRulesets(); }, [fetchRulesets]);

    // --- Ruleset Modal Handlers ---
    const handleOpenCreateRulesetModal = () => { setEditingRuleset(null); setIsRulesetFormOpen(true); };
    const handleOpenEditRulesetModal = (ruleset) => { setEditingRuleset(ruleset); setIsRulesetFormOpen(true); };

    const handleCreateOrUpdateRuleset = async (formData) => {
        const isEditing = !!editingRuleset?.id;
        setIsSavingRuleset(true); setError(null); setGeneralMessage('');
        const url = isEditing ? `/api/rulesets/${editingRuleset.id}` : '/api/rulesets';
        const method = isEditing ? 'PUT' : 'POST';
        try {
            const response = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || `HTTP error ${response.status}`);
            setGeneralMessage(`Ruleset "${result.name}" ${isEditing ? 'updated' : 'created'} successfully!`);
            setIsRulesetFormOpen(false); setEditingRuleset(null); fetchRulesets();
        } catch (e) { console.error(`Failed to ${isEditing ? 'update' : 'create'} ruleset:`, e); alert(`Error: ${e.message}`);
        } finally { setIsSavingRuleset(false); }
    };

    const handleDeleteRuleset = async (rulesetId, rulesetName) => { /* ... same ... */ };

    // --- Rule Modal Handlers ---
     const handleOpenCreateRuleModal = (rulesetId) => {
         setEditingRule(null); setSelectedRulesetIdForForm(rulesetId); setIsRuleFormOpen(true);
     };
      const handleOpenEditRuleModal = (rule, rulesetId) => {
          // Fetch full rule details IF needed, or assume list view has enough?
          // If list view is sufficient (contains conditions/actions):
          setEditingRule(rule);
          setSelectedRulesetIdForForm(rulesetId); // Store parent ID maybe useful later
          setIsRuleFormOpen(true);
          // If full details needed:
          // Fetch /api/rulesets/rules/{rule.id} first, then setEditingRule and open modal
      };

     const handleCreateOrUpdateRule = async (formData) => {
        const isEditing = !!editingRule?.id;
        setIsSavingRule(true); setError(null); setGeneralMessage('');
        if (!selectedRulesetIdForForm && !isEditing) {
             alert("Error: Cannot determine target ruleset."); setIsSavingRule(false); return;
        }
        const url = isEditing ? `/api/rulesets/rules/${editingRule.id}` : `/api/rulesets/${selectedRulesetIdForForm}/rules/`;
        const method = isEditing ? 'PUT' : 'POST';
         try {
            const response = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || `HTTP error ${response.status}`);
            setGeneralMessage(`Rule "${result.name}" ${isEditing ? 'updated' : 'created'} successfully.`);
            setIsRuleFormOpen(false); setEditingRule(null); fetchRulesets();
         } catch (e) { console.error(`Failed to ${isEditing ? 'update' : 'create'} rule:`, e); alert(`Failed to ${isEditing ? 'update' : 'create'} rule: ${e.message}`);
         } finally { setIsSavingRule(false); }
     };

     const handleDeleteRule = async (ruleId, ruleName, rulesetName) => { /* ... same (using API endpoint now) ... */ };

    if (isLoading) { /* ... same ... */ }

    return (
        <div>
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                 <h1 className="text-2xl font-semibold">Rules Editor</h1>
                 <Button onClick={handleOpenCreateRulesetModal}><PlusCircle className="mr-2 h-4 w-4" /> Add Ruleset</Button>
             </div>

             {/* Alerts */}
             {error && <Alert variant="destructive" className="mb-4"><AlertTitle>Error</AlertTitle><AlertDescription>{error}</AlertDescription></Alert>}
             {generalMessage && <Alert variant="success" className="mb-4"><AlertTitle>Success</AlertTitle><AlertDescription>{generalMessage}</AlertDescription></Alert>}

             {/* Ruleset Form Dialog (unified) */}
             <RulesetForm
                key={editingRuleset ? `edit-rs-${editingRuleset.id}` : 'create-rs'}
                open={isRulesetFormOpen}
                onOpenChange={setIsRulesetFormOpen}
                onSubmit={handleCreateOrUpdateRuleset}
                initialData={editingRuleset || {}}
                isLoading={isSavingRuleset}
            />

             {/* Accordion */}
             <Accordion type="single" collapsible className="w-full space-y-4">
                 {rulesets.length === 0 && !isLoading && <p className="text-center text-muted-foreground py-4">No rulesets found.</p>}
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
                                 <div className="flex items-center gap-2 flex-shrink-0">
                                     {/* Edit Ruleset Button */}
                                     <Button variant="ghost" size="icon" className="h-7 w-7" onClick={(e) => {e.stopPropagation(); handleOpenEditRulesetModal(ruleset);}} aria-label={`Edit ruleset ${ruleset.name}`}>
                                         <Pencil className="h-4 w-4" />
                                     </Button>
                                     {/* Delete Ruleset Button */}
                                     <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10" onClick={(e) => { e.stopPropagation(); handleDeleteRuleset(ruleset.id, ruleset.name); }} aria-label={`Delete ruleset ${ruleset.name}`}>
                                         <Trash2 className="h-4 w-4" />
                                     </Button>
                                 </div>
                             </div>
                         </AccordionTrigger>
                         <AccordionContent className="pt-2 pb-4 space-y-3">
                             <Button variant="outline" size="sm" className="mb-2" onClick={() => handleOpenCreateRuleModal(ruleset.id)}>
                                 <PlusCircle className="mr-2 h-4 w-4" /> Add Rule to this Ruleset
                             </Button>
                             {/* Rule List */}
                             {ruleset.rules && ruleset.rules.length > 0 ? (
                                ruleset.rules.sort((a, b) => a.priority - b.priority).map((rule) => (
                                     <Card key={rule.id} className="bg-background/50 border">
                                         <CardHeader className="pb-2 pt-3 px-4">
                                             <div className="flex justify-between items-start">
                                                 <div>
                                                     <CardTitle className="text-base">{rule.name || `Rule ID: ${rule.id}`}</CardTitle>
                                                     <CardDescription className="text-xs"> Priority: {rule.priority} | Logic: {rule.logic_operator} | Conds: {rule.conditions?.length || 0} | Acts: {rule.actions?.length || 0} </CardDescription>
                                                     {rule.description && <p className="text-sm text-muted-foreground mt-1">{rule.description}</p>}
                                                 </div>
                                                 <div className="flex items-center gap-1">
                                                      {/* Edit Rule Button */}
                                                      <Button variant="ghost" size="icon" className="h-7 w-7" onClick={(e) => { e.stopPropagation(); handleOpenEditRuleModal(rule, ruleset.id); }}>
                                                          <Pencil className="h-4 w-4" />
                                                      </Button>
                                                      {/* Delete Rule Button */}
                                                      <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10" onClick={(e) => { e.stopPropagation(); handleDeleteRule(rule.id, rule.name, ruleset.name); }} aria-label={`Delete rule ${rule.name}`}>
                                                          <Trash2 className="h-4 w-4" />
                                                      </Button>
                                                 </div>
                                             </div>
                                         </CardHeader>
                                         <CardContent className="px-4 pb-3 text-sm">
                                             {/* Conditions Display */}
                                             {rule.conditions?.length > 0 && (<div className="mt-2"><strong className="text-xs uppercase text-muted-foreground">Conditions ({rule.logic_operator}):</strong><ul className="list-disc list-inside pl-2 mt-1 space-y-0.5">{rule.conditions.map(c => (<li key={c.id} className="text-xs"><code className="bg-muted px-1 py-0.5 rounded">{c.attribute}</code> {c.operator} <code className="bg-muted px-1 py-0.5 rounded">{c.value}</code></li>))}</ul></div>)}
                                             {/* Actions Display */}
                                             {rule.actions?.length > 0 && (<div className="mt-2"><strong className="text-xs uppercase text-muted-foreground">Actions:</strong><ul className="list-disc list-inside pl-2 mt-1 space-y-0.5">{rule.actions.map(a => (<li key={a.id} className="text-xs">{a.action_type}{a.target && <> Target: <code className="bg-muted px-1 py-0.5 rounded">{a.target}</code></>}{a.parameters && <> Params: <code className="bg-muted px-1 py-0.5 rounded">{a.parameters}</code></>}</li>))}</ul></div>)}
                                             {(rule.conditions?.length === 0 && rule.actions?.length === 0) && <p className="text-xs text-muted-foreground mt-1">No conditions or actions.</p>}
                                         </CardContent>
                                     </Card>
                                 ))
                             ) : ( <p className="text-sm text-muted-foreground pl-1">No rules defined.</p> )}
                         </AccordionContent>
                     </AccordionItem>
                 ))}
             </Accordion>

             {/* Rule Form Dialog (unified) */}
             <RuleForm
                 key={editingRule ? `edit-rule-${editingRule.id}` : `create-rule-${selectedRulesetIdForForm || 'new'}`}
                 open={isRuleFormOpen}
                 onOpenChange={setIsRuleFormOpen}
                 onSubmit={handleCreateOrUpdateRule}
                 rulesetId={selectedRulesetIdForForm} // Needed for title when creating
                 initialData={editingRule} // Pass null or rule object
                 isLoading={isSavingRule}
             />

        </div>
    );
}
