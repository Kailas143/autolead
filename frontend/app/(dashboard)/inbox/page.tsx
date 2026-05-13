"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  MessageSquare, User, Calendar, XCircle, 
  CheckCircle2, Clock, Mail
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

interface Lead {
  id: number;
  first_name: string;
  last_name: string;
  company: string;
  email: string;
}

interface ThreadItem {
  type: "sent" | "received";
  id: number;
  subject: string;
  content: string;
  timestamp: string;
  status?: string;
  classification?: string;
}

interface Reply {
  id: number;
  message: string;
  classification: string;
  created_at: string;
  lead_id: number;
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
  
  // Thread state
  const [selectedThread, setSelectedThread] = useState<ThreadItem[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [isThreadOpen, setIsThreadOpen] = useState(false);
  const [loadingThread, setLoadingThread] = useState(false);
  
  useEffect(() => {
    let isCancelled = false;

    const fetchReplies = async () => {
      try {
        const response = await api.get("/replies/");
        if (!isCancelled) {
          setReplies(response.data);
        }
      } catch (error) {
        console.error("Failed to fetch replies:", error);
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };

    void fetchReplies();

    return () => {
      isCancelled = true;
    };
  }, []);

  const handleReply = (reply: Reply) => {
    if (!reply.lead?.email) {
      alert("No email found for this lead.");
      return;
    }
    const subject = `Re: ${reply.message.substring(0, 50)}...`;
    const mailto = `mailto:${reply.lead.email}?subject=${encodeURIComponent(subject)}`;
    window.location.href = mailto;
  };

  const handleViewThread = async (reply: Reply) => {
    if (!reply.lead_id) return;
    
    setLoadingThread(true);
    setIsThreadOpen(true);
    try {
      const response = await api.get(`/leads/${reply.lead_id}/thread`);
      setSelectedThread(response.data.thread);
      setSelectedLead(response.data.lead);
    } catch (error) {
      console.error("Failed to fetch thread:", error);
      alert("Failed to load thread.");
    } finally {
      setLoadingThread(false);
    }
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

      {/* Thread Dialog */}
      <Dialog open={isThreadOpen} onOpenChange={setIsThreadOpen}>
        <DialogContent className="sm:max-w-2xl max-h-[80vh] flex flex-col p-0 overflow-hidden">
          <DialogHeader className="p-6 border-b bg-card">
            <DialogTitle className="flex items-center gap-2">
              <Mail className="w-5 h-5 text-primary" />
              Conversation with {selectedLead ? `${selectedLead.first_name} ${selectedLead.last_name}` : "Lead"}
            </DialogTitle>
            <DialogDescription>
              Full outreach and reply history for {selectedLead?.company}
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-muted/30">
            {loadingThread ? (
              <div className="flex items-center justify-center h-40 text-muted-foreground">
                <Clock className="w-5 h-5 animate-spin mr-2" />
                Loading conversation...
              </div>
            ) : selectedThread.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                No messages found in this thread.
              </div>
            ) : (
              selectedThread.map((item, index) => (
                <div key={index} className={cn(
                  "flex flex-col gap-2 max-w-[85%]",
                  item.type === "sent" ? "ml-auto items-end" : "mr-auto items-start"
                )}>
                  <div className="flex items-center gap-2 text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">
                    <span>{formatDistanceToNow(new Date(item.timestamp))} ago</span>
                    {item.type === "sent" && (
                      <Badge variant="outline" className="px-1 py-0 text-[9px] h-4">
                        {item.status}
                      </Badge>
                    )}
                  </div>
                  <div className={cn(
                    "p-4 rounded-2xl text-sm leading-relaxed",
                    item.type === "sent" 
                      ? "bg-primary text-primary-foreground rounded-tr-none shadow-lg shadow-primary/10" 
                      : "bg-card border border-border/50 rounded-tl-none shadow-sm"
                  )}>
                    {item.type === "received" && (
                      <div className="flex items-center gap-1.5 mb-2">
                        <Badge className={cn("text-[9px] px-1.5 py-0 h-4", getClassificationConfig(item.classification!).color)}>
                          {item.classification?.replace("_", " ")}
                        </Badge>
                      </div>
                    )}
                    <div className="whitespace-pre-wrap">{item.content}</div>
                  </div>
                </div>
              ))
            )}
          </div>
          
          <div className="p-4 border-t bg-card flex justify-end">
            <button 
              onClick={() => setIsThreadOpen(false)}
              className="text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Close
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
