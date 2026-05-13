"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  Bell,
  LayoutDashboard,
  LogOut,
  Mail,
  Menu,
  Send,
  Settings,
  ShieldCheck,
  Users,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";

const sidebarItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Leads", href: "/leads", icon: Users },
  { name: "Campaigns", href: "/campaigns", icon: Send },
  { name: "Sent Messages", href: "/outreach", icon: Mail },
  { name: "Inbox", href: "/inbox", icon: Mail },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Admin Console", href: "/admin", icon: ShieldCheck },
  { name: "Settings", href: "/settings", icon: Settings },
];

function SidebarContent({
  pathname,
  onNavigate,
  onLogout,
}: {
  pathname: string;
  onNavigate?: () => void;
  onLogout: () => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="p-6 sm:p-8">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/20">
            <span className="text-xl font-bold text-white">A</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Aurvyz</h1>
            <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Outreach OS</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-4 pb-4">
        {sidebarItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "group flex items-center gap-3 rounded-xl px-4 py-3 transition-all duration-200",
                isActive
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                  : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
              )}
            >
              <item.icon className={cn("h-5 w-5", isActive ? "text-white" : "group-hover:text-foreground")} />
              <span className="font-medium">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/5 p-4">
        <button
          onClick={onLogout}
          className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-muted-foreground transition-all duration-200 hover:bg-destructive/10 hover:text-destructive"
        >
          <LogOut className="h-5 w-5" />
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { logout } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const handleLogout = React.useCallback(() => {
    logout();
    router.push("/login");
  }, [logout, router]);

  React.useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  return (
    <div className="flex min-h-screen bg-[#050505] dark">
      <aside className="hidden w-64 border-r border-white/5 bg-black/40 backdrop-blur-2xl lg:flex lg:flex-col">
        <SidebarContent pathname={pathname} onLogout={handleLogout} />
      </aside>

      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close navigation menu"
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          <aside className="relative z-10 flex h-full w-[84vw] max-w-xs flex-col border-r border-white/10 bg-[#0a0a0a] shadow-2xl">
            <div className="flex items-center justify-end p-4">
              <Button
                variant="ghost"
                size="icon"
                className="text-white hover:bg-white/10"
                onClick={() => setMobileMenuOpen(false)}
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
            <SidebarContent
              pathname={pathname}
              onNavigate={() => setMobileMenuOpen(false)}
              onLogout={handleLogout}
            />
          </aside>
        </div>
      )}

      <main className="flex min-h-screen flex-1 flex-col overflow-hidden">
        <header className="flex min-h-16 items-center justify-between border-b border-white/5 bg-black/20 px-4 backdrop-blur-xl sm:px-6 lg:px-8">
          <div className="flex items-center gap-3 text-muted-foreground">
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/10 lg:hidden"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open navigation menu"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div className="hidden items-center gap-4 sm:flex">
              <span className="text-xs font-semibold uppercase tracking-widest">Workspace</span>
              <span className="h-4 w-px bg-white/10" />
            </div>
            <h2 className="text-sm font-medium capitalize text-foreground">
              {pathname.split("/").pop() || "Overview"}
            </h2>
          </div>

          <div className="flex items-center gap-3 sm:gap-6">
            <button className="relative rounded-xl p-2 text-muted-foreground transition-colors hover:bg-white/5">
              <Bell className="h-5 w-5" />
              <span className="absolute top-2.5 right-2.5 h-1.5 w-1.5 rounded-full bg-primary ring-2 ring-black" />
            </button>
            <div className="flex items-center gap-3 pl-1 sm:pl-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-primary to-accent text-xs font-bold text-white shadow-lg">
                U
              </div>
              <button
                onClick={handleLogout}
                className="hidden text-xs font-semibold text-muted-foreground transition-colors hover:text-white sm:block"
              >
                Sign Out
              </button>
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-5 sm:px-6 sm:py-6 lg:px-8 lg:py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
