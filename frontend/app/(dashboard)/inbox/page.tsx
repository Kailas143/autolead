"use client";

import { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, User, Calendar, XCircle, CheckCircle2, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

interface Lead {
  first_name: string;
  last_name: string;
  company: string;
  email: string;
}

interface Reply {
  id: number;
  message: string;
  classification: string;
  created_at: string;
  lead?: Lead;
}

const getClassificationConfig = (classification: string) => {
  const normalized = classification?.toLowerCase()?.replace(/_/g, " ");
  switch (normalized) {
    case "interested":
      return { color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20", icon: CheckCircle2 };
    case "not interested":
      return { color: "text-destructive bg-destructive/10 border-destructive/20", icon: XCircle };
    case "later":
      return { color: "text-blue-500 bg-blue-500/10 border-blue-500/20", icon: Clock };
    case "booked call":
      return { color: "text-purple-500 bg-purple-500/10 border-purple-500/20", icon: Calendar };
    default:
      return { color: "text-muted-foreground bg-white/5 border-white/10", icon: MessageSquare };
  }
};

export default function InboxPage() {
  const [replies, setReplies] = useState<Reply[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReplies = useCallback(async () => {
    try {
      const response = await api.get("/replies/");
      setReplies(response.data);
    } catch (error) {
      console.error("Failed to fetch replies:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReplies();
  }, [fetchReplies]);

  const handleReply = (reply: Reply) => {
    if (!reply.lead?.email) {
      alert("No email found for this lead.");
      return;
    }
    const subject = `Re: ${reply.message.substring(0, 50)}...`;
    const mailto = `mailto:${reply.lead.email}?subject=${encodeURIComponent(subject)}`;
    window.location.href = mailto;
  };

  const handleViewThread = (reply: Reply) => {
    alert("Thread view is coming soon! You can reply directly to the lead in the meantime.");
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Inbox</h1>
        <p className="text-muted-foreground mt-1">AI-classified replies from your campaigns.</p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {loading ? (
          <div className="text-center py-12 text-muted-foreground">Loading replies...</div>
        ) : replies.length === 0 ? (
          <Card className="border-dashed border-border/50 bg-transparent">
            <CardContent className="p-12 flex flex-col items-center justify-center text-center">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <MessageSquare className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">No replies yet</h3>
              <p className="text-muted-foreground max-w-xs mx-auto mt-2">
                Your AI-classified replies will appear here once your campaigns start receiving engagement.
              </p>
            </CardContent>
          </Card>
        ) : (
          replies.map((reply) => {
            const config = getClassificationConfig(reply.classification);
            return (
              <Card key={reply.id} className="border-border/50 bg-card/30 backdrop-blur-sm hover:border-primary/50 transition-all duration-300 group">
                <CardContent className="p-6">
                  <div className="flex flex-col md:flex-row md:items-start gap-6">
                    <div className="flex-1 space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                            <User className="w-5 h-5 text-primary" />
                          </div>
                          <div>
                            <h3 className="font-bold text-foreground">
                              {reply.lead ? `${reply.lead.first_name} ${reply.lead.last_name}` : "Unknown Lead"}
                            </h3>
                            <p className="text-xs text-muted-foreground">{reply.lead?.company || "Unknown Company"}</p>
                          </div>
                        </div>
                        <Badge className={cn("capitalize flex items-center gap-1.5", config.color)}>
                          <config.icon className="w-3 h-3" />
                          {reply.classification.replace("_", " ")}
                        </Badge>
                      </div>
                      
                      <div className="bg-white/5 rounded-xl p-4 border border-white/10 italic text-sm text-foreground/80 leading-relaxed">
                        &quot;{reply.message}&quot;
                      </div>
  
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Received {formatDistanceToNow(new Date(reply.created_at))} ago</span>
                        <div className="flex gap-4">
                          <button 
                            onClick={() => handleViewThread(reply)}
                            className="hover:text-primary transition-colors cursor-pointer"
                          >
                            View Thread
                          </button>
                          <button 
                            onClick={() => handleReply(reply)}
                            className="hover:text-primary transition-colors cursor-pointer"
                          >
                            Reply Now
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}
