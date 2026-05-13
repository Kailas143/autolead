"use client";

import React, { useEffect, useState } from "react";
import SequenceBuilder from "@/components/campaigns/SequenceBuilder";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { format, formatDistanceToNow } from "date-fns";
import { Loader2, Play, Pause, BarChart3, Plus, Trash2, Clock3 } from "lucide-react";
import { cn } from "@/lib/utils";

interface Campaign {
  id: number;
  name: string;
  description: string;
  status: string;
  created_at: string;
  scheduled_for?: string | null;
  metrics: {
    sent: number;
    open_rate: string;
    reply_rate: string;
    progress: number;
  };
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [isActionLoading, setIsActionLoading] = useState<number | null>(null);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      const response = await api.get("/campaigns/");
      setCampaigns(response.data);
    } catch (error) {
      console.error("Failed to fetch campaigns:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    Promise.resolve().then(() => fetchCampaigns());
  }, []);

  const handlePause = async (id: number, currentStatus: string) => {
    try {
      setIsActionLoading(id);
      if (currentStatus === "active") {
        await api.post(`/campaigns/${id}/pause`);
      } else {
        await api.post(`/campaigns/${id}/launch`);
      }
      await fetchCampaigns();
    } catch (error) {
      console.error("Failed to toggle campaign status:", error);
    } finally {
      setIsActionLoading(null);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this campaign? This will remove all associated sequences.")) return;
    try {
      setIsActionLoading(id);
      await api.delete(`/campaigns/${id}`);
      await fetchCampaigns();
    } catch (error) {
      console.error("Failed to delete campaign:", error);
    } finally {
      setIsActionLoading(null);
    }
  };

  const CampaignCard = ({ campaign }: { campaign: Campaign }) => (
    <Card key={campaign.id} className="border-border/50 bg-card/30 backdrop-blur-sm hover:border-primary/50 transition-all duration-300 group">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-xl font-bold text-foreground">{campaign.name}</CardTitle>
          <p className="text-sm text-muted-foreground">
            Started {format(new Date(campaign.created_at), "MMM d, yyyy")}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge className={cn(
            "capitalize",
            campaign.status === "active"
              ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
              : campaign.status === "scheduled"
                ? "bg-sky-500/10 text-sky-500 border-sky-500/20"
                : "bg-orange-500/10 text-orange-500 border-orange-500/20"
          )}>
            {campaign.status}
          </Badge>
          <button 
            onClick={() => handleDelete(campaign.id)}
            disabled={isActionLoading === campaign.id}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors opacity-0 group-hover:opacity-100"
          >
            {isActionLoading === campaign.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
          </button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {campaign.status === "scheduled" && campaign.scheduled_for && (
          <div className="rounded-2xl border border-sky-500/20 bg-sky-500/8 p-4">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 rounded-xl bg-sky-500/12 p-2 text-sky-400">
                <Clock3 className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold uppercase tracking-[0.22em] text-sky-400">
                  Next scheduled send
                </div>
                <div className="mt-1 text-sm font-semibold text-white">
                  {format(new Date(campaign.scheduled_for), "MMM d, yyyy h:mm a")}
                </div>
                <div className="mt-1 text-xs text-sky-100/75">
                  {formatDistanceToNow(new Date(campaign.scheduled_for), { addSuffix: true })}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-xs text-muted-foreground uppercase mb-1">Sent</p>
            <p className="text-lg font-bold text-foreground">{campaign.metrics.sent}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground uppercase mb-1">Open</p>
            <p className="text-lg font-bold text-foreground">{campaign.metrics.open_rate}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground uppercase mb-1">Reply</p>
            <p className="text-lg font-bold text-foreground">{campaign.metrics.reply_rate}</p>
          </div>
        </div>
        
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Progress</span>
            <span className="text-foreground font-medium">{campaign.metrics.progress}%</span>
          </div>
          <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary transition-all duration-500" 
              style={{ width: `${campaign.metrics.progress}%` }} 
            />
          </div>
        </div>

        <div className="flex gap-3">
          <button 
            onClick={() => handlePause(campaign.id, campaign.status)}
            disabled={isActionLoading === campaign.id}
            className="flex-1 py-2 rounded-xl border border-border/50 bg-white/5 text-sm font-medium hover:bg-white/10 transition-colors flex items-center justify-center gap-2"
          >
            {isActionLoading === campaign.id ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : campaign.status === "active" || campaign.status === "scheduled" ? (
              <><Pause className="w-3.5 h-3.5" /> Pause</>
            ) : (
              <><Play className="w-3.5 h-3.5" /> Launch</>
            )}
          </button>
          <button 
            onClick={() => window.location.href = "/analytics"}
            className="flex-1 py-2 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
          >
            <BarChart3 className="w-3.5 h-3.5" /> View Stats
          </button>
        </div>
      </CardContent>
    </Card>
  );

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
          <TabsTrigger value="builder" className="rounded-lg px-6 flex items-center gap-2">
            <Plus className="w-4 h-4" /> Builder
          </TabsTrigger>
          <TabsTrigger value="active" className="rounded-lg px-6 flex items-center gap-2">
            <Play className="w-4 h-4" /> Active Campaigns
          </TabsTrigger>
          <TabsTrigger value="scheduled" className="rounded-lg px-6 flex items-center gap-2">
            <Loader2 className="w-4 h-4" /> Scheduled
          </TabsTrigger>
          <TabsTrigger value="drafts" className="rounded-lg px-6 flex items-center gap-2">
            <Loader2 className="w-4 h-4" /> Drafts
          </TabsTrigger>
        </TabsList>

        <TabsContent value="builder" className="animate-in fade-in duration-300">
          <SequenceBuilder />
        </TabsContent>

        <TabsContent value="active" className="animate-in fade-in duration-300">
          {loading ? (
            <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
          ) : campaigns.filter(c => c.status === "active").length === 0 ? (
            <div className="text-center py-20 bg-white/5 rounded-2xl border border-dashed border-border/50">
              <p className="text-muted-foreground">No active campaigns found. Launch one from the builder!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {campaigns.filter(c => c.status === "active").map((campaign) => (
                <CampaignCard key={campaign.id} campaign={campaign} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="scheduled" className="animate-in fade-in duration-300">
          {loading ? (
            <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
          ) : campaigns.filter(c => c.status === "scheduled").length === 0 ? (
            <div className="text-center py-20 bg-white/5 rounded-2xl border border-dashed border-border/50">
              <p className="text-muted-foreground">No scheduled campaigns yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {campaigns.filter(c => c.status === "scheduled").map((campaign) => (
                <CampaignCard key={campaign.id} campaign={campaign} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="drafts" className="animate-in fade-in duration-300">
          {loading ? (
            <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
          ) : campaigns.filter(c => c.status === "draft").length === 0 ? (
            <div className="text-center py-20 bg-white/5 rounded-2xl border border-dashed border-border/50">
              <p className="text-muted-foreground">No draft campaigns found.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {campaigns.filter(c => c.status === "draft").map((campaign) => (
                <CampaignCard key={campaign.id} campaign={campaign} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
