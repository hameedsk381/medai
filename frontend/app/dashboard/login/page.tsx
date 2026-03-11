'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/app/context/AuthContext';
import { Mail, Lock, LogIn, Loader2, Command, ShieldCheck, ChevronRight, Fingerprint } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch(`${API_URL}/api/auth/login`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Login failed');
            }

            const { access_token } = await response.json();
            login(access_token);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground flex relative overflow-hidden">

            {/* Ambient Ambient Background Lights */}
            <div className="absolute top-0 right-0 w-[60%] h-[60%] bg-primary/10 blur-[150px] rounded-full -z-10 animate-pulse" />
            <div className="absolute bottom-0 left-0 w-[40%] h-[40%] bg-secondary/10 blur-[150px] rounded-full -z-10" />

            {/* Left Panel: High Tech Aesthetic */}
            <div className="hidden lg:flex flex-col justify-between w-[40%] p-16 bg-black/40 backdrop-blur-3xl border-r border-border relative z-10">
                <div className="flex items-center gap-2 group cursor-pointer">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary to-secondary flex items-center justify-center shadow-lg shadow-primary/20">
                        <Command className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-xl font-bold tracking-tight font-display">MedVoice AI</span>
                </div>

                <div className="space-y-8">
                    <div className="inline-block badge-premium py-1">Secure Node Authorization</div>
                    <h2 className="text-6xl font-display font-bold leading-tight tracking-tight text-white">
                        Access Neural <br />
                        <span className="text-gradient">Control.</span>
                    </h2>
                    <p className="text-lg text-muted-foreground max-w-sm leading-relaxed font-medium">
                        Securely authenticate to access your clinic's neural intake logs and synchronize intelligence protocols.
                    </p>
                    <div className="flex items-center gap-4 pt-4">
                        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-border text-xs font-semibold text-primary">
                            <ShieldCheck className="w-4 h-4" />
                            Security Tier 4
                        </div>
                        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-border text-xs font-semibold text-secondary">
                            <Fingerprint className="w-4 h-4" />
                            Biometric Ready
                        </div>
                    </div>
                </div>

                <div className="text-xs font-medium text-muted-foreground/40 tracking-[0.2em] uppercase">
                    © 2026 MedVoice Orbital Systems
                </div>
            </div>

            {/* Right Panel: Login Form */}
            <div className="flex-1 flex items-center justify-center p-8 relative z-10">
                <div className="max-w-md w-full fade-in space-y-10">

                    <div className="text-center lg:text-left space-y-2">
                        <h1 className="text-4xl font-display font-bold text-white tracking-tight">Portal Entry</h1>
                        <p className="text-sm text-muted-foreground font-medium">Please enter your clinical credentials.</p>
                    </div>

                    {error && (
                        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl text-sm font-medium flex items-center gap-3 animate-shake">
                            <AlertCircle className="w-4 h-4" />
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-xs font-bold text-muted-foreground tracking-widest uppercase ml-1">Credential Hash</label>
                            <div className="relative group">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-11 pr-4 py-3 bg-white/5 border border-border rounded-xl text-white outline-none focus:border-primary/50 transition-all font-medium placeholder:text-muted-foreground/30"
                                    placeholder="doctor@auramed.systems"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex items-center justify-between ml-1">
                                <label className="text-xs font-bold text-muted-foreground tracking-widest uppercase">Secret key</label>
                                <Link href="#" className="text-[10px] font-bold text-primary uppercase tracking-widest hover:text-white transition-colors">Recover</Link>
                            </div>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-11 pr-4 py-3 bg-white/5 border border-border rounded-xl text-white outline-none focus:border-primary/50 transition-all font-medium placeholder:text-muted-foreground/30"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="btn-premium w-full py-3.5 flex items-center justify-center gap-2 disabled:opacity-50 mt-4 shadow-xl shadow-primary/10"
                        >
                            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
                            {loading ? 'Authenticating...' : 'Access Command Center'}
                        </button>
                    </form>

                    <div className="pt-8 border-t border-border/50 text-center lg:text-left">
                        <p className="text-sm font-medium text-muted-foreground">
                            New facility?{' '}
                            <Link href="/dashboard/register" className="text-primary hover:text-white transition-colors flex items-center gap-1 font-bold uppercase tracking-widest text-[10px] mt-2 inline-flex">
                                Deploy Instance <ChevronRight className="w-3 h-3" />
                            </Link>
                        </p>
                    </div>
                </div>
            </div>

            <style jsx>{`
               @keyframes shake {
                 0%, 100% { transform: translateX(0); }
                 25% { transform: translateX(-4px); }
                 75% { transform: translateX(4px); }
               }
               .animate-shake {
                 animation: shake 0.4s ease-in-out;
               }
            `}</style>
        </div>
    );
}

function AlertCircle({ className }: { className: string }) {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
            <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
    )
}
