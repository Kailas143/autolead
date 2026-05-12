"use client";

import React, { useEffect, useState } from "react";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Mail, MousePointer2, MessageSquare, BarChart3, Loader2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface Reply {
  id: number;
  message: string;
  classification: string;
  created_at: string;
  lead?: {
    first_name: string;
    last_name: string;
    company: string;
  };
}

export default function DashboardPage() {
  const [stats, setStats] = useState({
    total_leads: 0,
    total_emails_sent: 0,
    open_rate: "0%",
    reply_rate: "0%"
  });
  const [recentReplies, setRecentReplies] = useState<Reply[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsRes, repliesRes] = await Promise.all([
          api.get("/analytics/stats"),
          api.get("/replies/?limit=4")
        ]);
        
        // Use summary from nested API response
        if (statsRes.data.summary) {
          setStats(statsRes.data.summary);
        }
        setRecentReplies(repliesRes.data);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  const statItems = [
    { name: "Total Leads", value: stats.total_leads, icon: Users, color: "text-blue-500", bg: "bg-blue-500/10" },
    { name: "Emails Sent", value: stats.total_emails_sent, icon: Mail, color: "text-purple-500", bg: "bg-purple-500/10" },
    { name: "Open Rate", value: stats.open_rate, icon: MousePointer2, color: "text-emerald-500", bg: "bg-emerald-500/10" },
    { name: "Reply Rate", value: stats.reply_rate, icon: MessageSquare, color: "text-orange-500", bg: "bg-orange-500/10" },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[70vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight text-white">Welcome back, Aurvyz</h1>
        <p className="text-muted-foreground">Here&apos;s what&apos;s happening with your outreach today.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statItems.map((stat) => (
          <Card key={stat.name} className="border-white/5 bg-white/5 backdrop-blur-sm hover:border-primary/50 transition-all duration-500 group overflow-hidden relative">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {stat.name}
              </CardTitle>
              <div className={`${stat.bg} ${stat.color} p-2.5 rounded-xl transition-transform group-hover:scale-110 duration-300`}>
                <stat.icon className="w-4 h-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white tracking-tight">{stat.value}</div>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-md bg-emerald-500/10 text-emerald-500">
                  +0%
                </span>
                <span className="text-[10px] text-muted-foreground font-medium">from last week</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="lg:col-span-2 border-white/5 bg-white/5 backdrop-blur-sm shadow-2xl">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg">Campaign Performance</CardTitle>
              <p className="text-xs text-muted-foreground mt-1">Daily engagement metrics across all active campaigns.</p>
            </div>
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-primary" />
              <div className="w-3 h-3 rounded-full bg-accent" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-[350px] flex flex-col items-center justify-center border border-dashed border-white/10 rounded-2xl bg-black/20">
              <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-4">
                <BarChart3 className="w-6 h-6 text-muted-foreground" />
              </div>
              <span className="text-sm font-medium text-muted-foreground">Detailed analytics available in the Analytics tab</span>
              <button 
                onClick={() => window.location.href = "/analytics"}
                className="mt-4 text-xs font-semibold text-primary hover:underline"
              >
                View detailed report
              </button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/5 bg-white/5 backdrop-blur-sm shadow-2xl">
          <CardHeader>
            <CardTitle className="text-lg">Recent Engagement</CardTitle>
            <p className="text-xs text-muted-foreground mt-1">Latest replies and interested leads.</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {recentReplies.length === 0 ? (
                <div className="pt-4 text-center">
                  <span className="text-xs text-muted-foreground italic">Monitoring for new activity...</span>
                </div>
              ) : (
                recentReplies.map((reply) => (
                  <div key={reply.id} className="flex items-start gap-4 group">
                    <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                      <Users className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-xs font-bold text-white truncate">
                          {reply.lead ? `${reply.lead.first_name} ${reply.lead.last_name}` : "Lead"}
                        </p>
                        <span className="text-[10px] text-muted-foreground">
                          {formatDistanceToNow(new Date(reply.created_at))} ago
                        </span>
                      </div>
                      <p className="text-[11px] text-muted-foreground line-clamp-1 italic">
                        &quot;{reply.message}&quot;
                      </p>
                      <div className="mt-1">
                        <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 capitalize font-medium">
                          {reply.classification.replace("_", " ")}
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              )}
              {recentReplies.length > 0 && (
                <div className="pt-4 text-center border-t border-white/5">
                  <button 
                    onClick={() => window.location.href = "/inbox"}
                    className="text-xs font-semibold text-primary hover:underline"
                  >
                    View all in Inbox
                  </button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
