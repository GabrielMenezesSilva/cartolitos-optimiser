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
                    Gerador de Escalação
                </h3>
                <p className="text-sm text-slate-400 max-w-sm">
                    Ajuste o seu orçamento e selecione a estratégia desejada para criar a melhor opção de time.
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
                    <p className="text-xs text-emerald-400 font-mono">Encontrando os melhores jogadores para o seu time</p>
                </div>
            </div>
        );
    }

    const titulares = result.results?.lineup?.filter((p: any) => p.is_titular) ?? [];

    // Order: top=attackers, then midfielders, then defenders+fullbacks, then goalkeeper
    const rows: any[][] = [
        titulares.filter((p: any) => p.pos_id === 5),               // ATA
        titulares.filter((p: any) => p.pos_id === 4),               // MEI
        titulares.filter((p: any) => p.pos_id === 2 || p.pos_id === 3), // LAT + ZAG
        titulares.filter((p: any) => p.pos_id === 1),               // GOL
    ].filter(r => r.length > 0);

    const tec = titulares.find((p: any) => p.pos_id === 6);
    let delayCounter = 0;

    return (
        <div
            className="relative w-full rounded-3xl border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)] bg-slate-900 overflow-visible"
            style={{ minHeight: '580px' }}
        >
            {/* Field image — premium replacement */}
            <div className="absolute inset-0 rounded-3xl overflow-hidden pointer-events-none">
                <img
                    src="/campo_premium.png"
                    alt="Campo"
                    className="w-full h-full"
                    style={{
                        objectFit: 'cover',
                        objectPosition: 'center',
                        transform: 'scale(1.2)',
                        transformOrigin: 'center center',
                    }}
                />
                {/* Dark overlays for readability */}
                <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/30 to-black/70" />
            </div>

            {/* Tactical info badge */}
            <div className={`absolute top-4 left-4 bg-black/50 backdrop-blur-md border px-3 py-1.5 rounded-xl z-20 ${result.config?.objective === 'valorizacao' ? 'border-amber-500/50' : 'border-emerald-500/50'}`}>
                <p className={`text-[9px] uppercase tracking-widest font-bold ${result.config?.objective === 'valorizacao' ? 'text-amber-400' : 'text-emerald-400'}`}>
                    Estratégia
                </p>
                <p className="text-white text-xs font-mono font-bold">
                    {result.config?.objective === 'valorizacao' ? 'Foco em Cartoletas' : 'Foco em Pontuação'}
                </p>
            </div>

            {/* Players grid — portrait layout */}
            <div
                className="relative w-full h-full flex flex-col justify-between"
                style={{ padding: '52px 16px 20px', minHeight: '580px', zIndex: 10 }}
            >
                {rows.map((row: any[], rowIdx) => (
                    <motion.div
                        key={rowIdx}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: rowIdx * 0.1 }}
                        className="flex justify-around items-center w-full"
                        style={{ zIndex: 10 }}
                    >
                        {row.map((p: any) => {
                            delayCounter++;
                            return (
                                <div key={p.id} style={{ position: 'relative', zIndex: 10 }}>
                                    <PlayerCard
                                        player={p}
                                        isCaptain={p.is_capitao}
                                        delay={delayCounter}
                                    />
                                </div>
                            );
                        })}
                    </motion.div>
                ))}
            </div>

            {/* Coach badge */}
            {tec && (
                <div className="absolute bottom-4 right-4 z-20">
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
