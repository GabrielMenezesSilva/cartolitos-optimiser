import { useState, useEffect, useRef } from 'react';
import { Cpu, ShieldAlert, Zap, TrendingUp, Settings2, Save, User, CheckCircle, XCircle, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { optimizeLineup, saveLineup } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

// Toast simples inline (sem lib externa)
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
      // round_id derivado da data atual (semana do ano) como fallback real
      const weekNumber = Math.ceil((new Date().getDate() + new Date().getDay()) / 7);
      await saveLineup(
        token,
        weekNumber,
        result.total_expected_points ?? 0,
        result.total_cost ?? 0,
        { lineup: result.lineup, reserves: result.reserves },
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

  // Panic Button — re-otimiza a cada 30s
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
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-emerald-500/30">

      {/* Toast container */}
      <div className="fixed top-4 right-4 z-[99] flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-sm font-medium shadow-lg pointer-events-auto transition-all
              ${t.type === 'success'
                ? 'bg-emerald-950 border-emerald-500/30 text-emerald-300'
                : 'bg-red-950 border-red-500/30 text-red-300'}`}
          >
            {t.type === 'success'
              ? <CheckCircle className="w-4 h-4 flex-shrink-0" />
              : <XCircle className="w-4 h-4 flex-shrink-0" />}
            {t.message}
            <button
              onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
              className="ml-2 opacity-50 hover:opacity-100"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>

      {/* Header */}
      <header className="border-b border-white/10 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center">
              <Cpu className="w-5 h-5 text-slate-950 font-bold" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">
              Cartolitos <span className="text-emerald-500 font-light">Optimiser</span>
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setPanicMode(!panicMode)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors border
                ${panicMode
                  ? 'bg-red-500 text-white border-red-500 animate-pulse'
                  : 'bg-red-500/10 hover:bg-red-500/20 text-red-500 border-red-500/20'}`}
            >
              <ShieldAlert className="w-4 h-4" />
              <span>{panicMode ? 'Panic Mode ON' : 'Panic Button'}</span>
            </button>
            {user && (
              <button
                onClick={() => navigate('/profile')}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                title="Minha Conta"
              >
                {user.photoURL ? (
                  <img src={user.photoURL} alt="avatar" className="w-6 h-6 rounded-full" />
                ) : (
                  <User className="w-4 h-4 text-slate-300" />
                )}
                <span className="hidden sm:block text-sm text-slate-300 max-w-[120px] truncate">
                  {user.displayName}
                </span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <main className="max-w-7xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">

        {/* Painel de Controle */}
        <aside className="col-span-1 lg:col-span-3 space-y-6">
          <div className="bg-slate-900/50 border border-white/5 rounded-xl p-5">
            <h2 className="flex items-center gap-2 font-semibold text-white mb-4">
              <Settings2 className="w-4 h-4 text-emerald-500" />
              Calibração do Motor
            </h2>

            <div className="space-y-5">
              <div>
                <label className="text-xs text-slate-400 font-medium uppercase tracking-wider block mb-2">
                  Modo de Operação
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setModo('mitagem')}
                    className={`py-2 px-3 rounded-lg text-sm font-medium border flex items-center justify-center gap-2 transition-all
                      ${modo === 'mitagem'
                        ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400'
                        : 'bg-slate-800 border-white/5 text-slate-400 hover:bg-slate-800/80'}`}
                  >
                    <Zap className="w-4 h-4" /> Mitagem
                  </button>
                  <button
                    onClick={() => setModo('valorizacao')}
                    className={`py-2 px-3 rounded-lg text-sm font-medium border flex items-center justify-center gap-2 transition-all
                      ${modo === 'valorizacao'
                        ? 'bg-amber-500/10 border-amber-500/50 text-amber-400'
                        : 'bg-slate-800 border-white/5 text-slate-400 hover:bg-slate-800/80'}`}
                  >
                    <TrendingUp className="w-4 h-4" /> Patrimônio
                  </button>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-xs text-slate-400 font-medium uppercase tracking-wider">
                    Orçamento (C$)
                  </label>
                  <span className="text-sm font-mono text-emerald-400">{budget.toFixed(1)}</span>
                </div>
                <input
                  type="range"
                  min="80"
                  max="200"
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                  className="w-full accent-emerald-500 block h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-xs text-slate-400 font-medium uppercase tracking-wider">
                    Slider de Ousadia
                  </label>
                  <span className="text-sm font-mono text-indigo-400">{ousadia}/10</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={ousadia}
                  onChange={(e) => setOusadia(Number(e.target.value))}
                  className="w-full accent-indigo-500 block h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                  <span>Seguro (Reg.)</span>
                  <span>Kamikaze (Imp.)</span>
                </div>
              </div>

              <button
                onClick={handleOptimize}
                disabled={loading}
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="animate-pulse">Calculando Rota...</span>
                ) : (
                  <><Cpu className="w-4 h-4" /> Processar Escalação</>
                )}
              </button>
            </div>
          </div>
        </aside>

        {/* Centro — Campo */}
        <section className="col-span-1 lg:col-span-6 flex items-center justify-center">
          <div className="w-full flex flex-col xl:aspect-[3/4] bg-emerald-800/10 border-2 border-emerald-500/10 rounded-2xl relative overflow-hidden">
            {/* Linhas do campo */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute inset-0 border-[8px] border-emerald-500/10 m-4 rounded-lg mix-blend-overlay" />
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-24 border-b-2 border-x-2 border-emerald-500/10 rounded-b-sm mix-blend-overlay" />
              <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-40 h-24 border-t-2 border-x-2 border-emerald-500/10 rounded-t-sm mix-blend-overlay" />
              <div className="absolute top-1/2 left-0 w-full border-t-2 border-emerald-500/10 mix-blend-overlay" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 rounded-full border-2 border-emerald-500/10 mix-blend-overlay" />
            </div>

            <div className="relative z-10 w-full h-full p-4 overflow-y-auto flex flex-col">
              {/* Field UI */}
              {!result && !loading && (
                <div className="h-full flex flex-col items-center justify-center text-center px-6 min-h-[400px]">
                  <div className="w-16 h-16 bg-slate-900/80 rounded-full flex items-center justify-center mx-auto mb-4 border border-white/5">
                    <Cpu className="w-8 h-8 text-emerald-500/50" />
                  </div>
                  <h3 className="text-lg font-medium text-white/70 mb-1">Motor Ocioso</h3>
                  <p className="text-sm text-slate-400">Configure os parâmetros e clique em processar para gerar a escalação ótima.</p>
                </div>
              )}

              {loading && (
                <div className="h-full flex items-center justify-center min-h-[400px]">
                  <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
                    <span className="text-emerald-400 font-medium">Resolvendo O(N) com PuLP...</span>
                  </div>
                </div>
              )}

              {result && !loading && (
                <div className="flex-1 flex flex-col justify-between py-4 sm:py-8 gap-4 px-2">
                  {/* Rows for players (Attack, Mid, Def, GK) */}
                  {[ 
                    (result.lineup ?? []).filter((p: any) => p.pos === 5), // ATA
                    (result.lineup ?? []).filter((p: any) => p.pos === 4), // MEI
                    (result.lineup ?? []).filter((p: any) => p.pos === 2 || p.pos === 3), // ZAG + LAT
                    (result.lineup ?? []).filter((p: any) => p.pos === 1)  // GOL
                  ].map((row: any[], rowIdx) => (
                    <div key={rowIdx} className="flex justify-around items-center w-full">
                      {row.map((p: any, i: number) => {
                        const isCaptain = result.capitao_id === p.id;
                        const photoUrl = p.foto ? p.foto.replace('FORMATO', '140x140') : null;
                        
                        return (
                          <div key={i} className="flex flex-col items-center group relative cursor-default">
                            {/* Avatar / Marker */}
                            <div className={`w-12 h-12 sm:w-14 sm:h-14 rounded-full border-2 bg-slate-800 flex items-center justify-center overflow-hidden
                              ${isCaptain ? 'border-amber-400 shadow-[0_0_15px_rgba(251,191,36,0.4)]' : 'border-emerald-500'}
                            `}>
                              {photoUrl ? (
                                <img src={photoUrl} alt={p.nome} className="w-full h-full object-cover" />
                              ) : (
                                <User className={`w-6 h-6 ${isCaptain ? 'text-amber-400' : 'text-emerald-400'}`} />
                              )}
                              
                              {/* C captain badge */}
                              {isCaptain && (
                                <div className="absolute -bottom-1 -right-1 bg-amber-500 text-slate-900 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border border-slate-900 z-10">
                                  C
                                </div>
                              )}
                            </div>
                            
                            {/* Name and pts */}
                            <div className="mt-1 flex flex-col items-center bg-slate-900/80 backdrop-blur-sm px-2 py-0.5 rounded border border-white/10">
                              <span className="text-[10px] sm:text-xs font-medium text-white truncate max-w-[80px]">
                                {p.nome?.split(' ')[0]} 
                              </span>
                              <span className="text-[9px] font-mono text-emerald-400">
                                {(p.pontos_esperados ?? 0).toFixed(1)}p
                              </span>
                            </div>

                            {/* Hover tooltip for more info */}
                            <div className="absolute bottom-full mb-2 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-950 border border-slate-700 p-2 rounded shadow-xl z-20 w-36 pointer-events-none">
                              <p className="text-xs text-white font-bold mb-1 truncate">{p.nome}</p>
                              <div className="flex justify-between text-[10px] text-slate-400">
                                <span>Preço:</span>
                                <span className="font-mono text-amber-400">C$ {(p.preco ?? 0).toFixed(1)}</span>
                              </div>
                              <div className="flex justify-between text-[10px] text-slate-400">
                                <span>Pts Proj:</span>
                                <span className="font-mono text-emerald-400">{(p.pontos_esperados ?? 0).toFixed(2)}</span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ))}

                  {/* Coach */}
                  {(()=>{
                    const tec = (result.lineup ?? []).find((p: any) => p.pos === 6);
                    if (!tec) return null;
                    const photoUrl = tec.foto ? tec.foto.replace('FORMATO', '140x140') : null;

                    return (
                      <div className="absolute bottom-4 right-4 flex flex-col items-center group z-10">
                        <div className="w-10 h-10 rounded-full border border-slate-500 bg-slate-800 flex items-center justify-center overflow-hidden">
                          {photoUrl ? (
                            <img src={photoUrl} alt={tec.nome} className="w-full h-full object-cover" />
                          ) : (
                            <User className="w-5 h-5 text-slate-400" />
                          )}
                        </div>
                        <div className="mt-1 bg-slate-900/80 px-1.5 py-0.5 rounded border border-white/10">
                          <span className="text-[9px] font-medium text-slate-300 block text-center truncate max-w-[60px]">TEC</span>
                        </div>
                        <div className="absolute bottom-full mb-2 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-950 border border-slate-700 p-2 rounded shadow-xl z-20 w-32 pointer-events-none right-0">
                          <p className="text-xs text-white font-bold mb-1 truncate">{tec.nome}</p>
                          <div className="flex justify-between text-[10px] text-slate-400">
                            <span>Preço:</span>
                            <span className="font-mono text-amber-400">C$ {(tec.preco ?? 0).toFixed(1)}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Justificativa Matemática */}
        <aside className="col-span-1 lg:col-span-3 space-y-4">
          <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-5 h-full">
            <h3 className="text-sm font-semibold text-indigo-300 uppercase tracking-widest mb-4 flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Justificativa Matemática
            </h3>

            <div className="space-y-4">
              {/* Stats Block - moved here from the field */}
              {result && (
                <div className="grid grid-cols-2 gap-3 bg-slate-900/80 p-4 rounded-xl border border-emerald-500/20 mb-4">
                  <div>
                    <p className="text-[10px] text-slate-400 uppercase font-semibold mb-1">Custo Total</p>
                    <h3 className="text-white font-bold text-lg">C$ {(result.total_cost ?? 0).toFixed(1)}</h3>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-400 uppercase font-semibold mb-1">Pontos (Proj.)</p>
                    <p className="text-emerald-400 font-bold text-lg">{(result.total_expected_points ?? 0).toFixed(1)}</p>
                  </div>
                  {user && (
                    <div className="col-span-2 mt-2 pt-3 border-t border-white/5">
                      <button
                        onClick={handleSave}
                        disabled={saving}
                        className="w-full bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 py-2 rounded-lg text-sm font-medium flex gap-2 items-center justify-center transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Save className="w-4 h-4" />
                        {saving ? 'Salvando...' : 'Salvar no Histórico'}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Justifications */}
              {!result ? (
                <div className="border border-white/5 bg-slate-900/50 p-4 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">O cálculo será exibido aqui assim que a escalação for analisada.</p>
                  <div className="h-2 bg-slate-800 rounded-full w-3/4 mb-2" />
                  <div className="h-2 bg-slate-800 rounded-full w-1/2" />
                </div>
              ) : (
                <div className="space-y-3 overflow-y-auto max-h-[400px] pr-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Destaques Matemáticos
                  </h4>
                  {[...(result.lineup ?? [])]
                    .sort((a: any, b: any) => (b.pontos_esperados ?? 0) - (a.pontos_esperados ?? 0))
                    .slice(0, 5)
                    .map((p: any, i: number) => (
                      <div key={i} className="border border-indigo-500/20 bg-slate-900/80 p-3 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-medium text-white">{p.nome ?? '—'}</span>
                          <span className="ml-auto text-xs font-mono text-emerald-400">{(p.pontos_esperados ?? 0).toFixed(1)}p</span>
                        </div>
                        <p className="text-xs text-slate-400 leading-relaxed italic border-l-2 border-indigo-500/30 pl-3">
                          {modo === 'mitagem' 
                            ? (p.pos === 1 || p.pos === 2 || p.pos === 3 
                                ? "Muralha Estatística. Índice alto de desarmes com multiplicador positivo de SG para a rodada." 
                                : "Agressividade latente. xG + xA alto combinado com adversário vulnerável.")
                            : "Alto potencial de lucro. GAP entre média e pontos necessários favorável ao orçamento."}
                        </p>
                      </div>
                    ))}
                    
                    {/* Reservas na sidebar tbm */}
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mt-6 mb-2">
                      Banco de Reservas
                    </h4>
                    <div className="grid grid-cols-1 gap-2">
                      {(result.reserves ?? []).map((p: any, i: number) => (
                        <div key={`res-${i}`} className="bg-slate-900/40 p-2 rounded-lg border border-white/5 flex gap-3 items-center">
                           <div className="w-8 h-8 rounded-full border border-slate-600 bg-slate-800 flex items-center justify-center overflow-hidden flex-shrink-0">
                            {p.foto ? (
                              <img src={p.foto.replace('FORMATO', '140x140')} alt={p.nome} className="w-full h-full object-cover" />
                            ) : (
                              <User className="w-4 h-4 text-slate-400" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs text-white font-medium truncate">{p.nome}</p>
                            <p className="text-[10px] text-slate-400 font-mono">C$ {(p.preco ?? 0).toFixed(1)}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                </div>
              )}
            </div>
          </div>
        </aside>

      </main>
    </div>
  );
}
