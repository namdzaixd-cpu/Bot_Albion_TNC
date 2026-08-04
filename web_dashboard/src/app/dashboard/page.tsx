"use client";

import { useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { 
  LayoutDashboard, Users, Shield, 
  Swords, Gem, AlertTriangle, Package, Bot, ChevronLeft, Power, CheckCircle2, XCircle, Settings2
} from "lucide-react";

const MODULES = [
  { id: 'onboarding', name: 'Recruiter (Onboarding)', icon: Users },
  { id: 'guildcheck', name: 'GuildCheck System', icon: Shield },
  { id: 'massing', name: 'Massing / CTA', icon: Swords },
  { id: 'siphoned', name: 'Siphoned Energy', icon: Gem },
  { id: 'blacklist', name: 'Global Blacklist', icon: AlertTriangle },
  { id: 'corebank', name: 'Quản lý Core-Bank', icon: Package },
  { id: 'ai', name: 'AI Assistant & TTS', icon: Bot },
];

export default function Dashboard() {
  const { data: session } = useSession();
  const [activeModule, setActiveModule] = useState('onboarding');
  
  // Mock Data
  const [isOnboardEnabled, setIsOnboardEnabled] = useState(true);
  const [config, setConfig] = useState({
    apply_channel_id: "111122223333",
    question_channel_id: "",
    officer_role_id: "444455556666",
    member_role_id: ""
  });

  const handleConfigChange = (field: string, value: string) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 border-r border-border bg-surface/30 backdrop-blur-md flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-border/50">
          <Link href="/" className="flex items-center gap-3 text-text-muted hover:text-white transition-colors">
            <ChevronLeft className="w-5 h-5" />
            <span className="font-semibold text-sm">Về trang chủ</span>
          </Link>
        </div>
        
        <div className="p-6">
          <h2 className="text-xs font-bold text-text-muted uppercase tracking-wider mb-4 flex items-center gap-2">
            <LayoutDashboard className="w-4 h-4" />
            Guild Assistant Bot
          </h2>
          <nav className="space-y-2">
            {MODULES.map((mod) => (
              <button
                key={mod.id}
                onClick={() => setActiveModule(mod.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                  activeModule === mod.id 
                    ? 'bg-primary/20 text-primary font-semibold shadow-[inset_0_0_15px_rgba(99,102,241,0.2)] border border-primary/30' 
                    : 'text-text-muted hover:bg-surface hover:text-white border border-transparent'
                }`}
              >
                <mod.icon className={`w-5 h-5 ${activeModule === mod.id ? 'text-primary' : 'text-text-muted'}`} />
                <span className="text-sm">{mod.name}</span>
              </button>
            ))}
          </nav>
        </div>
        
        {/* User Profile */}
        <div className="mt-auto p-6 border-t border-border/50">
          <div className="flex items-center gap-3 glass-panel p-3 rounded-xl">
            <img src={session?.user?.image || 'https://cdn.discordapp.com/embed/avatars/0.png'} alt="Avatar" className="w-10 h-10 rounded-full border border-border" />
            <div className="overflow-hidden">
              <p className="text-sm font-bold text-white truncate">{session?.user?.name || 'Guest'}</p>
              <p className="text-xs text-text-muted truncate">Quản trị viên</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col bg-background/50 relative">
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))] opacity-5 pointer-events-none"></div>
        
        {/* Header */}
        <header className="h-20 flex items-center justify-between px-10 border-b border-border/50 z-10 relative">
          <div>
            <h1 className="text-2xl font-bold text-white">Cấu Hình Module</h1>
            <p className="text-sm text-text-muted mt-1">Quản lý và thiết lập trạng thái cho các tính năng của Bot.</p>
          </div>
          
          <div className="flex items-center gap-4">
            <span className="text-sm font-semibold text-text-muted">Trạng thái Module:</span>
            <button
              onClick={() => setIsOnboardEnabled(!isOnboardEnabled)}
              className={`relative inline-flex h-8 w-16 items-center rounded-full transition-colors duration-300 focus:outline-none ${
                isOnboardEnabled ? 'bg-green-500 shadow-[0_0_15px_rgba(34,197,94,0.4)]' : 'bg-surface'
              }`}
            >
              <span
                className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform duration-300 ${
                  isOnboardEnabled ? 'translate-x-9' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-sm font-bold ${isOnboardEnabled ? 'text-green-400' : 'text-text-muted'}`}>
              {isOnboardEnabled ? 'Đang Bật' : 'Đã Tắt'}
            </span>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 p-10 overflow-y-auto custom-scrollbar z-10 relative">
          {activeModule === 'onboarding' ? (
            <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
              
              <div className="glass-panel p-8 rounded-2xl border-primary/20">
                <div className="flex items-start gap-6">
                  <div className="w-16 h-16 rounded-2xl bg-primary/20 border border-primary/30 flex items-center justify-center text-3xl">
                    👋
                  </div>
                  <div className="flex-1">
                    <h2 className="text-2xl font-bold text-white">Recruiter (Onboarding)</h2>
                    <p className="text-text-muted mt-2 leading-relaxed">
                      Tính năng duyệt đơn tự động. Cho phép cấu hình kênh tiếp đón, kênh phỏng vấn và cài đặt vai trò tự động.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-8">
                {/* Lệnh / Cấu hình */}
                <div className="space-y-6">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Settings2 className="w-5 h-5 text-primary" />
                    Các Cấu Hình (Lệnh)
                  </h3>
                  
                  {/* Item 1 */}
                  <div className="glass-panel p-5 rounded-xl space-y-4 hover:border-primary/50 transition-colors">
                    <div>
                      <code className="text-primary font-mono text-xs bg-primary/10 px-2 py-1 rounded">/recuibot set_apply_channel</code>
                      <p className="text-sm font-medium mt-2">Kênh nộp đơn (Channel muốn bot hoạt động)</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <select 
                        value={config.apply_channel_id}
                        onChange={(e) => handleConfigChange('apply_channel_id', e.target.value)}
                        className="flex-1 bg-surface border border-border text-sm rounded-lg px-3 py-2 text-white outline-none focus:border-primary"
                      >
                        <option value="">-- Chọn Channel --</option>
                        <option value="111122223333">#apply-guild</option>
                        <option value="123456789">#welcome</option>
                      </select>
                    </div>
                  </div>

                  {/* Item 2 */}
                  <div className="glass-panel p-5 rounded-xl space-y-4 hover:border-primary/50 transition-colors">
                    <div>
                      <code className="text-primary font-mono text-xs bg-primary/10 px-2 py-1 rounded">/recuibot setup_channels</code>
                      <p className="text-sm font-medium mt-2">Kênh gửi câu hỏi / phỏng vấn</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <select 
                        value={config.question_channel_id}
                        onChange={(e) => handleConfigChange('question_channel_id', e.target.value)}
                        className="flex-1 bg-surface border border-border text-sm rounded-lg px-3 py-2 text-white outline-none focus:border-primary"
                      >
                        <option value="">-- Chọn Channel --</option>
                        <option value="987654321">#phong-van</option>
                      </select>
                    </div>
                  </div>
                  
                  {/* Item 3 */}
                  <div className="glass-panel p-5 rounded-xl space-y-4 hover:border-primary/50 transition-colors">
                    <div>
                      <code className="text-primary font-mono text-xs bg-primary/10 px-2 py-1 rounded">/recuibot setup_roles</code>
                      <p className="text-sm font-medium mt-2">Cấu hình Roles nhận được</p>
                    </div>
                    <div className="space-y-3">
                      <select 
                        value={config.officer_role_id}
                        onChange={(e) => handleConfigChange('officer_role_id', e.target.value)}
                        className="w-full bg-surface border border-border text-sm rounded-lg px-3 py-2 text-white outline-none focus:border-primary"
                      >
                        <option value="">-- Chọn Officer Role --</option>
                        <option value="444455556666">@Officer</option>
                      </select>
                      <select 
                        value={config.member_role_id}
                        onChange={(e) => handleConfigChange('member_role_id', e.target.value)}
                        className="w-full bg-surface border border-border text-sm rounded-lg px-3 py-2 text-white outline-none focus:border-primary"
                      >
                        <option value="">-- Chọn Member Role --</option>
                        <option value="999988887777">@Member</option>
                      </select>
                    </div>
                  </div>

                </div>

                {/* Trạng thái hiện tại */}
                <div className="space-y-6">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Power className="w-5 h-5 text-primary" />
                    Trạng Thái Cấu Hình
                  </h3>
                  
                  <div className="space-y-3 relative">
                    
                    {/* Status 1 */}
                    <div className={`p-4 rounded-xl border ${config.apply_channel_id ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'} flex items-center gap-4 transition-colors`}>
                      {config.apply_channel_id ? <CheckCircle2 className="text-green-400 w-6 h-6" /> : <XCircle className="text-red-400 w-6 h-6" />}
                      <div>
                        <p className={`font-semibold ${config.apply_channel_id ? 'text-green-400' : 'text-red-400'}`}>
                          {config.apply_channel_id ? 'Đang hoạt động' : 'Thiếu thông tin'}
                        </p>
                        <p className="text-xs text-text-muted mt-1">Kênh nộp đơn: {config.apply_channel_id || 'Chưa thiết lập'}</p>
                      </div>
                    </div>

                    {/* Status 2 */}
                    <div className={`p-4 rounded-xl border ${config.question_channel_id ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'} flex items-center gap-4 transition-colors`}>
                      {config.question_channel_id ? <CheckCircle2 className="text-green-400 w-6 h-6" /> : <XCircle className="text-red-400 w-6 h-6" />}
                      <div>
                        <p className={`font-semibold ${config.question_channel_id ? 'text-green-400' : 'text-red-400'}`}>
                          {config.question_channel_id ? 'Đang hoạt động' : 'Thiếu thông tin'}
                        </p>
                        <p className="text-xs text-text-muted mt-1">Kênh phỏng vấn: {config.question_channel_id || 'Chưa thiết lập'}</p>
                      </div>
                    </div>

                    {/* Status 3 */}
                    <div className={`p-4 rounded-xl border ${config.officer_role_id && config.member_role_id ? 'bg-green-500/10 border-green-500/30' : 'bg-yellow-500/10 border-yellow-500/30'} flex items-center gap-4 transition-colors`}>
                      {config.officer_role_id && config.member_role_id ? <CheckCircle2 className="text-green-400 w-6 h-6" /> : <AlertTriangle className="text-yellow-400 w-6 h-6" />}
                      <div>
                        <p className={`font-semibold ${config.officer_role_id && config.member_role_id ? 'text-green-400' : 'text-yellow-400'}`}>
                          {config.officer_role_id && config.member_role_id ? 'Đang hoạt động' : 'Thiếu thông tin (Roles)'}
                        </p>
                        <p className="text-xs text-text-muted mt-1">
                          Officer: {config.officer_role_id ? '✅' : '❌'} | Member: {config.member_role_id ? '✅' : '❌'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center animate-fade-in opacity-50">
              <Package className="w-24 h-24 text-text-muted mb-6" />
              <h2 className="text-2xl font-bold text-white mb-2">Tính Năng Đang Phát Triển</h2>
              <p className="text-text-muted max-w-md">
                Giao diện quản lý cấu hình cho {MODULES.find(m => m.id === activeModule)?.name} hiện đang được xây dựng. Vui lòng quay lại sau!
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
