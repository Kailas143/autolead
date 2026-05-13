"use client";

import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  BarChart3, TrendingUp, PieChart as PieChartIcon, 
  MousePointer2, Mail, MessageSquare, Loader2 
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import dynamic from "next/dynamic";

// Dynamically import Recharts components to avoid SSR dimension issues
const ResponsiveContainer = dynamic(
  () => import("recharts").then((mod) => mod.ResponsiveContainer),
  { ssr: false }
);
const AreaChart = dynamic(
  () => import("recharts").then((mod) => mod.AreaChart),
  { ssr: false }
);
const Area = dynamic(
  () => import("recharts").then((mod) => mod.Area),
  { ssr: false }
);
const XAxis = dynamic(
  () => import("recharts").then((mod) => mod.XAxis),
  { ssr: false }
);
const YAxis = dynamic(
  () => import("recharts").then((mod) => mod.YAxis),
  { ssr: false }
);
const CartesianGrid = dynamic(
  () => import("recharts").then((mod) => mod.CartesianGrid),
  { ssr: false }
);
const Tooltip = dynamic(
  () => import("recharts").then((mod) => mod.Tooltip),
  { ssr: false }
);
const PieChart = dynamic(
  () => import("recharts").then((mod) => mod.PieChart),
  { ssr: false }
);
const Pie = dynamic(
  () => import("recharts").then((mod) => mod.Pie),
  { ssr: false }
);
const Cell = dynamic(
  () => import("recharts").then((mod) => mod.Cell),
  { ssr: false }
);
const Legend = dynamic(
  () => import("recharts").then((mod) => mod.Legend),
  { ssr: false }
);

const COLORS = ["#10b981", "#ef4444", "#3b82f6", "#8b5cf6", "#f59e0b"];

interface AnalyticsData {
  summary: {
    total_leads: number;
    total_emails_sent: number;
    total_opens: number;
    open_rate: string;
    total_replies: number;
    reply_rate: string;
  };
  sentiment: Array<{ name: string; value: number }>;
  engagement: Array<{ date: string; sent: number; opens: number }>;
  top_sequences: Array<{
    subject: string;
    sent: number;
    opens: number;
    replies: number;
    reply_rate: string;
  }>;
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isCancelled = false;

    const fetchAnalytics = async () => {
      try {
        const response = await api.get("/analytics/stats");
        if (!isCancelled) {
          setData(response.data);
        }
      } catch (error) {
        console.error("Failed to fetch analytics:", error);
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };
    void fetchAnalytics();

    return () => {
      isCancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[70vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const summary = data?.summary || {
    total_leads: 0,
    total_emails_sent: 0,
    total_opens: 0,
    total_replies: 0,
    open_rate: "0%",
    reply_rate: "0%"
  };

  const metrics = [
    { name: "Total Sent", value: summary.total_emails_sent, trend: "Outreach Volume", icon: Mail },
    { name: "Total Opens", value: summary.total_opens, trend: summary.open_rate, icon: MousePointer2 },
    { name: "Total Replies", value: summary.total_replies, trend: summary.reply_rate, icon: MessageSquare },
    { name: "Lead Score", value: summary.total_leads, trend: "Total Leads", icon: TrendingUp },
  ];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Campaign Analytics</h1>
        <p className="text-muted-foreground mt-1">Deep dive into your outreach performance.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric) => (
          <Card key={metric.name} className="border-border/50 bg-card/30 backdrop-blur-sm shadow-xl">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-muted-foreground">{metric.name}</CardTitle>
              <metric.icon className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{metric.value}</div>
              <Badge variant="outline" className="mt-2 bg-primary/10 text-primary border-primary/20">
                {metric.trend}
              </Badge>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card className="border-border/50 bg-card/30 backdrop-blur-sm shadow-xl overflow-hidden">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-primary" />
              Engagement Over Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full min-w-0">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data?.engagement} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorSent" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorOpens" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#ffffff10" />
                  <XAxis dataKey="date" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#1e1e1e", border: "1px solid #333", borderRadius: "8px" }}
                    itemStyle={{ color: "#fff" }}
                  />
                  <Area type="monotone" dataKey="sent" stroke="#3b82f6" fillOpacity={1} fill="url(#colorSent)" />
                  <Area type="monotone" dataKey="opens" stroke="#10b981" fillOpacity={1} fill="url(#colorOpens)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50 bg-card/30 backdrop-blur-sm shadow-xl overflow-hidden">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChartIcon className="w-5 h-5 text-primary" />
              Reply Sentiment Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full min-w-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data?.sentiment}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {data?.sentiment?.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#1e1e1e", border: "1px solid #333", borderRadius: "8px" }}
                    itemStyle={{ color: "#fff" }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/50 bg-card/30 backdrop-blur-sm shadow-xl">
        <CardHeader>
          <CardTitle>Top Performing Sequences</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border/50 text-muted-foreground text-sm">
                  <th className="py-4 px-4 font-medium">Sequence Subject</th>
                  <th className="py-4 px-4 font-medium">Sent</th>
                  <th className="py-4 px-4 font-medium">Opens</th>
                  <th className="py-4 px-4 font-medium">Replies</th>
                  <th className="py-4 px-4 font-medium">Rate</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {data?.top_sequences?.map((seq, index) => (
                  <tr key={index} className="border-b border-border/50 hover:bg-white/5 transition-colors">
                    <td className="py-4 px-4 font-medium text-foreground">{seq.subject}</td>
                    <td className="py-4 px-4 text-muted-foreground">{seq.sent}</td>
                    <td className="py-4 px-4 text-muted-foreground">{seq.opens}</td>
                    <td className="py-4 px-4 text-muted-foreground">{seq.replies}</td>
                    <td className="py-4 px-4">
                      <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                        {seq.reply_rate}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!data?.top_sequences || data.top_sequences.length === 0) && (
              <div className="text-center py-12 text-muted-foreground italic">
                No top performing sequences yet.
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
