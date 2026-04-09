import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, DollarSign, Package, Bell, RefreshCw, Settings, 
  LogOut, TrendingUp, AlertTriangle, CheckCircle, XCircle,
  Search, ChevronRight, Activity, Zap, Brain, Clock
} from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api/admin';

// Auth helper
const getAuthHeader = () => {
  const token = localStorage.getItem('adminToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// ============ LOGIN PAGE ============
function AdminLogin({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const resp = await axios.post(`${API_URL}/login`, { email, password });
      localStorage.setItem('adminToken', resp.data.token);
      localStorage.setItem('adminUser', JSON.stringify(resp.data.admin));
      onLogin(resp.data.admin);
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="bg-gray-800 p-8 rounded-lg shadow-xl w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white">Drops Curated</h1>
          <p className="text-gray-400 mt-2">Admin Panel</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-amber-500"
              placeholder="admin@dropscurated.com"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-amber-500"
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <div className="text-red-400 text-sm bg-red-900/20 p-3 rounded">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-amber-600 hover:bg-amber-500 text-white font-medium rounded transition-colors disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-gray-500 text-xs mt-6">
          Default: admin@dropscurated.com / DropsCurated2024!
        </p>
      </div>
    </div>
  );
}

// ============ STAT CARD ============
function StatCard({ icon: Icon, label, value, subvalue, color = 'amber' }) {
  const colors = {
    amber: 'bg-amber-500/10 text-amber-500',
    green: 'bg-green-500/10 text-green-500',
    blue: 'bg-blue-500/10 text-blue-500',
    purple: 'bg-purple-500/10 text-purple-500',
    red: 'bg-red-500/10 text-red-500'
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg">
      <div className="flex items-center gap-3 mb-4">
        <div className={`p-2 rounded-lg ${colors[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <span className="text-gray-400 text-sm">{label}</span>
      </div>
      <div className="text-3xl font-bold text-white">{value}</div>
      {subvalue && <div className="text-sm text-gray-500 mt-1">{subvalue}</div>}
    </div>
  );
}

// ============ DASHBOARD ============
function Dashboard({ stats, onRefresh }) {
  if (!stats) return <div className="text-gray-400">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Dashboard Overview</h2>
        <button
          onClick={onRefresh}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-sm transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Users}
          label="Active Subscribers"
          value={stats.subscribers?.active || 0}
          subvalue={`${stats.subscribers?.new_this_month || 0} new this month`}
          color="green"
        />
        <StatCard
          icon={DollarSign}
          label="Monthly Revenue"
          value={`₹${(stats.revenue?.monthly || 0).toLocaleString()}`}
          subvalue={`₹${stats.revenue?.per_subscriber || 399} per subscriber`}
          color="amber"
        />
        <StatCard
          icon={Package}
          label="Total Products"
          value={(stats.products?.total || 0).toLocaleString()}
          subvalue={`${stats.products?.classification_rate || 0}% classified`}
          color="blue"
        />
        <StatCard
          icon={Bell}
          label="Alerts This Week"
          value={stats.alerts?.this_week || 0}
          subvalue={`${stats.alerts?.price_drops_detected || 0} price drops detected`}
          color="purple"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <QuickAction icon={RefreshCw} label="Trigger Scrape" action="scrape" />
          <QuickAction icon={Brain} label="Run Classification" action="classify" />
          <QuickAction icon={Activity} label="View Logs" action="logs" />
          <QuickAction icon={Settings} label="Settings" action="settings" />
        </div>
      </div>
    </div>
  );
}

function QuickAction({ icon: Icon, label, action }) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      if (action === 'scrape') {
        await axios.post(`${API_URL}/scraper/trigger`, {}, { headers: getAuthHeader() });
        alert('Scrape triggered!');
      } else if (action === 'classify') {
        await axios.post(`${API_URL}/classification/run?limit=1000`, {}, { headers: getAuthHeader() });
        alert('Classification started!');
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Action failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="flex items-center gap-2 px-4 py-3 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-sm transition-colors disabled:opacity-50"
    >
      <Icon className="w-4 h-4" />
      {loading ? 'Processing...' : label}
    </button>
  );
}

// ============ SUBSCRIBERS LIST ============
function SubscribersList() {
  const [subscribers, setSubscribers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('active');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetchSubscribers();
  }, [page, status]);

  const fetchSubscribers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, limit: 20, status });
      if (search) params.append('search', search);
      
      const resp = await axios.get(`${API_URL}/subscribers?${params}`, { headers: getAuthHeader() });
      setSubscribers(resp.data.subscribers);
      setTotal(resp.data.total);
    } catch (err) {
      console.error('Failed to fetch subscribers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchSubscribers();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Subscribers ({total})</h2>
        <div className="flex gap-2">
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm"
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="all">All</option>
          </select>
        </div>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by phone, name, or email..."
          className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-amber-500"
        />
        <button type="submit" className="px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded text-white">
          <Search className="w-4 h-4" />
        </button>
      </form>

      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="px-4 py-3 text-left text-xs text-gray-400 uppercase">Phone</th>
              <th className="px-4 py-3 text-left text-xs text-gray-400 uppercase">Name</th>
              <th className="px-4 py-3 text-left text-xs text-gray-400 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs text-gray-400 uppercase">Expires</th>
              <th className="px-4 py-3 text-left text-xs text-gray-400 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : subscribers.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">No subscribers found</td></tr>
            ) : (
              subscribers.map((sub, idx) => (
                <tr key={idx} className="border-t border-gray-700 hover:bg-gray-700/50">
                  <td className="px-4 py-3 text-white font-mono">{sub.phone}</td>
                  <td className="px-4 py-3 text-gray-300">{sub.name || '-'}</td>
                  <td className="px-4 py-3">
                    {sub.isActive && sub.isPaid ? (
                      <span className="flex items-center gap-1 text-green-400 text-sm">
                        <CheckCircle className="w-4 h-4" /> Active
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-gray-500 text-sm">
                        <XCircle className="w-4 h-4" /> Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-sm">
                    {sub.expiresAt ? new Date(sub.expiresAt).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <button className="text-amber-500 hover:text-amber-400 text-sm">
                      View <ChevronRight className="w-3 h-3 inline" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center text-sm text-gray-400">
        <span>Showing {subscribers.length} of {total}</span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded disabled:opacity-50"
          >
            Previous
          </button>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={subscribers.length < 20}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

// ============ BRANDS MANAGEMENT ============
function BrandsManager() {
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBrands();
  }, []);

  const fetchBrands = async () => {
    setLoading(true);
    try {
      const resp = await axios.get(`${API_URL}/brands`, { headers: getAuthHeader() });
      setBrands(resp.data.brands);
    } catch (err) {
      console.error('Failed to fetch brands:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleBrand = async (brandKey) => {
    try {
      await axios.post(`${API_URL}/brands/${brandKey}/toggle`, {}, { headers: getAuthHeader() });
      fetchBrands();
    } catch (err) {
      alert('Failed to toggle brand');
    }
  };

  const triggerScrape = async (brandKey) => {
    try {
      await axios.post(`${API_URL}/scraper/trigger/${brandKey}`, {}, { headers: getAuthHeader() });
      alert(`Scrape triggered for ${brandKey}`);
    } catch (err) {
      alert('Failed to trigger scrape');
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-white">Brands ({brands.length})</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="text-gray-500">Loading...</div>
        ) : (
          brands.map((brand, idx) => (
            <div key={idx} className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-white font-medium">{brand.name}</h3>
                <span className={`text-xs px-2 py-1 rounded ${brand.isActive !== false ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                  {brand.isActive !== false ? 'Active' : 'Disabled'}
                </span>
              </div>
              <div className="text-sm text-gray-400 mb-3">
                <p>{brand.productCount || 0} products</p>
                {brand.lastScrapedAt && (
                  <p className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Last scraped: {new Date(brand.lastScrapedAt).toLocaleString()}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => triggerScrape(brand.key)}
                  className="flex-1 px-3 py-2 bg-amber-600 hover:bg-amber-500 rounded text-white text-sm"
                >
                  Scrape Now
                </button>
                <button
                  onClick={() => toggleBrand(brand.key)}
                  className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-sm"
                >
                  {brand.isActive !== false ? 'Disable' : 'Enable'}
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ============ AI CLASSIFICATION STATS ============
function ClassificationStats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const resp = await axios.get(`${API_URL}/classification/stats`, { headers: getAuthHeader() });
      setStats(resp.data);
    } catch (err) {
      console.error('Failed to fetch classification stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const triggerClassification = async () => {
    try {
      await axios.post(`${API_URL}/classification/run?limit=2000`, {}, { headers: getAuthHeader() });
      alert('Classification job started for 2000 products!');
    } catch (err) {
      alert('Failed to start classification');
    }
  };

  if (loading) return <div className="text-gray-500">Loading...</div>;
  if (!stats) return <div className="text-gray-500">No data available</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">AI Classification</h2>
        <button
          onClick={triggerClassification}
          className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded text-white text-sm"
        >
          <Brain className="w-4 h-4" />
          Classify 2000 Products
        </button>
      </div>

      {/* Progress */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <div className="flex items-center justify-between mb-2">
          <span className="text-gray-400">Classification Progress</span>
          <span className="text-white font-bold">{stats.percentage}%</span>
        </div>
        <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
          <div 
            className="h-full bg-amber-500 transition-all duration-500"
            style={{ width: `${stats.percentage}%` }}
          />
        </div>
        <div className="flex justify-between text-sm text-gray-500 mt-2">
          <span>{stats.classified.toLocaleString()} classified</span>
          <span>{stats.unclassified.toLocaleString()} remaining</span>
        </div>
      </div>

      {/* Breakdowns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-white font-medium mb-4">By Category</h3>
          {Object.entries(stats.by_category || {}).map(([cat, count]) => (
            <div key={cat} className="flex items-center justify-between py-2 border-b border-gray-700 last:border-0">
              <span className="text-gray-400">{cat}</span>
              <span className="text-white">{count.toLocaleString()}</span>
            </div>
          ))}
        </div>
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-white font-medium mb-4">By Gender</h3>
          {Object.entries(stats.by_gender || {}).map(([gender, count]) => (
            <div key={gender} className="flex items-center justify-between py-2 border-b border-gray-700 last:border-0">
              <span className="text-gray-400">{gender}</span>
              <span className="text-white">{count.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============ MAIN ADMIN PANEL ============
export default function AdminPanel() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if already logged in
    const savedUser = localStorage.getItem('adminUser');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
      fetchStats();
    }
  }, []);

  const fetchStats = async () => {
    try {
      const resp = await axios.get(`${API_URL}/stats/overview`, { headers: getAuthHeader() });
      setStats(resp.data);
    } catch (err) {
      if (err.response?.status === 401) {
        handleLogout();
      }
    }
  };

  const handleLogin = (userData) => {
    setUser(userData);
    fetchStats();
  };

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminUser');
    setUser(null);
  };

  if (!user) {
    return <AdminLogin onLogin={handleLogin} />;
  }

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'subscribers', label: 'Subscribers', icon: Users },
    { id: 'brands', label: 'Brands', icon: Package },
    { id: 'classification', label: 'AI Classification', icon: Brain },
  ];

  return (
    <div className="min-h-screen bg-gray-900 flex">
      {/* Sidebar */}
      <div className="w-64 bg-gray-800 p-4 flex flex-col">
        <div className="mb-8">
          <h1 className="text-xl font-bold text-white">Drops Curated</h1>
          <p className="text-gray-500 text-sm">Admin Panel</p>
        </div>

        <nav className="flex-1 space-y-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                activeTab === tab.id
                  ? 'bg-amber-600 text-white'
                  : 'text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="border-t border-gray-700 pt-4 mt-4">
          <div className="text-sm text-gray-400 mb-2">{user.email}</div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-gray-400 hover:text-white text-sm"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-8 overflow-y-auto">
        {activeTab === 'dashboard' && <Dashboard stats={stats} onRefresh={fetchStats} />}
        {activeTab === 'subscribers' && <SubscribersList />}
        {activeTab === 'brands' && <BrandsManager />}
        {activeTab === 'classification' && <ClassificationStats />}
      </div>
    </div>
  );
}
