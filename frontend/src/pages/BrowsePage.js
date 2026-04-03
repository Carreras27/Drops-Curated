import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, SlidersHorizontal, X, RefreshCw, ExternalLink, Flame, Sparkles, Clock, AlertTriangle } from 'lucide-react';
import { Header, Footer } from './LandingPage';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const CATEGORIES = ['All', 'SHOES', 'CLOTHES', 'ACCESSORIES'];
const AUTO_REFRESH_INTERVAL = 15 * 60 * 1000; // 15 minutes in ms

// Last Updated Component
const LastUpdatedBadge = ({ lastUpdated, isRefreshing, onRefresh }) => {
  const [timeAgo, setTimeAgo] = useState('');
  
  useEffect(() => {
    const updateTimeAgo = () => {
      if (!lastUpdated) return;
      const now = new Date();
      const diff = Math.floor((now - lastUpdated) / 1000);
      
      if (diff < 60) setTimeAgo('Just now');
      else if (diff < 120) setTimeAgo('1 min ago');
      else if (diff < 3600) setTimeAgo(`${Math.floor(diff / 60)} mins ago`);
      else setTimeAgo(lastUpdated.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }));
    };
    
    updateTimeAgo();
    const timer = setInterval(updateTimeAgo, 30000); // Update every 30 seconds
    return () => clearInterval(timer);
  }, [lastUpdated]);
  
  return (
    <div className="flex items-center gap-3 text-xs text-primary/40">
      <div className="flex items-center gap-1.5">
        <span className={`w-1.5 h-1.5 rounded-full ${isRefreshing ? 'bg-accent animate-pulse' : 'bg-green-500'}`} />
        <span>
          {isRefreshing ? 'Refreshing...' : `Updated ${timeAgo}`}
        </span>
      </div>
      <span className="text-primary/20">·</span>
      <span>Auto-refresh in 15 mins</span>
      <button 
        onClick={onRefresh}
        disabled={isRefreshing}
        className="ml-1 p-1 hover:bg-primary/5 rounded transition-colors disabled:opacity-50"
        title="Refresh now"
      >
        <RefreshCw className={`w-3 h-3 ${isRefreshing ? 'animate-spin' : ''}`} />
      </button>
    </div>
  );
};

// Product Card Component
const ProductCard = ({ product, idx, showDate = false, showStock = false }) => {
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diff = Math.floor((now - date) / (1000 * 60 * 60 * 24));
      if (diff === 0) return 'Today';
      if (diff === 1) return 'Yesterday';
      if (diff < 7) return `${diff} days ago`;
      return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
    } catch {
      return '';
    }
  };

  return (
    <Link
      to={`/product/${product.id}`}
      className="group animate-fade-up"
      style={{ animationDelay: `${Math.min(idx * 0.04, 0.5)}s` }}
      data-testid={`product-card-${product.id}`}
    >
      <div className="aspect-square overflow-hidden mb-3 bg-surface relative">
        <img
          src={product.imageUrl}
          alt={product.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out"
          loading="lazy"
          onError={(e) => { e.target.style.display = 'none'; }}
        />
        {/* Limited Edition Badge */}
        {showStock && product.isLimited && (
          <div className="absolute top-2 left-2 bg-red-500 text-white px-2 py-1 text-[9px] font-bold uppercase tracking-wider flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            {product.stockLimit ? `Only ${product.stockLimit} in India` : 'Limited'}
          </div>
        )}
        {/* Date Badge */}
        {showDate && product.createdAt && (
          <div className="absolute bottom-2 right-2 bg-primary/80 text-background px-2 py-1 text-[9px] font-medium">
            {formatDate(product.createdAt)}
          </div>
        )}
      </div>
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-accent mb-1">{product.brand}</p>
        <h3 className="text-sm font-medium leading-snug line-clamp-2 mb-2 group-hover:text-accent transition-colors duration-200">{product.name}</h3>
        <div className="flex items-baseline gap-2">
          <span className="text-sm font-medium">
            {product.lowestPrice > 0 ? `₹${product.lowestPrice?.toLocaleString('en-IN')}` : '—'}
          </span>
          {product.highestPrice > 0 && product.highestPrice !== product.lowestPrice && (
            <span className="text-xs text-primary/30 line-through">₹{product.highestPrice?.toLocaleString('en-IN')}</span>
          )}
        </div>
        {product.store && (
          <p className="text-[10px] text-primary/30 mt-1">{product.store.replace(/_/g, ' ')}</p>
        )}
      </div>
    </Link>
  );
};

