import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Bell, Store, TrendingUp, MessageCircle } from 'lucide-react';

const NAV_LINKS = [
  { label: 'Drops', to: '/browse' },
  { label: 'Subscribe', to: '/subscribe' },
];

export const Header = ({ transparent = false }) => (
  <header className={`fixed top-0 left-0 right-0 z-50 ${transparent ? 'bg-background/85 backdrop-blur-xl' : 'bg-background'} border-b border-primary/10`}>
    <nav className="max-w-7xl mx-auto px-6 md:px-12 h-16 flex items-center justify-between">
      <Link to="/" className="font-serif text-xl tracking-tight" data-testid="logo-link">
        Drops <span className="text-accent">Curated</span>
      </Link>
      <div className="flex items-center gap-8">
        {NAV_LINKS.map(l => (
          <Link key={l.to} to={l.to} className="text-sm font-medium text-primary/70 hover:text-primary transition-colors duration-200" data-testid={`nav-${l.label.toLowerCase()}`}>
            {l.label}
          </Link>
        ))}
        <Link
          to="/subscribe"
          className="hidden md:inline-flex items-center gap-2 bg-primary text-background text-sm font-medium px-5 py-2 rounded-none hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300"
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
  <footer className="border-t border-primary/10 py-16 md:py-24">
    <div className="max-w-7xl mx-auto px-6 md:px-12">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
        <div>
          <p className="font-serif text-2xl mb-3">Drops <span className="text-accent">Curated</span></p>
          <p className="text-sm text-primary/50 leading-relaxed max-w-xs">
            India's premium streetwear discovery platform. Never miss a drop. Always get the best price.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-4">Explore</p>
          <div className="flex flex-col gap-3">
            <Link to="/browse" className="text-sm text-primary/60 hover:text-primary transition-colors">All Drops</Link>
            <Link to="/subscribe" className="text-sm text-primary/60 hover:text-primary transition-colors">WhatsApp Alerts</Link>
          </div>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-4">Brands</p>
          <div className="flex flex-col gap-3">
            <span className="text-sm text-primary/60">Crep Dog Crew</span>
            <span className="text-sm text-primary/60">Veg Non Veg</span>
            <span className="text-sm text-primary/60">Culture Circle</span>
          </div>
        </div>
      </div>
      <div className="mt-16 pt-8 border-t border-primary/10 text-center">
        <p className="text-xs text-primary/30">Drops Curated. All rights reserved.</p>
      </div>
    </div>
  </footer>
);

export default function LandingPage() {
  return (
    <div className="bg-background" data-testid="landing-page">
      <Header transparent />

      {/* Hero */}
      <section className="pt-32 pb-24 md:pt-40 md:pb-32">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-7">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-6 animate-fade-up">Premium Streetwear Discovery</p>
              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-medium tracking-tight leading-[1.05] mb-8 animate-fade-up" style={{ animationDelay: '0.1s' }} data-testid="hero-heading">
                Never Miss<br />a Drop.
              </h1>
              <p className="text-lg text-primary/60 leading-relaxed max-w-lg mb-10 animate-fade-up" style={{ animationDelay: '0.2s' }}>
                Curated drops from India's best streetwear brands. Real-time price comparison. WhatsApp alerts the moment prices fall.
              </p>
              <div className="flex flex-wrap gap-4 animate-fade-up" style={{ animationDelay: '0.3s' }}>
                <Link
                  to="/browse"
                  className="inline-flex items-center gap-3 bg-primary text-background px-8 py-4 rounded-none font-medium hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300"
                  data-testid="hero-browse-cta"
                >
                  Explore Drops
                  <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
                </Link>
                <Link
                  to="/subscribe"
                  className="inline-flex items-center gap-3 border border-primary/20 text-primary px-8 py-4 rounded-none font-medium hover:border-accent hover:text-accent transition-all duration-300"
                  data-testid="hero-subscribe-cta"
                >
                  <MessageCircle className="w-4 h-4" strokeWidth={1.5} />
                  WhatsApp Alerts
                </Link>
              </div>
            </div>
            <div className="lg:col-span-5 relative">
              <div className="aspect-[4/5] overflow-hidden">
                <img
                  src="https://images.pexels.com/photos/14773444/pexels-photo-14773444.jpeg"
                  alt="Premium sneakers"
                  className="w-full h-full object-cover hover:scale-105 transition-transform duration-700 ease-out"
                />
              </div>
              <div className="absolute -bottom-4 -left-4 bg-surface border border-primary/10 p-4 shadow-soft">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">Live Now</p>
                <p className="font-serif text-lg mt-1">998+ Products</p>
                <p className="text-xs text-primary/50 mt-1">Across 3 brands</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 md:py-32 border-t border-primary/10">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-4">How It Works</p>
          <h2 className="text-4xl md:text-5xl font-normal tracking-tight mb-16">The Smarter Way<br />to Shop Streetwear</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-16">
            {[
              { icon: <Store strokeWidth={1.5} />, title: 'Curated Drops', desc: 'We track Crep Dog Crew, Veg Non Veg, Culture Circle and more — so you don\'t have to.' },
              { icon: <TrendingUp strokeWidth={1.5} />, title: 'Price Comparison', desc: 'See real-time prices across stores. Buy from wherever it\'s cheapest.' },
              { icon: <Bell strokeWidth={1.5} />, title: 'WhatsApp Alerts', desc: 'Subscribe to get instant alerts on new drops and price reductions via WhatsApp.' },
            ].map((f, i) => (
              <div key={i} className="animate-fade-up" style={{ animationDelay: `${i * 0.15}s` }} data-testid={`feature-${i}`}>
                <div className="w-12 h-12 border border-accent/30 flex items-center justify-center mb-6 text-accent">
                  {f.icon}
                </div>
                <h3 className="font-serif text-xl mb-3">{f.title}</h3>
                <p className="text-sm text-primary/50 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 md:py-32 bg-primary text-background">
        <div className="max-w-7xl mx-auto px-6 md:px-12 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-6">Premium Service</p>
          <h2 className="font-serif text-4xl md:text-5xl tracking-tight mb-6">Never Miss a Price Drop</h2>
          <p className="text-lg text-background/60 max-w-xl mx-auto mb-10">
            Get instant WhatsApp notifications when your favourite streetwear drops in price or when limited editions go live.
          </p>
          <Link
            to="/subscribe"
            className="inline-flex items-center gap-3 bg-accent text-primary px-8 py-4 rounded-none font-medium hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300"
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
