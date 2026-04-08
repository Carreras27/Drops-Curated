import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Bell, Store, TrendingUp, MessageCircle, Zap, Clock, Shield, Handshake } from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

// Live Timestamp Component
const LiveTimestamp = () => {
  const [time, setTime] = useState(new Date());
  
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);
  
  const formatTime = (date) => {
    const hours = date.getHours();
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const hour12 = hours % 12 || 12;
    return { hour: hour12.toString().padStart(2, '0'), minutes, seconds, ampm };
  };
  
  const formatDate = (date) => {
    const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
    return {
      day: days[date.getDay()],
      date: date.getDate().toString().padStart(2, '0'),
      month: months[date.getMonth()]
    };
  };
  
  const t = formatTime(time);
  const d = formatDate(time);
  
  return (
    <div className="fixed bottom-4 left-4 z-50" data-testid="live-timestamp">
      <div className="flex items-center gap-2 text-primary/40">
        {/* Live Pulse */}
        <span className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
        
        {/* Date */}
        <span className="text-[10px] font-medium tracking-wide">
          {d.day} {d.date} {d.month}
        </span>
        
        <span className="text-primary/20">·</span>
        
        {/* Time */}
        <span className="text-[10px] font-mono">
          <span className="text-accent/70">{t.hour}</span>
          <span className="animate-pulse">:</span>
          <span className="text-accent/70">{t.minutes}</span>
          <span className="text-primary/30">:{t.seconds}</span>
          <span className="text-[8px] ml-0.5 text-primary/30">{t.ampm}</span>
        </span>
      </div>
    </div>
  );
};

// Funky Gen Z Style Background Elements
const GradientBlob = ({ className, color1 = "#D4AF37", color2 = "#001F3F", opacity = 0.15 }) => (
  <div 
    className={`absolute rounded-full blur-3xl ${className}`}
    style={{
      background: `radial-gradient(circle, ${color1} 0%, ${color2} 70%, transparent 100%)`,
      opacity
    }}
  />
);

const FloatingCircle = ({ className, filled = false }) => (
  <div 
    className={`absolute rounded-full ${filled ? 'bg-accent' : 'border-2 border-accent'} ${className}`}
  />
);

const GlitchLine = ({ className }) => (
  <div className={`absolute h-[2px] bg-gradient-to-r from-transparent via-accent to-transparent ${className}`} />
);

const NoiseOverlay = () => (
  <div 
    className="absolute inset-0 pointer-events-none opacity-[0.03] mix-blend-overlay"
    style={{
      backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
    }}
  />
);

const GeometricShape = ({ className, type = "square" }) => {
  if (type === "square") {
    return <div className={`absolute border border-accent/20 rotate-45 ${className}`} />;
  }
  if (type === "triangle") {
    return (
      <div 
        className={`absolute ${className}`}
        style={{
          width: 0,
          height: 0,
          borderLeft: '20px solid transparent',
          borderRight: '20px solid transparent',
          borderBottom: '35px solid',
          borderBottomColor: 'rgba(212, 175, 55, 0.15)',
        }}
      />
    );
  }
  return <div className={`absolute rounded-full border border-accent/20 ${className}`} />;
};

const StarBurst = ({ className }) => (
  <svg className={className} viewBox="0 0 100 100" fill="none">
    <path d="M50 0 L53 47 L100 50 L53 53 L50 100 L47 53 L0 50 L47 47 Z" fill="currentColor"/>
  </svg>
);

