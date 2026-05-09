import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, BarChart3, Mail, Zap, Target } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-black text-white selection:bg-primary/30">
      {/* Navigation */}
      <header className="px-6 lg:px-12 h-20 flex items-center border-b border-white/10 backdrop-blur-md sticky top-0 z-50 bg-black/50">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center group-hover:rotate-6 transition-transform">
            <Zap className="w-6 h-6 text-black fill-current" />
          </div>
          <span className="text-2xl font-bold tracking-tighter">Aurvyz</span>
        </Link>
        <nav className="ml-auto flex gap-4 sm:gap-6">
          <Link href="/login">
            <Button variant="ghost" className="text-zinc-400 hover:text-white hover:bg-white/10">
              Sign In
            </Button>
          </Link>
          <Link href="/register">
            <Button className="bg-white text-black hover:bg-zinc-200">
              Get Started
            </Button>
          </Link>
        </nav>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative py-24 lg:py-32 overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(120,119,198,0.3),rgba(0,0,0,0))]"></div>
          <div className="container px-4 md:px-6 mx-auto text-center relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 text-zinc-400 text-sm mb-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              AI-Powered Outreach for Modern Teams
            </div>
            <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-8 leading-[1.1]">
              Automate your outreach <br />
              <span className="text-zinc-500">with surgical precision.</span>
            </h1>
            <p className="max-w-[700px] mx-auto text-zinc-400 text-lg md:text-xl mb-12 leading-relaxed">
              Aurvyz uses Gemini 2.5 Flash to generate hyper-personalized cold emails, 
              track engagement, and handle follow-ups automatically.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/register">
                <Button size="lg" className="h-14 px-8 text-lg bg-white text-black hover:bg-zinc-200 gap-2">
                  Start Free Campaign <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="h-14 px-8 text-lg border-white/10 hover:bg-white/5 text-white">
                  Live Demo
                </Button>
              </Link>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-24 border-t border-white/5 bg-zinc-950/50">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
              <div className="flex flex-col gap-4 p-8 rounded-3xl border border-white/5 bg-black hover:border-primary/50 transition-colors group">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Target className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold">Lead Enrichment</h3>
                <p className="text-zinc-500 leading-relaxed">
                  Import Apollo CSVs and let our AI enrich your data with deep insights into every lead.
                </p>
              </div>
              <div className="flex flex-col gap-4 p-8 rounded-3xl border border-white/5 bg-black hover:border-primary/50 transition-colors group">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Mail className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold">AI Personalization</h3>
                <p className="text-zinc-500 leading-relaxed">
                  Generate unique opening lines and body text based on lead behavior and company data.
                </p>
              </div>
              <div className="flex flex-col gap-4 p-8 rounded-3xl border border-white/5 bg-black hover:border-primary/50 transition-colors group">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <BarChart3 className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold">Smart Tracking</h3>
                <p className="text-zinc-500 leading-relaxed">
                  Real-time analytics on opens, replies, and sentiment analysis for every campaign.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="py-12 border-t border-white/5 text-center text-zinc-600">
        <p>© 2026 Aurvyz. Built for high-performance outreach.</p>
      </footer>
    </div>
  );
}
