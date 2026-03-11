'use client';

import { type ElementType, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import {
    Activity,
    AlertCircle,
    BookOpen,
    Calendar,
    Command,
    LogOut,
    MessageSquare,
    PhoneCall,
    Play,
    Radio,
    RefreshCw,
    Settings,
    ShieldCheck,
    Square,
    Stethoscope,
    Waves
} from 'lucide-react';
import { useAuth } from '@/app/context/AuthContext';
import VoiceInterface from '@/components/VoiceInterface';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type LogEntry = {
    id: number;
    level: 'info' | 'success' | 'error';
    message: string;
};

export default function VoicePipelinePage() {
    const { token, logout } = useAuth();
    const [phoneNumber, setPhoneNumber] = useState('+918801260321');
    const [triggering, setTriggering] = useState(false);
    const [callSid, setCallSid] = useState<string | null>(null);
    const [socketState, setSocketState] = useState<'idle' | 'connecting' | 'open' | 'closed' | 'error'>('idle');
    const [socketBusy, setSocketBusy] = useState(false);
    const [logs, setLogs] = useState<LogEntry[]>([
        { id: 1, level: 'info', message: 'Voice console ready.' }
    ]);
    const socketRef = useRef<WebSocket | null>(null);
    const nextLogId = useRef(2);

    const wsUrl = useMemo(() => {
        if (API_URL.startsWith('https://')) return API_URL.replace('https://', 'wss://') + '/voice-stream';
        if (API_URL.startsWith('http://')) return API_URL.replace('http://', 'ws://') + '/voice-stream';
        return `${API_URL}/voice-stream`;
    }, []);

    const webWsUrl = useMemo(() => {
        if (API_URL.startsWith('https://')) return API_URL.replace('https://', 'wss://') + '/web-voice-stream';
        if (API_URL.startsWith('http://')) return API_URL.replace('http://', 'ws://') + '/web-voice-stream';
        return `${API_URL}/web-voice-stream`;
    }, []);

    const addLog = (message: string, level: LogEntry['level'] = 'info') => {
        setLogs((current) => [
            { id: nextLogId.current++, level, message },
            ...current
        ].slice(0, 16));
    };

    useEffect(() => {
        return () => {
            if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                socketRef.current.close();
            }
        };
    }, []);

    const triggerOutboundCall = async () => {
        if (!token) {
            addLog('Login required before triggering the outbound voice flow.', 'error');
            return;
        }

        setTriggering(true);
        setCallSid(null);

        try {
            const response = await fetch(`${API_URL}/api/voice/trigger-outcall`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ phone_number: phoneNumber })
            });

            const payload = await response.json();

            if (!response.ok) {
                throw new Error(payload.detail || payload.message || 'Trigger failed');
            }

            setCallSid(payload.call_sid || null);
            addLog(`Outbound call queued successfully (${payload.call_sid}).`, 'success');
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Trigger failed';
            addLog(message, 'error');
        } finally {
            setTriggering(false);
        }
    };

    const connectProbe = async () => {
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            addLog('Socket probe already connected.');
            return;
        }

        setSocketBusy(true);
        setSocketState('connecting');
        addLog(`Connecting socket probe to ${wsUrl} ...`);

        try {
            const socket = new WebSocket(wsUrl);
            socketRef.current = socket;

            socket.onopen = () => {
                setSocketState('open');
                setSocketBusy(false);
                addLog('WebSocket probe connected.', 'success');
            };

            socket.onmessage = (event) => {
                addLog(`Socket event: ${event.data}`);
            };

            socket.onerror = () => {
                setSocketState('error');
                setSocketBusy(false);
                addLog('WebSocket probe error.', 'error');
            };

            socket.onclose = () => {
                setSocketState('closed');
                setSocketBusy(false);
                addLog('WebSocket probe disconnected.');
            };
        } catch (error) {
            setSocketState('error');
            setSocketBusy(false);
            const message = error instanceof Error ? error.message : 'Probe connection failed';
            addLog(message, 'error');
        }
    };

    const sendStartEvent = () => {
        const socket = socketRef.current;
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            addLog('Open the socket probe before sending a start event.', 'error');
            return;
        }

        socket.send(JSON.stringify({
            event: 'start',
            start: {
                streamSid: 'ui-probe-stream',
                callSid: 'ui-probe-call',
                customParameters: {
                    business_id: 'ui-probe',
                    is_outbound: 'true',
                    caller: phoneNumber
                }
            }
        }));

        addLog('Synthetic start event sent to the voice pipeline.', 'success');
    };

    const disconnectProbe = () => {
        if (socketRef.current) {
            socketRef.current.close();
            socketRef.current = null;
        }
    };

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden">
            <div className="fixed top-0 right-0 w-[50%] h-[50%] bg-primary/5 blur-[120px] rounded-full -z-10" />
            <div className="fixed bottom-0 left-0 w-[40%] h-[40%] bg-secondary/5 blur-[120px] rounded-full -z-10" />

            <aside className="w-72 border-r border-border bg-black/40 backdrop-filter backdrop-blur-xl flex flex-col p-6 space-y-8 z-50">
                <div className="flex items-center gap-2 px-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-primary to-secondary flex items-center justify-center shadow-lg shadow-primary/20">
                        <Command className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-lg font-bold tracking-tight font-display">MedVoice AI</span>
                </div>

                <nav className="flex-1 space-y-1.5 overflow-y-auto pr-2 custom-scrollbar">
                    <SidebarLink href="/dashboard" icon={Activity} label="Command Center" />
                    <SidebarLink href="/dashboard/voice" icon={Radio} label="Voice Pipeline" active />
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

            <main className="flex-1 overflow-y-auto custom-scrollbar p-10 space-y-8 pb-32">
                <header className="flex items-center justify-between pb-6 border-b border-border/50">
                    <div className="space-y-2">
                        <div className="badge-premium py-1 lowercase inline-flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                            voice orchestration panel
                        </div>
                        <h1 className="text-3xl font-display font-semibold tracking-tight text-white">Voice Pipeline Console</h1>
                        <p className="text-sm text-muted-foreground max-w-2xl">
                            Trigger outbound calls, probe the Twilio websocket, and validate the live voice path without leaving the dashboard.
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <a
                            href={`${API_URL}/docs`}
                            target="_blank"
                            rel="noreferrer"
                            className="px-4 py-2 rounded-xl border border-border bg-white/5 hover:bg-white/10 transition-all text-sm font-medium"
                        >
                            Backend Docs
                        </a>
                        <button
                            onClick={() => addLog('Console refreshed.')}
                            className="p-2.5 rounded-xl border border-border hover:bg-white/10 transition-all"
                        >
                            <RefreshCw className="w-4 h-4" />
                        </button>
                    </div>
                </header>

                <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <StatusCard title="API Base" value={API_URL} icon={PhoneCall} tone="primary" />
                    <StatusCard title="WebSocket" value={wsUrl} icon={Waves} tone="secondary" />
                    <StatusCard title="Probe State" value={socketState.toUpperCase()} icon={Radio} tone={socketState === 'open' ? 'success' : 'neutral'} />
                </section>

                <section className="grid grid-cols-1 xl:grid-cols-[1.2fr,0.8fr] gap-8">
                    {/* Real-time Web Voice Interface */}
                    <div className="cartesia-card space-y-6 flex flex-col h-[600px]">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-display font-semibold text-white">Live Web Agent</h2>
                                <p className="text-sm text-muted-foreground mt-1">
                                    Interact directly with the voice AI pipeline through your browser.
                                </p>
                            </div>
                            <Waves className="w-5 h-5 text-primary" />
                        </div>

                        <div className="flex-1 overflow-hidden min-h-0">
                            <VoiceInterface wsUrl={webWsUrl} token={token || undefined} />
                        </div>
                    </div>

                    <div className="space-y-8 flex flex-col">
                        <div className="cartesia-card space-y-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h2 className="text-xl font-display font-semibold text-white">Outbound Call Trigger</h2>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        Sends a real outbound call through Twilio.
                                    </p>
                                </div>
                                <PhoneCall className="w-5 h-5 text-primary" />
                            </div>

                            <div className="space-y-3">
                                <label className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Target Number</label>
                                <input
                                    value={phoneNumber}
                                    onChange={(event) => setPhoneNumber(event.target.value)}
                                    className="w-full px-4 py-3 bg-white/5 border border-border rounded-xl text-white outline-none focus:border-primary/50 transition-all font-mono"
                                    placeholder="+91..."
                                />
                            </div>

                            <div className="flex flex-wrap gap-3">
                                <button
                                    onClick={triggerOutboundCall}
                                    disabled={triggering || !token}
                                    className="px-5 py-3 rounded-xl bg-primary text-white font-semibold hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all inline-flex items-center gap-2"
                                >
                                    <Play className="w-4 h-4" />
                                    {triggering ? 'Triggering...' : 'Trigger Outbound'}
                                </button>
                                <Link
                                    href="/dashboard/conversations"
                                    className="px-5 py-3 rounded-xl border border-border bg-white/5 hover:bg-white/10 transition-all inline-flex items-center gap-2 text-sm font-medium"
                                >
                                    <MessageSquare className="w-4 h-4" />
                                    Logs
                                </Link>
                            </div>
                        </div>

                        <div className="cartesia-card space-y-6 flex-1">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h2 className="text-xl font-display font-semibold text-white">WebSocket Probe</h2>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        Validate the `/voice-stream` path.
                                    </p>
                                </div>
                                <Radio className="w-5 h-5 text-secondary" />
                            </div>

                            <div className="flex flex-wrap gap-2">
                                <button
                                    onClick={connectProbe}
                                    disabled={socketBusy || socketState === 'open'}
                                    className="p-3 rounded-xl border border-border bg-white/5 hover:bg-white/10 disabled:opacity-50 transition-all text-sm font-medium"
                                    title="Connect"
                                >
                                    <Radio className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={sendStartEvent}
                                    disabled={socketState !== 'open'}
                                    className="px-4 py-3 rounded-xl border border-border bg-white/5 hover:bg-white/10 disabled:opacity-50 transition-all inline-flex items-center gap-2 text-sm font-medium"
                                >
                                    <Play className="w-4 h-4" />
                                    Start
                                </button>
                                <button
                                    onClick={disconnectProbe}
                                    disabled={socketState !== 'open'}
                                    className="p-3 rounded-xl border border-border bg-white/5 hover:bg-white/10 disabled:opacity-50 transition-all text-sm font-medium"
                                    title="Disconnect"
                                >
                                    <Square className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </div>
                </section>

                <section className="cartesia-card space-y-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-display font-semibold text-white">Activity Feed</h2>
                            <p className="text-sm text-muted-foreground mt-1">Recent UI-side voice operations and probe events.</p>
                        </div>
                    </div>

                    <div className="space-y-3">
                        {logs.map((entry) => (
                            <div
                                key={entry.id}
                                className={`rounded-2xl border px-4 py-3 text-sm ${entry.level === 'error'
                                    ? 'border-rose-500/20 bg-rose-500/10 text-rose-300'
                                    : entry.level === 'success'
                                        ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-300'
                                        : 'border-border bg-white/5 text-muted-foreground'
                                    }`}
                            >
                                <div className="flex items-start gap-3">
                                    <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                                    <span>{entry.message}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>
            </main>
        </div>
    );
}

function SidebarLink({ href, icon: Icon, label, active = false }: { href: string; icon: ElementType; label: string; active?: boolean; }) {
    return (
        <Link
            href={href}
            className={`flex items-center gap-4 p-4 rounded-2xl font-bold text-sm transition-all group ${active
                ? 'bg-white text-[#131313] shadow-lg shadow-white/5'
                : 'text-white/50 hover:bg-white/5 hover:text-white'
                }`}
        >
            <Icon className={`w-5 h-5 transition-colors ${active ? 'text-[#131313]' : 'text-white/30 group-hover:text-white'}`} />
            <span className="tracking-wide">{label}</span>
        </Link>
    );
}

function StatusCard({ title, value, icon: Icon, tone }: { title: string; value: string; icon: ElementType; tone: 'primary' | 'secondary' | 'success' | 'neutral'; }) {
    const toneMap = {
        primary: 'from-primary/20 to-primary/5 border-primary/20',
        secondary: 'from-secondary/20 to-secondary/5 border-secondary/20',
        success: 'from-emerald-500/20 to-emerald-500/5 border-emerald-500/20',
        neutral: 'from-white/10 to-white/5 border-border'
    } as const;

    return (
        <div className={`cartesia-card bg-gradient-to-br ${toneMap[tone]}`}>
            <div className="flex items-center justify-between mb-4">
                <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">{title}</span>
                <Icon className="w-5 h-5 text-white" />
            </div>
            <div className="text-sm text-white font-semibold break-all">{value}</div>
        </div>
    );
}

function InfoTile({ label, value }: { label: string; value: string; }) {
    return (
        <div className="rounded-2xl border border-border bg-white/5 px-4 py-4">
            <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground mb-2">{label}</div>
            <div className="text-sm font-semibold text-white break-all">{value}</div>
        </div>
    );
}
