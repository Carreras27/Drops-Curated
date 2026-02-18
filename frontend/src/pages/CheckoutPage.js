import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { ChefHat, CreditCard, Loader } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const CheckoutPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const orderId = searchParams.get('order_id');
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (orderId) {
      fetchOrder();
    }
  }, [orderId]);

  const fetchOrder = async () => {
    try {
      const res = await axios.get(`${API_URL}/orders/${orderId}`);
      setOrder(res.data);
    } catch (error) {
      toast.error('Failed to load order');
      navigate('/customer/orders');
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    setProcessing(true);
    try {
      const response = await axios.post(`${API_URL}/checkout`, {
        order_id: orderId,
        origin_url: window.location.origin,
      });

      // Redirect to Stripe
      window.location.href = response.data.url;
    } catch (error) {
      toast.error('Failed to process payment');
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text-muted">Order not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-main font-dmsans py-12 px-6" data-testid="checkout-page">
      <div className="container mx-auto max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <ChefHat className="w-10 h-10 text-primary" />
            <span className="text-3xl font-fredoka font-bold text-text-main">House of Kitchens</span>
          </div>
          <h1 className="text-3xl font-fredoka font-bold text-text-main mb-2">Complete Your Order</h1>
          <p className="text-text-muted">Review your order and proceed to payment</p>
        </div>

        {/* Order Summary */}
        <div className="bg-white rounded-3xl p-8 shadow-lg border border-border-light mb-6">
          <h2 className="font-fredoka font-bold text-xl text-text-main mb-4">Order Summary</h2>
          
          <div className="space-y-3 mb-6">
            {order.items.map((item, idx) => (
              <div key={idx} className="flex justify-between items-center" data-testid={`checkout-item-${idx}`}>
                <div>
                  <p className="font-medium text-text-main">{item.name}</p>
                  <p className="text-sm text-text-muted">Quantity: {item.quantity}</p>
                </div>
                <p className="font-bold text-text-main">${(item.price * item.quantity).toFixed(2)}</p>
              </div>
            ))}
          </div>

          <div className="border-t border-border-light pt-4 mb-6">
            <div className="flex justify-between text-text-muted mb-2">
              <span>Subtotal</span>
              <span>${order.total_amount.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-text-muted mb-2">
              <span>Delivery Fee</span>
              <span>$2.99</span>
            </div>
            <div className="flex justify-between font-bold text-lg text-text-main mt-3">
              <span>Total</span>
              <span data-testid="checkout-total">${(order.total_amount + 2.99).toFixed(2)}</span>
            </div>
          </div>

          <div className="bg-gray-50 rounded-2xl p-4 mb-6">
            <p className="text-sm font-medium text-text-main mb-1">Delivery Address:</p>
            <p className="text-sm text-text-muted">{order.delivery_address}</p>
          </div>

          <button
            onClick={handlePayment}
            disabled={processing}
            data-testid="pay-now-btn"
            className="w-full bg-primary hover:bg-primary-hover text-white rounded-full py-4 font-bold transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {processing ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <CreditCard className="w-5 h-5" />
                Pay ${(order.total_amount + 2.99).toFixed(2)}
              </>
            )}
          </button>

          <p className="text-xs text-text-muted text-center mt-4">
            Secure payment processed by Stripe
          </p>
        </div>
      </div>
    </div>
  );
};

export default CheckoutPage;
