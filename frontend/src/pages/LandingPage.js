import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Bell, Store, TrendingUp, MessageCircle, Zap, Clock, Shield, Handshake } from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const NAV_LINKS = [
  { label: 'Drops', to: '/browse' },
  { label: 'Partners', to: '/partners' },
  { label: 'Subscribe', to: '/subscribe' },
];

export const Header = ({ transparent = false }) => (
  <header className={`fixed top-0 left-0 right-0 z-50 ${transparent ? 'bg-background/90 backdrop-blur-xl' : 'bg-background'} border-b border-primary/[0.06]`}>
    <nav className="max-w-7xl mx-auto px-6 md:px-12 h-16 flex items-center justify-between">
      <Link to="/" className="font-serif text-xl tracking-tight" data-testid="logo-link">
        Drops <span className="text-accent">Curated</span>
      </Link>
      <div className="flex items-center gap-6 md:gap-8">
        {NAV_LINKS.map(l => (
          <Link key={l.to} to={l.to} className="text-xs md:text-sm font-medium text-primary/60 hover:text-primary transition-colors duration-200" data-testid={`nav-${l.label.toLowerCase()}`}>
            {l.label}
          </Link>
        ))}
        <Link
          to="/subscribe"
          className="hidden md:inline-flex items-center gap-2 bg-primary text-background text-xs font-medium px-5 py-2.5 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300"
          data-testid="nav-subscribe-cta"
        >
          <Bell className="w-3.5 h-3.5" strokeWidth={1.5} />
          Get Alerts
        </Link>
      </div>
    </nav>
  </header>
);

export const Footer = () => (
  <footer className="border-t border-primary/[0.06] py-16 md:py-20 bg-background">
    <div className="max-w-7xl mx-auto px-6 md:px-12">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-10 md:gap-12">
        <div className="col-span-2 md:col-span-1">
          <p className="font-serif text-xl mb-3">Drops <span className="text-accent">Curated</span></p>
          <p className="text-xs text-primary/40 leading-relaxed max-w-[220px]">
            India's premium streetwear discovery. Never miss a drop.
          </p>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4">Explore</p>
          <div className="flex flex-col gap-2.5">
            <Link to="/browse" className="text-xs text-primary/50 hover:text-primary transition-colors">All Drops</Link>
            <Link to="/subscribe" className="text-xs text-primary/50 hover:text-primary transition-colors">Membership</Link>
          </div>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4">Brands</p>
          <div className="flex flex-col gap-2.5">
            <span className="text-xs text-primary/40">Crep Dog Crew</span>
            <span className="text-xs text-primary/40">Veg Non Veg</span>
            <span className="text-xs text-primary/40">Culture Circle</span>
            <span className="text-xs text-primary/40">Huemn</span>
            <span className="text-xs text-primary/40">Urban Monkey</span>
            <Link to="/browse" className="text-xs text-accent hover:text-primary transition-colors">+ 9 more</Link>
          </div>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4">Company</p>
          <div className="flex flex-col gap-2.5">
            <Link to="/partners" className="text-xs text-primary/50 hover:text-primary transition-colors">Partner With Us</Link>
          </div>
        </div>
      </div>
      <div className="mt-14 pt-6 border-t border-primary/[0.06] flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-[10px] text-primary/25">Drops Curated. All rights reserved.</p>
        <p className="text-[10px] text-primary/25">Made in India</p>
      </div>
    </div>
  </footer>
);

