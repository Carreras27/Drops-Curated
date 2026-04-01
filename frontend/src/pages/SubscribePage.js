import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { MessageCircle, Check, ArrowRight, Shield, CreditCard, Clock, Zap, ChevronRight, Smartphone, Bell, Settings, X, Ruler, Apple, Wallet } from 'lucide-react';
import { Header, Footer } from './LandingPage';
import axios from 'axios';
import { toast } from 'sonner';

// Size Guide Modal Component
const SizeGuideModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-background border border-primary/10 max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="sticky top-0 bg-background border-b border-primary/10 p-6 flex items-center justify-between">
          <div>
            <p className="text-xs text-accent uppercase tracking-widest mb-1">Reference</p>
            <h3 className="font-serif text-xl">Size Guide</h3>
          </div>
          <button onClick={onClose} className="w-10 h-10 border border-primary/10 flex items-center justify-center hover:border-accent transition-colors" data-testid="close-size-guide">
            <X className="w-4 h-4" strokeWidth={1.5} />
          </button>
        </div>
        
        <div className="p-6 space-y-8">
          {/* Garments */}
          <div>
            <h4 className="text-sm font-medium mb-4 flex items-center gap-2">
              <span className="w-6 h-6 bg-accent/10 flex items-center justify-center text-accent text-xs">1</span>
              Garments (T-shirts, Hoodies, Jackets)
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-primary/10">
                    <th className="text-left py-2 pr-4 text-primary/40 font-medium">Size</th>
                    <th className="text-center py-2 px-4 text-primary/40 font-medium">Chest (in)</th>
                    <th className="text-center py-2 px-4 text-primary/40 font-medium">Length (in)</th>
                    <th className="text-center py-2 pl-4 text-primary/40 font-medium">Fits</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { size: 'XS', chest: '36-38', length: '26', fits: 'Extra Small' },
                    { size: 'S', chest: '38-40', length: '27', fits: 'Small' },
                    { size: 'M', chest: '40-42', length: '28', fits: 'Medium' },
                    { size: 'L', chest: '42-44', length: '29', fits: 'Large' },
                    { size: 'XL', chest: '44-46', length: '30', fits: 'Extra Large' },
                    { size: 'XXL', chest: '46-48', length: '31', fits: 'Double XL' },
                  ].map(row => (
                    <tr key={row.size} className="border-b border-primary/5">
                      <td className="py-2 pr-4 font-medium">{row.size}</td>
                      <td className="py-2 px-4 text-center text-primary/60">{row.chest}</td>
                      <td className="py-2 px-4 text-center text-primary/60">{row.length}</td>
                      <td className="py-2 pl-4 text-center text-primary/40">{row.fits}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Sneakers */}
          <div>
            <h4 className="text-sm font-medium mb-4 flex items-center gap-2">
              <span className="w-6 h-6 bg-accent/10 flex items-center justify-center text-accent text-xs">2</span>
              Sneakers (UK to EU/US Conversion)
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-primary/10">
                    <th className="text-left py-2 pr-4 text-primary/40 font-medium">UK</th>
                    <th className="text-center py-2 px-4 text-primary/40 font-medium">EU</th>
                    <th className="text-center py-2 px-4 text-primary/40 font-medium">US Men</th>
                    <th className="text-center py-2 pl-4 text-primary/40 font-medium">CM</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { uk: 'UK6', eu: '39.5', us: '7', cm: '25' },
                    { uk: 'UK7', eu: '40.5', us: '8', cm: '26' },
                    { uk: 'UK8', eu: '42', us: '9', cm: '27' },
                    { uk: 'UK9', eu: '43', us: '10', cm: '28' },
                    { uk: 'UK10', eu: '44.5', us: '11', cm: '29' },
                    { uk: 'UK11', eu: '45.5', us: '12', cm: '30' },
                    { uk: 'UK12', eu: '47', us: '13', cm: '31' },
                  ].map(row => (
                    <tr key={row.uk} className="border-b border-primary/5">
                      <td className="py-2 pr-4 font-medium">{row.uk}</td>
                      <td className="py-2 px-4 text-center text-primary/60">{row.eu}</td>
                      <td className="py-2 px-4 text-center text-primary/60">{row.us}</td>
                      <td className="py-2 pl-4 text-center text-primary/40">{row.cm}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Tips */}
          <div className="bg-primary/[0.02] border border-primary/10 p-4">
            <p className="text-xs font-medium mb-2">Pro Tips</p>
            <ul className="text-xs text-primary/50 space-y-1">
              <li>• Indian streetwear brands often run slightly smaller - consider sizing up</li>
              <li>• For oversized fits (popular in streetwear), go 1-2 sizes up</li>
              <li>• Sneaker sizes are consistent across most brands on our platform</li>
              <li>• When in doubt, check brand-specific size guides on their websites</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const ALL_BRANDS = [
  { key: 'CREPDOG_CREW', name: 'Crep Dog Crew' },
  { key: 'ALMOST_GODS', name: 'Almost Gods' },
  { key: 'CODE_BROWN', name: 'Code Brown' },
  { key: 'JAYWALKING', name: 'Jaywalking' },
  { key: 'HUEMN', name: 'Huemn' },
  { key: 'NOUGHTONE', name: 'Noughtone' },
  { key: 'BLUORNG', name: 'Bluorng' },
  { key: 'CAPSUL', name: 'Capsul' },
  { key: 'URBAN_MONKEY', name: 'Urban Monkey' },
  { key: 'HOUSE_OF_KOALA', name: 'House of Koala' },
  { key: 'FARAK', name: 'Farak' },
  { key: 'HIYEST', name: 'Hiyest' },
  { key: 'VEG_NON_VEG', name: 'Veg Non Veg' },
  { key: 'CULTURE_CIRCLE', name: 'Culture Circle' },
  { key: 'SUPERKICKS', name: 'Superkicks' },
];

const STEPS = ['verify', 'details', 'payment', 'preferences', 'success'];

export default function SubscribePage() {
  const [step, setStep] = useState('verify');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [sandboxOtp, setSandboxOtp] = useState('');
  const [membership, setMembership] = useState(null);
  const [orderId, setOrderId] = useState('');
  // Preferences
  const [selectedBrands, setSelectedBrands] = useState([]);
  const [alertTypes, setAlertTypes] = useState(['price_drop', 'new_release']);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [selectedSizes, setSelectedSizes] = useState([]);
  const [showSizeGuide, setShowSizeGuide] = useState(false);
  const [walletLoading, setWalletLoading] = useState({ apple: false, google: false });

  const sendOtp = async () => {
    if (phone.length !== 10 || !'6789'.includes(phone[0])) {
      toast.error('Enter a valid 10-digit Indian mobile number');
      return;
    }
    setLoading(true);
    try {
      const resp = await axios.post(`${API_URL}/otp/send`, { phone });
      if (resp.data.sandbox_otp) {
        setSandboxOtp(resp.data.sandbox_otp);
        setOtp(resp.data.sandbox_otp);
        toast.success(`Sandbox OTP: ${resp.data.sandbox_otp}`);
      } else {
        toast.success('OTP sent to your WhatsApp!');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async () => {
    if (otp.length !== 6) { toast.error('Enter 6-digit OTP'); return; }
    setLoading(true);
    try {
      await axios.post(`${API_URL}/otp/verify`, { phone, otp });
      toast.success('Phone verified!');
      setStep('details');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  const createOrder = async () => {
    if (!name.trim()) { toast.error('Please enter your name'); return; }
    setLoading(true);
    try {
      const resp = await axios.post(`${API_URL}/payment/create-order`, { phone, name, plan: 'monthly' });
      setOrderId(resp.data.order_id);
      if (resp.data.sandbox) {
        setStep('payment');
      } else {
        const options = {
          key: resp.data.key_id, amount: resp.data.amount, currency: resp.data.currency,
          order_id: resp.data.order_id, name: 'Drops Curated', description: 'Monthly Membership',
          handler: (r) => completePayment(r.razorpay_payment_id, r.razorpay_signature, resp.data.order_id),
          prefill: { name, contact: phone }, theme: { color: '#001F3F' },
        };
        new window.Razorpay(options).open();
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create order');
    } finally {
      setLoading(false);
    }
  };

  const completePayment = async (paymentId = 'sandbox_pay', signature = '', oid = '') => {
    setLoading(true);
    try {
      const resp = await axios.post(`${API_URL}/payment/verify`, {
        phone, order_id: oid || orderId, payment_id: paymentId, signature,
      });
      if (resp.data.success) {
        setMembership(resp.data);
        setStep('preferences');
        toast.success('Payment successful!');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Payment failed');
    } finally {
      setLoading(false);
    }
  };

  const toggleBrand = (key) => {
    setSelectedBrands(prev => prev.includes(key) ? prev.filter(b => b !== key) : [...prev, key]);
  };

  const toggleAlertType = (type) => {
    setAlertTypes(prev => {
      const next = prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type];
      return next.length > 0 ? next : prev;
    });
  };

  const toggleCategory = (cat) => {
    setSelectedCategories(prev => prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]);
  };

  const toggleSize = (size) => {
    setSelectedSizes(prev => prev.includes(size) ? prev.filter(s => s !== size) : [...prev, size]);
  };

  const savePreferences = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_URL}/preferences`, {
        phone,
        brands: selectedBrands,
        alert_types: alertTypes,
        categories: selectedCategories,
        sizes: selectedSizes,
      });
      toast.success('Preferences saved!');
      setStep('success');
    } catch {
      toast.error('Failed to save preferences');
    } finally {
      setLoading(false);
    }
  };

  const addToWallet = async (walletType) => {
    if (!membership) return;
    
    setWalletLoading(prev => ({ ...prev, [walletType]: true }));
    try {
      const resp = await axios.post(`${API_URL}/wallet/${walletType}`, {
        phone,
        name,
        membership_id: membership.membership_id,
        expires_at: membership.expires_at,
      });
      
      if (resp.data.pass_url) {
        // Download or redirect to pass
        window.open(resp.data.pass_url, '_blank');
        toast.success(`${walletType === 'apple' ? 'Apple' : 'Google'} Wallet pass ready!`);
      } else if (resp.data.message) {
        toast.info(resp.data.message);
      }
    } catch (err) {
      const message = err.response?.data?.detail || `Failed to generate ${walletType} pass`;
      toast.error(message);
    } finally {
      setWalletLoading(prev => ({ ...prev, [walletType]: false }));
    }
  };

  const stepIndex = STEPS.indexOf(step);

  return (
    <div className="bg-background min-h-screen" data-testid="subscribe-page">
      <Header />

      <main className="pt-28 pb-24">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          {/* Hero */}
          <div className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-4">Membership</p>
            <h1 className="font-serif text-4xl md:text-5xl lg:text-6xl tracking-tight mb-4" data-testid="subscribe-heading">
              Join the Inner Circle
            </h1>
            <p className="text-base md:text-lg text-primary/50 max-w-lg mx-auto">
              WhatsApp alerts within 10 seconds. Choose your brands. Never miss out.
            </p>
          </div>

          {/* Progress */}
          <div className="flex items-center justify-center gap-1.5 sm:gap-2 mb-12">
            {['Verify', 'Details', 'Pay', 'Alerts', 'Done'].map((label, i) => (
              <React.Fragment key={label}>
                <div className={`flex items-center gap-1.5 ${i <= stepIndex ? 'text-accent' : 'text-primary/20'}`}>
                  <div className={`w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center text-[10px] sm:text-xs font-medium border transition-all ${
                    i < stepIndex ? 'bg-accent text-primary border-accent' : i === stepIndex ? 'border-accent text-accent' : 'border-primary/20'
                  }`}>
                    {i < stepIndex ? <Check className="w-3 h-3" /> : i + 1}
                  </div>
                  <span className="text-[10px] sm:text-xs hidden sm:inline">{label}</span>
                </div>
                {i < 4 && <div className={`w-5 sm:w-12 h-px ${i < stepIndex ? 'bg-accent' : 'bg-primary/10'}`} />}
              </React.Fragment>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16">
            {/* Left: Form */}
            <div className="lg:col-span-7">
              {/* Step 1: Verify */}
              {step === 'verify' && (
                <div className="animate-fade-up" data-testid="step-verify">
                  <div className="w-14 h-14 border border-accent/30 flex items-center justify-center mb-6">
                    <Smartphone className="w-6 h-6 text-accent" strokeWidth={1.5} />
                  </div>
                  <h2 className="font-serif text-2xl md:text-3xl mb-2">Verify via WhatsApp</h2>
                  <p className="text-sm text-primary/40 mb-8">Verified via WhatsApp so alerts are never flagged as spam.</p>
                  <div className="space-y-4 max-w-md">
                    <div>
                      <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">WhatsApp Number</label>
                      <div className="flex">
                        <span className="flex items-center px-4 bg-primary/[0.03] border border-primary/10 border-r-0 text-sm text-primary/50 font-medium">+91</span>
                        <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))} placeholder="9876543210"
                          className="flex-1 px-4 py-3.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors" data-testid="phone-input" />
                      </div>
                    </div>
                    {!sandboxOtp ? (
                      <button onClick={sendOtp} disabled={loading || phone.length !== 10}
                        className="w-full bg-primary text-background py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40" data-testid="send-otp-btn">
                        {loading ? 'Sending...' : 'Send OTP via WhatsApp'}
                        <MessageCircle className="w-4 h-4" strokeWidth={1.5} />
                      </button>
                    ) : (
                      <>
                        <div>
                          <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">Enter OTP</label>
                          <input type="text" value={otp} onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))} placeholder="6-digit OTP"
                            className="w-full px-4 py-3.5 bg-surface border border-primary/10 text-sm text-center tracking-[0.5em] font-mono placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors" data-testid="otp-input" />
                        </div>
                        <button onClick={verifyOtp} disabled={loading || otp.length !== 6}
                          className="w-full bg-accent text-primary py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40" data-testid="verify-otp-btn">
                          {loading ? 'Verifying...' : 'Verify & Continue'}
                          <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* Step 2: Details */}
              {step === 'details' && (
                <div className="animate-fade-up" data-testid="step-details">
                  <div className="w-14 h-14 border border-accent/30 flex items-center justify-center mb-6">
                    <CreditCard className="w-6 h-6 text-accent" strokeWidth={1.5} />
                  </div>
                  <h2 className="font-serif text-2xl md:text-3xl mb-2">Your Details</h2>
                  <p className="text-sm text-primary/40 mb-8">Name for your membership card.</p>
                  <div className="space-y-4 max-w-md">
                    <div>
                      <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">Full Name</label>
                      <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name"
                        className="w-full px-4 py-3.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors" data-testid="name-input" />
                    </div>
                    <div className="bg-primary/[0.03] border border-primary/10 p-5">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium">Monthly Membership</span>
                        <span className="font-serif text-2xl">₹399</span>
                      </div>
                      <ul className="space-y-2">
                        {['Instant WhatsApp alerts (<10s)', 'Price drop notifications', 'New collection drops', 'Choose your brands', 'Digital membership card'].map((f, i) => (
                          <li key={i} className="flex items-center gap-2 text-xs text-primary/50">
                            <Check className="w-3.5 h-3.5 text-accent flex-shrink-0" strokeWidth={1.5} />{f}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <button onClick={createOrder} disabled={loading || !name.trim()}
                      className="w-full bg-primary text-background py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40" data-testid="proceed-payment-btn">
                      {loading ? 'Processing...' : 'Pay ₹399 via UPI'}
                      <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
                    </button>
                  </div>
                </div>
              )}

              {/* Step 3: Payment (Sandbox) */}
              {step === 'payment' && (
                <div className="animate-fade-up" data-testid="step-payment">
                  <div className="w-14 h-14 border border-accent/30 flex items-center justify-center mb-6">
                    <CreditCard className="w-6 h-6 text-accent" strokeWidth={1.5} />
                  </div>
                  <h2 className="font-serif text-2xl md:text-3xl mb-2">Complete Payment</h2>
                  <p className="text-sm text-primary/40 mb-8">Sandbox mode: Click to simulate payment.</p>
                  <div className="max-w-md space-y-4">
                    <div className="bg-primary/[0.03] border border-primary/10 p-6 text-center">
                      <p className="text-xs text-primary/40 uppercase tracking-widest mb-2">Amount</p>
                      <p className="font-serif text-4xl mb-1">₹399</p>
                      <p className="text-xs text-primary/30">Monthly Membership</p>
                    </div>
                    <button onClick={() => completePayment()} disabled={loading}
                      className="w-full bg-accent text-primary py-4 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40" data-testid="confirm-payment-btn">
                      {loading ? 'Processing...' : 'Confirm Payment (Sandbox)'}
                      <Check className="w-4 h-4" strokeWidth={1.5} />
                    </button>
                    <p className="text-[10px] text-primary/30 text-center flex items-center justify-center gap-1">
                      <Shield className="w-3 h-3" /> Secure payment via Razorpay UPI
                    </p>
                  </div>
                </div>
              )}

              {/* Step 4: Preferences */}
              {step === 'preferences' && (
                <div className="animate-fade-up" data-testid="step-preferences">
                  <div className="w-14 h-14 border border-accent/30 flex items-center justify-center mb-6">
                    <Settings className="w-6 h-6 text-accent" strokeWidth={1.5} />
                  </div>
                  <h2 className="font-serif text-2xl md:text-3xl mb-2">Customize Your Alerts</h2>
                  <p className="text-sm text-primary/40 mb-8">Choose which brands and alert types you care about.</p>

                  <div className="space-y-8 max-w-lg">
                    {/* Alert types */}
                    <div>
                      <p className="text-xs text-primary/40 uppercase tracking-widest mb-4">Notification Type</p>
                      <div className="space-y-3">
                        {[
                          { key: 'price_drop', label: 'Price Drops', desc: 'When prices fall on tracked products' },
                          { key: 'new_release', label: 'New Releases', desc: 'When brands drop new collections' },
                        ].map(type => (
                          <button
                            key={type.key}
                            onClick={() => toggleAlertType(type.key)}
                            className={`w-full flex items-center justify-between p-4 border transition-all text-left ${
                              alertTypes.includes(type.key) ? 'border-accent bg-accent/[0.03]' : 'border-primary/10 hover:border-primary/20'
                            }`}
                            data-testid={`alert-type-${type.key}`}
                          >
                            <div>
                              <p className="text-sm font-medium">{type.label}</p>
                              <p className="text-xs text-primary/40 mt-0.5">{type.desc}</p>
                            </div>
                            <div className={`w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 ${
                              alertTypes.includes(type.key) ? 'bg-accent border-accent' : 'border-primary/20'
                            }`}>
                              {alertTypes.includes(type.key) && <Check className="w-3 h-3 text-primary" strokeWidth={2} />}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Categories */}
                    <div>
                      <p className="text-xs text-primary/40 uppercase tracking-widest mb-4">Product Categories</p>
                      {selectedCategories.length === 0 && (
                        <p className="text-[10px] text-accent/60 mb-3">No categories selected = alerts for ALL categories</p>
                      )}
                      <div className="grid grid-cols-3 gap-2">
                        {[
                          { key: 'garments', label: 'Garments' },
                          { key: 'sneakers', label: 'Sneakers' },
                          { key: 'accessories', label: 'Accessories' },
                        ].map(cat => (
                          <button
                            key={cat.key}
                            onClick={() => toggleCategory(cat.key)}
                            className={`flex items-center justify-center gap-2 p-3 border text-xs transition-all ${
                              selectedCategories.includes(cat.key) ? 'border-accent bg-accent/[0.03] text-primary' : 'border-primary/10 text-primary/50 hover:border-primary/20'
                            }`}
                            data-testid={`pref-category-${cat.key}`}
                          >
                            <div className={`w-4 h-4 rounded-sm border flex items-center justify-center flex-shrink-0 ${
                              selectedCategories.includes(cat.key) ? 'bg-accent border-accent' : 'border-primary/20'
                            }`}>
                              {selectedCategories.includes(cat.key) && <Check className="w-2.5 h-2.5 text-primary" strokeWidth={2} />}
                            </div>
                            {cat.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Sizes */}
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <p className="text-xs text-primary/40 uppercase tracking-widest">Preferred Sizes</p>
                        <button
                          onClick={() => setShowSizeGuide(true)}
                          className="text-[10px] text-accent hover:text-primary transition-colors flex items-center gap-1"
                          data-testid="open-size-guide"
                        >
                          <Ruler className="w-3 h-3" /> Size Guide
                        </button>
                      </div>
                      {selectedSizes.length === 0 && (
                        <p className="text-[10px] text-accent/60 mb-3">No sizes selected = alerts for ALL sizes</p>
                      )}
                      <div className="grid grid-cols-5 gap-2">
                        {['XS', 'S', 'M', 'L', 'XL', 'XXL', 'UK6', 'UK7', 'UK8', 'UK9', 'UK10', 'UK11', 'UK12', 'Free Size'].map(size => (
                          <button
                            key={size}
                            onClick={() => toggleSize(size)}
                            className={`flex items-center justify-center p-2 border text-xs transition-all ${
                              selectedSizes.includes(size) ? 'border-accent bg-accent/[0.03] text-primary' : 'border-primary/10 text-primary/50 hover:border-primary/20'
                            }`}
                            data-testid={`pref-size-${size}`}
                          >
                            {size}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Brands */}
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <p className="text-xs text-primary/40 uppercase tracking-widest">Select Brands</p>
                        <button
                          onClick={() => setSelectedBrands(selectedBrands.length === ALL_BRANDS.length ? [] : ALL_BRANDS.map(b => b.key))}
                          className="text-[10px] text-accent hover:text-primary transition-colors"
                          data-testid="toggle-all-brands"
                        >
                          {selectedBrands.length === 0 ? 'All brands (default)' : selectedBrands.length === ALL_BRANDS.length ? 'Deselect all' : 'Select all'}
                        </button>
                      </div>
                      {selectedBrands.length === 0 && (
                        <p className="text-[10px] text-accent/60 mb-3">No brands selected = alerts from ALL brands</p>
                      )}
                      <div className="grid grid-cols-2 gap-2">
                        {ALL_BRANDS.map(brand => (
                          <button
                            key={brand.key}
                            onClick={() => toggleBrand(brand.key)}
                            className={`flex items-center gap-2 p-3 border text-left text-xs transition-all ${
                              selectedBrands.includes(brand.key) ? 'border-accent bg-accent/[0.03] text-primary' : 'border-primary/10 text-primary/50 hover:border-primary/20'
                            }`}
                            data-testid={`pref-brand-${brand.key}`}
                          >
                            <div className={`w-4 h-4 rounded-sm border flex items-center justify-center flex-shrink-0 ${
                              selectedBrands.includes(brand.key) ? 'bg-accent border-accent' : 'border-primary/20'
                            }`}>
                              {selectedBrands.includes(brand.key) && <Check className="w-2.5 h-2.5 text-primary" strokeWidth={2} />}
                            </div>
                            {brand.name}
                          </button>
                        ))}
                      </div>
                    </div>

                    <button onClick={savePreferences} disabled={loading}
                      className="w-full bg-primary text-background py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40" data-testid="save-preferences-btn">
                      {loading ? 'Saving...' : 'Save & Start Receiving Alerts'}
                      <Bell className="w-4 h-4" strokeWidth={1.5} />
                    </button>
                  </div>
                </div>
              )}

              {/* Step 5: Success */}
              {step === 'success' && membership && (
                <div className="animate-fade-up" data-testid="step-success">
                  <div className="max-w-md">
                    {/* Membership Card */}
                    <div className="bg-primary text-background p-8 mb-8 relative overflow-hidden" data-testid="membership-card">
                      <div className="absolute top-0 right-0 w-48 h-48 bg-accent/10 rounded-full -translate-x-1/3 -translate-y-1/2" />
                      <div className="relative">
                        <p className="text-xs uppercase tracking-[0.3em] text-accent mb-6">Drops Curated</p>
                        <p className="font-serif text-2xl mb-1">{name}</p>
                        <p className="text-xs text-background/50 mb-8">+91 {phone}</p>
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[9px] uppercase tracking-widest text-background/40 mb-1">Member ID</p>
                            <p className="text-sm font-mono tracking-wider">{membership.membership_id}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-[9px] uppercase tracking-widest text-background/40 mb-1">Valid Until</p>
                            <p className="text-sm">{new Date(membership.expires_at).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <h2 className="font-serif text-3xl mb-3">Welcome to the Club</h2>
                    <p className="text-sm text-primary/50 mb-2">Your alerts are configured and ready.</p>
                    <div className="text-xs text-primary/40 mb-6 space-y-1">
                      <p>Alerts: {alertTypes.includes('price_drop') && alertTypes.includes('new_release') ? 'Price drops + New releases' : alertTypes.includes('price_drop') ? 'Price drops only' : 'New releases only'}</p>
                      <p>Brands: {selectedBrands.length === 0 ? 'All 14 brands' : `${selectedBrands.length} brand${selectedBrands.length > 1 ? 's' : ''} selected`}</p>
                      <p>Categories: {selectedCategories.length === 0 ? 'All categories' : selectedCategories.join(', ')}</p>
                      <p>Sizes: {selectedSizes.length === 0 ? 'All sizes' : selectedSizes.join(', ')}</p>
                    </div>

                    <div className="space-y-3 mb-8">
                      <button 
                        onClick={() => addToWallet('apple')}
                        disabled={walletLoading.apple}
                        className="w-full border border-primary/10 py-3 text-sm font-medium flex items-center justify-center gap-2 hover:border-accent transition-colors disabled:opacity-50" 
                        data-testid="add-apple-wallet"
                      >
                        <Apple className="w-4 h-4" strokeWidth={1.5} />
                        {walletLoading.apple ? 'Generating...' : 'Add to Apple Wallet'}
                        <ChevronRight className="w-4 h-4" strokeWidth={1.5} />
                      </button>
                      <button 
                        onClick={() => addToWallet('google')}
                        disabled={walletLoading.google}
                        className="w-full border border-primary/10 py-3 text-sm font-medium flex items-center justify-center gap-2 hover:border-accent transition-colors disabled:opacity-50" 
                        data-testid="add-google-wallet"
                      >
                        <Wallet className="w-4 h-4" strokeWidth={1.5} />
                        {walletLoading.google ? 'Generating...' : 'Add to Google Wallet'}
                        <ChevronRight className="w-4 h-4" strokeWidth={1.5} />
                      </button>
                    </div>

                    <Link to="/browse" className="block w-full bg-primary text-background py-3.5 font-medium text-sm text-center hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300" data-testid="browse-after-subscribe">
                      Explore Drops
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Right: Value Prop */}
            <div className="lg:col-span-5">
              <div className="lg:sticky lg:top-28">
                <div className="border border-primary/10 p-8 mb-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-6">What You Get</p>
                  <div className="space-y-6">
                    {[
                      { icon: <Zap strokeWidth={1.5} />, title: '<10 Second Alerts', desc: 'Fastest drop alerts in India. Before the crowd.' },
                      { icon: <MessageCircle strokeWidth={1.5} />, title: 'WhatsApp Delivery', desc: 'No app needed. Alerts directly in WhatsApp.' },
                      { icon: <Settings strokeWidth={1.5} />, title: 'Choose Your Brands', desc: 'Only get alerts from brands you care about.' },
                      { icon: <CreditCard strokeWidth={1.5} />, title: 'Digital Membership', desc: 'Card for Apple Wallet & Google Wallet.' },
                      { icon: <Clock strokeWidth={1.5} />, title: 'Auto-Updated Every 15 Min', desc: 'Prices refreshed across all 14 brands.' },
                    ].map((f, i) => (
                      <div key={i} className="flex gap-4">
                        <div className="w-10 h-10 border border-accent/20 flex items-center justify-center flex-shrink-0 text-accent">{f.icon}</div>
                        <div>
                          <h3 className="text-sm font-medium mb-0.5">{f.title}</h3>
                          <p className="text-xs text-primary/40">{f.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="text-center py-6">
                  <p className="font-serif text-3xl mb-1">₹399<span className="text-sm text-primary/30 font-sans">/month</span></p>
                  <p className="text-xs text-primary/30">Cancel anytime. No commitments.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer />
      
      {/* Size Guide Modal */}
      <SizeGuideModal isOpen={showSizeGuide} onClose={() => setShowSizeGuide(false)} />
    </div>
  );
}
