import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChefHat, MapPin, Clock, Package } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const statusSteps = [
  { key: 'pending', label: 'Order Placed', icon: Package },
  { key: 'confirmed', label: 'Confirmed', icon: Package },
  { key: 'preparing', label: 'Preparing', icon: ChefHat },
  { key: 'on_the_way', label: 'On the Way', icon: MapPin },
  { key: 'delivered', label: 'Delivered', icon: Package },
];

const OrderTracking = () => {
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrder();
    const interval = setInterval(fetchOrder, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, [orderId]);

  const fetchOrder = async () => {
    try {
      const res = await axios.get(`${API_URL}/orders/${orderId}`);
      setOrder(res.data);
    } catch (error) {
      toast.error('Failed to load order');
    } finally {
      setLoading(false);
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

  const currentStepIndex = statusSteps.findIndex((s) => s.key === order.status);

  return (
    <div className="min-h-screen bg-bg-main font-dmsans py-12 px-6" data-testid="order-tracking-page">
      <div className="container mx-auto max-w-3xl">
        {/* Header */}
        <div className="text-center mb-8">
          <Link to={order.customer_id ? '/customer/orders' : '/chef/orders'} className="inline-flex items-center gap-2 mb-4 text-primary hover:underline">
            ← Back to Orders
          </Link>
          <h1 className="text-3xl font-fredoka font-bold text-text-main mb-2">Order Tracking</h1>
          <p className="text-text-muted">Order #{order.id.slice(-8)}</p>
        </div>

        {/* Order Status Timeline */}
        <div className="bg-white rounded-3xl p-8 shadow-lg border border-border-light mb-6">
          <h2 className="font-fredoka font-bold text-xl text-text-main mb-6">Order Status</h2>
          
          <div className="relative">
            {/* Progress Line */}
            <div className="absolute left-6 top-8 bottom-8 w-0.5 bg-gray-200"></div>
            <div
              className="absolute left-6 top-8 w-0.5 bg-primary transition-all duration-500"
              style={{ height: `${(currentStepIndex / (statusSteps.length - 1)) * 100}%` }}
            ></div>

            {/* Status Steps */}
            <div className="space-y-8">
              {statusSteps.map((step, index) => {
                const Icon = step.icon;
                const isCompleted = index <= currentStepIndex;
                const isCurrent = index === currentStepIndex;

                return (
                  <div key={step.key} className="relative flex items-center gap-4" data-testid={`status-${step.key}`}>
                    <div
                      className={`relative z-10 w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                        isCompleted
                          ? 'bg-primary text-white'
                          : 'bg-gray-200 text-gray-400'
                      } ${isCurrent ? 'ring-4 ring-primary/20 scale-110' : ''}`}
                    >
                      <Icon className="w-6 h-6" />
                    </div>
                    <div className="flex-1">
                      <p className={`font-bold ${
                        isCompleted ? 'text-text-main' : 'text-text-muted'
                      }`}>
                        {step.label}
                      </p>
                      {isCurrent && (
                        <p className="text-sm text-primary font-medium">Current Status</p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {order.status === 'cancelled' && (
            <div className="mt-6 bg-red-50 border border-red-200 rounded-2xl p-4">
              <p className="text-red-600 font-bold">Order Cancelled</p>
            </div>
          )}
        </div>

        {/* Order Details */}
        <div className="bg-white rounded-3xl p-8 shadow-lg border border-border-light mb-6">
          <h2 className="font-fredoka font-bold text-xl text-text-main mb-4">Order Details</h2>
          
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <Package className="w-5 h-5 text-primary mt-1" />
              <div className="flex-1">
                <p className="font-medium text-text-main mb-2">Items:</p>
                {order.items.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm mb-1">
                    <span>{item.name} x {item.quantity}</span>
                    <span className="font-medium">${(item.price * item.quantity).toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-start gap-3">
              <MapPin className="w-5 h-5 text-primary mt-1" />
              <div>
                <p className="font-medium text-text-main">Delivery Address:</p>
                <p className="text-sm text-text-muted">{order.delivery_address}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Clock className="w-5 h-5 text-primary mt-1" />
              <div>
                <p className="font-medium text-text-main">Order Time:</p>
                <p className="text-sm text-text-muted">{new Date(order.created_at).toLocaleString()}</p>
              </div>
            </div>

            <div className="border-t border-border-light pt-4 mt-4">
              <div className="flex justify-between font-bold text-lg text-text-main">
                <span>Total Amount:</span>
                <span data-testid="order-total">${order.total_amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm mt-2">
                <span className="text-text-muted">Payment Status:</span>
                <span className={`font-bold ${
                  order.payment_status === 'paid' ? 'text-secondary' : 'text-red-600'
                }`}>
                  {order.payment_status.toUpperCase()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderTracking;
