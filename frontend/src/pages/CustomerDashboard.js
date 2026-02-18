import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import { ChefHat, ShoppingCart, Package, LogOut, Search, Plus, Minus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const CustomerBrowse = () => {
  const [menuItems, setMenuItems] = useState([]);
  const [chefs, setChefs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const { addToCart } = useCart();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [itemsRes, chefsRes] = await Promise.all([
        axios.get(`${API_URL}/menu`),
        axios.get(`${API_URL}/chefs`),
      ]);
      setMenuItems(itemsRes.data);
      setChefs(chefsRes.data);
    } catch (error) {
      toast.error('Failed to load menu items');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    try {
      const res = await axios.get(`${API_URL}/menu`, {
        params: searchQuery ? { search: searchQuery } : {},
      });
      setMenuItems(res.data);
    } catch (error) {
      toast.error('Search failed');
    }
  };

  const handleAddToCart = (item) => {
    addToCart(item, 1);
    toast.success(`${item.name} added to cart!`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div data-testid="customer-browse">
      {/* Search Bar */}
      <div className="mb-8">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              data-testid="search-input"
              placeholder="Search for food or category..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-12 pr-4 py-3 bg-white border border-border-light rounded-2xl focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
            />
          </div>
          <button
            onClick={handleSearch}
            data-testid="search-btn"
            className="bg-primary hover:bg-primary-hover text-white rounded-2xl px-8 py-3 font-bold transition-all"
          >
            Search
          </button>
        </div>
      </div>

      {/* Menu Items Grid */}
      <div>
        <h2 className="text-2xl font-fredoka font-bold text-text-main mb-6">Available Dishes</h2>
        {menuItems.length === 0 ? (
          <p className="text-center text-text-muted py-12">No dishes available at the moment.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {menuItems.map((item) => (
              <div
                key={item.id}
                data-testid={`menu-item-${item.id}`}
                className="bg-white rounded-3xl overflow-hidden shadow-sm hover:shadow-md transition-all group cursor-pointer border border-gray-100"
              >
                <div className="relative h-48 overflow-hidden">
                  <img
                    src={item.image_url}
                    alt={item.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <div className="absolute top-3 right-3 bg-accent text-black px-3 py-1 rounded-full text-sm font-bold">
                    ${item.price.toFixed(2)}
                  </div>
                </div>
                <div className="p-5">
                  <h3 className="text-xl font-fredoka font-bold text-text-main mb-2">{item.name}</h3>
                  <p className="text-text-muted text-sm mb-3 line-clamp-2">{item.description}</p>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <img
                        src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${item.chef_name}`}
                        alt={item.chef_name}
                        className="w-8 h-8 rounded-full"
                      />
                      <span className="text-sm font-medium text-text-main">{item.chef_name}</span>
                    </div>
                    <span className="text-xs bg-secondary/10 text-secondary px-2 py-1 rounded-full font-medium">
                      {item.category}
                    </span>
                  </div>
                  <button
                    onClick={() => handleAddToCart(item)}
                    data-testid={`add-to-cart-${item.id}`}
                    className="w-full bg-primary hover:bg-primary-hover text-white rounded-full py-2.5 font-bold transition-all"
                  >
                    Add to Cart
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const CustomerCart = () => {
  const { cart, updateQuantity, removeFromCart, totalAmount, clearCart } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [address, setAddress] = useState('');
  const [loading, setLoading] = useState(false);

  const handleCheckout = async () => {
    if (!address.trim()) {
      toast.error('Please enter delivery address');
      return;
    }

    if (cart.length === 0) {
      toast.error('Your cart is empty');
      return;
    }

    setLoading(true);
    try {
      const orderData = {
        items: cart.map((item) => ({
          menu_item_id: item.id,
          name: item.name,
          price: item.price,
          quantity: item.quantity,
          chef_id: item.chef_id,
        })),
        delivery_address: address,
        origin_url: window.location.origin,
      };

      const response = await axios.post(`${API_URL}/orders`, orderData);
      const order = response.data;

      // Clear cart and navigate to checkout
      clearCart();
      navigate(`/checkout?order_id=${order.id}`);
    } catch (error) {
      toast.error('Failed to create order');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="customer-cart">
      <h2 className="text-2xl font-fredoka font-bold text-text-main mb-6">Your Cart</h2>

      {cart.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center">
          <ShoppingCart className="w-16 h-16 text-text-muted mx-auto mb-4" />
          <p className="text-text-muted text-lg">Your cart is empty</p>
          <Link
            to="/customer"
            className="inline-block mt-4 text-primary font-bold hover:underline"
          >
            Start browsing
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            {cart.map((item) => (
              <div
                key={item.id}
                data-testid={`cart-item-${item.id}`}
                className="bg-white rounded-3xl p-5 flex gap-4 items-center border border-border-light"
              >
                <img
                  src={item.image_url}
                  alt={item.name}
                  className="w-24 h-24 rounded-2xl object-cover"
                />
                <div className="flex-1">
                  <h3 className="font-fredoka font-bold text-lg text-text-main">{item.name}</h3>
                  <p className="text-text-muted text-sm">by {item.chef_name}</p>
                  <p className="text-primary font-bold mt-1">${item.price.toFixed(2)}</p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => updateQuantity(item.id, item.quantity - 1)}
                    data-testid={`decrease-qty-${item.id}`}
                    className="w-8 h-8 bg-gray-100 hover:bg-gray-200 rounded-full flex items-center justify-center transition-colors"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                  <span className="font-bold w-8 text-center" data-testid={`qty-${item.id}`}>{item.quantity}</span>
                  <button
                    onClick={() => updateQuantity(item.id, item.quantity + 1)}
                    data-testid={`increase-qty-${item.id}`}
                    className="w-8 h-8 bg-gray-100 hover:bg-gray-200 rounded-full flex items-center justify-center transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
                <button
                  onClick={() => removeFromCart(item.id)}
                  data-testid={`remove-${item.id}`}
                  className="text-red-500 hover:text-red-600 text-sm font-medium"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>

          <div className="lg:col-span-1">
            <div className="bg-white rounded-3xl p-6 border border-border-light sticky top-6">
              <h3 className="font-fredoka font-bold text-xl text-text-main mb-4">Order Summary</h3>
              
              <div className="space-y-3 mb-4">
                <div className="flex justify-between text-text-muted">
                  <span>Subtotal</span>
                  <span>${totalAmount.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-text-muted">
                  <span>Delivery Fee</span>
                  <span>$2.99</span>
                </div>
                <div className="border-t border-border-light pt-3 flex justify-between font-bold text-lg text-text-main">
                  <span>Total</span>
                  <span data-testid="cart-total">${(totalAmount + 2.99).toFixed(2)}</span>
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-text-main mb-2">Delivery Address</label>
                <textarea
                  data-testid="delivery-address-input"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Enter your delivery address"
                  rows={3}
                  className="w-full bg-gray-50 border-transparent focus:border-primary focus:bg-white rounded-xl px-4 py-3 transition-all outline-none focus:ring-2 focus:ring-primary/20 resize-none"
                />
              </div>

              <button
                onClick={handleCheckout}
                data-testid="checkout-btn"
                disabled={loading}
                className="w-full bg-primary hover:bg-primary-hover text-white rounded-full py-3 font-bold transition-all disabled:opacity-50"
              >
                {loading ? 'Processing...' : 'Proceed to Checkout'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const CustomerOrders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const res = await axios.get(`${API_URL}/orders/my`);
      setOrders(res.data);
    } catch (error) {
      toast.error('Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div data-testid="customer-orders">
      <h2 className="text-2xl font-fredoka font-bold text-text-main mb-6">My Orders</h2>

      {orders.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center">
          <Package className="w-16 h-16 text-text-muted mx-auto mb-4" />
          <p className="text-text-muted text-lg">No orders yet</p>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <div
              key={order.id}
              data-testid={`order-${order.id}`}
              className="bg-white rounded-3xl p-6 border border-border-light"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-sm text-text-muted">Order #{order.id.slice(-8)}</p>
                  <p className="text-xs text-text-muted mt-1">
                    {new Date(order.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="text-right">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                    order.status === 'delivered' ? 'bg-secondary/10 text-secondary' :
                    order.status === 'cancelled' ? 'bg-red-100 text-red-600' :
                    'bg-accent/10 text-accent'
                  }`}>
                    {order.status}
                  </span>
                  <p className="text-lg font-bold text-text-main mt-2">${order.total_amount.toFixed(2)}</p>
                </div>
              </div>

              <div className="space-y-2 mb-4">
                {order.items.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm">
                    <span className="text-text-main">{item.name} x {item.quantity}</span>
                    <span className="text-text-muted">${(item.price * item.quantity).toFixed(2)}</span>
                  </div>
                ))}
              </div>

              <div className="flex gap-3">
                <Link
                  to={`/order/${order.id}`}
                  data-testid={`view-order-${order.id}`}
                  className="flex-1 bg-primary/10 text-primary hover:bg-primary/20 rounded-full py-2 text-center font-bold transition-all"
                >
                  View Details
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const CustomerDashboard = () => {
  const { user, logout } = useAuth();
  const { cart } = useCart();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-bg-main font-dmsans">
      {/* Header */}
      <header className="bg-white border-b border-border-light sticky top-0 z-40">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ChefHat className="w-8 h-8 text-primary" />
              <span className="text-2xl font-fredoka font-bold text-text-main">House of Kitchens</span>
            </div>

            <nav className="flex items-center gap-6">
              <Link
                to="/customer"
                data-testid="nav-browse"
                className="text-text-main hover:text-primary font-medium transition-colors"
              >
                Browse
              </Link>
              <Link
                to="/customer/cart"
                data-testid="nav-cart"
                className="text-text-main hover:text-primary font-medium transition-colors relative"
              >
                <ShoppingCart className="w-6 h-6" />
                {cart.length > 0 && (
                  <span className="absolute -top-2 -right-2 bg-primary text-white text-xs w-5 h-5 rounded-full flex items-center justify-center" data-testid="cart-count">
                    {cart.length}
                  </span>
                )}
              </Link>
              <Link
                to="/customer/orders"
                data-testid="nav-orders"
                className="text-text-main hover:text-primary font-medium transition-colors"
              >
                Orders
              </Link>
              <button
                onClick={handleLogout}
                data-testid="logout-btn"
                className="text-text-muted hover:text-primary transition-colors"
              >
                <LogOut className="w-6 h-6" />
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-fredoka font-bold text-text-main mb-2">Welcome, {user?.name}!</h1>
          <p className="text-text-muted">Discover delicious homemade meals from talented local chefs</p>
        </div>

        <Routes>
          <Route index element={<CustomerBrowse />} />
          <Route path="cart" element={<CustomerCart />} />
          <Route path="orders" element={<CustomerOrders />} />
        </Routes>
      </main>
    </div>
  );
};

export default CustomerDashboard;
