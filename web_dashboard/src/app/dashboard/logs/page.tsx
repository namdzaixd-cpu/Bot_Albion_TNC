"use client";

import { useState, useEffect, useRef } from "react";
import { Terminal, Trash2, RefreshCw } from "lucide-react";
import { toast } from "react-hot-toast";

interface LogEntry {
  id: string;
  created_at: string;
  level: string;
  module: string;
  message: string;
}

export default function LogsDashboard() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchLogs = async () => {
    try {
      const res = await fetch('/api/logs');
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error("Lỗi lấy logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    
    // Polling mỗi 3 giây
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Tự động cuộn xuống dưới cùng nếu autoScroll bật
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const clearLogs = async () => {
    if (!confirm("Bạn có chắc chắn muốn xoá toàn bộ System Logs không?")) return;
    
    try {
      const res = await fetch('/api/logs', { method: 'DELETE' });
      if (res.ok) {
        toast.success("Đã dọn dẹp logs!");
        setLogs([]);
      } else {
        toast.error("Lỗi xoá logs!");
      }
    } catch (err) {
      toast.error("Lỗi mạng!");
    }
  };

  const getLogColor = (level: string) => {
    switch (level) {
      case "ERROR": return "text-red-400";
      case "WARNING": return "text-yellow-400";
      default: return "text-gray-300";
    }
  };

  return (
    <div className="max-w-5xl mx-auto flex flex-col h-full pb-10">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gray-700/50 flex items-center justify-center border border-gray-600/50">
            <Terminal className="w-5 h-5 text-gray-300" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">System Logs</h1>
            <p className="text-text-muted text-sm mt-1">Lịch sử hoạt động của Bot (Terminal View).</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
            <input 
              type="checkbox" 
              checked={autoScroll} 
              onChange={(e) => setAutoScroll(e.target.checked)} 
              className="rounded bg-background border-border text-primary focus:ring-primary"
            />
            Auto-scroll
          </label>
          <button 
            onClick={fetchLogs}
            className="p-2 rounded-lg bg-surface border border-border hover:bg-surface-hover transition-colors text-text-muted hover:text-white"
            title="Làm mới"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button 
            onClick={clearLogs}
            className="p-2 rounded-lg bg-red-500/10 border border-red-500/30 hover:bg-red-500/20 transition-colors text-red-400"
            title="Xoá tất cả"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 bg-[#1e1e1e] border border-gray-800 rounded-xl p-4 shadow-2xl relative overflow-hidden flex flex-col min-h-[500px]">
        {/* Terminal Header */}
        <div className="flex items-center gap-2 mb-4 px-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span className="text-xs text-gray-500 font-mono ml-2">bash - bot_process</span>
        </div>

        {/* Logs Output */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto font-mono text-sm space-y-1 custom-scrollbar pr-2"
        >
          {logs.length === 0 ? (
            <p className="text-gray-500 italic">Đang chờ log...</p>
          ) : (
            logs.map(log => (
              <div key={log.id} className="hover:bg-white/5 px-1 rounded transition-colors break-words">
                <span className="text-gray-500 text-xs mr-3">[{new Date(log.created_at).toLocaleTimeString()}]</span>
                <span className={`font-semibold text-xs mr-2 ${getLogColor(log.level)}`}>[{log.level}]</span>
                <span className={getLogColor(log.level)}>{log.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
