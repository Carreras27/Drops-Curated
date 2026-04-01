import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { MessageCircle, Check, ArrowRight, Shield, CreditCard, Clock, Zap, ChevronRight, Smartphone } from 'lucide-react';
import { Header, Footer } from './LandingPage';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const STEPS = ['verify', 'details', 'payment', 'success'];

export default function SubscribePage() {
  const [step, setStep] = useState('verify'); // verify → details → payment → success
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [sandboxOtp, setSandboxOtp] = useState('');
  const [membership, setMembership] = useState(null);
  const [orderId, setOrderId] = useState('');

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
        setOtp(resp.data.sandbox_otp); // Auto-fill in sandbox
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
      const resp = await axios.post(`${API_URL}/otp/verify`, { phone, otp });
      if (resp.data.verified) {
        toast.success('Phone verified!');
        setStep('details');
      }
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
        // Sandbox mode: simulate payment
        setStep('payment');
      } else {
        // Production: open Razorpay checkout
        openRazorpay(resp.data);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create order');
    } finally {
      setLoading(false);
    }
  };

  const openRazorpay = (orderData) => {
    const options = {
      key: orderData.key_id,
      amount: orderData.amount,
      currency: orderData.currency,
      order_id: orderData.order_id,
      name: 'Drops Curated',
      description: 'Monthly Membership - ₹399',
      handler: (response) => completePayment(response.razorpay_payment_id, response.razorpay_signature, orderData.order_id),
      prefill: { name, contact: phone },
      theme: { color: '#001F3F' },
    };
    const rzp = new window.Razorpay(options);
    rzp.open();
  };

  const completePayment = async (paymentId = 'sandbox_pay', signature = '', oid = '') => {
    setLoading(true);
    try {
      const resp = await axios.post(`${API_URL}/payment/verify`, {
        phone,
        order_id: oid || orderId,
        payment_id: paymentId,
        signature,
      });
      if (resp.data.success) {
        setMembership(resp.data);
        setStep('success');
        toast.success('Welcome to Drops Curated!');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Payment verification failed');
    } finally {
      setLoading(false);
    }
  };

  const stepIndex = STEPS.indexOf(step);

  return (
    <div className="bg-background min-h-screen" data-testid="subscribe-page">
      <Header />

      <main className="pt-28 pb-24">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          {/* Hero */}
          <div className="text-center mb-16">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-4">Membership</p>
            <h1 className="font-serif text-4xl md:text-5xl lg:text-6xl tracking-tight mb-4" data-testid="subscribe-heading">
              Join the Inner Circle
            </h1>
            <p className="text-base md:text-lg text-primary/50 max-w-lg mx-auto">
              WhatsApp alerts within 10 seconds of every drop, price cut, and exclusive deal.
            </p>
          </div>

          {/* Progress */}
          <div className="flex items-center justify-center gap-2 mb-12">
            {['Verify', 'Details', 'Pay', 'Done'].map((label, i) => (
              <React.Fragment key={label}>
                <div className={`flex items-center gap-2 ${i <= stepIndex ? 'text-accent' : 'text-primary/20'}`}>
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium border transition-all ${
                    i < stepIndex ? 'bg-accent text-primary border-accent' : i === stepIndex ? 'border-accent text-accent' : 'border-primary/20'
                  }`}>
                    {i < stepIndex ? <Check className="w-3.5 h-3.5" /> : i + 1}
                  </div>
                  <span className="text-xs hidden sm:inline">{label}</span>
                </div>
                {i < 3 && <div className={`w-8 sm:w-16 h-px ${i < stepIndex ? 'bg-accent' : 'bg-primary/10'}`} />}
              </React.Fragment>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16">
            {/* Left: Form */}
            <div className="lg:col-span-7">
              {/* Step 1: Verify Phone */}
              {step === 'verify' && (
                <div className="animate-fade-up" data-testid="step-verify">
                  <div className="w-14 h-14 border border-accent/30 flex items-center justify-center mb-6">
                    <Smartphone className="w-6 h-6 text-accent" strokeWidth={1.5} />
                  </div>
                  <h2 className="font-serif text-2xl md:text-3xl mb-2">Verify via WhatsApp</h2>
                  <p className="text-sm text-primary/40 mb-8">We verify via WhatsApp so your alerts are never flagged as spam.</p>

                  <div className="space-y-4 max-w-md">
                    <div>
                      <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">WhatsApp Number</label>
                      <div className="flex">
                        <span className="flex items-center px-4 bg-primary/[0.03] border border-primary/10 border-r-0 text-sm text-primary/50 font-medium">+91</span>
                        <input
                          type="tel"
                          value={phone}
                          onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                          placeholder="9876543210"
                          className="flex-1 px-4 py-3.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors"
                          data-testid="phone-input"
                        />
                      </div>
                    </div>

                    {!sandboxOtp ? (
                      <button
                        onClick={sendOtp}
                        disabled={loading || phone.length !== 10}
                        className="w-full bg-primary text-background py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40"
                        data-testid="send-otp-btn"
                      >
                        {loading ? 'Sending...' : 'Send OTP via WhatsApp'}
                        <MessageCircle className="w-4 h-4" strokeWidth={1.5} />
                      </button>
                    ) : (
                      <>
                        <div>
                          <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">Enter OTP</label>
                          <input
                            type="text"
                            value={otp}
                            onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                            placeholder="6-digit OTP"
                            className="w-full px-4 py-3.5 bg-surface border border-primary/10 text-sm text-center tracking-[0.5em] font-mono placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors"
                            data-testid="otp-input"
                          />
                        </div>
                        <button
                          onClick={verifyOtp}
                          disabled={loading || otp.length !== 6}
                          className="w-full bg-accent text-primary py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40"
                          data-testid="verify-otp-btn"
                        >
                          {loading ? 'Verifying...' : 'Verify & Continue'}
                          <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
                        </button>
                        {sandboxOtp && (
                          <p className="text-[10px] text-accent/60 text-center">Sandbox mode: OTP auto-filled</p>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* Step 2: Name */}
              {step === 'details' && (
                <div className="animate-fade-up" data-testid="step-details">
                  <div className="w-14 h-14 border border-accent/30 flex items-center justify-center mb-6">
                    <CreditCard className="w-6 h-6 text-accent" strokeWidth={1.5} />
                  </div>
                  <h2 className="font-serif text-2xl md:text-3xl mb-2">Almost There</h2>
                  <p className="text-sm text-primary/40 mb-8">Your name for the membership card.</p>

                  <div className="space-y-4 max-w-md">
                    <div>
                      <label className="text-xs text-primary/40 uppercase tracking-widest mb-2 block">Full Name</label>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Your name"
                        className="w-full px-4 py-3.5 bg-surface border border-primary/10 text-sm placeholder:text-primary/20 focus:outline-none focus:border-accent transition-colors"
                        data-testid="name-input"
                      />
                    </div>
                    <div className="bg-primary/[0.03] border border-primary/10 p-5">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium">Monthly Membership</span>
                        <span className="font-serif text-2xl">₹399</span>
                      </div>
                      <ul className="space-y-2">
                        {['Instant WhatsApp alerts (<10s)', 'Price drop notifications', 'New collection drops', 'Digital membership card'].map((f, i) => (
                          <li key={i} className="flex items-center gap-2 text-xs text-primary/50">
                            <Check className="w-3.5 h-3.5 text-accent flex-shrink-0" strokeWidth={1.5} />
                            {f}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <button
                      onClick={createOrder}
                      disabled={loading || !name.trim()}
                      className="w-full bg-primary text-background py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40"
                      data-testid="proceed-payment-btn"
                    >
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
                  <p className="text-sm text-primary/40 mb-8">Sandbox mode: Click below to simulate payment.</p>

                  <div className="max-w-md space-y-4">
                    <div className="bg-primary/[0.03] border border-primary/10 p-6 text-center">
                      <p className="text-xs text-primary/40 uppercase tracking-widest mb-2">Amount</p>
                      <p className="font-serif text-4xl mb-1">₹399</p>
                      <p className="text-xs text-primary/30">Monthly Membership</p>
                    </div>
                    <button
                      onClick={() => completePayment()}
                      disabled={loading}
                      className="w-full bg-accent text-primary py-4 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300 disabled:opacity-40"
                      data-testid="confirm-payment-btn"
                    >
                      {loading ? 'Processing...' : 'Confirm Payment (Sandbox)'}
                      <Check className="w-4 h-4" strokeWidth={1.5} />
                    </button>
                    <p className="text-[10px] text-primary/30 text-center flex items-center justify-center gap-1">
                      <Shield className="w-3 h-3" /> Secure payment via Razorpay UPI
                    </p>
                  </div>
                </div>
              )}

              {/* Step 4: Success + Membership Card */}
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
                    <p className="text-sm text-primary/50 mb-6">
                      Your membership card has been created. You'll start receiving WhatsApp alerts for new drops and price reductions within 10 seconds.
                    </p>

                    <div className="space-y-3 mb-8">
                      <button className="w-full border border-primary/10 py-3 text-sm font-medium flex items-center justify-center gap-2 hover:border-accent transition-colors" data-testid="add-apple-wallet">
                        Add to Apple Wallet
                        <ChevronRight className="w-4 h-4" strokeWidth={1.5} />
                      </button>
                      <button className="w-full border border-primary/10 py-3 text-sm font-medium flex items-center justify-center gap-2 hover:border-accent transition-colors" data-testid="add-google-wallet">
                        Add to Google Wallet
                        <ChevronRight className="w-4 h-4" strokeWidth={1.5} />
                      </button>
                    </div>

                    <Link
                      to="/browse"
                      className="block w-full bg-primary text-background py-3.5 font-medium text-sm text-center hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300"
                      data-testid="browse-after-subscribe"
                    >
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
                      { icon: <Zap strokeWidth={1.5} />, title: '<10 Second Alerts', desc: 'Fastest drop alerts in India. Get notified before the crowd.' },
                      { icon: <MessageCircle strokeWidth={1.5} />, title: 'WhatsApp Delivery', desc: 'No app to download. Alerts arrive directly in WhatsApp.' },
                      { icon: <CreditCard strokeWidth={1.5} />, title: 'Digital Membership', desc: 'Premium card for Apple Wallet & Google Wallet.' },
                      { icon: <Clock strokeWidth={1.5} />, title: 'Price History', desc: 'Track prices over time. Buy at the perfect moment.' },
                    ].map((f, i) => (
                      <div key={i} className="flex gap-4">
                        <div className="w-10 h-10 border border-accent/20 flex items-center justify-center flex-shrink-0 text-accent">
                          {f.icon}
                        </div>
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
    </div>
  );
}
