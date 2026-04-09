import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { MessageCircle, Check, ArrowRight, Shield, CreditCard, Clock, Zap, ChevronRight, Smartphone, Bell, Settings, X, Ruler, Apple, Wallet, FlaskConical, Loader2, TrendingDown, Package, Sparkles } from 'lucide-react';
import { Header, Footer } from './LandingPage';
import axios from 'axios';
import { toast } from 'sonner';

// Test Preferences Modal Component
const TestPreferencesModal = ({ isOpen, onClose, simulationData, isLoading }) => {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-background border border-primary/10 max-w-2xl w-full max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="sticky top-0 bg-background border-b border-primary/10 p-6 flex items-center justify-between">
          <div>
            <p className="text-xs text-accent uppercase tracking-widest mb-1">Preview</p>
            <h3 className="font-serif text-xl">Test My Preferences</h3>
          </div>
          <button onClick={onClose} className="w-10 h-10 border border-primary/10 flex items-center justify-center hover:border-accent transition-colors" data-testid="close-test-modal">
            <X className="w-4 h-4" strokeWidth={1.5} />
          </button>
        </div>
        
        {isLoading ? (
          <div className="p-12 flex flex-col items-center justify-center">
            <Loader2 className="w-8 h-8 text-accent animate-spin mb-4" />
            <p className="text-sm text-primary/50">Simulating your preferences...</p>
          </div>
        ) : simulationData ? (
          <div className="p-6 space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-primary/[0.02] border border-primary/10 p-4 text-center">
                <p className="text-2xl font-serif text-primary">{simulationData.total_matching_products}</p>
                <p className="text-[10px] text-primary/40 uppercase tracking-wider mt-1">Products Match</p>
              </div>
              <div className="bg-accent/5 border border-accent/20 p-4 text-center">
                <p className="text-2xl font-serif text-accent">{simulationData.estimated_daily_alerts?.total || 0}</p>
                <p className="text-[10px] text-primary/40 uppercase tracking-wider mt-1">Est. Daily Alerts</p>
              </div>
              <div className={`p-4 text-center border ${
                simulationData.estimated_daily_alerts?.frequency_impact === 'Low' 
                  ? 'bg-green-500/5 border-green-500/20' 
                  : simulationData.estimated_daily_alerts?.frequency_impact === 'High'
                    ? 'bg-orange-500/5 border-orange-500/20'
                    : 'bg-blue-500/5 border-blue-500/20'
              }`}>
                <p className={`text-2xl font-serif ${
                  simulationData.estimated_daily_alerts?.frequency_impact === 'Low' 
                    ? 'text-green-600' 
                    : simulationData.estimated_daily_alerts?.frequency_impact === 'High'
                      ? 'text-orange-600'
                      : 'text-blue-600'
                }`}>{simulationData.estimated_daily_alerts?.frequency_impact}</p>
                <p className="text-[10px] text-primary/40 uppercase tracking-wider mt-1">Alert Volume</p>
              </div>
            </div>

            {/* Filters Applied */}
            <div className="bg-primary/[0.02] border border-primary/10 p-4">
              <p className="text-xs font-medium mb-3">Filters Applied</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div><span className="text-primary/40">Brands:</span> <span className="text-primary">{simulationData.filters_applied?.brands}</span></div>
                <div><span className="text-primary/40">Categories:</span> <span className="text-primary">{Array.isArray(simulationData.filters_applied?.categories) ? simulationData.filters_applied.categories.join(', ') || 'All' : simulationData.filters_applied?.categories}</span></div>
                <div><span className="text-primary/40">Sizes:</span> <span className="text-primary">{Array.isArray(simulationData.filters_applied?.sizes) ? simulationData.filters_applied.sizes.join(', ') || 'All' : simulationData.filters_applied?.sizes}</span></div>
                <div><span className="text-primary/40">Budget:</span> <span className="text-primary">{simulationData.filters_applied?.price_range}</span></div>
              </div>
            </div>

            {/* Alert Type Samples */}
            <div className="space-y-4">
              {/* New Drops */}
              {simulationData.new_drops?.enabled && (
                <div className="border border-primary/10 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="w-4 h-4 text-blue-500" />
                    <span className="text-sm font-medium">New Drops</span>
                    <span className="text-xs text-primary/40 ml-auto">{simulationData.new_drops.count} found</span>
                  </div>
                  {simulationData.new_drops.sample?.length > 0 ? (
                    <div className="space-y-2">
                      {simulationData.new_drops.sample.map((prod, i) => (
                        <div key={i} className="flex items-center gap-3 p-2 bg-primary/[0.02]">
                          {prod.imageUrl && (
                            <img src={prod.imageUrl} alt="" className="w-12 h-12 object-cover" />
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium truncate">{prod.name}</p>
                            <p className="text-[10px] text-primary/40">{prod.brand}</p>
                          </div>
                          <p className="text-xs font-medium">₹{prod.lowestPrice?.toLocaleString()}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-primary/40 italic">No new drops in last 7 days matching your filters</p>
                  )}
                </div>
              )}

              {/* Price Drops */}
              {simulationData.price_drops?.enabled && (
                <div className="border border-primary/10 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <TrendingDown className="w-4 h-4 text-green-500" />
                    <span className="text-sm font-medium">Price Drops ({simulationData.price_drops.threshold}%+ off)</span>
                    <span className="text-xs text-primary/40 ml-auto">{simulationData.price_drops.count} found</span>
                  </div>
                  {simulationData.price_drops.sample?.length > 0 ? (
                    <div className="space-y-2">
                      {simulationData.price_drops.sample.map((prod, i) => (
                        <div key={i} className="flex items-center gap-3 p-2 bg-green-500/5">
                          {prod.imageUrl && (
                            <img src={prod.imageUrl} alt="" className="w-12 h-12 object-cover" />
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium truncate">{prod.name}</p>
                            <p className="text-[10px] text-primary/40">{prod.brand}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs font-medium text-green-600">₹{prod.lowestPrice?.toLocaleString()}</p>
                            <p className="text-[10px] text-primary/40 line-through">₹{prod.originalPrice?.toLocaleString()}</p>
                          </div>
                          <span className="text-[10px] bg-green-500 text-white px-1.5 py-0.5">{prod.dropPercent}% OFF</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-primary/40 italic">No price drops meeting your {simulationData.price_drops.threshold}% threshold</p>
                  )}
                </div>
              )}

              {/* Restocks */}
              {simulationData.restocks?.enabled && (
                <div className="border border-primary/10 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Package className="w-4 h-4 text-purple-500" />
                    <span className="text-sm font-medium">Restock Alerts</span>
                  </div>
                  <p className="text-xs text-primary/40 italic">{simulationData.restocks.note}</p>
                </div>
              )}
            </div>

            {/* Sample Daily Digest */}
            <div className="border border-accent/20 bg-accent/5 p-4">
              <p className="text-xs font-medium mb-3 flex items-center gap-2">
                <MessageCircle className="w-4 h-4 text-accent" />
                Sample Daily Digest (8 PM)
              </p>
              <div className="bg-white border border-primary/10 p-3 text-xs font-mono whitespace-pre-wrap text-primary/70 max-h-48 overflow-y-auto">
                {simulationData.sample_daily_digest}
              </div>
            </div>

            {/* Tips */}
            <div className="bg-blue-500/5 border border-blue-500/20 p-4">
              <p className="text-xs font-medium text-blue-700 mb-2">Tips to Optimize</p>
              <ul className="text-[10px] text-blue-600/70 space-y-1">
                {simulationData.total_matching_products > 500 && (
                  <li>• Consider selecting fewer brands or adding size filters to reduce alerts</li>
                )}
                {simulationData.estimated_daily_alerts?.total > 10 && (
                  <li>• Daily Digest mode recommended for {simulationData.estimated_daily_alerts.total}+ daily alerts</li>
                )}
                {simulationData.price_drops?.count === 0 && simulationData.price_drops?.enabled && (
                  <li>• Try lowering your price drop threshold to catch more deals</li>
                )}
                {simulationData.total_matching_products < 50 && (
                  <li>• Your filters are very specific - you'll only get highly relevant alerts!</li>
                )}
              </ul>
            </div>
          </div>
        ) : (
          <div className="p-12 text-center">
            <p className="text-sm text-primary/50">No simulation data available</p>
          </div>
        )}
      </div>
    </div>
  );
};

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

// High-frequency vs Low-frequency brands (based on avg daily drops)
const ALL_BRANDS = [
  // High-frequency brands (5+ drops/day) - marked with volume indicator
  { key: 'CREPDOG_CREW', name: 'Crep Dog Crew', volume: 'high' },
  { key: 'CAPSUL', name: 'Capsul', volume: 'high' },
  { key: 'URBAN_MONKEY', name: 'Urban Monkey', volume: 'high' },
  { key: 'HUEMN', name: 'Huemn', volume: 'high' },
  { key: 'SUPERKICKS', name: 'Superkicks', volume: 'high' },
  { key: 'MAINSTREET', name: 'Mainstreet Marketplace', volume: 'high' },
  { key: 'BLUORNG', name: 'Bluorng', volume: 'medium' },
  { key: 'HOUSE_OF_KOALA', name: 'House of Koala', volume: 'medium' },
  { key: 'FARAK', name: 'Farak', volume: 'medium' },
  { key: 'EVEMEN', name: 'Evemen', volume: 'medium' },
  { key: 'VOID_WORLDWIDE', name: 'Void Worldwide', volume: 'medium' },
  // Low-frequency brands (more exclusive, fewer drops)
  { key: 'ALMOST_GODS', name: 'Almost Gods', volume: 'low' },
  { key: 'JAYWALKING', name: 'Jaywalking', volume: 'low' },
  { key: 'CODE_BROWN', name: 'Code Brown', volume: 'low' },
  { key: 'NOUGHTONE', name: 'Noughtone', volume: 'low' },
  { key: 'HIYEST', name: 'Hiyest', volume: 'low' },
  { key: 'VEG_NON_VEG', name: 'Veg Non Veg', volume: 'low' },
  { key: 'CULTURE_CIRCLE', name: 'Culture Circle', volume: 'low' },
  { key: 'TOFFLE', name: 'Toffle', volume: 'low' },
  { key: 'LEAVE_THE_REST', name: 'Leave The Rest', volume: 'low' },
  { key: 'DEADBEAR', name: 'Deadbear', volume: 'low' },
  { key: 'NATTY_GARB', name: 'Natty Garb', volume: 'low' },
  { key: 'BOMAACHI', name: 'Bomaachi', volume: 'low' },
];

// Brand selection limits
const BRAND_LIMITS = [
  { value: 5, label: 'Top 5', desc: 'Your favorite brands only' },
  { value: 10, label: 'Top 10', desc: 'Balanced coverage' },
  { value: 0, label: 'Unlimited', desc: 'All brands (more alerts)' },
];

const STEPS = ['verify', 'details', 'payment', 'preferences', 'success'];

export default function SubscribePage() {
  const [step, setStep] = useState('verify');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [address, setAddress] = useState('');
  const [dob, setDob] = useState(''); // Date of Birth for offers
  const [consentChecked, setConsentChecked] = useState(false); // WhatsApp consent
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
  
  // Advanced Preference Funnel Filters
  const [priceRange, setPriceRange] = useState({ min: '', max: '' });
  const [keywords, setKeywords] = useState([]);
  const [keywordInput, setKeywordInput] = useState('');
  const [dropThreshold, setDropThreshold] = useState(10); // Minimum % drop to alert (default 10%)
  const [alertFrequency, setAlertFrequency] = useState('daily'); // instant, daily - daily recommended
  const [brandLimit, setBrandLimit] = useState(10); // 5, 10, or 0 (unlimited)
  const [selectedGender, setSelectedGender] = useState('all'); // men, women, unisex, all

  const addKeyword = () => {
    const kw = keywordInput.trim().toLowerCase();
    if (kw && !keywords.includes(kw) && keywords.length < 10) {
      setKeywords([...keywords, kw]);
      setKeywordInput('');
    }
  };

  const removeKeyword = (kw) => {
    setKeywords(keywords.filter(k => k !== kw));
  };

  // Test My Preferences
  const [showTestModal, setShowTestModal] = useState(false);
  const [simulationData, setSimulationData] = useState(null);
  const [simulationLoading, setSimulationLoading] = useState(false);

  const testMyPreferences = async () => {
    setShowTestModal(true);
    setSimulationLoading(true);
    try {
      const resp = await axios.post(`${API_URL}/preferences/simulate`, {
        brands: selectedBrands,
        brand_limit: brandLimit,
        alert_types: alertTypes,
        gender: selectedGender,
        categories: selectedCategories,
        sizes: selectedSizes,
        price_range: {
          min: priceRange.min ? parseInt(priceRange.min) : null,
          max: priceRange.max ? parseInt(priceRange.max) : null,
        },
        keywords: keywords,
        drop_threshold: dropThreshold,
      });
      setSimulationData(resp.data);
    } catch (err) {
      toast.error('Failed to simulate preferences');
      setShowTestModal(false);
    } finally {
      setSimulationLoading(false);
    }
  };

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
    if (!name.trim()) { toast.error('Please enter your full name'); return; }
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { toast.error('Please enter a valid email address'); return; }
    if (!address.trim() || address.trim().length < 10) { toast.error('Please enter your complete home address'); return; }
    if (!dob) { toast.error('Please enter your date of birth'); return; }
    setLoading(true);
    try {
      const resp = await axios.post(`${API_URL}/payment/create-order`, { phone, name, email, address, dob, plan: 'monthly' });
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
      // Log consent with timestamp (IP is captured server-side)
      const consentTimestamp = new Date().toISOString();
      
      const resp = await axios.post(`${API_URL}/payment/verify`, {
        phone, 
        order_id: oid || orderId, 
        payment_id: paymentId, 
        signature,
        // Consent logging for Meta compliance
        consent: {
          whatsapp_opt_in: true,
          timestamp: consentTimestamp,
          agreed_to_terms: true,
        }
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
    setSelectedBrands(prev => {
      if (prev.includes(key)) {
        return prev.filter(b => b !== key);
      } else {
        // Enforce brand limit if set
        if (brandLimit > 0 && prev.length >= brandLimit) {
          toast.error(`You can select up to ${brandLimit} brands. Upgrade or remove one to add another.`);
          return prev;
        }
        return [...prev, key];
      }
    });
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
        // Brand selection
        brands: selectedBrands,
        brand_limit: brandLimit,
        // Trigger types (what alerts to receive)
        alert_types: alertTypes,
        // Specificity filters
        gender: selectedGender,
        categories: selectedCategories,
        sizes: selectedSizes,
        // Budget range filter
        price_range: {
          min: priceRange.min ? parseInt(priceRange.min) : null,
          max: priceRange.max ? parseInt(priceRange.max) : null,
        },
        // Keyword matching
        keywords: keywords,
        // Price drop threshold (only alert if discount >= threshold)
        drop_threshold: dropThreshold,
        // Notification frequency
        alert_frequency: alertFrequency,
      });
      toast.success('Preferences saved! Your alerts are now customized.');
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
                  <p className="text-sm text-primary/40 mb-8">We need your details for membership and delivery.</p>
                  <div className="space-y-4 max-w-md">
                    <div>
                      <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">Full Name <span className="text-red-500">*</span></label>
                      <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your full name"
                        className="w-full px-4 py-3.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors" data-testid="name-input" required />
                    </div>
                    <div>
                      <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">Email Address <span className="text-red-500">*</span></label>
                      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="your@email.com"
                        className="w-full px-4 py-3.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors" data-testid="email-input" required />
                    </div>
                    <div>
                      <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">WhatsApp Number</label>
                      <div className="flex">
                        <span className="flex items-center px-4 bg-primary/[0.03] border border-primary/10 border-r-0 text-sm text-primary/50 font-medium">+91</span>
                        <input type="tel" value={phone} disabled
                          className="flex-1 px-4 py-3.5 bg-primary/[0.02] border border-primary/10 text-sm text-primary/60 cursor-not-allowed" data-testid="whatsapp-display" />
                      </div>
                      <p className="text-[10px] text-primary/30 mt-1">Verified in previous step</p>
                    </div>
                    <div>
                      <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">Home Address <span className="text-red-500">*</span></label>
                      <textarea value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Full address including city, state, and PIN code"
                        rows={3}
                        className="w-full px-4 py-3.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors resize-none" data-testid="address-input" required />
                    </div>
                    <div>
                      <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">Date of Birth <span className="text-red-500">*</span></label>
                      <input type="date" value={dob} onChange={(e) => setDob(e.target.value)}
                        max={new Date().toISOString().split('T')[0]}
                        className="w-full px-4 py-3.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors" data-testid="dob-input" required />
                      <p className="text-[10px] text-accent/60 mt-1">For exclusive birthday offers & discounts</p>
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
                    <button onClick={createOrder} disabled={loading || !name.trim() || !email.trim() || !address.trim() || !dob}
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
                  <p className="text-sm text-primary/40 mb-6">Sandbox mode: Click to simulate payment.</p>
                  
                  <div className="max-w-md space-y-6">
                    <div className="bg-primary/[0.03] border border-primary/10 p-6 text-center">
                      <p className="text-xs text-primary/40 uppercase tracking-widest mb-2">Amount</p>
                      <p className="font-serif text-4xl mb-1">₹399</p>
                      <p className="text-xs text-primary/30">Monthly Membership</p>
                    </div>

                    {/* WhatsApp Consent Disclaimer */}
                    <div className="bg-blue-50 border border-blue-200 p-4 text-xs">
                      <p className="font-medium text-blue-800 mb-3">WhatsApp Subscription & Terms Agreement</p>
                      <div className="text-blue-700/80 space-y-2 mb-4">
                        <p><span className="font-medium">1. Explicit Consent:</span> You authorize Drops Curated to send automated notifications, product alerts, and marketing messages to your registered mobile number via WhatsApp.</p>
                        <p><span className="font-medium">2. Frequency & Content:</span> You understand that alerts will be sent based on your selected brand and price-drop preferences.</p>
                        <p><span className="font-medium">3. Meta Terms Compliance:</span> You acknowledge that these services are delivered via the WhatsApp platform and agree to abide by Meta's Terms of Service.</p>
                        <p><span className="font-medium">4. Opt-Out Anytime:</span> You can stop all alerts at any time by replying <span className="font-bold">"STOP"</span> or <span className="font-bold">"UNSUBSCRIBE"</span> to any of our WhatsApp messages. We process opt-out requests instantly.</p>
                        <p><span className="font-medium">5. Data Privacy:</span> Your number will only be used for the alert services you have subscribed to and will not be shared with third parties.</p>
                      </div>
                      
                      <label className="flex items-start gap-3 cursor-pointer group">
                        <div className="relative mt-0.5">
                          <input
                            type="checkbox"
                            checked={consentChecked}
                            onChange={(e) => setConsentChecked(e.target.checked)}
                            className="sr-only"
                            data-testid="consent-checkbox"
                          />
                          <div className={`w-5 h-5 border-2 rounded flex items-center justify-center transition-all ${
                            consentChecked 
                              ? 'bg-blue-600 border-blue-600' 
                              : 'border-blue-400 group-hover:border-blue-500'
                          }`}>
                            {consentChecked && <Check className="w-3 h-3 text-white" strokeWidth={3} />}
                          </div>
                        </div>
                        <span className="text-blue-800 leading-tight">
                          I have read and agree to the above terms. I consent to receive WhatsApp messages from Drops Curated.
                        </span>
                      </label>
                    </div>

                    <button 
                      onClick={() => completePayment()} 
                      disabled={loading || !consentChecked}
                      className="w-full bg-accent text-primary py-4 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed" 
                      data-testid="confirm-payment-btn"
                    >
                      {loading ? 'Processing...' : 'Confirm Payment (Sandbox)'}
                      <Check className="w-4 h-4" strokeWidth={1.5} />
                    </button>
                    
                    {!consentChecked && (
                      <p className="text-[10px] text-red-500 text-center">Please agree to the WhatsApp terms above to proceed</p>
                    )}
                    
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
                  <h2 className="font-serif text-2xl md:text-3xl mb-2">Preference Funnel</h2>
                  <p className="text-sm text-primary/40 mb-8">Fine-tune your alerts to only get what you care about. This saves costs and noise.</p>

                  <div className="space-y-10 max-w-lg">
                    
                    {/* Section A: Brand Selection */}
                    <div className="border-b border-primary/10 pb-8">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="w-6 h-6 bg-accent/10 text-accent text-xs font-bold flex items-center justify-center">A</span>
                        <p className="text-sm font-medium">Brand Selection (Your "Follow" List)</p>
                      </div>
                      
                      {/* Brand Limit Selector */}
                      <div className="mb-4">
                        <p className="text-xs text-primary/40 mb-3">How many brands do you want alerts from?</p>
                        <div className="grid grid-cols-3 gap-2">
                          {BRAND_LIMITS.map(limit => (
                            <button
                              key={limit.value}
                              onClick={() => {
                                setBrandLimit(limit.value);
                                // If reducing limit and too many selected, trim selection
                                if (limit.value > 0 && selectedBrands.length > limit.value) {
                                  setSelectedBrands(prev => prev.slice(0, limit.value));
                                  toast.info(`Selection trimmed to ${limit.value} brands`);
                                }
                              }}
                              className={`flex flex-col items-center p-3 border text-center transition-all ${
                                brandLimit === limit.value 
                                  ? 'border-accent bg-accent/[0.03]' 
                                  : 'border-primary/10 hover:border-primary/20'
                              }`}
                              data-testid={`brand-limit-${limit.value}`}
                            >
                              <p className={`text-sm font-medium ${brandLimit === limit.value ? 'text-primary' : 'text-primary/50'}`}>
                                {limit.label}
                              </p>
                              <p className="text-[9px] text-primary/30 mt-0.5">{limit.desc}</p>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Brand Selection Grid */}
                      <div className="flex items-center justify-between mb-3">
                        <p className="text-xs text-primary/40">
                          {selectedBrands.length > 0 
                            ? `${selectedBrands.length}${brandLimit > 0 ? `/${brandLimit}` : ''} brands selected`
                            : 'Select your favorite brands'
                          }
                        </p>
                        {brandLimit === 0 && (
                          <button
                            onClick={() => setSelectedBrands(selectedBrands.length === ALL_BRANDS.length ? [] : ALL_BRANDS.map(b => b.key))}
                            className="text-[10px] text-accent hover:text-primary transition-colors"
                            data-testid="toggle-all-brands"
                          >
                            {selectedBrands.length === ALL_BRANDS.length ? 'Deselect all' : 'Select all'}
                          </button>
                        )}
                      </div>
                      
                      {/* Show hint for low-volume brands */}
                      <div className="bg-green-500/5 border border-green-500/20 p-3 mb-4 text-xs">
                        <span className="text-green-600 font-medium">Pro Tip:</span>
                        <span className="text-green-700/70 ml-1">Low-volume brands (marked in green) drop less frequently = fewer alerts but more exclusive items.</span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto">
                        {ALL_BRANDS.map(brand => (
                          <button
                            key={brand.key}
                            onClick={() => toggleBrand(brand.key)}
                            className={`flex items-center gap-2 p-3 border text-left text-xs transition-all ${
                              selectedBrands.includes(brand.key) 
                                ? 'border-accent bg-accent/[0.03] text-primary' 
                                : 'border-primary/10 text-primary/50 hover:border-primary/20'
                            }`}
                            data-testid={`pref-brand-${brand.key}`}
                            disabled={brandLimit > 0 && !selectedBrands.includes(brand.key) && selectedBrands.length >= brandLimit}
                          >
                            <div className={`w-4 h-4 rounded-sm border flex items-center justify-center flex-shrink-0 ${
                              selectedBrands.includes(brand.key) ? 'bg-accent border-accent' : 'border-primary/20'
                            }`}>
                              {selectedBrands.includes(brand.key) && <Check className="w-2.5 h-2.5 text-primary" strokeWidth={2} />}
                            </div>
                            <span className="flex-1">{brand.name}</span>
                            <span className={`text-[9px] px-1.5 py-0.5 rounded ${
                              brand.volume === 'low' 
                                ? 'bg-green-500/10 text-green-600' 
                                : brand.volume === 'high' 
                                  ? 'bg-orange-500/10 text-orange-600'
                                  : 'bg-primary/5 text-primary/40'
                            }`}>
                              {brand.volume === 'low' ? 'Exclusive' : brand.volume === 'high' ? 'High Vol' : 'Med'}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Section B: Trigger-Based Filtering */}
                    <div className="border-b border-primary/10 pb-8">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="w-6 h-6 bg-accent/10 text-accent text-xs font-bold flex items-center justify-center">B</span>
                        <p className="text-sm font-medium">Trigger-Based Filtering</p>
                      </div>
                      <p className="text-xs text-primary/40 mb-4">Instead of "all updates," pick specific triggers:</p>
                      
                      <div className="space-y-3">
                        {[
                          { key: 'new_release', label: 'New Drops Only', desc: 'When a brand launches a new collection', icon: '🆕' },
                          { key: 'price_drop', label: 'Price Drops Only', desc: 'Only alert if a product price decreases (highly valuable for buyers)', icon: '💰' },
                          { key: 'restock', label: 'Restock Alerts', desc: 'When "Sold Out" items come back in stock', icon: '📦' },
                        ].map(type => (
                          <button
                            key={type.key}
                            onClick={() => toggleAlertType(type.key)}
                            className={`w-full flex items-center justify-between p-4 border transition-all text-left ${
                              alertTypes.includes(type.key) ? 'border-accent bg-accent/[0.03]' : 'border-primary/10 hover:border-primary/20'
                            }`}
                            data-testid={`alert-type-${type.key}`}
                          >
                            <div className="flex items-center gap-3">
                              <span className="text-lg">{type.icon}</span>
                              <div>
                                <p className="text-sm font-medium">{type.label}</p>
                                <p className="text-xs text-primary/40 mt-0.5">{type.desc}</p>
                              </div>
                            </div>
                            <div className={`w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 ${
                              alertTypes.includes(type.key) ? 'bg-accent border-accent' : 'border-primary/20'
                            }`}>
                              {alertTypes.includes(type.key) && <Check className="w-3 h-3 text-primary" strokeWidth={2} />}
                            </div>
                          </button>
                        ))}
                      </div>
                      
                      {/* Price Drop Threshold - Only show if price_drop is selected */}
                      {alertTypes.includes('price_drop') && (
                        <div className="mt-4 p-4 bg-primary/[0.02] border border-primary/10">
                          <p className="text-xs text-primary/60 mb-3">Alert me only when price drops by at least:</p>
                          <div className="flex gap-2">
                            {[5, 10, 15, 20, 30].map(threshold => (
                              <button
                                key={threshold}
                                onClick={() => setDropThreshold(threshold)}
                                className={`flex-1 py-2 border text-xs transition-all ${
                                  dropThreshold === threshold 
                                    ? 'border-accent bg-accent/[0.03] text-primary font-medium' 
                                    : 'border-primary/10 text-primary/50 hover:border-primary/20'
                                }`}
                                data-testid={`threshold-${threshold}`}
                              >
                                {threshold}%+
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Section C: Specificity (Size & Category) */}
                    <div className="border-b border-primary/10 pb-8">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="w-6 h-6 bg-accent/10 text-accent text-xs font-bold flex items-center justify-center">C</span>
                        <p className="text-sm font-medium">Specificity (Best Cost Saver)</p>
                      </div>
                      <p className="text-xs text-primary/40 mb-4">Only get alerts for your gender, size and category.</p>
                      
                      {/* Gender Filter */}
                      <div className="mb-6">
                        <p className="text-xs text-primary/60 mb-3">Gender Collection</p>
                        <div className="grid grid-cols-4 gap-2">
                          {[
                            { key: 'all', label: 'All', desc: 'Everything' },
                            { key: 'men', label: 'Men', desc: "Men's collection" },
                            { key: 'women', label: 'Women', desc: "Women's collection" },
                            { key: 'unisex', label: 'Unisex', desc: 'Gender neutral' },
                          ].map(gender => (
                            <button
                              key={gender.key}
                              onClick={() => setSelectedGender(gender.key)}
                              className={`flex flex-col items-center p-3 border text-center transition-all ${
                                selectedGender === gender.key ? 'border-accent bg-accent/[0.03] text-primary' : 'border-primary/10 text-primary/50 hover:border-primary/20'
                              }`}
                              data-testid={`pref-gender-${gender.key}`}
                            >
                              <div className={`w-4 h-4 rounded-full border flex items-center justify-center mb-1 ${
                                selectedGender === gender.key ? 'bg-accent border-accent' : 'border-primary/20'
                              }`}>
                                {selectedGender === gender.key && <div className="w-2 h-2 bg-primary rounded-full" />}
                              </div>
                              <span className="text-xs font-medium">{gender.label}</span>
                              <span className="text-[9px] text-primary/30 mt-0.5 hidden sm:block">{gender.desc}</span>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Categories */}
                      <div className="mb-6">
                        <p className="text-xs text-primary/60 mb-3">Category Filter</p>
                        {selectedCategories.length === 0 && (
                          <p className="text-[10px] text-accent/60 mb-2">No selection = alerts for ALL categories</p>
                        )}
                        <div className="grid grid-cols-3 gap-2">
                          {[
                            { key: 'garments', label: 'Garments', desc: 'T-shirts, Hoodies, Jackets' },
                            { key: 'sneakers', label: 'Sneakers', desc: 'Shoes, Slides' },
                            { key: 'accessories', label: 'Accessories', desc: 'Caps, Bags, etc.' },
                          ].map(cat => (
                            <button
                              key={cat.key}
                              onClick={() => toggleCategory(cat.key)}
                              className={`flex flex-col items-center p-3 border text-center transition-all ${
                                selectedCategories.includes(cat.key) ? 'border-accent bg-accent/[0.03] text-primary' : 'border-primary/10 text-primary/50 hover:border-primary/20'
                              }`}
                              data-testid={`pref-category-${cat.key}`}
                            >
                              <div className={`w-4 h-4 rounded-sm border flex items-center justify-center mb-1 ${
                                selectedCategories.includes(cat.key) ? 'bg-accent border-accent' : 'border-primary/20'
                              }`}>
                                {selectedCategories.includes(cat.key) && <Check className="w-2.5 h-2.5 text-primary" strokeWidth={2} />}
                              </div>
                              <span className="text-xs font-medium">{cat.label}</span>
                              <span className="text-[9px] text-primary/30 mt-0.5">{cat.desc}</span>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Sizes - "My Size" Filter */}
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <p className="text-xs text-primary/60">The "My Size" Filter</p>
                            <p className="text-[10px] text-primary/30 mt-0.5">Only send alert if product drops in YOUR size</p>
                          </div>
                          <button
                            onClick={() => setShowSizeGuide(true)}
                            className="text-[10px] text-accent hover:text-primary transition-colors flex items-center gap-1"
                            data-testid="open-size-guide"
                          >
                            <Ruler className="w-3 h-3" /> Size Guide
                          </button>
                        </div>
                        {selectedSizes.length === 0 && (
                          <p className="text-[10px] text-accent/60 mb-3">No selection = alerts for ALL sizes</p>
                        )}
                        
                        {/* Garments Sizes */}
                        <div className="mb-4">
                          <p className="text-[10px] text-primary/40 uppercase tracking-wider mb-2 font-medium">Garments</p>
                          <div className="grid grid-cols-6 gap-2">
                            {['XS', 'S', 'M', 'L', 'XL', 'XXL'].map(size => (
                              <button
                                key={size}
                                onClick={() => toggleSize(size)}
                                className={`flex items-center justify-center p-2 border text-xs transition-all ${
                                  selectedSizes.includes(size) ? 'border-accent bg-accent/[0.03] text-primary font-medium' : 'border-primary/10 text-primary/50 hover:border-primary/20'
                                }`}
                                data-testid={`pref-size-${size}`}
                              >
                                {size}
                              </button>
                            ))}
                          </div>
                        </div>

                        {/* Shoes Sizes */}
                        <div className="mb-4">
                          <p className="text-[10px] text-primary/40 uppercase tracking-wider mb-2 font-medium">Shoes</p>
                          <div className="grid grid-cols-5 gap-2">
                            {['UK6', 'UK7', 'UK8', 'UK9', 'UK10', 'UK11', 'UK12'].map(size => (
                              <button
                                key={size}
                                onClick={() => toggleSize(size)}
                                className={`flex items-center justify-center p-2 border text-xs transition-all ${
                                  selectedSizes.includes(size) ? 'border-accent bg-accent/[0.03] text-primary font-medium' : 'border-primary/10 text-primary/50 hover:border-primary/20'
                                }`}
                                data-testid={`pref-size-${size}`}
                              >
                                {size}
                              </button>
                            ))}
                          </div>
                        </div>

                        {/* Accessories */}
                        <div>
                          <p className="text-[10px] text-primary/40 uppercase tracking-wider mb-2 font-medium">Accessories</p>
                          <div className="grid grid-cols-3 gap-2">
                            <button
                              onClick={() => toggleSize('Free Size')}
                              className={`flex items-center justify-center p-2 border text-xs transition-all ${
                                selectedSizes.includes('Free Size') ? 'border-accent bg-accent/[0.03] text-primary font-medium' : 'border-primary/10 text-primary/50 hover:border-primary/20'
                              }`}
                              data-testid="pref-size-Free Size"
                            >
                              Free Size
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Section D: Notification Frequency (Noise Control) */}
                    <div className="border-b border-primary/10 pb-8">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="w-6 h-6 bg-accent/10 text-accent text-xs font-bold flex items-center justify-center">D</span>
                        <p className="text-sm font-medium">Notification Frequency (Noise Control)</p>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3">
                        <button
                          onClick={() => setAlertFrequency('instant')}
                          className={`flex flex-col p-4 border transition-all text-left ${
                            alertFrequency === 'instant' 
                              ? 'border-accent bg-accent/[0.03]' 
                              : 'border-primary/10 hover:border-primary/20'
                          }`}
                          data-testid="freq-instant"
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <Zap className="w-4 h-4 text-orange-500" />
                            <span className={`text-sm font-medium ${alertFrequency === 'instant' ? 'text-primary' : 'text-primary/50'}`}>
                              Instant
                            </span>
                          </div>
                          <p className="text-[10px] text-primary/40">Real-time alerts within 10 seconds</p>
                          <p className="text-[9px] text-orange-500/70 mt-1">Best for limited "hype" items</p>
                        </button>
                        
                        <button
                          onClick={() => setAlertFrequency('daily')}
                          className={`flex flex-col p-4 border transition-all text-left relative ${
                            alertFrequency === 'daily' 
                              ? 'border-accent bg-accent/[0.03]' 
                              : 'border-primary/10 hover:border-primary/20'
                          }`}
                          data-testid="freq-daily"
                        >
                          <span className="absolute -top-2 -right-2 bg-green-500 text-white text-[8px] px-2 py-0.5 font-medium">
                            RECOMMENDED
                          </span>
                          <div className="flex items-center gap-2 mb-2">
                            <Clock className="w-4 h-4 text-green-500" />
                            <span className={`text-sm font-medium ${alertFrequency === 'daily' ? 'text-primary' : 'text-primary/50'}`}>
                              Daily Digest
                            </span>
                          </div>
                          <p className="text-[10px] text-primary/40">Single message at 8:00 PM</p>
                          <p className="text-[9px] text-green-600/70 mt-1">"Today: 15 new arrivals, 4 price drops"</p>
                        </button>
                      </div>
                    </div>

                    {/* Budget Range (Optional) */}
                    <div className="border-b border-primary/10 pb-8">
                      <p className="text-xs text-primary/40 uppercase tracking-widest mb-4">Budget Range (Optional)</p>
                      <p className="text-[10px] text-accent/60 mb-3">Only get alerts for products in your budget</p>
                      <div className="flex gap-3">
                        <div className="flex-1">
                          <label className="text-[10px] text-primary/30 mb-1 block">Min Price</label>
                          <input
                            type="number"
                            value={priceRange.min}
                            onChange={(e) => setPriceRange({ ...priceRange, min: e.target.value })}
                            placeholder="₹0"
                            className="w-full px-3 py-2.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors"
                            data-testid="price-min"
                          />
                        </div>
                        <div className="flex items-end pb-2.5 text-primary/30">—</div>
                        <div className="flex-1">
                          <label className="text-[10px] text-primary/30 mb-1 block">Max Price</label>
                          <input
                            type="number"
                            value={priceRange.max}
                            onChange={(e) => setPriceRange({ ...priceRange, max: e.target.value })}
                            placeholder="No limit"
                            className="w-full px-3 py-2.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors"
                            data-testid="price-max"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Keywords Filter (Optional) */}
                    <div className="border-b border-primary/10 pb-8">
                      <p className="text-xs text-primary/40 uppercase tracking-widest mb-4">Product Keywords (Optional)</p>
                      <p className="text-[10px] text-accent/60 mb-3">Get alerts only for products matching keywords (e.g., Jordan, Yeezy, Dunk, Oversized)</p>
                      <div className="flex gap-2 mb-3">
                        <input
                          type="text"
                          value={keywordInput}
                          onChange={(e) => setKeywordInput(e.target.value)}
                          onKeyPress={(e) => e.key === 'Enter' && addKeyword()}
                          placeholder="Add keyword..."
                          className="flex-1 px-3 py-2.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors"
                          data-testid="keyword-input"
                        />
                        <button
                          onClick={addKeyword}
                          className="px-4 bg-primary/10 text-primary text-sm hover:bg-primary/20 transition-colors"
                          data-testid="add-keyword-btn"
                        >
                          Add
                        </button>
                      </div>
                      {keywords.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {keywords.map(kw => (
                            <span
                              key={kw}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-accent/10 text-xs"
                            >
                              {kw}
                              <button onClick={() => removeKeyword(kw)} className="hover:text-red-500">
                                <X className="w-3 h-3" />
                              </button>
                            </span>
                          ))}
                        </div>
                      )}
                      {keywords.length === 0 && (
                        <p className="text-[10px] text-primary/30">No keywords = alerts for ALL products matching other filters</p>
                      )}
                    </div>

                    {/* Cost Savings Summary */}
                    <div className="bg-green-500/5 border border-green-500/20 p-4">
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 bg-green-500/10 rounded-full flex items-center justify-center flex-shrink-0">
                          <Check className="w-5 h-5 text-green-600" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-green-700">Your Preference Funnel</p>
                          <div className="text-xs text-green-600/70 mt-2 space-y-1">
                            <p>• Brands: {selectedBrands.length > 0 ? `${selectedBrands.length} selected` : 'All brands'} {brandLimit > 0 ? `(max ${brandLimit})` : ''}</p>
                            <p>• Triggers: {alertTypes.length > 0 ? alertTypes.map(t => t.replace('_', ' ')).join(', ') : 'None'}</p>
                            <p>• Gender: {selectedGender === 'all' ? 'All collections' : selectedGender.charAt(0).toUpperCase() + selectedGender.slice(1)}</p>
                            <p>• Categories: {selectedCategories.length > 0 ? selectedCategories.join(', ') : 'All'}</p>
                            <p>• Sizes: {selectedSizes.length > 0 ? selectedSizes.join(', ') : 'All'}</p>
                            <p>• Frequency: {alertFrequency === 'daily' ? 'Daily Digest (8 PM)' : 'Instant'}</p>
                            {priceRange.min || priceRange.max ? <p>• Budget: ₹{priceRange.min || '0'} - ₹{priceRange.max || '∞'}</p> : null}
                          </div>
                          <p className="text-xs text-green-600 font-medium mt-3">
                            Estimated alert reduction: ~{Math.min(95, 
                              (selectedBrands.length > 0 ? 25 : 0) + 
                              (selectedGender !== 'all' ? 15 : 0) +
                              (selectedCategories.length > 0 ? 20 : 0) + 
                              (selectedSizes.length > 0 ? 20 : 0) +
                              (keywords.length > 0 ? 15 : 0) +
                              (priceRange.min || priceRange.max ? 10 : 0) +
                              (alertFrequency === 'daily' ? 5 : 0)
                            )}%
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Test My Preferences Button */}
                    <button 
                      onClick={testMyPreferences}
                      disabled={alertTypes.length === 0}
                      className="w-full border-2 border-accent text-accent py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:bg-accent/5 transition-all duration-300 mb-4 disabled:opacity-40"
                      data-testid="test-preferences-btn"
                    >
                      <FlaskConical className="w-4 h-4" strokeWidth={1.5} />
                      Test My Preferences
                    </button>

                    <button onClick={savePreferences} disabled={loading || alertTypes.length === 0}
                      className="w-full bg-primary text-background py-4 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40" data-testid="save-preferences-btn">
                      {loading ? 'Saving...' : 'Save Preferences & Start Receiving Alerts'}
                      <Bell className="w-4 h-4" strokeWidth={1.5} />
                    </button>
                    
                    {alertTypes.length === 0 && (
                      <p className="text-xs text-red-500 text-center">Please select at least one trigger type</p>
                    )}
                  </div>
                </div>
              )}

              {/* Step 5: Success */}
              {step === 'success' && membership && (
                <div className="animate-fade-up" data-testid="step-success">
                  <div className="max-w-md">
                    {/* Personalized Header */}
                    <div className="mb-8">
                      <p className="text-xs text-accent uppercase tracking-widest mb-2">{name.split(' ')[0]}'s Drops Curated</p>
                      <h2 className="font-serif text-3xl md:text-4xl mb-3">Welcome, {name.split(' ')[0]}!</h2>
                      <p className="text-sm text-primary/50">You're now part of India's most exclusive streetwear community.</p>
                    </div>

                    {/* Membership Card */}
                    <div className="bg-primary text-background p-8 mb-8 relative overflow-hidden" data-testid="membership-card">
                      <div className="absolute top-0 right-0 w-48 h-48 bg-accent/10 rounded-full -translate-x-1/3 -translate-y-1/2" />
                      <div className="relative">
                        <p className="text-xs uppercase tracking-[0.3em] text-accent mb-6">VIP Member</p>
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

                    <div className="bg-accent/10 border border-accent/20 p-4 mb-6">
                      <p className="text-sm font-medium text-primary mb-2">Your Alert Preferences</p>
                      <div className="text-xs text-primary/60 space-y-1">
                        <p>• Alerts: {alertTypes.map(t => t === 'price_drop' ? 'Price Drops' : t === 'new_release' ? 'New Releases' : 'Restocks').join(', ') || 'None'}</p>
                        <p>• Brands: {selectedBrands.length === 0 ? 'All 23 brands' : `${selectedBrands.length} brand${selectedBrands.length > 1 ? 's' : ''} selected`}</p>
                        <p>• Gender: {selectedGender === 'all' ? 'All collections' : selectedGender.charAt(0).toUpperCase() + selectedGender.slice(1)}</p>
                        <p>• Categories: {selectedCategories.length === 0 ? 'All categories' : selectedCategories.join(', ')}</p>
                        <p>• Sizes: {selectedSizes.length === 0 ? 'All sizes' : selectedSizes.join(', ')}</p>
                        <p>• Frequency: {alertFrequency === 'daily' ? 'Daily Digest at 8 PM' : 'Instant alerts'}</p>
                      </div>
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
      
      {/* Test Preferences Modal */}
      <TestPreferencesModal 
        isOpen={showTestModal} 
        onClose={() => setShowTestModal(false)} 
        simulationData={simulationData}
        isLoading={simulationLoading}
      />
    </div>
  );
}
