"use client";

import { useState, useEffect } from "react";
import { Search, LayoutDashboard, Users, Shield, Gem, Ban, Bot, Terminal } from "lucide-react";

const ITEMS = [
  { id: "overview", name: "Tổng quan", icon: LayoutDashboard },
  { id: "onboarding", name: "Recruiter (Onboarding)", icon: Users },
  { id: "guildcheck", name: "GuildCheck System", icon: Shield },
  { id: "corebank", name: "Quản lý Core-Bank", icon: Gem },
  { id: "blacklist", name: "Global Blacklist", icon: Ban },
  { id: "ai", name: "AI Assistant & TTS", icon: Bot },
  { id: "logs", name: "System Logs", icon: Terminal },
];

export default function CommandPalette({ onSelect }: { onSelect: (id: string) => void }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
        setQ(""); setIdx(0);
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const filtered = ITEMS.filter((i) => i.name.toLowerCase().includes(q.toLowerCase()));

  const choose = (id: string) => { onSelect(id); setOpen(false); setQ(""); };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/60 backdrop-blur-sm animate-fade-in" onClick={() => setOpen(false)}>
      <div className="w-full max-w-lg rounded-2xl border border-border bg-surface shadow-2xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-3 px-4 border-b border-border">
          <Search className="w-5 h-5 text-text-muted" />
          <input
            autoFocus
            value={q}
            onChange={(e) => { setQ(e.target.value); setIdx(0); }}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") { e.preventDefault(); setIdx((i) => Math.min(i + 1, filtered.length - 1)); }
              if (e.key === "ArrowUp") { e.preventDefault(); setIdx((i) => Math.max(i - 1, 0)); }
              if (e.key === "Enter" && filtered[idx]) choose(filtered[idx].id);
            }}
            placeholder="Tìm module... (Ctrl+K)"
            className="flex-1 bg-transparent py-4 text-white outline-none placeholder:text-text-muted"
          />
          <kbd className="text-xs text-text-muted border border-border rounded px-1.5 py-0.5">ESC</kbd>
        </div>
        <div className="max-h-80 overflow-y-auto p-2">
          {filtered.length === 0 && <div className="text-center text-text-muted py-6 text-sm">Không tìm thấy</div>}
          {filtered.map((it, i) => (
            <button
              key={it.id}
              onMouseEnter={() => setIdx(i)}
              onClick={() => choose(it.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-colors ${i === idx ? "bg-primary/20 text-primary" : "text-text-muted hover:bg-surface-2"}`}
            >
              <it.icon className="w-4 h-4" />
              <span className="text-sm">{it.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
