import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { loginWithGoogle } from '../lib/firebase';
import { Zap, TrendingUp, ShieldCheck, BarChart2 } from 'lucide-react';

const features = [
    {
        icon: <Zap className="w-5 h-5 text-emerald-400" />,
        title: 'Otimização ILP (Knapsack)',
        desc: 'Algoritmo de Programação Linear Inteira que resolve o problema da escalação em milissegundos.',
    },
    {
        icon: <TrendingUp className="w-5 h-5 text-amber-400" />,
        title: 'Modo Valorização',
        desc: 'Maximiza seu patrimônio de Cartoletas com base em MPV e valorização esperada E[V].',
    },
    {
        icon: <ShieldCheck className="w-5 h-5 text-indigo-400" />,
        title: 'Reserva de Luxo 2026',
        desc: 'Constraint Big-M que escolhe o reserva que mais protege contra scouts negativos dos titulares.',
    },
    {
        icon: <BarChart2 className="w-5 h-5 text-pink-400" />,
        title: 'Prova Real',
        desc: 'Auditoria histórica que compara E[P] previsto com pontuação real de cada rodada.',
    },
];

export default function Login() {
    const { user } = useAuth();

    if (user) {
        return <Navigate to="/" replace />;
    }

    return (
        <div className="min-h-screen bg-slate-950 flex flex-col lg:flex-row font-sans">

            {/* Left panel — storytelling */}
            <div className="relative flex-1 flex flex-col justify-between overflow-hidden p-8 lg:p-12 bg-gradient-to-br from-slate-900 via-emerald-950/30 to-slate-950 border-r border-white/5">

                {/* Glow backdrop */}
                <div className="pointer-events-none absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-emerald-600/10 blur-[120px]" />
                <div className="pointer-events-none absolute top-1/2 -right-60 w-[500px] h-[500px] rounded-full bg-indigo-600/10 blur-[120px]" />

                {/* Logo */}
                <div className="relative z-10 flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-emerald-500 flex items-center justify-center shadow-lg shadow-emerald-500/30">
                        <Zap className="w-5 h-5 text-slate-950" />
                    </div>
                    <span className="text-white font-bold text-xl tracking-tight">
                        Cartolitos <span className="text-emerald-400 font-light">Optimiser</span>
                    </span>
                </div>

                {/* Hero text */}
                <div className="relative z-10 my-8 lg:my-0">
                    <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-3 py-1 mb-6">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-emerald-400 text-xs font-medium uppercase tracking-wider">Motor Matemático Ativo</span>
                    </div>

                    <h1 className="text-4xl lg:text-5xl font-extrabold text-white leading-tight mb-4">
                        A Escalação{' '}
                        <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                            Ótima
                        </span>{' '}
                        <br className="hidden lg:block" />
                        do seu Cartola
                    </h1>

                    <p className="text-slate-400 text-base leading-relaxed max-w-md">
                        Não é feeling. É matemática. O Cartolitos usa Programação Linear Inteira (ILP) para montar a melhor escalação possível com base em{' '}
                        <span className="text-white">pontuação esperada</span>,{' '}
                        <span className="text-white">valorização</span> e{' '}
                        <span className="text-white">proteção por reserva</span>.
                    </p>

                    {/* Stats row */}
                    <div className="flex gap-6 mt-8">
                        {[
                            { label: 'Algoritmo', value: 'ILP/PuLP' },
                            { label: 'Modo Padrão', value: 'Mitagem' },
                            { label: 'Rodada 1 Rule', value: '54%' },
                        ].map((s) => (
                            <div key={s.label}>
                                <p className="text-2xl font-bold text-white">{s.value}</p>
                                <p className="text-xs text-slate-500 uppercase tracking-wide">{s.label}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Feature grid */}
                <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {features.map((f) => (
                        <div
                            key={f.title}
                            className="bg-slate-900/60 border border-white/5 rounded-xl p-4 hover:border-white/10 transition-colors"
                        >
                            <div className="mb-2">{f.icon}</div>
                            <p className="text-sm font-semibold text-white mb-1">{f.title}</p>
                            <p className="text-xs text-slate-500 leading-relaxed">{f.desc}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Right panel — auth */}
            <div className="flex items-center justify-center w-full lg:w-[420px] xl:w-[480px] p-8 lg:p-12 flex-shrink-0">
                <div className="w-full max-w-sm">

                    <div className="mb-8">
                        <h2 className="text-2xl font-bold text-white mb-2">Acesse o Motor</h2>
                        <p className="text-slate-400 text-sm">
                            Entre com sua conta Google para acessar o Optimiser e salvar suas escalações.
                        </p>
                    </div>

                    <button
                        onClick={loginWithGoogle}
                        className="w-full group flex items-center justify-center gap-3 px-4 py-3.5 rounded-xl bg-white hover:bg-slate-50 text-slate-900 font-semibold text-sm transition-all duration-200 shadow-lg shadow-black/20 hover:shadow-xl hover:shadow-black/30 hover:-translate-y-0.5"
                    >
                        <img
                            src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
                            alt="Google"
                            className="w-5 h-5"
                        />
                        Entrar com Google
                    </button>

                    <div className="flex items-center gap-3 my-6">
                        <div className="flex-1 h-px bg-white/5" />
                        <span className="text-xs text-slate-600">acesso restrito</span>
                        <div className="flex-1 h-px bg-white/5" />
                    </div>

                    <p className="text-center text-xs text-slate-600 leading-relaxed">
                        Apenas usuários convidados têm acesso à Engine ILP. <br />
                        Seus dados são gerenciados pelo{' '}
                        <span className="text-slate-400">Firebase Auth</span> e nunca compartilhados.
                    </p>

                    {/* Decorative score preview */}
                    <div className="mt-10 bg-slate-900/80 border border-white/5 rounded-xl p-4">
                        <p className="text-xs text-slate-500 uppercase tracking-wider mb-3 font-medium">Preview — última escalação</p>
                        <div className="grid grid-cols-3 gap-3 text-center">
                            {[
                                { label: 'E[P] Previsto', val: '86.4', color: 'text-emerald-400' },
                                { label: 'ROI (C$)', val: '+14.2', color: 'text-amber-400' },
                                { label: 'Proteção', val: '9.1/10', color: 'text-indigo-400' },
                            ].map((m) => (
                                <div key={m.label} className="bg-slate-800/60 rounded-lg p-3">
                                    <p className={`text-lg font-bold ${m.color}`}>{m.val}</p>
                                    <p className="text-[10px] text-slate-500 mt-1">{m.label}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}
