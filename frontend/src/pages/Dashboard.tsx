import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { fetchLineupHistory } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { History, ShieldAlert } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Dashboard() {
    const { token } = useAuth();
    const [history, setHistory] = useState<any[]>([]);
    const [loadError, setLoadError] = useState<string | null>(null);

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
                    setLoadError("Não foi possível carregar o histórico. Tente novamente.");
                }
            }
        }
        loadHistory();
    }, [token]);

    const pageVariants = {
        initial: { opacity: 0, y: 10 },
        animate: { opacity: 1, y: 0, transition: { duration: 0.4 } },
        exit: { opacity: 0, y: -10, transition: { duration: 0.3 } }
    };

    return (
        <motion.div
            className="text-slate-200 font-sans"
            initial="initial"
            animate="animate"
            exit="exit"
            variants={pageVariants}
        >
            <div className="mb-8">
                <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
                    <History className="w-6 h-6 text-emerald-500" />
                    Auditoria de Resultados (Prova Real)
                </h2>
                <p className="text-slate-400">Acompanhe a precisão do Cartolitos Optimiser comparando a pontuação prevista (Target) contra a pontuação real alcançada por nossa squad.</p>
            </div>

            {/* Error Banner */}
            {loadError && (
                <div className="mb-6 flex items-center gap-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl px-4 py-3 text-sm">
                    <ShieldAlert className="w-4 h-4 flex-shrink-0" />
                    {loadError}
                </div>
            )}

            <div className="glass-panel p-6 mb-8">
                <div className="h-[400px] w-full">
                    {history.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={history} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                <XAxis dataKey="round_id" stroke="#94a3b8" tickFormatter={(v) => `Rodada ${v}`} />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#020617', borderColor: '#1e293b', color: '#f8fafc', borderRadius: '0.75rem' }}
                                    itemStyle={{ color: '#10b981' }}
                                />
                                <Legend />
                                <Line type="monotone" dataKey="expected_points" name="Previsto (E[P])" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                                <Line type="monotone" dataKey="real_points" name="Realizado" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-slate-500">
                            <ShieldAlert className="w-12 h-12 mb-4 text-slate-600/50" />
                            <p className="font-medium text-slate-400">Nenhuma escalação auditada ainda.</p>
                            <p className="text-sm mt-2 text-slate-500">Gere e salve escalações no Optimiser para iniciar a Prova Real.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Historico Listagem detalhada */}
            {history.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {history.map((item, idx) => (
                        <motion.div
                            key={idx}
                            className="glass-panel p-5 hover:border-emerald-500/30 transition-colors"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: idx * 0.05 }}
                        >
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="font-bold text-white">Rodada {item.round_id}</h3>
                                <span className={`text-xs px-2 py-1 rounded-md font-mono ${item.real_points ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-700/50 text-slate-400'}`}>
                                    {item.real_points
                                        ? `Delta: ${(item.real_points - (item.expected_points ?? 0)).toFixed(2)}`
                                        : 'Pendente'}
                                </span>
                            </div>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between text-slate-400">
                                    <span>Previsão Matemática (E[P])</span>
                                    <span className="font-mono text-indigo-400">{(item.expected_points ?? 0).toFixed(2)} pts</span>
                                </div>
                                <div className="flex justify-between text-slate-400">
                                    <span>Custo Planejado (C$)</span>
                                    <span className="font-mono text-slate-300">{(item.cost ?? 0).toFixed(2)} C$</span>
                                </div>
                                <div className="h-px bg-white/5 my-2"></div>
                                <div className="flex justify-between text-white font-medium">
                                    <span>Resultado Real</span>
                                    <span className="font-mono text-emerald-400">{item.real_points ? `${item.real_points.toFixed(2)} pts` : '--'}</span>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}
        </motion.div>
    );
}
