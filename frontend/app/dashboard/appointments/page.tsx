'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    Activity,
    Calendar,
    Clock,
    User,
    Stethoscope,
    ArrowLeft,
    CheckCircle2,
    Clock3,
    AlertCircle,
    ChevronLeft,
    ChevronRight,
    Search,
    Filter,
    Plus,
    X,
    MessageSquare,
    BookOpen,
    ShieldCheck,
    Settings,
    LogOut,
    PlusCircle,
    BrainCircuit,
    Zap,
    ArrowUpRight
} from 'lucide-react';
import { useAuth } from '@/app/context/AuthContext';

interface Appointment {
    id: string;
    patient_id: string;
    doctor_id: string;
    date: string;
    time_slot: string;
    status: string;
    created_via: string;
    created_at: string;
    patient_name?: string;
    doctor_name?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AppointmentsPage() {
    const [appointments, setAppointments] = useState<Appointment[]>([]);
    const [loading, setLoading] = useState(true);
    const [currentMonth, setCurrentMonth] = useState(new Date());
    const { token, logout } = useAuth();

    useEffect(() => {
        fetchAppointments();
    }, []);

    const fetchAppointments = async () => {
        try {
            const res = await fetch(`${API_URL}/api/appointments`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setAppointments(data);
            }
        } catch (error) {
            console.error('Failed to fetch appointments:', error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusStyles = (status: string) => {
        switch (status) {
            case 'scheduled': return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
            case 'cancelled': return 'bg-rose-500/10 text-rose-500 border-rose-500/20';
            case 'pending': return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
            default: return 'bg-slate-500/10 text-slate-500 border-slate-500/20';
        }
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
                    <SidebarLink href="/dashboard/appointments" icon={Calendar} label="Appointments" active />
                    <SidebarLink href="/dashboard/doctors" icon={Stethoscope} label="Medical Staff" />
                    <SidebarLink href="/dashboard/conversations" icon={MessageSquare} label="Transcripts" />
                    <SidebarLink href="/dashboard/knowledge" icon={BookOpen} label="Intelligence Lab" />
                    <div className="py-6 my-2 border-t border-white/5">
                        <span className="text-[10px] font-black text-white/30 uppercase tracking-[0.25em] px-4">Administration</span>
                    </div>
                    <SidebarLink href="/dashboard/compliance" icon={ShieldCheck} label="Security" />
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
                            <h1 className="text-4xl text-foreground tracking-tighter mb-1">Scheduling Hub</h1>
                            <p className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em]">High-Fidelity Automated Appointment Manager</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2 bg-card border border-border rounded-full px-5 py-2 shadow-sm">
                            <button className="p-2 hover:bg-muted rounded-full transition text-foreground">
                                <ChevronLeft className="w-5 h-5" />
                            </button>
                            <span className="px-4 font-black text-[11px] uppercase tracking-widest min-w-[160px] text-center text-foreground">
                                {currentMonth.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })}
                            </span>
                            <button className="p-2 hover:bg-muted rounded-full transition text-foreground">
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>
                        <button className="btn-sarvam-primary flex items-center gap-2">
                            <PlusCircle className="w-5 h-5" />
                            Manual Booking
                        </button>
                    </div>
                </header>

                {/* Key Metrics Bar */}
                <div className="grid grid-cols-4 gap-8">
                    <MetricCard title="Total Slots" value={appointments.length} icon={Calendar} color="light" delta="STABLE" />
                    <MetricCard title="AI Bookings" value={appointments.filter(a => a.created_via === 'ai_call').length} icon={BrainCircuit} color="dark" delta="+12%" />
                    <MetricCard title="Confirmed" value={appointments.filter(a => a.status === 'scheduled').length} icon={CheckCircle2} color="light" delta="+5%" />
                    <MetricCard title="Upcoming" value={appointments.filter(a => a.status === 'pending').length} icon={Clock3} color="light" delta="QUEUED" />
                </div>

                {/* Main Dashboard Layout */}
                <div className="space-y-10">
                    <div className="flex items-center justify-between">
                        <h2 className="text-3xl tracking-tight text-foreground">Interactive Clinical Pipeline</h2>
                        <div className="flex items-center gap-3">
                            <div className="relative group">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-foreground transition-colors" />
                                <input
                                    type="text"
                                    placeholder="Search neural records..."
                                    className="pl-12 pr-6 py-3 bg-card border border-border rounded-full text-sm w-80 focus:ring-1 focus:ring-foreground outline-none transition-all shadow-sm"
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
                                    <th className="px-10 py-6 text-[11px] font-black uppercase text-muted-foreground tracking-[0.2em]">Patient Profile</th>
                                    <th className="px-10 py-6 text-[11px] font-black uppercase text-muted-foreground tracking-[0.2em]">Clinician</th>
                                    <th className="px-10 py-6 text-[11px] font-black uppercase text-muted-foreground tracking-[0.2em]">Scheduling</th>
                                    <th className="px-10 py-6 text-[11px] font-black uppercase text-muted-foreground tracking-[0.2em]">Triage Status</th>
                                    <th className="px-10 py-6 text-[11px] font-black uppercase text-muted-foreground tracking-[0.2em]">Source</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {loading ? (
                                    <tr>
                                        <td colSpan={5} className="px-10 py-32 text-center text-muted-foreground text-base font-medium italic">
                                            Initializing clinical schedule stream...
                                        </td>
                                    </tr>
                                ) : appointments.length === 0 ? (
                                    <tr>
                                        <td colSpan={5} className="px-10 py-32 text-center text-muted-foreground text-base font-medium italic">
                                            No clinical sessions programmed for this period.
                                        </td>
                                    </tr>
                                ) : (
                                    appointments.map((apt) => (
                                        <tr key={apt.id} className="group hover:bg-muted transition cursor-pointer">
                                            <td className="px-10 py-8">
                                                <div className="flex items-center gap-4">
                                                    <div className="w-12 h-12 rounded-2xl bg-background border border-border flex items-center justify-center text-muted-foreground group-hover:text-foreground transition-colors">
                                                        <User className="w-6 h-6" />
                                                    </div>
                                                    <span className="text-lg font-medium text-foreground tracking-tight">{apt.patient_name || 'Guest Patient'}</span>
                                                </div>
                                            </td>
                                            <td className="px-10 py-8">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-500">
                                                        <Stethoscope className="w-5 h-5" />
                                                    </div>
                                                    <span className="text-sm font-bold text-foreground">Dr. {apt.doctor_name || 'Unassigned'}</span>
                                                </div>
                                            </td>
                                            <td className="px-10 py-8">
                                                <div className="flex flex-col gap-1">
                                                    <div className="flex items-center gap-2 text-sm font-black text-foreground">
                                                        <Calendar className="w-4 h-4 text-foreground/40" />
                                                        {new Date(apt.date).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}
                                                    </div>
                                                    <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                                                        <Clock className="w-3.5 h-3.5" />
                                                        {apt.time_slot}
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-10 py-8">
                                                <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border ${getStatusStyles(apt.status)}`}>
                                                    {apt.status}
                                                </span>
                                            </td>
                                            <td className="px-10 py-8">
                                                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest ${apt.created_via === 'ai_call'
                                                    ? 'bg-indigo-500/10 text-indigo-500 border border-indigo-500/20'
                                                    : 'bg-muted text-muted-foreground border border-border'
                                                    }`}>
                                                    {apt.created_via === 'ai_call' ? <BrainCircuit className="w-3.5 h-3.5" /> : <User className="w-3.5 h-3.5" />}
                                                    {apt.created_via.replace('_', ' ')}
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
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

function MetricCard({ title, value, icon: Icon, color, delta }: any) {
    const isDark = color === 'dark';
    return (
        <div className={`sarvam-card overflow-hidden group hover:scale-[1.02] transition-transform duration-500 shadow-xl shadow-black/5 ${isDark ? 'bg-[#131313] text-white border-none' : 'bg-card border border-border text-foreground'}`}>
            <div className="flex items-start justify-between mb-8">
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg ${isDark ? 'bg-white/10' : 'bg-muted border border-border'}`}>
                    <Icon className={`w-7 h-7 ${isDark ? 'text-white' : 'text-foreground'}`} />
                </div>
                <div className={`px-4 py-1.5 rounded-full text-[10px] font-black border tracking-widest ${isDark ? 'border-white/10 bg-white/5 text-white/50' : 'border-border bg-muted text-muted-foreground'}`}>
                    {delta}
                </div>
            </div>
            <div className="text-5xl font-medium tracking-tighter mb-2" style={{ fontFamily: "'DM Serif Text', serif" }}>{value}</div>
            <div className={`text-[11px] font-black uppercase tracking-[0.2em] ${isDark ? 'text-white/30' : 'text-muted-foreground'}`}>{title}</div>
        </div>
    );
}
