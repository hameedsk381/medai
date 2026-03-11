'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Mail, Lock, Building, UserPlus, Loader2, Activity, ShieldCheck, Zap, Sparkles, ChevronLeft } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function RegisterPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [businessName, setBusinessName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${API_URL}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    password,
                    business_name: businessName
                }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Registration failed');
            }

            router.push('/dashboard/login?registered=success');
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground flex relative overflow-hidden selection:bg-brand/10">

            {/* Left Panel: Form */}
            <div className="flex-1 flex items-center justify-center p-12 relative z-10 bg-background lg:bg-card">
                <div className="max-w-md w-full animate-fade-in space-y-12">

                    <div className="text-center lg:text-left space-y-4">
                        <h1 className="text-4xl text-foreground tracking-tighter">Clinic Onboarding</h1>
                        <p className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em]">Neural Intelligence Deployment</p>
                    </div>

                    {error && (
                        <div className="p-5 bg-rose-500/5 border border-rose-500/10 text-rose-500 rounded-3xl text-xs font-bold italic flex items-center gap-3">
                            <div className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></div>
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="space-y-3">
                            <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Facility Identity</label>
                            <div className="relative group">
                                <Building className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-border group-focus-within:text-foreground transition-colors" />
                                <input
                                    type="text"
                                    required
                                    value={businessName}
                                    onChange={(e) => setBusinessName(e.target.value)}
                                    className="w-full pl-14 pr-6 py-5 bg-muted border border-border rounded-[24px] text-foreground outline-none focus:ring-1 focus:ring-foreground transition-all shadow-sm"
                                    placeholder="e.g. Aura Medical Center"
                                />
                            </div>
                        </div>

                        <div className="space-y-3">
                            <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Administrative Email</label>
                            <div className="relative group">
                                <Mail className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-border group-focus-within:text-foreground transition-colors" />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-14 pr-6 py-5 bg-muted border border-border rounded-[24px] text-foreground outline-none focus:ring-1 focus:ring-foreground transition-all shadow-sm"
                                    placeholder="admin@yourclinic.com"
                                />
                            </div>
                        </div>

                        <div className="space-y-3">
                            <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Secure Passcode</label>
                            <div className="relative group">
                                <Lock className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-border group-focus-within:text-foreground transition-colors" />
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-14 pr-6 py-5 bg-muted border border-border rounded-[24px] text-foreground outline-none focus:ring-1 focus:ring-foreground transition-all shadow-sm"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-[0.15em] text-center leading-relaxed">
                            By deployment, you authorize HIPAA compliance and <br />
                            the clinical service architecture guidelines.
                        </p>

                        <button
                            type="submit"
                            disabled={loading}
                            className="btn-sarvam-primary w-full py-5 flex items-center justify-center gap-3 shadow-xl shadow-black/5 disabled:opacity-50"
                        >
                            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
                            {loading ? 'Initializing Architecture...' : 'Deploy Intelligence'}
                        </button>
                    </form>

                    <div className="pt-10 border-t border-border text-center lg:text-left">
                        <Link href="/dashboard/login" className="text-foreground hover:underline inline-flex items-center gap-2 font-black uppercase tracking-widest text-[10px]">
                            <ChevronLeft className="w-4 h-4" /> Return to Portal Access
                        </Link>
                    </div>
                </div>
            </div>

            {/* Right Panel: Feature Grid */}
            <div className="hidden lg:flex flex-col justify-center w-[45%] p-24 bg-[#131313] relative z-10 space-y-16">
                <div className="space-y-6">
                    <h2 className="text-6xl text-white tracking-tighter leading-[1.05]" style={{ fontFamily: "'DM Serif Text', serif" }}>
                        Empowering <br />
                        Modern <span className="italic bg-gradient-to-r from-[#a5bbfc] to-[#d5e2ff] bg-clip-text text-transparent">Facilities.</span>
                    </h2>
                    <p className="text-xl text-white/50 leading-relaxed max-w-md">
                        MedVoice AI orchestrates clinical heavy lifting, allowing your staff to focus on critical outcomes.
                    </p>
                </div>

                <div className="grid grid-cols-2 gap-12">
                    <FeatureBox
                        icon={Zap}
                        title="Sub-Second Intake"
                        desc="Neural intent recognition understands patients in less than 500ms."
                    />
                    <FeatureBox
                        icon={ShieldCheck}
                        title="HIPAA Verified"
                        desc="Advanced encryption for data residency and BAA compliance."
                    />
                    <FeatureBox
                        icon={Activity}
                        title="Live Coordination"
                        desc="Monitor real-time AI triage logs and staff synchronization."
                    />
                    <FeatureBox
                        icon={Activity}
                        title="Autonomous Flow"
                        desc="Read EHR schedules and book appointments with zero intervention."
                    />
                </div>
            </div>
        </div>
    );
}

function FeatureBox({ icon: Icon, title, desc }: any) {
    return (
        <div className="space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
                <Icon className="w-7 h-7 text-white" />
            </div>
            <h4 className="text-[11px] font-black text-white/30 uppercase tracking-[0.25em]">{title}</h4>
            <p className="text-sm text-white/50 leading-relaxed">
                {desc}
            </p>
        </div>
    );
}
