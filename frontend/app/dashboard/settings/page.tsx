'use client';

import React from 'react';
import Link from 'next/link';
import {
    Settings,
    User,
    Bell,
    Lock,
    Globe,
    Activity,
    Calendar,
    Stethoscope,
    MessageSquare,
    BookOpen,
    ShieldCheck,
    LogOut,
    ArrowLeft,
    ChevronRight,
    Zap,
    Cpu,
    Database,
    Phone
} from 'lucide-react';
import { useAuth } from '@/app/context/AuthContext';

export default function SettingsPage() {
    const { logout } = useAuth();

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden">

            {/* Sidebar Navigation - Sarvam Dark Style */}
            <aside className="w-80 bg-[#131313] flex flex-col p-8 space-y-10 z-50">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-white flex items-center justify-center shadow-lg shadow-white/5">
                        <Activity className="w-6 h-6 text-[#131313]" />
                    </div>
                    <span className="text-xl font-bold tracking-tight text-white">MedVoice AI</span>
                </div>

                <nav className="flex-1 space-y-3">
                    <SidebarLink href="/dashboard" icon={Activity} label="Clinical Pulse" />
                    <SidebarLink href="/dashboard/appointments" icon={Calendar} label="Appointments" />
                    <SidebarLink href="/dashboard/doctors" icon={Stethoscope} label="Medical Staff" />
                    <SidebarLink href="/dashboard/conversations" icon={MessageSquare} label="Transcripts" />
                    <SidebarLink href="/dashboard/knowledge" icon={BookOpen} label="Intelligence Lab" />
                    <div className="py-6 my-2 border-t border-white/5">
                        <span className="text-[10px] font-black text-white/30 uppercase tracking-[0.25em] px-4">Administration</span>
                    </div>
                    <SidebarLink href="/dashboard/compliance" icon={ShieldCheck} label="Security" />
                    <SidebarLink href="/dashboard/settings" icon={Settings} label="Settings" active />
                </nav>

                <div className="pt-8 border-t border-white/5">
                    <button onClick={logout} className="flex items-center gap-3 text-rose-500 hover:bg-rose-500/10 w-full p-4 rounded-[20px] transition font-bold text-sm tracking-wide uppercase">
                        <LogOut className="w-5 h-5" />
                        Sign Out
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 overflow-y-auto relative p-12 space-y-12 pb-32">

                {/* Global Header */}
                <header className="flex items-center justify-between pb-8 border-b border-border">
                    <div className="flex items-center gap-6">
                        <Link href="/dashboard" className="p-3 bg-card border border-border rounded-full hover:bg-muted transition-all shadow-sm">
                            <ArrowLeft className="w-5 h-5 text-foreground" />
                        </Link>
                        <div>
                            <h1 className="text-4xl text-foreground tracking-tighter mb-1">System Configuration</h1>
                            <p className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em] italic">Architectural Tethers & Neural Overrides</p>
                        </div>
                    </div>
                </header>

                <div className="grid lg:grid-cols-12 gap-12">
                    {/* Settings Navigation */}
                    <div className="lg:col-span-3 space-y-4">
                        <SettingsNav icon={User} label="Facility Profile" active />
                        <SettingsNav icon={Bell} label="Notification Matrix" />
                        <SettingsNav icon={Lock} label="Access Control" />
                        <SettingsNav icon={Globe} label="API & Integrations" />
                        <SettingsNav icon={Cpu} label="Neural Modeling" />
                    </div>

                    {/* Settings Content */}
                    <div className="lg:col-span-9 space-y-12">
                        <section className="space-y-8">
                            <div className="flex items-center justify-between">
                                <h2 className="text-3xl tracking-tight text-foreground uppercase" style={{ fontFamily: "'DM Serif Text', serif" }}>Facility Parameters</h2>
                                <button className="btn-sarvam-primary">Update Protocol</button>
                            </div>

                            <div className="sarvam-card bg-card border border-border grid grid-cols-2 gap-10">
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Practice Identity</label>
                                    <input
                                        type="text"
                                        defaultValue="Aura Medical Center"
                                        className="w-full px-6 py-4 rounded-[24px] border border-border bg-muted text-foreground focus:ring-1 focus:ring-foreground outline-none transition shadow-sm"
                                    />
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Administrative Email</label>
                                    <input
                                        type="email"
                                        defaultValue="admin@auramed.com"
                                        className="w-full px-6 py-4 rounded-[24px] border border-border bg-muted text-foreground focus:ring-1 focus:ring-foreground outline-none transition shadow-sm"
                                    />
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Primary Reception Line</label>
                                    <div className="relative">
                                        <Phone className="absolute left-6 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                        <input
                                            type="tel"
                                            defaultValue="+1 (555) 000-1234"
                                            className="w-full pl-14 pr-6 py-4 rounded-[24px] border border-border bg-muted text-foreground focus:ring-1 focus:ring-foreground outline-none transition shadow-sm"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Neural Baseline Region</label>
                                    <div className="relative">
                                        <Globe className="absolute left-6 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                        <input
                                            type="text"
                                            defaultValue="US-East (Virginia)"
                                            className="w-full pl-14 pr-6 py-4 rounded-[24px] border border-border bg-muted text-foreground focus:ring-1 focus:ring-foreground outline-none transition shadow-sm"
                                        />
                                    </div>
                                </div>
                            </div>
                        </section>

                        <section className="space-y-8">
                            <h2 className="text-3xl tracking-tight text-foreground uppercase" style={{ fontFamily: "'DM Serif Text', serif" }}>Neural Infrastructure</h2>
                            <div className="grid grid-cols-2 gap-8">
                                <InfrastructureCard
                                    icon={Database}
                                    title="EHR Synchronization"
                                    status="HEALTHY"
                                    desc="Real-time read/write access to Epic and Cerner clinical records."
                                />
                                <InfrastructureCard
                                    icon={Zap}
                                    title="STT Virtualization"
                                    status="ACTIVE"
                                    desc="Low-latency speech-to-text processing for medical terminology."
                                />
                            </div>
                        </section>
                    </div>
                </div>
            </main>
        </div>
    );
}

