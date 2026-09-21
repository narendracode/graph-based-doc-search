import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AuthProvider } from "@/lib/auth-context";
import { ThemeProvider } from "@/lib/theme-context";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "NBCC Document Archive",
  description: "Central document archive for NBCC (India) Limited",
};

// Applies the right theme class before first paint, so there's no flash of the
// wrong theme while React hydrates and ThemeProvider's own effect catches up.
const NO_FLASH_THEME_SCRIPT = `
(function () {
  try {
    var stored = localStorage.getItem("nbcc-theme") || "system";
    var resolved = stored === "system"
      ? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
      : stored;
    document.documentElement.classList.toggle("dark", resolved === "dark");
    document.documentElement.style.colorScheme = resolved;
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      // The no-flash script below sets the `dark` class and `color-scheme` style on
      // this element before hydration, intentionally out-of-band from React — this
      // tells React not to warn about (and not to "fix") that expected mismatch.
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: NO_FLASH_THEME_SCRIPT }} />
      </head>
      <body className="flex min-h-full flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
        <ThemeProvider>
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
