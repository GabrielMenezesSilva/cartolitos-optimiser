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
            {/* Avatar Wrapper so badge isn't hidden by overflow */}
            <div className="relative">
                <div
                    className={cn(
                        "w-12 h-12 sm:w-14 sm:h-14 rounded-full border-2 flex items-center justify-center overflow-hidden transition-all duration-300",
                        isCaptain
                            ? "border-amber-400 shadow-[0_0_15px_rgba(251,191,36,0.6)] z-10"
                            : isCoach
                                ? "border-indigo-500 bg-slate-800 w-10 h-10 sm:w-12 sm:h-12"
                                : "border-emerald-500 bg-slate-800 shadow-[0_4px_10px_rgba(0,0,0,0.5)] group-hover:border-emerald-400 group-hover:shadow-[0_0_15px_rgba(16,185,129,0.5)]"
                    )}
                >
                    {photoUrl ? (
                        <img src={photoUrl} alt={player.nome} className="w-full h-full object-cover transition-transform group-hover:scale-110" />
                    ) : (
                        <User className={cn("w-6 h-6", isCaptain ? "text-amber-400" : isCoach ? "text-indigo-400" : "text-emerald-400")} />
                    )}
                </div>

                {/* Captain badge */}
                {isCaptain && (
                    <div className="absolute -bottom-1 -right-1 bg-gradient-to-br from-amber-400 to-amber-600 text-slate-900 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border border-slate-900 z-20 shadow-lg">
                        C
                    </div>
                )}
            </div>

            {/* Name and pts */}
            <div className="mt-1.5 flex flex-col items-center bg-slate-900/90 backdrop-blur-md px-2 py-0.5 rounded-md border border-white/10 shadow-lg transition-transform group-hover:-translate-y-1">
                <span className="text-[10px] sm:text-xs font-bold text-white truncate max-w-[80px] drop-shadow-md">
                    {isCoach ? 'TEC: ' + player.nome?.split(' ')[0] : player.nome?.split(' ')[0]}
                </span>
                <span className={cn(
                    "text-[9px] font-mono font-semibold",
                    isCoach ? "text-indigo-400" : "text-emerald-400"
                )}>
                    {isCoach ? `C$ ${(player.preco ?? 0).toFixed(1)}` : `${(player.pontos_esperados ?? 0).toFixed(1)}p`}
                </span>
            </div>

            {/* Modern Hover tooltip */}
            <div className="absolute bottom-full mb-3 opacity-0 group-hover:opacity-100 transition-all group-hover:translate-y-[-4px] bg-slate-950/95 backdrop-blur-xl border border-white/10 p-3 rounded-xl shadow-2xl z-30 w-44 pointer-events-none">
                <p className="text-sm text-white font-bold mb-2 truncate">{player.nome}</p>
                <div className="space-y-1.5">
                    <div className="flex justify-between items-center text-[11px]">
                        <span className="text-slate-400">Preço</span>
                        <span className="font-mono text-amber-400 font-semibold flex items-center gap-1">
                            <span className="text-[9px] text-amber-500/70">C$</span> {(player.preco ?? 0).toFixed(1)}
                        </span>
                    </div>
                    {!isCoach && (
                        <div className="flex justify-between items-center text-[11px]">
                            <span className="text-slate-400">Pts Proj.</span>
                            <span className="font-mono text-emerald-400 font-semibold">{(player.pontos_esperados ?? 0).toFixed(2)}</span>
                        </div>
                    )}
                    {!isCoach && (
                        <div className="flex justify-between items-center text-[11px] pt-1 border-t border-white/5">
                            <span className="text-slate-400">Exp. Valorização</span>
                            <span className={cn("font-mono font-semibold", (player.pontos_valorizacao ?? 0) > 0 ? "text-emerald-400" : "text-red-400")}>
                                {(player.pontos_valorizacao ?? 0).toFixed(2)}
                            </span>
                        </div>
                    )}
                    {player.reason && (
                        <div className="flex flex-col text-[11px] pt-1 border-t border-white/5">
                            <span className="text-slate-400">Justificativa</span>
                            <span className="text-slate-300 italic text-[10px] leading-tight">
                                {player.reason}
                            </span>
                        </div>
                    )}
                </div>
                <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-slate-950/95 border-b border-r border-white/10 rotate-45 transform" />
            </div>
        </motion.div>
    );
}