function SidebarLink({ href, icon: Icon, label, active = false }: any) {
    return (
        <Link
            href={href}
            className={`flex items-center gap-4 p-5 rounded-[24px] font-bold text-sm transition-all group ${active
                ? 'bg-white text-[#131313] shadow-lg shadow-white/5'
                : 'text-white/40 hover:bg-white/5 hover:text-white'
                }`}
        >
            <Icon className={`w-6 h-6 transition-colors ${active ? 'text-[#131313]' : 'text-white/20 group-hover:text-white'}`} />
            <span className="tracking-wide">{label}</span>
        </Link>
    );
}

function SettingsNav({ icon: Icon, label, active = false }: any) {
    return (
        <button className={`w-full flex items-center justify-between p-5 rounded-[24px] border transition-all ${active ? 'bg-card border-border shadow-sm' : 'border-transparent text-muted-foreground hover:bg-muted'}`}>
            <div className="flex items-center gap-4">
                <div className={`p-2 rounded-xl ${active ? 'bg-foreground text-background' : 'bg-muted text-border'}`}>
                    <Icon className="w-5 h-5" />
                </div>
                <span className={`text-xs font-black uppercase tracking-widest ${active ? 'text-foreground' : ''}`}>{label}</span>
            </div>
            <ChevronRight className={`w-4 h-4 ${active ? 'text-foreground' : 'text-border'}`} />
        </button>
    );
}

function InfrastructureCard({ icon: Icon, title, status, desc }: any) {
    return (
        <div className="sarvam-card bg-card border border-border group hover:border-foreground/30 transition-all">
            <div className="flex items-start justify-between mb-6">
                <div className="p-4 rounded-2xl bg-muted border border-border text-foreground group-hover:scale-110 transition-transform">
                    <Icon className="w-6 h-6" />
                </div>
                <div className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 text-[9px] font-black tracking-widest uppercase">
                    {status}
                </div>
            </div>
            <h3 className="text-xl font-bold text-foreground mb-2 uppercase tracking-tight">{title}</h3>
            <p className="text-xs text-muted-foreground leading-relaxed font-medium">{desc}</p>
        </div>
    );
}
