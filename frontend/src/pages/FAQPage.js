import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Header, Footer } from './LandingPage';
import { ChevronDown, Bell, MessageCircle, CreditCard, Shield, Clock, HelpCircle } from 'lucide-react';

// FAQ Data organized by category
const FAQ_DATA = [
  {
    category: 'Getting Started',
    icon: HelpCircle,
    questions: [
      {
        q: 'What is Drops Curated?',
        a: 'Drops Curated is India\'s fastest streetwear alert service. We track 11,400+ products from 23 premium brands and send you instant WhatsApp alerts when new drops are released or prices change. Think of us as your personal streetwear scout — we do the watching, you do the copping.'
      },
      {
        q: 'How does it work?',
        a: 'Our system scans 23 streetwear stores every 15 minutes. When we detect a new product, price drop, or restock, we send you a WhatsApp message within 10 seconds. You set your preferences (brands, sizes, price range) and we only alert you about drops you actually care about.'
      },
      {
        q: 'What brands do you track?',
        a: 'We track premium Indian brands like Crep Dog Crew, Superkicks, Urban Monkey, Huemn, VegNonVeg, Capsul, and more. Plus international brands available in India: Nike, Jordan, Adidas, ON Running, New Balance, AMIRI, Off-White, Supreme, Palace, Fear of God, and others.'
      },
      {
        q: 'Why WhatsApp and not an app?',
        a: 'WhatsApp is where you already are. No need to download another app, enable push notifications, or check a separate feed. Alerts come straight to your chat — you see them instantly, just like messages from friends. Plus, WhatsApp works even on slow connections.'
      }
    ]
  },
  {
    category: 'Alerts & Notifications',
    icon: Bell,
    questions: [
      {
        q: 'How fast are the alerts?',
        a: 'From the moment we detect a new drop or price change to the moment it hits your WhatsApp — under 10 seconds. We\'ve tested this extensively. You\'ll know about drops before most Instagram posts go live.'
      },
      {
        q: 'Can I customize what alerts I receive?',
        a: 'Absolutely! You can filter by: brands (pick your favorites), categories (shoes, clothes, accessories), sizes (we auto-convert UK/US/EU), price range (set min/max), and alert types (new drops, price drops, restocks). Only get notified about what matters to you.'
      },
      {
        q: 'How do size-specific alerts work?',
        a: 'Tell us your shoe size (UK 9, US 10, EU 44 — we handle conversions) and your clothing sizes (S, M, L, etc.). We\'ll only alert you when products in YOUR sizes are available. No more clicking through to find your size is sold out.'
      },
      {
        q: 'How many alerts will I get per day?',
        a: 'It depends on your preferences. If you\'re tracking all brands and categories, expect 10-30 alerts on busy days. If you\'ve narrowed it down to specific brands and sizes, maybe 2-5. You\'re always in control.'
      },
      {
        q: 'Can I pause alerts temporarily?',
        a: 'Yes! Reply "PAUSE" to any alert message to pause for 24 hours, or "STOP" to pause indefinitely. Reply "RESUME" when you\'re ready to start receiving alerts again. Your preferences are saved.'
      }
    ]
  },
  {
    category: 'Subscription & Pricing',
    icon: CreditCard,
    questions: [
      {
        q: 'How much does it cost?',
        a: '₹399 per month. That\'s less than ₹14 per day for unlimited alerts across all brands. No hidden fees, no setup costs, no premium tiers. Everyone gets the same fast alerts.'
      },
      {
        q: 'Is there a free trial?',
        a: 'We don\'t offer a traditional free trial, but you can browse all 11,400+ products on our site for free. You\'ll see exactly what we track. The subscription is just for the instant WhatsApp alerts.'
      },
      {
        q: 'How do I pay?',
        a: 'We accept UPI, cards (Visa, Mastercard, Rupay), net banking, and wallets through Razorpay. Payments are secure and processed in INR. You\'ll get a receipt via email.'
      },
      {
        q: 'Can I cancel anytime?',
        a: 'Yes, cancel anytime with no questions asked. Your alerts will continue until the end of your billing period. No cancellation fees, no hoops to jump through. Just message us or click the cancel link in your account.'
      },
      {
        q: 'Do you offer refunds?',
        a: 'If you\'re not satisfied within the first 7 days, we\'ll refund you in full. After that, you can cancel anytime but refunds are prorated based on usage. We want you to be happy.'
      }
    ]
  },
  {
    category: 'Privacy & Security',
    icon: Shield,
    questions: [
      {
        q: 'Is my phone number safe?',
        a: 'Your phone number is used only for sending alerts. We never share, sell, or use it for marketing. It\'s stored securely and encrypted. You can delete your account anytime and we\'ll remove all your data.'
      },
      {
        q: 'Do you spam or sell data?',
        a: 'Never. We hate spam as much as you do. You\'ll only receive the alerts you signed up for. We don\'t sell data to third parties, period. Our business model is simple: you pay for alerts, we send alerts.'
      },
      {
        q: 'What data do you collect?',
        a: 'Just what we need: your phone number (for alerts), email (for receipts), and preferences (brands, sizes, etc.). We don\'t track your browsing, don\'t use cookies for advertising, and don\'t build profiles to sell.'
      }
    ]
  },
  {
    category: 'Technical',
    icon: Clock,
    questions: [
      {
        q: 'How often do you scan for new drops?',
        a: 'Every 15 minutes, 24/7. That\'s 96 scans per day across all 23 stores. When something changes, you know within seconds.'
      },
      {
        q: 'What if a drop sells out before I see the alert?',
        a: 'We can\'t guarantee stock — that\'s up to the stores and how fast you act. But we give you the best possible chance by alerting you faster than any other service. Many of our members have copped drops that sold out in minutes.'
      },
      {
        q: 'Do you track restocks?',
        a: 'Yes! When a previously sold-out item comes back in stock, we detect it and send an alert. Restock alerts are included in your subscription at no extra cost.'
      },
      {
        q: 'Why isn\'t [brand/store] tracked?',
        a: 'We\'re always adding new stores. If there\'s a brand you want us to track, let us know! We prioritize based on member requests. Some stores are technically difficult to track, but we\'re working on it.'
      }
    ]
  }
];

