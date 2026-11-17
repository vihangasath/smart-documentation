"use client";

import { useEffect, useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { errorMessage, signup as signupRequest } from "@/lib/api";
import AuthSheet from "@/components/AuthSheet";
import { AlertCircle, ArrowRight, CheckCircle2, Eye, EyeOff, Loader2 } from "lucide-react";

function PasswordStrength({ password }: { password: string }) {
  const checks = [
    { label: "8+ characters", pass: password.length >= 8 },
    { label: "Uppercase letter", pass: /[A-Z]/.test(password) },
    { label: "Number", pass: /\d/.test(password) },
  ];
  if (!password) return null;
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 mt-1.5">
      {checks.map((c) => (
        <li
          key={c.label}
          className="flex items-center gap-1 text-xs font-medium"
          style={{ color: c.pass ? "var(--ok)" : "var(--ink-3)" }}
        >
          <CheckCircle2 className={`w-3.5 h-3.5 ${c.pass ? "" : "opacity-40"}`} aria-hidden />
          {c.label}
          <span className="sr-only">{c.pass ? " met" : " not met"}</span>
        </li>
      ))}
    </ul>
  );
}

export default function SignupPage() {
  const { login, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) router.replace("/");
  }, [isAuthenticated, router]);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (new TextEncoder().encode(password).length > 72) {
      setError("Password must be at most 72 bytes long.");
      return;
    }

    setIsLoading(true);
    try {
      const data = await signupRequest(name.trim(), email, password);
      login(data.access_token, data.user);
      router.replace("/");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const mismatch = confirmPassword !== "" && confirmPassword !== password;

  return (
    <AuthSheet
      title="Create your account"
      subtitle="Start using Structify"
      footerText="Already have an account?"
      footerLinkText="Sign in"
      footerHref="/login"
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {error && (
          <div
            role="alert"
            className="flex items-start gap-2 p-3 text-sm border"
            style={{ borderColor: "var(--danger)", color: "var(--danger)" }}
          >
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" aria-hidden />
            <span>{error}</span>
          </div>
        )}

        <div className="space-y-1.5">
          <label htmlFor="signup-name" className="field-label">
            Full name
          </label>
          <input
            id="signup-name"
            type="text"
            autoComplete="name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Jane Smith"
            className="auth-input"
          />
        </div>

        <div className="space-y-1.5">
          <label htmlFor="signup-email" className="field-label">
            Email
          </label>
          <input
            id="signup-email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="auth-input"
          />
        </div>

        <div className="space-y-1.5">
          <label htmlFor="signup-password" className="field-label">
            Password
          </label>
          <div className="relative">
            <input
              id="signup-password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min. 8 characters"
              className="auth-input pr-11"
            />
            <button
              type="button"
              onClick={() => setShowPassword((p) => !p)}
              className="absolute right-1 top-1/2 -translate-y-1/2 icon-btn !border-0"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          <PasswordStrength password={password} />
        </div>

        <div className="space-y-1.5">
          <label htmlFor="signup-confirm" className="field-label">
            Confirm password
          </label>
          <input
            id="signup-confirm"
            type={showPassword ? "text" : "password"}
            autoComplete="new-password"
            required
            aria-invalid={mismatch}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Re-enter your password"
            className="auth-input"
            style={mismatch ? { borderColor: "var(--danger)" } : undefined}
          />
        </div>

        <button type="submit" id="signup-submit" disabled={isLoading} className="btn-signal mt-2">
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
              Creating account…
            </>
          ) : (
            <>
              Create account
              <ArrowRight className="w-5 h-5 arrow" aria-hidden />
            </>
          )}
        </button>
      </form>
    </AuthSheet>
  );
}
