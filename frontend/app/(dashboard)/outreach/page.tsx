"use client";

import React, { useEffect, useState } from "react";
import api from "@/lib/api";
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
import { Loader2, Mail, CheckCircle2, Clock, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { format } from "date-fns";

interface OutreachLog {
  id: number;
  lead_name: string;
  company: string;
  email: string;
  industry: string;
  emails_sent: number;
  last_step: number;
  last_sent: string | null;
  status: "active" | "replied" | "pending";
}

export default function OutreachPage() {
  const [logs, setLogs] = useState<OutreachLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await api.get("/analytics/outreach-log");
        setLogs(response.data);
      } catch (error) {
        console.error("Failed to fetch outreach logs:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  const filteredLogs = logs.filter(log => 
    log.lead_name.toLowerCase().includes(search.toLowerCase()) ||
    log.company.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-white">Outreach Tracking</h1>
          <p className="text-muted-foreground mt-1">Track which follow-ups have been sent to which customers.</p>
        </div>
      </div>

      <Card className="border-white/5 bg-white/5 backdrop-blur-sm overflow-hidden">
        <CardHeader className="border-b border-white/5 bg-white/[0.02] flex flex-row items-center justify-between">
          <CardTitle className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">Follow-up Log</CardTitle>
          <div className="relative w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input 
              placeholder="Search leads or companies..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 bg-black/20 border-white/10 h-9 text-xs"
            />
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
          ) : (
            <Table>
              <TableHeader className="bg-white/[0.01]">
                <TableRow className="border-white/5 hover:bg-transparent">
                  <TableHead className="text-muted-foreground">Customer Name</TableHead>
                  <TableHead className="text-muted-foreground">Company</TableHead>
                  <TableHead className="text-muted-foreground">Status</TableHead>
                  <TableHead className="text-muted-foreground">Steps Sent</TableHead>
                  <TableHead className="text-muted-foreground text-right">Last Follow-up</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredLogs.map((log) => (
                  <TableRow key={log.id} className="border-white/5 hover:bg-white/[0.02] transition-colors group">
                    <TableCell>
                      <div className="font-medium text-white">{log.lead_name}</div>
                      <div className="text-xs text-muted-foreground">{log.email}</div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm text-white/80">{log.company}</div>
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wider">{log.industry}</div>
                    </TableCell>
                    <TableCell>
                      {log.status === "replied" ? (
                        <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 gap-1.5 px-2.5">
                          <CheckCircle2 className="w-3 h-3" /> Replied
                        </Badge>
                      ) : log.status === "active" ? (
                        <Badge className="bg-primary/10 text-primary border-primary/20 gap-1.5 px-2.5">
                          <Mail className="w-3 h-3" /> Active
                        </Badge>
                      ) : (
                        <Badge className="bg-white/5 text-muted-foreground border-white/10 gap-1.5 px-2.5">
                          <Clock className="w-3 h-3" /> Pending
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-bold text-white">{log.emails_sent}</span>
                        <span className="text-xs text-muted-foreground">/ steps</span>
                        {log.last_step > 0 && (
                          <span className="text-[10px] text-primary bg-primary/10 px-1.5 py-0.5 rounded ml-2">Step {log.last_step}</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      {log.last_sent ? (
                        <div className="text-sm text-white/70">
                          {format(new Date(log.last_sent), "MMM d, h:mm a")}
                        </div>
                      ) : (
                        <span className="text-muted-foreground text-xs italic">Not started</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {filteredLogs.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-20 text-muted-foreground">
                      No outreach history found.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
