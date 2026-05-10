"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Users, Mail, MousePointer2, MessageSquare, BarChart3 } from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight text-white">Welcome back, Aurvyz</h1>
        <p className="text-muted-foreground">Here&apos;s what&apos;s happening with your outreach today.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { name: "Total Leads", value: "27", icon: Users, color: "text-blue-500", bg: "bg-blue-500/10" },
          { name: "Emails Sent", value: "0", icon: Mail, color: "text-purple-500", bg: "bg-purple-500/10" },
          { name: "Open Rate", value: "0%", icon: MousePointer2, color: "text-emerald-500", bg: "bg-emerald-500/10" },
          { name: "Reply Rate", value: "0%", icon: MessageSquare, color: "text-orange-500", bg: "bg-orange-500/10" },
        ].map((stat) => (
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
        <Card className="lg:col-span-2 border-white/5 bg-white/5 backdrop-blur-sm">
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
              <span className="text-sm font-medium text-muted-foreground">Analytics will appear once campaigns start</span>
              <button className="mt-4 text-xs font-semibold text-primary hover:underline">Launch your first campaign</button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/5 bg-white/5 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-lg">Recent Engagement</CardTitle>
            <p className="text-xs text-muted-foreground mt-1">Latest replies and interested leads.</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-4 animate-pulse">
                  <div className="w-10 h-10 rounded-xl bg-white/5" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 w-24 bg-white/5 rounded" />
                    <div className="h-2 w-full bg-white/5 rounded" />
                  </div>
                </div>
              ))}
              <div className="pt-4 text-center">
                <span className="text-xs text-muted-foreground">Monitoring for new activity...</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
