import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Bell, Store, TrendingUp, MessageCircle, Zap, Clock, Shield, Handshake } from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

// Monotone Line Drawing SVGs for background decoration
const SneakerOutline = ({ className }) => (
  <svg className={className} viewBox="0 0 200 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M15 70 L25 65 Q35 60 50 60 L120 60 Q140 60 155 55 L175 45 Q185 42 190 50 L190 65 Q190 75 180 78 L40 78 Q25 78 18 72 Z" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M50 60 L55 45 Q60 35 75 32 L110 32 Q125 32 130 40 L140 55" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M75 32 L80 20 Q85 15 95 15 L105 15" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <circle cx="60" cy="78" r="3" stroke="currentColor" strokeWidth="1"/>
    <circle cx="80" cy="78" r="3" stroke="currentColor" strokeWidth="1"/>
    <circle cx="100" cy="78" r="3" stroke="currentColor" strokeWidth="1"/>
    <circle cx="120" cy="78" r="3" stroke="currentColor" strokeWidth="1"/>
    <path d="M155 55 L160 50 L165 55" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
  </svg>
);

const HoodieOutline = ({ className }) => (
  <svg className={className} viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M70 40 Q100 25 130 40" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M70 40 L50 55 L30 140 L30 180 L85 180 L85 160" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M130 40 L150 55 L170 140 L170 180 L115 180 L115 160" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M85 160 Q100 155 115 160" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <ellipse cx="100" cy="165" rx="20" ry="8" stroke="currentColor" strokeWidth="1"/>
    <path d="M30 140 L10 145 L10 100 L30 95" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M170 140 L190 145 L190 100 L170 95" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M75 50 Q100 70 125 50" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M80 55 Q100 75 120 55" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M70 40 L60 30 Q100 10 140 30 L130 40" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
  </svg>
);

const TShirtOutline = ({ className }) => (
  <svg className={className} viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M75 30 Q100 20 125 30" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M75 30 L45 45 L20 80 L40 90 L55 70 L55 180 L145 180 L145 70 L160 90 L180 80 L155 45 L125 30" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
    <ellipse cx="100" cy="30" rx="15" ry="8" stroke="currentColor" strokeWidth="1"/>
  </svg>
);

const JacketOutline = ({ className }) => (
  <svg className={className} viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M80 25 Q100 18 120 25" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M80 25 L60 35 L40 60 L25 140 L25 185 L90 185 L90 60" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M120 25 L140 35 L160 60 L175 140 L175 185 L110 185 L110 60" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M90 60 L100 185" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M110 60 L100 185" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M25 140 L5 145 L5 90 L25 85" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M175 140 L195 145 L195 90 L175 85" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <rect x="35" y="110" width="20" height="25" rx="2" stroke="currentColor" strokeWidth="1"/>
    <rect x="145" y="110" width="20" height="25" rx="2" stroke="currentColor" strokeWidth="1"/>
    <circle cx="95" cy="80" r="3" stroke="currentColor" strokeWidth="1"/>
    <circle cx="95" cy="100" r="3" stroke="currentColor" strokeWidth="1"/>
    <circle cx="95" cy="120" r="3" stroke="currentColor" strokeWidth="1"/>
  </svg>
);

