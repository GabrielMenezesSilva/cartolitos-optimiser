import { User } from 'lucide-react';
import { cn } from '../lib/utils';
import { motion } from 'framer-motion';

interface PlayerCardProps {
    player: any;
    isCaptain?: boolean;
    delay?: number;
    className?: string;
    isCoach?: boolean;
}

export function PlayerCard({ player, isCaptain = false, delay = 0, className, isCoach = false }: PlayerCardProps) {
    const photoUrl = player.foto ? player.foto.replace('FORMATO', '140x140') : null;

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ delay: delay * 0.08, type: 'spring', stiffness: 200, damping: 15 }}
            className={cn("flex flex-col items-center group relative cursor-pointer", className)}
        >
            {/* Status Indicator (Difficulty/Form) - Placeholder for future integration */}
            {!isCoach && (
                <div className="absolute -top-1 -left-1 w-3 h-3 rounded-full bg-emerald-500 border-2 border-slate-950 z-20 shadow-lg" title="Bom Confronto" />
            )}

            <div className="relative">
                <div
                    className={cn(
                        "w-14 h-14 sm:w-16 sm:h-16 rounded-full border-2 flex items-center justify-center overflow-hidden transition-all duration-300",
                        isCaptain
                            ? "border-amber-400 shadow-[0_0_20px_rgba(251,191,36,0.3)] scale-110 z-10 p-0.5 bg-gradient-to-b from-amber-400/20 to-transparent"
                            : isCoach
                                ? "border-indigo-500 bg-slate-900/80 w-12 h-12"
                                : "border-white/20 bg-slate-900/40 backdrop-blur-sm shadow-xl group-hover:border-emerald-400 group-hover:shadow-[0_0_15px_rgba(16,185,129,0.3)]"
                    )}
                >
                    {photoUrl ? (
                        <img
                            src={photoUrl}
                            alt={player.nome}
                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-115"
                            style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.5))' }}
                        />
                    ) : (
                        <User className={cn("w-7 h-7", isCaptain ? "text-amber-400" : isCoach ? "text-indigo-400" : "text-emerald-400/80")} />
                    )}
                </div>

                {/* Team Badge Small Placeholder */}
                <div className="absolute top-0 right-0 w-5 h-5 bg-white rounded-full border border-slate-950 flex items-center justify-center overflow-hidden shadow-md">
                    <span className="text-[8px] font-bold text-slate-950">{player.clube_slug?.substring(0, 3).toUpperCase() || '??'}</span>
                </div>

                {/* Captain badge */}
                {isCaptain && (
                    <div className="absolute -bottom-1 -right-1 bg-gradient-to-br from-amber-400 to-amber-600 text-slate-900 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border border-slate-900 z-20 shadow-lg ring-2 ring-amber-400/20">
                        C
                    </div>
                )}
            </div>

            {/* Name and pts - PREMIUM LABEL */}
            <div className="mt-2 flex flex-col items-center bg-black/60 backdrop-blur-xl px-3 py-1 rounded-lg border border-white/10 shadow-2xl transition-all duration-300 group-hover:bg-emerald-900/40 group-hover:border-emerald-500/30 group-hover:-translate-y-1 min-w-[70px]">
                <span className="text-[10px] sm:text-[11px] font-black text-white truncate max-w-[85px] tracking-tight uppercase">
                    {isCoach ? player.nome?.split(' ')[0] : player.nome?.split(' ')[0]}
                </span>
                <div className="flex items-center gap-1">
                    <span className={cn(
                        "text-[10px] font-black",
                        isCoach ? "text-indigo-400" : "text-emerald-400"
                    )}>
                        {isCoach ? `C$ ${(player.preco ?? 0).toFixed(1)}` : `${(player.pontos_esperados ?? 0).toFixed(1)}`}
                    </span>
                    {!isCoach && <span className="text-[8px] text-white/40 font-bold uppercase">pts</span>}
                </div>
            </div>

            {/* Premium Hover tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 opacity-0 group-hover:opacity-100 transition-all duration-300 group-hover:translate-y-[-8px] bg-slate-950/95 backdrop-blur-2xl border border-white/10 p-4 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] z-50 w-52 pointer-events-none overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500" />

                <p className="text-xs text-slate-400 font-bold mb-0.5 uppercase tracking-tighter">{player.pos_nome || 'Jogador'}</p>
                <p className="text-sm text-white font-black mb-3 leading-none">{player.nome}</p>

                <div className="space-y-2">
                    <div className="flex justify-between items-center text-[11px]">
                        <span className="text-slate-400">Custo</span>
                        <span className="font-mono text-amber-400 font-black flex items-center gap-1">
                            <span className="text-[9px] text-amber-500/70 italic font-normal">C$</span> {(player.preco ?? 0).toFixed(2)}
                        </span>
                    </div>
                    {!isCoach && (
                        <div className="flex justify-between items-center text-[11px] bg-emerald-500/5 p-1 px-1.5 rounded-md border border-emerald-500/10">
                            <span className="text-emerald-500/80 font-bold">Projeção</span>
                            <span className="font-mono text-emerald-400 font-black">{(player.pontos_esperados ?? 0).toFixed(2)} <span className="text-[9px] font-normal opacity-70">pts</span></span>
                        </div>
                    )}
                    {!isCoach && (
                        <div className="space-y-1 pt-1">
                            <div className="flex justify-between items-center text-[10px]">
                                <span className="text-slate-500 italic">Mín. p/ Valorizar</span>
                                <span className="font-mono text-slate-300 font-bold">{(player.pontos_valorizacao ?? 0).toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between items-center text-[10px]">
                                <span className="text-slate-500 italic">Média</span>
                                <span className="font-mono text-slate-300 font-bold">{(player.media ?? 0).toFixed(2)}</span>
                            </div>
                        </div>
                    )}
                </div>

                {player.reason && (
                    <div className="mt-3 p-2 bg-white/5 rounded-lg border border-white/5">
                        <p className="text-[10px] text-slate-500 font-bold mb-1 uppercase tracking-tight">Análise do Optimizer</p>
                        <p className="text-slate-300 italic text-[10px] leading-relaxed">
                            {player.reason}
                        </p>
                    </div>
                )}

                <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-slate-950/95 border-b border-r border-white/10 rotate-45 transform" />
            </div>
        </motion.div>
    );
}
