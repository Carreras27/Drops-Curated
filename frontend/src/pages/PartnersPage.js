import React, { useState } from 'react';
import { ArrowRight, Check, Users, Megaphone, BarChart3, Gift } from 'lucide-react';
import { Header, Footer } from './LandingPage';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

export default function PartnersPage() {
  const [form, setForm] = useState({ brand: '', contact: '', email: '', message: '' });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API_URL}/partner-inquiry`, form);
      setSubmitted(true);
      toast.success('Inquiry sent! We\'ll be in touch.');
    } catch {
      toast.error('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-background min-h-screen" data-testid="partners-page">
      <Header />

      <main className="pt-32 pb-24">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          {/* Hero */}
          <div className="max-w-3xl mb-24">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-4">For Brands</p>
            <h1 className="font-serif text-4xl md:text-5xl lg:text-6xl tracking-tight mb-6" data-testid="partners-heading">
              Showcase Your<br />Next Collection
            </h1>
            <p className="text-lg text-primary/50 leading-relaxed">
              Partner with Drops Curated to reach India's most engaged streetwear audience.
              Feature your upcoming drops and gift premium memberships to your VIP customers.
            </p>
          </div>

          {/* Value Props */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-24">
            {[
              { icon: <Users strokeWidth={1.5} />, title: 'Engaged Audience', desc: 'Direct access to verified streetwear enthusiasts who are ready to buy.' },
              { icon: <Megaphone strokeWidth={1.5} />, title: 'Collection Spotlight', desc: 'Feature your upcoming drops on our platform before they go live.' },
              { icon: <Gift strokeWidth={1.5} />, title: 'Bulk Memberships', desc: 'Buy memberships at a discount and gift them to your premium customers.' },
              { icon: <BarChart3 strokeWidth={1.5} />, title: 'Analytics', desc: 'See how your products perform — views, interest, and price tracking.' },
            ].map((item, i) => (
              <div key={i} className="animate-fade-up" style={{ animationDelay: `${i * 0.1}s` }} data-testid={`partner-feature-${i}`}>
                <div className="w-12 h-12 border border-accent/30 flex items-center justify-center mb-5 text-accent">
                  {item.icon}
                </div>
                <h3 className="font-serif text-lg mb-2">{item.title}</h3>
                <p className="text-sm text-primary/40 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>

          {/* How it works */}
          <div className="mb-24">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-4">Partnership</p>
            <h2 className="font-serif text-3xl md:text-4xl tracking-tight mb-12">How It Works</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
              {[
                { step: '01', title: 'Connect', desc: 'Tell us about your brand and upcoming collections. We\'ll set up your profile.' },
                { step: '02', title: 'Feature', desc: 'Your drops get featured to our audience. We track prices and alert subscribers.' },
                { step: '03', title: 'Grow', desc: 'Gift memberships to your top customers. They get alerts — you get loyalty.' },
              ].map((s, i) => (
                <div key={i} className="animate-fade-up" style={{ animationDelay: `${i * 0.15}s` }}>
                  <p className="font-serif text-5xl text-accent/20 mb-4">{s.step}</p>
                  <h3 className="font-serif text-xl mb-2">{s.title}</h3>
                  <p className="text-sm text-primary/40 leading-relaxed">{s.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Contact Form */}
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-4">Get Started</p>
            <h2 className="font-serif text-3xl tracking-tight mb-8">Partner With Us</h2>

            {!submitted ? (
              <form onSubmit={handleSubmit} className="space-y-4" data-testid="partner-form">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">Brand Name</label>
                    <input
                      type="text"
                      value={form.brand}
                      onChange={(e) => setForm({ ...form, brand: e.target.value })}
                      className="w-full px-4 py-3.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors"
                      placeholder="Your Brand"
                      required
                      data-testid="partner-brand-input"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">Contact Person</label>
                    <input
                      type="text"
                      value={form.contact}
                      onChange={(e) => setForm({ ...form, contact: e.target.value })}
                      className="w-full px-4 py-3.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors"
                      placeholder="Your Name"
                      required
                      data-testid="partner-contact-input"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">Email</label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="w-full px-4 py-3.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors"
                    placeholder="brand@example.com"
                    required
                    data-testid="partner-email-input"
                  />
                </div>
                <div>
                  <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">Tell Us About Your Brand</label>
                  <textarea
                    value={form.message}
                    onChange={(e) => setForm({ ...form, message: e.target.value })}
                    className="w-full px-4 py-3.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors h-32 resize-none"
                    placeholder="Your brand story, upcoming collections, what you're looking for..."
                    data-testid="partner-message-input"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-primary text-background px-8 py-3.5 font-medium text-sm flex items-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40"
                  data-testid="partner-submit-btn"
                >
                  {loading ? 'Sending...' : 'Start Partnership'}
                  <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
                </button>
              </form>
            ) : (
              <div className="border border-accent/30 p-8 text-center animate-fade-up" data-testid="partner-success">
                <div className="w-14 h-14 border border-accent bg-accent/5 flex items-center justify-center mx-auto mb-4">
                  <Check className="w-7 h-7 text-accent" strokeWidth={1.5} />
                </div>
                <h3 className="font-serif text-2xl mb-2">Inquiry Received</h3>
                <p className="text-sm text-primary/40">We'll review your brand and get back to you within 48 hours.</p>
              </div>
            )}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
