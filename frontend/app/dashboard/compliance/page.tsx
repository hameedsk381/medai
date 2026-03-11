'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    Shield,
    Clock,
    User,
    Activity,
    Search,
    Filter,
    ArrowLeft,
    FileText,
    AlertCircle,
    CheckCircle,
    LogOut,
    Calendar,
    Stethoscope,
    MessageSquare,
    BookOpen,
    ShieldCheck,
    Settings,
    ArrowUpRight,
    Loader2
} from 'lucide-react';
import { useAuth } from '@/app/context/AuthContext';

interface AuditLog {
    id: string;
    action: string;
    resource_id: string | null;
    details: string;
    created_at: string;
    user_id: string | null;
}

export default function CompliancePage() {
    const { token, logout } = useAuth();
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        if (token) {
            fetchAuditLogs();
        }
    }, [token]);

    const fetchAuditLogs = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/audit-logs`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setLogs(data);
            }
        } catch (err) {
            console.error('Failed to fetch audit logs:', err);
        } finally {
            setLoading(false);
        }
    };

    const filteredLogs = logs.filter(log =>
        log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.details.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getActionColor = (action: string) => {
        if (action.includes('TRANSFER')) return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
        if (action.includes('IDENTIFY')) return 'text-indigo-500 bg-indigo-500/10 border-indigo-500/20';
        if (action.includes('BOOK')) return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
        return 'text-muted-foreground bg-muted border-border';
    };

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
                    <SidebarLink href="/dashboard/compliance" icon={ShieldCheck} label="Security" active />
                    <SidebarLink href="/dashboard/settings" icon={Settings} label="Settings" />
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
                            <h1 className="text-4xl text-foreground tracking-tighter mb-1">Security & Accountability</h1>
                            <p className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em] italic">HIPAA Compliance Audit Trails</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/5 text-[9px] font-black text-indigo-500 uppercase tracking-widest border border-indigo-500/10">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        BAA Agreement Active
                    </div>
                </header>

                <div className="grid lg:grid-cols-4 gap-10">
                    {/* Status Overview */}
                    <div className="lg:col-span-1 space-y-8">
                        <div className="sarvam-card bg-card border border-border space-y-8">
                            <h2 className="text-[11px] font-black uppercase tracking-[0.3em] text-muted-foreground flex items-center gap-3">
                                <Activity className="w-4 h-4" />
                                Readiness Matrix
                            </h2>
                            <div className="space-y-4">
                                <StatusItem label="Audit Logging" active />
                                <StatusItem label="Multi-tenancy" active />
                                <StatusItem label="Data Encryption" active />
                                <StatusItem label="Patient Verification" warning icon={AlertCircle} />
                            </div>
                        </div>

                        <div className="sarvam-card bg-[#131313] text-white space-y-6 relative overflow-hidden group">
                            <div className="absolute -right-10 -bottom-10 opacity-10 group-hover:scale-125 transition-transform duration-1000">
                                <Shield className="w-32 h-32 text-white" />
                            </div>
                            <h3 className="text-2xl tracking-tighter">HIPAA Protocol</h3>
                            <p className="text-xs text-white/50 leading-relaxed font-medium uppercase tracking-widest">
                                AES-256 Encryption <br />
                                Direct Tenant Isolation <br />
                                Sovereign Data Residency
                            </p>
                        </div>
                    </div>

                    {/* Audit Log Table */}
                    <div className="lg:col-span-3 space-y-8">
                        <div className="flex items-center justify-between">
                            <h2 className="text-3xl tracking-tight text-foreground">Immutable Audit Trail</h2>
                            <div className="flex items-center gap-3">
                                <div className="relative group">
                                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-foreground transition-colors" />
                                    <input
                                        type="text"
                                        placeholder="Search neural history..."
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                        className="pl-12 pr-6 py-3 bg-card border border-border rounded-full text-sm w-72 focus:ring-1 focus:ring-foreground outline-none transition-all shadow-sm"
                                    />
                                </div>
                                <button className="p-3 bg-card border border-border rounded-full hover:bg-muted transition-all shadow-sm">
                                    <Filter className="w-5 h-5 text-foreground" />
                                </button>
                            </div>
                        </div>

                        <div className="sarvam-card !p-0 overflow-hidden shadow-xl shadow-black/5 bg-card border border-border">
                            <table className="w-full text-left">
                                <thead className="bg-muted border-b border-border">
                                    <tr>
                                        <th className="px-10 py-6 text-[11px] font-black uppercase text-muted-foreground tracking-[0.2em]">Action</th>
                                        <th className="px-10 py-6 text-[11px] font-black uppercase text-muted-foreground tracking-[0.2em]">Protocol Details</th>
                                        <th className="px-10 py-6 text-[11px] font-black uppercase text-muted-foreground tracking-[0.2em]">Neural Timestamp</th>
                                        <th className="px-10 py-6 text-[11px] font-black uppercase text-muted-foreground tracking-[0.2em] text-right">Reference</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {loading ? (
                                        <tr>
                                            <td colSpan={4} className="px-10 py-32 text-center text-muted-foreground">
                                                <div className="flex flex-col items-center gap-6">
                                                    <Loader2 className="w-8 h-8 animate-spin text-foreground" />
                                                    <span className="text-[10px] font-black uppercase tracking-widest">Accessing Secure Archives...</span>
                                                </div>
                                            </td>
                                        </tr>
                                    ) : filteredLogs.length === 0 ? (
                                        <tr>
                                            <td colSpan={4} className="px-10 py-32 text-center text-muted-foreground text-base font-medium italic">
                                                No immutable audit trails detected in this sector.
                                            </td>
                                        </tr>
                                    ) : (
                                        filteredLogs.map((log) => (
                                            <tr key={log.id} className="group hover:bg-muted transition cursor-pointer">
                                                <td className="px-10 py-8 whitespace-nowrap">
                                                    <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border ${getActionColor(log.action)}`}>
                                                        {log.action}
                                                    </span>
                                                </td>
                                                <td className="px-10 py-8">
                                                    <p className="text-sm font-medium text-foreground max-w-md truncate italic" title={log.details}>
                                                        "{log.details}"
                                                    </p>
                                                </td>
                                                <td className="px-10 py-8 whitespace-nowrap">
                                                    <div className="flex items-center gap-3 text-xs font-bold text-muted-foreground uppercase tracking-tight">
                                                        <Clock className="w-4 h-4 text-border" />
                                                        {new Date(log.created_at).toLocaleString()}
                                                    </div>
                                                </td>
                                                <td className="px-10 py-8 text-right whitespace-nowrap">
                                                    <code className="text-[9px] font-black tracking-widest bg-muted px-3 py-1.5 rounded-full border border-border text-muted-foreground uppercase">
                                                        {log.id.slice(0, 8)}
                                                    </code>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
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

function StatusItem({ label, active = false, warning = false, icon: Icon = CheckCircle }: any) {
    return (
        <div className={`flex items-center justify-between p-5 rounded-[24px] border ${active ? 'bg-emerald-500/5 border-emerald-500/10' : 'bg-muted border-border'
            }`}>
            <span className={`text-[11px] font-black uppercase tracking-widest ${active ? 'text-emerald-500' : 'text-muted-foreground'}`}>{label}</span>
            <Icon className={`w-4 h-4 ${active ? 'text-emerald-500' : 'text-border'}`} />
        </div>
    );
}
