"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, TrendingUp, PieChart, MousePointer2, Mail, MessageSquare } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export default function AnalyticsPage() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Campaign Analytics</h1>
        <p className="text-muted-foreground mt-1">Deep dive into your outreach performance.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { name: "Total Sent", value: "-", trend: "-", icon: Mail },
          { name: "Total Opens", value: "-", trend: "-", icon: MousePointer2 },
          { name: "Total Replies", value: "-", trend: "-", icon: MessageSquare },
          { name: "Conversion", value: "-", trend: "-", icon: TrendingUp },
        ].map((metric) => (
          <Card key={metric.name} className="border-border/50 bg-card/30 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-muted-foreground">{metric.name}</CardTitle>
              <metric.icon className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{metric.value}</div>
              <Badge variant="outline" className="mt-2 bg-muted text-muted-foreground border-border/50">
                {metric.trend}
              </Badge>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card className="border-border/50 bg-card/30 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-primary" />
              Engagement Over Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full bg-white/5 border border-dashed border-border rounded-xl flex items-center justify-center">
              <span className="text-muted-foreground italic">Run campaigns to see engagement analytics</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50 bg-card/30 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="w-5 h-5 text-primary" />
              Reply Sentiment Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full bg-white/5 border border-dashed border-border rounded-xl flex items-center justify-center">
              <span className="text-muted-foreground italic">Create campaigns to analyze sentiment</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/50 bg-card/30 backdrop-blur-sm">
        <CardHeader>
          <CardTitle>Top Performing Sequences</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-center h-[300px] text-muted-foreground">
              No top performing sequences yet. Create campaigns to see results.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
