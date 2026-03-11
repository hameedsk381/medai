'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    Activity,
    BookOpen,
    Clock,
    MapPin,
    ShieldCheck,
    Plus,
    Trash2,
    Save,
    Info,
    ArrowLeft,
    HelpCircle,
    Calendar,
    Phone,
    Stethoscope,
    MessageSquare,
    Settings,
    LogOut,
    BrainCircuit,
    ChevronRight,
    Sparkles,
    Loader2,
    ArrowUpRight
} from 'lucide-react';
import { useAuth } from '@/app/context/AuthContext';

interface KnowledgeItem {
    id: string;
    category: 'general' | 'hours' | 'policy' | 'faq';
    key: string;
    value: string;
}

export default function KnowledgePage() {
    const { token, logout } = useAuth();
    const [items, setItems] = useState<KnowledgeItem[]>([]);
    const [loading, setLoading] = useState(true);

    // New item states
    const [newFaqQ, setNewFaqQ] = useState('');
    const [newFaqA, setNewFaqA] = useState('');
    const [newPolicy, setNewPolicy] = useState('');

    useEffect(() => {
        if (token) {
            fetchKnowledge();
        }
    }, [token]);

    const fetchKnowledge = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/knowledge`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setItems(data);
            }
        } catch (err) {
            console.error('Failed to fetch knowledge:', err);
        } finally {
            setLoading(false);
        }
    };

    const saveItem = async (category: string, key: string, value: string) => {
        if (!value.trim()) return;
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/knowledge`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ category, key, value })
            });
            if (res.ok) {
                fetchKnowledge();
            }
        } catch (err) {
            console.error('Save failed:', err);
        }
    };

    const deleteItem = async (id: string) => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/knowledge/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                setItems(items.filter(i => i.id !== id));
            }
        } catch (err) {
            console.error('Delete failed:', err);
        }
    };

    const getItemValue = (category: string, key: string) => {
        return items.find(i => i.category === category && i.key === key)?.value || '';
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
                    <SidebarLink href="/dashboard/knowledge" icon={BookOpen} label="Intelligence Lab" active />
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
                    <div>
                        <h1 className="text-4xl text-foreground tracking-tighter mb-1">Intelligence Laboratory</h1>
                        <p className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em]">Neural Behavior & Protocol Engineering</p>
                    </div>
                    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/5 text-[9px] font-black text-indigo-500 uppercase tracking-widest border border-indigo-500/10">
                        <BrainCircuit className="w-3.5 h-3.5" />
                        Neural Sync Active
                    </div>
                </header>

                <div className="max-w-7xl mx-auto space-y-12 animate-fade-in">

                    {/* Lab Overview Hero */}
                    <div className="sarvam-card bg-[#131313] text-white overflow-hidden relative group">
                        <div className="absolute -right-20 -top-20 opacity-10 group-hover:scale-125 transition-transform duration-1000">
                            <Sparkles className="w-64 h-64 text-white" />
                        </div>
                        <div className="relative z-10 space-y-6">
                            <h2 className="text-5xl tracking-tighter" style={{ fontFamily: "'DM Serif Text', serif" }}>Refining Neural Awareness.</h2>
                            <p className="text-xl text-white/50 leading-relaxed max-w-2xl font-medium">
                                Architect your AI agent's responses by defining facility-specific protocols and patient interactions. Changes take effect across all voice pipelines instantly.
                            </p>
                        </div>
                    </div>

                    <div className="grid lg:grid-cols-3 gap-10">

                        <div className="space-y-10">
                            {/* General & Info */}
                            <div className="sarvam-card bg-card border border-border space-y-8">
                                <h3 className="text-[11px] font-black uppercase tracking-[0.3em] text-muted-foreground">Facility Profile</h3>
                                <div className="space-y-6">
                                    <div className="space-y-3">
                                        <label className="block text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Archive Address</label>
                                        <textarea
                                            className="w-full px-5 py-4 bg-muted border border-border rounded-[24px] text-sm focus:ring-1 focus:ring-foreground outline-none transition-all"
                                            rows={2}
                                            value={getItemValue('general', 'address')}
                                            onChange={(e) => {
                                                const newItems = [...items];
                                                const idx = newItems.findIndex(i => i.category === 'general' && i.key === 'address');
                                                if (idx > -1) newItems[idx].value = e.target.value;
                                                else newItems.push({ id: 'temp', category: 'general', key: 'address', value: e.target.value });
                                                setItems(newItems);
                                            }}
                                            onBlur={(e) => saveItem('general', 'address', e.target.value)}
                                            placeholder="Facility geographic coordinates..."
                                        />
                                    </div>
                                    <div className="space-y-3">
                                        <label className="block text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">Direct Liaison Line</label>
                                        <div className="relative">
                                            <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-border" />
                                            <input
                                                type="text"
                                                className="w-full pl-12 pr-6 py-4 bg-muted border border-border rounded-full text-sm focus:ring-1 focus:ring-foreground outline-none transition-all"
                                                value={getItemValue('general', 'phone')}
                                                onChange={(e) => {
                                                    const newItems = [...items];
                                                    const idx = newItems.findIndex(i => i.category === 'general' && i.key === 'phone');
                                                    if (idx > -1) newItems[idx].value = e.target.value;
                                                    else newItems.push({ id: 'temp', category: 'general', key: 'phone', value: e.target.value });
                                                    setItems(newItems);
                                                }}
                                                onBlur={(e) => saveItem('general', 'phone', e.target.value)}
                                                placeholder="+1 000 000 0000"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Business Hours */}
                            <div className="sarvam-card bg-card border border-border space-y-8">
                                <h3 className="text-[11px] font-black uppercase tracking-[0.3em] text-muted-foreground">Clinical Cycles</h3>
                                <div className="space-y-6">
                                    {['Weekdays', 'Saturday', 'Sunday'].map(day => (
                                        <div key={day} className="space-y-2">
                                            <span className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1 font-sans">{day}</span>
                                            <input
                                                type="text"
                                                className="w-full px-5 py-4 bg-muted border border-border rounded-full text-sm focus:ring-1 focus:ring-foreground outline-none transition-all"
                                                placeholder="Availability protocol..."
                                                value={getItemValue('hours', day)}
                                                onBlur={(e) => saveItem('hours', day, e.target.value)}
                                                onChange={(e) => {
                                                    const newItems = [...items];
                                                    const idx = newItems.findIndex(i => i.category === 'hours' && i.key === day);
                                                    if (idx > -1) newItems[idx].value = e.target.value;
                                                    else newItems.push({ id: 'temp', category: 'hours', key: day, value: e.target.value });
                                                    setItems(newItems);
                                                }}
                                            />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Protocols & FAQs */}
                        <div className="lg:col-span-2 space-y-10">

                            {/* Operational Protocols */}
                            <div className="sarvam-card bg-card border border-border space-y-8">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-3xl tracking-tight text-foreground">Clinical Protocols</h3>
                                    <div className="px-4 py-1.5 rounded-full bg-emerald-500/5 text-[9px] font-black text-emerald-500 uppercase tracking-widest border border-emerald-500/10">Active</div>
                                </div>
                                <div className="space-y-4">
                                    {items.filter(i => i.category === 'policy').map(policy => (
                                        <div key={policy.id} className="flex items-start justify-between gap-6 p-6 rounded-[32px] bg-muted border border-border group hover:border-foreground transition-all">
                                            <p className="text-base text-foreground flex-1 leading-relaxed font-medium italic">"{policy.value}"</p>
                                            <button
                                                onClick={() => deleteItem(policy.id)}
                                                className="text-border hover:text-rose-500 transition-colors py-2 px-1"
                                            >
                                                <Trash2 className="w-5 h-5" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                                <div className="flex gap-4 pt-4">
                                    <input
                                        type="text"
                                        placeholder="Define architectural protocol..."
                                        className="flex-1 px-8 py-5 bg-muted border border-border rounded-full text-sm focus:ring-1 focus:ring-foreground outline-none shadow-sm"
                                        value={newPolicy}
                                        onChange={(e) => setNewPolicy(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && (saveItem('policy', `policy-${Date.now()}`, newPolicy), setNewPolicy(''))}
                                    />
                                    <button
                                        onClick={() => { saveItem('policy', `policy-${Date.now()}`, newPolicy); setNewPolicy(''); }}
                                        className="btn-sarvam-primary !p-5"
                                    >
                                        <Plus className="w-6 h-6" />
                                    </button>
                                </div>
                            </div>

                            {/* Intelligent Response Grid */}
                            <div className="sarvam-card bg-card border border-border space-y-10">
                                <h3 className="text-3xl tracking-tight text-foreground">Neural Response Tree</h3>
                                <div className="grid grid-cols-1 gap-6">
                                    {items.filter(i => i.category === 'faq').map(faq => (
                                        <div key={faq.id} className="p-8 rounded-[40px] bg-muted border border-border group hover:bg-card hover:border-foreground/20 transition-all space-y-4">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-4">
                                                    <div className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.3em]">Neural Trigger</div>
                                                    <h4 className="text-lg font-bold text-foreground">{faq.key}</h4>
                                                </div>
                                                <button
                                                    onClick={() => deleteItem(faq.id)}
                                                    className="text-border hover:text-rose-500 transition-colors"
                                                >
                                                    <Trash2 className="w-5 h-5" />
                                                </button>
                                            </div>
                                            <div className="pl-6 border-l-2 border-foreground/5">
                                                <p className="text-base text-muted-foreground leading-relaxed italic">"{faq.value}"</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                <div className="sarvam-card bg-[#131313] text-white space-y-8">
                                    <div className="flex items-center gap-3">
                                        <Sparkles className="w-5 h-5 text-white/40" />
                                        <h3 className="text-lg font-black uppercase tracking-[0.3em] text-white/40">Program Neural Behavior</h3>
                                    </div>
                                    <div className="space-y-6">
                                        <input
                                            type="text"
                                            placeholder="Simulated Patient Inquiry..."
                                            className="w-full px-8 py-5 bg-white/5 border border-white/10 text-white placeholder:text-white/30 rounded-full text-sm outline-none focus:ring-1 focus:ring-white/40 transition-all"
                                            value={newFaqQ}
                                            onChange={(e) => setNewFaqQ(e.target.value)}
                                        />
                                        <textarea
                                            placeholder="Standard Protocol Response..."
                                            className="w-full px-8 py-5 bg-white/5 border border-white/10 text-white placeholder:text-white/30 rounded-[32px] text-sm outline-none focus:ring-1 focus:ring-white/40 transition-all"
                                            rows={3}
                                            value={newFaqA}
                                            onChange={(e) => setNewFaqA(e.target.value)}
                                        />
                                        <button
                                            onClick={() => {
                                                saveItem('faq', newFaqQ, newFaqA);
                                                setNewFaqQ('');
                                                setNewFaqA('');
                                            }}
                                            disabled={!newFaqQ || !newFaqA}
                                            className="w-full py-5 bg-white text-[#131313] rounded-full font-black shadow-xl hover:bg-slate-50 transition-all disabled:opacity-30 uppercase tracking-[0.2em] text-xs"
                                        >
                                            Commit to Neural Core
                                        </button>
                                    </div>
                                </div>
                            </div>

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