// Single FAQ Item Component
function FAQItem({ question, answer, isOpen, onClick }) {
  return (
    <div className="border-b border-primary/10 last:border-0">
      <button
        onClick={onClick}
        className="w-full py-5 flex items-start justify-between gap-4 text-left hover:text-accent transition-colors"
        data-testid={`faq-q-${question.slice(0, 20).replace(/\s/g, '-').toLowerCase()}`}
      >
        <span className="font-medium">{question}</span>
        <ChevronDown 
          className={`w-5 h-5 flex-shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} 
        />
      </button>
      <div 
        className={`overflow-hidden transition-all duration-300 ${isOpen ? 'max-h-96 pb-5' : 'max-h-0'}`}
      >
        <p className="text-primary/70 leading-relaxed">{answer}</p>
      </div>
    </div>
  );
}

// FAQ Category Section
function FAQCategory({ category, icon: Icon, questions, openItems, toggleItem }) {
  return (
    <div className="mb-12">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-accent/10 flex items-center justify-center">
          <Icon className="w-5 h-5 text-accent" />
        </div>
        <h2 className="text-xl font-serif">{category}</h2>
      </div>
      <div className="bg-surface border border-primary/5 p-6">
        {questions.map((item, idx) => (
          <FAQItem
            key={idx}
            question={item.q}
            answer={item.a}
            isOpen={openItems[`${category}-${idx}`]}
            onClick={() => toggleItem(`${category}-${idx}`)}
          />
        ))}
      </div>
    </div>
  );
}

export default function FAQPage() {
  const [openItems, setOpenItems] = useState({});
  
  const toggleItem = (key) => {
    setOpenItems(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };
  
  // Expand all in a category
  const expandAll = () => {
    const allOpen = {};
    FAQ_DATA.forEach(cat => {
      cat.questions.forEach((_, idx) => {
        allOpen[`${cat.category}-${idx}`] = true;
      });
    });
    setOpenItems(allOpen);
  };
  
  const collapseAll = () => {
    setOpenItems({});
  };

  return (
    <div className="bg-background min-h-screen" data-testid="faq-page">
      <Header />
      
      {/* Hero */}
      <section className="pt-28 pb-12 md:pt-36 md:pb-16 bg-gradient-to-b from-primary/5 to-transparent">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <span className="inline-block text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4">FAQ</span>
          <h1 className="text-4xl md:text-5xl font-serif mb-4">Frequently Asked Questions</h1>
          <p className="text-lg text-primary/60">
            Everything you need to know about Drops Curated. Can't find what you're looking for? 
            <a href="mailto:help@dropscurated.com" className="text-accent hover:underline ml-1">Contact us</a>.
          </p>
        </div>
      </section>
      
      {/* Quick Links */}
      <section className="py-8 border-b border-primary/10">
        <div className="max-w-4xl mx-auto px-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap gap-2">
              {FAQ_DATA.map((cat) => (
                <a
                  key={cat.category}
                  href={`#${cat.category.toLowerCase().replace(/\s/g, '-')}`}
                  className="px-3 py-1.5 text-xs border border-primary/10 hover:border-accent hover:text-accent transition-colors"
                >
                  {cat.category}
                </a>
              ))}
            </div>
            <div className="flex gap-2">
              <button 
                onClick={expandAll}
                className="text-xs text-primary/50 hover:text-accent transition-colors"
              >
                Expand All
              </button>
              <span className="text-primary/20">|</span>
              <button 
                onClick={collapseAll}
                className="text-xs text-primary/50 hover:text-accent transition-colors"
              >
                Collapse All
              </button>
            </div>
          </div>
        </div>
      </section>
      
      {/* FAQ Content */}
      <section className="py-12 md:py-16">
        <div className="max-w-4xl mx-auto px-6">
          {FAQ_DATA.map((cat) => (
            <div key={cat.category} id={cat.category.toLowerCase().replace(/\s/g, '-')}>
              <FAQCategory
                category={cat.category}
                icon={cat.icon}
                questions={cat.questions}
                openItems={openItems}
                toggleItem={toggleItem}
              />
            </div>
          ))}
        </div>
      </section>
      
      {/* Still Have Questions */}
      <section className="py-16 bg-surface">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl md:text-3xl font-serif mb-4">Still have questions?</h2>
          <p className="text-primary/60 mb-8">
            Can't find the answer you're looking for? Our team is here to help.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="mailto:help@dropscurated.com"
              className="inline-flex items-center justify-center gap-2 border border-primary/15 px-6 py-3 font-medium text-sm hover:border-accent hover:text-accent transition-all"
            >
              <MessageCircle className="w-4 h-4" />
              Email Support
            </a>
            <Link
              to="/subscribe"
              className="inline-flex items-center justify-center gap-2 bg-primary text-background px-6 py-3 font-medium text-sm hover:-translate-y-0.5 hover:shadow-lift transition-all"
            >
              <Bell className="w-4 h-4" />
              Get Started — ₹399/mo
            </Link>
          </div>
        </div>
      </section>
      
      <Footer />
    </div>
  );
}
