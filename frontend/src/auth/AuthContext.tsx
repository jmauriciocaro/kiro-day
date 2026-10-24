// Minimal auth state: holds the JWT and role, persisted in sessionStorage so a
// page reload during a shift keeps the session.
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Role } from "../types";

interface AuthState {
  token: string | null;
  role: Role | null;
  username: string | null;
}

interface AuthContextValue extends AuthState {
  login: (token: string, role: Role, username: string) => void;
  logout: () => void;
}

const STORAGE_KEY = "pos.auth";
const AuthContext = createContext<AuthContextValue | null>(null);

function readStored(): AuthState {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as AuthState;
  } catch {
    // ignore
  }
  return { token: null, role: null, username: null };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(readStored);

  const login = useCallback((token: string, role: Role, username: string) => {
    const next = { token, role, username };
    setState(next);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }, []);

  const logout = useCallback(() => {
    setState({ token: null, role: null, username: null });
    sessionStorage.removeItem(STORAGE_KEY);
  }, []);

  const value = useMemo(
    () => ({ ...state, login, logout }),
    [state, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
