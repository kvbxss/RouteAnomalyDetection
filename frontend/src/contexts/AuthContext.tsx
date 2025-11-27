import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { isAuthenticated, logout as apiLogout, login as apiLogin } from "@/lib/api";

interface AuthContextType {
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is authenticated on mount
    setAuthenticated(isAuthenticated());
    setLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    await apiLogin(username, password);
    setAuthenticated(true);
  };

  const logout = () => {
    apiLogout();
    setAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated: authenticated, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
