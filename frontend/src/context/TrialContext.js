import React, { createContext, useContext, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Lock, X, Sparkles } from 'lucide-react';

const TRIAL_KEY = 'drops_curated_trial_start';
const TRIAL_DAYS = 7;

// Trial Context
const TrialContext = createContext(null);

export const useTrial = () => {
  const context = useContext(TrialContext);
  if (!context) {
    throw new Error('useTrial must be used within a TrialProvider');
  }
  return context;
};

export const TrialProvider = ({ children }) => {
  const [trialStart, setTrialStart] = useState(null);
  const [isTrialActive, setIsTrialActive] = useState(true);
  const [daysRemaining, setDaysRemaining] = useState(TRIAL_DAYS);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  useEffect(() => {
    // Check for existing trial
    const stored = localStorage.getItem(TRIAL_KEY);
    
    if (stored) {
      const startDate = new Date(stored);
      setTrialStart(startDate);
      
      const now = new Date();
      const diffTime = now - startDate;
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
      const remaining = TRIAL_DAYS - diffDays;
      
      setDaysRemaining(Math.max(0, remaining));
      setIsTrialActive(remaining > 0);
    } else {
      // No trial started yet
      setTrialStart(null);
      setIsTrialActive(false);
      setDaysRemaining(0);
    }
  }, []);

  const startTrial = () => {
    const now = new Date().toISOString();
    localStorage.setItem(TRIAL_KEY, now);
    setTrialStart(new Date(now));
    setIsTrialActive(true);
    setDaysRemaining(TRIAL_DAYS);
  };

  const hasStartedTrial = () => {
    return localStorage.getItem(TRIAL_KEY) !== null;
  };

  const requiresUpgrade = () => {
    // If no trial started, they need to start trial first
    if (!hasStartedTrial()) return false;
    // If trial expired, they need to upgrade
    return !isTrialActive;
  };

  const checkFeatureAccess = (featureName) => {
    if (!hasStartedTrial()) {
      // Show start trial prompt
      return { allowed: false, reason: 'start_trial' };
    }
    if (!isTrialActive) {
      // Show upgrade prompt
      return { allowed: false, reason: 'trial_expired' };
    }
    return { allowed: true };
  };

  return (
    <TrialContext.Provider value={{
      trialStart,
      isTrialActive,
      daysRemaining,
      startTrial,
      hasStartedTrial,
      requiresUpgrade,
      checkFeatureAccess,
      showUpgradeModal,
      setShowUpgradeModal,
    }}>
      {children}
      {showUpgradeModal && <UpgradeModal onClose={() => setShowUpgradeModal(false)} />}
    </TrialContext.Provider>
  );
};

// Upgrade Modal Component
const UpgradeModal = ({ onClose }) => {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-background border border-primary/10 max-w-md w-full p-8 relative animate-fade-up shadow-lift">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-primary/40 hover:text-primary transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
        
        <div className="text-center">
          <div className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center mx-auto mb-6">
            <Lock className="w-8 h-8 text-accent" />
          </div>
          
          <h3 className="font-serif text-2xl mb-3">Your Trial Has Ended</h3>
          <p className="text-primary/60 text-sm mb-6 leading-relaxed">
            Upgrade to Premium to unlock all features including real-time price alerts, 
            advanced filters, wishlist tracking, and instant WhatsApp notifications.
          </p>
          
          <div className="bg-primary/[0.03] border border-primary/10 p-4 mb-6">
            <p className="text-xs text-primary/50 uppercase tracking-wider mb-2">Premium Membership</p>
            <p className="font-serif text-3xl">₹399<span className="text-sm font-sans text-primary/50">/month</span></p>
          </div>
          
          <Link
            to="/subscribe"
            onClick={onClose}
            className="w-full inline-flex items-center justify-center gap-2 bg-primary text-background py-4 font-medium text-sm hover:bg-primary/90 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            Upgrade Now
          </Link>
          
          <p className="text-xs text-primary/40 mt-4">
            Cancel anytime. No questions asked.
          </p>
        </div>
      </div>
    </div>
  );
};

