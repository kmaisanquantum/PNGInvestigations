"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, clearToken, CurrentUser } from "@/lib/api";

export default function Shell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    api.me().then(setUser).catch(() => {});
  }, []);

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-ink text-paper flex flex-col shrink-0">
        <div className="px-5 py-6 border-b border-white/10">
          <p className="stamp text-[10px] text-brass mb-1">Case Mgmt</p>
          <p className="font-display text-lg font-semibold leading-tight">Investigation<br />Platform</p>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1 text-sm">
          <Link href="/cases" className="block px-3 py-2 rounded hover:bg-white/10 transition-colors">
            Cases
          </Link>
        </nav>
        <div className="px-5 py-4 border-t border-white/10 text-xs">
          {user && (
            <>
              <p className="text-paper/90">{user.full_name}</p>
              <p className="stamp text-brass">{user.role}</p>
            </>
          )}
          <button onClick={handleLogout} className="mt-3 text-paper/60 hover:text-paper underline">
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 min-w-0">{children}</main>
    </div>
  );
}
