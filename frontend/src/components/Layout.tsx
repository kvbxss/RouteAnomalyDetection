import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  Plane,
  TriangleAlert,
  Map as MapIcon,
  Bot,
} from "lucide-react";
import { JSX } from "react";

interface LayoutProps {
  children: React.ReactNode;
}

type NavItem = { name: string; href: string; icon: JSX.Element };

const SIDEBAR_WIDTH = 240; // px

const Layout = ({ children }: LayoutProps) => {
  const location = useLocation();

  const navigation: NavItem[] = [
    { name: "Dashboard", href: "/", icon: <LayoutDashboard size={16} /> },
    { name: "Flights", href: "/flights", icon: <Plane size={16} /> },
    {
      name: "Anomalies",
      href: "/anomalies",
      icon: <TriangleAlert size={16} />,
    },
    { name: "Map", href: "/map", icon: <MapIcon size={16} /> },
    { name: "Chatbot", href: "/chatbot", icon: <Bot size={16} /> },
  ];

  return (
    <div className="min-h-screen w-full overflow-x-hidden bg-background text-foreground md:pl-60">
      {/* Fixed Sidebar */}
      <aside
        className="fixed inset-y-0 left-0 z-40 hidden w-60 border-r border-border bg-card md:block"
        style={{ width: SIDEBAR_WIDTH }}
      >
        <div className="px-4 py-5">
          <div className="mb-3 text-[10px] font-medium uppercase tracking-[0.2em] text-muted-foreground">
            Menu
          </div>
          <nav className="space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`group flex items-center gap-3 rounded-md px-3 py-2 text-[11px] uppercase tracking-[0.15em] transition-colors ${
                    isActive
                      ? "bg-primary/15 text-primary"
                      : "text-muted-foreground hover:bg-muted/40 hover:text-foreground"
                  }`}
                >
                  <span className="opacity-80 group-hover:opacity-100">
                    {item.icon}
                  </span>
                  <span className="font-semibold">{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* Content Area */}
      <header className="sticky top-0 z-30 border-b border-border bg-card/70 backdrop-blur supports-[backdrop-filter]:bg-card/50">
        <div className="flex h-12 w-full items-center justify-between px-4 md:px-8">
          <div className="flex items-center gap-2">
            <div className="h-5 w-5 rounded bg-primary" />
            <span className="text-sm font-semibold tracking-widest uppercase">
              Route Anomaly Detection
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              API Status
            </Button>
          </div>
        </div>
      </header>

      <main className="px-4 py-8 md:px-8">{children}</main>
    </div>
  );
};

export default Layout;
