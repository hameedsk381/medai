'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    Users,
    UserPlus,
    Edit2,
    Trash2,
    CheckCircle,
    XCircle,
    Clock,
    Star,
    Briefcase,
    Phone,
    ArrowLeft,
    RefreshCw,
    Award,
    TrendingUp,
    LogOut,
    Activity,
    MessageSquare,
    BookOpen,
    ShieldCheck,
    Settings,
    ArrowUpRight,
    Loader2,
    Zap,
    X,
    Filter,
    Search,
    Calendar,
    Stethoscope
} from 'lucide-react';
import { useAuth } from '@/app/context/AuthContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Worker {
    id: string;
    name: string;
    phone: string;
    skills: string[];
    status: string;
    current_tasks: number;
    max_tasks: number;
    rating: number | null;
    total_jobs: number;
    created_at: string;
    updated_at: string;
}

interface WorkerStats {
    total_workers: number;
    available: number;
    busy: number;
    offline: number;
    total_jobs_done: number;
    average_rating: number | null;
}

const SKILL_OPTIONS = [
    "Clinical Triage",
    "Protocol Management",
    "Patient Intake",
    "EHR Integration",
    "Insurance Verification",
    "Laboratory Logistics",
    "Radiology Support",
    "Administrative Operations"
];

export default function WorkersPage() {
    const [workers, setWorkers] = useState<Worker[]>([]);
    const [stats, setStats] = useState<WorkerStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [showAddForm, setShowAddForm] = useState(false);
    const [editingWorker, setEditingWorker] = useState<Worker | null>(null);
    const [filterStatus, setFilterStatus] = useState<string>('all');
    const [searchTerm, setSearchTerm] = useState('');
    const { token, logout } = useAuth();

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        phone: '',
        skills: [] as string[],
        max_tasks: 5,
        status: 'available'
    });

    useEffect(() => {
        fetchData();
    }, [filterStatus]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const workersUrl = filterStatus === 'all'
                ? `${API_URL}/api/workers`
                : `${API_URL}/api/workers?status=${filterStatus}`;

            const headers = {
                'Authorization': `Bearer ${token}`
            };

            const [workersRes, statsRes] = await Promise.all([
                fetch(workersUrl, { headers }),
                fetch(`${API_URL}/api/workers/stats`, { headers })
            ]);

            const workersData = await workersRes.json();
            const statsData = await statsRes.json();

            setWorkers(workersData);
            setStats(statsData);
        } catch (error) {
            console.error('Failed to fetch data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        try {
            if (editingWorker) {
                const response = await fetch(`${API_URL}/api/workers/${editingWorker.id}`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(formData)
                });

                if (!response.ok) throw new Error('Failed to update worker');
            } else {
                const response = await fetch(`${API_URL}/api/workers`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(formData)
                });

                if (!response.ok) throw new Error('Failed to create worker');
            }

            resetForm();
            fetchData();
        } catch (error) {
            console.error('Error saving worker:', error);
        }
    };

    const handleDelete = async (workerId: string) => {
        if (!confirm('Are you sure you want to decommission this unit?')) return;

        try {
            const response = await fetch(`${API_URL}/api/workers/${workerId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) throw new Error('Failed to delete worker');
            fetchData();
        } catch (error) {
            console.error('Error deleting worker:', error);
        }
    };

    const resetForm = () => {
        setFormData({
            name: '',
            phone: '',
            skills: [],
            max_tasks: 5,
            status: 'available'
        });
        setShowAddForm(false);
        setEditingWorker(null);
    };

    const startEdit = (worker: Worker) => {
        setFormData({
            name: worker.name,
            phone: worker.phone,
            skills: worker.skills,
            max_tasks: worker.max_tasks,
            status: worker.status
        });
        setEditingWorker(worker);
        setShowAddForm(true);
    };

    const toggleSkill = (skill: string) => {
        setFormData(prev => ({
            ...prev,
            skills: prev.skills.includes(skill)
                ? prev.skills.filter(s => s !== skill)
                : [...prev.skills, skill]
        }));
    };

    const getStatusStyles = (status: string) => {
        switch (status) {
            case 'available': return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
            case 'busy': return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
            case 'offline': return 'bg-rose-500/10 text-rose-500 border-rose-500/20';
            default: return 'bg-muted text-muted-foreground border-border';
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
                    <SidebarLink href="/dashboard/workers" icon={Users} label="Intelligence Nodes" active />
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
                            <h1 className="text-4xl text-foreground tracking-tighter mb-1">Intelligence Nodes</h1>
                            <p className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em] italic">Manage Clinical Support & Field Operations</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <button
                            onClick={fetchData}
                            className="p-3 bg-card border border-border rounded-full hover:bg-muted transition-all shadow-sm"
                        >
                            <RefreshCw className={`w-5 h-5 text-foreground ${loading ? 'animate-spin' : ''}`} />
                        </button>
                        <button
                            onClick={() => setShowAddForm(true)}
                            className="btn-sarvam-primary flex items-center gap-2"
                        >
                            <UserPlus className="w-5 h-5" />
                            Deploy Node
                        </button>
                    </div>
                </header>

                {/* Stats Overview */}
                {stats && (
                    <div className="grid grid-cols-4 gap-8">
                        <MetricCard title="Total Nodes" value={stats.total_workers} icon={Users} color="light" delta="STABLE" />
                        <MetricCard title="Operational" value={stats.available} icon={CheckCircle} color="light" delta="ACTIVE" />
                        <MetricCard title="Capacity" value={stats.busy} icon={Clock} color="dark" delta="COMPUTING" />
                        <MetricCard title="Performance" value={stats.average_rating ? stats.average_rating.toFixed(1) : 'N/A'} icon={Star} color="light" delta="OPTIMAL" />
                    </div>
                )}

                {/* Filters & Control Bar */}
                <div className="space-y-10">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-6">
                            <h2 className="text-3xl tracking-tight text-foreground">Operational Roster</h2>
                            <div className="flex bg-muted p-1 rounded-full border border-border">
                                {['all', 'available', 'busy', 'offline'].map((status) => (
                                    <button
                                        key={status}
                                        onClick={() => setFilterStatus(status)}
                                        className={`px-5 py-2 rounded-full text-[10px] font-black uppercase tracking-widest transition-all ${filterStatus === status
                                            ? 'bg-card text-foreground shadow-sm border border-border'
                                            : 'text-muted-foreground hover:text-foreground'
                                            }`}
                                    >
                                        {status}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="relative group">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-foreground transition-colors" />
                            <input
                                type="text"
                                placeholder="Filter node ID..."
                                className="pl-12 pr-6 py-3 bg-card border border-border rounded-full text-sm w-72 focus:ring-1 focus:ring-foreground outline-none transition-all shadow-sm"
                            />
                        </div>
                    </div>

                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-64 space-y-4">
                            <Loader2 className="w-12 h-12 text-foreground animate-spin" />
                            <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Synchronizing Node States...</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {workers.map((worker) => (
                                <div
                                    key={worker.id}
                                    className="sarvam-card bg-card border border-border hover:shadow-2xl hover:shadow-black/5 transition-all group relative overflow-hidden"
                                >
                                    <div className="flex justify-between items-start mb-8">
                                        <div className="w-16 h-16 rounded-[24px] bg-muted border border-border flex items-center justify-center text-foreground group-hover:scale-110 transition-transform">
                                            <Briefcase className="w-8 h-8" />
                                        </div>
                                        <div className={`px-4 py-1.5 rounded-full text-[9px] font-black uppercase tracking-widest border ${getStatusStyles(worker.status)}`}>
                                            {worker.status}
                                        </div>
                                    </div>

                                    <div className="space-y-1 mb-6">
                                        <h3 className="text-2xl font-bold text-foreground tracking-tight uppercase" style={{ fontFamily: "'DM Serif Text', serif" }}>{worker.name}</h3>
                                        <div className="flex items-center gap-2 text-xs font-bold text-muted-foreground">
                                            <Phone className="w-4 h-4 text-border" />
                                            {worker.phone}
                                        </div>
                                    </div>

                                    <div className="mb-8 min-h-[64px]">
                                        <div className="flex flex-wrap gap-2">
                                            {worker.skills.map((skill) => (
                                                <span
                                                    key={skill}
                                                    className="px-3 py-1 bg-muted border border-border rounded-full text-[9px] font-black uppercase tracking-widest text-muted-foreground"
                                                >
                                                    {skill}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-6 mb-8 pt-6 border-t border-border">
                                        <div>
                                            <div className="text-[9px] font-black text-muted-foreground uppercase tracking-widest mb-1">Compute Load</div>
                                            <div className="text-xl font-bold text-foreground">
                                                {worker.current_tasks}<span className="text-muted-foreground/30 mx-1">/</span>{worker.max_tasks}
                                            </div>
                                        </div>
                                        <div>
                                            <div className="text-[9px] font-black text-muted-foreground uppercase tracking-widest mb-1">Protocol Success</div>
                                            <div className="text-xl font-bold text-foreground flex items-center gap-2">
                                                <TrendingUp className="w-4 h-4 text-emerald-500" />
                                                {worker.total_jobs}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex gap-4 pt-6 border-t border-border">
                                        <button
                                            onClick={() => startEdit(worker)}
                                            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-muted border border-border text-foreground rounded-[20px] font-black text-[10px] uppercase tracking-widest hover:bg-background transition-colors"
                                        >
                                            <Edit2 className="w-4 h-4" />
                                            Reconfigure
                                        </button>
                                        <button
                                            onClick={() => handleDelete(worker.id)}
                                            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-rose-500/5 border border-rose-500/10 text-rose-500 rounded-[20px] font-black text-[10px] uppercase tracking-widest hover:bg-rose-500/10 transition-colors"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                            Decommission
                                        </button>
                                    </div>
                                    <button className="absolute bottom-6 right-6 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <ArrowUpRight className="w-5 h-5 text-foreground" />
                                    </button>
                                </div>
                            ))}

                            {workers.length === 0 && (
                                <div className="col-span-3 text-center py-32 bg-card border border-border rounded-[40px] shadow-sm">
                                    <Users className="w-16 h-16 text-muted-foreground/20 mx-auto mb-6" />
                                    <h3 className="text-2xl font-bold text-foreground mb-4 racking-tighter">No Active Nodes</h3>
                                    <p className="text-muted-foreground mb-10 max-w-sm mx-auto text-sm leading-relaxed font-medium">Get started by deploying your first clinical intelligence node to the operational field.</p>
                                    <button
                                        onClick={() => setShowAddForm(true)}
                                        className="btn-sarvam-primary flex items-center gap-2 mx-auto"
                                    >
                                        <UserPlus className="w-5 h-5" />
                                        Initialize First Node
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </main>

            {/* Add Node Modal - Sarvam Style */}
            {showAddForm && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-300">
                    <div className="bg-card border border-border rounded-[40px] w-full max-w-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
                        <div className="p-10 border-b border-border flex items-center justify-between">
                            <div>
                                <h2 className="text-3xl tracking-tighter text-foreground">Node Provisioning</h2>
                                <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mt-1">Configure Field Intelligence Protocols</p>
                            </div>
                            <button onClick={resetForm} className="p-3 hover:bg-muted rounded-full transition-colors border border-border">
                                <X className="w-5 h-5 text-foreground" />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="p-10 space-y-8 max-h-[70vh] overflow-y-auto">
                            <div className="grid grid-cols-2 gap-8">
                                <div className="space-y-3">
                                    <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Assigned Name</label>
                                    <input
                                        type="text"
                                        required
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="w-full px-6 py-4 rounded-[20px] border border-border bg-muted text-foreground focus:ring-1 focus:ring-foreground outline-none transition shadow-sm"
                                        placeholder="Alpha-7 Personnel"
                                    />
                                </div>

                                <div className="space-y-3">
                                    <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Direct Secure Line</label>
                                    <input
                                        type="tel"
                                        required
                                        value={formData.phone}
                                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                        className="w-full px-6 py-4 rounded-[20px] border border-border bg-muted text-foreground focus:ring-1 focus:ring-foreground outline-none transition shadow-sm"
                                        placeholder="+1 000 000 0000"
                                    />
                                </div>
                            </div>

                            <div className="space-y-4">
                                <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Neural Skill Matrices (Select Required)</label>
                                <div className="grid grid-cols-2 gap-3">
                                    {SKILL_OPTIONS.map((skill) => (
                                        <button
                                            key={skill}
                                            type="button"
                                            onClick={() => toggleSkill(skill)}
                                            className={`px-6 py-4 rounded-[20px] text-[10px] font-black uppercase tracking-widest transition-all border ${formData.skills.includes(skill)
                                                ? 'bg-foreground text-background border-foreground'
                                                : 'bg-muted text-muted-foreground border-border hover:border-foreground/30'
                                                }`}
                                        >
                                            {skill}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-8">
                                <div className="space-y-3">
                                    <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Concurrent Task Limit</label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="20"
                                        value={formData.max_tasks}
                                        onChange={(e) => setFormData({ ...formData, max_tasks: parseInt(e.target.value) })}
                                        className="w-full px-6 py-4 rounded-[20px] border border-border bg-muted text-foreground focus:ring-1 focus:ring-foreground outline-none transition shadow-sm"
                                    />
                                </div>

                                {editingWorker && (
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Operational Status</label>
                                        <select
                                            value={formData.status}
                                            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                                            className="w-full px-6 py-4 rounded-[20px] border border-border bg-muted text-foreground focus:ring-1 focus:ring-foreground outline-none transition shadow-sm appearance-none"
                                        >
                                            <option value="available">Available</option>
                                            <option value="busy">Busy</option>
                                            <option value="offline">Offline</option>
                                        </select>
                                    </div>
                                )}
                            </div>

                            <div className="flex gap-4 pt-8">
                                <button
                                    type="button"
                                    onClick={resetForm}
                                    className="flex-1 py-5 border border-border text-foreground rounded-[24px] font-black text-[11px] uppercase tracking-widest hover:bg-muted transition-colors"
                                >
                                    Abort
                                </button>
                                <button
                                    type="submit"
                                    disabled={formData.skills.length === 0}
                                    className="btn-sarvam-primary flex-1 py-5 shadow-xl shadow-black/5"
                                >
                                    {editingWorker ? 'Commit Configuration' : 'Deploy Intelligence Node'}
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