// Section Component
const DropSection = ({ title, icon: Icon, iconColor, products, showDate, showStock, emptyMessage }) => {
  if (!products || products.length === 0) return null;
  
  return (
    <div className="mb-16">
      <div className="flex items-center gap-3 mb-6">
        <div className={`w-8 h-8 flex items-center justify-center ${iconColor}`}>
          <Icon className="w-4 h-4" strokeWidth={2} />
        </div>
        <div>
          <h2 className="font-serif text-2xl">{title}</h2>
          <p className="text-xs text-primary/40">{products.length} drops</p>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-8">
        {products.map((product, idx) => (
          <ProductCard 
            key={product.id} 
            product={product} 
            idx={idx} 
            showDate={showDate}
            showStock={showStock}
          />
        ))}
      </div>
    </div>
  );
};

export default function BrowsePage() {
  const [products, setProducts] = useState([]);
  const [curatedDrops, setCuratedDrops] = useState({ limited_edition: [], trending: [], new_drops: [] });
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [query, setQuery] = useState('');
  const [selectedBrand, setSelectedBrand] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState('curated'); // 'curated' or 'all'

  useEffect(() => {
    fetchBrands();
    fetchCuratedDrops();
    
    // Auto-refresh every 15 minutes
    const refreshTimer = setInterval(() => {
      if (viewMode === 'curated') {
        fetchCuratedDrops(true);
      }
    }, AUTO_REFRESH_INTERVAL);
    
    return () => clearInterval(refreshTimer);
  }, [viewMode]);

  const fetchBrands = async () => {
    try {
      const resp = await axios.get(`${API_URL}/scrape/status`);
      setBrands(resp.data.brands || []);
    } catch {}
  };

  const fetchCuratedDrops = async (isAutoRefresh = false) => {
    if (isAutoRefresh) {
      setIsRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const resp = await axios.get(`${API_URL}/drops/curated`);
      setCuratedDrops(resp.data);
      // Use backend timestamp if available, otherwise use current time
      const serverTime = resp.data.generated_at ? new Date(resp.data.generated_at) : new Date();
      setLastUpdated(serverTime);
    } catch {} finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleManualRefresh = () => {
    fetchCuratedDrops(true);
  };

  const fetchProducts = async (q, brand) => {
    setLoading(true);
    setViewMode('all');
    try {
      let url = `${API_URL}/search?limit=60`;
      if (q) url += `&q=${encodeURIComponent(q)}`;
      else if (brand) url += `&q=${encodeURIComponent(brand)}`;
      else url += '&q=';
      const resp = await axios.get(url);
      setProducts(resp.data.products || []);
    } catch {} finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e?.preventDefault();
    setSelectedBrand(null);
    if (query.trim()) {
      fetchProducts(query);
    } else {
      setViewMode('curated');
      fetchCuratedDrops();
    }
  };

  const handleBrandClick = (brand) => {
    setSelectedBrand(brand);
    setQuery('');
    fetchProducts('', brand.name);
  };

  const clearFilters = () => {
    setSelectedBrand(null);
    setSelectedCategory('All');
    setQuery('');
    setViewMode('curated');
    fetchCuratedDrops();
  };

  const filtered = selectedCategory === 'All'
    ? products
    : products.filter(p => p.category === selectedCategory);

  return (
    <div className="bg-background min-h-screen" data-testid="browse-page">
      <Header />

      <main className="pt-24 pb-16">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          {/* Title */}
          <div className="mb-8">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-3">Explore</p>
            <h1 className="font-serif text-4xl md:text-5xl tracking-tight mb-4">All Drops</h1>
            <LastUpdatedBadge 
              lastUpdated={lastUpdated} 
              isRefreshing={isRefreshing}
              onRefresh={handleManualRefresh}
            />
          </div>

          {/* Search + Filters */}
          <div className="flex flex-col md:flex-row gap-4 mb-8">
            <form onSubmit={handleSearch} className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/30" strokeWidth={1.5} />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search sneakers, brands, styles..."
                className="w-full pl-11 pr-4 py-3 bg-surface border border-primary/10 text-sm placeholder:text-primary/30 focus:outline-none focus:border-accent transition-colors"
                data-testid="search-input"
              />
            </form>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="inline-flex items-center gap-2 border border-primary/10 px-5 py-3 text-sm hover:border-accent transition-colors"
              data-testid="filter-toggle"
            >
              <SlidersHorizontal className="w-4 h-4" strokeWidth={1.5} />
              Filters
            </button>
          </div>

          {/* Filter panel */}
          {showFilters && (
            <div className="mb-8 p-6 border border-primary/10 bg-surface animate-fade-up" data-testid="filter-panel">
              <div className="flex items-center justify-between mb-4">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">Refine</p>
                <button onClick={clearFilters} className="text-xs text-primary/40 hover:text-primary flex items-center gap-1">
                  <X className="w-3 h-3" /> Clear all
                </button>
              </div>

              {/* Brands */}
              <div className="mb-6">
                <p className="text-xs text-primary/50 mb-3">Brands</p>
                <div className="flex flex-wrap gap-2">
                  {brands.map(b => (
                    <button
                      key={b.key}
                      onClick={() => handleBrandClick(b)}
                      className={`text-xs px-4 py-2 border transition-colors ${selectedBrand?.key === b.key ? 'border-accent text-accent bg-accent/5' : 'border-primary/10 text-primary/60 hover:border-primary/30'}`}
                      data-testid={`brand-filter-${b.key}`}
                    >
                      {b.name} ({b.productCount})
                    </button>
                  ))}
                </div>
              </div>

              {/* Categories */}
              <div>
                <p className="text-xs text-primary/50 mb-3">Category</p>
                <div className="flex flex-wrap gap-2">
                  {CATEGORIES.map(c => (
                    <button
                      key={c}
                      onClick={() => setSelectedCategory(c)}
                      className={`text-xs px-4 py-2 border transition-colors ${selectedCategory === c ? 'border-accent text-accent bg-accent/5' : 'border-primary/10 text-primary/60 hover:border-primary/30'}`}
                      data-testid={`category-filter-${c.toLowerCase()}`}
                    >
                      {c === 'All' ? 'All' : c.charAt(0) + c.slice(1).toLowerCase()}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Active filters */}
          {(selectedBrand || selectedCategory !== 'All') && (
            <div className="flex items-center gap-3 mb-6 text-sm">
              <span className="text-primary/40">Showing:</span>
              {selectedBrand && (
                <span className="border border-accent text-accent text-xs uppercase tracking-widest px-3 py-1 rounded-full">
                  {selectedBrand.name}
                </span>
              )}
              {selectedCategory !== 'All' && (
                <span className="border border-primary/20 text-primary/60 text-xs uppercase tracking-widest px-3 py-1 rounded-full">
                  {selectedCategory}
                </span>
              )}
              <button onClick={clearFilters} className="text-xs text-primary/30 hover:text-primary ml-2">Clear</button>
            </div>
          )}

          {/* Content */}
          {loading ? (
            <div className="flex justify-center py-24">
              <RefreshCw className="w-5 h-5 animate-spin text-primary/20" />
            </div>
          ) : viewMode === 'curated' ? (
            <>
              {/* Limited Edition Section */}
              <DropSection
                title="Limited Edition"
                icon={AlertTriangle}
                iconColor="bg-red-500/10 text-red-500"
                products={curatedDrops.limited_edition}
                showStock={true}
                showDate={true}
                emptyMessage="No limited drops right now"
              />

              {/* Trending Section */}
              <DropSection
                title="Trending Now"
                icon={Flame}
                iconColor="bg-orange-500/10 text-orange-500"
                products={curatedDrops.trending}
                showDate={true}
                emptyMessage="No trending drops"
              />

              {/* New Drops Section */}
              <DropSection
                title="New Drops"
                icon={Sparkles}
                iconColor="bg-accent/10 text-accent"
                products={curatedDrops.new_drops}
                showDate={true}
                emptyMessage="No new drops this week"
              />

              {/* If no curated drops, show message */}
              {!curatedDrops.limited_edition?.length && !curatedDrops.trending?.length && !curatedDrops.new_drops?.length && (
                <div className="text-center py-24" data-testid="no-results">
                  <p className="font-serif text-2xl text-primary/30 mb-2">Loading drops...</p>
                  <p className="text-sm text-primary/20">Fresh drops coming soon</p>
                </div>
              )}
            </>
          ) : (
            /* All Products Grid */
            filtered.length > 0 ? (
              <>
                <p className="text-xs text-primary/30 mb-6">{filtered.length} drops</p>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-8" data-testid="products-grid">
                  {filtered.map((product, idx) => (
                    <ProductCard key={product.id} product={product} idx={idx} showDate={true} />
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center py-24" data-testid="no-results">
                <p className="font-serif text-2xl text-primary/30 mb-2">No drops found</p>
                <p className="text-sm text-primary/20">Try adjusting your search or filters</p>
              </div>
            )
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
