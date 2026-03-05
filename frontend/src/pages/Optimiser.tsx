import { useState, useEffect } from 'react';
import { Cpu, ShieldAlert, Zap, TrendingUp, Settings2, Save, User } from 'lucide-react';
import { optimizeLineup, saveLineup } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function Optimiser() {
  const [loading, setLoading] = useState(false);
  const [budget, setBudget] = useState(140);
  const [ousadia, setOusadia] = useState(5);
  const [modo, setModo] = useState('mitagem');
  const [result, setResult] = useState<any>(null);
  const [panicMode, setPanicMode] = useState(false);
  const [saving, setSaving] = useState(false);

  const { token, user } = useAuth();

  const handleOptimize = async () => {
    setLoading(true);
    setResult(null);
    try {
      const data = await optimizeLineup(budget, ousadia, modo, token);
      setResult(data);
    } catch (e) {
      console.error('Error optimizing:', e);
      alert('Falha ao rodar o otimizador');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!result || !token) return;
    setSaving(true);
    try {
      // Usar a rodada fictícia ou real para histórico
      await saveLineup(token, 1, result.total_expected_points, result.total_cost, { lineup: result.lineup, reserves: result.reserves }, modo);
      alert('Escalação salva com sucesso no histórico!');
    } catch (e) {
      console.error('Falha ao salvar a escalação', e);
      alert('Falha ao salvar a escalação');
    } finally {
      setSaving(false);
    }
  };

  // The Panic Button mechanics - Polling via useEffect
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (panicMode) {
      // Re-run optimization every 30 seconds when in panic mode
      interval = setInterval(() => {
        console.log("Panic Mode: Otimizando novamente para capturar lesões/mudanças de status...");
        handleOptimize();
      }, 30000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [panicMode, budget, ousadia, modo, token]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-emerald-500/30">

      {/* Header */}
      <header className="border-b border-white/10 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center">
              <Cpu className="w-5 h-5 text-slate-950 font-bold" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">Cartolitos <span className="text-emerald-500 font-light">Optimiser</span></h1>
          </div>

          <button
            onClick={() => setPanicMode(!panicMode)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${panicMode ? 'bg-red-500 text-white border-red-500 animate-pulse' : 'bg-red-500/10 hover:bg-red-500/20 text-red-500 border-red-500/20'}`}>
            <ShieldAlert className="w-4 h-4" />
            <span>{panicMode ? 'Panic Mode ON' : 'Panic Button'}</span>
          </button>
        </div>
      </header>

      {/* Main Layout */}
      <main className="max-w-7xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">

        {/* Painel de Controle Lado Esquerdo */}
        <aside className="col-span-1 lg:col-span-3 space-y-6">
          <div className="bg-slate-900/50 border border-white/5 rounded-xl p-5">
            <h2 className="flex items-center gap-2 font-semibold text-white mb-4">
              <Settings2 className="w-4 h-4 text-emerald-500" />
              Calibração do Motor
            </h2>

            <div className="space-y-5">
              <div>
                <label className="text-xs text-slate-400 font-medium uppercase tracking-wider block mb-2">Modo de Operação</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setModo('mitagem')}
                    className={`py-2 px-3 rounded-lg text-sm font-medium border flex items-center justify-center gap-2 transition-all ${modo === 'mitagem' ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400' : 'bg-slate-800 border-white/5 text-slate-400 hover:bg-slate-800/80'}`}>
                    <Zap className="w-4 h-4" /> Mitagem
                  </button>
                  <button
                    onClick={() => setModo('valorizacao')}
                    className={`py-2 px-3 rounded-lg text-sm font-medium border flex items-center justify-center gap-2 transition-all ${modo === 'valorizacao' ? 'bg-amber-500/10 border-amber-500/50 text-amber-400' : 'bg-slate-800 border-white/5 text-slate-400 hover:bg-slate-800/80'}`}>
                    <TrendingUp className="w-4 h-4" /> Patrimônio
                  </button>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-xs text-slate-400 font-medium uppercase tracking-wider">Orçamento (C$)</label>
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
                  <label className="text-xs text-slate-400 font-medium uppercase tracking-wider">Slider de Ousadia</label>
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
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
                {loading ? (
                  <span className="animate-pulse">Calculando Rota...</span>
                ) : (
                  <>
                    <Cpu className="w-4 h-4" /> Processar Escalação
                  </>
                )}
              </button>
            </div>
          </div>
        </aside>

        {/* Centro - Campo de Futebol */}
        <section className="col-span-1 lg:col-span-6 flex items-center justify-center">
          <div className="w-full flex flex-col xl:aspect-[3/4] bg-emerald-800/10 border-2 border-emerald-500/10 rounded-2xl relative overflow-hidden">
            {/* Campo e Linhas */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute inset-0 border-[8px] border-emerald-500/10 m-4 rounded-lg mix-blend-overlay"></div>
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-24 border-b-2 border-x-2 border-emerald-500/10 rounded-b-sm mix-blend-overlay"></div>
              <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-40 h-24 border-t-2 border-x-2 border-emerald-500/10 rounded-t-sm mix-blend-overlay"></div>
              <div className="absolute top-1/2 left-0 w-full border-t-2 border-emerald-500/10 mix-blend-overlay"></div>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 rounded-full border-2 border-emerald-500/10 mix-blend-overlay"></div>
            </div>

            <div className="relative z-10 w-full h-full p-4 overflow-y-auto">
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
                    <div className="w-12 h-12 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin"></div>
                    <span className="text-emerald-400 font-medium">Resolvendo O(N) com PuLP...</span>
                  </div>
                </div>
              )}
              {result && !loading && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-slate-900/80 p-4 rounded-xl border border-white/5">
                    <div>
                      <p className="text-xs text-slate-400 uppercase font-semibold mb-1">Custo Total</p>
                      <h3 className="text-white font-bold text-xl">C$ {result.total_cost.toFixed(2)}</h3>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 uppercase font-semibold mb-1">Pontos (Proj.)</p>
                      <p className="text-emerald-400 font-bold text-xl">{result.total_expected_points.toFixed(2)}</p>
                    </div>
                    {result.roi_cartoletas !== undefined && (
                      <div>
                        <p className="text-xs text-slate-400 uppercase font-semibold mb-1">ROI (Proj.)</p>
                        <p className="text-amber-400 font-bold text-xl">C$ {result.roi_cartoletas.toFixed(2)}</p>
                      </div>
                    )}
                    {result.score_protecao !== undefined && (
                      <div>
                        <p className="text-xs text-slate-400 uppercase font-semibold mb-1">Proteção (Reserva)</p>
                        <p className="text-indigo-400 font-bold text-xl">{result.score_protecao.toFixed(1)} <span className="text-sm font-normal text-slate-500">/ 10</span></p>
                      </div>
                    )}
                    {user && (
                      <div className="col-span-2 md:col-span-4 mt-2 pt-4 border-t border-white/5 flex justify-end">
                        <button onClick={handleSave} disabled={saving} className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2 rounded-lg text-sm font-medium flex gap-2 items-center transition-colors">
                          <Save className="w-4 h-4" /> {saving ? 'Salvando...' : 'Salvar no Histórico'}
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="h-px w-full bg-white/5 my-4"></div>

                  {/* Titulares */}
                  <div>
                    <h4 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-3">Titulares</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {result.lineup.map((p: any, i: number) => (
                        <div key={i} className="bg-slate-900/40 p-3 rounded-lg border border-white/5 flex flex-col gap-1">
                          <div className="flex justify-between">
                            <span className="text-white font-medium text-sm flex items-center gap-2"><User className="w-3 h-3 text-emerald-500" /> {p.nome}</span>
                            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">{p.posicao}</span>
                          </div>
                          <div className="flex justify-between items-center mt-1">
                            <span className="text-xs text-slate-400">{p.clube}</span>
                            <span className="text-xs font-mono text-emerald-400">C$ {p.preco.toFixed(1)} | {p.pontos_esperados.toFixed(1)} pts</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Reservas */}
                  <div className="mt-6">
                    <h4 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-3">Banco de Reservas</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {result.reserves.map((p: any, i: number) => (
                        <div key={i} className="bg-slate-900/40 p-3 rounded-lg border border-white/5 flex flex-col gap-1 opacity-80">
                          <div className="flex justify-between">
                            <span className="text-white font-medium text-sm flex items-center gap-2"><User className="w-3 h-3 text-amber-500" /> {p.nome}</span>
                            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">{p.posicao}</span>
                          </div>
                          <div className="flex justify-between items-center mt-1">
                            <span className="text-xs text-slate-400">{p.clube}</span>
                            <span className="text-xs font-mono text-amber-400">C$ {p.preco.toFixed(1)} | {p.pontos_esperados.toFixed(1)} pts</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              )}
            </div>
          </div>
        </section>

        {/* Lado Direito - Why Him? Cards */}
        <aside className="col-span-1 lg:col-span-3 space-y-4">
          <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-5 h-full">
            <h3 className="text-sm font-semibold text-indigo-300 uppercase tracking-widest mb-4 flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Justificativa Matemática
            </h3>

            <div className="space-y-3">
              {!result ? (
                <div className="border border-white/5 bg-slate-900/50 p-4 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">O cálculo será exibido aqui assim que a escalação for analisada.</p>
                  <div className="h-2 bg-slate-800 rounded-full w-3/4 mb-2"></div>
                  <div className="h-2 bg-slate-800 rounded-full w-1/2"></div>
                </div>
              ) : (
                <div className="space-y-3 overflow-y-auto max-h-[600px] pr-2 custom-scrollbar">
                  {[...result.lineup].sort((a, b) => b.pontos_esperados - a.pontos_esperados).slice(0, 5).map((p: any, i: number) => (
                    <div key={i} className="border border-indigo-500/20 bg-slate-900/80 p-4 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-6 h-6 rounded bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-xs">{i + 1}</div>
                        <span className="text-sm font-medium text-white">{p.nome}</span>
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed italic border-l-2 border-indigo-500/30 pl-3">
                        "{p.justificativa}"
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </aside>

      </main>
    </div>
  );
}
