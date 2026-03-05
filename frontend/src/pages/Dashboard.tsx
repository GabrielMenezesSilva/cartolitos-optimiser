import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { fetchLineupHistory } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { LogOut, History, ShieldAlert } from 'lucide-react';
import { logout } from '../lib/firebase';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
    const { user, token } = useAuth();
    const navigate = useNavigate();
    const [history, setHistory] = useState<any[]>([]);

    useEffect(() => {
        async function loadHistory() {
            if (token) {
                try {
                    const data = await fetchLineupHistory(token);
                    if (data && data.lineups) {
                        setHistory(data.lineups);
                    }
                } catch (error) {
                    console.error("Erro ao puxar história", error);
                }
            }
        }
        loadHistory();
    }, [token]);

    const handleLogout = async () => {
        await logout();
    };

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-emerald-500/30">
            <header className="border-b border-white/10 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <h1 className="text-xl font-bold tracking-tight text-white cursor-pointer" onClick={() => navigate('/')}>
                            Cartolitos <span className="text-emerald-500 font-light">Dashboard</span>
                        </h1>
                        <nav className="hidden md:flex items-center gap-4 ml-6 pl-6 border-l border-white/10">
                            <button onClick={() => navigate('/optimiser')} className="text-sm font-medium text-slate-400 hover:text-white transition-colors">
                                Optimiser Engine
                            </button>
                            <button className="text-sm font-medium text-emerald-400 border-b-2 border-emerald-500 py-5">
                                Prova Real (Histórico)
                            </button>
                        </nav>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-3 mr-4">
                            <img src={user?.photoURL || ''} alt="Avatar" className="w-8 h-8 rounded-full border border-white/10" />
                            <div className="hidden sm:block text-sm">
                                <p className="font-semibold text-white leading-none mb-1">{user?.displayName}</p>
                                <p className="text-xs text-slate-400 leading-none">{user?.email}</p>
                            </div>
                        </div>
                        <button onClick={handleLogout} className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-slate-400 transition-colors">
                            <LogOut className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 py-8">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
                        <History className="w-6 h-6 text-emerald-500" />
                        Auditoria de Resultados (Prova Real)
                    </h2>
                    <p className="text-slate-400">Acompanhe a precisão do Cartolitos Optimiser comparando a pontuação prevista (Target) contra a pontuação real alcançada por nossa squad.</p>
                </div>

                <div className="bg-slate-900 border border-white/10 rounded-2xl p-6 mb-8">
                    <div className="h-[400px] w-full">
                        {history.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={history} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                    <XAxis dataKey="round_id" stroke="#94a3b8" tickFormatter={(v) => `Rodada ${v}`} />
                                    <YAxis stroke="#94a3b8" />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc' }}
                                        itemStyle={{ color: '#10b981' }}
                                    />
                                    <Legend />
                                    <Line type="monotone" dataKey="expected_points" name="Previsto (E[P])" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                                    <Line type="monotone" dataKey="real_points" name="Realizado" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-slate-500">
                                <ShieldAlert className="w-12 h-12 mb-4 text-slate-600" />
                                <p>Nenhuma escalação auditada ainda.</p>
                                <p className="text-sm mt-2">Gere e salve escalações no Optimiser para iniciar a Prova Real.</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Historico Listagem detalhada */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {history.map((item, idx) => (
                        <div key={idx} className="bg-slate-900 border border-white/10 rounded-xl p-5 hover:border-emerald-500/30 transition-colors">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="font-bold text-white">Rodada {item.round_id}</h3>
                                <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-1 rounded-md font-mono">
                                    Delta: {item.real_points ? (item.real_points - item.expected_points).toFixed(2) : 'Pendente'}
                                </span>
                            </div>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between text-slate-400">
                                    <span>Previsão Matemática (E[P])</span>
                                    <span className="font-mono text-indigo-400">{item.expected_points?.toFixed(2)} pts</span>
                                </div>
                                <div className="flex justify-between text-slate-400">
                                    <span>Custo Planejado (C$)</span>
                                    <span className="font-mono text-slate-300">{item.cost?.toFixed(2)} C$</span>
                                </div>
                                <div className="h-px bg-white/5 my-2"></div>
                                <div className="flex justify-between text-white font-medium">
                                    <span>Resultado Real</span>
                                    <span className="font-mono text-emerald-400">{item.real_points ? `${item.real_points.toFixed(2)} pts` : '--'}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </main>
        </div>
    );
}