// Trial Banner Component (shows days remaining)
export const TrialBanner = () => {
  const { isTrialActive, daysRemaining, hasStartedTrial } = useTrial();
  
  if (!hasStartedTrial() || !isTrialActive) return null;
  
  return (
    <div className="bg-accent/10 border-b border-accent/20 py-2 px-4 text-center">
      <p className="text-xs text-primary">
        <span className="font-semibold text-accent">{daysRemaining} day{daysRemaining !== 1 ? 's' : ''}</span>
        {' '}remaining in your free trial
        <Link to="/subscribe" className="ml-2 underline hover:text-accent transition-colors">
          Upgrade now
        </Link>
      </p>
    </div>
  );
};

// Locked Feature Overlay
export const LockedOverlay = ({ feature = "feature", onUpgrade }) => {
  const { hasStartedTrial, setShowUpgradeModal } = useTrial();
  
  const handleClick = () => {
    if (onUpgrade) {
      onUpgrade();
    } else {
      setShowUpgradeModal(true);
    }
  };
  
  return (
    <div 
      className="absolute inset-0 bg-background/80 backdrop-blur-[2px] z-10 flex items-center justify-center cursor-pointer group"
      onClick={handleClick}
    >
      <div className="text-center p-4">
        <Lock className="w-6 h-6 text-primary/40 mx-auto mb-2 group-hover:text-accent transition-colors" />
        <p className="text-xs text-primary/60 group-hover:text-primary transition-colors">
          {hasStartedTrial() ? 'Upgrade to unlock' : 'Start trial to unlock'}
        </p>
      </div>
    </div>
  );
};

// Blurred Price Component
export const BlurredPrice = ({ price, originalPrice, className = "" }) => {
  const { isTrialActive, hasStartedTrial, setShowUpgradeModal } = useTrial();
  
  const showBlur = hasStartedTrial() && !isTrialActive;
  
  if (!showBlur) {
    return (
      <div className={className}>
        <span className="font-semibold">₹{price?.toLocaleString()}</span>
        {originalPrice && originalPrice > price && (
          <span className="text-primary/40 line-through ml-2 text-sm">
            ₹{originalPrice?.toLocaleString()}
          </span>
        )}
      </div>
    );
  }
  
  return (
    <div 
      className={`${className} relative cursor-pointer group`}
      onClick={() => setShowUpgradeModal(true)}
    >
      <span className="font-semibold blur-md select-none">₹{price?.toLocaleString()}</span>
      {originalPrice && originalPrice > price && (
        <span className="text-primary/40 line-through ml-2 text-sm blur-md select-none">
          ₹{originalPrice?.toLocaleString()}
        </span>
      )}
      <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
        <span className="text-xs text-accent flex items-center gap-1">
          <Lock className="w-3 h-3" /> View price
        </span>
      </div>
    </div>
  );
};

// Start Trial Button
export const StartTrialButton = ({ className = "", children }) => {
  const { startTrial, hasStartedTrial, isTrialActive } = useTrial();
  
  if (hasStartedTrial() && isTrialActive) {
    return (
      <Link
        to="/browse"
        className={`inline-flex items-center justify-center gap-2 bg-primary text-background px-8 py-4 font-medium text-sm hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 ${className}`}
      >
        {children || 'Continue Browsing'}
      </Link>
    );
  }
  
  if (hasStartedTrial() && !isTrialActive) {
    return (
      <Link
        to="/subscribe"
        className={`inline-flex items-center justify-center gap-2 bg-accent text-primary px-8 py-4 font-medium text-sm hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 ${className}`}
      >
        <Sparkles className="w-4 h-4" />
        {children || 'Upgrade to Premium'}
      </Link>
    );
  }
  
  return (
    <button
      onClick={startTrial}
      className={`inline-flex items-center justify-center gap-2 bg-primary text-background px-8 py-4 font-medium text-sm hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 ${className}`}
    >
      <Sparkles className="w-4 h-4" />
      {children || 'Try Free for 7 Days'}
    </button>
  );
};

export default TrialProvider;
