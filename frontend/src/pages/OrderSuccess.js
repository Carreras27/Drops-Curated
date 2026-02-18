import React, { useState, useEffect } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { CheckCircle, Loader } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const OrderSuccess = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = searchParams.get('session_id');
  const [paymentStatus, setPaymentStatus] = useState('checking');
  const [attempts, setAttempts] = useState(0);
  const maxAttempts = 10;

  useEffect(() => {
    if (sessionId) {
      pollPaymentStatus();
    } else {
      navigate('/customer/orders');
    }
  }, [sessionId]);

  const pollPaymentStatus = async () => {
    if (attempts >= maxAttempts) {
      setPaymentStatus('timeout');
      return;
    }

    try {
      const response = await axios.get(`${API_URL}/checkout/status/${sessionId}`);
      
      if (response.data.payment_status === 'paid') {
        setPaymentStatus('success');
        toast.success('Payment successful!');
      } else if (response.data.status === 'expired') {
        setPaymentStatus('failed');
        toast.error('Payment session expired');
      } else {
        // Continue polling
        setAttempts(prev => prev + 1);
        setTimeout(pollPaymentStatus, 2000);
      }
    } catch (error) {
      console.error('Error checking payment status:', error);
      setAttempts(prev => prev + 1);
      setTimeout(pollPaymentStatus, 2000);
    }
  };

  if (paymentStatus === 'checking') {
    return (
      <div className="min-h-screen bg-bg-main flex items-center justify-center px-6" data-testid="order-success-page">
        <div className="text-center">
          <Loader className="w-16 h-16 text-primary mx-auto mb-4 animate-spin" />
          <h2 className="text-2xl font-fredoka font-bold text-text-main mb-2">Processing Payment</h2>
          <p className="text-text-muted">Please wait while we confirm your payment...</p>
        </div>
      </div>
    );
  }

  if (paymentStatus === 'failed' || paymentStatus === 'timeout') {
    return (
      <div className="min-h-screen bg-bg-main flex items-center justify-center px-6">
        <div className="bg-white rounded-3xl p-12 text-center max-w-md shadow-lg border border-border-light">
          <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <span className="text-4xl">❌</span>
          </div>
          <h2 className="text-2xl font-fredoka font-bold text-text-main mb-4">Payment Failed</h2>
          <p className="text-text-muted mb-6">
            {paymentStatus === 'timeout'
              ? 'Payment verification timed out. Please check your orders or contact support.'
              : 'Your payment could not be processed. Please try again.'}
          </p>
          <Link
            to="/customer/orders"
            data-testid="view-orders-btn"
            className="inline-block bg-primary hover:bg-primary-hover text-white rounded-full px-8 py-3 font-bold transition-all"
          >
            View My Orders
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-main flex items-center justify-center px-6" data-testid="order-success-page">
      <div className="bg-white rounded-3xl p-12 text-center max-w-md shadow-lg border border-border-light">
        <div className="w-20 h-20 bg-secondary/10 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="w-12 h-12 text-secondary" />
        </div>
        <h2 className="text-3xl font-fredoka font-bold text-text-main mb-4">Order Confirmed!</h2>
        <p className="text-text-muted mb-6">
          Thank you for your order! Your payment was successful and your chef has been notified.
        </p>
        <div className="space-y-3">
          <Link
            to="/customer/orders"
            data-testid="view-orders-link"
            className="block bg-primary hover:bg-primary-hover text-white rounded-full px-8 py-3 font-bold transition-all"
          >
            View My Orders
          </Link>
          <Link
            to="/customer"
            data-testid="continue-browsing-link"
            className="block bg-white border-2 border-primary text-primary hover:bg-orange-50 rounded-full px-8 py-3 font-bold transition-all"
          >
            Continue Browsing
          </Link>
        </div>
      </div>
    </div>
  );
};

export default OrderSuccess;
