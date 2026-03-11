import { useState } from 'react';
import { User } from 'lucide-react';
import { cn } from '../lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface PlayerCardProps {
    player: any;
    isCaptain?: boolean;
    delay?: number;
    className?: string;
    isCoach?: boolean;
    isLeftmost?: boolean;
    isRightmost?: boolean;
}

export function PlayerCard({ player, isCaptain = false, delay = 0, className, isCoach = false, isLeftmost = false, isRightmost = false }: PlayerCardProps) {
    const [hovered, setHovered] = useState(false);
    const photoUrl = player.foto ? player.foto.replace('FORMATO', '140x140') : null;

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ delay: delay * 0.08, type: 'spring', stiffness: 200, damping: 15 }}
            className={cn("flex flex-col items-center cursor-pointer select-none", className)}
            style={{ position: 'relative', zIndex: hovered ? 999 : 1, isolation: 'isolate' }}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
        >
            {/* Status Indicator */}
            {!isCoach && (
                <div className="absolute -top-1 -left-1 w-3 h-3 rounded-full bg-emerald-500 border-2 border-slate-950 shadow-lg" style={{ zIndex: 2 }} title="Bom Confronto" />
            )}

            {/* Avatar */}
            <div className="relative">
                <div
                    className={cn(
                        "rounded-full border-2 flex items-center justify-center overflow-hidden transition-all duration-300",
                        isCaptain
                            ? "w-16 h-16 border-amber-400 shadow-[0_0_20px_rgba(251,191,36,0.4)] p-0.5 bg-gradient-to-b from-amber-400/20 to-transparent"
                            : isCoach
                                ? "w-12 h-12 border-indigo-500 bg-slate-900/80"
                                : hovered
                                    ? "w-14 h-14 border-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.4)]"
                                    : "w-14 h-14 border-white/20 bg-slate-900/40 backdrop-blur-sm shadow-xl"
                    )}
                >
                    {photoUrl ? (
                        <img
                            src={photoUrl}
                            alt={player.nome}
                            className="w-full h-full object-cover"
                            style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.5))' }}
                        />
                    ) : (
                        <User className={cn("w-6 h-6", isCaptain ? "text-amber-400" : isCoach ? "text-indigo-400" : "text-emerald-400/80")} />
                    )}
                </div>

                {/* Club badge */}
                <div className="absolute top-0 right-0 w-5 h-5 bg-white rounded-full border border-slate-950 flex items-center justify-center overflow-hidden shadow-md" style={{ zIndex: 2 }}>
                    <span className="text-[7px] font-bold text-slate-950">{player.clube_slug?.substring(0, 3).toUpperCase() || '??'}</span>
                </div>

                {/* Captain badge */}
                {isCaptain && (
                    <div className="absolute -bottom-1 -right-1 bg-gradient-to-br from-amber-400 to-amber-600 text-slate-900 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border border-slate-900 shadow-lg ring-2 ring-amber-400/20" style={{ zIndex: 2 }}>
                        C
                    </div>
                )}
            </div>

            {/* Name label */}
            <div className={cn(
                "mt-1.5 flex flex-col items-center backdrop-blur-xl px-2 py-1 rounded-lg border shadow-2xl transition-all duration-200 min-w-[60px] max-w-[90px]",
                hovered ? "bg-emerald-900/60 border-emerald-500/40 -translate-y-1" : "bg-black/60 border-white/10"
            )}>
                <span className="text-[9px] sm:text-[10px] font-black text-white truncate w-full text-center tracking-tight uppercase">
                    {player.nome?.split(' ')[0] || '—'}
                </span>
                <div className="flex items-center gap-0.5">
                    <span className={cn("text-[9px] font-black", isCoach ? "text-indigo-400" : "text-emerald-400")}>
                        {isCoach ? `C$ ${(player.preco ?? 0).toFixed(1)}` : `${(player.pontos_esperados ?? 0).toFixed(1)}`}
                    </span>
                    {!isCoach && <span className="text-[7px] text-white/40 font-bold uppercase">pts</span>}
                </div>
            </div>

            {/* Tooltip — only renders when hovered, on TOP of everything */}
            <AnimatePresence>
                {hovered && (
                    <motion.div
                        initial={{ opacity: 0, y: -6, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -6, scale: 0.95 }}
                        transition={{ duration: 0.15 }}
                        className={cn(
                            "absolute bg-slate-950/98 backdrop-blur-2xl border border-white/10 p-4 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.7)] w-52 pointer-events-none overflow-hidden top-full mt-3",
                            isLeftmost ? "left-0" : isRightmost ? "right-0" : "left-1/2 -translate-x-1/2"
                        )}
                        style={{ zIndex: 9999 }}
                    >
                        <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500 rounded-l-2xl" />

                        <p className="text-[10px] text-slate-400 font-bold mb-0.5 uppercase tracking-tighter pl-2">{player.pos_nome || 'Jogador'}</p>
                        <p className="text-sm text-white font-black mb-3 leading-none pl-2">{player.nome}</p>

                        <div className="space-y-2 pl-2">
                            <div className="flex justify-between items-center text-[11px]">
                                <span className="text-slate-400">Custo</span>
                                <span className="font-mono text-amber-400 font-black">
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
                            <div className="mt-3 p-2 bg-black/30 rounded-lg border border-white/10 ml-2">
                                <p className="text-[10px] text-emerald-400/90 font-black mb-1 uppercase tracking-tight">Análise do Optimizer</p>
                                <p className="text-slate-200 italic text-[11px] leading-relaxed font-medium">{player.reason}</p>
                            </div>
                        )}

                        {/* Arrow */}
                        <div className={cn(
                            "absolute w-3 h-3 bg-slate-950 border-white/10 rotate-45 transform -top-1.5 border-t border-l",
                            isLeftmost ? "left-6" : isRightmost ? "right-6" : "left-1/2 -translate-x-1/2"
                        )} />
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}
