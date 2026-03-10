import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';
import { useNavigate } from 'react-router-dom';
import {
    LogOut, BarChart2, Zap, TrendingUp, ShieldCheck, History, Cpu, User, Mail, ArrowLeft,
} from 'lucide-react';

const statCards = [
    { label: 'Escalações Geradas', value: '—', icon: <Cpu className="w-4 h-4" />, color: 'emerald', desc: 'Total histórico' },
    { label: 'Rodadas Auditadas', value: '—', icon: <History className="w-4 h-4" />, color: 'indigo', desc: 'Prova Real ativa' },
    { label: 'Melhor E[P]', value: '—', icon: <BarChart2 className="w-4 h-4" />, color: 'amber', desc: 'Pontos previstos' },
    { label: 'ROI Acumulado', value: '—', icon: <TrendingUp className="w-4 h-4" />, color: 'pink', desc: 'Em Cartoletas (C$)' },
];

const colorMap: Record<string, string> = {
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    indigo: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    pink: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
};

const capabilities = [
    { icon: <Zap className="w-4 h-4 text-emerald-400" />, label: 'Modo Mitagem', desc: 'Maximiza E[P] por Rodada' },
    { icon: <TrendingUp className="w-4 h-4 text-amber-400" />, label: 'Modo Valorização', desc: 'Maximiza E[V] e patrimônio' },
    { icon: <ShieldCheck className="w-4 h-4 text-indigo-400" />, label: 'Reserva de Luxo 2026', desc: 'Proteção via constraint Big-M' },
    { icon: <BarChart2 className="w-4 h-4 text-pink-400" />, label: 'Context Multiplier', desc: 'Bônus Mando (+10%) e FDR (+25%)' },
];

