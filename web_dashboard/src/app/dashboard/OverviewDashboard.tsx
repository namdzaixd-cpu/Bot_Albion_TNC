"use client";

import { useState, useEffect } from "react";
import { Users, Gem, Ban, Bot, ArrowUpRight, Activity } from "lucide-react";

type Activity = { time: string; event: string; module: string; status: string };

const fmtNum = (n: number) =>
  n >= 1_000_000 ? (n / 1_000_000).toFixed(1) + "M"
  : n >= 1_000 ? (n / 1_000).toFixed(1) + "k"
  : n.toString();

const fmtTime = (iso: string) => {
  try { return new Date(iso).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }); }
  catch { return "—"; }
};

export default function OverviewDashboard() {
  const [stats, setStats] = useState({ members: 0, corebank_total: 0, blacklist_count: 0, ai_today: 0 });
  const [activity, setActivity] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const res = await fetch("/api/overview");
        if (res.ok) {
          const d = await res.json();
          if (!mounted) return;
          setStats(d.stats);
          setActivity(d.activity);
        }
      } catch { /* ignore */ }
      finally { if (mounted) setLoading(false); }
    };
    load();
    // Realtime refresh mỗi 15s
    const iv = setInterval(load, 15000);
    return () => { mounted = false; clearInterval(iv); };
  }, []);

  const cards = [
    { label: "Thành viên", value: fmtNum(stats.members), sub: "Tổng thành viên guild", icon: Users, accent: "from-indigo-500/20 to-indigo-500/5", ring: "group-hover:shadow-[0_0_25px_rgba(99,102,241,0.35)]" },
    { label: "Core Bank", value: fmtNum(stats.corebank_total), sub: "Tổng silver quản lý", icon: Gem, accent: "from-emerald-500/20 to-emerald-500/5", ring: "group-hover:shadow-[0_0_25px_rgba(52,211,153,0.35)]" },
    { label: "Blacklist", value: fmtNum(stats.blacklist_count), sub: "Người bị cấm", icon: Ban, accent: "from-rose-500/20 to-rose-500/5", ring: "group-hover:shadow-[0_0_25px_rgba(244,63,94,0.35)]" },
    { label: "AI hôm nay", value: fmtNum(stats.ai_today), sub: "Lượt chat AI", icon: Bot, accent: "from-cyan-500/20 to-cyan-500/5", ring: "group-hover:shadow-[0_0_25px_rgba(34,211,238,0.35)]" },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {cards.map((c) => (
          <div key={c.label} className={`group relative overflow-hidden rounded-2xl border border-border bg-surface/60 backdrop-blur-md p-5 transition-all duration-300 hover:-translate-y-1 ${c.ring}`}>
            <div className={`absolute inset-0 bg-gradient-to-br ${c.accent} opacity-60`} />
            <div className="relative">
              <div className="flex items-center justify-between">
                <span className="text-sm text-text-muted">{c.label}</span>
                <c.icon className="w-5 h-5 text-text-muted group-hover:text-white transition-colors" />
              </div>
              <div className="mt-3 text-3xl font-bold text-white tabular-nums">
                {loading ? <div className="h-8 w-16 rounded bg-surface-2 animate-pulse" /> : c.value}
              </div>
              <div className="mt-1 text-xs text-text-muted">{c.sub}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Activity feed */}
      <div className="rounded-2xl border border-border bg-surface/60 backdrop-blur-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" /> Hoạt động gần đây
          </h2>
          <span className="text-xs text-text-muted flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" /> Real-time
          </span>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 rounded-xl bg-surface-2 animate-pulse" />
            ))}
          </div>
        ) : activity.length === 0 ? (
          <div className="text-center text-text-muted py-12">
            <div className="text-4xl mb-3 opacity-50">📭</div>
            Chưa có hoạt động nào được ghi nhận.
          </div>
        ) : (
          <div className="space-y-2">
            {activity.map((a, i) => (
              <div key={i} className="flex items-center gap-4 rounded-xl border border-border/50 bg-background/40 px-4 py-3 hover:bg-surface-2/50 transition-colors">
                <span className="text-xs text-text-muted font-mono w-12">{fmtTime(a.time)}</span>
                <span className="flex-1 text-sm text-white/90 truncate">{a.event}</span>
                <span className="text-xs px-2.5 py-1 rounded-md bg-surface-2 text-text-muted">{a.module}</span>
                <span className={`text-xs px-2.5 py-1 rounded-md ${a.status === "ok" || a.status === "OK" ? "bg-green-500/15 text-green-400" : "bg-rose-500/15 text-rose-400"}`}>
                  {a.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