export default function LandingPage() {
  const [stats, setStats] = useState({ products: 0, brands: 0 });

  useEffect(() => {
    axios.get(`${API_URL}/scrape/status`).then(r => {
      setStats({ products: r.data.total_products, brands: r.data.brands?.length || 0 });
    }).catch(() => {});
  }, []);

  return (
    <div className="bg-background" data-testid="landing-page">
      <Header transparent />

      {/* Hero */}
      <section className="pt-28 pb-20 md:pt-36 md:pb-28 lg:pt-40 lg:pb-32">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16 items-center">
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 border border-accent/30 px-4 py-1.5 mb-8 animate-fade-up">
                <span className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
                <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent">Live — {stats.products}+ Products Tracked</span>
              </div>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-serif tracking-tight leading-[1.05] mb-6 animate-fade-up" style={{ animationDelay: '0.1s' }} data-testid="hero-heading">
                Never Miss<br />a Drop Again.
              </h1>
              <p className="text-base md:text-lg text-primary/50 leading-relaxed max-w-lg mb-10 animate-fade-up" style={{ animationDelay: '0.2s' }}>
                India's fastest streetwear alerts. Price drops, new collections, restocks — delivered to your WhatsApp in under 10 seconds.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 animate-fade-up" style={{ animationDelay: '0.3s' }}>
                <Link
                  to="/subscribe"
                  className="inline-flex items-center justify-center gap-3 bg-primary text-background px-8 py-4 font-medium text-sm hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300"
                  data-testid="hero-subscribe-cta"
                >
                  <MessageCircle className="w-4 h-4" strokeWidth={1.5} />
                  Get WhatsApp Alerts — ₹399/mo
                </Link>
                <Link
                  to="/browse"
                  className="inline-flex items-center justify-center gap-3 border border-primary/15 text-primary px-8 py-4 font-medium text-sm hover:border-accent hover:text-accent transition-all duration-300"
                  data-testid="hero-browse-cta"
                >
                  Explore Drops
                  <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
                </Link>
              </div>
            </div>
            <div className="lg:col-span-5 relative hidden lg:block">
              <div className="aspect-[4/5] overflow-hidden">
                <img
                  src="https://images.pexels.com/photos/14773444/pexels-photo-14773444.jpeg"
                  alt="Premium sneakers"
                  className="w-full h-full object-cover hover:scale-[1.03] transition-transform duration-700 ease-out"
                />
              </div>
              <div className="absolute -bottom-5 -left-5 bg-surface border border-primary/[0.06] p-5 shadow-soft">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2 h-2 bg-green-400 rounded-full" />
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent">Live Tracking</p>
                </div>
                <p className="font-serif text-lg">{stats.products}+ Products</p>
                <p className="text-[10px] text-primary/40 mt-0.5">{stats.brands} brands monitored</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3 Pillars */}
      <section className="py-20 md:py-28 border-t border-primary/[0.06]">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4">Three Pillars</p>
          <h2 className="font-serif text-3xl md:text-4xl tracking-tight mb-14">What We Do</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10 md:gap-16">
            {[
              { icon: <TrendingUp strokeWidth={1.5} />, title: 'Best Price Comparison', desc: 'Real-time prices from every major Indian retailer. Always know where it\'s cheapest.' },
              { icon: <Zap strokeWidth={1.5} />, title: 'Instant Price Drop Alerts', desc: 'The moment a price drops, you know. WhatsApp alerts in under 10 seconds.' },
              { icon: <Store strokeWidth={1.5} />, title: 'New Collection Drops', desc: 'Be first to know when brands drop new collections, restocks, and limited editions.' },
            ].map((f, i) => (
              <div key={i} className="animate-fade-up" style={{ animationDelay: `${i * 0.15}s` }} data-testid={`pillar-${i}`}>
                <div className="w-12 h-12 border border-accent/20 flex items-center justify-center mb-5 text-accent">
                  {f.icon}
                </div>
                <h3 className="font-serif text-xl mb-3">{f.title}</h3>
                <p className="text-sm text-primary/40 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Different */}
      <section className="py-20 md:py-28 bg-primary text-background">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4">Why Us</p>
          <h2 className="font-serif text-3xl md:text-4xl tracking-tight mb-14">Built Different</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { stat: '<10s', label: 'Alert delivery speed. Fastest in India.' },
              { stat: '₹399', label: 'Per month. No hidden fees. Cancel anytime.' },
              { stat: `${stats.products || '4,900'}+`, label: 'Products tracked in real-time across brands.' },
              { stat: '0%', label: 'Commission on your purchases. We never take a cut.' },
            ].map((s, i) => (
              <div key={i} className="animate-fade-up" style={{ animationDelay: `${i * 0.1}s` }} data-testid={`stat-${i}`}>
                <p className="font-serif text-4xl md:text-5xl text-accent mb-2">{s.stat}</p>
                <p className="text-sm text-background/50 leading-relaxed">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* For Brands */}
      <section className="py-20 md:py-28 border-t border-primary/[0.06]">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4">For Brands</p>
              <h2 className="font-serif text-3xl md:text-4xl tracking-tight mb-6">Partner With Drops Curated</h2>
              <p className="text-primary/50 leading-relaxed mb-8">
                Showcase your upcoming collections to India's most engaged streetwear community.
                Buy bulk memberships at a discount and gift them to your VIP customers.
              </p>
              <div className="space-y-4 mb-8">
                {[
                  'Feature upcoming collections before launch',
                  'Gift memberships to your premium customers',
                  'Real-time analytics on product performance',
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-5 h-5 border border-accent/30 flex items-center justify-center flex-shrink-0">
                      <svg className="w-3 h-3 text-accent" viewBox="0 0 12 12" fill="none"><path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    </div>
                    <p className="text-sm text-primary/60">{item}</p>
                  </div>
                ))}
              </div>
              <Link
                to="/partners"
                className="inline-flex items-center gap-3 border border-primary/15 text-primary px-6 py-3 text-sm font-medium hover:border-accent hover:text-accent transition-all duration-300"
                data-testid="partner-cta"
              >
                <Handshake className="w-4 h-4" strokeWidth={1.5} />
                Become a Partner
              </Link>
            </div>
            <div className="hidden lg:flex justify-center">
              <div className="grid grid-cols-2 gap-4">
                {['Crep Dog Crew', 'Huemn', 'Urban Monkey', 'Your Brand?'].map((b, i) => (
                  <div key={i} className={`border ${i === 3 ? 'border-accent/30 border-dashed' : 'border-primary/10'} p-6 flex items-center justify-center min-h-[120px]`}>
                    <p className={`text-sm font-medium text-center ${i === 3 ? 'text-accent' : 'text-primary/60'}`}>{b}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 md:py-28 bg-primary text-background">
        <div className="max-w-7xl mx-auto px-6 md:px-12 text-center">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-6">Join the Inner Circle</p>
          <h2 className="font-serif text-3xl md:text-4xl lg:text-5xl tracking-tight mb-4">Stop Missing Out</h2>
          <p className="text-base text-background/50 max-w-md mx-auto mb-10">
            WhatsApp alerts in 10 seconds. Price comparison across every store. ₹399/month.
          </p>
          <Link
            to="/subscribe"
            className="inline-flex items-center gap-3 bg-accent text-primary px-8 py-4 font-medium text-sm hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300"
            data-testid="cta-subscribe"
          >
            Subscribe Now
            <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