export default function Profile() {
    const { user } = useAuth();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await supabase.auth.signOut();
        navigate('/login');
    };

    const initials = user?.user_metadata?.full_name
        ? user.user_metadata.full_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()
        : '??';

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 font-sans">
            {/* Header */}
            <header className="border-b border-white/5 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
                    <button
                        onClick={() => navigate('/optimiser')}
                        className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Voltar ao Optimiser
                    </button>
                    <button
                        onClick={handleLogout}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-all"
                    >
                        <LogOut className="w-4 h-4" />
                        Sair
                    </button>
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-4 py-10">

                {/* Hero do perfil */}
                <div className="relative bg-gradient-to-br from-slate-900 via-emerald-950/20 to-slate-900 border border-white/5 rounded-2xl p-8 mb-8 overflow-hidden">
                    <div className="pointer-events-none absolute -top-20 -right-20 w-80 h-80 rounded-full bg-emerald-600/10 blur-[80px]" />

                    <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center gap-6">
                        {/* Avatar */}
                        <div className="relative flex-shrink-0">
                            {user?.user_metadata?.avatar_url ? (
                                <img
                                    src={user.user_metadata.avatar_url}
                                    alt="Avatar"
                                    className="w-20 h-20 rounded-2xl border-2 border-emerald-500/30 shadow-lg shadow-emerald-500/10"
                                />
                            ) : (
                                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-500/30 to-indigo-500/30 border border-white/10 flex items-center justify-center">
                                    <span className="text-2xl font-bold text-white">{initials}</span>
                                </div>
                            )}
                            <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-slate-900" />
                        </div>

                        {/* Info */}
                        <div className="flex-1">
                            <div className="flex items-center gap-3 mb-1">
                                <h1 className="text-2xl font-bold text-white">{user?.user_metadata?.full_name || 'Cartoleiro'}</h1>
                                <span className="text-xs bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full font-medium">
                                    Engine Access
                                </span>
                            </div>
                            <div className="flex flex-col sm:flex-row gap-3 mt-2">
                                <div className="flex items-center gap-2 text-slate-400 text-sm">
                                    <Mail className="w-3.5 h-3.5" />
                                    {user?.email}
                                </div>
                                <div className="flex items-center gap-2 text-slate-400 text-sm">
                                    <User className="w-3.5 h-3.5" />
                                    UID: <span className="font-mono text-slate-500 text-xs">{user?.id?.slice(0, 12)}...</span>
                                </div>
                            </div>
                        </div>

                        {/* Acesso rápido ao optimiser */}
                        <button
                            onClick={() => navigate('/optimiser')}
                            className="flex-shrink-0 flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-4 py-2.5 rounded-xl text-sm transition-all shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30 hover:-translate-y-0.5"
                        >
                            <Zap className="w-4 h-4" />
                            Abrir Optimiser
                        </button>
                    </div>
                </div>

                {/* Estatísticas */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    {statCards.map((s) => (
                        <div
                            key={s.label}
                            className="bg-slate-900/60 border border-white/5 rounded-xl p-5 hover:border-white/10 transition-colors"
                        >
                            <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg border text-xs font-medium mb-3 ${colorMap[s.color]}`}>
                                {s.icon}
                                {s.label}
                            </div>
                            <p className="text-3xl font-bold text-white mb-1">{s.value}</p>
                            <p className="text-xs text-slate-500">{s.desc}</p>
                        </div>
                    ))}
                </div>

                {/* Grid inferior */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                    {/* Funcionalidades ativas */}
                    <div className="bg-slate-900/60 border border-white/5 rounded-xl p-6">
                        <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
                            Capacidades do Motor
                        </h2>
                        <div className="space-y-3">
                            {capabilities.map((c) => (
                                <div key={c.label} className="flex items-start gap-3">
                                    <div className="mt-0.5 flex-shrink-0">{c.icon}</div>
                                    <div>
                                        <p className="text-sm font-medium text-white">{c.label}</p>
                                        <p className="text-xs text-slate-500">{c.desc}</p>
                                    </div>
                                    <div className="ml-auto flex-shrink-0 w-2 h-2 rounded-full bg-emerald-500 mt-1.5" />
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Histórico rápido / atalhos */}
                    <div className="bg-slate-900/60 border border-white/5 rounded-xl p-6">
                        <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
                            Atalhos Rápidos
                        </h2>
                        <div className="space-y-3">
                            {[
                                { label: 'Ver Prova Real (Auditoria)', sub: 'Histórico de previsão vs realidade', path: '/dashboard', icon: <History className="w-4 h-4 text-indigo-400" /> },
                                { label: 'Abrir Engine (Optimiser)', sub: 'Gerar escalação com ILP', path: '/optimiser', icon: <Cpu className="w-4 h-4 text-emerald-400" /> },
                            ].map((l) => (
                                <button
                                    key={l.label}
                                    onClick={() => navigate(l.path)}
                                    className="w-full flex items-center gap-4 p-4 bg-slate-800/50 hover:bg-slate-800 border border-white/5 hover:border-white/10 rounded-xl text-left transition-all group"
                                >
                                    <div className="flex-shrink-0">{l.icon}</div>
                                    <div>
                                        <p className="text-sm font-medium text-white group-hover:text-emerald-400 transition-colors">{l.label}</p>
                                        <p className="text-xs text-slate-500">{l.sub}</p>
                                    </div>
                                </button>
                            ))}

                            <div className="h-px bg-white/5 my-2" />

                            <button
                                onClick={handleLogout}
                                className="w-full flex items-center gap-4 p-4 bg-red-500/5 hover:bg-red-500/10 border border-red-500/10 hover:border-red-500/20 rounded-xl text-left transition-all group"
                            >
                                <LogOut className="w-4 h-4 text-red-400 flex-shrink-0" />
                                <div>
                                    <p className="text-sm font-medium text-red-400">Desconectar conta</p>
                                    <p className="text-xs text-slate-500">Sair do Firebase Auth</p>
                                </div>
                            </button>
                        </div>
                    </div>

                </div>
            </main>
        </div>
    );
}
