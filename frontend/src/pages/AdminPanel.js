import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, DollarSign, Package, Bell, RefreshCw, Settings, 
  LogOut, TrendingUp, AlertTriangle, CheckCircle, XCircle,
  Search, ChevronRight, Activity, Zap, Brain, Clock, 
  Shield, Wifi, WifiOff, AlertCircle, Play, RotateCcw,
  Heart, Send, BarChart3, Eye, Database, Globe, Server,
  MessageSquare, UserCheck, UserX, IndianRupee
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

// ============ SCRAPER HEALTH DASHBOARD ============
function ScraperHealthDashboard() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [retrying, setRetrying] = useState({});

  useEffect(() => {
    fetchHealth();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchHealth = async () => {
    try {
      const resp = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/admin/scraper-health`);
      setHealth(resp.data);
    } catch (err) {
      console.error('Failed to fetch scraper health:', err);
    } finally {
      setLoading(false);
    }
  };

  const triggerScrape = async (brandKey) => {
    setRetrying(prev => ({ ...prev, [brandKey]: true }));
    try {
      await axios.post(`${API_URL}/scraper/trigger/${brandKey}`, {}, { headers: getAuthHeader() });
      // Refresh after 3 seconds
      setTimeout(fetchHealth, 3000);
    } catch (err) {
      alert(`Failed to trigger scrape for ${brandKey}`);
    } finally {
      setTimeout(() => setRetrying(prev => ({ ...prev, [brandKey]: false })), 2000);
    }
  };

  const triggerFullScrape = async () => {
    try {
      await axios.post(`${API_URL}/scraper/trigger`, {}, { headers: getAuthHeader() });
      alert('Full scrape cycle triggered!');
      setTimeout(fetchHealth, 5000);
    } catch (err) {
      alert('Failed to trigger full scrape');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  if (!health) {
    return <div className="text-gray-500">Failed to load scraper health data</div>;
  }

  const getStatusColor = (scraper) => {
    if (scraper.is_blocked) return 'red';
    if (scraper.consecutive_failures > 0) return 'yellow';
    if (scraper.success_rate >= 80) return 'green';
    if (scraper.success_rate >= 50) return 'yellow';
    return 'gray';
  };

  const getStatusIcon = (scraper) => {
    if (scraper.is_blocked) return <XCircle className="w-5 h-5 text-red-500" />;
    if (scraper.consecutive_failures > 0) return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    if (scraper.last_success) return <CheckCircle className="w-5 h-5 text-green-500" />;
    return <Clock className="w-5 h-5 text-gray-500" />;
  };

  const formatTime = (isoString) => {
    if (!isoString) return 'Never';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Shield className="w-6 h-6 text-amber-500" />
            Scraper Health Dashboard
          </h2>
          <p className="text-gray-500 text-sm mt-1">LLM-powered self-healing system monitoring</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchHealth}
            className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-sm transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={triggerFullScrape}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded text-white text-sm transition-colors"
          >
            <Play className="w-4 h-4" />
            Scrape All
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg text-center">
          <div className="text-3xl font-bold text-white">{health.summary.total_brands}</div>
          <div className="text-gray-500 text-sm">Total Brands</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg text-center">
          <div className="text-3xl font-bold text-green-400">{health.summary.healthy}</div>
          <div className="text-gray-500 text-sm">Healthy</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg text-center">
          <div className="text-3xl font-bold text-yellow-400">{health.summary.degraded}</div>
          <div className="text-gray-500 text-sm">Degraded</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg text-center">
          <div className="text-3xl font-bold text-red-400">{health.summary.blocked}</div>
          <div className="text-gray-500 text-sm">Blocked</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg text-center">
          <div className="text-3xl font-bold text-amber-400">{health.summary.average_success_rate}%</div>
          <div className="text-gray-500 text-sm">Avg Success</div>
        </div>
      </div>

      {/* System Status */}
      <div className="bg-gray-800 p-4 rounded-lg flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`w-3 h-3 rounded-full ${
            health.system_health?.status === 'healthy' ? 'bg-green-500 animate-pulse' :
            health.system_health?.status === 'degraded' ? 'bg-yellow-500 animate-pulse' :
            'bg-red-500 animate-pulse'
          }`} />
          <div>
            <span className="text-white font-medium">System Status: </span>
            <span className={`font-bold ${
              health.system_health?.status === 'healthy' ? 'text-green-400' :
              health.system_health?.status === 'degraded' ? 'text-yellow-400' :
              'text-red-400'
            }`}>
              {health.system_health?.status?.toUpperCase() || 'UNKNOWN'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            {health.system_health?.db_healthy ? 
              <CheckCircle className="w-4 h-4 text-green-500" /> : 
              <XCircle className="w-4 h-4 text-red-500" />}
            <span className="text-gray-400">Database</span>
          </div>
          <div className="flex items-center gap-2">
            {health.system_health?.scraper_healthy ? 
              <CheckCircle className="w-4 h-4 text-green-500" /> : 
              <XCircle className="w-4 h-4 text-red-500" />}
            <span className="text-gray-400">Scraper</span>
          </div>
          <div className="flex items-center gap-2">
            {health.agent?.llm_enabled ? 
              <Brain className="w-4 h-4 text-green-500" /> : 
              <Brain className="w-4 h-4 text-gray-500" />}
            <span className="text-gray-400">LLM Healer</span>
          </div>
        </div>
      </div>

      {/* Scrapers Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {health.scrapers.map((scraper) => {
          const statusColor = getStatusColor(scraper);
          const borderColor = {
            green: 'border-green-500/30',
            yellow: 'border-yellow-500/30',
            red: 'border-red-500/30',
            gray: 'border-gray-600'
          }[statusColor];
          
          return (
            <div 
              key={scraper.brand_key} 
              className={`bg-gray-800 rounded-lg border-l-4 ${borderColor} p-4`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  {getStatusIcon(scraper)}
                  <h3 className="text-white font-medium">{scraper.brand_name}</h3>
                </div>
                {scraper.is_blocked && (
                  <span className="px-2 py-1 bg-red-500/20 text-red-400 text-xs rounded-full">
                    BLOCKED
                  </span>
                )}
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Success Rate</span>
                  <span className={`font-medium ${
                    scraper.success_rate >= 80 ? 'text-green-400' :
                    scraper.success_rate >= 50 ? 'text-yellow-400' :
                    'text-gray-400'
                  }`}>
                    {scraper.success_rate}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Products Found</span>
                  <span className="text-white">{scraper.products_found.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Last Success</span>
                  <span className="text-gray-400">{formatTime(scraper.last_success)}</span>
                </div>
                {scraper.consecutive_failures > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Failures</span>
                    <span className="text-red-400">{scraper.consecutive_failures} consecutive</span>
                  </div>
                )}
                {scraper.last_error && (
                  <div className="mt-2 p-2 bg-red-500/10 rounded text-red-400 text-xs truncate">
                    {scraper.last_error}
                  </div>
                )}
              </div>

              <button
                onClick={() => triggerScrape(scraper.brand_key)}
                disabled={retrying[scraper.brand_key]}
                className={`mt-3 w-full flex items-center justify-center gap-2 px-3 py-2 rounded text-sm transition-colors ${
                  scraper.is_blocked 
                    ? 'bg-red-600 hover:bg-red-500 text-white' 
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                }`}
              >
                {retrying[scraper.brand_key] ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                    Retrying...
                  </>
                ) : (
                  <>
                    <RotateCcw className="w-4 h-4" />
                    {scraper.is_blocked ? 'Force Retry' : 'Scrape Now'}
                  </>
                )}
              </button>
            </div>
          );
        })}
      </div>

      {/* Agent Stats */}
      {health.agent && (
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-amber-500" />
            Self-Healing Agent Statistics
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-gray-500">Total Attempts</div>
              <div className="text-white text-lg font-bold">{health.agent.total_attempts || 0}</div>
            </div>
            <div>
              <div className="text-gray-500">Successful Heals</div>
              <div className="text-green-400 text-lg font-bold">{health.agent.successful_heals || 0}</div>
            </div>
            <div>
              <div className="text-gray-500">Success Rate</div>
              <div className="text-amber-400 text-lg font-bold">{health.agent.success_rate || 0}%</div>
            </div>
            <div>
              <div className="text-gray-500">Currently Healing</div>
              <div className="text-blue-400 text-lg font-bold">{health.agent.brands_currently_healing?.length || 0}</div>
            </div>
          </div>
          
          {/* Top Strategies */}
          {health.agent.top_strategies?.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-700">
              <div className="text-gray-400 text-sm mb-2">Top Working Strategies:</div>
              <div className="flex flex-wrap gap-2">
                {health.agent.top_strategies.map((s, i) => (
                  <span key={i} className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded">
                    {s.strategy}: {s.successes} wins
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Recent Activity */}
          {health.agent.recent_activity?.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-700">
              <div className="text-gray-400 text-sm mb-2">Recent Activity:</div>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {health.agent.recent_activity.slice(0, 5).map((a, i) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <span className="text-gray-400">{a.brand_key}</span>
                    <span className={a.success ? 'text-green-400' : 'text-red-400'}>
                      {a.strategy} {a.success ? '✓' : '✗'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Last Updated */}
      <div className="text-center text-gray-600 text-xs">
        Last updated: {new Date(health.timestamp).toLocaleString()} • Auto-refreshes every 30s
      </div>
    </div>
  );
}

// ============ AGENT LOGS VIEWER ============
function AgentLogsViewer() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedBrand, setSelectedBrand] = useState('');

  useEffect(() => {
    fetchLogs();
  }, [selectedBrand]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: 100 });
      if (selectedBrand) params.append('brand_key', selectedBrand);
      
      const resp = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/admin/agent-logs?${params}`
      );
      setData(resp.data);
    } catch (err) {
      console.error('Failed to fetch agent logs:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  if (!data) return <div className="text-gray-500">Failed to load agent logs</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Brain className="w-6 h-6 text-amber-500" />
            Agent Logs & Strategies
          </h2>
          <p className="text-gray-500 text-sm mt-1">What the LLM agent tried, learned, and remembered</p>
        </div>
        <button
          onClick={fetchLogs}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg text-center">
          <div className="text-3xl font-bold text-white">{data.summary?.total_attempts || 0}</div>
          <div className="text-gray-500 text-sm">Total Attempts</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg text-center">
          <div className="text-3xl font-bold text-green-400">{data.summary?.successful_heals || 0}</div>
          <div className="text-gray-500 text-sm">Successful Heals</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg text-center">
          <div className="text-3xl font-bold text-amber-400">{data.summary?.success_rate || 0}%</div>
          <div className="text-gray-500 text-sm">Success Rate</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg text-center">
          <div className={`text-3xl font-bold ${data.summary?.llm_enabled ? 'text-green-400' : 'text-red-400'}`}>
            {data.summary?.llm_enabled ? 'ON' : 'OFF'}
          </div>
          <div className="text-gray-500 text-sm">LLM Status</div>
        </div>
      </div>

      {/* Proactive Warnings */}
      {data.proactive_warnings?.length > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 p-4 rounded-lg">
          <h3 className="text-yellow-400 font-medium flex items-center gap-2 mb-2">
            <AlertCircle className="w-5 h-5" />
            Proactive Warnings (Response Time Degradation)
          </h3>
          <div className="space-y-2">
            {data.proactive_warnings.map((w, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="text-white">{w.brand_key}</span>
                <span className="text-yellow-400">
                  {w.early_avg_ms}ms → {w.recent_avg_ms}ms ({w.warning})
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Brand Strategies (Confidence Scores) */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-white font-medium mb-4">Learned Strategies (Memory System)</h3>
        {data.brand_strategies?.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.brand_strategies.map((s, i) => (
              <div key={i} className="bg-gray-700 p-3 rounded">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-medium">{s.brand_key}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    s.confidence_score >= 70 ? 'bg-green-500/20 text-green-400' :
                    s.confidence_score >= 40 ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-red-500/20 text-red-400'
                  }`}>
                    {s.confidence_score?.toFixed(0)}% confidence
                  </span>
                </div>
                <div className="text-sm text-gray-400">
                  Strategy: <span className="text-amber-400">{s.strategy}</span>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {s.success_count} wins / {s.failure_count} losses
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-500 text-center py-4">No strategies learned yet</div>
        )}
      </div>

      {/* Filter */}
      <div className="flex items-center gap-4">
        <select
          value={selectedBrand}
          onChange={(e) => setSelectedBrand(e.target.value)}
          className="px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white"
        >
          <option value="">All Brands</option>
          {[...new Set(data.logs?.map(l => l.brand_key) || [])].map(b => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>
      </div>

      {/* Logs Table */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="px-4 py-3 text-left text-xs text-gray-400 uppercase">Time</th>
              <th className="px-4 py-3 text-left text-xs text-gray-400 uppercase">Brand</th>
              <th className="px-4 py-3 text-left text-xs text-gray-400 uppercase">Strategy</th>
              <th className="px-4 py-3 text-left text-xs text-gray-400 uppercase">Result</th>
              <th className="px-4 py-3 text-left text-xs text-gray-400 uppercase">Message</th>
            </tr>
          </thead>
          <tbody>
            {data.logs?.length > 0 ? (
              data.logs.slice(0, 50).map((log, i) => (
                <tr key={i} className="border-t border-gray-700 hover:bg-gray-700/50">
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-white text-sm">{log.brand_key}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 bg-gray-600 text-gray-300 text-xs rounded">
                      {log.strategy}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {log.success ? (
                      <span className="flex items-center gap-1 text-green-400 text-sm">
                        <CheckCircle className="w-4 h-4" /> Success
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-red-400 text-sm">
                        <XCircle className="w-4 h-4" /> Failed
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs max-w-xs truncate">
                    {log.message}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                  No logs yet. Logs appear when scrapers fail and the agent tries to heal them.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============ AETHER MASTER DASHBOARD ============
function AetherMasterDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const resp = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/admin/aether-status`);
      setData(resp.data);
    } catch (err) {
      console.error('Failed to fetch aether status:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const triggerCycle = async () => {
    setRunning(true);
    try {
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/admin/aether-run`);
      setTimeout(fetchStatus, 2000);
    } catch (err) {
      alert('Failed to trigger cycle');
    } finally {
      setTimeout(() => setRunning(false), 2000);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
    </div>
  );

  const current = data?.current || {};
  const components = current.components || {};
  const metrics = current.metrics || {};
  const latencies = current.latencies_ms || {};
  const incidents = current.incidents || [];
  const history = data?.history || [];

  const statusColor = {
    healthy: 'text-green-400',
    degraded: 'text-yellow-400',
    critical: 'text-red-400',
    not_yet_run: 'text-gray-400',
  };

  const statusBg = {
    healthy: 'bg-green-500',
    degraded: 'bg-yellow-500',
    critical: 'bg-red-500',
    not_yet_run: 'bg-gray-500',
  };

  const ComponentCard = ({ name, ok, latency }) => (
    <div className={`bg-gray-800 p-4 rounded-lg border-l-4 ${ok ? 'border-green-500/50' : 'border-red-500/50'}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-white font-medium capitalize">{name}</span>
        {ok ? <CheckCircle className="w-5 h-5 text-green-400" /> : <XCircle className="w-5 h-5 text-red-400" />}
      </div>
      <div className="text-sm text-gray-400">
        {ok ? 'Operational' : 'Down'}
        {latency != null && <span className="ml-2 text-gray-500">({latency}ms)</span>}
      </div>
    </div>
  );

  return (
    <div className="space-y-6" data-testid="aether-master-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Eye className="w-6 h-6 text-cyan-400" />
            AETHER MASTER — Site Guardian
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            Autonomous monitoring every 5 minutes | Cycles: {current.cycles_completed || 0}
          </p>
        </div>
        <button
          onClick={triggerCycle}
          disabled={running}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded text-white text-sm transition-colors disabled:opacity-50"
          data-testid="aether-run-cycle-btn"
        >
          {running ? (
            <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div> Running...</>
          ) : (
            <><Play className="w-4 h-4" /> Run Cycle Now</>
          )}
        </button>
      </div>

      {/* Overall Status */}
      <div className="bg-gray-800 p-5 rounded-lg flex items-center gap-4">
        <div className={`w-4 h-4 rounded-full animate-pulse ${statusBg[current.overall_status] || 'bg-gray-500'}`} />
        <div>
          <span className="text-gray-400">Overall Status: </span>
          <span className={`font-bold text-lg ${statusColor[current.overall_status] || 'text-gray-400'}`}>
            {(current.overall_status || 'NOT YET RUN').toUpperCase()}
          </span>
        </div>
        <div className="ml-auto text-sm text-gray-500">
          {current.timestamp ? new Date(current.timestamp).toLocaleString() : '—'}
        </div>
      </div>

      {/* Component Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <ComponentCard name="MongoDB" ok={components.mongodb} latency={latencies.mongodb_ping} />
        <ComponentCard name="Backend" ok={components.backend} latency={latencies['Backend Health']} />
        <ComponentCard name="Frontend" ok={components.frontend} latency={latencies.frontend} />
        <ComponentCard name="Scrapers" ok={components.scrapers} />
        <ComponentCard name="Scheduler" ok={components.scheduler} />
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg text-center">
          <Database className="w-5 h-5 text-blue-400 mx-auto mb-2" />
          <div className="text-2xl font-bold text-white">{(metrics.total_products || 0).toLocaleString()}</div>
          <div className="text-gray-500 text-xs">Products in DB</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg text-center">
          <Globe className="w-5 h-5 text-green-400 mx-auto mb-2" />
          <div className="text-2xl font-bold text-green-400">{metrics.brands_healthy || 0}</div>
          <div className="text-gray-500 text-xs">Brands Healthy</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg text-center">
          <AlertTriangle className="w-5 h-5 text-red-400 mx-auto mb-2" />
          <div className="text-2xl font-bold text-red-400">{metrics.brands_blocked || 0}</div>
          <div className="text-gray-500 text-xs">Blocked</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg text-center">
          <Server className="w-5 h-5 text-amber-400 mx-auto mb-2" />
          <div className="text-2xl font-bold text-white">{current.auto_heals || 0}</div>
          <div className="text-gray-500 text-xs">Auto-Heals</div>
        </div>
      </div>

      {/* Latency Breakdown */}
      <div className="bg-gray-800 p-5 rounded-lg">
        <h3 className="text-white font-medium mb-3">Endpoint Latencies</h3>
        <div className="space-y-2">
          {Object.entries(latencies).map(([name, ms]) => (
            <div key={name} className="flex items-center gap-3">
              <span className="text-gray-400 text-sm w-36 truncate">{name}</span>
              <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${ms > 3000 ? 'bg-red-500' : ms > 1000 ? 'bg-yellow-500' : 'bg-green-500'}`}
                  style={{ width: `${Math.min(100, (ms / 5000) * 100)}%` }}
                />
              </div>
              <span className={`text-sm font-mono w-16 text-right ${ms > 3000 ? 'text-red-400' : ms > 1000 ? 'text-yellow-400' : 'text-green-400'}`}>
                {ms}ms
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Incidents */}
      {incidents.length > 0 && (
        <div className="bg-gray-800 p-5 rounded-lg">
          <h3 className="text-white font-medium mb-3 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-400" />
            Incidents ({incidents.length})
          </h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {incidents.map((inc, i) => (
              <div key={i} className={`flex items-start gap-3 p-3 rounded ${
                inc.severity === 'critical' ? 'bg-red-500/10' : inc.severity === 'warning' ? 'bg-yellow-500/10' : 'bg-gray-700/50'
              }`}>
                <div className={`w-2 h-2 rounded-full mt-1.5 ${
                  inc.severity === 'critical' ? 'bg-red-500' : inc.severity === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                }`} />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-white text-sm font-medium">[{inc.component}]</span>
                    <span className="text-gray-300 text-sm">{inc.message}</span>
                  </div>
                  {inc.auto_healed && (
                    <span className="text-green-400 text-xs mt-1 block">Auto-healed: {inc.heal_action}</span>
                  )}
                </div>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  inc.severity === 'critical' ? 'bg-red-500/20 text-red-400' : 
                  inc.severity === 'warning' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-blue-500/20 text-blue-400'
                }`}>
                  {inc.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* History Timeline */}
      {history.length > 0 && (
        <div className="bg-gray-800 p-5 rounded-lg">
          <h3 className="text-white font-medium mb-3">Recent Cycles</h3>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {history.slice(0, 15).map((h, i) => (
              <div key={i} className="flex items-center justify-between text-sm py-1.5 border-b border-gray-700/50 last:border-0">
                <span className="text-gray-500 text-xs">{new Date(h.timestamp).toLocaleString()}</span>
                <span className={`font-medium ${
                  h.overall_status === 'healthy' ? 'text-green-400' :
                  h.overall_status === 'degraded' ? 'text-yellow-400' : 'text-red-400'
                }`}>
                  {h.overall_status?.toUpperCase()}
                </span>
                <span className="text-gray-500 text-xs">
                  {(h.incidents?.length || 0)} incidents | {h.auto_heals || 0} heals
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============ CRM DASHBOARD ============
function CRMDashboard() {
  const [tab, setTab] = useState('analytics');
  const [analytics, setAnalytics] = useState(null);
  const [revenue, setRevenue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [broadcastMsg, setBroadcastMsg] = useState('');
  const [sending, setSending] = useState(false);
  const [broadcastResult, setBroadcastResult] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [aResp, rResp] = await Promise.all([
        axios.get(`${API_URL}/crm/analytics`, { headers: getAuthHeader() }),
        axios.get(`${API_URL}/crm/revenue`, { headers: getAuthHeader() }),
      ]);
      setAnalytics(aResp.data);
      setRevenue(rResp.data);
    } catch (err) {
      console.error('CRM fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const sendBroadcast = async () => {
    if (!broadcastMsg.trim() || broadcastMsg.length < 5) {
      alert('Message must be at least 5 characters');
      return;
    }
    if (!window.confirm(`Send this message to ALL active paid subscribers?`)) return;

    setSending(true);
    try {
      const resp = await axios.post(
        `${API_URL}/crm/broadcast?message=${encodeURIComponent(broadcastMsg)}`,
        {},
        { headers: getAuthHeader() },
      );
      setBroadcastResult(resp.data);
      setBroadcastMsg('');
    } catch (err) {
      alert(err.response?.data?.detail || 'Broadcast failed');
    } finally {
      setSending(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
    </div>
  );

  const t = analytics?.totals || {};
  const rev = revenue || {};
  const signups = analytics?.signups_by_day || [];

  const crmTabs = [
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'revenue', label: 'Revenue', icon: IndianRupee },
    { id: 'broadcast', label: 'Broadcast', icon: Send },
  ];

  return (
    <div className="space-y-6" data-testid="crm-dashboard">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Heart className="w-6 h-6 text-pink-400" />
          CRM Dashboard
        </h2>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-sm"
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* CRM Sub-tabs */}
      <div className="flex gap-2 border-b border-gray-700 pb-2">
        {crmTabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-t text-sm transition-colors ${
              tab === t.id ? 'bg-gray-800 text-white border-b-2 border-amber-500' : 'text-gray-400 hover:text-white'
            }`}
          >
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      {/* ── Analytics Tab ── */}
      {tab === 'analytics' && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="bg-gray-800 p-4 rounded-lg text-center">
              <Users className="w-5 h-5 text-blue-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-white">{t.total || 0}</div>
              <div className="text-gray-500 text-xs">Total Subscribers</div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg text-center">
              <UserCheck className="w-5 h-5 text-green-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-green-400">{t.active_paid || 0}</div>
              <div className="text-gray-500 text-xs">Active Paid</div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg text-center">
              <Clock className="w-5 h-5 text-amber-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-amber-400">{t.trial_only || 0}</div>
              <div className="text-gray-500 text-xs">On Trial</div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg text-center">
              <UserX className="w-5 h-5 text-red-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-red-400">{t.expired || 0}</div>
              <div className="text-gray-500 text-xs">Expired</div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg text-center">
              <TrendingUp className="w-5 h-5 text-cyan-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-cyan-400">{t.conversion_rate || 0}%</div>
              <div className="text-gray-500 text-xs">Trial → Paid</div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg text-center">
              <AlertTriangle className="w-5 h-5 text-orange-400 mx-auto mb-2" />
              <div className="text-2xl font-bold text-orange-400">{t.churned_30d || 0}</div>
              <div className="text-gray-500 text-xs">Churned (30d)</div>
            </div>
          </div>

          {/* Signups Chart (bar chart using divs) */}
          {signups.length > 0 && (
            <div className="bg-gray-800 p-5 rounded-lg">
              <h3 className="text-white font-medium mb-4">Signups (Last 30 Days)</h3>
              <div className="flex items-end gap-1 h-40">
                {signups.map((s, i) => {
                  const max = Math.max(...signups.map(x => x.count), 1);
                  const pct = (s.count / max) * 100;
                  return (
                    <div key={i} className="flex-1 flex flex-col items-center group relative">
                      <div
                        className="w-full bg-amber-500/80 rounded-t hover:bg-amber-400 transition-colors min-h-[2px]"
                        style={{ height: `${pct}%` }}
                      />
                      <div className="absolute -top-8 bg-gray-700 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                        {s.date}: {s.count}
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-2">
                <span>{signups[0]?.date}</span>
                <span>{signups[signups.length - 1]?.date}</span>
              </div>
            </div>
          )}

          {/* Preferences */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-800 p-5 rounded-lg">
              <h3 className="text-white font-medium mb-3">Top Categories</h3>
              {(analytics?.top_categories || []).length > 0 ? (
                <div className="space-y-2">
                  {analytics.top_categories.map((c, i) => (
                    <div key={i} className="flex items-center justify-between py-1">
                      <span className="text-gray-300 text-sm">{c.name}</span>
                      <span className="text-amber-400 font-medium text-sm">{c.count}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No preference data yet</p>
              )}
            </div>
            <div className="bg-gray-800 p-5 rounded-lg">
              <h3 className="text-white font-medium mb-3">Popular Shoe Sizes</h3>
              {(analytics?.top_sizes || []).length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {analytics.top_sizes.map((s, i) => (
                    <span key={i} className="px-3 py-1.5 bg-gray-700 text-white text-sm rounded-full">
                      {s.size} <span className="text-gray-400">({s.count})</span>
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No size data yet</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Revenue Tab ── */}
      {tab === 'revenue' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-amber-600/20 to-amber-800/10 border border-amber-500/20 p-5 rounded-lg text-center">
              <div className="text-sm text-amber-300 mb-1">Monthly Revenue (MRR)</div>
              <div className="text-3xl font-bold text-white">{'\u20B9'}{(rev.mrr || 0).toLocaleString()}</div>
            </div>
            <div className="bg-gradient-to-br from-green-600/20 to-green-800/10 border border-green-500/20 p-5 rounded-lg text-center">
              <div className="text-sm text-green-300 mb-1">Annual Run Rate (ARR)</div>
              <div className="text-3xl font-bold text-white">{'\u20B9'}{(rev.arr || 0).toLocaleString()}</div>
            </div>
            <div className="bg-gray-800 p-5 rounded-lg text-center">
              <div className="text-sm text-gray-400 mb-1">Active Paid</div>
              <div className="text-3xl font-bold text-green-400">{rev.active_paid || 0}</div>
            </div>
            <div className="bg-gray-800 p-5 rounded-lg text-center">
              <div className="text-sm text-gray-400 mb-1">Lifetime Paid</div>
              <div className="text-3xl font-bold text-white">{rev.total_ever_paid || 0}</div>
            </div>
          </div>

          {/* Monthly Breakdown */}
          {(rev.monthly_breakdown || []).length > 0 && (
            <div className="bg-gray-800 p-5 rounded-lg">
              <h3 className="text-white font-medium mb-4">Monthly Revenue Breakdown</h3>
              <div className="space-y-3">
                {rev.monthly_breakdown.map((m, i) => (
                  <div key={i} className="flex items-center gap-4">
                    <span className="text-gray-400 text-sm w-24">{m.month}</span>
                    <div className="flex-1 h-3 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-500 rounded-full"
                        style={{
                          width: `${Math.min(100, (m.revenue / Math.max(...rev.monthly_breakdown.map(x => x.revenue), 1)) * 100)}%`,
                        }}
                      />
                    </div>
                    <span className="text-white font-medium text-sm w-24 text-right">
                      {'\u20B9'}{m.revenue.toLocaleString()}
                    </span>
                    <span className="text-gray-500 text-xs w-16 text-right">{m.subscribers} subs</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-gray-800 p-5 rounded-lg text-center text-gray-500 text-sm">
            Price per subscriber: {'\u20B9'}399/month
          </div>
        </div>
      )}

      {/* ── Broadcast Tab ── */}
      {tab === 'broadcast' && (
        <div className="space-y-6">
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-white font-medium mb-4 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-green-400" />
              WhatsApp Broadcast
            </h3>
            <p className="text-gray-400 text-sm mb-4">
              Send a message to all active paid subscribers via WhatsApp.
            </p>
            <textarea
              value={broadcastMsg}
              onChange={(e) => setBroadcastMsg(e.target.value)}
              placeholder="Type your message here... (min 5 characters)"
              rows={4}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-green-500 resize-none"
              data-testid="broadcast-message-input"
            />
            <div className="flex items-center justify-between mt-4">
              <span className="text-gray-500 text-sm">{broadcastMsg.length} characters</span>
              <button
                onClick={sendBroadcast}
                disabled={sending || broadcastMsg.length < 5}
                className="flex items-center gap-2 px-6 py-2.5 bg-green-600 hover:bg-green-500 rounded text-white text-sm transition-colors disabled:opacity-50"
                data-testid="send-broadcast-btn"
              >
                {sending ? (
                  <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div> Sending...</>
                ) : (
                  <><Send className="w-4 h-4" /> Send Broadcast</>
                )}
              </button>
            </div>
          </div>

          {broadcastResult && (
            <div className="bg-green-500/10 border border-green-500/30 p-4 rounded-lg">
              <h4 className="text-green-400 font-medium mb-2">Broadcast Sent</h4>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-white">{broadcastResult.total}</div>
                  <div className="text-gray-500 text-xs">Total Recipients</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-400">{broadcastResult.sent}</div>
                  <div className="text-gray-500 text-xs">Delivered</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-400">{broadcastResult.failed}</div>
                  <div className="text-gray-500 text-xs">Failed</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============ TELEGRAM BOT DASHBOARD ============
// Lets an admin see the current webhook state and re-point the bot at the
// deployed production URL after going live. Without this, the bot keeps
// responding on the last-known URL (usually preview) after a deploy.
function TelegramDashboard() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [url, setUrl] = useState('');
  const [lastResult, setLastResult] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const r = await axios.get(`${API_URL}/telegram/status`, { headers: getAuthHeader() });
      setStatus(r.data);
      const current = r.data?.webhook_info?.result?.url || '';
      if (current) {
        // Trim the /api/telegram/webhook suffix for a cleaner edit target
        setUrl(current.replace(/\/api\/telegram\/webhook\/?$/, ''));
      } else {
        // Fall back to current page origin so one click = "use this host"
        try { setUrl(window.location.origin); } catch { /* noop */ }
      }
    } catch (e) {
      console.error('Failed to fetch telegram status:', e);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const useThisHost = () => {
    try { setUrl(window.location.origin); } catch { /* noop */ }
  };

  const saveWebhook = async () => {
    if (!url.trim()) { alert('Enter a URL first'); return; }
    if (!/^https:\/\//.test(url.trim())) {
      alert('Webhook URL must start with https:// (Telegram requirement)');
      return;
    }
    setSaving(true);
    setLastResult(null);
    try {
      const r = await axios.post(`${API_URL}/telegram/set-webhook`,
        { webhook_url: url.trim() },
        { headers: getAuthHeader() }
      );
      setLastResult(r.data);
      await fetchStatus();
    } catch (e) {
      setLastResult({ ok: false, result: e.response?.data?.detail || String(e) });
    } finally { setSaving(false); }
  };

  const currentUrl = status?.webhook_info?.result?.url;
  const pending = status?.webhook_info?.result?.pending_update_count ?? 0;
  const lastError = status?.webhook_info?.result?.last_error_message;

  return (
    <div className="space-y-6" data-testid="telegram-dashboard">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Send className="w-6 h-6 text-amber-500" />
          Telegram Bot
        </h2>
        <p className="text-gray-500 text-sm mt-1">Re-point the bot webhook after deploy · restart alert delivery</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-amber-500" />
        </div>
      ) : !status ? (
        <div className="bg-red-500/10 border border-red-500/30 p-4 rounded text-red-300 text-sm">
          Failed to load Telegram status.
        </div>
      ) : (
        <>
          {/* Current state */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="text-gray-500 text-xs uppercase tracking-wider mb-1">Bot</div>
              <div className="text-white font-semibold">
                {status.configured ? `@${status.bot_username}` : 'Not configured'}
              </div>
              <div className={`text-xs mt-1 ${status.configured ? 'text-green-400' : 'text-red-400'}`}>
                {status.configured ? '● Token set' : '● No token'}
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="text-gray-500 text-xs uppercase tracking-wider mb-1">Pending updates</div>
              <div className="text-white font-semibold text-2xl tabular-nums">{pending}</div>
              <div className="text-xs text-gray-500 mt-1">Queued messages waiting for delivery</div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="text-gray-500 text-xs uppercase tracking-wider mb-1">Last error</div>
              <div className="text-white font-semibold text-sm break-words">
                {lastError || <span className="text-green-400">None</span>}
              </div>
            </div>
          </div>

          {/* Current webhook */}
          <div className="bg-gray-800 p-4 rounded-lg">
            <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">Current webhook URL</div>
            {currentUrl ? (
              <code className="text-amber-400 text-sm break-all" data-testid="telegram-current-url">{currentUrl}</code>
            ) : (
              <span className="text-red-400 text-sm">No webhook set — bot cannot receive messages</span>
            )}
          </div>

          {/* Re-point form */}
          <div className="bg-gray-800 p-6 rounded-lg space-y-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Point bot at this origin</label>
              <p className="text-gray-500 text-xs mb-3">
                Paste your deployed site URL (e.g. <code className="text-amber-400">https://your-app.emergent.host</code>).
                We'll append <code className="text-amber-400">/api/telegram/webhook</code> automatically.
              </p>
              <div className="flex gap-2">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://your-deployed-url"
                  className="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white text-sm font-mono focus:border-amber-500 focus:outline-none"
                  data-testid="telegram-webhook-url-input"
                />
                <button
                  onClick={useThisHost}
                  type="button"
                  className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-xs whitespace-nowrap"
                  data-testid="telegram-use-this-host-btn"
                  title="Use the URL this admin panel is served from"
                >
                  Use this host
                </button>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={saveWebhook}
                disabled={saving || !url.trim()}
                className="flex items-center gap-2 px-5 py-2.5 bg-amber-600 hover:bg-amber-500 rounded text-white font-medium text-sm transition-colors disabled:opacity-40"
                data-testid="telegram-save-webhook-btn"
              >
                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                {saving ? 'Registering...' : 'Register webhook with Telegram'}
              </button>
              <button
                onClick={fetchStatus}
                type="button"
                className="flex items-center gap-2 px-4 py-2.5 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-sm"
              >
                <RefreshCw className="w-4 h-4" /> Refresh
              </button>
            </div>

            {lastResult && (
              <div className={`mt-3 text-sm p-3 rounded border ${
                lastResult.ok ? 'bg-green-500/10 border-green-500/30 text-green-300' : 'bg-red-500/10 border-red-500/30 text-red-300'
              }`} data-testid="telegram-save-result">
                {lastResult.ok ? '✓ Webhook registered successfully.' : '✗ Failed: '}
                {lastResult.webhook_url && <div className="text-xs font-mono mt-1 break-all">{lastResult.webhook_url}</div>}
                {!lastResult.ok && <div className="text-xs mt-1">{lastResult.result}</div>}
              </div>
            )}
          </div>

          {/* Help */}
          <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-4 text-xs text-gray-400 leading-relaxed">
            <div className="font-medium text-blue-300 mb-1">When to use this</div>
            After every deploy to a new URL (production, custom domain, etc.), hit <b>Register webhook</b> once so Telegram routes bot
            messages to the new backend. Without this, <code>/start</code> commands and account-link codes won't reach your users.
          </div>
        </>
      )}
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
    { id: 'crm', label: 'CRM', icon: Heart },
    { id: 'subscribers', label: 'Subscribers', icon: Users },
    { id: 'brands', label: 'Brands', icon: Package },
    { id: 'telegram', label: 'Telegram', icon: Send },
    { id: 'aether-master', label: 'Aether Master', icon: Eye },
    { id: 'scraper-health', label: 'Scraper Health', icon: Shield },
    { id: 'agent-logs', label: 'Agent Logs', icon: Brain },
    { id: 'classification', label: 'AI Classification', icon: Zap },
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
        {activeTab === 'crm' && <CRMDashboard />}
        {activeTab === 'subscribers' && <SubscribersList />}
        {activeTab === 'brands' && <BrandsManager />}
        {activeTab === 'telegram' && <TelegramDashboard />}
        {activeTab === 'aether-master' && <AetherMasterDashboard />}
        {activeTab === 'scraper-health' && <ScraperHealthDashboard />}
        {activeTab === 'agent-logs' && <AgentLogsViewer />}
        {activeTab === 'classification' && <ClassificationStats />}
      </div>
    </div>
  );
}
