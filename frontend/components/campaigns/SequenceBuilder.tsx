"use client";

import React, { useState } from "react";
import { Plus, Trash2, Clock, Sparkles, Paperclip, X, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

interface SequenceStep {
  id: string;
  subject: string;
  body: string;
  delayDays: number;
  delayMinutes: number;
  mediatype?: string;
  mimetype?: string;
  media?: string;
  fileName?: string;
  pollQuestion?: string;
  pollOptions?: string[];
}

type CampaignChannel = "email" | "whatsapp";

const INDUSTRY_OPTIONS = [
  "SaaS",
  "Healthcare",
  "Health Care",
  "Hospital",
  "Care",
  "Clinic",
  "Education",
  "Real Estate",
  "Logistics",
  "Supermarket",
];

export default function SequenceBuilder() {
  const router = useRouter();
  const [channel, setChannel] = useState<CampaignChannel>("email");
  const [steps, setSteps] = useState<SequenceStep[]>([
    {
      id: "1",
      subject: "Struggling with {industry} manual workflows?",
      body: `Hi {first_name},

Hope you’re doing well.

I came across {company} while researching study abroad consultancies and noticed how much coordination these workflows usually involve — student follow-ups, document tracking, counselor communication, appointments, and application stages.

At Aurvyz, we’re currently building intelligent systems designed to simplify and automate operational workflows for consultancies and service businesses.

As part of our research and product exploration, we created a lightweight prototype around consultancy workflow automation — focused on improving visibility, reducing manual follow-ups, and organizing student operations more efficiently.

A few areas we explored:
• Student inquiry & lead tracking
• Application stage management
• Follow-up reminders & workflow automation
• Centralized student dashboard
• Internal coordination workflows

Would be happy to share the prototype with you and hear your thoughts from a real consultancy perspective.

Please go through this link : https://aurvyz.com/

No sales pressure — just looking to connect and exchange ideas around operational efficiency in this space.

Best regards,
Sreekailas v.s
📩 hello@aurvyz.com
🌐 www.aurvyz.com`,
      delayDays: 0,
      delayMinutes: 0,
    },
  ]);
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);
  const [title, setTitle] = useState<string>("");
  const [whatsappInstanceName, setWhatsappInstanceName] = useState<string>("supermarket_campaign");
  const [scheduledFor, setScheduledFor] = useState<string>("");
  const [dailySendLimit, setDailySendLimit] = useState<number>(50);
  const [restrictSendingHours, setRestrictSendingHours] = useState(false);
  const [sendWindowStartHour, setSendWindowStartHour] = useState<number>(9);
  const [sendWindowEndHour, setSendWindowEndHour] = useState<number>(17);
  const [campaignType, setCampaignType] = useState<"drip" | "broadcast">("drip");
  const [isLaunching, setIsLaunching] = useState(false);

  const addStep = () => {
    const newStep = {
      id: Math.random().toString(36).substr(2, 9),
      subject: channel === "whatsapp" ? "WhatsApp Follow-up" : "Follow up: {company}",
      body: channel === "whatsapp"
        ? "Hi {first_name},\n\nJust following up on my previous message about {company}."
        : "Hi {first_name},\n\nJust wanted to follow up on my previous email...",
      delayDays: 0,
      delayMinutes: 2,
    };
    setSteps([...steps, newStep]);
  };

  const removeStep = (id: string) => {
    setSteps(steps.filter((s) => s.id !== id));
  };

  const updateStep = (id: string, field: keyof SequenceStep, value: string | number) => {
    setSteps(steps.map(s => s.id === id ? { ...s, [field]: value } : s));
  };

  const handleLaunch = async () => {
    if (!title) {
      toast.error("Please enter a campaign name");
      return;
    }

    if (channel === "whatsapp" && !whatsappInstanceName.trim()) {
      toast.error("Please enter your connected Evolution instance name");
      return;
    }

    try {
      setIsLaunching(true);
      const industryValue = selectedIndustries.length > 0 ? selectedIndustries.join(", ") : null;
      const payload = {
        name: title,
        channel,
        evolution_instance_name: channel === "whatsapp" ? whatsappInstanceName.trim() : null,
        target_industry: industryValue,
        scheduled_for: scheduledFor ? new Date(scheduledFor).toISOString() : null,
        daily_send_limit: campaignType === "broadcast" ? 99999 : Math.max(1, dailySendLimit || 1),
        send_window_start_hour: campaignType === "broadcast" ? 0 : (restrictSendingHours ? Math.max(0, Math.min(23, sendWindowStartHour || 0)) : 0),
        send_window_end_hour: campaignType === "broadcast" ? 0 : (restrictSendingHours ? Math.max(0, Math.min(23, sendWindowEndHour || 0)) : 0),
        sequences: steps.map((s, index) => ({
          step_number: index + 1,
          subject: s.subject,
          body: s.body,
          delay_days: campaignType === "broadcast" ? 0 : s.delayDays,
          delay_minutes: campaignType === "broadcast" ? 0 : s.delayMinutes,
          mediatype: s.mediatype,
          mimetype: s.mimetype,
          media: s.media,
          poll_question: s.pollQuestion,
          poll_options: s.pollOptions?.filter(opt => opt.trim() !== "") || null,
        }))
      };

      const response = await api.post("/campaigns/", payload);
      console.log("Campaign created:", response.data);

      // Now launch it
      await api.post(`/campaigns/${response.data.id}/launch`);

      toast.success(scheduledFor ? "Campaign scheduled successfully!" : "Campaign launched successfully!");
      router.push("/dashboard");
    } catch (error) {
      console.error("Failed to launch campaign:", error);
      toast.error("Failed to launch campaign. Please check backend logs.");
    } finally {
      setIsLaunching(false);
    }
  };

  const handleFileUpload = (id: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      toast.error("File size must be less than 5MB");
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const base64String = (event.target?.result as string).split(',')[1];
      let mediatype = "document";
      if (file.type.startsWith("image/")) mediatype = "image";
      else if (file.type.startsWith("video/")) mediatype = "video";
      else if (file.type.startsWith("audio/")) mediatype = "audio";

      setSteps(steps.map(s => s.id === id ? {
        ...s,
        mediatype,
        mimetype: file.type,
        media: base64String,
        fileName: file.name
      } : s));
    };
    reader.readAsDataURL(file);
  };

  const handleGenerateAI = async (id: string) => {
    try {
      updateStep(id, "body", "Generating professional follow-up...");
      const industryValue = selectedIndustries.length > 0 ? selectedIndustries.join(", ") : "consultancy";

      const leadData = {
        first_name: "{first_name}",
        company: "{company}",
        industry: industryValue,
      };

      const response = await api.post("/ai/generate-followup", { lead_data: leadData });
      updateStep(id, "body", response.data.content);
    } catch (error) {
      console.error("Failed to generate AI follow-up:", error);
      toast.error("Failed to generate AI content. Using default.");
      updateStep(id, "body", "Hi {first_name},\n\nJust wanted to follow up on my previous email...");
    }
  };

  return (
    <div className="space-y-6">
      {/* Campaign Settings */}
      <Card className="border-white/5 bg-white/5 backdrop-blur-sm p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Campaign Name</label>
            <Input
              placeholder="e.g., Study Abroad Outreach Q2"
              className="bg-black/20 border-white/10 h-12"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Channel</label>
            <select
              value={channel}
              onChange={(e) => setChannel(e.target.value as CampaignChannel)}
              className="w-full h-12 bg-black/20 border border-white/10 rounded-xl px-4 text-sm focus:outline-none focus:border-primary/50 transition-all"
            >
              <option value="email">Email</option>
              <option value="whatsapp">WhatsApp</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Industry Target</label>
            <select
              multiple
              value={selectedIndustries}
              onChange={(e) => setSelectedIndustries(Array.from(e.target.selectedOptions, (option) => option.value))}
              className="w-full min-h-[9rem] bg-black/20 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-primary/50 transition-all"
            >
              {INDUSTRY_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <p className="text-xs text-muted-foreground">
              Hold Ctrl or Cmd to select multiple industries. Leave empty to target all industries.
            </p>
          </div>
          {channel === "whatsapp" && (
            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Evolution Instance</label>
              <Input
                placeholder="supermarket_campaign"
                className="bg-black/20 border-white/10 h-12"
                value={whatsappInstanceName}
                onChange={(e) => setWhatsappInstanceName(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Use the connected Evolution API instance name that should send this campaign.
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Advanced Settings */}
      <Card className="border-white/5 bg-white/5 backdrop-blur-sm p-6 mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-4 h-4 text-primary" />
          <h3 className="text-sm font-semibold text-white uppercase tracking-widest">Advanced Settings</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Campaign Mode</label>
            <div className="flex gap-2 p-1 bg-black/20 rounded-xl border border-white/10">
              <button
                className={`flex-1 py-2 text-sm font-medium rounded-lg transition-colors ${campaignType === "drip" ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:text-white"}`}
                onClick={() => setCampaignType("drip")}
              >
                Drip Sequence
              </button>
              <button
                className={`flex-1 py-2 text-sm font-medium rounded-lg transition-colors ${campaignType === "broadcast" ? "bg-destructive text-destructive-foreground shadow-sm" : "text-muted-foreground hover:text-white"}`}
                onClick={() => setCampaignType("broadcast")}
              >
                Broadcast Blast
              </button>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Sender Profile</label>
            <div className="h-12 flex items-center px-4 bg-black/20 border border-white/10 rounded-xl text-sm text-white/70">
              {channel === "whatsapp" ? whatsappInstanceName || "Evolution instance" : "hello@aurvyz.com"}
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Start Time</label>
            <Input
              type="datetime-local"
              value={scheduledFor}
              onChange={(e) => setScheduledFor(e.target.value)}
              className="bg-black/20 border-white/10 h-12"
            />
            <p className="text-xs text-muted-foreground">Leave blank to launch immediately. Uses your local browser time.</p>
          </div>

          {campaignType === "broadcast" ? (
            <div className="col-span-1 md:col-span-2 mt-2">
              <div className="flex items-start gap-3 bg-destructive/10 border border-destructive/20 rounded-xl p-4">
                <AlertTriangle className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
                <div className="flex flex-col">
                  <span className="text-sm font-bold text-destructive">High Risk of Ban</span>
                  <span className="text-xs text-destructive/80 mt-1">Broadcast mode sends all messages immediately without delays or daily limits. This has an extremely high risk of getting your WhatsApp number banned for spam by Meta. Ensure your contacts have opted in.</span>
                </div>
              </div>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Daily Send Limit</label>
                <Input
                  type="number"
                  min="1"
                  value={dailySendLimit}
                  onChange={(e) => setDailySendLimit(parseInt(e.target.value, 10) || 1)}
                  className="bg-black/20 border-white/10 h-12"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Sending Hours</label>
                <label className="flex items-center gap-3 rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white/80">
                  <input
                    type="checkbox"
                    checked={restrictSendingHours}
                    onChange={(e) => setRestrictSendingHours(e.target.checked)}
                    className="h-4 w-4 rounded border-white/20 bg-transparent"
                  />
                  <span>Restrict sending hours</span>
                </label>
                {restrictSendingHours && (
                  <>
                    <div className="grid grid-cols-2 gap-3 mt-3">
                      <Input
                        type="number"
                        min="0"
                        max="23"
                        value={sendWindowStartHour}
                        onChange={(e) => setSendWindowStartHour(parseInt(e.target.value, 10) || 0)}
                        className="bg-black/20 border-white/10 h-12"
                        placeholder="Start hour"
                      />
                      <Input
                        type="number"
                        min="0"
                        max="23"
                        value={sendWindowEndHour}
                        onChange={(e) => setSendWindowEndHour(parseInt(e.target.value, 10) || 0)}
                        className="bg-black/20 border-white/10 h-12"
                        placeholder="End hour"
                      />
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">24-hour clock in campaign timezone. Example: 9 to 17 sends between 9 AM and 5 PM.</p>
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </Card>

      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-white flex items-center gap-3">
          Sequence Flow
          <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 rounded-lg px-3">
            {steps.length} Steps
          </Badge>
        </h2>
        <Button onClick={addStep} variant="outline" className="gap-2 rounded-xl border-white/10 hover:bg-white/5">
          <Plus className="w-4 h-4" /> Add Step
        </Button>
      </div>

      <div className="space-y-4">
        {steps.map((step, index) => (
          <Card key={step.id} className="border-white/5 bg-white/5 backdrop-blur-sm overflow-hidden group">
            <div className="bg-white/5 px-6 py-3 flex justify-between items-center border-b border-white/5">
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold">
                  {index + 1}
                </span>
                <span className="text-sm font-medium text-white">Step {index + 1}</span>
                {index > 0 && campaignType === "drip" && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground ml-4 bg-white/5 px-3 py-1 rounded-lg border border-white/5 group-hover:border-primary/30 transition-all">
                    <Clock className="w-3.5 h-3.5 text-primary" />
                    <span className="whitespace-nowrap">Wait</span>
                    <input
                      type="number"
                      min="0"
                      max="30"
                      value={step.delayDays}
                      onChange={(e) => updateStep(step.id, "delayDays", parseInt(e.target.value, 10) || 0)}
                      className="w-10 bg-black/40 border-none text-white text-center font-bold focus:ring-0 cursor-pointer hover:text-primary transition-colors"
                    />
                    <span className="whitespace-nowrap">days</span>
                    <input
                      type="number"
                      min="0"
                      max="1440"
                      value={step.delayMinutes}
                      onChange={(e) => updateStep(step.id, "delayMinutes", parseInt(e.target.value, 10) || 0)}
                      className="w-14 bg-black/40 border-none text-white text-center font-bold focus:ring-0 cursor-pointer hover:text-primary transition-colors"
                    />
                    <span className="whitespace-nowrap">min</span>
                  </div>
                )}
                {index > 0 && campaignType === "broadcast" && (
                  <Badge variant="outline" className="ml-4 bg-destructive/10 text-destructive border-destructive/20 rounded-md">
                    Sends Immediately
                  </Badge>
                )}
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => removeStep(step.id)}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
            <CardContent className="p-6 space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {channel === "whatsapp" ? "Step Label" : "Subject Line"}
                </label>
                <div className="relative">
                  <Input
                    value={step.subject}
                    onChange={(e) => updateStep(step.id, "subject", e.target.value)}
                    className="bg-black/20 border-white/10 focus:border-primary/50"
                  />
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex gap-2">
                    <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-500 border-emerald-500/20">AI Optimized</Badge>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {channel === "whatsapp" ? "WhatsApp Message" : "Email Body"}
                  </label>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 text-primary hover:text-primary hover:bg-primary/10 gap-2"
                    onClick={() => handleGenerateAI(step.id)}
                  >
                    <Sparkles className="w-3 h-3" />
                    AI Generate
                  </Button>
                </div>
                <textarea
                  className="w-full min-h-[150px] bg-black/20 border border-white/10 rounded-xl p-4 text-sm text-white focus:outline-none focus:border-primary/50 transition-colors custom-scrollbar"
                  value={step.body}
                  onChange={(e) => updateStep(step.id, "body", e.target.value)}
                />
              </div>

              <div className="flex flex-wrap gap-2 pt-2">
                {["{first_name}", "{company}", "{title}", "{personalization}"].map((tag) => (
                  <button
                    key={tag}
                    onClick={() => {
                      const newBody = step.body + " " + tag;
                      updateStep(step.id, "body", newBody);
                    }}
                    className="px-2 py-1 rounded-md bg-white/5 border border-white/10 text-[10px] font-mono text-muted-foreground hover:text-white hover:border-white/20 transition-all"
                  >
                    {tag}
                  </button>
                ))}
              </div>

              {channel === "whatsapp" && (
                <div className="pt-4 border-t border-white/5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Attachment (Optional)
                    </label>
                  </div>
                  {step.fileName ? (
                    <div className="mt-3 flex items-center justify-between bg-white/[0.02] hover:bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3 transition-colors group/attach">
                      <div className="flex items-center gap-4 overflow-hidden">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20">
                          <Paperclip className="w-4 h-4 text-primary" />
                        </div>
                        <div className="flex flex-col">
                          <span className="text-sm font-medium text-white truncate">{step.fileName}</span>
                          <span className="text-xs text-muted-foreground">Ready to send</span>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:bg-destructive/10 hover:text-destructive shrink-0 opacity-0 group-hover/attach:opacity-100 transition-opacity"
                        onClick={() => {
                          setSteps(steps.map(s => s.id === step.id ? { ...s, mediatype: undefined, mimetype: undefined, media: undefined, fileName: undefined } : s));
                        }}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ) : (
                    <div className="mt-3 relative group/upload">
                      <input
                        type="file"
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                        onChange={(e) => handleFileUpload(step.id, e)}
                        accept="image/*,video/*,audio/*,application/pdf,.doc,.docx,.xls,.xlsx"
                      />
                      <div className="flex flex-col items-center justify-center gap-3 w-full border-2 border-dashed border-white/10 bg-white/[0.02] group-hover/upload:bg-primary/[0.02] group-hover/upload:border-primary/30 rounded-xl py-8 transition-all duration-300">
                        <div className="h-12 w-12 rounded-full bg-white/5 group-hover/upload:bg-primary/10 group-hover/upload:scale-110 flex items-center justify-center transition-all duration-300 border border-white/5 group-hover/upload:border-primary/20">
                          <Paperclip className="w-5 h-5 text-muted-foreground group-hover/upload:text-primary transition-colors" />
                        </div>
                        <div className="flex flex-col items-center gap-1">
                          <span className="text-sm font-medium text-white group-hover/upload:text-primary transition-colors">Click to attach media</span>
                          <span className="text-xs text-muted-foreground">JPG, PNG, PDF, MP4 up to 5MB</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {channel === "whatsapp" && (
                <div className="pt-4 border-t border-white/5 space-y-4">
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Interactive Poll (Optional)
                    </label>
                    <span className="text-[10px] text-muted-foreground">Add a poll for quick replies (e.g. Yes / No)</span>
                  </div>

                  <Input
                    placeholder="Poll Question (e.g., Are you interested?)"
                    value={step.pollQuestion || ""}
                    onChange={(e) => updateStep(step.id, "pollQuestion", e.target.value)}
                    className="bg-black/20 border-white/10"
                  />

                  {step.pollQuestion && (
                    <div className="space-y-2 pl-4 border-l-2 border-white/10">
                      {[0, 1, 2].map((optIndex) => (
                        <div key={optIndex} className="flex gap-2 items-center">
                          <div className="w-4 h-4 rounded-full border border-white/20 flex items-center justify-center bg-black/40 text-[8px] text-white/50">{optIndex + 1}</div>
                          <Input
                            placeholder={`Option ${optIndex + 1}`}
                            value={step.pollOptions?.[optIndex] || ""}
                            onChange={(e) => {
                              const newOptions = [...(step.pollOptions || ["", "", ""])];
                              newOptions[optIndex] = e.target.value;
                              updateStep(step.id, "pollOptions", newOptions as any);
                            }}
                            className="bg-black/20 border-white/10 h-9 text-sm"
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex justify-end gap-4 pt-6">
        <Button variant="outline" className="rounded-xl border-white/10">Save Draft</Button>
        <Button
          onClick={handleLaunch}
          disabled={isLaunching}
          className="px-8 shadow-lg shadow-primary/20 rounded-xl h-11"
        >
          {isLaunching ? (scheduledFor ? "Scheduling..." : "Launching...") : (scheduledFor ? "Schedule Campaign" : "Launch Campaign")}
        </Button>
      </div>
    </div>
  );
}
