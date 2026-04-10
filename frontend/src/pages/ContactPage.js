import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Header, Footer } from './LandingPage';
import { Send, CheckCircle, User, Mail, Phone, MessageSquare, HelpCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    subject: '',
    category: 'general',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    // Validate
    if (!formData.name || !formData.email || !formData.message) {
      setError('Please fill in all required fields');
      setIsSubmitting(false);
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      setIsSubmitting(false);
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/contact`, formData);
      
      if (response.data.success) {
        setIsSubmitted(true);
        setFormData({
          name: '',
          email: '',
          phone: '',
          subject: '',
          category: 'general',
          message: ''
        });
      } else {
        setError(response.data.message || 'Failed to send message. Please try again.');
      }
    } catch (err) {
      console.error('Contact form error:', err);
      setError('Failed to send message. Please try again later.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Success State
  if (isSubmitted) {
    return (
      <div className="bg-background min-h-screen" data-testid="contact-page">
        <Header />
        
        <section className="pt-28 pb-20 md:pt-36 md:pb-32">
          <div className="max-w-xl mx-auto px-6 text-center">
            <div className="w-20 h-20 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-10 h-10 text-green-500" />
            </div>
            <h1 className="text-3xl md:text-4xl font-serif mb-4">Message Sent!</h1>
            <p className="text-primary/60 mb-8">
              Thank you for reaching out. We've received your message and will get back to you within 24 hours.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => setIsSubmitted(false)}
                className="px-6 py-3 border border-primary/15 text-sm font-medium hover:border-accent hover:text-accent transition-all"
              >
                Send Another Message
              </button>
              <Link
                to="/"
                className="px-6 py-3 bg-primary text-background text-sm font-medium hover:-translate-y-0.5 hover:shadow-lift transition-all"
              >
                Back to Home
              </Link>
            </div>
          </div>
        </section>
        
        <Footer />
      </div>
    );
  }

  return (
    <div className="bg-background min-h-screen" data-testid="contact-page">
      <Header />
      
      {/* Hero */}
      <section className="pt-28 pb-12 md:pt-36 md:pb-16 bg-gradient-to-b from-primary/5 to-transparent">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <span className="inline-block text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4">Contact Us</span>
          <h1 className="text-4xl md:text-5xl font-serif mb-4">Get in Touch</h1>
          <p className="text-lg text-primary/60 max-w-xl mx-auto">
            Have a question, feedback, or partnership inquiry? We'd love to hear from you.
          </p>
        </div>
      </section>
      
      {/* Contact Form */}
      <section className="py-12 md:py-16">
        <div className="max-w-2xl mx-auto px-6">
          <form onSubmit={handleSubmit} className="space-y-6" data-testid="contact-form">
            
            {/* Error Message */}
            {error && (
              <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 text-red-600">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <p className="text-sm">{error}</p>
              </div>
            )}
            
            {/* Name & Email Row */}
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-primary/50 mb-2">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/30" />
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="Your name"
                    required
                    className="w-full pl-11 pr-4 py-3 bg-surface border border-primary/10 text-sm placeholder:text-primary/30 focus:outline-none focus:border-accent transition-colors"
                    data-testid="contact-name"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-primary/50 mb-2">
                  Email Address <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/30" />
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="you@example.com"
                    required
                    className="w-full pl-11 pr-4 py-3 bg-surface border border-primary/10 text-sm placeholder:text-primary/30 focus:outline-none focus:border-accent transition-colors"
                    data-testid="contact-email"
                  />
                </div>
              </div>
            </div>
            
            {/* Phone & Category Row */}
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-primary/50 mb-2">
                  Phone Number
                </label>
                <div className="relative">
                  <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/30" />
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="+91 98765 43210"
                    className="w-full pl-11 pr-4 py-3 bg-surface border border-primary/10 text-sm placeholder:text-primary/30 focus:outline-none focus:border-accent transition-colors"
                    data-testid="contact-phone"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-primary/50 mb-2">
                  Category
                </label>
                <div className="relative">
                  <HelpCircle className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/30" />
                  <select
                    name="category"
                    value={formData.category}
                    onChange={handleChange}
                    className="w-full pl-11 pr-4 py-3 bg-surface border border-primary/10 text-sm focus:outline-none focus:border-accent transition-colors appearance-none cursor-pointer"
                    data-testid="contact-category"
                  >
                    <option value="general">General Inquiry</option>
                    <option value="support">Support / Help</option>
                    <option value="billing">Billing / Subscription</option>
                    <option value="partnership">Partnership / Business</option>
                    <option value="feedback">Feedback / Suggestion</option>
                    <option value="bug">Report a Bug</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
            </div>
            
            {/* Subject */}
            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-primary/50 mb-2">
                Subject
              </label>
              <input
                type="text"
                name="subject"
                value={formData.subject}
                onChange={handleChange}
                placeholder="Brief subject of your message"
                className="w-full px-4 py-3 bg-surface border border-primary/10 text-sm placeholder:text-primary/30 focus:outline-none focus:border-accent transition-colors"
                data-testid="contact-subject"
              />
            </div>
            
            {/* Message */}
            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-primary/50 mb-2">
                Message <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <MessageSquare className="absolute left-4 top-4 w-4 h-4 text-primary/30" />
                <textarea
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  placeholder="Tell us how we can help you..."
                  required
                  rows={6}
                  className="w-full pl-11 pr-4 py-3 bg-surface border border-primary/10 text-sm placeholder:text-primary/30 focus:outline-none focus:border-accent transition-colors resize-none"
                  data-testid="contact-message"
                />
              </div>
            </div>
            
            {/* Submit Button */}
            <div className="pt-4">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex items-center justify-center gap-2 bg-primary text-background py-4 font-medium text-sm hover:-translate-y-0.5 hover:shadow-lift transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
                data-testid="contact-submit"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-background/30 border-t-background rounded-full animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Send Message
                  </>
                )}
              </button>
            </div>
            
            <p className="text-xs text-primary/40 text-center">
              We typically respond within 24 hours. For urgent matters, include your phone number.
            </p>
          </form>
        </div>
      </section>
      
      {/* Additional Contact Info */}
      <section className="py-12 md:py-16 bg-surface">
        <div className="max-w-4xl mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="w-12 h-12 bg-accent/10 flex items-center justify-center mx-auto mb-4">
                <Mail className="w-5 h-5 text-accent" />
              </div>
              <h3 className="font-medium mb-2">Email</h3>
              <p className="text-sm text-primary/60">For general inquiries</p>
              <p className="text-sm text-accent mt-1">help@dropscurated.com</p>
            </div>
            
            <div>
              <div className="w-12 h-12 bg-accent/10 flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="w-5 h-5 text-accent" />
              </div>
              <h3 className="font-medium mb-2">WhatsApp</h3>
              <p className="text-sm text-primary/60">Quick support</p>
              <p className="text-sm text-accent mt-1">Reply to any alert message</p>
            </div>
            
            <div>
              <div className="w-12 h-12 bg-accent/10 flex items-center justify-center mx-auto mb-4">
                <HelpCircle className="w-5 h-5 text-accent" />
              </div>
              <h3 className="font-medium mb-2">FAQ</h3>
              <p className="text-sm text-primary/60">Find quick answers</p>
              <Link to="/faq" className="text-sm text-accent mt-1 hover:underline">Visit FAQ Page</Link>
            </div>
          </div>
        </div>
      </section>
      
      <Footer />
    </div>
  );
}
