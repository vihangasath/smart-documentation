"use client";

import Link from "next/link";
import LogoMark from "@/components/LogoMark";
import ThemeToggle from "@/components/ThemeToggle";

interface AuthSheetProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footerText: string;
  footerLinkText: string;
  footerHref: string;
}

/** Shared frame for the sign-in and sign-up pages: a drawing sheet with a form column. */
export default function AuthSheet({
  title,
  subtitle,
  children,
  footerText,
  footerLinkText,
  footerHref,
}: AuthSheetProps) {
  return (
    <div className="min-h-screen p-2 sm:p-3 flex">
      <div className="sheet-frame flex-1 grid lg:grid-cols-[1fr_minmax(420px,520px)]">
        {/* statement column */}
        <div
          className="hidden lg:flex relative flex-col justify-end p-12"
          style={{ borderRight: "1px solid var(--rule)" }}
          aria-hidden
        >
          <span className="reg-mark tl" />
          <span className="reg-mark tr" />
          <span className="reg-mark bl" />
          <span className="reg-mark br" />
          {/* a drafted entity sketch, in hairlines, so the sheet is not empty */}
          <svg
            viewBox="0 0 420 220"
            className="absolute top-16 left-12 w-[min(420px,60%)]"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            style={{ color: "var(--ink-3)" }}
          >
            <rect x="8" y="20" width="120" height="64" />
            <path d="M8 44H128M8 64H128" />
            <rect x="292" y="20" width="120" height="64" />
            <path d="M292 44H412M292 64H412" />
            <rect x="150" y="140" width="120" height="64" />
            <path d="M150 164H270M150 184H270" />
            <path d="M128 52H210V140M292 52H210" />
            <path d="M210 128v12M204 134l6 6 6-6M120 46v12M290 46v12" strokeWidth="1.5" />
            <rect x="203" y="45" width="14" height="14" fill="var(--signal)" stroke="none" />
          </svg>
          <p className="font-cond font-bold leading-[0.92] tracking-tight text-[clamp(3.5rem,7vw,6rem)]">
            Spec in.
            <br />
            Structure out.
          </p>
          <div className="mt-8 h-[6px] w-40" style={{ background: "var(--signal)" }} />
          <p className="mt-5 max-w-sm text-lg" style={{ color: "var(--ink-2)" }}>
            Requirements become a domain model, diagrams and a starter project.
          </p>
        </div>

        {/* form column */}
        <div className="flex flex-col">
          <div className="flex items-center justify-between px-5 py-3" style={{ borderBottom: "1px solid var(--rule)" }}>
            <div className="flex items-center gap-2.5">
              <LogoMark size={34} className="shrink-0" />
              <span className="font-cond text-2xl font-semibold leading-none tracking-tight">Structify</span>
            </div>
            <ThemeToggle />
          </div>

          <div className="flex-1 flex flex-col justify-center px-5 sm:px-10 py-10 w-full max-w-md mx-auto">
            <h1 className="font-cond text-5xl font-bold leading-none tracking-tight">{title}</h1>
            <p className="mt-2 mb-7" style={{ color: "var(--ink-2)" }}>
              {subtitle}
            </p>
            {children}
          </div>

          <p
            className="px-5 py-4 text-sm text-center"
            style={{ borderTop: "1px solid var(--rule)", color: "var(--ink-2)" }}
          >
            {footerText}{" "}
            <Link href={footerHref} className="font-semibold underline underline-offset-4 decoration-2" style={{ textDecorationColor: "var(--signal)" }}>
              {footerLinkText}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
