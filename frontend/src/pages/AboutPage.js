import React from 'react';
import { Link } from 'react-router-dom';
import { Header, Footer } from './LandingPage';
import { Bell, Zap, Shield, Users, TrendingUp, Clock, Heart, Target } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

export default function AboutPage() {
  return (
    <div className="bg-background min-h-screen" data-testid="about-page">
      <Header />
      
      {/* Hero Section */}
      <section className="pt-28 pb-16 md:pt-36 md:pb-20 bg-gradient-to-b from-primary/5 to-transparent">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <span className="inline-block text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4">About Us</span>
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-serif mb-6">
            India's Fastest<br />Streetwear Alerts
          </h1>
          <p className="text-lg text-primary/60 max-w-2xl mx-auto">
            We built Drops Curated because we were tired of missing out on limited drops. 
            Now, over 11,000 products from 23 premium brands are tracked in real-time — 
            and you get alerts before anyone else.
          </p>
        </div>
      </section>
      
      {/* Our Story */}
      <section className="py-16 md:py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4 block">Our Story</span>
              <h2 className="text-3xl md:text-4xl font-serif mb-6">Born from FOMO</h2>
              <div className="space-y-4 text-primary/70">
                <p>
                  It started with a missed Jordan drop. Then a Yeezy restock we found out about 3 hours too late. 
                  And that limited AMIRI collab that sold out while we were sleeping.
                </p>
                <p>
                  We realized the problem: Indian streetwear enthusiasts had no reliable way to track drops 
                  across multiple stores. By the time news spread on Instagram or Discord, the best pieces were gone.
                </p>
                <p>
                  So we built Drops Curated — a platform that scans 23 premium streetwear stores every 15 minutes 
                  and sends WhatsApp alerts within 10 seconds of detecting a new drop or price change.
                </p>
                <p className="font-medium text-primary">
                  No more FOMO. No more L's. Just instant alerts for the drops you care about.
                </p>
              </div>
            </div>
            <div className="relative">
              <div className="aspect-square bg-surface overflow-hidden">
                <img 
                  src="https://images.pexels.com/photos/1598505/pexels-photo-1598505.jpeg"
                  alt="Streetwear collection"
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="absolute -bottom-4 -left-4 bg-accent text-primary p-4">
                <p className="text-2xl font-serif">23+</p>
                <p className="text-xs uppercase tracking-wider">Premium Brands</p>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* What Makes Us Different */}
      <section className="py-16 md:py-24 bg-surface">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4 block">Why Choose Us</span>
            <h2 className="text-3xl md:text-4xl font-serif">What Makes Us Different</h2>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-12 h-12 bg-accent/10 flex items-center justify-center mx-auto mb-4">
                <Zap className="w-6 h-6 text-accent" />
              </div>
              <h3 className="font-medium mb-2">10-Second Alerts</h3>
              <p className="text-sm text-primary/60">From detection to your WhatsApp in under 10 seconds. Faster than any Discord or Telegram group.</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-accent/10 flex items-center justify-center mx-auto mb-4">
                <Target className="w-6 h-6 text-accent" />
              </div>
              <h3 className="font-medium mb-2">Size-Specific</h3>
              <p className="text-sm text-primary/60">Only get alerts for YOUR sizes. No more clicking through to find your size is sold out.</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-accent/10 flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="w-6 h-6 text-accent" />
              </div>
              <h3 className="font-medium mb-2">Price Tracking</h3>
              <p className="text-sm text-primary/60">We track prices across stores and alert you the moment something drops in price.</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-accent/10 flex items-center justify-center mx-auto mb-4">
                <Shield className="w-6 h-6 text-accent" />
              </div>
              <h3 className="font-medium mb-2">Verified Stores Only</h3>
              <p className="text-sm text-primary/60">We only track authorized retailers and verified resellers. No fakes, no scams.</p>
            </div>
          </div>
        </div>
      </section>
      
      {/* Stats */}
      <section className="py-16 md:py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <p className="text-4xl md:text-5xl font-serif text-accent mb-2">11,400+</p>
              <p className="text-sm text-primary/60 uppercase tracking-wider">Products Tracked</p>
            </div>
            <div>
              <p className="text-4xl md:text-5xl font-serif text-accent mb-2">23</p>
              <p className="text-sm text-primary/60 uppercase tracking-wider">Premium Brands</p>
            </div>
            <div>
              <p className="text-4xl md:text-5xl font-serif text-accent mb-2">15 min</p>
              <p className="text-sm text-primary/60 uppercase tracking-wider">Scan Interval</p>
            </div>
            <div>
              <p className="text-4xl md:text-5xl font-serif text-accent mb-2">&lt;10s</p>
              <p className="text-sm text-primary/60 uppercase tracking-wider">Alert Speed</p>
            </div>
          </div>
        </div>
      </section>
      
      {/* Brands We Track */}
      <section className="py-16 md:py-24 bg-surface">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4 block">Our Network</span>
            <h2 className="text-3xl md:text-4xl font-serif mb-4">Brands We Track</h2>
            <p className="text-primary/60">Premium Indian and international streetwear, all in one place.</p>
          </div>
          
          <div className="flex flex-wrap justify-center gap-4">
            {[
              'Crep Dog Crew', 'Superkicks', 'Urban Monkey', 'Huemn', 'Capsul',
              'Mainstreet Marketplace', 'VegNonVeg', 'Bluorng', 'Almost Gods',
              'House of Koala', 'Nike', 'Adidas', 'Jordan', 'ON Running',
              'New Balance', 'AMIRI', 'Off-White', 'Supreme', 'Palace',
              'Fear of God', 'Yeezy', 'Stussy', 'BAPE'
            ].map((brand) => (
              <span 
                key={brand}
                className="px-4 py-2 bg-background border border-primary/10 text-sm text-primary/70 hover:border-accent hover:text-accent transition-colors"
              >
                {brand}
              </span>
            ))}
          </div>
        </div>
      </section>
      
      {/* CTA */}
      <section className="py-16 md:py-24">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-4xl font-serif mb-4">Ready to Never Miss a Drop?</h2>
          <p className="text-primary/60 mb-8 max-w-xl mx-auto">
            Join Drops Curated today and get instant WhatsApp alerts for new releases, 
            price drops, and restocks from your favorite brands.
          </p>
          <Link
            to="/subscribe"
            className="inline-flex items-center gap-2 bg-primary text-background px-8 py-4 font-medium hover:-translate-y-0.5 hover:shadow-lift transition-all"
            data-testid="about-cta"
          >
            <Bell className="w-4 h-4" />
            Get Alerts — ₹399/mo
          </Link>
        </div>
      </section>
      
      <Footer />
    </div>
  );
}
