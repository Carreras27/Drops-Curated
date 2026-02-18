import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import { ChefHat, Plus, Edit, Trash2, LogOut, DollarSign, Package, Star } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const ChefMenu = () => {
  const [menuItems, setMenuItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    category: '',
    image_url: 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80',
    is_available: true,
  });

  useEffect(() => {
    fetchMenuItems();
  }, []);

  const fetchMenuItems = async () => {
    try {
      const res = await axios.get(`${API_URL}/menu/my`);
      setMenuItems(res.data);
    } catch (error) {
      toast.error('Failed to load menu items');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingItem) {
        await axios.put(`${API_URL}/menu/${editingItem.id}`, {
          ...formData,
          price: parseFloat(formData.price),
        });
        toast.success('Menu item updated!');
      } else {
        await axios.post(`${API_URL}/menu`, {
          ...formData,
          price: parseFloat(formData.price),
        });
        toast.success('Menu item added!');
      }
      setShowForm(false);
      setEditingItem(null);
      setFormData({
        name: '',
        description: '',
        price: '',
        category: '',
        image_url: 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80',
        is_available: true,
      });
      fetchMenuItems();
    } catch (error) {
      toast.error('Failed to save menu item');
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setFormData({
      name: item.name,
      description: item.description,
      price: item.price.toString(),
      category: item.category,
      image_url: item.image_url,
      is_available: item.is_available,
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this item?')) return;
    
    try {
      await axios.delete(`${API_URL}/menu/${id}`);
      toast.success('Menu item deleted');
      fetchMenuItems();
    } catch (error) {
      toast.error('Failed to delete menu item');
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
    <div data-testid="chef-menu">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-fredoka font-bold text-text-main">My Menu</h2>
        <button
          onClick={() => {
            setShowForm(!showForm);
            setEditingItem(null);
            setFormData({
              name: '',
              description: '',
              price: '',
              category: '',
              image_url: 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80',
              is_available: true,
            });
          }}
          data-testid="add-menu-item-btn"
          className="bg-primary hover:bg-primary-hover text-white rounded-full px-6 py-3 font-bold flex items-center gap-2 transition-all"
        >
          <Plus className="w-5 h-5" />
          Add Item
        </button>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <div className="bg-white rounded-3xl p-6 mb-6 border border-border-light" data-testid="menu-item-form">
          <h3 className="font-fredoka font-bold text-xl text-text-main mb-4">
            {editingItem ? 'Edit Menu Item' : 'Add New Menu Item'}
          </h3>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-main mb-2">Name</label>
              <input
                type="text"
                data-testid="menu-name-input"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full bg-gray-50 border-transparent focus:border-primary focus:bg-white rounded-xl px-4 py-3 transition-all outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="Dish name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-main mb-2">Category</label>
              <input
                type="text"
                data-testid="menu-category-input"
                required
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full bg-gray-50 border-transparent focus:border-primary focus:bg-white rounded-xl px-4 py-3 transition-all outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="e.g., Italian, Indian, Dessert"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-main mb-2">Price ($)</label>
              <input
                type="number"
                step="0.01"
                data-testid="menu-price-input"
                required
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                className="w-full bg-gray-50 border-transparent focus:border-primary focus:bg-white rounded-xl px-4 py-3 transition-all outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-main mb-2">Image URL</label>
              <input
                type="url"
                data-testid="menu-image-input"
                required
                value={formData.image_url}
                onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                className="w-full bg-gray-50 border-transparent focus:border-primary focus:bg-white rounded-xl px-4 py-3 transition-all outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="https://..."
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-text-main mb-2">Description</label>
              <textarea
                data-testid="menu-description-input"
                required
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="w-full bg-gray-50 border-transparent focus:border-primary focus:bg-white rounded-xl px-4 py-3 transition-all outline-none focus:ring-2 focus:ring-primary/20 resize-none"
                placeholder="Describe your dish..."
              />
            </div>
            <div className="md:col-span-2 flex items-center gap-2">
              <input
                type="checkbox"
                id="is_available"
                data-testid="menu-available-checkbox"
                checked={formData.is_available}
                onChange={(e) => setFormData({ ...formData, is_available: e.target.checked })}
                className="w-5 h-5 rounded text-primary focus:ring-primary"
              />
              <label htmlFor="is_available" className="text-sm font-medium text-text-main">
                Available for ordering
              </label>
            </div>
            <div className="md:col-span-2 flex gap-3">
              <button
                type="submit"
                data-testid="save-menu-item-btn"
                className="bg-primary hover:bg-primary-hover text-white rounded-full px-8 py-3 font-bold transition-all"
              >
                {editingItem ? 'Update' : 'Add'} Item
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingItem(null);
                }}
                data-testid="cancel-menu-form-btn"
                className="bg-gray-100 hover:bg-gray-200 text-text-main rounded-full px-8 py-3 font-bold transition-all"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Menu Items List */}
      {menuItems.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center">
          <ChefHat className="w-16 h-16 text-text-muted mx-auto mb-4" />
          <p className="text-text-muted text-lg">No menu items yet</p>
          <p className="text-text-muted text-sm mt-2">Add your first dish to get started!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {menuItems.map((item) => (
            <div
              key={item.id}
              data-testid={`menu-item-${item.id}`}
              className="bg-white rounded-3xl overflow-hidden shadow-sm border border-gray-100"
            >
              <div className="relative h-48">
                <img src={item.image_url} alt={item.name} className="w-full h-full object-cover" />
                <div className="absolute top-3 right-3 bg-accent text-black px-3 py-1 rounded-full text-sm font-bold">
                  ${item.price.toFixed(2)}
                </div>
                {!item.is_available && (
                  <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                    <span className="bg-white text-text-main px-4 py-2 rounded-full font-bold">Unavailable</span>
                  </div>
                )}
              </div>
              <div className="p-5">
                <h3 className="text-xl font-fredoka font-bold text-text-main mb-2">{item.name}</h3>
                <p className="text-text-muted text-sm mb-3 line-clamp-2">{item.description}</p>
                <span className="text-xs bg-secondary/10 text-secondary px-2 py-1 rounded-full font-medium">
                  {item.category}
                </span>
                <div className="flex gap-2 mt-4">
                  <button
                    onClick={() => handleEdit(item)}
                    data-testid={`edit-menu-${item.id}`}
                    className="flex-1 bg-primary/10 text-primary hover:bg-primary/20 rounded-full py-2 font-bold transition-all flex items-center justify-center gap-2"
                  >
                    <Edit className="w-4 h-4" />
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    data-testid={`delete-menu-${item.id}`}
                    className="flex-1 bg-red-50 text-red-600 hover:bg-red-100 rounded-full py-2 font-bold transition-all flex items-center justify-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const ChefOrders = () => {
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

  const updateOrderStatus = async (orderId, status) => {
    try {
      await axios.put(`${API_URL}/orders/${orderId}/status?status=${status}`);
      toast.success('Order status updated');
      fetchOrders();
    } catch (error) {
      toast.error('Failed to update order status');
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
    <div data-testid="chef-orders">
      <h2 className="text-2xl font-fredoka font-bold text-text-main mb-6">Orders</h2>

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
                  <p className="font-bold text-text-main">Order #{order.id.slice(-8)}</p>
                  <p className="text-sm text-text-muted mt-1">Customer: {order.customer_name}</p>
                  <p className="text-xs text-text-muted">{new Date(order.created_at).toLocaleString()}</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-text-main">${order.total_amount.toFixed(2)}</p>
                  <span className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-bold uppercase ${
                    order.payment_status === 'paid' ? 'bg-secondary/10 text-secondary' : 'bg-red-100 text-red-600'
                  }`}>
                    {order.payment_status}
                  </span>
                </div>
              </div>

              <div className="bg-gray-50 rounded-2xl p-4 mb-4">
                <p className="text-sm font-medium text-text-main mb-2">Items:</p>
                {order.items.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm mb-1">
                    <span>{item.name} x {item.quantity}</span>
                    <span className="font-medium">${(item.price * item.quantity).toFixed(2)}</span>
                  </div>
                ))}
                <div className="border-t border-gray-200 mt-2 pt-2">
                  <p className="text-xs text-text-muted">
                    <strong>Delivery:</strong> {order.delivery_address}
                  </p>
                </div>
              </div>

              <div className="flex gap-2">
                <select
                  value={order.status}
                  onChange={(e) => updateOrderStatus(order.id, e.target.value)}
                  data-testid={`order-status-${order.id}`}
                  className="flex-1 bg-gray-50 border border-border-light rounded-xl px-4 py-2 outline-none focus:border-primary"
                >
                  <option value="pending">Pending</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="preparing">Preparing</option>
                  <option value="on_the_way">On the Way</option>
                  <option value="delivered">Delivered</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const ChefEarnings = () => {
  const [earnings, setEarnings] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEarnings();
  }, []);

  const fetchEarnings = async () => {
    try {
      const res = await axios.get(`${API_URL}/chef/earnings`);
      setEarnings(res.data);
    } catch (error) {
      toast.error('Failed to load earnings');
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
    <div data-testid="chef-earnings">
      <h2 className="text-2xl font-fredoka font-bold text-text-main mb-6">Earnings & Stats</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-3xl p-6 border border-border-light">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-primary" />
            </div>
            <p className="text-sm text-text-muted">Total Earnings</p>
          </div>
          <p className="text-3xl font-fredoka font-bold text-text-main" data-testid="total-earnings">
            ${earnings?.total_earnings || 0}
          </p>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-border-light">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-secondary/10 rounded-2xl flex items-center justify-center">
              <Package className="w-6 h-6 text-secondary" />
            </div>
            <p className="text-sm text-text-muted">Total Orders</p>
          </div>
          <p className="text-3xl font-fredoka font-bold text-text-main" data-testid="total-orders">
            {earnings?.total_orders || 0}
          </p>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-border-light">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-accent/10 rounded-2xl flex items-center justify-center">
              <Star className="w-6 h-6 text-accent" />
            </div>
            <p className="text-sm text-text-muted">Average Rating</p>
          </div>
          <p className="text-3xl font-fredoka font-bold text-text-main" data-testid="avg-rating">
            {earnings?.average_rating || 0} 
            <span className="text-lg text-text-muted">/5</span>
          </p>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-border-light">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-secondary/10 rounded-2xl flex items-center justify-center">
              <Star className="w-6 h-6 text-secondary" />
            </div>
            <p className="text-sm text-text-muted">Total Reviews</p>
          </div>
          <p className="text-3xl font-fredoka font-bold text-text-main" data-testid="total-reviews">
            {earnings?.total_reviews || 0}
          </p>
        </div>
      </div>
    </div>
  );
};

const ChefDashboard = () => {
  const { user, logout } = useAuth();
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
                to="/chef"
                data-testid="nav-menu"
                className="text-text-main hover:text-primary font-medium transition-colors"
              >
                Menu
              </Link>
              <Link
                to="/chef/orders"
                data-testid="nav-orders"
                className="text-text-main hover:text-primary font-medium transition-colors"
              >
                Orders
              </Link>
              <Link
                to="/chef/earnings"
                data-testid="nav-earnings"
                className="text-text-main hover:text-primary font-medium transition-colors"
              >
                Earnings
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
          <h1 className="text-3xl font-fredoka font-bold text-text-main mb-2">Chef Dashboard</h1>
          <p className="text-text-muted">Welcome back, {user?.name}!</p>
        </div>

        <Routes>
          <Route index element={<ChefMenu />} />
          <Route path="orders" element={<ChefOrders />} />
          <Route path="earnings" element={<ChefEarnings />} />
        </Routes>
      </main>
    </div>
  );
};

export default ChefDashboard;
