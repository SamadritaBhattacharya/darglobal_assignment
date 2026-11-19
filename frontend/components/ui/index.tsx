import type { ButtonHTMLAttributes, ReactNode, SVGProps } from "react";

/** Small shadcn-style primitives. Styling lives in globals.css (.btn, .badge, .card, ...). */

type Variant = "accent" | "outline" | "ghost" | "dark";

export function Button({
  variant = "outline",
  size,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: "sm" }) {
  return <button {...props} className={`btn btn-${variant}${size ? ` btn-${size}` : ""} ${className}`.trim()} />;
}

export function Badge({ tone, children, ...rest }: { tone?: "warn"; children: ReactNode; "data-testid"?: string }) {
  return (
    <span className={`badge${tone ? ` badge-${tone}` : ""}`} {...rest}>
      {children}
    </span>
  );
}

export function Spinner() {
  return (
    <svg className="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
      <path d="M21 12a9 9 0 1 1-6.2-8.55" />
    </svg>
  );
}

const icon = (path: ReactNode) =>
  function Icon(props: SVGProps<SVGSVGElement>) {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
        {path}
      </svg>
    );
  };

export const ArrowUpIcon = icon(<><path d="M12 19V5" /><path d="m5 12 7-7 7 7" /></>);
export const ExternalIcon = icon(<><path d="M7 17 17 7" /><path d="M8 7h9v9" /></>);
export const TrashIcon = icon(<><path d="M3 6h18" /><path d="M8 6V4h8v2" /><path d="m19 6-1 14H6L5 6" /></>);
export const AlertIcon = icon(<><circle cx="12" cy="12" r="10" /><path d="M12 8v4" /><path d="M12 16h.01" /></>);
export const SunIcon = icon(<><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" /></>);
export const MoonIcon = icon(<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />);
export const InfoIcon = icon(<><circle cx="12" cy="12" r="10" /><path d="M12 16v-4" /><path d="M12 8h.01" /></>);
