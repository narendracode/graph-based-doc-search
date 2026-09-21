"use client";

import { useTheme, type ThemeSetting } from "./theme-context";

const OPTIONS: { value: ThemeSetting; label: string }[] = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "system", label: "System" },
];

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <select
      value={theme}
      onChange={(e) => setTheme(e.target.value as ThemeSetting)}
      aria-label="Theme"
      className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-600 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
    >
      {OPTIONS.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}
