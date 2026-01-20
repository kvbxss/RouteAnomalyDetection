import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Plane,
  TriangleAlert,
  Map as MapIcon,
  Bot,
  LogOut,
} from "lucide-react";
import { JSX } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

interface LayoutProps {
  children: React.ReactNode;
}

type NavItem = { name: string; href: string; icon: JSX.Element };

const Layout = ({ children }: LayoutProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

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
    <div className="min-h-screen w-full overflow-x-hidden bg-background text-foreground md:pl-56">
      {/* Fixed Sidebar */}
      <aside
        className="fixed inset-y-0 left-0 z-40 hidden w-56 border-r border-border bg-card md:block"
        style={{ width: 224 }}
      >
        <div className="flex h-14 items-center border-b border-border px-6">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-primary" />
            <span className="text-sm font-medium">Anomaly Detection</span>
          </div>
        </div>
        <div className="px-3 py-4">
          <nav className="space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`group flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all ${
                    isActive
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  }`}
                >
                  <span className={isActive ? "opacity-100" : "opacity-70 group-hover:opacity-100"}>
                    {item.icon}
                  </span>
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* Content Area */}
      <header className="sticky top-0 z-30 border-b border-border bg-card/80 backdrop-blur-sm">
        <div className="flex h-14 w-full items-center justify-between px-6">
          <h1 className="text-sm font-medium text-muted-foreground">
            Flight Route Analysis System
          </h1>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
              <span>Online</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="gap-2 text-muted-foreground hover:text-foreground"
            >
              <LogOut size={14} />
              <span className="text-xs">Logout</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="px-6 py-6 md:px-8 md:py-8">{children}</main>
    </div>
  );
};

export default Layout;
