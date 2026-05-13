import type { Metadata } from "next";
import "./globals.css";
import PWARegistrar from "@/components/pwa/PWARegistrar";

export const metadata: Metadata = {
  title: "Aurvyz | AI-Powered Outreach & Lead Intelligence",
  description: "Automate your sales outreach with intelligent AI personalization and lead tracking.",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Aurvyz",
  },
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/logo.svg", type: "image/svg+xml" },
    ],
    apple: [{ url: "/favicon.ico" }],
  },
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover" as const,
  themeColor: "#050505",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased dark">
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <PWARegistrar />
        {children}
      </body>
    </html>
  );
}
