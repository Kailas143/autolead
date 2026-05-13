"use client";

import React, { useEffect, useState, useCallback } from "react";
import CSVUploader from "@/components/leads/CSVUploader";
import api from "@/lib/api";
import { cn } from "@/lib/utils";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Eye, Edit, Trash2, MoreHorizontal, Loader2, Mail } from "lucide-react";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogFooter,
  DialogTrigger 
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Lead {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  company: string;
  industry: string;
  status: string;
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState<number | null>(null);
  const [leadStats, setLeadStats] = useState<{ campaign_name: string; total_emails: number } | null>(null);

  const fetchLeads = useCallback(async () => {
    try {
      const response = await api.get("/leads/");
      setLeads(response.data);
    } catch (error) {
      console.error("Failed to fetch leads:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  useEffect(() => {
    if (isViewDialogOpen && selectedLead) {
      const fetchStats = async () => {
        try {
          const response = await api.get(`/leads/${selectedLead.id}/thread`);
          setLeadStats({
            campaign_name: response.data.campaign_name,
            total_emails: response.data.total_emails
          });
        } catch (error) {
          console.error("Failed to fetch lead stats:", error);
        }
      };
      fetchStats();
    } else {
      setLeadStats(null);
    }
  }, [isViewDialogOpen, selectedLead]);

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this lead?")) return;
    
    try {
      setIsDeleting(id);
      await api.delete(`/leads/${id}`);
      setLeads(leads.filter(l => l.id !== id));
    } catch (error) {
      console.error("Failed to delete lead:", error);
      alert("Failed to delete lead");
    } finally {
      setIsDeleting(null);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLead) return;

    try {
      const response = await api.put(`/leads/${selectedLead.id}`, selectedLead);
      setLeads(leads.map(l => l.id === selectedLead.id ? response.data : l));
      setIsEditDialogOpen(false);
    } catch (error) {
      console.error("Failed to update lead:", error);
      alert("Failed to update lead");
    }
  };

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Lead Intelligence</h1>
          <p className="text-muted-foreground mt-1">Enrich, manage, and segment your high-intent leads.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <Card className="lg:col-span-1 border-white/5 bg-white/5 backdrop-blur-sm h-fit">
          <CardHeader>
            <CardTitle className="text-lg">Inbound Stream</CardTitle>
          </CardHeader>
          <CardContent>
            <CSVUploader onUploadSuccess={() => {
              fetchLeads();
              let attempts = 0;
              const interval = setInterval(async () => {
                await fetchLeads();
                attempts++;
                if (attempts >= 5) clearInterval(interval);
              }, 2000);
            }} />
          </CardContent>
        </Card>

        <Card className="lg:col-span-3 border-white/5 bg-white/5 backdrop-blur-sm overflow-hidden">
          <CardHeader className="border-b border-white/5 pb-4">
            <CardTitle className="text-lg">Database Records</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader className="bg-white/[0.01]">
                <TableRow className="hover:bg-transparent border-white/5">
                  <TableHead className="text-muted-foreground pl-6">Name</TableHead>
                  <TableHead className="text-muted-foreground">Company</TableHead>
                  <TableHead className="text-muted-foreground">Status</TableHead>
                  <TableHead className="text-muted-foreground text-right pr-6">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                   <TableRow>
                    <TableCell colSpan={4} className="text-center py-20 text-muted-foreground">
                      <div className="flex flex-col items-center gap-2">
                        <Loader2 className="w-8 h-8 animate-spin text-primary" />
                        <span>Loading records...</span>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : leads.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-20 text-muted-foreground">
                      No leads imported yet. Upload a CSV file to get started.
                    </TableCell>
                  </TableRow>
                ) : (
                  leads.map((lead) => (
                    <TableRow key={lead.id} className="border-white/5 hover:bg-white/[0.02] transition-colors group">
                      <TableCell className="pl-6">
                        <div className="font-medium text-white">{lead.first_name} {lead.last_name}</div>
                        <div className="text-xs text-muted-foreground">{lead.email}</div>
                      </TableCell>
                      <TableCell>
                        <div className="text-white/80">{lead.company}</div>
                        <div className="text-[10px] text-muted-foreground uppercase tracking-widest">{lead.industry}</div>
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant="secondary" 
                          className={cn(
                            "capitalize rounded-lg px-2.5 py-0.5",
                            lead.status === "new" && "bg-blue-500/10 text-blue-500 border-blue-500/20",
                            lead.status === "contacted" && "bg-purple-500/10 text-purple-500 border-purple-500/20",
                            lead.status === "replied" && "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
                            lead.status === "converted" && "bg-orange-500/10 text-orange-500 border-orange-500/20"
                          )}
                        >
                          {lead.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right pr-6">
                        <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 hover:bg-white/10 text-muted-foreground hover:text-white"
                            onClick={() => {
                              setSelectedLead(lead);
                              setIsViewDialogOpen(true);
                            }}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 hover:bg-white/10 text-muted-foreground hover:text-white"
                            onClick={() => {
                              setSelectedLead(lead);
                              setIsEditDialogOpen(true);
                            }}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
                            onClick={() => handleDelete(lead.id)}
                            disabled={isDeleting === lead.id}
                          >
                            {isDeleting === lead.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="bg-[#0a0a0a] border-white/10 text-white sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Edit Lead Details</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUpdate} className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground uppercase tracking-widest font-bold">First Name</label>
                <Input 
                  value={selectedLead?.first_name || ""} 
                  onChange={e => setSelectedLead(prev => prev ? {...prev, first_name: e.target.value} : null)}
                  className="bg-white/5 border-white/10 h-11"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground uppercase tracking-widest font-bold">Last Name</label>
                <Input 
                  value={selectedLead?.last_name || ""} 
                  onChange={e => setSelectedLead(prev => prev ? {...prev, last_name: e.target.value} : null)}
                  className="bg-white/5 border-white/10 h-11"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground uppercase tracking-widest font-bold">Email Address</label>
              <Input 
                value={selectedLead?.email || ""} 
                onChange={e => setSelectedLead(prev => prev ? {...prev, email: e.target.value} : null)}
                className="bg-white/5 border-white/10 h-11"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground uppercase tracking-widest font-bold">Company</label>
              <Input 
                value={selectedLead?.company || ""} 
                onChange={e => setSelectedLead(prev => prev ? {...prev, company: e.target.value} : null)}
                className="bg-white/5 border-white/10 h-11"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground uppercase tracking-widest font-bold">Industry</label>
              <Input 
                value={selectedLead?.industry || ""} 
                onChange={e => setSelectedLead(prev => prev ? {...prev, industry: e.target.value} : null)}
                className="bg-white/5 border-white/10 h-11"
              />
            </div>
            <DialogFooter className="pt-6">
              <Button type="button" variant="ghost" onClick={() => setIsEditDialogOpen(false)}>Cancel</Button>
              <Button type="submit" className="px-8 shadow-lg shadow-primary/20">Save Changes</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Dialog */}
      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent className="bg-[#0a0a0a] border-white/10 text-white sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              Lead Profile
              <Badge variant="outline" className="text-[10px] uppercase border-white/10">{selectedLead?.status}</Badge>
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-8 py-6">
            <div className="flex items-center gap-6">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-primary/20 to-primary/5 border border-primary/20 flex items-center justify-center text-3xl font-bold text-primary shadow-xl">
                {selectedLead?.first_name[0]}{selectedLead?.last_name[0]}
              </div>
              <div>
                <h2 className="text-2xl font-bold">{selectedLead?.first_name} {selectedLead?.last_name}</h2>
                <p className="text-muted-foreground">{selectedLead?.email}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-8">
              <div className="space-y-1">
                <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">Company</p>
                <p className="text-lg font-medium">{selectedLead?.company}</p>
              </div>
              <div className="space-y-1">
                <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">Industry</p>
                <p className="text-lg font-medium">{selectedLead?.industry}</p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Outreach History</span>
                <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded">
                  {leadStats?.campaign_name || "Active Campaign"}
                </span>
              </div>
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-sm text-white/70">
                  <Mail className="w-4 h-4 text-primary" />
                  <span>
                    {leadStats ? (
                      leadStats.total_emails > 0 
                        ? `${leadStats.total_emails} emails sent to this lead`
                        : "No emails sent yet"
                    ) : (
                      "Loading history..."
                    )}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button className="w-full h-12 text-sm font-semibold" onClick={() => setIsViewDialogOpen(false)}>Close Profile</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

