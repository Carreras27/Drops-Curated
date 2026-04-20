import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Shield, Mail, MessageCircle, Send, Check, ArrowRight, Loader2, Crown, PauseCircle, PlayCircle, LogOut, ExternalLink, Sparkles, Copy } from 'lucide-react';

const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AccountPage() {
  const [step, setStep] = useState('phone'); // phone | otp | loaded
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [subscriber, setSubscriber] = useState(null);
  const [tgLink, setTgLink] = useState(null); // {deep_link, code}

  // Persist session across reloads (simple — just the phone; API re-verifies)
  useEffect(() => {
    const stored = sessionStorage.getItem('dc_account_phone');
    if (stored) {
      setPhone(stored);
      axios.get(`${API_URL}/account/${stored}`)
        .then(r => {
          setSubscriber(r.data.subscriber);
          setStep('loaded');
        })
        .catch(() => sessionStorage.removeItem('dc_account_phone'));
    }
  }, []);

  const sendOtp = async () => {
    if (!/^[6-9]\d{9}$/.test(phone.trim())) {
      toast.error('Enter a valid 10-digit Indian phone number');
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${API_URL}/otp/send`, { phone: phone.trim() });
      toast.success('OTP sent');
      setStep('otp');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to send OTP');
    } finally { setLoading(false); }
  };

  const verifyOtp = async () => {
    if (otp.length < 4) { toast.error('Enter the OTP'); return; }
    setLoading(true);
    try {
      const r = await axios.post(`${API_URL}/account/login`, { phone: phone.trim(), otp });
      setSubscriber(r.data.subscriber);
      sessionStorage.setItem('dc_account_phone', phone.trim());
      setStep('loaded');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Verification failed');
    } finally { setLoading(false); }
  };

  const logout = () => {
    sessionStorage.removeItem('dc_account_phone');
    setSubscriber(null);
    setStep('phone');
    setPhone('');
    setOtp('');
  };

  const refreshSubscriber = useCallback(async () => {
    if (!subscriber?.phone) return;
    try {
      const r = await axios.get(`${API_URL}/account/${subscriber.phone}`);
      setSubscriber(r.data.subscriber);
    } catch { /* ignore */ }
  }, [subscriber?.phone]);

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-6 md:px-12 py-14 md:py-20">
        <div className="mb-12 flex items-start justify-between">
          <div>
            <p className="text-[10px] uppercase tracking-[0.22em] text-accent mb-3 font-semibold">Member Account</p>
            <h1 className="font-serif text-3xl md:text-4xl tracking-tight mb-2">Your Drops Curated</h1>
            <p className="text-sm text-primary/50 max-w-md leading-relaxed">
              Manage how, when, and where you receive drop alerts — all in one calm place.
            </p>
          </div>
          {step === 'loaded' && (
            <button
              onClick={logout}
              className="text-xs text-primary/50 hover:text-primary flex items-center gap-1.5 tracking-wide transition-colors"
              data-testid="account-logout-btn"
            >
              <LogOut className="w-3.5 h-3.5" strokeWidth={1.5} /> Sign out
            </button>
          )}
        </div>

        {step === 'phone' && (
          <AuthCard title="Sign in to your account" subtitle="We'll send a one-time code to your WhatsApp to get you in.">
            <label className="text-[10px] uppercase tracking-[0.2em] text-primary/40 mb-2 block">Phone number</label>
            <div className="flex items-center border border-primary/15 bg-surface focus-within:border-primary transition-colors mb-4">
              <span className="px-4 text-sm text-primary/50">+91</span>
              <input
                type="tel" maxLength={10} value={phone}
                onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                className="flex-1 bg-transparent py-3.5 pr-4 text-sm outline-none tabular-nums"
                placeholder="10-digit number"
                data-testid="account-phone-input"
              />
            </div>
            <button onClick={sendOtp} disabled={loading} data-testid="account-send-otp-btn"
              className="w-full bg-primary text-background py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Send OTP <ArrowRight className="w-4 h-4" strokeWidth={1.5} /></>}
            </button>
          </AuthCard>
        )}

        {step === 'otp' && (
          <AuthCard title="Enter the code" subtitle={`We sent a 6-digit code to +91 ${phone}`}>
            <input
              type="text" inputMode="numeric" maxLength={6} value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
              className="w-full border border-primary/15 bg-surface py-3.5 px-4 text-center text-2xl tabular-nums tracking-[0.4em] outline-none focus:border-primary mb-4"
              placeholder="••••••"
              data-testid="account-otp-input"
            />
            <button onClick={verifyOtp} disabled={loading || otp.length < 4} data-testid="account-verify-otp-btn"
              className="w-full bg-primary text-background py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Verify & continue <ArrowRight className="w-4 h-4" strokeWidth={1.5} /></>}
            </button>
            <button onClick={() => setStep('phone')} className="text-xs text-primary/40 hover:text-primary mt-4 w-full text-center">
              ← use a different number
            </button>
          </AuthCard>
        )}

        {step === 'loaded' && subscriber && (
          <AccountDashboard
            subscriber={subscriber}
            onRefresh={refreshSubscriber}
            tgLink={tgLink}
            setTgLink={setTgLink}
          />
        )}
      </div>
    </div>
  );
}


const AuthCard = ({ title, subtitle, children }) => (
  <div className="max-w-md border border-primary/10 bg-surface p-8 md:p-10 shadow-soft">
    <h2 className="font-serif text-2xl mb-2">{title}</h2>
    <p className="text-sm text-primary/50 mb-6 leading-relaxed">{subtitle}</p>
    {children}
    <div className="flex items-center gap-2 mt-5 text-[10px] text-primary/35 tracking-wide">
      <Shield className="w-3 h-3" strokeWidth={1.5} /> OTP-based · no password needed
    </div>
  </div>
);


const AccountDashboard = ({ subscriber, onRefresh, tgLink, setTgLink }) => {
  const navigate = useNavigate();
  const isVip = subscriber.tier === 'vip';

  // Parse channel string
  const channels = new Set(
    ((subscriber.notificationChannel || 'email').replace('both', 'email,whatsapp')).split(',').map(c => c.trim()).filter(Boolean)
  );

  const pausedUntil = subscriber.alertsPausedUntil ? new Date(subscriber.alertsPausedUntil) : null;
  const isPaused = pausedUntil && pausedUntil > new Date();

  const saveChannels = async (nextSet) => {
    try {
      const r = await axios.post(`${API_URL}/account/channels`, {
        phone: subscriber.phone,
        channels: Array.from(nextSet),
      });
      toast.success('Channel preferences updated');
      onRefresh();
      return r.data;
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Update failed');
    }
  };

  const toggle = (ch) => {
    if (ch === 'email') return; // locked
    const next = new Set(channels);
    if (next.has(ch)) next.delete(ch); else next.add(ch);
    saveChannels(next);
  };

  const connectTelegram = async () => {
    try {
      const r = await axios.post(`${API_URL}/telegram/link-code`, { phone: subscriber.phone });
      setTgLink(r.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to generate link');
    }
  };

  const disconnectTelegram = async () => {
    try {
      await axios.post(`${API_URL}/account/telegram-disconnect`, { phone: subscriber.phone });
      toast.success('Telegram disconnected');
      onRefresh();
    } catch { toast.error('Failed'); }
  };

  const pauseAlerts = async (days) => {
    try {
      await axios.post(`${API_URL}/account/pause`, { phone: subscriber.phone, days });
      toast.success(days === 0 ? 'Alerts resumed' : `Alerts paused for ${days} days`);
      onRefresh();
    } catch { toast.error('Failed'); }
  };

  return (
    <div className="space-y-6" data-testid="account-dashboard">

      {/* Membership summary */}
      <div className={`border p-6 md:p-8 ${isVip ? 'border-accent bg-gradient-to-br from-accent/[0.08] to-transparent' : 'border-primary/10 bg-surface'}`} data-testid="membership-summary">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="flex items-center gap-2 mb-2">
              {isVip && <Crown className="w-4 h-4 text-accent" strokeWidth={1.5} />}
              <p className="text-[10px] uppercase tracking-[0.22em] font-semibold" style={{ color: isVip ? '#D4AF37' : 'rgba(0,31,63,0.4)' }}>
                {isVip ? 'VIP Member' : 'Regular Member'}
              </p>
            </div>
            <p className="font-serif text-2xl mb-1">{subscriber.name || 'Member'}</p>
            <p className="text-xs text-primary/50">
              {subscriber.membershipId} · Expires {subscriber.expiresAt ? new Date(subscriber.expiresAt).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'}
            </p>
          </div>
          {!isVip && (
            <button onClick={() => navigate('/subscribe?plan=vip_yearly')} className="text-xs bg-accent text-primary px-4 py-2 font-medium hover:-translate-y-0.5 hover:shadow-lift transition-all">
              Upgrade to VIP →
            </button>
          )}
        </div>
        {isPaused && (
          <div className="mt-4 pt-4 border-t border-primary/10 flex items-center gap-3">
            <PauseCircle className="w-4 h-4 text-primary/60" strokeWidth={1.5} />
            <p className="text-xs text-primary/60 flex-1">
              Alerts paused until <span className="font-medium text-primary">{pausedUntil.toLocaleDateString('en-IN')}</span>
            </p>
            <button onClick={() => pauseAlerts(0)} className="text-xs text-accent underline-offset-4 hover:underline" data-testid="resume-alerts-btn">
              Resume now
            </button>
          </div>
        )}
      </div>

      {/* Notification Channels */}
      <Section title="Notification Channels" subtitle="Email is always on. WhatsApp and Telegram are optional add-ons you can toggle anytime." testid="channels-section">

        <ChannelRow
          icon={Mail} label="Email" checked={channels.has('email')} locked
          badge="Default · Always on" description={subscriber.email || 'No email on file'}
          data-testid="channel-row-email"
        />

        <ChannelRow
          icon={MessageCircle} label="WhatsApp" checked={channels.has('whatsapp')}
          badge={channels.has('whatsapp') ? 'Active' : 'Off'} description={`+91 ${subscriber.phone}`}
          onClick={() => toggle('whatsapp')}
          data-testid="channel-row-whatsapp"
        />

        <ChannelRow
          icon={Send} label="Telegram"
          checked={channels.has('telegram')}
          badge={
            !subscriber.telegramLinked ? 'Not connected' :
            channels.has('telegram') ? `Active · @${subscriber.telegramUsername || 'linked'}` : 'Off'
          }
          description={subscriber.telegramLinked ? 'Tap to toggle alerts on this Telegram chat' : 'Connect your Telegram to receive alerts there'}
          onClick={() => subscriber.telegramLinked && toggle('telegram')}
          disabled={!subscriber.telegramLinked}
          data-testid="channel-row-telegram"
        />

        {!subscriber.telegramLinked && (
          <div className="mt-3">
            {!tgLink ? (
              <button onClick={connectTelegram} className="text-xs bg-primary text-background px-4 py-2.5 flex items-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all" data-testid="connect-telegram-btn">
                <Send className="w-3.5 h-3.5" strokeWidth={1.5} /> Connect Telegram
              </button>
            ) : (
              <div className="border border-accent/40 bg-accent/[0.06] p-4" data-testid="telegram-link-card">
                <p className="text-xs text-primary/70 leading-relaxed mb-3">
                  <Sparkles className="inline w-3 h-3 mr-1 text-accent" strokeWidth={1.5} />
                  Tap the button below to open our bot in Telegram. Your account will auto-connect. Link expires in 10 min.
                </p>
                <a href={tgLink.deep_link} target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 bg-primary text-background px-4 py-2.5 text-xs font-medium hover:-translate-y-0.5 hover:shadow-lift transition-all"
                  data-testid="telegram-deep-link-btn"
                >
                  <Send className="w-3.5 h-3.5" strokeWidth={1.5} /> Open Telegram
                  <ExternalLink className="w-3 h-3" strokeWidth={1.5} />
                </a>
                <button
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(tgLink.deep_link);
                      toast.success('Link copied');
                    } catch { toast.error('Copy failed'); }
                  }}
                  className="ml-3 text-xs text-primary/50 hover:text-primary inline-flex items-center gap-1"
                  data-testid="telegram-copy-link-btn"
                >
                  <Copy className="w-3 h-3" strokeWidth={1.5} /> Copy link
                </button>
                <button
                  onClick={async () => { await onRefresh(); toast('Refreshed'); }}
                  className="ml-3 text-xs text-primary/50 hover:text-primary"
                  data-testid="telegram-refresh-btn"
                >
                  I've linked it — refresh
                </button>
              </div>
            )}
          </div>
        )}

        {subscriber.telegramLinked && (
          <button onClick={disconnectTelegram} className="text-xs text-primary/50 hover:text-red-500 mt-3 inline-flex items-center gap-1.5" data-testid="telegram-disconnect-btn">
            <ExternalLink className="w-3 h-3" strokeWidth={1.5} /> Disconnect Telegram
          </button>
        )}
      </Section>

      {/* Pause alerts */}
      <Section title="Pause Alerts" subtitle="Going on vacation or feeling overwhelmed? Mute everything for a few days." testid="pause-section">
        <div className="flex flex-wrap gap-2">
          {[3, 7, 14, 30].map(d => (
            <button
              key={d} onClick={() => pauseAlerts(d)}
              className="text-xs border border-primary/15 bg-background px-4 py-2 hover:border-primary hover:bg-primary hover:text-background transition-all"
              data-testid={`pause-${d}-btn`}
            >
              {d} days
            </button>
          ))}
          {isPaused && (
            <button onClick={() => pauseAlerts(0)} className="text-xs bg-accent/20 border border-accent text-primary px-4 py-2 hover:bg-accent transition-all inline-flex items-center gap-1.5" data-testid="pause-resume-btn">
              <PlayCircle className="w-3.5 h-3.5" strokeWidth={1.5} /> Resume now
            </button>
          )}
        </div>
      </Section>

      {/* Quick preference summary */}
      <Section title="Your Preferences" subtitle="A snapshot of the filters powering your alerts." testid="prefs-section">
        <PrefRow label="Brands" value={
          subscriber.preferences.brands?.length
            ? `${subscriber.preferences.brands.length} selected`
            : 'All 25 brands'
        } />
        <PrefRow label="Alert types" value={(subscriber.preferences.alert_types || []).join(' · ') || '—'} />
        <PrefRow label="Gender" value={subscriber.preferences.gender || 'all'} />
        <PrefRow label="Frequency" value={subscriber.preferences.alert_frequency === 'daily' ? 'Daily digest (8 PM IST)' : 'Instant'} />
        <PrefRow label="Price drop threshold" value={`${subscriber.preferences.drop_threshold || 10}% off or more`} />
        <button onClick={() => navigate('/subscribe')} className="text-xs text-accent hover:underline underline-offset-4 mt-3" data-testid="edit-preferences-btn">
          Edit all preferences →
        </button>
      </Section>

    </div>
  );
};


const Section = ({ title, subtitle, testid, children }) => (
  <div className="border border-primary/10 bg-surface p-6 md:p-8" data-testid={testid}>
    <h2 className="font-serif text-xl mb-1">{title}</h2>
    {subtitle && <p className="text-xs text-primary/50 mb-5 leading-relaxed">{subtitle}</p>}
    {children}
  </div>
);


const ChannelRow = ({ icon: Icon, label, checked, locked, badge, description, onClick, disabled, 'data-testid': testid }) => {
  const interactive = !locked && !disabled && onClick;
  return (
    <div
      onClick={interactive ? onClick : undefined}
      className={`flex items-center gap-3 p-4 border mb-2 ${
        checked ? (locked ? 'border-accent bg-accent/[0.06]' : 'border-primary bg-primary/[0.04]') : 'border-primary/10'
      } ${interactive ? 'cursor-pointer hover:border-primary/40 transition-colors' : ''} ${disabled ? 'opacity-60' : ''}`}
      data-testid={testid}
    >
      <div className={`w-5 h-5 border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
        checked ? (locked ? 'border-accent bg-accent' : 'border-primary bg-primary') : 'border-primary/30'
      }`}>
        {checked && <Check className="w-3 h-3" style={{ color: locked ? '#001F3F' : '#FAF8F5' }} strokeWidth={3} />}
      </div>
      <Icon className="w-4 h-4 text-primary/70 flex-shrink-0" strokeWidth={1.5} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium">{label}</span>
          {badge && <span className={`text-[9px] uppercase tracking-[0.18em] font-semibold ${
            locked ? 'text-accent' : checked ? 'text-primary/70' : 'text-primary/40'
          }`}>{badge}</span>}
        </div>
        {description && <p className="text-xs text-primary/50 mt-0.5 leading-relaxed truncate">{description}</p>}
      </div>
    </div>
  );
};


const PrefRow = ({ label, value }) => (
  <div className="flex items-center justify-between py-2.5 border-b border-primary/5 last:border-0">
    <span className="text-xs text-primary/50 uppercase tracking-wider">{label}</span>
    <span className="text-sm text-primary">{value}</span>
  </div>
);
