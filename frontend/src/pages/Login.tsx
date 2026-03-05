import { Navigate } from 'react-router-dom';
import { LogIn } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { loginWithGoogle } from '../lib/firebase';

export default function Login() {
    const { user } = useAuth();

    if (user) {
        return <Navigate to="/" replace />;
    }

    return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-slate-800 rounded-2xl shadow-xl p-8 border border-white/10 text-center">
                <div className="w-16 h-16 bg-blue-500/20 text-blue-400 rounded-2xl flex items-center justify-center mx-auto mb-6">
                    <LogIn size={32} />
                </div>
                <h1 className="text-3xl font-bold text-white mb-2">Cartolitos Optimiser</h1>
                <p className="text-slate-400 mb-8">
                    Acesse a inteligência matemática da escalação perfeita.
                </p>

                <button
                    onClick={loginWithGoogle}
                    className="w-full bg-white hover:bg-slate-50 text-slate-900 font-semibold py-3 px-4 rounded-xl transition-all duration-200 flex items-center justify-center gap-3"
                >
                    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" className="w-5 h-5" />
                    Entrar com Google
                </button>

                <p className="mt-8 text-sm text-slate-500">
                    Apenas usuários convidados têm acesso à Engine ILP.
                </p>
            </div>
        </div>
    );
}
