"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { TOKEN_KEY, UNAUTHORIZED_EVENT, fetchMe, getStoredToken } from "@/lib/api";
import type { User } from "@/types/api";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  login: () => {},
  logout: () => {},
});

function clearStoredToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore the session: validate any stored token against /api/auth/me.
  useEffect(() => {
    let cancelled = false;

    async function restore() {
      const stored = getStoredToken();
      let restored: { token: string; user: User } | null = null;
      if (stored) {
        try {
          restored = { token: stored, user: await fetchMe(stored) };
        } catch {
          clearStoredToken();
        }
      }
      if (cancelled) return;
      if (restored) {
        setToken(restored.token);
        setUser(restored.user);
      }
      setIsLoading(false);
    }

    void restore();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback((newToken: string, newUser: User) => {
    try {
      localStorage.setItem(TOKEN_KEY, newToken);
    } catch {
      /* session-only login if storage is unavailable */
    }
    setToken(newToken);
    setUser(newUser);
  }, []);

  const logout = useCallback(() => {
    clearStoredToken();
    setToken(null);
    setUser(null);
  }, []);

  // apiFetch signals a rejected token (expired / revoked) with a window event.
  useEffect(() => {
    window.addEventListener(UNAUTHORIZED_EVENT, logout);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, logout);
  }, [logout]);

  const value = useMemo(
    () => ({ user, token, isAuthenticated: !!token && !!user, isLoading, login, logout }),
    [user, token, isLoading, login, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
