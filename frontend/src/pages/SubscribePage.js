import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { MessageCircle, Check, ArrowRight, Shield } from 'lucide-react';
import { Header, Footer } from './LandingPage';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const PLANS = [
  {
    name: 'Free',
    price: '₹0',
    period: 'forever',
    features: ['Browse all drops', 'Price comparison', 'Basic search'],
    cta: 'Current Plan',
    disabled: true,
  },
  {
    name: 'Pro',
    price: '₹199',
    period: '/month',
    features: ['Everything in Free', 'WhatsApp price alerts', 'New drop notifications', 'Priority support'],
    cta: 'Subscribe via UPI',
    popular: true,
  },
  {
    name: 'Premium',
    price: '₹499',
    period: '/month',
    features: ['Everything in Pro', 'Unlimited alerts', 'Early access to drops', 'Exclusive deals'],
    cta: 'Subscribe via UPI',
  },
];

export default function SubscribePage() {
  const [phone, setPhone] = useState('');
  const [name, setName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState('Pro');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!phone.match(/^[6-9]\d{9}$/)) {
      toast.error('Please enter a valid Indian mobile number');
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(`${API_URL}/subscribe`, { name, phone, plan: selectedPlan });
      setSubmitted(true);
      toast.success('Subscription request received!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Subscription failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-background min-h-screen" data-testid="subscribe-page">
      <Header />

      <main className="pt-32 pb-16">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          {/* Hero */}
          <div className="text-center mb-16 md:mb-24">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-4">Premium Alerts</p>
            <h1 className="font-serif text-4xl md:text-6xl tracking-tight mb-6" data-testid="subscribe-heading">
              Drops, Delivered<br />to Your WhatsApp
            </h1>
            <p className="text-lg text-primary/50 max-w-xl mx-auto">
              Get instant notifications when prices drop or new limited editions go live. Never miss out.
            </p>
          </div>

          {/* Plans */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8 mb-24" data-testid="plans-grid">
            {PLANS.map((plan) => (
              <div
                key={plan.name}
                className={`border p-8 relative transition-all duration-300 ${
                  plan.popular
                    ? 'border-accent shadow-soft'
                    : 'border-primary/10 hover:border-primary/20'
                } ${selectedPlan === plan.name ? 'ring-1 ring-accent' : ''}`}
                data-testid={`plan-${plan.name.toLowerCase()}`}
              >
                {plan.popular && (
                  <span className="absolute -top-3 left-6 border border-accent text-accent text-[9px] uppercase tracking-widest px-3 py-1 bg-background">
                    Most Popular
                  </span>
                )}
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary/40 mb-4">{plan.name}</p>
                <div className="flex items-baseline gap-1 mb-6">
                  <span className="font-serif text-4xl">{plan.price}</span>
                  <span className="text-sm text-primary/30">{plan.period}</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((f, i) => (
                    <li key={i} className="flex items-center gap-3 text-sm text-primary/60">
                      <Check className="w-4 h-4 text-accent flex-shrink-0" strokeWidth={1.5} />
                      {f}
                    </li>
                  ))}
                </ul>
                <button
                  disabled={plan.disabled}
                  onClick={() => !plan.disabled && setSelectedPlan(plan.name)}
                  className={`w-full py-3 text-sm font-medium transition-all duration-300 ${
                    plan.disabled
                      ? 'border border-primary/10 text-primary/30 cursor-not-allowed'
                      : selectedPlan === plan.name
                        ? 'bg-accent text-primary hover:-translate-y-0.5'
                        : 'bg-primary text-background hover:-translate-y-0.5 hover:shadow-lift'
                  }`}
                  data-testid={`select-plan-${plan.name.toLowerCase()}`}
                >
                  {selectedPlan === plan.name && !plan.disabled ? 'Selected' : plan.cta}
                </button>
              </div>
            ))}
          </div>

          {/* Subscribe form */}
          {!submitted ? (
            <div className="max-w-lg mx-auto" data-testid="subscribe-form-section">
              <div className="text-center mb-8">
                <div className="w-14 h-14 border border-accent/30 flex items-center justify-center mx-auto mb-4">
                  <MessageCircle className="w-6 h-6 text-accent" strokeWidth={1.5} />
                </div>
                <h2 className="font-serif text-2xl mb-2">Enter Your WhatsApp Number</h2>
                <p className="text-sm text-primary/40">We'll send alerts directly to your WhatsApp</p>
              </div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Your name"
                    className="w-full px-4 py-3 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors"
                    required
                    data-testid="name-input"
                  />
                </div>
                <div>
                  <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">WhatsApp Number</label>
                  <div className="flex">
                    <span className="flex items-center px-4 bg-primary/5 border border-primary/10 border-r-0 text-sm text-primary/50">+91</span>
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                      placeholder="9876543210"
                      className="flex-1 px-4 py-3 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors"
                      required
                      data-testid="phone-input"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full bg-primary text-background py-4 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-50"
                  data-testid="subscribe-submit"
                >
                  {submitting ? 'Processing...' : (
                    <>
                      Subscribe to {selectedPlan} Plan
                      <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
                    </>
                  )}
                </button>
                <div className="flex items-center justify-center gap-2 text-[10px] text-primary/30">
                  <Shield className="w-3 h-3" strokeWidth={1.5} />
                  Your number is safe. No spam, ever.
                </div>
              </form>
            </div>
          ) : (
            <div className="max-w-lg mx-auto text-center py-12" data-testid="subscribe-success">
              <div className="w-16 h-16 border border-accent bg-accent/5 flex items-center justify-center mx-auto mb-6">
                <Check className="w-8 h-8 text-accent" strokeWidth={1.5} />
              </div>
              <h2 className="font-serif text-3xl mb-3">You're In</h2>
              <p className="text-primary/50 mb-8">
                You'll receive WhatsApp alerts for new drops and price reductions.
              </p>
              <Link
                to="/browse"
                className="inline-flex items-center gap-2 bg-primary text-background px-8 py-4 font-medium hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300"
                data-testid="browse-after-subscribe"
              >
                Explore Drops
                <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
              </Link>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
