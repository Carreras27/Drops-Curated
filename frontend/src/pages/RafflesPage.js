import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Users, Trophy, Shield, AlertTriangle, Check, X, Ticket, ChevronRight } from 'lucide-react';
import { Header, Footer } from './LandingPage';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

// Countdown Timer Component
const Countdown = ({ targetDate, label, onComplete }) => {
  const [timeLeft, setTimeLeft] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    const calculateTimeLeft = () => {
      const now = new Date().getTime();
      const target = new Date(targetDate).getTime();
      const difference = target - now;

      if (difference <= 0) {
        setIsComplete(true);
        onComplete?.();
        return { days: 0, hours: 0, minutes: 0, seconds: 0 };
      }

      return {
        days: Math.floor(difference / (1000 * 60 * 60 * 24)),
        hours: Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
        minutes: Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60)),
        seconds: Math.floor((difference % (1000 * 60)) / 1000),
      };
    };

    setTimeLeft(calculateTimeLeft());
    const timer = setInterval(() => setTimeLeft(calculateTimeLeft()), 1000);
    return () => clearInterval(timer);
  }, [targetDate, onComplete]);

  if (isComplete) {
    return <span className="text-accent font-medium">{label} Complete</span>;
  }

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-primary/40 uppercase tracking-wider">{label}</span>
      <div className="flex items-center gap-1 font-mono text-sm">
        {timeLeft.days > 0 && (
          <>
            <span className="bg-primary/5 px-2 py-1">{timeLeft.days}d</span>
            <span className="text-primary/20">:</span>
          </>
        )}
        <span className="bg-primary/5 px-2 py-1">{String(timeLeft.hours).padStart(2, '0')}h</span>
        <span className="text-primary/20">:</span>
        <span className="bg-primary/5 px-2 py-1">{String(timeLeft.minutes).padStart(2, '0')}m</span>
        <span className="text-primary/20">:</span>
        <span className="bg-accent/10 text-accent px-2 py-1">{String(timeLeft.seconds).padStart(2, '0')}s</span>
      </div>
    </div>
  );
};

