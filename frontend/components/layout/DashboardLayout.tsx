"use client";

import React from "react";
import { 
  LayoutDashboard, 
  Users, 
  Send, 
  Mail, 
  BarChart3, 
  Settings, 
  LogOut,
  Bell
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";

const sidebarItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Leads", href: "/leads", icon: Users },
  { name: "Campaigns", href: "/campaigns", icon: Send },
  { name: "Inbox", href: "/inbox", icon: Mail },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  // Redirect to login if not authenticated
  React.useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  return (
    <div className="flex h-screen bg-[#050505] overflow-hidden dark">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/5 bg-black/40 backdrop-blur-2xl flex flex-col">
        <div className="p-8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
              <span className="text-white font-bold text-xl">A</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Aurvyz
            </h1>
          </div>
        </div>
        
        <nav className="flex-1 px-4 space-y-1">
          {sidebarItems.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group",
                  isActive 
                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" 
                    : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                )}
              >
                <item.icon className={cn("w-5 h-5", isActive ? "text-white" : "group-hover:text-foreground")} />
                <span className="font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-border">
          <button 
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 w-full rounded-xl text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-all duration-200"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-16 border-b border-white/5 bg-black/20 backdrop-blur-xl flex items-center justify-between px-8">
          <div className="flex items-center gap-4 text-muted-foreground">
            <span className="text-xs uppercase tracking-widest font-semibold">Workspace</span>
            <span className="w-px h-4 bg-white/10"></span>
            <h2 className="text-sm font-medium text-foreground capitalize">
              {pathname.split("/").pop() || "Overview"}
            </h2>
          </div>
          
          <div className="flex items-center gap-6">
            <button className="p-2 rounded-xl hover:bg-white/5 text-muted-foreground relative transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-2.5 right-2.5 w-1.5 h-1.5 bg-primary rounded-full ring-2 ring-black"></span>
            </button>
            <div className="flex items-center gap-3 pl-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-primary to-accent flex items-center justify-center font-bold text-xs text-white shadow-lg">
                U
              </div>
              <button 
                onClick={handleLogout}
                className="text-xs font-semibold text-muted-foreground hover:text-white transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          {children}
        </div>
      </main>
    </div>
  );
}
