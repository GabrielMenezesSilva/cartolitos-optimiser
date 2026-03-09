import { Cpu } from 'lucide-react';
import { PlayerCard } from './PlayerCard';
import { motion } from 'framer-motion';

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

    const rows = [
        (result.lineup ?? []).filter((p: any) => p.pos === 5), // ATA
        (result.lineup ?? []).filter((p: any) => p.pos === 4), // MEI
        (result.lineup ?? []).filter((p: any) => p.pos === 2 || p.pos === 3), // ZAG + LAT
        (result.lineup ?? []).filter((p: any) => p.pos === 1)  // GOL
    ];

    const tec = (result.lineup ?? []).find((p: any) => p.pos === 6);
    let delayCounter = 0;

    return (
        <div className="flex-1 flex flex-col justify-between py-6 sm:py-10 gap-6 px-4">
            {rows.map((row: any[], rowIdx) => (
                <div key={rowIdx} className="flex justify-around items-center w-full z-10">
                    {row.map((p: any) => {
                        delayCounter++;
                        return (
                            <PlayerCard
                                key={p.id}
                                player={p}
                                isCaptain={result.capitao_id === p.id}
                                delay={delayCounter}
                            />
                        );
                    })}
                </div>
            ))}

            {/* Coach Layer */}
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
    );
}