// Raffle Card Component
const RaffleCard = ({ raffle, userPhone, onEnter }) => {
  const [entry, setEntry] = useState(null);
  const [checking, setChecking] = useState(true);

  const now = new Date();
  const entryStart = new Date(raffle.entry_start);
  const entryEnd = new Date(raffle.entry_end);
  const drawTime = new Date(raffle.draw_time);

  const isUpcoming = now < entryStart;
  const isOpen = now >= entryStart && now < entryEnd;
  const isClosed = now >= entryEnd && raffle.status !== 'completed';
  const isCompleted = raffle.status === 'completed';

  useEffect(() => {
    if (userPhone) {
      checkEntry();
    } else {
      setChecking(false);
    }
  }, [userPhone, raffle.id]);

  const checkEntry = async () => {
    try {
      const resp = await axios.get(`${API_URL}/raffles/check-entry/${raffle.id}/${userPhone}`);
      setEntry(resp.data);
    } catch {} finally {
      setChecking(false);
    }
  };

  const getStatusBadge = () => {
    if (isCompleted) return <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 bg-primary/10 text-primary">Completed</span>;
    if (isClosed) return <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 bg-orange-500/10 text-orange-500">Drawing Soon</span>;
    if (isOpen) return <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 bg-green-500/10 text-green-500 animate-pulse">Open Now</span>;
    return <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 bg-accent/10 text-accent">Upcoming</span>;
  };

  return (
    <div className="border border-primary/10 bg-surface overflow-hidden group hover:border-accent/30 transition-colors" data-testid={`raffle-${raffle.id}`}>
      {/* Product Image */}
      <div className="aspect-square relative overflow-hidden">
        <img 
          src={raffle.product_image} 
          alt={raffle.product_name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />
        <div className="absolute top-3 left-3">
          {getStatusBadge()}
        </div>
        <div className="absolute top-3 right-3 bg-red-500 text-white px-2 py-1 text-[10px] font-bold">
          {raffle.total_pairs} PAIRS
        </div>
        {entry?.is_winner && (
          <div className="absolute inset-0 bg-green-500/90 flex items-center justify-center">
            <div className="text-center text-white">
              <Trophy className="w-12 h-12 mx-auto mb-2" />
              <p className="font-bold text-xl">YOU WON!</p>
              <p className="text-sm opacity-90">Size {entry.selected_size}</p>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-accent mb-1">{raffle.brand}</p>
        <h3 className="font-serif text-lg mb-2 line-clamp-2">{raffle.product_name}</h3>
        
        <div className="flex items-center justify-between mb-4">
          <span className="font-medium">₹{raffle.retail_price?.toLocaleString('en-IN')}</span>
          <div className="flex items-center gap-1 text-xs text-primary/50">
            <Users className="w-3 h-3" />
            <span>{raffle.total_entries || 0} entries</span>
          </div>
        </div>

        {/* Countdown */}
        <div className="mb-4">
          {isUpcoming && <Countdown targetDate={raffle.entry_start} label="Opens in" />}
          {isOpen && <Countdown targetDate={raffle.entry_end} label="Closes in" />}
          {isClosed && <Countdown targetDate={raffle.draw_time} label="Draw in" />}
          {isCompleted && (
            <p className="text-xs text-primary/40">
              Winners announced • {raffle.winners?.length || 0} selected
            </p>
          )}
        </div>

        {/* Entry Status / Action */}
        {checking ? (
          <div className="h-10 bg-primary/5 animate-pulse" />
        ) : entry?.entered ? (
          <div className="flex items-center gap-2 text-sm">
            <Check className="w-4 h-4 text-green-500" />
            <span className="text-green-600">Entered • Size {entry.selected_size}</span>
          </div>
        ) : isOpen ? (
          <button
            onClick={() => onEnter(raffle)}
            className="w-full bg-accent text-primary py-3 text-sm font-medium hover:bg-accent/90 transition-colors flex items-center justify-center gap-2"
            data-testid={`enter-raffle-${raffle.id}`}
          >
            <Ticket className="w-4 h-4" />
            Enter Raffle
          </button>
        ) : isUpcoming ? (
          <button disabled className="w-full border border-primary/10 py-3 text-sm text-primary/40 cursor-not-allowed">
            Entry Opens Soon
          </button>
        ) : (
          <button disabled className="w-full border border-primary/10 py-3 text-sm text-primary/40 cursor-not-allowed">
            Entry Closed
          </button>
        )}
      </div>
    </div>
  );
};

// Entry Modal Component
const EntryModal = ({ raffle, userPhone, userName, onClose, onSuccess }) => {
  const [selectedSize, setSelectedSize] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!selectedSize) {
      toast.error('Please select a size');
      return;
    }
    if (!userPhone) {
      toast.error('Please subscribe first to enter raffles');
      return;
    }

    setLoading(true);
    try {
      const resp = await axios.post(`${API_URL}/raffles/enter`, {
        raffle_id: raffle.id,
        phone: userPhone,
        name: userName || 'VIP Member',
        selected_size: selectedSize,
      });
      
      toast.success(resp.data.message);
      onSuccess?.();
      onClose();
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to enter raffle';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-background border border-primary/10 max-w-md w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="sticky top-0 bg-background border-b border-primary/10 p-4 flex items-center justify-between">
          <div>
            <p className="text-xs text-accent uppercase tracking-widest">Enter Raffle</p>
            <h3 className="font-serif text-xl">{raffle.product_name}</h3>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center hover:bg-primary/5">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-6">
          {/* Product Preview */}
          <div className="flex gap-4">
            <img src={raffle.product_image} alt="" className="w-24 h-24 object-cover" />
            <div>
              <p className="text-xs text-accent">{raffle.brand}</p>
              <p className="font-medium">₹{raffle.retail_price?.toLocaleString('en-IN')}</p>
              <p className="text-xs text-primary/40 mt-1">{raffle.total_pairs} pairs available</p>
            </div>
          </div>

          {/* Bot Protection Notice */}
          <div className="flex items-start gap-3 p-3 bg-green-500/5 border border-green-500/20">
            <Shield className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-green-600">Secured Entry</p>
              <p className="text-xs text-primary/50">Bot protection active. One entry per person. Fair random draw.</p>
            </div>
          </div>

          {/* Size Selection */}
          <div>
            <p className="text-xs text-primary/50 uppercase tracking-wider mb-3">Select Your Size</p>
            <div className="grid grid-cols-4 gap-2">
              {raffle.sizes_available?.map(size => (
                <button
                  key={size}
                  onClick={() => setSelectedSize(size)}
                  className={`py-3 text-sm border transition-colors ${
                    selectedSize === size 
                      ? 'border-accent bg-accent/10 text-accent font-medium' 
                      : 'border-primary/10 hover:border-primary/30'
                  }`}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>

          {/* Requirements */}
          <div>
            <p className="text-xs text-primary/50 uppercase tracking-wider mb-2">Entry Requirements</p>
            <ul className="space-y-1">
              {raffle.entry_requirements?.map((req, i) => (
                <li key={i} className="flex items-center gap-2 text-xs text-primary/60">
                  <Check className="w-3 h-3 text-green-500" />
                  {req}
                </li>
              ))}
            </ul>
          </div>

          {/* Draw Info */}
          <div className="flex items-center gap-2 text-xs text-primary/40">
            <Clock className="w-3 h-3" />
            Draw: {new Date(raffle.draw_time).toLocaleString('en-IN', { 
              dateStyle: 'medium', 
              timeStyle: 'short' 
            })}
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={loading || !selectedSize}
            className="w-full bg-accent text-primary py-4 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              'Entering...'
            ) : (
              <>
                <Ticket className="w-4 h-4" />
                Confirm Entry
              </>
            )}
          </button>

          <p className="text-[10px] text-center text-primary/30">
            By entering, you agree to purchase if selected. Winners will be notified via WhatsApp.
          </p>
        </div>
      </div>
    </div>
  );
};

export default function RafflesPage() {
  const [raffles, setRaffles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRaffle, setSelectedRaffle] = useState(null);
  const [userPhone, setUserPhone] = useState('');
  const [userName, setUserName] = useState('');
  const [filter, setFilter] = useState('all'); // all, open, upcoming, completed

  useEffect(() => {
    fetchRaffles();
    // Check if user is logged in (from localStorage)
    const savedPhone = localStorage.getItem('dc_phone');
    const savedName = localStorage.getItem('dc_name');
    if (savedPhone) setUserPhone(savedPhone);
    if (savedName) setUserName(savedName);
  }, []);

  const fetchRaffles = async () => {
    setLoading(true);
    try {
      const resp = await axios.get(`${API_URL}/raffles`);
      setRaffles(resp.data.raffles || []);
    } catch (err) {
      console.error('Failed to fetch raffles', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredRaffles = raffles.filter(r => {
    if (filter === 'all') return true;
    if (filter === 'open') return r.status === 'open' || (new Date() >= new Date(r.entry_start) && new Date() < new Date(r.entry_end));
    if (filter === 'upcoming') return new Date() < new Date(r.entry_start);
    if (filter === 'completed') return r.status === 'completed';
    return true;
  });

  return (
    <div className="bg-background min-h-screen" data-testid="raffles-page">
      <Header />

      <main className="pt-24 pb-16">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          {/* Hero */}
          <div className="mb-12">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-accent/10 flex items-center justify-center">
                <Ticket className="w-5 h-5 text-accent" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">Fair Drops</p>
                <h1 className="font-serif text-4xl md:text-5xl tracking-tight">Raffles</h1>
              </div>
            </div>
            <p className="text-primary/50 max-w-xl">
              Enter for a chance to purchase limited releases. Secured with bot protection and randomized fair drawing.
            </p>
          </div>

          {/* Security Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
            {[
              { icon: Shield, title: 'Bot Protection', desc: 'Fingerprinting & rate limiting block automated entries' },
              { icon: Users, title: 'One Entry Per Person', desc: 'Verified VIP members only, one entry per raffle' },
              { icon: Trophy, title: 'Fair Random Draw', desc: 'Cryptographically secure random winner selection' },
            ].map((feature, i) => (
              <div key={i} className="flex items-start gap-3 p-4 border border-primary/10">
                <feature.icon className="w-5 h-5 text-accent flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium">{feature.title}</p>
                  <p className="text-xs text-primary/40">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Filters */}
          <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-2">
            {[
              { key: 'all', label: 'All Raffles' },
              { key: 'open', label: 'Open Now' },
              { key: 'upcoming', label: 'Upcoming' },
              { key: 'completed', label: 'Completed' },
            ].map(f => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={`px-4 py-2 text-sm whitespace-nowrap border transition-colors ${
                  filter === f.key 
                    ? 'border-accent bg-accent/5 text-accent' 
                    : 'border-primary/10 text-primary/50 hover:border-primary/30'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Raffles Grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="border border-primary/10 p-4 animate-pulse">
                  <div className="aspect-square bg-primary/5 mb-4" />
                  <div className="h-4 bg-primary/5 mb-2 w-1/3" />
                  <div className="h-6 bg-primary/5 mb-4" />
                  <div className="h-10 bg-primary/5" />
                </div>
              ))}
            </div>
          ) : filteredRaffles.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredRaffles.map(raffle => (
                <RaffleCard
                  key={raffle.id}
                  raffle={raffle}
                  userPhone={userPhone}
                  onEnter={setSelectedRaffle}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-24">
              <Ticket className="w-12 h-12 text-primary/10 mx-auto mb-4" />
              <p className="font-serif text-2xl text-primary/30 mb-2">No raffles available</p>
              <p className="text-sm text-primary/20">Check back soon for new drops</p>
            </div>
          )}

          {/* CTA for non-members */}
          {!userPhone && (
            <div className="mt-16 p-8 bg-primary text-background text-center">
              <h3 className="font-serif text-2xl mb-2">Want to Enter Raffles?</h3>
              <p className="text-background/60 mb-6">VIP membership required to participate in exclusive drops</p>
              <Link
                to="/subscribe"
                className="inline-flex items-center gap-2 bg-accent text-primary px-8 py-3 font-medium hover:bg-accent/90 transition-colors"
              >
                Become a VIP Member
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          )}
        </div>
      </main>

      <Footer />

      {/* Entry Modal */}
      {selectedRaffle && (
        <EntryModal
          raffle={selectedRaffle}
          userPhone={userPhone}
          userName={userName}
          onClose={() => setSelectedRaffle(null)}
          onSuccess={fetchRaffles}
        />
      )}
    </div>
  );
}