const HighTopOutline = ({ className }) => (
  <svg className={className} viewBox="0 0 200 150" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M30 110 L45 105 Q60 100 80 100 L140 100 Q160 100 170 95 L185 85 Q195 80 195 90 L195 110 Q195 120 185 122 L50 122 Q35 122 32 115 Z" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M80 100 L80 50 Q80 35 95 30 L130 30 Q145 30 150 45 L155 95" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    <path d="M90 45 L145 45" stroke="currentColor" strokeWidth="0.8" strokeLinecap="round"/>
    <path d="M88 55 L147 55" stroke="currentColor" strokeWidth="0.8" strokeLinecap="round"/>
    <path d="M86 65 L149 65" stroke="currentColor" strokeWidth="0.8" strokeLinecap="round"/>
    <path d="M84 75 L151 75" stroke="currentColor" strokeWidth="0.8" strokeLinecap="round"/>
    <path d="M82 85 L153 85" stroke="currentColor" strokeWidth="0.8" strokeLinecap="round"/>
    <circle cx="70" cy="122" r="4" stroke="currentColor" strokeWidth="1"/>
    <circle cx="95" cy="122" r="4" stroke="currentColor" strokeWidth="1"/>
    <circle cx="120" cy="122" r="4" stroke="currentColor" strokeWidth="1"/>
  </svg>
);

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
      <section className="pt-28 pb-20 md:pt-36 md:pb-28 lg:pt-40 lg:pb-32 relative overflow-hidden">
        {/* Background Line Drawings */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <SneakerOutline className="absolute top-20 -left-10 w-48 h-24 text-primary/[0.06] rotate-[-15deg]" />
          <HoodieOutline className="absolute top-40 right-0 w-40 h-40 text-primary/[0.06] rotate-[10deg] translate-x-1/4" />
          <TShirtOutline className="absolute bottom-20 left-10 w-32 h-32 text-primary/[0.06] rotate-[5deg]" />
          <HighTopOutline className="absolute bottom-10 right-20 w-44 h-32 text-primary/[0.06] rotate-[-8deg]" />
          <JacketOutline className="absolute top-1/2 left-1/4 w-28 h-28 text-primary/[0.05] rotate-[12deg] hidden lg:block" />
        </div>
        
        <div className="max-w-7xl mx-auto px-6 md:px-12 relative z-10">
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
      <section className="py-20 md:py-28 border-t border-primary/[0.06] relative overflow-hidden">
        {/* Background Line Drawings */}
        <div className="absolute inset-0 pointer-events-none">
          <SneakerOutline className="absolute top-10 right-10 w-56 h-28 text-primary/[0.05] rotate-[8deg]" />
          <TShirtOutline className="absolute bottom-10 left-20 w-36 h-36 text-primary/[0.05] rotate-[-5deg]" />
        </div>
        
        <div className="max-w-7xl mx-auto px-6 md:px-12 relative z-10">
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
      <section className="py-20 md:py-28 bg-primary text-background relative overflow-hidden">
        {/* Background Line Drawings - lighter for dark bg */}
        <div className="absolute inset-0 pointer-events-none">
          <HighTopOutline className="absolute top-5 left-5 w-52 h-36 text-background/[0.06] rotate-[-10deg]" />
          <HoodieOutline className="absolute bottom-5 right-5 w-44 h-44 text-background/[0.06] rotate-[15deg]" />
          <JacketOutline className="absolute top-1/2 right-1/4 w-36 h-36 text-background/[0.05] -translate-y-1/2 hidden lg:block" />
        </div>
        
        <div className="max-w-7xl mx-auto px-6 md:px-12 relative z-10">
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
      <section className="py-20 md:py-28 border-t border-primary/[0.06] relative overflow-hidden">
        {/* Background Line Drawings */}
        <div className="absolute inset-0 pointer-events-none">
          <SneakerOutline className="absolute bottom-20 right-10 w-48 h-24 text-primary/[0.05] rotate-[5deg]" />
          <TShirtOutline className="absolute top-20 left-5 w-32 h-32 text-primary/[0.05] rotate-[-8deg]" />
        </div>
        
        <div className="max-w-7xl mx-auto px-6 md:px-12 relative z-10">
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
      <section className="py-20 md:py-28 bg-primary text-background relative overflow-hidden">
        {/* Background Line Drawings */}
        <div className="absolute inset-0 pointer-events-none">
          <SneakerOutline className="absolute top-10 left-10 w-40 h-20 text-background/[0.06] rotate-[12deg]" />
          <HighTopOutline className="absolute top-5 right-20 w-48 h-32 text-background/[0.06] rotate-[-5deg]" />
          <HoodieOutline className="absolute bottom-5 left-1/4 w-36 h-36 text-background/[0.05] rotate-[8deg]" />
          <TShirtOutline className="absolute bottom-10 right-10 w-32 h-32 text-background/[0.06] rotate-[-12deg]" />
        </div>
        
        <div className="max-w-7xl mx-auto px-6 md:px-12 text-center relative z-10">
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
