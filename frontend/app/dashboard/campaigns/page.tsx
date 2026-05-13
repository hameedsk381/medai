'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    Activity,
    Calendar,
    Stethoscope,
    Users,
    MessageSquare,
    BookOpen,
    ShieldCheck,
    Settings,
    LogOut,
    Plus,
    Send,
    RefreshCw,
    Loader2,
    CheckCircle,
    Clock,
    AlertCircle,
    ArrowLeft,
    ChevronRight,
    Command,
    X,
    Filter,
    Search,
    Type,
    Phone
} from 'lucide-react';
import { useAuth } from '@/app/context/AuthContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface CampaignRecipient {
    id: string;
    phone_number: string;
    status: 'pending' | 'sent' | 'failed';
    error_message?: string;
    sent_at?: string;
}

interface Campaign {
    id: string;
    name: string;
    message_template: string;
    status: 'pending' | 'sending' | 'completed' | 'failed';
    created_at: string;
    sent_at?: string;
    total_recipients: number;
    success_count: number;
    failure_count: number;
}

export default function CampaignsPage() {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [activeCampaign, setActiveCampaign] = useState<any>(null);
    const [showDetailsModal, setShowDetailsModal] = useState(false);
    const { token, logout } = useAuth();

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        message_template: '',
        recipient_phones: [] as string[],
        phone_input: '',
        use_all_patients: false
    });

    useEffect(() => {
        fetchCampaigns();
    }, []);

    const fetchCampaigns = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_URL}/api/campaigns`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                setCampaigns(await response.json());
            }
        } catch (error) {
            console.error('Failed to fetch campaigns:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchCampaignDetails = async (id: string) => {
        try {
            const response = await fetch(`${API_URL}/api/campaigns/${id}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const details = await response.json();
                setActiveCampaign(details);
                setShowDetailsModal(true);
            }
        } catch (error) {
            console.error('Failed to fetch campaign details:', error);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        const phones = [...formData.recipient_phones];
        if (formData.use_all_patients) {
            phones.push('all_patients');
        }
        
        if (phones.length === 0) {
            alert('Please add at least one recipient or select "All Patients"');
            return;
        }

        try {
            const response = await fetch(`${API_URL}/api/campaigns`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: formData.name,
                    message_template: formData.message_template,
                    recipient_phones: phones
                })
            });

            if (response.ok) {
                setShowAddModal(false);
                resetForm();
                fetchCampaigns();
            } else {
                const err = await response.json();
                alert(`Error: ${err.detail || 'Failed to create campaign'}`);
            }
        } catch (error) {
            console.error('Error creating campaign:', error);
        }
    };

    const runCampaign = async (id: string) => {
        try {
            const response = await fetch(`${API_URL}/api/campaigns/${id}/run`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                fetchCampaigns();
            }
        } catch (error) {
            console.error('Error running campaign:', error);
        }
    };

    const resetForm = () => {
        setFormData({
            name: '',
            message_template: '',
            recipient_phones: [],
            phone_input: '',
            use_all_patients: false
        });
    };

    const addPhone = () => {
        if (formData.phone_input.trim()) {
            setFormData(prev => ({
                ...prev,
                recipient_phones: [...prev.recipient_phones, prev.phone_input.trim()],
                phone_input: ''
            }));
        }
    };

    const removePhone = (index: number) => {
        setFormData(prev => ({
            ...prev,
            recipient_phones: prev.recipient_phones.filter((_, i) => i !== index)
        }));
    };

    const getStatusStyles = (status: string) => {
        switch (status) {
            case 'completed': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
            case 'sending': return 'text-primary bg-primary/10 border-primary/20 animate-pulse';
            case 'pending': return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
            case 'failed': return 'text-rose-400 bg-rose-400/10 border-rose-400/20';
            default: return 'text-muted-foreground bg-muted border-border';
        }
    };

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden font-display">
            {/* Ambient Glows */}
            <div className="fixed top-0 right-0 w-[50%] h-[50%] bg-primary/5 blur-[120px] rounded-full -z-10" />
            <div className="fixed bottom-0 left-0 w-[40%] h-[40%] bg-secondary/5 blur-[120px] rounded-full -z-10" />

            {/* Sidebar (Duplicate of Dashboard Sidebar but themed) */}
            <aside className="w-72 border-r border-border bg-black/40 backdrop-filter backdrop-blur-xl flex flex-col p-6 space-y-8 z-50">
                <div className="flex items-center gap-2 px-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-primary to-secondary flex items-center justify-center shadow-lg shadow-primary/20">
                        <Command className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-lg font-bold tracking-tight">MedVoice AI</span>
                </div>

                <nav className="flex-1 space-y-1.5 overflow-y-auto pr-2 custom-scrollbar">
                    <SidebarLink href="/dashboard" icon={Activity} label="Command Center" />
                    <SidebarLink href="/dashboard/appointments" icon={Calendar} label="Appointments" />
                    <SidebarLink href="/dashboard/doctors" icon={Stethoscope} label="Medical Staff" />
                    <SidebarLink href="/dashboard/campaigns" icon={Send} label="Outbound Flow" active />
                    <SidebarLink href="/dashboard/conversations" icon={MessageSquare} label="Neural Logs" />
                    <SidebarLink href="/dashboard/knowledge" icon={BookOpen} label="Intelligence Base" />

                    <div className="pt-6 pb-2 px-4">
                        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em]">Management</span>
                    </div>

                    <SidebarLink href="/dashboard/compliance" icon={ShieldCheck} label="Security Core" />
                    <SidebarLink href="/dashboard/settings" icon={Settings} label="System Config" />
                </nav>

                <div className="pt-4 border-t border-border">
                    <button onClick={logout} className="flex items-center gap-3 text-muted-foreground hover:text-white hover:bg-white/5 w-full p-3 rounded-xl transition-all font-medium text-sm">
                        <LogOut className="w-4 h-4" />
                        Disconnect
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto p-10 space-y-8 pb-32">
                <header className="flex items-center justify-between pb-6 border-b border-border/50">
                    <div className="space-y-1">
                        <h1 className="text-3xl font-semibold tracking-tight text-white">Outbound Flow</h1>
                        <p className="text-xs font-medium text-muted-foreground uppercase tracking-[0.1em]">WhatsApp Automation & Campaign Management</p>
                    </div>

                    <div className="flex items-center gap-4">
                        <button onClick={fetchCampaigns} className="p-2.5 border border-border rounded-xl hover:bg-white/5 transition-all">
                            <RefreshCw className={`w-4 h-4 text-white ${loading ? 'animate-spin' : ''}`} />
                        </button>
                        <button 
                            onClick={() => setShowAddModal(true)}
                            className="btn-sarvam-primary flex items-center gap-2"
                        >
                            <Plus className="w-5 h-5" />
                            Launch Campaign
                        </button>
                    </div>
                </header>

                {/* Campaigns List */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {loading ? (
                        Array(6).fill(0).map((_, i) => (
                            <div key={i} className="cartesia-card animate-pulse h-64 bg-white/5" />
                        ))
                    ) : campaigns.length > 0 ? (
                        campaigns.map((campaign) => (
                            <div key={campaign.id} className="cartesia-card group hover:border-primary/30 transition-all cursor-pointer flex flex-col justify-between" onClick={() => fetchCampaignDetails(campaign.id)}>
                                <div className="space-y-4">
                                    <div className="flex items-start justify-between">
                                        <div className={`px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase border ${getStatusStyles(campaign.status)}`}>
                                            {campaign.status}
                                        </div>
                                        <div className="text-[10px] text-muted-foreground font-mono">
                                            {new Date(campaign.created_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-bold text-white mb-1">{campaign.name}</h3>
                                        <p className="text-xs text-muted-foreground line-clamp-2 italic">"{campaign.message_template}"</p>
                                    </div>
                                </div>

                                <div className="mt-8 space-y-4">
                                    <div className="grid grid-cols-3 gap-2">
                                        <div className="p-2 bg-white/5 rounded-xl border border-border">
                                            <div className="text-[10px] font-bold text-muted-foreground uppercase mb-1">Total</div>
                                            <div className="text-lg font-bold text-white">{campaign.total_recipients}</div>
                                        </div>
                                        <div className="p-2 bg-emerald-500/5 rounded-xl border border-emerald-500/10">
                                            <div className="text-[10px] font-bold text-emerald-500 uppercase mb-1">Sent</div>
                                            <div className="text-lg font-bold text-emerald-400">{campaign.success_count}</div>
                                        </div>
                                        <div className="p-2 bg-rose-500/5 rounded-xl border border-rose-500/10">
                                            <div className="text-[10px] font-bold text-rose-500 uppercase mb-1">Failed</div>
                                            <div className="text-lg font-bold text-rose-400">{campaign.failure_count}</div>
                                        </div>
                                    </div>

                                    {campaign.status === 'pending' ? (
                                        <button 
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                runCampaign(campaign.id);
                                            }}
                                            className="w-full py-2.5 bg-primary text-white rounded-xl text-xs font-bold uppercase tracking-widest hover:bg-primary/80 transition-all flex items-center justify-center gap-2"
                                        >
                                            <Send className="w-4 h-4" />
                                            Execute Script
                                        </button>
                                    ) : (
                                        <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                                            <div 
                                                className="h-full bg-primary transition-all duration-1000" 
                                                style={{ width: `${(campaign.success_count + campaign.failure_count) / campaign.total_recipients * 100}%` }}
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="col-span-full py-40 text-center space-y-4">
                            <Send className="w-16 h-16 text-muted-foreground/20 mx-auto" />
                            <h2 className="text-2xl font-bold text-white">No active flows</h2>
                            <p className="text-muted-foreground max-w-sm mx-auto text-sm font-medium leading-relaxed">Broadcast clinical notifications or marketing messages via secure WhatsApp channels.</p>
                            <button onClick={() => setShowAddModal(true)} className="btn-sarvam-primary mx-auto mt-6">Initialize First Flow</button>
                        </div>
                    )}
                </div>
            </main>

            {/* Create Campaign Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-[100] flex items-center justify-center p-6 animate-in fade-in duration-300">
                    <div className="bg-background border border-border rounded-[32px] w-full max-w-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
                        <div className="p-8 border-b border-border flex items-center justify-between">
                            <div>
                                <h2 className="text-2xl font-bold text-white tracking-tight">Campaign Provisioning</h2>
                                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mt-1">Configure automated outbound protocols</p>
                            </div>
                            <button onClick={() => setShowAddModal(false)} className="p-2 hover:bg-white/5 rounded-full transition-colors border border-border/50">
                                <X className="w-5 h-5 text-white" />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="p-8 space-y-6">
                            <div className="space-y-2">
                                <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest ml-1">Flow Identity</label>
                                <input 
                                    type="text" 
                                    required
                                    placeholder="Appointment Recall 2024"
                                    value={formData.name}
                                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                                    className="w-full bg-white/5 border border-border rounded-2xl px-5 py-4 text-white outline-none focus:border-primary/50 transition-all shadow-inner placeholder:text-muted-foreground/30"
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest ml-1">Neural Template (Message Content)</label>
                                <textarea 
                                    required
                                    placeholder="Hello! This is a reminder from MedClinic about your pending health check..."
                                    rows={4}
                                    value={formData.message_template}
                                    onChange={(e) => setFormData({...formData, message_template: e.target.value})}
                                    className="w-full bg-white/5 border border-border rounded-2xl px-5 py-4 text-white outline-none focus:border-primary/50 transition-all shadow-inner placeholder:text-muted-foreground/30 resize-none font-medium text-sm"
                                />
                            </div>

                            <div className="space-y-4">
                                <div className="flex items-center justify-between ml-1">
                                    <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Recipient Array</label>
                                    <button 
                                        type="button" 
                                        onClick={() => setFormData({...formData, use_all_patients: !formData.use_all_patients})}
                                        className={`text-[10px] font-bold px-3 py-1 rounded-lg border transition-all ${formData.use_all_patients ? 'bg-primary/20 text-primary border-primary/30' : 'bg-white/5 text-muted-foreground border-border'}`}
                                    >
                                        TARGET ALL PATIENTS
                                    </button>
                                </div>

                                {!formData.use_all_patients && (
                                    <div className="space-y-3">
                                        <div className="flex gap-2">
                                            <input 
                                                type="tel" 
                                                placeholder="+91 00000 00000"
                                                value={formData.phone_input}
                                                onChange={(e) => setFormData({...formData, phone_input: e.target.value})}
                                                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addPhone())}
                                                className="flex-1 bg-white/5 border border-border rounded-xl px-4 py-3 text-white outline-none focus:border-primary/50 transition-all text-sm"
                                            />
                                            <button 
                                                type="button" 
                                                onClick={addPhone}
                                                className="p-3 bg-white/5 border border-border rounded-xl hover:bg-white/10 transition-all"
                                            >
                                                <Plus className="w-5 h-5 text-white" />
                                            </button>
                                        </div>
                                        <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 border border-border/30 rounded-xl bg-black/20 custom-scrollbar">
                                            {formData.recipient_phones.map((phone, i) => (
                                                <div key={i} className="flex items-center gap-2 bg-white/5 border border-border px-3 py-1.5 rounded-lg text-xs font-mono text-primary group">
                                                    {phone}
                                                    <X className="w-3 h-3 cursor-pointer hover:text-white transition-colors" onClick={() => removePhone(i)} />
                                                </div>
                                            ))}
                                            {formData.recipient_phones.length === 0 && (
                                                <span className="text-[10px] text-muted-foreground/50 py-1 px-2 font-medium">No custom targets defined...</span>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="flex gap-4 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setShowAddModal(false)}
                                    className="flex-1 py-4 border border-border text-white rounded-2xl font-bold text-xs uppercase tracking-widest hover:bg-white/5 transition-all"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 py-4 bg-primary text-white rounded-2xl font-bold text-xs uppercase tracking-widest shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all"
                                >
                                    Initialize Flow
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Campaign Details Modal */}
            {showDetailsModal && activeCampaign && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-[100] flex items-center justify-center p-6 animate-in fade-in duration-300">
                    <div className="bg-background border border-border rounded-[32px] w-full max-w-4xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300 flex flex-col max-h-[90vh]">
                        <div className="p-8 border-b border-border flex items-center justify-between shrink-0">
                            <div className="flex items-center gap-4">
                                <Link href="#" onClick={(e) => { e.preventDefault(); setShowDetailsModal(false); }} className="p-2 border border-border rounded-full hover:bg-white/5 transition-all">
                                    <ArrowLeft className="w-4 h-4 text-white" />
                                </Link>
                                <div>
                                    <h2 className="text-2xl font-bold text-white tracking-tight">{activeCampaign.campaign.name}</h2>
                                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Neural Delivery Audit Log</p>
                                </div>
                            </div>
                            <div className={`px-3 py-1 rounded-lg text-[10px] font-bold uppercase border ${getStatusStyles(activeCampaign.campaign.status)}`}>
                                {activeCampaign.campaign.status}
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-8">
                            <div className="grid grid-cols-4 gap-4">
                                <AuditCard title="Total Capacity" value={activeCampaign.campaign.total_recipients} icon={Users} />
                                <AuditCard title="Successful Handshakes" value={activeCampaign.campaign.success_count} icon={CheckCircle} color="text-emerald-400" />
                                <AuditCard title="Injection Failures" value={activeCampaign.campaign.failure_count} icon={AlertCircle} color="text-rose-400" />
                                <AuditCard title="Completion Epoch" value={activeCampaign.campaign.sent_at ? new Date(activeCampaign.campaign.sent_at).toLocaleTimeString() : '---'} icon={Clock} />
                            </div>

                            <div className="space-y-4">
                                <h3 className="text-xs font-bold text-white uppercase tracking-widest ml-1">Delivery Matrix</h3>
                                <div className="cartesia-card p-0 overflow-hidden">
                                    <table className="w-full text-left">
                                        <thead className="bg-white/5 border-b border-border">
                                            <tr>
                                                <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Endpoint</th>
                                                <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Status</th>
                                                <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">SID / Error</th>
                                                <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-widest text-muted-foreground text-right">Timestamp</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-border/30">
                                            {activeCampaign.recipients.map((r: any) => (
                                                <tr key={r.id} className="hover:bg-white/[0.02] transition">
                                                    <td className="px-6 py-4 font-mono text-xs text-primary">{r.phone_number}</td>
                                                    <td className="px-6 py-4">
                                                        <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold uppercase border ${
                                                            r.status === 'sent' ? 'text-emerald-400 border-emerald-400/20 bg-emerald-400/5' : 
                                                            r.status === 'failed' ? 'text-rose-400 border-rose-400/20 bg-rose-400/5' : 
                                                            'text-amber-400 border-amber-400/20 bg-amber-400/5'
                                                        }`}>
                                                            {r.status}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-xs font-medium text-muted-foreground truncate max-w-[200px]">
                                                        {r.message_sid || r.error_message || '---'}
                                                    </td>
                                                    <td className="px-6 py-4 text-[10px] text-muted-foreground text-right">
                                                        {r.sent_at ? new Date(r.sent_at).toLocaleTimeString() : '---'}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div className="p-8 border-t border-border bg-black/20 shrink-0">
                            <button 
                                onClick={() => setShowDetailsModal(false)}
                                className="w-full py-4 bg-white/5 border border-border text-white rounded-2xl font-bold text-xs uppercase tracking-widest hover:bg-white/10 transition-all"
                            >
                                Close Audit
                            </button>
                        </div>
                    </div>
                </div>
            )}

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

function AuditCard({ title, value, icon: Icon, color = "text-muted-foreground" }: any) {
    return (
        <div className="p-5 bg-white/5 border border-border rounded-2xl space-y-3">
            <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{title}</span>
                <Icon className={`w-4 h-4 ${color}`} />
            </div>
            <div className={`text-2xl font-bold ${color === "text-muted-foreground" ? "text-white" : color}`}>{value}</div>
        </div>
    );
}
