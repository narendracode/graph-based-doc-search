"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

export type ThemeSetting = "light" | "dark" | "system";
type ResolvedTheme = "light" | "dark";

interface ThemeContextValue {
  theme: ThemeSetting;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: ThemeSetting) => void;
}

const STORAGE_KEY = "nbcc-theme";
const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

function systemTheme(): ResolvedTheme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(resolved: ResolvedTheme) {
  document.documentElement.classList.toggle("dark", resolved === "dark");
  document.documentElement.style.colorScheme = resolved;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // The inline script in layout.tsx already applied the right class before paint —
  // these just pick up what it decided so React state matches the DOM.
  const [theme, setThemeState] = useState<ThemeSetting>("system");
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>("light");

  useEffect(() => {
    const stored = (localStorage.getItem(STORAGE_KEY) as ThemeSetting | null) ?? "system";
    setThemeState(stored);
    setResolvedTheme(stored === "system" ? systemTheme() : stored);
  }, []);

  useEffect(() => {
    if (theme !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      const resolved = systemTheme();
      setResolvedTheme(resolved);
      applyTheme(resolved);
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [theme]);

  const setTheme = useCallback((next: ThemeSetting) => {
    setThemeState(next);
    localStorage.setItem(STORAGE_KEY, next);
    const resolved = next === "system" ? systemTheme() : next;
    setResolvedTheme(resolved);
    applyTheme(resolved);
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
