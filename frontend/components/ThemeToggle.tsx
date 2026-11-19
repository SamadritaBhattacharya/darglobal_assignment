"use client";

import { useEffect, useState } from "react";
import { Button, MoonIcon, SunIcon } from "./ui";

type Theme = "light" | "dark";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme | null>(null);

  useEffect(() => {
    // The page script has already set data-theme; mirror it after mount to avoid a hydration mismatch.
    /* eslint-disable react-hooks/set-state-in-effect */
    setTheme(document.documentElement.dataset.theme === "dark" ? "dark" : "light");
    /* eslint-enable react-hooks/set-state-in-effect */
  }, []);

  function toggle() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    const root = document.documentElement;
    root.classList.add("theme-switching");
    root.dataset.theme = next;
    window.setTimeout(() => root.classList.remove("theme-switching"), 350);
    try {
      localStorage.setItem("dar-theme", next);
    } catch {
      /* storage blocked: the choice still applies for this visit */
    }
    setTheme(next);
  }

  const dark = theme === "dark";
  return (
    <Button
      variant="ghost"
      size="sm"
      type="button"
      className="theme-toggle"
      onClick={toggle}
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      title={dark ? "Light theme" : "Dark theme"}
    >
      {dark ? <SunIcon /> : <MoonIcon />}
    </Button>
  );
}
