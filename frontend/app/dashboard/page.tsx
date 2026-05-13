'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    Activity,
    Stethoscope,
    Calendar,
    Users,
    ClipboardList,
    ShieldCheck,
    PhoneCall,
    Search,
    RefreshCw,
    Clock,
    Zap,
    LogOut,
    BookOpen,
    Filter,
    ChevronRight,
    Bell,
    Settings,
    UserCheck,
    MessageSquare,
    AlertCircle,
    ArrowUpRight,
    Loader2,
    Command,
    Terminal,
    Wind,
    Radio,
    Send
} from 'lucide-react';
import { useAuth } from '@/app/context/AuthContext';

interface Task {
    task_id: string;
    intent: string;
    issue: string;
    urgency: string;
    location?: string;
    preferred_time?: string;
    confidence: number;
    status: string;
    customer_phone: string;
    created_at: string;
    assigned_to?: string;
    assigned_worker_name?: string;
}

interface DashboardStats {
    total_calls: number;
    tasks_created: number;
    escalations: number;
    failures: number;
    appointments_count: number;
    patients_count: number;
    success_rate: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function DashboardPage() {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [filteredTasks, setFilteredTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [searchQuery, setSearchQuery] = useState('');
    const { token, logout } = useAuth();

    useEffect(() => {
        fetchDashboardData();
    }, []);

    useEffect(() => {
        filterTasks();
    }, [tasks, statusFilter, searchQuery]);

    const fetchDashboardData = async () => {
        setLoading(true);
        try {
            const headers = { 'Authorization': `Bearer ${token}` };
            const [statsRes, tasksRes] = await Promise.all([
                fetch(`${API_URL}/api/dashboard/stats`, { headers }),
                fetch(`${API_URL}/api/tasks`, { headers })
            ]);

            if (statsRes.ok) setStats(await statsRes.json());
            if (tasksRes.ok) setTasks(await tasksRes.json());
        } catch (error) {
            console.error('Data fetch failed:', error);
        } finally {
            setLoading(false);
        }
    };

    const filterTasks = () => {
        let filtered = [...tasks];
        if (statusFilter !== 'all') {
            filtered = filtered.filter(t => t.status === statusFilter);
        }
        if (searchQuery) {
            filtered = filtered.filter(t =>
                t.issue.toLowerCase().includes(searchQuery.toLowerCase()) ||
                t.intent.toLowerCase().includes(searchQuery.toLowerCase()) ||
                t.customer_phone.includes(searchQuery)
            );
        }
        setFilteredTasks(filtered);
    };

    const getUrgencyStyles = (urgency: string) => {
        switch (urgency.toLowerCase()) {
            case 'critical': return 'text-rose-400 bg-rose-400/10 border-rose-400/20';
            case 'high': return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
            default: return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
        }
    };

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden">

            {/* Global Ambient Glows */}
            <div className="fixed top-0 right-0 w-[50%] h-[50%] bg-primary/5 blur-[120px] rounded-full -z-10" />
            <div className="fixed bottom-0 left-0 w-[40%] h-[40%] bg-secondary/5 blur-[120px] rounded-full -z-10" />

            {/* Sidebar Navigation */}
            <aside className="w-72 border-r border-border bg-black/40 backdrop-filter backdrop-blur-xl flex flex-col p-6 space-y-8 z-50">
                <div className="flex items-center gap-2 group px-2 cursor-pointer">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-primary to-secondary flex items-center justify-center shadow-lg shadow-primary/20">
                        <Command className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-lg font-bold tracking-tight font-display">MedVoice AI</span>
                </div>

                <nav className="flex-1 space-y-1.5 overflow-y-auto pr-2 custom-scrollbar">
                    <SidebarLink href="/dashboard" icon={Activity} label="Command Center" active />
                    <SidebarLink href="/dashboard/voice" icon={Radio} label="Voice Pipeline" />
                    <SidebarLink href="/dashboard/appointments" icon={Calendar} label="Appointments" />
                    <SidebarLink href="/dashboard/doctors" icon={Stethoscope} label="Medical Staff" />
                    <SidebarLink href="/dashboard/conversations" icon={MessageSquare} label="Neural Logs" />
                    <SidebarLink href="/dashboard/knowledge" icon={BookOpen} label="Intelligence Base" />

                    <div className="pt-6 pb-2 px-4">
                        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em]">Management</span>
                    </div>

                    <SidebarLink href="/dashboard/compliance" icon={ShieldCheck} label="Security Core" />
                    <SidebarLink href="/dashboard/settings" icon={Settings} label="System Config" />
                </nav>

                <div className="pt-4 border-t border-border">
                    <button
                        onClick={logout}
                        className="flex items-center gap-3 text-muted-foreground hover:text-white hover:bg-white/5 w-full p-3 rounded-xl transition-all font-medium text-sm"
                    >
                        <LogOut className="w-4 h-4" />
                        Disconnect
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 overflow-y-auto relative custom-scrollbar p-10 space-y-8 pb-32">

                {/* Header */}
                <header className="flex items-center justify-between pb-6 border-b border-border/50">
                    <div className="space-y-1">
                        <h1 className="text-3xl font-display font-semibold tracking-tight text-white">System Overview</h1>
                        <div className="flex items-center gap-4">
                            <span className="badge-premium py-1 lowercase flex items-center gap-1.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                                neural pipeline operational
                            </span>
                            <span className="text-xs font-medium text-muted-foreground">Aura Medical Center • Node 04</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-3 bg-white/5 border border-border rounded-xl px-4 py-2 hover:bg-white/10 transition-colors cursor-pointer">
                            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary/40 to-secondary/40 border border-white/10 flex items-center justify-center text-[10px] font-bold text-white">SW</div>
                            <div className="hidden sm:block">
                                <span className="block text-xs font-bold leading-none text-white">Dr. Sarah Wilson</span>
                                <span className="text-[10px] text-muted-foreground font-medium">Administrator</span>
                            </div>
                        </div>
                        <button className="p-2.5 rounded-xl border border-border hover:bg-white/10 transition-all relative">
                            <Bell className="w-4 h-4" />
                            <span className="absolute top-2.5 right-2.5 w-1.5 h-1.5 bg-primary rounded-full shadow-sm shadow-primary/40" />
                        </button>
                    </div>
                </header>

                {/* Key Metrics */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <MetricCard title="Daily Intake" value={stats?.total_calls || 0} icon={PhoneCall} trend="+12.4%" />
                    <MetricCard title="Scheduled" value={stats?.appointments_count || 0} icon={Calendar} trend="+2.1%" />
                    <MetricCard title="New Patients" value={stats?.patients_count || 0} icon={Users} trend="+18.5%" />
                    <MetricCard title="System Precision" value={`${stats?.success_rate || 0}%`} icon={Zap} trend="Optimal" isSuccess />
                </div>

                {/* Dashboard Grid */}
                <div className="grid lg:grid-cols-3 gap-8">

                    {/* Active Triage Queue */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Terminal className="w-4 h-4 text-primary" />
                                <h2 className="text-xl font-display font-semibold text-white">Triage Monitor</h2>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="relative group">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-white transition-colors" />
                                    <input
                                        type="text"
                                        placeholder="Filter records..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="pl-9 pr-4 py-2 bg-white/5 border border-border rounded-xl text-sm w-64 focus:border-primary/50 outline-none transition-all text-white placeholder:text-muted-foreground/50"
                                    />
                                </div>
                                <button onClick={fetchDashboardData} className="p-2 border border-border rounded-xl hover:bg-white/5 transition-all">
                                    <RefreshCw className={`w-4 h-4 text-white ${loading ? 'animate-spin' : ''}`} />
                                </button>
                            </div>
                        </div>

                        <div className="cartesia-card p-0">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead className="border-b border-border/50">
                                        <tr>
                                            <th className="px-6 py-4 text-[10px] font-bold uppercase text-muted-foreground tracking-widest leading-none">Record</th>
                                            <th className="px-6 py-4 text-[10px] font-bold uppercase text-muted-foreground tracking-widest leading-none">Subject</th>
                                            <th className="px-6 py-4 text-[10px] font-bold uppercase text-muted-foreground tracking-widest leading-none">Severity</th>
                                            <th className="px-6 py-4 text-[10px] font-bold uppercase text-muted-foreground tracking-widest leading-none text-right">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/30">
                                        {filteredTasks.length > 0 ? (
                                            filteredTasks.map((task) => (
                                                <tr key={task.task_id} className="group hover:bg-white/[0.02] transition cursor-pointer">
                                                    <td className="px-6 py-5">
                                                        <div className="font-mono text-xs text-primary mb-1 uppercase font-semibold">{task.task_id.slice(0, 8)}</div>
                                                        <div className="text-xs text-muted-foreground">{task.customer_phone}</div>
                                                    </td>
                                                    <td className="px-6 py-5">
                                                        <div className="text-sm font-semibold mb-1 text-white">{task.intent}</div>
                                                        <div className="text-xs text-muted-foreground line-clamp-1 max-w-xs">{task.issue}</div>
                                                    </td>
                                                    <td className="px-6 py-5">
                                                        <span className={`px-3 py-1 rounded-lg text-[10px] font-bold uppercase border ${getUrgencyStyles(task.urgency)}`}>
                                                            {task.urgency}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-5 text-right">
                                                        <button className="p-2 rounded-lg hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-all border border-transparent hover:border-border">
                                                            <ArrowUpRight className="w-4 h-4 text-white" />
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan={4} className="px-6 py-20 text-center">
                                                    <div className="max-w-xs mx-auto space-y-3">
                                                        {loading ? (
                                                            <Loader2 className="w-6 h-6 animate-spin mx-auto text-primary/50" />
                                                        ) : (
                                                            <>
                                                                <div className="text-sm font-semibold text-white">Triage Clear</div>
                                                                <div className="text-xs text-muted-foreground">No active clinical intake records found in the current buffer.</div>
                                                            </>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* Side Insight Panels */}
                    <div className="space-y-8">
                        <div className="flex items-center gap-2">
                            <Zap className="w-4 h-4 text-amber-400" />
                            <h2 className="text-xl font-display font-semibold text-white">Live Metrics</h2>
                        </div>

                        <div className="cartesia-card bg-gradient-to-br from-primary/20 to-transparent border-primary/20 space-y-6">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-bold text-primary tracking-widest uppercase">inference speed</span>
                                <Wind className="w-4 h-4 text-primary animate-pulse" />
                            </div>
                            <div className="space-y-1">
                                <div className="text-4xl font-display font-bold text-white">142ms</div>
                                <p className="text-xs text-muted-foreground font-medium">End-to-end neural latency</p>
                            </div>
                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                <div className="h-full bg-primary w-[85%] rounded-full shadow-[0_0_10px_rgba(99,102,241,0.5)]" />
                            </div>
                        </div>

                        <Link href="/dashboard/voice" className="cartesia-card bg-gradient-to-br from-secondary/15 to-transparent border-secondary/20 space-y-5 group block">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-bold text-secondary tracking-widest uppercase">voice console</span>
                                <Radio className="w-4 h-4 text-secondary group-hover:scale-110 transition-transform" />
                            </div>
                            <div className="space-y-2">
                                <div className="text-2xl font-display font-semibold text-white">Launch live pipeline controls</div>
                                <p className="text-xs text-muted-foreground">
                                    Trigger outbound calls, probe `/voice-stream`, and validate your Twilio tunnel from one place.
                                </p>
                            </div>
                        </Link>

                        <div className="cartesia-card space-y-6">
                            <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Active Personnel</h4>
                            <div className="space-y-3">
                                {[
                                    { name: 'Dr. Sarah Wilson', role: 'Chief of Staff', status: 'In Session', online: true },
                                    { name: 'Dr. James Chen', role: 'Radiology', status: 'Available', online: true },
                                    { name: 'Dr. Maria Garcia', role: 'Surgery', status: 'On Call', online: false }
                                ].map(staff => (
                                    <div key={staff.name} className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-border/50 hover:bg-white/10 transition-all cursor-pointer">
                                        <div className="flex items-center gap-3">
                                            <div className="relative">
                                                <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center text-[10px] font-bold border border-white/5 uppercase text-white">{staff.name.split(' ').map(n => n[0]).join('')}</div>
                                                <div className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-background ${staff.online ? 'bg-emerald-500' : 'bg-muted-foreground'}`} />
                                            </div>
                                            <div>
                                                <div className="text-xs font-bold text-white">{staff.name}</div>
                                                <div className="text-[10px] text-muted-foreground font-medium">{staff.role}</div>
                                            </div>
                                        </div>
                                        <span className="text-[9px] font-bold text-muted-foreground uppercase">{staff.status}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <Link href="/dashboard/knowledge" className="cartesia-card bg-gradient-to-tr from-secondary/10 to-transparent border-secondary/20 p-6 flex flex-col items-center text-center gap-4 group cursor-pointer block">
                            <div className="w-12 h-12 rounded-2xl bg-secondary/10 border border-secondary/20 flex items-center justify-center group-hover:bg-secondary/20 transition-all">
                                <BookOpen className="w-6 h-6 text-secondary" />
                            </div>
                            <div className="space-y-1">
                                <div className="text-lg font-display font-semibold text-white">Intelligence Base</div>
                                <p className="text-xs text-muted-foreground font-medium">Adjust system protocols and neural response vectors.</p>
                            </div>
                        </Link>
                    </div>

                </div>
            </main>

            <style jsx global>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
            `}</style>
        </div>
    );
}

function SidebarLink({ href, icon: Icon, label, active = false }: { href: string, icon: any, label: string, active?: boolean }) {
    return (
        <Link
            href={href}
            className={`flex items-center gap-3.5 p-3 rounded-xl text-sm transition-all group ${active
                ? 'bg-primary text-white shadow-lg shadow-primary/20'
                : 'text-muted-foreground hover:text-white hover:bg-white/5'
                }`}
        >
            <Icon className={`w-4 h-4 transition-colors ${active ? 'text-white' : 'text-muted-foreground group-hover:text-white'}`} />
            <span className="font-medium">{label}</span>
            {active && <ChevronRight className="ml-auto w-3.5 h-3.5 opacity-50" />}
        </Link>
    );
}

function MetricCard({ title, value, icon: Icon, trend, isSuccess = false }: { title: string, value: string | number, icon: any, trend: string, isSuccess?: boolean }) {
    return (
        <div className="cartesia-card hover:border-primary/30 group">
            <div className="flex items-start justify-between mb-6">
                <div className="w-10 h-10 rounded-xl bg-white/5 border border-border flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Icon className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
                <div className={`text-[10px] font-bold flex items-center gap-1.5 px-2.5 py-1 rounded-lg border ${isSuccess ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-primary/10 text-primary border-primary/20'}`}>
                    {trend}
                </div>
            </div>
            <div className="text-4xl font-display font-bold tracking-tight mb-1 text-white">{value}</div>
            <div className="text-xs font-bold text-muted-foreground uppercase tracking-widest">{title}</div>
        </div>
    );
}
