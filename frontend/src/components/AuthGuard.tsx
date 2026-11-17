"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

/**
 * AuthGuard — wraps a page and redirects to /login if the user is not authenticated.
 * Shows a quiet loading state while the auth token is being validated.
 */
export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen grid place-items-center" role="status" aria-live="polite">
        <div className="w-48">
          <div className="stage" data-state="live">
            <div className="stage-bar">
              <span className="stage-chip" />
            </div>
            <span className="stage-label">Loading sheet</span>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Will be redirected; render nothing
    return null;
  }

  return <>{children}</>;
}
