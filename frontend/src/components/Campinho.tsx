import { Cpu } from 'lucide-react';
import { PlayerCard } from './PlayerCard';

interface CampinhoProps {
    loading: boolean;
    result: any;
}

export function Campinho({ loading, result }: CampinhoProps) {
    if (!result && !loading) {
        return (
            <div className="h-full flex flex-col items-center justify-center text-center px-6 min-h-[500px]">
                <div className="w-20 h-20 bg-slate-900/80 rounded-full flex items-center justify-center mx-auto mb-6 border border-emerald-500/20 shadow-[0_0_30px_rgba(16,185,129,0.15)] relative">
                    <div className="absolute inset-0 rounded-full border border-emerald-500/30 animate-ping opacity-20" />
                    <Cpu className="w-10 h-10 text-emerald-500/80" />
                </div>
                <h3 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent mb-2">
                    Motor Matemático
                </h3>
                <p className="text-sm text-slate-400 max-w-sm">
                    Ajuste o orçamento, slider de ousadia e clique em processar para invocar a PuLP (O(N)) no backend.
                </p>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="h-full flex flex-col items-center justify-center min-h-[500px] gap-6">
                <div className="relative">
                    <div className="w-16 h-16 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
                    <div className="absolute inset-0 flex items-center justify-center">
                        <Cpu className="w-6 h-6 text-emerald-500 animate-pulse" />
                    </div>
                </div>
                <div className="text-center">
                    <h3 className="text-lg font-bold text-white mb-1">Analisando milhares de combinações</h3>
                    <p className="text-xs text-emerald-400 font-mono">Maximizando Expectativa de Retorno (E[P])</p>
                </div>
            </div>
        );
    }

    const titulares = result.results?.lineup?.filter((p: any) => p.is_titular) ?? [];

    const rows = [
        titulares.filter((p: any) => p.pos_id === 5), // ATA
        titulares.filter((p: any) => p.pos_id === 4), // MEI
        titulares.filter((p: any) => p.pos_id === 2 || p.pos_id === 3), // ZAG + LAT
        titulares.filter((p: any) => p.pos_id === 1)  // GOL
    ];

    const tec = titulares.find((p: any) => p.pos_id === 6);
    let delayCounter = 0;

    return (
        <div 
            className="relative flex-1 min-h-[600px] w-full max-w-4xl mx-auto rounded-3xl overflow-hidden border border-white/10 shadow-2xl bg-slate-900 group"
            style={{
                backgroundImage: 'url("/campo.png")',
                backgroundSize: 'cover',
                backgroundPosition: 'center'
            }}
        >
            {/* Overlay for better readability */}
            <div className="absolute inset-0 bg-gradient-to-b from-black/20 via-transparent to-black/40 pointer-events-none" />
            
            {/* Field Lines Overlay (Optional if image already has them, but adds depth) */}
            <div className="absolute inset-0 opacity-20 pointer-events-none border-[12px] border-white/20 m-4 rounded-[40px]" />

            <div className="relative h-full flex flex-col justify-between py-8 sm:py-12 gap-4 px-4">
                {rows.map((row: any[], rowIdx) => (
                    <div key={rowIdx} className="flex justify-around items-center w-full z-10">
                        {row.map((p: any) => {
                            delayCounter++;
                            return (
                                <PlayerCard
                                    key={p.id}
                                    player={p}
                                    isCaptain={p.is_capitao}
                                    delay={delayCounter}
                                />
                            );
                        })}
                    </div>
                ))}

                {/* Coach / Executive Area */}
                {tec && (
                    <div className="absolute bottom-6 right-6 z-20">
                        <PlayerCard
                            player={tec}
                            isCoach={true}
                            delay={delayCounter + 1}
                        />
                    </div>
                )}
            </div>

            {/* Tactical Info Badge */}
            <div className="absolute top-4 left-6 bg-black/40 backdrop-blur-md border border-white/10 p-2 rounded-lg z-20">
                <p className="text-[10px] uppercase tracking-widest text-emerald-400 font-bold">Modo de Otimização</p>
                <p className="text-white text-xs font-mono">{result.objective === 'valorizacao' ? 'Maximização de Cartoletas' : 'Maximização de Pontos'}</p>
            </div>
        </div>
    );
}
