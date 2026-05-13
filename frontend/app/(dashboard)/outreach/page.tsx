"use client";

import { useEffect, useMemo, useState } from "react";
import { format, formatDistanceToNow } from "date-fns";
import { ArrowDownAZ, ArrowUpAZ, Clock3, Loader2, Mail, Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import api from "@/lib/api";
import { cn } from "@/lib/utils";

interface SentMessage {
  id: number;
  customer_name: string;
  customer_email: string;
  company: string;
  industry: string;
  subject: string;
  body_preview: string;
  sent_at: string;
  campaign_name: string;
  sequence_step: number;
  status: "sent" | "opened" | "replied";
}

interface SentMessagesResponse {
  summary: {
    total_messages: number;
    total_customers: number;
    latest_sent_at: string | null;
  };
  messages: SentMessage[];
}

type SortOption = "newest" | "oldest" | "az" | "za";

const sortOptions: Array<{
  value: SortOption;
  label: string;
  icon: typeof Clock3;
}> = [
  { value: "newest", label: "Newest first", icon: Clock3 },
  { value: "oldest", label: "Oldest first", icon: Clock3 },
  { value: "az", label: "A to Z", icon: ArrowDownAZ },
  { value: "za", label: "Z to A", icon: ArrowUpAZ },
];

const statusClasses: Record<SentMessage["status"], string> = {
  sent: "bg-sky-500/10 text-sky-400 border-sky-400/20",
  opened: "bg-amber-500/10 text-amber-400 border-amber-400/20",
  replied: "bg-emerald-500/10 text-emerald-400 border-emerald-400/20",
};

export default function OutreachPage() {
  const [data, setData] = useState<SentMessagesResponse>({
    summary: {
      total_messages: 0,
      total_customers: 0,
      latest_sent_at: null,
    },
    messages: [],
  });
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<SortOption>("newest");

  useEffect(() => {
    let isCancelled = false;

    const fetchSentMessages = async () => {
      try {
        const response = await api.get("/analytics/sent-messages");
        if (!isCancelled) {
          setData(response.data);
        }
      } catch (error) {
        console.error("Failed to fetch sent messages:", error);
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };

    void fetchSentMessages();

    return () => {
      isCancelled = true;
    };
  }, []);

  const filteredMessages = useMemo(() => {
    const query = search.trim().toLowerCase();
    const filtered = data.messages.filter((message) => {
      if (!query) return true;

      return [
        message.customer_name,
        message.customer_email,
        message.company,
        message.subject,
        message.campaign_name,
      ].some((value) => value?.toLowerCase().includes(query));
    });

    const sorted = [...filtered];
    sorted.sort((a, b) => {
      if (sortBy === "newest") {
        return new Date(b.sent_at).getTime() - new Date(a.sent_at).getTime();
      }
      if (sortBy === "oldest") {
        return new Date(a.sent_at).getTime() - new Date(b.sent_at).getTime();
      }
      const nameCompare = a.customer_name.localeCompare(b.customer_name);
      return sortBy === "az" ? nameCompare : nameCompare * -1;
    });

    return sorted;
  }, [data.messages, search, sortBy]);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Sent Messages</h1>
          <p className="mt-1 text-muted-foreground">
            Browse every outreach email with customer names, send times, and quick search.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Card className="min-w-36 border-white/5 bg-white/5 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Messages</div>
              <div className="mt-2 text-2xl font-bold text-white">{data.summary.total_messages}</div>
            </CardContent>
          </Card>
          <Card className="min-w-36 border-white/5 bg-white/5 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Customers</div>
              <div className="mt-2 text-2xl font-bold text-white">{data.summary.total_customers}</div>
            </CardContent>
          </Card>
          <Card className="min-w-48 border-white/5 bg-white/5 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Latest send</div>
              <div className="mt-2 text-sm font-semibold text-white">
                {data.summary.latest_sent_at
                  ? format(new Date(data.summary.latest_sent_at), "MMM d, h:mm a")
                  : "No messages yet"}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card className="overflow-hidden border-white/5 bg-white/5 backdrop-blur-sm">
        <CardHeader className="gap-4 border-b border-white/5 bg-white/[0.02]">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <CardTitle className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
              Message History
            </CardTitle>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <div className="relative w-full sm:w-80">
                <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search customer, company, subject..."
                  className="h-10 border-white/10 bg-black/20 pl-9 text-sm"
                />
              </div>
              <select
                value={sortBy}
                onChange={(event) => setSortBy(event.target.value as SortOption)}
                className="h-10 rounded-lg border border-white/10 bg-black/30 px-3 text-sm text-white outline-none transition focus:border-white/30"
                aria-label="Sort sent messages"
              >
                {sortOptions.map((option) => (
                  <option key={option.value} value={option.value} className="bg-[#101010] text-white">
                    Sort: {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-20">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : filteredMessages.length === 0 ? (
            <div className="px-6 py-20 text-center text-muted-foreground">
              No sent messages match your current search.
            </div>
          ) : (
            <>
              <div className="hidden md:block">
                <Table>
                  <TableHeader className="bg-white/[0.01]">
                    <TableRow className="border-white/5 hover:bg-transparent">
                      <TableHead className="text-muted-foreground">Customer</TableHead>
                      <TableHead className="text-muted-foreground">Campaign</TableHead>
                      <TableHead className="text-muted-foreground">Subject</TableHead>
                      <TableHead className="text-muted-foreground">Status</TableHead>
                      <TableHead className="text-right text-muted-foreground">Sent time</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredMessages.map((message) => (
                      <TableRow
                        key={message.id}
                        className="border-white/5 transition-colors hover:bg-white/[0.02]"
                      >
                        <TableCell className="whitespace-normal">
                          <div className="font-medium text-white">{message.customer_name}</div>
                          <div className="text-xs text-muted-foreground">{message.customer_email}</div>
                          <div className="mt-1 text-[11px] uppercase tracking-[0.2em] text-muted-foreground/80">
                            {message.company}
                          </div>
                        </TableCell>
                        <TableCell className="whitespace-normal">
                          <div className="text-sm text-white/85">{message.campaign_name}</div>
                          <div className="text-xs text-muted-foreground">Step {message.sequence_step}</div>
                        </TableCell>
                        <TableCell className="max-w-sm whitespace-normal">
                          <div className="font-medium text-white/90">{message.subject}</div>
                          <div className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">
                            {message.body_preview}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={cn("capitalize border px-2.5", statusClasses[message.status])}>
                            {message.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right whitespace-normal">
                          <div className="text-sm text-white/80">
                            {format(new Date(message.sent_at), "MMM d, yyyy")}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {format(new Date(message.sent_at), "h:mm a")}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="grid gap-4 p-4 md:hidden">
                {filteredMessages.map((message) => (
                  <Card key={message.id} className="border-white/8 bg-black/20 backdrop-blur-sm">
                    <CardContent className="space-y-4 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="font-semibold text-white">{message.customer_name}</div>
                          <div className="text-xs text-muted-foreground">{message.customer_email}</div>
                          <div className="mt-1 text-[11px] uppercase tracking-[0.2em] text-muted-foreground/80">
                            {message.company}
                          </div>
                        </div>
                        <Badge className={cn("capitalize border px-2.5", statusClasses[message.status])}>
                          {message.status}
                        </Badge>
                      </div>

                      <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-3">
                        <div className="text-sm font-medium text-white/90">{message.subject}</div>
                        <div className="mt-2 text-xs leading-5 text-muted-foreground">{message.body_preview}</div>
                      </div>

                      <div className="flex items-center justify-between gap-4 text-xs text-muted-foreground">
                        <div className="flex items-center gap-2">
                          <Mail className="h-4 w-4 text-primary" />
                          <span>{message.campaign_name}</span>
                        </div>
                        <span>Step {message.sequence_step}</span>
                      </div>

                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{format(new Date(message.sent_at), "MMM d, yyyy")}</span>
                        <span>{formatDistanceToNow(new Date(message.sent_at))} ago</span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
