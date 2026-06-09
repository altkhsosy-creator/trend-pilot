import React from "react";
import { Link, useLocation } from "wouter";
import { useHealthCheck } from "@workspace/api-client-react";
import { 
  Activity, 
  BarChart2, 
  Eye, 
  Menu, 
  Moon, 
  Sun, 
  Zap, 
  Signal,
  Clapperboard,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

export function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();
  const { theme, setTheme } = useTheme();
  const { data: health } = useHealthCheck();

  const isHealthy = health?.status === "ok";

  const navigation = [
    { name: "Dashboard", href: "/", icon: Activity },
    { name: "Trends", href: "/trends", icon: BarChart2 },
    { name: "Watchlist", href: "/watchlist", icon: Eye },
    { name: "Studio", href: "/studio", icon: Clapperboard },
  ];

  const NavLinks = () => (
    <>
      {navigation.map((item) => {
        const isActive = location === item.href || (item.href !== "/" && location.startsWith(item.href));
        return (
          <Link
            key={item.name}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors hover-elevate",
              isActive 
                ? "bg-primary/10 text-primary" 
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <item.icon className="h-4 w-4" />
            {item.name}
          </Link>
        );
      })}
    </>
  );

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row">
      <aside className="hidden md:flex flex-col w-64 border-r border-border/50 bg-card z-10 sticky top-0 h-screen">
        <div className="p-6 flex items-center gap-2 text-primary font-bold text-xl tracking-tight border-b border-border/50">
          <Zap className="h-6 w-6" />
          TrendPilot
        </div>
        <nav className="flex-1 px-4 py-6 space-y-2">
          <NavLinks />
        </nav>
        <div className="p-4 border-t border-border/50 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground font-mono flex items-center gap-2">
              <Signal className={cn("h-3 w-3", isHealthy ? "text-emerald-500" : "text-destructive")} />
              {isHealthy ? "SYSTEM OPTIMAL" : "CONNECTING..."}
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start gap-2 text-xs"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            Toggle Theme
          </Button>
        </div>
      </aside>

      <header className="md:hidden flex items-center justify-between p-4 border-b border-border/50 bg-card sticky top-0 z-50">
        <div className="flex items-center gap-2 text-primary font-bold text-lg">
          <Zap className="h-5 w-5" />
          TrendPilot
        </div>
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[240px] sm:w-[300px] flex flex-col p-0">
            <div className="p-6 flex items-center gap-2 text-primary font-bold text-xl border-b border-border/50">
              <Zap className="h-6 w-6" />
              TrendPilot
            </div>
            <nav className="flex-1 px-4 py-6 space-y-2">
              <NavLinks />
            </nav>
            <div className="p-4 border-t border-border/50">
               <Button
                variant="outline"
                size="sm"
                className="w-full justify-start gap-2"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              >
                {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                Toggle Theme
              </Button>
            </div>
          </SheetContent>
        </Sheet>
      </header>

      <main className="flex-1 flex flex-col min-w-0">
        {children}
      </main>
    </div>
  );
}
