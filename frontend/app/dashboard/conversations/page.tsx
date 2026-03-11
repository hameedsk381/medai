'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    Activity,
    Phone,
    MessageSquare,
    Clock,
    Search,
    DownloadCloud,
    Calendar,
    User,
    ShieldCheck,
    Settings,
    LogOut,
    BrainCircuit,
    Zap,
    Stethoscope,
    BookOpen,
    ArrowUpRight,
    Loader2
} from 'lucide-react';
import { useAuth } from '@/app/context/AuthContext';

interface Conversation {
    id: string;
    caller_phone: string;
    patient_id?: string;
    transcript?: string;
    intent?: string;
    outcome?: string;
    duration_seconds?: number;
    created_at: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ConversationsPage() {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedConvo, setSelectedConvo] = useState<Conversation | null>(null);
    const { token, logout } = useAuth();

    useEffect(() => {
        fetchConversations();
    }, []);

    const fetchConversations = async () => {
        try {
            const res = await fetch(`${API_URL}/api/conversations`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setConversations(data);
                if (data.length > 0) setSelectedConvo(data[0]);
            }
        } catch (error) {
            console.error('Failed to fetch conversations:', error);
        } finally {
            setLoading(false);
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
                    <SidebarLink href="/dashboard/appointments" icon={Calendar} label="Appointments" />
                    <SidebarLink href="/dashboard/doctors" icon={Stethoscope} label="Medical Staff" />
                    <SidebarLink href="/dashboard/conversations" icon={MessageSquare} label="Transcripts" active />
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
            <main className="flex-1 flex flex-col overflow-hidden relative">

                {/* Internal Header */}
                <header className="px-12 py-8 border-b border-border flex items-center justify-between bg-card z-40">
                    <div>
                        <h1 className="text-4xl text-foreground tracking-tighter mb-1">Neural Insight Logs</h1>
                        <p className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em]">Complete Clinical Documentation Archival</p>
                    </div>
                    <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/5 border border-emerald-500/10 text-[10px] text-emerald-500 uppercase tracking-widest font-black">
                        <Activity className="w-4 h-4 animate-pulse" />
                        Live Sync Active
                    </div>
                </header>

                <div className="flex-1 flex overflow-hidden">
                    {/* Architectural List Pane */}
                    <div className="w-[450px] border-r border-border bg-card flex flex-col">
                        <div className="p-8 border-b border-border">
                            <div className="relative group">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-border group-focus-within:text-foreground transition-colors" />
                                <input
                                    type="text"
                                    placeholder="Filter neural records..."
                                    className="w-full pl-12 pr-6 py-4 bg-muted border border-border rounded-full text-sm outline-none focus:ring-1 focus:ring-foreground transition-all"
                                />
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto divide-y divide-border">
                            {loading ? (
                                <div className="p-20 text-center space-y-6">
                                    <Loader2 className="w-8 h-8 text-foreground animate-spin mx-auto" />
                                    <p className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.25em]">Accessing Clinical Archives...</p>
                                </div>
                            ) : conversations.map((convo) => (
                                <div
                                    key={convo.id}
                                    onClick={() => setSelectedConvo(convo)}
                                    className={`p-10 cursor-pointer transition-all hover:bg-muted relative group ${selectedConvo?.id === convo.id
                                        ? 'bg-muted'
                                        : 'bg-transparent'
                                        }`}
                                >
                                    {selectedConvo?.id === convo.id && (
                                        <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-foreground"></div>
                                    )}
                                    <div className="flex justify-between items-start mb-4">
                                        <span className="font-bold text-foreground text-lg tracking-tight">{convo.caller_phone}</span>
                                        <span className="text-[9px] font-black text-muted-foreground uppercase tracking-[0.2em]">
                                            {new Date(convo.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-4 mb-4">
                                        <span className={`px-4 py-1.5 rounded-full text-[9px] font-black uppercase tracking-widest ${convo.outcome?.includes('success')
                                            ? 'bg-emerald-500/10 text-emerald-500'
                                            : 'bg-foreground/5 text-muted-foreground'
                                            }`}>
                                            {convo.intent || 'GENERAL'}
                                        </span>
                                        <span className="text-[10px] font-black text-muted-foreground flex items-center gap-2 uppercase tracking-tight">
                                            <Clock className="w-3.5 h-3.5" />
                                            {convo.duration_seconds || '0'}s Interaction
                                        </span>
                                    </div>
                                    <p className="text-sm text-muted-foreground line-clamp-1 italic">
                                        "{convo.transcript || 'No data captured'}"
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* High-Fidelity Detail Pane */}
                    <div className="flex-1 bg-background p-16 overflow-y-auto">
                        {selectedConvo ? (
                            <div className="max-w-5xl mx-auto space-y-12 animate-fade-in">

                                <div className="sarvam-card bg-card border border-border flex items-center justify-between">
                                    <div className="flex items-center gap-10">
                                        <div className="w-24 h-24 rounded-3xl bg-[#131313] flex items-center justify-center text-white shadow-xl shadow-black/5">
                                            <Phone className="w-10 h-10" />
                                        </div>
                                        <div>
                                            <h2 className="text-5xl text-foreground tracking-tighter mb-4" style={{ fontFamily: "'DM Serif Text', serif" }}>{selectedConvo.caller_phone}</h2>
                                            <div className="flex items-center gap-8 text-[11px] font-black text-muted-foreground uppercase tracking-[0.2em]">
                                                <span className="flex items-center gap-2"><Calendar className="w-4 h-4" /> {new Date(selectedConvo.created_at).toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' })}</span>
                                                <span className="flex items-center gap-2"><Clock className="w-4 h-4" /> SECURE SESSION #{selectedConvo.id.slice(0, 6)}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <button className="flex items-center gap-2 px-8 py-4 bg-card border border-border rounded-full text-[10px] font-black uppercase tracking-[0.2em] hover:bg-muted transition-all shadow-sm">
                                        <DownloadCloud className="w-4 h-4" />
                                        Export Protocol
                                    </button>
                                </div>

                                <div className="grid grid-cols-3 gap-8">
                                    <MetricSmall label="Neural Intent" value={selectedConvo.intent || 'Undefined'} icon={BrainCircuit} />
                                    <MetricSmall label="Patient Verification" value={selectedConvo.patient_id ? 'Authenticated' : 'New Intake'} icon={User} />
                                    <MetricSmall label="Interaction Status" value={selectedConvo.outcome || 'Logged'} icon={Zap} />
                                </div>

                                <div className="sarvam-card bg-card border border-border !p-0 overflow-hidden shadow-xl shadow-black/5">
                                    <div className="px-12 py-8 border-b border-border bg-muted flex items-center justify-between">
                                        <h3 className="text-[11px] font-black uppercase tracking-[0.3em] text-muted-foreground flex items-center gap-3">
                                            <MessageSquare className="w-4 h-4" />
                                            Clinical Transcription Protocol
                                        </h3>
                                        <div className="flex items-center gap-2 text-[9px] font-black text-emerald-500 bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20 uppercase tracking-[0.1em]">
                                            <ShieldCheck className="w-3.5 h-3.5" />
                                            HIPAA Encrypted
                                        </div>
                                    </div>
                                    <div className="p-20 bg-card">
                                        <div className="relative">
                                            <div className="absolute -left-10 top-0 bottom-0 w-0.5 bg-foreground/10"></div>
                                            <p className="text-2xl leading-[1.6] text-foreground tracking-tight font-medium italic pl-4">
                                                {selectedConvo.transcript || 'Neural processing was unable to generate a legible transcript for this interaction.'}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                            </div>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                                <BrainCircuit className="w-24 h-24 mb-8 opacity-10 animate-pulse text-foreground" />
                                <h3 className="text-2xl tracking-tighter">Initialize Neural Insight</h3>
                                <p className="text-sm font-medium mt-3 uppercase tracking-widest opacity-40">Awaiting Log Selection</p>
                            </div>
                        )}
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

function MetricSmall({ label, value, icon: Icon }: any) {
    return (
        <div className="sarvam-card bg-card border border-border p-8 space-y-4">
            <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 text-muted-foreground/30" />
                <span className="text-[10px] font-black uppercase text-muted-foreground tracking-[0.25em]">{label}</span>
            </div>
            <div className="text-2xl font-bold text-foreground tracking-tight truncate uppercase" style={{ fontFamily: "'DM Serif Text', serif" }}>{value}</div>
        </div>
    );
}
