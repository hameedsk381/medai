'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    Users,
    Plus,
    Phone,
    Stethoscope,
    Calendar,
    ArrowLeft,
    Search,
    UserPlus,
    X,
    Check,
    LogOut,
    Activity,
    MessageSquare,
    BookOpen,
    ShieldCheck,
    Settings,
    ArrowUpRight,
    Loader2
} from 'lucide-react';
import { useAuth } from '@/app/context/AuthContext';

interface Doctor {
    id: string;
    name: string;
    specialization: string;
    phone: string;
    status: string;
    created_at: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function DoctorsPage() {
    const [doctors, setDoctors] = useState<Doctor[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [newDoctor, setNewDoctor] = useState({
        name: '',
        specialization: '',
        phone: ''
    });
    const { token, logout } = useAuth();

    useEffect(() => {
        fetchDoctors();
    }, []);

    const fetchDoctors = async () => {
        try {
            const res = await fetch(`${API_URL}/api/doctors`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setDoctors(data);
            }
        } catch (error) {
            console.error('Failed to fetch doctors:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleAddDoctor = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await fetch(`${API_URL}/api/doctors`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(newDoctor)
            });
            if (res.ok) {
                setShowModal(false);
                setNewDoctor({ name: '', specialization: '', phone: '' });
                fetchDoctors();
            }
        } catch (error) {
            console.error('Failed to add doctor:', error);
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
                    <SidebarLink href="/dashboard/doctors" icon={Stethoscope} label="Medical Staff" active />
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
                            <h1 className="text-4xl text-foreground tracking-tighter mb-1">Medical Personnel</h1>
                            <p className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em] italic">Authorized Clinical Decision Makers</p>
                        </div>
                    </div>

                    <button
                        onClick={() => setShowModal(true)}
                        className="btn-sarvam-primary flex items-center gap-2"
                    >
                        <UserPlus className="w-5 h-5" />
                        Onboard Practitioner
                    </button>
                </header>

                {/* Main Content Layout */}
                <div className="space-y-10">
                    <div className="flex items-center justify-between">
                        <h2 className="text-3xl tracking-tight text-foreground">Registered Staff</h2>
                        <div className="relative group">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-foreground transition-colors" />
                            <input
                                type="text"
                                placeholder="Filter personnel..."
                                className="pl-12 pr-6 py-3 bg-card border border-border rounded-full text-sm w-80 focus:ring-1 focus:ring-foreground outline-none transition-all shadow-sm"
                            />
                        </div>
                    </div>

                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-64 space-y-4">
                            <Loader2 className="w-12 h-12 text-foreground animate-spin" />
                            <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Accessing Personnel Archives...</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {doctors.map((doctor) => (
                                <div key={doctor.id} className="sarvam-card bg-card border border-border hover:shadow-2xl hover:shadow-black/5 transition-all group relative overflow-hidden">
                                    <div className="flex justify-between items-start mb-8">
                                        <div className="w-16 h-16 rounded-[24px] bg-muted border border-border flex items-center justify-center text-foreground group-hover:scale-110 transition-transform">
                                            <Users className="w-8 h-8" />
                                        </div>
                                        <div className={`px-4 py-1.5 rounded-full text-[9px] font-black uppercase tracking-widest border ${doctor.status === 'active' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : 'bg-muted text-muted-foreground border-border'
                                            }`}>
                                            {doctor.status}
                                        </div>
                                    </div>
                                    <div className="space-y-1 mb-6">
                                        <h3 className="text-2xl font-bold text-foreground tracking-tight uppercase" style={{ fontFamily: "'DM Serif Text', serif" }}>{doctor.name}</h3>
                                        <div className="flex items-center gap-2 text-xs font-bold text-muted-foreground uppercase tracking-widest">
                                            <Stethoscope className="w-4 h-4" />
                                            {doctor.specialization}
                                        </div>
                                    </div>
                                    <div className="space-y-3 pt-6 border-t border-border">
                                        <div className="flex items-center gap-3 text-xs font-bold text-muted-foreground">
                                            <Phone className="w-4 h-4 text-border" />
                                            {doctor.phone}
                                        </div>
                                        <div className="flex items-center gap-3 text-xs font-bold text-muted-foreground">
                                            <Calendar className="w-4 h-4 text-border" />
                                            Protocol Active Since {new Date(doctor.created_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                    <button className="absolute bottom-8 right-8 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <ArrowUpRight className="w-5 h-5 text-foreground" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </main>

            {/* Add Doctor Modal - Sarvam Style */}
            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-300">
                    <div className="bg-card border border-border rounded-[40px] w-full max-w-xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
                        <div className="p-10 border-b border-border flex items-center justify-between">
                            <div>
                                <h2 className="text-3xl tracking-tighter text-foreground">Personnel Onboarding</h2>
                                <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mt-1">Initialize Clinical Decision Core</p>
                            </div>
                            <button onClick={() => setShowModal(false)} className="p-3 hover:bg-muted rounded-full transition-colors border border-border">
                                <X className="w-5 h-5 text-foreground" />
                            </button>
                        </div>
                        <form onSubmit={handleAddDoctor} className="p-10 space-y-8">
                            <div className="space-y-3">
                                <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Full Practitioner Name</label>
                                <input
                                    required
                                    type="text"
                                    placeholder="Dr. Julian Vane"
                                    className="w-full px-6 py-4 rounded-[20px] border border-border bg-muted text-foreground focus:ring-1 focus:ring-foreground outline-none transition shadow-sm"
                                    value={newDoctor.name}
                                    onChange={(e) => setNewDoctor({ ...newDoctor, name: e.target.value })}
                                />
                            </div>
                            <div className="space-y-3">
                                <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Specialization Matrix</label>
                                <input
                                    required
                                    type="text"
                                    placeholder="Neuro-Radiology, etc."
                                    className="w-full px-6 py-4 rounded-[20px] border border-border bg-muted text-foreground focus:ring-1 focus:ring-foreground outline-none transition shadow-sm"
                                    value={newDoctor.specialization}
                                    onChange={(e) => setNewDoctor({ ...newDoctor, specialization: e.target.value })}
                                />
                            </div>
                            <div className="space-y-3">
                                <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Direct Secure Line</label>
                                <input
                                    required
                                    type="tel"
                                    placeholder="+1 000 000 0000"
                                    className="w-full px-6 py-4 rounded-[20px] border border-border bg-muted text-foreground focus:ring-1 focus:ring-foreground outline-none transition shadow-sm"
                                    value={newDoctor.phone}
                                    onChange={(e) => setNewDoctor({ ...newDoctor, phone: e.target.value })}
                                />
                            </div>
                            <div className="pt-6">
                                <button type="submit" className="btn-sarvam-primary w-full py-5 text-sm uppercase tracking-widest shadow-xl shadow-black/5">
                                    Commit Personnel Record
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
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
