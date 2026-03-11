import Link from 'next/link';
import {
  Activity,
  Calendar,
  ShieldCheck,
  ArrowRight,
  ChevronRight,
  Mic,
  Search,
  Lock,
  Globe,
  Zap,
  Sparkles,
  Command,
  Cpu,
  Fingerprint
} from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen selection:bg-primary/30 bg-background text-foreground">

      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 glass-nav">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 group cursor-pointer">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary to-secondary flex items-center justify-center shadow-lg shadow-primary/20 group-hover:scale-105 transition-transform">
                <Command className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold tracking-tight font-display">
                MedVoice AI
              </span>
            </div>

            <div className="hidden md:flex items-center gap-8">
              <Link href="#solutions" className="text-sm font-medium text-muted-foreground hover:text-white transition-colors">Features</Link>
              <Link href="#compliance" className="text-sm font-medium text-muted-foreground hover:text-white transition-colors">Security</Link>

              <Link
                href="/dashboard"
                className="btn-premium px-5 py-2 text-sm"
              >
                Access Portal
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-48 pb-32 px-6 overflow-hidden">
        <div className="max-w-5xl mx-auto text-center space-y-8 fade-in">

          <div className="inline-flex items-center justify-center">
            <span className="badge-premium animate-pulse">
              <Sparkles className="w-3 h-3 mr-2 inline" />
              The Future of Clinical Operations
            </span>
          </div>

          <h1 className="text-6xl md:text-8xl font-display leading-[1.1] tracking-tight">
            The New Standard in <br />
            <span className="text-gradient font-extrabold">Neural Medical Intake</span>
          </h1>

          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            MedVoice AI orchestrates enterprise-grade clinical coordination, handling intake, scheduling, and protocol management with a sub-second neural pipeline.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-6">
            <Link href="/dashboard" className="btn-premium px-8 py-4 text-lg">
              Launch Console
              <ArrowRight className="w-5 h-5" />
            </Link>
            <button className="btn-secondary px-8 py-4 text-lg">
              Book a Demo
            </button>
          </div>

          {/* User Feedback Preview */}
          <div className="pt-20 flex flex-col items-center gap-4 animate-float">
            <div className="flex -space-x-3">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="w-10 h-10 rounded-full border-2 border-background bg-muted ring-2 ring-primary/20">
                  <img src={`https://i.pravatar.cc/100?u=${i + 20}`} alt="User" className="rounded-full" />
                </div>
              ))}
              <div className="w-10 h-10 rounded-full border-2 border-background bg-muted flex items-center justify-center text-[10px] font-bold ring-2 ring-primary/20">
                +42
              </div>
            </div>
            <p className="text-xs font-medium text-muted-foreground tracking-widest uppercase">
              Operational in over 200+ medical units
            </p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="solutions" className="py-32 px-6 relative">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center space-y-4">
            <h2 className="text-4xl md:text-5xl font-display">Powered by Precision.</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">Our stack combines sovereign LLMs with ultra-low latency inference to provide an experience that feels like magic.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <FeatureCard
              icon={Mic}
              title="Real-time Intent"
              desc="Sub-500ms speech-to-intent pipeline using Groq LPU acceleration."
            />
            <FeatureCard
              icon={Calendar}
              title="Smart Scheduling"
              desc="Direct EHR integration for autonomous appointment orchestration."
            />
            <FeatureCard
              icon={Cpu}
              title="Clinical RAG"
              desc="Personalized knowledge base for clinic-specific medical protocols."
            />
          </div>
        </div>
      </section>

      {/* Security Section */}
      <section id="compliance" className="py-32 px-6 bg-muted/50 border-y border-border">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-16 items-center">
          <div className="space-y-8 text-left">
            <div className="inline-block badge-premium">
              Enterprise Grade
            </div>
            <h2 className="text-5xl font-display leading-tight">Fortified Security for <br />Patient Trust.</h2>
            <p className="text-xl text-muted-foreground leading-relaxed">
              We understand the critical nature of medical data. MedVoice AI is built from the ground up to exceed global compliance standards.
            </p>

            <div className="space-y-4">
              <SecurityItem icon={ShieldCheck} text="HIPAA & SOC2 Type II Compliant" />
              <SecurityItem icon={Fingerprint} text="Advanced Biometric Authentication" />
              <SecurityItem icon={Lock} text="End-to-End Interaction Encryption" />
            </div>
          </div>

          <div className="relative">
            <div className="cartesia-card p-0 overflow-hidden shadow-2xl shadow-primary/20 scale-105">
              <div className="bg-muted p-4 border-b border-border flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500/20" />
                <div className="w-3 h-3 rounded-full bg-amber-500/20" />
                <div className="w-3 h-3 rounded-full bg-emerald-500/20" />
                <div className="ml-4 h-4 w-32 bg-muted-foreground/10 rounded-full" />
              </div>
              <div className="p-8 space-y-6">
                <div className="h-4 w-3/4 bg-primary/20 rounded-full animate-pulse" />
                <div className="h-4 w-1/2 bg-muted-foreground/10 rounded-full" />
                <div className="h-24 w-full bg-muted-foreground/5 rounded-2xl" />
                <div className="flex justify-end">
                  <div className="h-10 w-24 bg-primary rounded-lg" />
                </div>
              </div>
            </div>
            {/* Decorative Elements */}
            <div className="absolute -top-10 -right-10 w-40 h-40 bg-primary/10 blur-3xl rounded-full" />
            <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-secondary/10 blur-3xl rounded-full" />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-40 px-6">
        <div className="max-w-4xl mx-auto cartesia-card text-center space-y-8 bg-gradient-to-b from-primary/10 to-transparent">
          <h2 className="text-4xl md:text-5xl font-display">Ready to Automate your Clinic?</h2>
          <p className="text-lg text-muted-foreground max-w-xl mx-auto">Join the new era of healthcare operations with the world's most advanced AI medical receptionist.</p>
          <div className="flex justify-center flex-wrap gap-4 pt-4">
            <Link href="/dashboard" className="btn-premium px-10 py-4">Get Started Now</Link>
            <button className="btn-secondary px-10 py-4">Talk to Sales</button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-20 px-6 border-t border-border">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-12">
          <div className="flex items-center gap-2">
            <Command className="w-6 h-6 text-primary" />
            <span className="text-xl font-bold font-display tracking-tight">MedVoice AI</span>
          </div>

          <div className="flex gap-8 text-sm text-muted-foreground font-medium">
            <Link href="#" className="hover:text-white transition-colors">Privacy</Link>
            <Link href="#" className="hover:text-white transition-colors">Terms</Link>
            <Link href="#" className="hover:text-white transition-colors">Security</Link>
            <Link href="#" className="hover:text-white transition-colors">API</Link>
          </div>

          <div className="text-sm text-muted-foreground font-medium">
            © 2026 MedVoice AI. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, desc }: any) {
  return (
    <div className="cartesia-card space-y-4 hover:scale-[1.02]">
      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-xl font-display">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
    </div>
  );
}

function SecurityItem({ icon: Icon, text }: any) {
  return (
    <div className="flex items-center gap-3 text-foreground/80 font-medium">
      <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
        <Icon className="w-3.5 h-3.5 text-emerald-500" />
      </div>
      <span className="text-sm">{text}</span>
    </div>
  );
}