const NAV_LINKS = [
  { label: 'Drops', to: '/browse' },
  { label: 'Raffles', to: '/raffles' },
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

export const Footer = () => {
  const [brands, setBrands] = useState([]);
  
  useEffect(() => {
    const fetchBrands = async () => {
      try {
        const resp = await axios.get(`${API_URL}/scrape/status`);
        setBrands(resp.data.brands || []);
      } catch (err) {
        console.error('Failed to fetch brands for footer');
      }
    };
    fetchBrands();
  }, []);
  
  // Double the brands for seamless infinite scroll
  const scrollingBrands = [...brands, ...brands];
  
  return (
    <footer className="border-t border-primary/[0.06] bg-background">
      {/* Auto-scrolling Brands Marquee */}
      {brands.length > 0 && (
        <div className="py-8 border-b border-primary/[0.06] overflow-hidden">
          <p className="text-[10px] uppercase tracking-[0.3em] text-center text-accent mb-6">Brands Listed</p>
          <div className="relative">
            {/* Gradient overlays for fade effect */}
            <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-background to-transparent z-10" />
            <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-background to-transparent z-10" />
            
            {/* Scrolling container */}
            <div className="flex animate-marquee hover:pause-animation">
              {scrollingBrands.map((brand, idx) => (
                <Link
                  key={`${brand.key}-${idx}`}
                  to={`/brands/${brand.storeKey || brand.key?.toUpperCase()}`}
                  className="flex-shrink-0 mx-4 md:mx-6 group"
                >
                  <div className="flex flex-col items-center transition-all duration-300 transform group-hover:scale-110">
                    <div className="w-12 h-12 md:w-14 md:h-14 bg-primary/5 rounded-full flex items-center justify-center group-hover:bg-accent/20 transition-colors mb-2">
                      <span className="text-lg md:text-xl font-bold text-primary/40 group-hover:text-accent transition-colors">
                        {brand.name?.charAt(0) || '?'}
                      </span>
                    </div>
                    <span className="text-[10px] md:text-xs text-primary/40 group-hover:text-accent transition-colors whitespace-nowrap">
                      {brand.name}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Main Footer Content */}
      <div className="py-16 md:py-20">
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
                <Link to="/brands" className="text-xs text-primary/50 hover:text-primary transition-colors">All Brands</Link>
                <Link to="/raffles" className="text-xs text-primary/50 hover:text-primary transition-colors">Raffles</Link>
                <Link to="/subscribe" className="text-xs text-primary/50 hover:text-primary transition-colors">Membership</Link>
              </div>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4">Top Brands</p>
              <div className="flex flex-col gap-2.5">
                {brands.slice(0, 5).map((brand) => (
                  <Link 
                    key={brand.key} 
                    to={`/brands/${brand.storeKey || brand.key?.toUpperCase()}`}
                    className="text-xs text-primary/40 hover:text-accent transition-colors"
                  >
                    {brand.name}
                  </Link>
                ))}
                {brands.length > 5 && (
                  <Link to="/brands" className="text-xs text-accent hover:text-primary transition-colors">
                    + {brands.length - 5} more
                  </Link>
                )}
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
      </div>
    </footer>
  );
};

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
        {/* Funky Gen Z Background Elements */}
        <NoiseOverlay />
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {/* Gradient Blobs */}
          <GradientBlob className="w-[600px] h-[600px] -top-40 -right-40" opacity={0.08} />
          <GradientBlob className="w-[400px] h-[400px] bottom-0 -left-20" color1="#D4AF37" color2="#F5F5DC" opacity={0.06} />
          
          {/* Floating Circles */}
          <FloatingCircle className="w-4 h-4 top-32 left-[15%] opacity-20" />
          <FloatingCircle className="w-6 h-6 top-48 right-[30%] opacity-15" filled />
          <FloatingCircle className="w-3 h-3 bottom-40 left-[25%] opacity-25" />
          <FloatingCircle className="w-8 h-8 bottom-20 right-[15%] opacity-10" />
          
          {/* Geometric Shapes */}
          <GeometricShape className="w-12 h-12 top-40 left-[8%] opacity-30" type="square" />
          <GeometricShape className="w-16 h-16 bottom-32 right-[25%] opacity-20" type="circle" />
          <GeometricShape className="top-60 right-[10%] opacity-40" type="triangle" />
          
          {/* Glitch Lines */}
          <GlitchLine className="w-32 top-36 left-[5%] opacity-30" />
          <GlitchLine className="w-24 bottom-48 right-[20%] opacity-20" />
          
          {/* Star Bursts */}
          <StarBurst className="w-6 h-6 top-28 right-[35%] text-accent/20" />
          <StarBurst className="w-4 h-4 bottom-36 left-[30%] text-accent/15" />
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
              <div className="absolute -bottom-5 -left-5 bg-surface border border-primary/[0.06] p-5 shadow-soft overflow-hidden">
                {/* Animated scanning line */}
                <div className="absolute inset-0 overflow-hidden pointer-events-none">
                  <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-accent/50 to-transparent animate-scan" />
                </div>
                
                <div className="flex items-center gap-2 mb-2">
                  {/* Animated pulse ring */}
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
                  </span>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent">Live Tracking</p>
                </div>
                
                {/* Animated counter effect */}
                <p className="font-serif text-lg flex items-baseline gap-1">
                  <span className="tabular-nums">{stats.products?.toLocaleString() || '9,355'}</span>
                  <span className="text-accent animate-pulse">+</span>
                  <span className="text-sm font-normal text-primary/60">Products</span>
                </p>
                
                {/* Activity ticker */}
                <div className="flex items-center gap-2 mt-2 text-[9px] text-primary/40">
                  <span className="flex items-center gap-1">
                    <span className="w-1 h-1 bg-accent rounded-full animate-pulse" />
                    Scanning
                  </span>
                  <span className="text-primary/20">|</span>
                  <span>{stats.brands} brands</span>
                  <span className="text-primary/20">|</span>
                  <span className="text-green-500">Live</span>
                </div>
                
                {/* Mini activity bars */}
                <div className="flex items-end gap-[2px] mt-3 h-3">
                  {[...Array(8)].map((_, i) => (
                    <div 
                      key={i}
                      className="w-1 bg-accent/40 rounded-sm animate-pulse"
                      style={{ 
                        height: `${Math.random() * 100}%`,
                        animationDelay: `${i * 0.15}s`,
                        animationDuration: '0.8s'
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3 Pillars */}
      <section className="py-20 md:py-28 border-t border-primary/[0.06] relative overflow-hidden">
        {/* Funky Background */}
        <NoiseOverlay />
        <div className="absolute inset-0 pointer-events-none">
          <GradientBlob className="w-[500px] h-[500px] -top-60 -left-40" color1="#F5F5DC" color2="#D4AF37" opacity={0.04} />
          <FloatingCircle className="w-5 h-5 top-20 right-[20%] opacity-15" filled />
          <FloatingCircle className="w-10 h-10 bottom-20 left-[10%] opacity-10" />
          <GeometricShape className="w-14 h-14 top-32 right-[8%] opacity-25" type="square" />
          <StarBurst className="w-5 h-5 bottom-40 right-[30%] text-accent/15" />
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
        {/* Funky Dark Background */}
        <div className="absolute inset-0 pointer-events-none">
          <GradientBlob className="w-[700px] h-[700px] -top-40 -right-60" color1="#D4AF37" color2="#001F3F" opacity={0.12} />
          <GradientBlob className="w-[400px] h-[400px] bottom-0 left-0" color1="#F5F5DC" color2="#001F3F" opacity={0.06} />
          
          {/* Floating elements on dark */}
          <FloatingCircle className="w-6 h-6 top-24 left-[15%] opacity-10 border-background/30" />
          <FloatingCircle className="w-4 h-4 bottom-32 right-[25%] opacity-15 bg-accent/20" filled />
          <FloatingCircle className="w-8 h-8 top-40 right-[12%] opacity-8 border-accent/20" />
          
          <GeometricShape className="w-16 h-16 bottom-24 left-[8%] opacity-15 border-background/20" type="square" />
          <StarBurst className="w-8 h-8 top-32 right-[30%] text-accent/10" />
          <StarBurst className="w-5 h-5 bottom-40 left-[35%] text-background/10" />
          
          <GlitchLine className="w-40 top-20 left-[10%] opacity-15" />
          <GlitchLine className="w-28 bottom-28 right-[15%] opacity-10" />
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
        {/* Funky Background */}
        <NoiseOverlay />
        <div className="absolute inset-0 pointer-events-none">
          <GradientBlob className="w-[450px] h-[450px] -bottom-40 -right-40" opacity={0.05} />
          <FloatingCircle className="w-5 h-5 top-32 right-[15%] opacity-20" />
          <FloatingCircle className="w-3 h-3 bottom-24 left-[20%] opacity-15" filled />
          <GeometricShape className="w-10 h-10 top-20 left-[5%] opacity-20" type="square" />
          <StarBurst className="w-4 h-4 top-48 right-[25%] text-accent/20" />
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
        {/* Funky Dark CTA Background */}
        <div className="absolute inset-0 pointer-events-none">
          <GradientBlob className="w-[600px] h-[600px] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" color1="#D4AF37" color2="#001F3F" opacity={0.15} />
          
          {/* Scattered elements */}
          <FloatingCircle className="w-4 h-4 top-16 left-[12%] opacity-15 bg-accent/30" filled />
          <FloatingCircle className="w-6 h-6 top-20 right-[18%] opacity-10 border-background/20" />
          <FloatingCircle className="w-3 h-3 bottom-20 left-[25%] opacity-20 bg-background/20" filled />
          <FloatingCircle className="w-5 h-5 bottom-16 right-[15%] opacity-15 border-accent/30" />
          
          <GeometricShape className="w-12 h-12 top-24 left-[8%] opacity-15 border-accent/20" type="square" />
          <GeometricShape className="w-10 h-10 bottom-28 right-[10%] opacity-10 border-background/15" type="square" />
          
          <StarBurst className="w-6 h-6 top-12 right-[30%] text-accent/15" />
          <StarBurst className="w-4 h-4 bottom-24 left-[35%] text-background/10" />
          <StarBurst className="w-5 h-5 top-1/2 left-[5%] text-accent/10" />
          
          <GlitchLine className="w-32 top-28 left-[15%] opacity-15" />
          <GlitchLine className="w-24 bottom-32 right-[20%] opacity-10" />
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
      
      {/* Live Timestamp */}
      <LiveTimestamp />
    </div>
  );
}
