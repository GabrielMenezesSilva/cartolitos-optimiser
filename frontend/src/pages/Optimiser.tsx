import { useState, useEffect, useRef } from 'react';
import { Cpu, ShieldAlert, Zap, TrendingUp, Settings2, Save, User, CheckCircle, XCircle, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { optimizeLineup, saveLineup } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Campinho } from '../components/Campinho';
import { motion, AnimatePresence } from 'framer-motion';

// Toast simples
type Toast = { id: number; type: 'success' | 'error'; message: string };

export default function Optimiser() {
  const [loading, setLoading] = useState(false);
  const [budget, setBudget] = useState(140);
  const [ousadia, setOusadia] = useState(5);
  const [modo, setModo] = useState('mitagem');
  const [result, setResult] = useState<any>(null);
  const [panicMode, setPanicMode] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastCounter = useRef(0);

  const { token, user } = useAuth();
  const navigate = useNavigate();

  const addToast = (type: 'success' | 'error', message: string) => {
    const id = ++toastCounter.current;
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  };

  const handleOptimize = async () => {
    setLoading(true);
    setResult(null);
    try {
      const data = await optimizeLineup(budget, ousadia, modo, token);
      setResult(data);
    } catch (e: any) {
      console.error('Error optimizing:', e);
      const msg = e?.response?.data?.detail ?? 'Falha ao rodar o otimizador. Tente novamente.';
      addToast('error', msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!result || !token) return;
    setSaving(true);
    try {
      const weekNumber = Math.ceil((new Date().getDate() + new Date().getDay()) / 7);
      const lineup = result.results?.lineup?.filter((p: any) => p.is_titular) || [];
      const reserves = result.results?.lineup?.filter((p: any) => !p.is_titular) || [];
      await saveLineup(
        token,
        weekNumber,
        result.meta?.total_expected_points ?? 0,
        result.meta?.total_cost ?? 0,
        { lineup, reserves },
        modo
      );
      addToast('success', 'Escalação salva no histórico com sucesso!');
    } catch (e) {
      console.error('Falha ao salvar a escalação', e);
      addToast('error', 'Falha ao salvar a escalação. Tente novamente.');
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (panicMode) {
      interval = setInterval(() => {
        handleOptimize();
      }, 30000);
    }
    return () => { if (interval) clearInterval(interval); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [panicMode, budget, ousadia, modo, token]);

  return (
    <div className="flex flex-col h-full w-full">
      {/* Toasts */}
      <div className="fixed top-4 right-4 z-[99] flex flex-col gap-2 pointer-events-none">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, scale: 0.8, x: 20 }}
              animate={{ opacity: 1, scale: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.8, x: 20 }}
              className={`flex items-center gap-3 px-4 py-3 rounded-2xl border text-sm font-medium shadow-2xl pointer-events-auto backdrop-blur-xl
                ${t.type === 'success'
                  ? 'bg-emerald-950/80 border-emerald-500/30 text-emerald-300'
                  : 'bg-red-950/80 border-red-500/30 text-red-300'}`}
            >
              {t.type === 'success' ? <CheckCircle className="w-5 h-5 flex-shrink-0" /> : <XCircle className="w-5 h-5 flex-shrink-0" />}
              {t.message}
              <button onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))} className="ml-2 opacity-50 hover:opacity-100 transition-opacity">
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Page Header */}
      <div className="w-full px-6 py-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800/50 bg-[#0f172a]/30 backdrop-blur-md sticky top-0 z-30">
        <div>
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-100 to-teal-100 tracking-tight">
            Motor de Escalação
          </h1>
          <p className="text-sm text-slate-400 mt-1">Otimize seu elenco utilizando algoritmos avançados e Inteligência Artificial.</p>
        </div>

        <div className="flex items-center gap-3">
          {user && (
            <button
              onClick={() => navigate('/profile')}
              className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 transition-colors shadow-sm"
              title="Minha Conta"
            >
              {user.user_metadata?.avatar_url ? (
                <img src={user.user_metadata.avatar_url} alt="avatar" className="w-7 h-7 rounded-full border border-slate-600" />
              ) : (
                <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center">
                  <User className="w-4 h-4 text-emerald-400" />
                </div>
              )}
              <span className="hidden sm:block text-sm font-medium text-slate-300 max-w-[120px] truncate">
                {user.user_metadata?.full_name || user.email}
              </span>
            </button>
          )}

          <button
            onClick={() => setPanicMode(!panicMode)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all shadow-lg border
              ${panicMode
                ? 'bg-red-500/20 text-red-400 border-red-500/50 shadow-red-500/20 animate-pulse'
                : 'bg-slate-800/50 hover:bg-slate-800 text-slate-300 border-slate-700/50 hover:border-slate-600'}`}
          >
            <ShieldAlert className="w-4 h-4" />
            <span className="hidden sm:inline">{panicMode ? 'Panic Mode Ativo' : 'Panic Button'}</span>
          </button>
        </div>
      </div>

      {/* Dashboard Grid */}
      <div className="flex-1 p-6 h-full overflow-y-auto">
        <div className="max-w-[1600px] mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 pb-20">

          {/* Lado Esquerdo: Controles */}
          <aside className="col-span-1 lg:col-span-3 space-y-6">
            <div className="glass-panel rounded-3xl p-6">
              <h2 className="flex items-center gap-3 font-bold text-white mb-6 text-lg tracking-tight">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                  <Settings2 className="w-4 h-4 text-emerald-400" />
                </div>
                Parâmetros
              </h2>

              <div className="space-y-8">
                {/* Objetivo */}
                <div>
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-3">
                    Modo Operacional
                  </label>
                  <div className="p-1 bg-slate-900 rounded-xl flex gap-1 border border-slate-800/80 shadow-inner">
                    <button
                      onClick={() => setModo('mitagem')}
                      className={`flex-1 py-2.5 px-3 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all
                        ${modo === 'mitagem'
                          ? 'bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md'
                          : 'text-slate-400 hover:text-slate-200'}`}
                    >
                      <Zap className="w-4 h-4" /> Mitagem
                    </button>
                    <button
                      onClick={() => setModo('valorizacao')}
                      className={`flex-1 py-2.5 px-3 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all
                        ${modo === 'valorizacao'
                          ? 'bg-gradient-to-br from-amber-500 to-orange-600 text-white shadow-md'
                          : 'text-slate-400 hover:text-slate-200'}`}
                    >
                      <TrendingUp className="w-4 h-4" /> Patrimônio
                    </button>
                  </div>
                </div>

                {/* Orçamento */}
                <div>
                  <div className="flex justify-between items-end mb-3">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                      Orçamento Máx.
                    </label>
                    <div className="bg-slate-900 border border-slate-800 px-3 py-1 rounded-lg">
                      <span className="text-lg font-mono font-bold text-emerald-400">C$ {budget.toFixed(1)}</span>
                    </div>
                  </div>
                  <input
                    type="range"
                    min="80"
                    max="200"
                    value={budget}
                    onChange={(e) => setBudget(Number(e.target.value))}
                    className="w-full accent-emerald-500 block h-1.5 bg-slate-800 rounded-full appearance-none cursor-pointer hover:bg-slate-700 transition-colors"
                  />
                </div>

                {/* Ousadia */}
                <div>
                  <div className="flex justify-between items-end mb-3">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                      Nível de Ousadia
                    </label>
                    <div className="bg-slate-900 border border-slate-800 px-3 py-1 rounded-lg">
                      <span className="text-lg font-mono font-bold text-indigo-400">{ousadia}<span className="text-xs text-slate-500 font-sans">/10</span></span>
                    </div>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={ousadia}
                    onChange={(e) => setOusadia(Number(e.target.value))}
                    className="w-full accent-indigo-500 block h-1.5 bg-slate-800 rounded-full appearance-none cursor-pointer hover:bg-slate-700 transition-colors"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 mt-2 font-medium uppercase tracking-wider">
                    <span>Conservador</span>
                    <span>Arrojado</span>
                  </div>
                </div>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleOptimize}
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold py-4 rounded-xl shadow-xl shadow-emerald-500/20 transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed border border-emerald-400/30"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Processando Matriz...
                    </span>
                  ) : (
                    <><Cpu className="w-5 h-5" /> Gerar Escalação Ideal</>
                  )}
                </motion.button>
              </div>
            </div>

            {/* Call to action secondary if needed */}
            {result && user && (
              <motion.button
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSave}
                disabled={saving}
                className="w-full glass-panel text-slate-300 hover:text-white py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all mt-4 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="w-5 h-5 text-indigo-400" />
                {saving ? 'Gravando...' : 'Salvar no Histórico'}
              </motion.button>
            )}
          </aside>

          {/* Centro: O Campo */}
          <section className="col-span-1 lg:col-span-6 flex flex-col border border-slate-800/60 rounded-3xl bg-[#0a0f1d] shadow-2xl relative min-h-[600px] xl:min-h-[750px]">
            {/* Inner background glow */}
            <div className="absolute inset-0 bg-emerald-500/5 mix-blend-screen pointer-events-none" />
            <Campinho loading={loading} result={result} />
          </section>

          {/* Lado Direito: Dashboards Analíticos */}
          <aside className="col-span-1 lg:col-span-3 space-y-6">
            <div className="glass-panel rounded-3xl p-6 h-full flex flex-col relative overflow-hidden">
              {/* Background gradient decorative */}
              <div className="absolute top-0 right-0 -mr-16 -mt-16 w-32 h-32 bg-indigo-500/10 blur-3xl rounded-full" />

              <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-3 tracking-tight">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                  <Zap className="w-4 h-4 text-indigo-400" />
                </div>
                Indicadores Chave
              </h3>

              {!result ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center opacity-50 space-y-4 py-12">
                  <div className="w-16 h-16 rounded-full border border-dashed border-slate-600 flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-slate-500" />
                  </div>
                  <p className="text-sm font-medium text-slate-400 max-w-[200px]">Execute a simulação para visualizar as justificativas estatísticas.</p>
                </div>
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="space-y-6 flex-1 flex flex-col"
                >
                  {/* Totals */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 flex flex-col items-center justify-center text-center shadow-lg shadow-black/20">
                      <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1.5">Investimento</p>
                      <h3 className="text-2xl font-mono font-black text-white">C$ {(result.meta?.total_cost ?? 0).toFixed(1)}</h3>
                    </div>
                    <div className="bg-emerald-950/20 border border-emerald-500/20 rounded-2xl p-4 flex flex-col items-center justify-center text-center shadow-lg shadow-emerald-900/10">
                      <p className="text-[10px] text-emerald-500/80 font-bold uppercase tracking-widest mb-1.5">Retorno (E[P])</p>
                      <h3 className="text-2xl font-mono font-black text-emerald-400">{(result.meta?.total_expected_points ?? 0).toFixed(1)}</h3>
                    </div>
                  </div>

                  {/* Highlights */}
                  <div className="flex-1 flex flex-col gap-3 min-h-0">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-800/50">
                      <h4 className="text-xs font-bold uppercase tracking-widest text-slate-400">
                        Destaques do Algoritmo
                      </h4>
                    </div>

                    <div className="overflow-y-auto pr-2 space-y-3 flex-1 custom-scrollbar">
                      {[...(result.results?.lineup?.filter((p: any) => p.is_titular) ?? [])]
                        .sort((a: any, b: any) => (b.pontos_esperados ?? 0) - (a.pontos_esperados ?? 0))
                        .slice(0, 5)
                        .map((p: any, i: number) => (
                          <div key={i} className="group bg-slate-900/40 hover:bg-slate-800/80 border border-slate-800/80 hover:border-indigo-500/30 p-3.5 rounded-2xl transition-colors">
                            <div className="flex items-start justify-between gap-2 mb-2">
                              <div>
                                <span className="text-sm font-bold text-white block leading-tight">{p.nome ?? '—'}</span>
                                <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">{p.pos_nome}</span>
                              </div>
                              <div className="text-right">
                                <span className="block text-sm font-mono font-black text-emerald-400">{(p.pontos_esperados ?? 0).toFixed(1)}pt</span>
                                <span className="block text-[10px] font-mono text-slate-500">C$ {(p.preco ?? 0).toFixed(1)}</span>
                              </div>
                            </div>
                            <p className="text-xs text-slate-400 leading-relaxed bg-black/20 p-2.5 rounded-xl border border-white/5 border-l-2 border-l-indigo-500/50">
                              {p.reason ?? "Métrica avançada indica superioridade neste confronto."}
                            </p>
                          </div>
                        ))}

                      {/* Reservas */}
                      <div className="mt-6">
                        <h4 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3 pb-2 border-b border-slate-800/50">
                          Banco de Reservas
                        </h4>
                        <div className="space-y-2">
                          {(result.results?.lineup?.filter((p: any) => !p.is_titular) ?? []).map((p: any, i: number) => (
                            <div key={`res-${i}`} className="bg-slate-900/30 p-2.5 rounded-xl border border-slate-800/50 flex gap-3 items-center">
                              <div className="w-8 h-8 rounded-full border border-slate-700 bg-slate-800 flex items-center justify-center overflow-hidden flex-shrink-0">
                                {p.foto ? (
                                  <img src={p.foto.replace('FORMATO', '140x140')} alt={p.nome} className="w-full h-full object-cover" />
                                ) : (
                                  <User className="w-4 h-4 text-slate-500" />
                                )}
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-xs text-slate-200 font-bold truncate">{p.nome}</p>
                                <div className="flex gap-2 text-[10px] font-mono text-slate-500">
                                  <span>C$ {(p.preco ?? 0).toFixed(1)}</span>
                                  <span>•</span>
                                  <span className="text-emerald-500">{(p.pontos_esperados ?? 0).toFixed(1)}pt</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </aside>

        </div>
      </div>

    </div>
  );
}
