'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Waves, Volume2, VolumeX, MessageSquare } from 'lucide-react';

interface VoiceInterfaceProps {
    wsUrl: string;
    token?: string;
}

export default function VoiceInterface({ wsUrl, token }: VoiceInterfaceProps) {
    const [isActive, setIsActive] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [isThinking, setIsThinking] = useState(false);
    const [transcript, setTranscript] = useState<{ text: string, role: string, is_final?: boolean }[]>([]);
    const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
    const [volume, setVolume] = useState(0);

    const socketRef = useRef<WebSocket | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const processorRef = useRef<ScriptProcessorNode | null>(null);
    const audioQueue = useRef<AudioBuffer[]>([]);
    const isPlaying = useRef(false);

    // Auto-scroll transcript
    const transcriptEndRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [transcript]);

    const startSession = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;

            const socket = new WebSocket(wsUrl);
            socketRef.current = socket;

            socket.onopen = () => {
                console.log('Connected to Web Voice Stream (Gemini AI)');
                setIsActive(true);
                setTranscript(prev => [...prev, { text: "Connected! Gemini STT is active.", role: "system" }]);
                setupAudioProcessing(stream);
            };

            socket.onmessage = async (event) => {
                const data = JSON.parse(event.data);

                if (data.event === 'transcript') {
                    setTranscript(prev => {
                        const last = prev[prev.length - 1];
                        if (last && last.role === data.role && data.role === 'user' && !last.is_final) {
                            const updated = [...prev];
                            updated[updated.length - 1] = { text: data.text, role: data.role, is_final: data.is_final };
                            return updated;
                        }
                        return [...prev, { text: data.text, role: data.role, is_final: data.is_final }];
                    });
                    if (data.role === 'user' && data.is_final) setIsThinking(true);
                    if (data.role === 'assistant') setIsThinking(false);
                } else if (data.event === 'audio') {
                    handleIncomingAudio(data.payload);
                } else if (data.event === 'clear') {
                    stopPlayback();
                }
            };

            socket.onclose = () => {
                stopSession();
                setTranscript(prev => [...prev, { text: "Connection closed.", role: "system" }]);
            };

            socket.onerror = (err) => {
                console.error('Socket error:', err);
                stopSession();
            };

        } catch (err) {
            console.error('Failed to start voice session:', err);
            alert("Please allow microphone access to talk to the AI.");
        }
    };

    const stopSession = () => {
        setIsActive(false);
        setIsAgentSpeaking(false);

        if (socketRef.current) {
            socketRef.current.close();
            socketRef.current = null;
        }

        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }

        if (processorRef.current) {
            processorRef.current.disconnect();
            processorRef.current = null;
        }

        if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }

        audioQueue.current = [];
        isPlaying.current = false;
    };

    const setupAudioProcessing = (stream: MediaStream) => {
        // Create audio context at 16kHz for uniform processing
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
        audioContextRef.current = audioContext;

        const source = audioContext.createMediaStreamSource(stream);
        // ScriptProcessor size 4096 gives us ~256ms of audio per chunk at 16kHz
        const processor = audioContext.createScriptProcessor(4096, 1, 1);
        processorRef.current = processor;

        const analyser = audioContext.createAnalyser();
        source.connect(analyser);

        processor.onaudioprocess = (e) => {
            if (!isActive || isMuted || !socketRef.current) return;

            const inputData = e.inputBuffer.getChannelData(0);
            
            // 1. Send Audio Chunks to Backend for Gemini STT
            // Convert Float32Array to Int16Array PCM
            const pcmData = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
            }
            
            // Convert to base64 for payload (or send as binary)
            // Sending as JSON payload for consistency with existing web pipeline
            const base64Audio = btoa(String.fromCharCode(...new Uint8Array(pcmData.buffer)));
            
            if (socketRef.current.readyState === WebSocket.OPEN) {
                socketRef.current.send(JSON.stringify({
                    event: 'audio_input',
                    payload: base64Audio
                }));
            }

            // 2. Analyze volume for UI
            let sum = 0;
            for (let i = 0; i < inputData.length; i++) sum += inputData[i] * inputData[i];
            setVolume(Math.sqrt(sum / inputData.length));
        };

        source.connect(processor);
        processor.connect(audioContext.destination);
    };

    const handleIncomingAudio = async (base64Payload: string) => {
        if (!audioContextRef.current) return;

        const binaryString = atob(base64Payload);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }

        try {
            const audioBuffer = await audioContextRef.current.decodeAudioData(bytes.buffer);
            audioQueue.current.push(audioBuffer);
            if (!isPlaying.current) {
                playNextInQueue();
            }
        } catch (e) {
            console.error("Error decoding audio chunk:", e);
        }
    };

    const playNextInQueue = () => {
        if (audioQueue.current.length === 0 || !audioContextRef.current) {
            isPlaying.current = false;
            setIsAgentSpeaking(false);
            return;
        }

        isPlaying.current = true;
        setIsAgentSpeaking(true);
        const buffer = audioQueue.current.shift()!;
        const source = audioContextRef.current.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContextRef.current.destination);

        source.onended = () => {
            playNextInQueue();
        };

        source.start();
    };

    const stopPlayback = () => {
        audioQueue.current = [];
        isPlaying.current = false;
        setIsAgentSpeaking(false);
    };

    return (
        <div className="flex flex-col h-full space-y-4">
            <div className="flex-1 cartesia-card bg-black/40 backdrop-blur-xl border border-white/10 p-6 flex flex-col overflow-hidden relative">
                {/* Visualizer and Status */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${isActive ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
                        <span className="text-sm font-medium text-white/70">
                            {isActive ? (isAgentSpeaking ? 'AI is speaking...' : 'STT Listening...') : 'Offline'}
                        </span>
                    </div>

                    {isActive && (
                        <div className="flex items-center gap-2">
                            <div className="flex gap-1">
                                {[1, 2, 3, 4, 5].map(i => (
                                    <div
                                        key={i}
                                        className={`w-1 bg-primary rounded-full transition-all duration-150 ${isActive && !isMuted ? 'animate-bounce' : 'h-2'
                                            }`}
                                        style={{
                                            height: isActive && !isMuted ? `${volume * 100 + 4}px` : '4px',
                                            animationDelay: `${i * 0.1}s`
                                        }}
                                    />
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Chat History */}
                <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
                    {transcript.length === 0 && (
                        <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-50">
                            <Waves className="w-12 h-12 text-primary" />
                            <p className="text-sm">Click "Start Session" to speak with Gemini-powered AI</p>
                        </div>
                    )}
                    {transcript.map((item, idx) => (
                        <div
                            key={idx}
                            className={`flex ${item.role === 'user' ? 'justify-end' : 'justify-start'} ${item.role === 'system' ? 'justify-center' : ''}`}
                        >
                            <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm transition-all ${item.role === 'user'
                                ? 'bg-primary text-white rounded-tr-none'
                                : item.role === 'system'
                                    ? 'bg-white/5 text-white/40 text-[10px] uppercase tracking-widest font-bold border border-white/5'
                                    : 'bg-white/10 text-white rounded-tl-none border border-white/10'
                                }`}>
                                {item.text}
                            </div>
                        </div>
                    ))}
                    {isThinking && (
                        <div className="flex justify-start">
                            <div className="bg-white/5 border border-white/10 rounded-2xl px-4 py-3 flex gap-1">
                                <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                                <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                                <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                            </div>
                        </div>
                    )}
                    <div ref={transcriptEndRef} />
                </div>

                {/* Controls */}
                <div className="pt-6 border-t border-white/10 flex items-center justify-center gap-6">
                    <button
                        onClick={() => setIsMuted(!isMuted)}
                        disabled={!isActive}
                        className={`p-3 rounded-full transition-all ${isMuted ? 'bg-rose-500/20 text-rose-500' : 'bg-white/5 text-white hover:bg-white/10'
                            } disabled:opacity-30`}
                    >
                        {isMuted ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                    </button>

                    <button
                        onClick={isActive ? stopSession : startSession}
                        className={`px-8 py-3 rounded-2xl font-bold transition-all flex items-center gap-3 ${isActive
                            ? 'bg-rose-500/10 text-rose-500 border border-rose-500/20 hover:bg-rose-500/20'
                            : 'bg-primary text-white shadow-lg shadow-primary/20 hover:scale-105 active:scale-95'
                            }`}
                    >
                        {isActive ? (
                            <>
                                <VolumeX className="w-5 h-5" />
                                End Session
                            </>
                        ) : (
                            <>
                                <Waves className="w-5 h-5 animate-pulse" />
                                Start Live Agent
                            </>
                        )}
                    </button>

                    <button
                        className="p-3 rounded-full bg-white/5 text-white hover:bg-white/10 disabled:opacity-30"
                        title="Text Chat fallback"
                    >
                        <MessageSquare className="w-6 h-6" />
                    </button>
                </div>
            </div>
        </div>
    );
}
