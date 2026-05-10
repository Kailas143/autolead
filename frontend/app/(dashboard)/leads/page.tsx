"use client";

import React, { useEffect, useState, useCallback } from "react";
import CSVUploader from "@/components/leads/CSVUploader";
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
import { cn } from "@/lib/utils";
import api from "@/lib/api";

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

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white">Lead Intelligence</h1>
        <p className="text-muted-foreground mt-1">Enrich, manage, and segment your high-intent leads.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <Card className="lg:col-span-1 border-white/5 bg-white/5 backdrop-blur-sm h-fit">
          <CardHeader>
            <CardTitle className="text-lg">Inbound Stream</CardTitle>
          </CardHeader>
          <CardContent>
            <CSVUploader onUploadSuccess={() => {
              fetchLeads(); // Immediate refresh
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
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-border/50">
                  <TableHead className="text-muted-foreground">Name</TableHead>
                  <TableHead className="text-muted-foreground">Company</TableHead>
                  <TableHead className="text-muted-foreground">Industry</TableHead>
                  <TableHead className="text-muted-foreground">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                   <TableRow>
                    <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                      Loading leads...
                    </TableCell>
                  </TableRow>
                ) : leads.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                      No leads imported yet. Upload a CSV file to get started.
                    </TableCell>
                  </TableRow>
                ) : (
                  leads.map((lead) => (
                    <TableRow key={lead.id} className="border-border/50 hover:bg-white/5 transition-colors">
                      <TableCell className="font-medium">
                        <div>
                          <p className="text-foreground">{lead.first_name} {lead.last_name}</p>
                          <p className="text-xs text-muted-foreground">{lead.email}</p>
                        </div>
                      </TableCell>
                      <TableCell className="text-foreground">{lead.company}</TableCell>
                      <TableCell className="text-foreground">{lead.industry}</TableCell>
                      <TableCell>
                        <Badge 
                          variant="secondary" 
                          className={cn(
                            "capitalize",
                            lead.status === "new" && "bg-blue-500/10 text-blue-500 border-blue-500/20",
                            lead.status === "contacted" && "bg-purple-500/10 text-purple-500 border-purple-500/20",
                            lead.status === "replied" && "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
                            lead.status === "converted" && "bg-orange-500/10 text-orange-500 border-orange-500/20"
                          )}
                        >
                          {lead.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

