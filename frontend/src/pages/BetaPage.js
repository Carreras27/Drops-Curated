import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Sparkles, Mail, MessageCircle, Send, Check, ArrowRight, Loader2, Shield, Zap, Clock, Star } from 'lucide-react';

const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Closed-beta signup page. Hard-capped at 100 — when full, shows waitlist CTA.
// No payment step: 30 days free for whoever makes it in.
export default function BetaPage() {
  const [status, setStatus] = useState(null); // null until first fetch resolves
  const [step, setStep] = useState('intro'); // intro | phone | otp | details | done
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sandboxOtp, setSandboxOtp] = useState('');
  const [signupResult, setSignupResult] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    let alive = true;
    const fetchStatus = () => axios.get(`${API_URL}/beta/status`)
      .then(r => { if (alive) setStatus(r.data); })
      .catch(() => { /* ignore — default state */ });
    fetchStatus();
    const t = setInterval(fetchStatus, 15000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  const pct = status ? Math.round((status.taken / status.total) * 100) : 0;
  const urgency = status && status.spots_left <= 10 ? 'critical' : status && status.spots_left <= 30 ? 'warning' : 'calm';

  const sendOtp = async () => {
    if (!/^[6-9]\d{9}$/.test(phone.trim())) { toast.error('Enter a valid 10-digit Indian phone'); return; }
    setLoading(true);
    try {
      const r = await axios.post(`${API_URL}/otp/send`, { phone: phone.trim() });
      if (r.data.sandbox_otp) setSandboxOtp(r.data.sandbox_otp);
      toast.success('Verification code sent via WhatsApp');
      setStep('otp');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Could not send OTP');
    } finally { setLoading(false); }
  };

  const verifyOtp = async () => {
    if (otp.length < 4) { toast.error('Enter the code'); return; }
    setLoading(true);
    try {
      await axios.post(`${API_URL}/otp/verify`, { phone: phone.trim(), otp });
      setStep('details');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Verification failed');
    } finally { setLoading(false); }
  };

  const finalSignup = async () => {
    if (!name.trim() || !email.trim() || !/\S+@\S+\.\S+/.test(email)) {
      toast.error('Please enter your name and a valid email');
      return;
    }
    setLoading(true);
    try {
      const r = await axios.post(`${API_URL}/beta/signup`, {
        phone: phone.trim(), name: name.trim(), email: email.trim()
      });
      setSignupResult(r.data);
      setStep('done');
    } catch (e) {
      const msg = e.response?.data?.detail || 'Signup failed';
      // Already-a-member dead-end: route them to /account instead of trapping them
      // on a disabled form with only a toast.
      if (/already have a paid membership|paid membership/i.test(msg)) {
        setStep('already_member');
        return;
      }
      toast.error(msg);
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-6 md:px-12 py-14 md:py-20">

        {/* Hero */}
        <div className="mb-14 text-center">
          <p className="text-[10px] uppercase tracking-[0.22em] text-accent mb-4 font-semibold inline-flex items-center gap-2">
            <Sparkles className="w-3 h-3" strokeWidth={1.5} />
            Closed Beta · By Invitation
          </p>
          <h1 className="font-serif text-4xl md:text-5xl tracking-tight mb-4 leading-[1.1]">
            Be one of the first <span className="italic text-accent">{status ? status.total : 100}</span> inside.
          </h1>
          <p className="text-sm md:text-base text-primary/55 max-w-xl mx-auto leading-relaxed mb-8">
            You get 30 days free. All 25+ brands unlocked. Alerts across email, WhatsApp & Telegram.
            Zero payment, zero catches — just pure early access in exchange for your feedback.
          </p>

          {/* Spots counter — only after first fetch resolves, to avoid a misleading 0/100 flash */}
          {status ? (
            <div className="max-w-sm mx-auto" data-testid="beta-spots-counter">
              <div className="flex items-center justify-between text-xs text-primary/60 mb-2">
                <span className="tabular-nums font-medium">{status.taken} of {status.total} spots taken</span>
                <span className={`font-semibold tabular-nums ${
                  urgency === 'critical' ? 'text-red-600' : urgency === 'warning' ? 'text-accent' : 'text-primary/60'
                }`}>{status.spots_left} left</span>
              </div>
              <div className="h-1 bg-primary/10 overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    urgency === 'critical' ? 'bg-red-500' : urgency === 'warning' ? 'bg-accent' : 'bg-primary'
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          ) : (
            <div className="max-w-sm mx-auto h-8" aria-hidden="true" />
          )}
        </div>

        {/* Perks strip */}
        {step === 'intro' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8 max-w-3xl mx-auto mb-12">
            {[
              { icon: Zap, title: '10-second alerts', body: 'Drops surface instantly across all your channels.' },
              { icon: Star, title: 'All 25+ brands', body: 'Almost Gods, Comet, Superkicks, HUEMN & more.' },
              { icon: Shield, title: 'Cancel anytime', body: 'No payment now. No auto-charge after beta.' },
            ].map((p, i) => (
              <div key={i} className="text-center md:text-left">
                <p.icon className="w-5 h-5 text-accent mb-3 mx-auto md:mx-0" strokeWidth={1.5} />
                <p className="font-medium text-sm mb-1">{p.title}</p>
                <p className="text-xs text-primary/50 leading-relaxed">{p.body}</p>
              </div>
            ))}
          </div>
        )}

        {/* Signup card */}
        <div className="max-w-md mx-auto">
          {status && !status.is_open && step !== 'done' && (
            <div className="border border-red-500/30 bg-red-50 p-8" data-testid="beta-full-card">
              <p className="text-[10px] uppercase tracking-[0.22em] text-red-700 mb-3 font-semibold">Beta is full</p>
              <h2 className="font-serif text-2xl mb-2">We've maxed out at {status.total}.</h2>
              <p className="text-sm text-primary/60 leading-relaxed mb-6">
                You can still get in — grab a <button onClick={() => navigate('/subscribe')} className="text-accent underline underline-offset-4">paid membership</button> for ₹399/month, or sign up for the public launch.
              </p>
            </div>
          )}

          {status && status.is_open && step === 'intro' && (
            <div className="border border-primary/10 bg-surface p-8 md:p-10 shadow-soft text-center" data-testid="beta-intro-card">
              <button
                onClick={() => setStep('phone')}
                className="w-full bg-primary text-background py-4 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300"
                data-testid="beta-start-btn"
              >
                Claim your spot
                <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
              </button>
              <p className="text-[10px] text-primary/35 mt-3 tracking-wide">
                Takes 60 seconds · No card required
              </p>
            </div>
          )}

          {status && status.is_open && step === 'phone' && (
            <SignupCard title="Verify your number" subtitle="We'll WhatsApp a 6-digit code to confirm it's you.">
              <label className="text-[10px] uppercase tracking-[0.2em] text-primary/40 mb-2 block">Phone number</label>
              <div className="flex items-center border border-primary/15 bg-background focus-within:border-primary transition-colors mb-4">
                <span className="px-4 text-sm text-primary/50">+91</span>
                <input type="tel" maxLength={10} value={phone}
                  onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                  className="flex-1 bg-transparent py-3.5 pr-4 text-sm outline-none tabular-nums"
                  placeholder="10-digit number"
                  data-testid="beta-phone-input"
                />
              </div>
              <button onClick={sendOtp} disabled={loading} data-testid="beta-send-otp-btn"
                className="w-full bg-primary text-background py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40">
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Send code <ArrowRight className="w-4 h-4" strokeWidth={1.5} /></>}
              </button>
            </SignupCard>
          )}

          {status && status.is_open && step === 'otp' && (
            <SignupCard title="Enter the code" subtitle={`We sent a 6-digit code to +91 ${phone}`}>
              {sandboxOtp && (
                <div className="bg-accent/10 border border-accent/30 p-2 mb-3 text-[10px] text-primary/70 text-center tabular-nums tracking-wider" data-testid="beta-sandbox-otp">
                  Sandbox OTP: <b>{sandboxOtp}</b>
                </div>
              )}
              <input type="text" inputMode="numeric" maxLength={6} value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                className="w-full border border-primary/15 bg-background py-3.5 px-4 text-center text-2xl tabular-nums tracking-[0.4em] outline-none focus:border-primary mb-4"
                placeholder="••••••"
                data-testid="beta-otp-input"
              />
              <button onClick={verifyOtp} disabled={loading || otp.length < 4} data-testid="beta-verify-otp-btn"
                className="w-full bg-primary text-background py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40">
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Verify <ArrowRight className="w-4 h-4" strokeWidth={1.5} /></>}
              </button>
            </SignupCard>
          )}

          {status && status.is_open && step === 'details' && (
            <SignupCard title="Tell us about you" subtitle="Just your name and email — we'll send your welcome kit there.">
              <label className="text-[10px] uppercase tracking-[0.2em] text-primary/40 mb-2 block">Your name</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)}
                className="w-full border border-primary/15 bg-background py-3.5 px-4 text-sm outline-none focus:border-primary mb-4"
                placeholder="Arjun Kapoor"
                data-testid="beta-name-input"
              />
              <label className="text-[10px] uppercase tracking-[0.2em] text-primary/40 mb-2 block">Email address</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                className="w-full border border-primary/15 bg-background py-3.5 px-4 text-sm outline-none focus:border-primary mb-5"
                placeholder="you@example.com"
                data-testid="beta-email-input"
              />
              <button onClick={finalSignup} disabled={loading} data-testid="beta-signup-btn"
                className="w-full bg-primary text-background py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40">
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Claim my spot <Sparkles className="w-4 h-4" strokeWidth={1.5} /></>}
              </button>
            </SignupCard>
          )}

          {step === 'already_member' && (
            <div className="border border-accent/40 bg-gradient-to-br from-accent/[0.08] to-transparent p-8 md:p-10 text-center" data-testid="beta-already-member-card">
              <Sparkles className="w-8 h-8 text-accent mx-auto mb-4" strokeWidth={1.5} />
              <p className="text-[10px] uppercase tracking-[0.22em] text-accent mb-3 font-semibold">Welcome back</p>
              <h2 className="font-serif text-2xl mb-3">You're already a member.</h2>
              <p className="text-sm text-primary/60 leading-relaxed mb-6">
                The number <b className="text-primary">+91 {phone}</b> already has an active membership on Drops Curated. Head to your account to manage alerts, pause notifications, or view your plan.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={() => navigate(`/account?phone=${phone}`)}
                  className="bg-primary text-background px-6 py-3 text-sm font-medium inline-flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all"
                  data-testid="beta-go-to-account-btn"
                >
                  Go to my account <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
                </button>
                <button
                  onClick={() => navigate('/browse')}
                  className="border border-primary/20 text-primary px-6 py-3 text-sm hover:bg-primary hover:text-background transition-all"
                >
                  Browse drops
                </button>
              </div>
            </div>
          )}

          {step === 'done' && signupResult && (
            <div className="border border-accent bg-gradient-to-br from-accent/10 to-transparent p-8 md:p-10 text-center" data-testid="beta-success-card">
              <Sparkles className="w-8 h-8 text-accent mx-auto mb-4" strokeWidth={1.5} />
              <p className="text-[10px] uppercase tracking-[0.22em] text-accent mb-3 font-semibold">You're in</p>
              <h2 className="font-serif text-3xl mb-3">Welcome to the beta, {name.split(' ')[0]}.</h2>
              <p className="text-sm text-primary/60 leading-relaxed mb-6">
                Your 30 days are active. Check your inbox — we've sent a welcome kit to <b className="text-primary">{email}</b>.
                All 25+ brands are unlocked. Now tell us what to alert you about.
              </p>
              <p className="text-[11px] text-primary/40 mb-6 tabular-nums">
                Membership ID · <b className="text-primary">{signupResult.membership_id}</b>
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button onClick={() => navigate(`/subscribe?channels=email&skipPayment=1`)}
                  className="bg-primary text-background px-6 py-3 text-sm font-medium hover:-translate-y-0.5 hover:shadow-lift transition-all"
                  data-testid="beta-configure-btn"
                >
                  Configure my alerts →
                </button>
                <button onClick={() => navigate('/browse')}
                  className="border border-primary/20 text-primary px-6 py-3 text-sm hover:bg-primary hover:text-background transition-all"
                >
                  Browse drops
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Feedback teaser */}
        {step !== 'done' && (
          <div className="mt-16 text-center">
            <p className="text-xs text-primary/45 mb-2 uppercase tracking-wider">Already a beta member?</p>
            <button onClick={() => navigate('/beta/feedback')} className="text-sm text-accent hover:underline underline-offset-4" data-testid="beta-feedback-link">
              Share feedback →
            </button>
          </div>
        )}

      </div>
    </div>
  );
}

const SignupCard = ({ title, subtitle, children }) => (
  <div className="border border-primary/10 bg-surface p-8 md:p-10 shadow-soft">
    <h2 className="font-serif text-2xl mb-2">{title}</h2>
    <p className="text-sm text-primary/50 mb-6 leading-relaxed">{subtitle}</p>
    {children}
    <div className="flex items-center gap-2 mt-5 text-[10px] text-primary/35 tracking-wide">
      <Shield className="w-3 h-3" strokeWidth={1.5} /> OTP-based · no password required
    </div>
  </div>
);
