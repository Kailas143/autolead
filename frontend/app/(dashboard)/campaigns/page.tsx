"use client";

import React from "react";
import SequenceBuilder from "@/components/campaigns/SequenceBuilder";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Send, Clock, CheckCircle2, Play } from "lucide-react";

export default function CampaignsPage() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Campaigns</h1>
          <p className="text-muted-foreground mt-1">Design and automate your outreach flows.</p>
        </div>
      </div>

      <Tabs defaultValue="builder" className="space-y-6">
        <TabsList className="bg-card/50 border border-border/50 p-1 rounded-xl">
          <TabsTrigger value="builder" className="rounded-lg px-6">Sequence Builder</TabsTrigger>
          <TabsTrigger value="active" className="rounded-lg px-6">Active Campaigns</TabsTrigger>
          <TabsTrigger value="drafts" className="rounded-lg px-6">Drafts</TabsTrigger>
        </TabsList>

        <TabsContent value="builder" className="animate-in fade-in duration-300">
          <SequenceBuilder />
        </TabsContent>

        <TabsContent value="active" className="animate-in fade-in duration-300">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2].map((i) => (
              <Card key={i} className="border-border/50 bg-card/30 backdrop-blur-sm hover:border-primary/50 transition-all duration-300 group">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-xl font-bold text-foreground">SaaS Founders Outreach</CardTitle>
                    <p className="text-sm text-muted-foreground">Started May 2, 2026</p>
                  </div>
                  <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">Active</Badge>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground uppercase mb-1">Sent</p>
                      <p className="text-lg font-bold text-foreground">842</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground uppercase mb-1">Open</p>
                      <p className="text-lg font-bold text-foreground">42%</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground uppercase mb-1">Reply</p>
                      <p className="text-lg font-bold text-foreground">12%</p>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Progress</span>
                      <span className="text-foreground font-medium">65%</span>
                    </div>
                    <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full bg-primary w-[65%]" />
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <button className="flex-1 py-2 rounded-xl border border-border/50 bg-white/5 text-sm font-medium hover:bg-white/10 transition-colors">
                      Pause
                    </button>
                    <button className="flex-1 py-2 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity">
                      View Analytics
                    </button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
