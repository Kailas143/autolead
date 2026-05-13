"use client";

import React, { useEffect, useState } from "react";
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Cpu, 
  History, 
  ShieldCheck, 
  Trash2,
  RefreshCcw,
  Clock
} from "lucide-react";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

type SystemLog = {
  id: number;
  created_at: string;
  category: string;
  message: string;
  level: string;
};

type AIUsageEntry = {
  id: number;
  model_name: string;
  task_type: string;
  prompt_tokens: number;
  completion_tokens: number;
  created_at: string;
};

type AIUsageStats = {
  totals: {
    total: number;
    prompt: number;
    completion: number;
  };
  by_task: Record<string, number>;
  recent: AIUsageEntry[];
};

export default function AdminDashboard() {
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [aiUsage, setAiUsage] = useState<AIUsageStats | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshData = async () => {
    try {
      setLoading(true);
      const [logsRes, usageRes] = await Promise.all([
        api.get<SystemLog[]>("/admin/logs"),
        api.get<AIUsageStats>("/admin/ai-usage")
      ]);
      setLogs(logsRes.data);
      setAiUsage(usageRes.data);
    } catch (error) {
      console.error("Failed to fetch admin data:", error);
    } finally {
      setLoading(false);
    }
  };

  const clearLogs = async () => {
    if (!confirm("Are you sure you want to clear all system logs?")) return;
    try {
      await api.delete("/admin/logs/clear");
      setLogs([]);
    } catch (error) {
      console.error("Failed to clear logs:", error);
    }
  };

  useEffect(() => {
    let isCancelled = false;

    const loadData = async () => {
      try {
        const [logsRes, usageRes] = await Promise.all([
          api.get<SystemLog[]>("/admin/logs"),
          api.get<AIUsageStats>("/admin/ai-usage")
        ]);

        if (isCancelled) {
          return;
        }

        setLogs(logsRes.data);
        setAiUsage(usageRes.data);
      } catch (error) {
        if (!isCancelled) {
          console.error("Failed to fetch admin data:", error);
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };

    void loadData();

    return () => {
      isCancelled = true;
    };
  }, []);

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <ShieldCheck className="w-8 h-8 text-primary" />
            Infrastructure Console
          </h1>
          <p className="text-muted-foreground mt-1 text-sm uppercase tracking-widest font-medium">System Health & Token Analytics</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" size="sm" className="bg-white/5 border-white/10 gap-2 h-9" onClick={refreshData}>
            <RefreshCcw className="w-4 h-4" /> Refresh
          </Button>
          <Button variant="destructive" size="sm" className="gap-2 h-9" onClick={clearLogs}>
            <Trash2 className="w-4 h-4" /> Clear Logs
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="border-white/5 bg-white/5 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Total AI Tokens</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{(aiUsage?.totals?.total || 0).toLocaleString()}</div>
            <p className="text-[10px] text-emerald-500 mt-1 font-medium italic">Gemini Flash Active</p>
          </CardContent>
        </Card>
        <Card className="border-white/5 bg-white/5 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-bold text-muted-foreground uppercase tracking-widest">System Errors</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{logs.filter(l => l.level === "ERROR").length}</div>
            <p className="text-[10px] text-muted-foreground mt-1 font-medium">Last 50 entries</p>
          </CardContent>
        </Card>
        <Card className="border-white/5 bg-white/5 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Completion Ratio</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {aiUsage?.totals?.total > 0 
                ? ((aiUsage.totals.completion / aiUsage.totals.total) * 100).toFixed(1) 
                : 0}%
            </div>
            <p className="text-[10px] text-muted-foreground mt-1 font-medium">Output Efficiency</p>
          </CardContent>
        </Card>
        <Card className="border-white/5 bg-white/5 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Avg Response</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">1.2s</div>
            <p className="text-[10px] text-emerald-500 mt-1 font-medium">Optimized latency</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="logs" className="space-y-6">
        <TabsList className="bg-white/5 border border-white/5 p-1">
          <TabsTrigger value="logs" className="gap-2 px-6"><History className="w-4 h-4" /> System Logs</TabsTrigger>
          <TabsTrigger value="usage" className="gap-2 px-6"><Cpu className="w-4 h-4" /> AI Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="logs" className="animate-in fade-in duration-500">
          <Card className="border-white/5 bg-white/5 backdrop-blur-sm overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-white/5 hover:bg-transparent">
                  <TableHead className="text-muted-foreground pl-6">Time</TableHead>
                  <TableHead className="text-muted-foreground">Category</TableHead>
                  <TableHead className="text-muted-foreground">Message</TableHead>
                  <TableHead className="text-muted-foreground">Level</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow><TableCell colSpan={4} className="text-center py-20 text-muted-foreground">Loading logs...</TableCell></TableRow>
                ) : logs.length === 0 ? (
                  <TableRow><TableCell colSpan={4} className="text-center py-20 text-muted-foreground">No logs found.</TableCell></TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id} className="border-white/5 group hover:bg-white/[0.02]">
                      <TableCell className="pl-6 text-xs text-muted-foreground">
                        {format(new Date(log.created_at), "HH:mm:ss MMM d")}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-[10px] uppercase font-bold border-white/10">{log.category}</Badge>
                      </TableCell>
                      <TableCell className="max-w-md">
                        <p className="text-sm text-white/80 line-clamp-1 group-hover:line-clamp-none transition-all">{log.message}</p>
                      </TableCell>
                      <TableCell>
                        <div className={cn(
                          "w-2 h-2 rounded-full",
                          log.level === "ERROR" ? "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]" : "bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"
                        )} />
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        <TabsContent value="usage" className="animate-in fade-in duration-500">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <Card className="lg:col-span-1 border-white/5 bg-white/5 backdrop-blur-sm h-fit">
              <CardHeader>
                <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Task Distribution</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {aiUsage && Object.entries(aiUsage.by_task).map(([task, tokens]) => (
                  <div key={task} className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="capitalize text-white/70">{task.replace("_", " ")}</span>
                      <span className="text-primary font-bold">{tokens.toLocaleString()}</span>
                    </div>
                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary transition-all duration-500" 
                        style={{ width: `${(tokens / aiUsage.totals.total) * 100}%` }} 
                      />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="lg:col-span-2 border-white/5 bg-white/5 backdrop-blur-sm overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="border-white/5 hover:bg-transparent">
                    <TableHead className="text-muted-foreground pl-6">Model</TableHead>
                    <TableHead className="text-muted-foreground">Task</TableHead>
                    <TableHead className="text-muted-foreground">Prompt</TableHead>
                    <TableHead className="text-muted-foreground">Output</TableHead>
                    <TableHead className="text-muted-foreground text-right pr-6">Time</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {aiUsage?.recent.map((entry) => (
                    <TableRow key={entry.id} className="border-white/5 hover:bg-white/[0.02]">
                      <TableCell className="pl-6 text-xs text-white/80">{entry.model_name}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="text-[10px] uppercase bg-primary/10 text-primary border-none">
                          {entry.task_type.replace("_", " ")}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs font-mono text-muted-foreground">{entry.prompt_tokens}</TableCell>
                      <TableCell className="text-xs font-mono text-muted-foreground">{entry.completion_tokens}</TableCell>
                      <TableCell className="text-right pr-6 text-xs text-muted-foreground flex items-center justify-end gap-2">
                        <Clock className="w-3 h-3" />
                        {format(new Date(entry.created_at), "HH:mm:ss")}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
