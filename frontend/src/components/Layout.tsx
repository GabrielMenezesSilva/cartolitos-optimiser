import { type ReactNode } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { TrendingUp, Settings } from 'lucide-react';
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Utility function to merge tailwind classes safely */
export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface LayoutProps {
    children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
    const location = useLocation();

    const navItems = [
        { name: 'Otimizador', path: '/optimiser', icon: TrendingUp },
    ];

    return (
        <div className="flex h-screen w-full bg-[#020617] text-slate-100 overflow-hidden">
            {/* Sidebar Desktop */}
            <aside className="hidden md:flex flex-col w-64 border-r border-slate-800/50 bg-[#0f172a]/80 backdrop-blur-xl">
                <div className="p-6 flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                        <span className="font-bold text-white tracking-tighter text-lg">C</span>
                    </div>
                    <span className="font-bold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-emerald-100 to-teal-100">
                        Cartolitos
                    </span>
                </div>

                <nav className="flex-1 px-4 py-6 space-y-2">
                    <div className="mb-4 px-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        Menu Principal
                    </div>
                    {navItems.map((item) => {
                        const isActive = location.pathname.startsWith(item.path);
                        return (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                className={cn(
                                    "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group text-sm font-medium",
                                    isActive
                                        ? "bg-slate-800/60 text-emerald-400 shadow-sm border border-slate-700/50"
                                        : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/30"
                                )}
                            >
                                <item.icon className={cn("w-5 h-5 transition-colors", isActive ? "text-emerald-400" : "text-slate-500 group-hover:text-slate-300")} />
                                {item.name}
                            </NavLink>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-slate-800/50">
                    <button className="flex w-full items-center gap-3 px-3 py-2.5 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800/30 transition-all text-sm font-medium">
                        <Settings className="w-5 h-5 text-slate-500" />
                        Configurações
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col h-full relative overflow-y-auto overflow-x-hidden">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-emerald-900/10 via-[#020617] to-[#020617] -z-10 pointer-events-none" />
                {children}
            </main>

            {/* Mobile Bottom Nav */}
            <nav className="md:hidden fixed bottom-0 left-0 right-0 border-t border-slate-800/80 bg-[#0f172a]/90 backdrop-blur-xl flex justify-around p-3 pb-safe z-50">
                {navItems.map((item) => {
                    const isActive = location.pathname.startsWith(item.path);
                    return (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={cn(
                                "flex flex-col items-center justify-center w-full gap-1 p-2 rounded-xl transition-all",
                                isActive ? "text-emerald-400" : "text-slate-500"
                            )}
                        >
                            <item.icon className="w-6 h-6" />
                            <span className="text-[10px] font-medium">{item.name}</span>
                        </NavLink>
                    );
                })}
            </nav>
        </div>
    );
}
