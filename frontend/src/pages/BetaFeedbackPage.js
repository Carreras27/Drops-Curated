import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Bug, Lightbulb, Heart, MessageSquare, Send, Loader2, Check } from 'lucide-react';

const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Low-friction feedback collector for beta users. No auth required.
export default function BetaFeedbackPage() {
  const [category, setCategory] = useState('bug');
  const [message, setMessage] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [rating, setRating] = useState(0);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const navigate = useNavigate();

  const submit = async () => {
    if (message.trim().length < 5) { toast.error('Tell us a bit more — at least a sentence.'); return; }
    setLoading(true);
    try {
      await axios.post(`${API_URL}/beta/feedback`, {
        phone: phone.trim() || null,
        email: email.trim() || null,
        category,
        message: message.trim(),
        page: typeof window !== 'undefined' ? window.location.pathname : '',
        rating: rating || null,
      });
      setSubmitted(true);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Could not submit — please try again');
    } finally { setLoading(false); }
  };

  const categories = [
    { k: 'bug', label: 'Bug', icon: Bug },
    { k: 'idea', label: 'Idea', icon: Lightbulb },
    { k: 'love', label: 'Love', icon: Heart },
    { k: 'other', label: 'Other', icon: MessageSquare },
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-2xl mx-auto px-6 md:px-12 py-14 md:py-20">

        <div className="mb-10">
          <p className="text-[10px] uppercase tracking-[0.22em] text-accent mb-3 font-semibold">Beta feedback</p>
          <h1 className="font-serif text-3xl md:text-4xl tracking-tight mb-3">Shape what comes next.</h1>
          <p className="text-sm text-primary/55 leading-relaxed">
            Every piece of feedback goes straight to the founding team. Be brutal — it's how the product gets sharp.
          </p>
        </div>

        {submitted ? (
          <div className="border border-accent bg-gradient-to-br from-accent/[0.08] to-transparent p-10 text-center" data-testid="beta-feedback-success">
            <Check className="w-8 h-8 text-accent mx-auto mb-4" strokeWidth={1.5} />
            <h2 className="font-serif text-2xl mb-2">Got it. Thank you.</h2>
            <p className="text-sm text-primary/55 mb-6 leading-relaxed">
              We read every message. If it's a bug we'll fix it. If it's an idea we'll weigh it. Either way — you just made Drops Curated better.
            </p>
            <div className="flex gap-3 justify-center">
              <button onClick={() => { setSubmitted(false); setMessage(''); setRating(0); }} className="text-sm text-accent underline underline-offset-4" data-testid="beta-feedback-send-another-btn">
                Send another
              </button>
              <span className="text-primary/20">·</span>
              <button onClick={() => navigate('/browse')} className="text-sm text-primary/60 hover:text-primary">
                Back to drops
              </button>
            </div>
          </div>
        ) : (
          <div className="border border-primary/10 bg-surface p-8 md:p-10 space-y-6">
            {/* Category selector */}
            <div>
              <label className="text-[10px] uppercase tracking-[0.2em] text-primary/40 mb-3 block">Type of feedback</label>
              <div className="grid grid-cols-4 gap-2">
                {categories.map(c => (
                  <button key={c.k} type="button" onClick={() => setCategory(c.k)}
                    className={`p-3 border transition-all flex flex-col items-center gap-1.5 ${
                      category === c.k ? 'border-primary bg-primary/[0.04]' : 'border-primary/10 hover:border-primary/30'
                    }`}
                    data-testid={`beta-feedback-cat-${c.k}`}
                  >
                    <c.icon className={`w-4 h-4 ${category === c.k ? 'text-primary' : 'text-primary/60'}`} strokeWidth={1.5} />
                    <span className="text-xs">{c.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Message */}
            <div>
              <label className="text-[10px] uppercase tracking-[0.2em] text-primary/40 mb-2 block">Your message</label>
              <textarea value={message} onChange={(e) => setMessage(e.target.value)}
                rows={6}
                className="w-full border border-primary/15 bg-background py-3 px-4 text-sm outline-none focus:border-primary resize-y leading-relaxed"
                placeholder={
                  category === 'bug' ? "Describe what you were doing, what you expected, and what actually happened. Screenshots help — send them to Dropscurated@gmail.com." :
                  category === 'idea' ? "What should we build next? Why does it matter?" :
                  category === 'love' ? "What part of the product did you love today?" :
                  "Tell us anything..."
                }
                data-testid="beta-feedback-message"
              />
              <p className="text-[10px] text-primary/30 mt-1 tabular-nums">{message.length}/4000</p>
            </div>

            {/* Rating — optional */}
            <div>
              <label className="text-[10px] uppercase tracking-[0.2em] text-primary/40 mb-3 block">Overall experience (optional)</label>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map(n => (
                  <button key={n} type="button" onClick={() => setRating(rating === n ? 0 : n)}
                    className={`w-10 h-10 border text-sm transition-all ${
                      rating >= n ? 'bg-accent border-accent text-primary' : 'border-primary/15 text-primary/40 hover:border-primary/40'
                    }`}
                    data-testid={`beta-feedback-rating-${n}`}
                  >
                    {n}
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-primary/30 mt-2">1 = "hated it" · 5 = "game-changer"</p>
            </div>

            {/* Optional contact */}
            <details className="group">
              <summary className="text-xs text-primary/50 cursor-pointer hover:text-primary select-none">
                Want us to follow up? Add contact (optional)
              </summary>
              <div className="mt-4 space-y-3">
                <input type="tel" maxLength={10} value={phone} onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                  className="w-full border border-primary/15 bg-background py-2.5 px-4 text-sm outline-none focus:border-primary"
                  placeholder="Phone number (optional)"
                  data-testid="beta-feedback-phone"
                />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  className="w-full border border-primary/15 bg-background py-2.5 px-4 text-sm outline-none focus:border-primary"
                  placeholder="Email (optional)"
                  data-testid="beta-feedback-email"
                />
              </div>
            </details>

            <button onClick={submit} disabled={loading || message.trim().length < 5}
              className="w-full bg-primary text-background py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40"
              data-testid="beta-feedback-submit-btn"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Send className="w-4 h-4" strokeWidth={1.5} /> Send feedback</>}
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
