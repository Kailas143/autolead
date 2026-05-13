"use client";

import React, { useState } from "react";
import { Plus, Trash2, Clock, Sparkles, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { useRouter } from "next/navigation";

interface SequenceStep {
  id: string;
  subject: string;
  body: string;
  delay: number;
}

export default function SequenceBuilder() {
  const router = useRouter();
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
      delay: 0 
    },
  ]);
  const [industry, setIndustry] = useState<string>("All Industries");
  const [title, setTitle] = useState<string>("");
  const [scheduledFor, setScheduledFor] = useState<string>("");
  const [dailySendLimit, setDailySendLimit] = useState<number>(50);
  const [restrictSendingHours, setRestrictSendingHours] = useState(false);
  const [sendWindowStartHour, setSendWindowStartHour] = useState<number>(9);
  const [sendWindowEndHour, setSendWindowEndHour] = useState<number>(17);
  const [isLaunching, setIsLaunching] = useState(false);

  const addStep = () => {
    const newStep = {
      id: Math.random().toString(36).substr(2, 9),
      subject: "Follow up: {company}",
      body: "Hi {first_name},\n\nJust wanted to follow up on my previous email...",
      delay: 3,
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
      alert("Please enter a campaign name");
      return;
    }

    try {
      setIsLaunching(true);
      const payload = {
        name: title,
        target_industry: industry === "All Industries" ? null : industry,
        scheduled_for: scheduledFor ? new Date(scheduledFor).toISOString() : null,
        daily_send_limit: Math.max(1, dailySendLimit || 1),
        send_window_start_hour: restrictSendingHours ? Math.max(0, Math.min(23, sendWindowStartHour || 0)) : 0,
        send_window_end_hour: restrictSendingHours ? Math.max(0, Math.min(23, sendWindowEndHour || 0)) : 0,
        sequences: steps.map((s, index) => ({
          step_number: index + 1,
          subject: s.subject,
          body: s.body,
          delay_days: s.delay
        }))
      };

      const response = await api.post("/campaigns/", payload);
      console.log("Campaign created:", response.data);

      // Now launch it
      await api.post(`/campaigns/${response.data.id}/launch`);

      alert(scheduledFor ? "Campaign scheduled successfully!" : "Campaign launched successfully!");
      router.push("/dashboard");
    } catch (error) {
      console.error("Failed to launch campaign:", error);
      alert("Failed to launch campaign. Please check backend logs.");
    } finally {
      setIsLaunching(false);
    }
  };

  const handleGenerateAI = async (id: string) => {
    try {
      updateStep(id, "body", "Generating professional follow-up...");
      
      const leadData = {
        first_name: "{first_name}",
        company: "{company}",
        industry: industry === "All Industries" ? "consultancy" : industry,
      };

      const response = await api.post("/ai/generate-followup", { lead_data: leadData });
      updateStep(id, "body", response.data.content);
    } catch (error) {
      console.error("Failed to generate AI follow-up:", error);
      alert("Failed to generate AI content. Using default.");
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
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Industry Target</label>
            <div className="relative group">
              <select
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="w-full h-12 bg-black/20 border border-white/10 rounded-xl px-4 text-sm appearance-none focus:outline-none focus:border-primary/50 transition-all cursor-pointer"
              >
                <option>All Industries</option>
                <option>SaaS</option>
                <option>Healthcare</option>
                <option>Clinic</option>
                <option>Education</option>
                <option>Real Estate</option>
                <option>Logistics</option>
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground">
                <ChevronDown className="w-4 h-4" />
              </div>
            </div>
          </div>
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
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Sender Profile</label>
            <div className="h-12 flex items-center px-4 bg-black/20 border border-white/10 rounded-xl text-sm text-white/70">
              hello@aurvyz.com
            </div>
          </div>
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
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Start Time</label>
            <Input
              type="datetime-local"
              value={scheduledFor}
              onChange={(e) => setScheduledFor(e.target.value)}
              className="bg-black/20 border-white/10 h-12"
            />
            <p className="text-xs text-muted-foreground">Leave blank to launch immediately. Uses your local browser time.</p>
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
                <div className="grid grid-cols-2 gap-3">
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
                <p className="text-xs text-muted-foreground">24-hour clock in campaign timezone. Example: 9 to 17 sends between 9 AM and 5 PM.</p>
              </>
            )}
          </div>
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
                {index > 0 && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground ml-4 bg-white/5 px-3 py-1 rounded-lg border border-white/5 group-hover:border-primary/30 transition-all">
                    <Clock className="w-3.5 h-3.5 text-primary" />
                    <span className="whitespace-nowrap">Wait</span>
                    <input 
                      type="number" 
                      min="1"
                      max="30"
                      value={step.delay}
                      onChange={(e) => updateStep(step.id, "delay", parseInt(e.target.value) || 1)}
                      className="w-10 bg-black/40 border-none text-white text-center font-bold focus:ring-0 cursor-pointer hover:text-primary transition-colors"
                    />
                    <span className="whitespace-nowrap">days</span>
                  </div>
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
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Subject Line</label>
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
                  <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Email Body</label>
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
