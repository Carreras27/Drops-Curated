import React, { useState, useEffect, useCallback } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ExternalLink, Package, TrendingUp, RefreshCw, Search, X } from 'lucide-react';
import { Header, Footer } from './LandingPage';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

// Single Brand Page Component
export function BrandPage() {
  const { brandKey } = useParams();
  const navigate = useNavigate();
  const [brand, setBrand] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [totalProducts, setTotalProducts] = useState(0);

  useEffect(() => {
    fetchBrandDetails();
    fetchProducts(1, '');
  }, [brandKey]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery !== '') {
        fetchProducts(1, searchQuery);
      } else {
        fetchProducts(1, '');
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const fetchBrandDetails = async () => {
    try {
      const resp = await axios.get(`${API_URL}/scrape/status`);
      const brands = resp.data.brands || [];
      const found = brands.find(b => 
        b.storeKey === brandKey || 
        b.key === brandKey.toLowerCase() ||
        b.store_key === brandKey
      );
      setBrand(found);
    } catch (err) {
      console.error('Failed to fetch brand details');
    }
  };

  const fetchProducts = async (pageNum, query = '') => {
    if (pageNum === 1) setLoading(true);
    else setLoadingMore(true);
    setIsSearching(query !== '');
    
    try {
      // Build query params - always filter by store (brand), optionally add search query
      let url = `${API_URL}/search?store=${brandKey}&limit=24&skip=${(pageNum - 1) * 24}&sort=date`;
      if (query.trim()) {
        url = `${API_URL}/brand-search?store=${brandKey}&q=${encodeURIComponent(query.trim())}&limit=24&skip=${(pageNum - 1) * 24}&sort=date`;
      }
      
      const resp = await axios.get(url);
      const newProducts = resp.data.products || [];
      
      if (pageNum === 1) {
        setProducts(newProducts);
        setTotalProducts(resp.data.total || newProducts.length);
      } else {
        setProducts(prev => [...prev, ...newProducts]);
      }
      
      setHasMore(newProducts.length === 24);
      setPage(pageNum);
    } catch (err) {
      console.error('Failed to fetch products');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
  };

  const loadMore = () => {
    if (!loadingMore && hasMore) {
      fetchProducts(page + 1, searchQuery);
    }
  };

  // Infinite scroll
  useEffect(() => {
    const handleScroll = () => {
      if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
        loadMore();
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [page, loadingMore, hasMore, searchQuery]);

  return (
    <div className="min-h-screen bg-background text-primary">
      <Header />
      
      <main className="pt-24 pb-16">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          {/* Back Button */}
          <button 
            onClick={() => navigate('/brands')}
            className="flex items-center gap-2 text-sm text-primary/50 hover:text-accent transition-colors mb-8"
          >
            <ArrowLeft className="w-4 h-4" />
            All Brands
          </button>

          {/* Brand Header */}
          {brand && (
            <div className="mb-8 pb-8 border-b border-primary/10">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                <div>
                  <div className="w-20 h-20 bg-gradient-to-br from-accent/20 to-primary/10 rounded-full flex items-center justify-center mb-4">
                    <span className="text-3xl font-bold text-accent">
                      {brand.name?.charAt(0) || '?'}
                    </span>
                  </div>
                  <h1 className="font-serif text-4xl md:text-5xl mb-2">{brand.name}</h1>
                  <p className="text-primary/50 flex items-center gap-4">
                    <span className="flex items-center gap-1.5">
                      <Package className="w-4 h-4" />
                      {brand.productCount || products.length} products
                    </span>
                    {brand.lastScrapedAt && (
                      <span className="flex items-center gap-1.5">
                        <RefreshCw className="w-4 h-4" />
                        Updated {new Date(brand.lastScrapedAt).toLocaleDateString()}
                      </span>
                    )}
                  </p>
                </div>
                <a
                  href={brand.websiteUrl || brand.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-background text-sm font-medium hover:bg-accent transition-colors"
                >
                  Visit Official Store
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          )}

          {/* Search Bar within Brand */}
          <div className="mb-8">
            <div className="relative max-w-2xl">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-primary/30" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={`Search within ${brand?.name || 'this brand'}...`}
                className="w-full pl-12 pr-12 py-4 bg-surface border border-primary/10 text-sm placeholder:text-primary/30 focus:outline-none focus:border-accent transition-colors"
                data-testid="brand-search-input"
              />
              {searchQuery && (
                <button
                  onClick={clearSearch}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-primary/40 hover:text-primary transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
            {isSearching && (
              <p className="mt-3 text-sm text-primary/50">
                {loading ? 'Searching...' : `Found ${totalProducts} results for "${searchQuery}" in ${brand?.name}`}
              </p>
            )}
          </div>

          {/* Products Grid */}
          {loading ? (
            <div className="flex justify-center py-24">
              <RefreshCw className="w-6 h-6 animate-spin text-primary/30" />
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
                {products.map((product, idx) => (
                  <Link
                    key={product.id}
                    to={`/product/${product.id}`}
                    className="group animate-fade-up"
                    style={{ animationDelay: `${(idx % 24) * 0.03}s` }}
                  >
                    <div className="aspect-square overflow-hidden bg-white mb-3 border border-primary/5">
                      <img
                        src={product.imageUrl}
                        alt={product.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        loading="lazy"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    </div>
                    <p className="text-[10px] uppercase tracking-wider text-accent mb-1">{product.brand}</p>
                    <h3 className="text-sm font-medium line-clamp-2 group-hover:text-accent transition-colors mb-1">
                      {product.name}
                    </h3>
                    <p className="text-sm font-semibold">
                      ₹{(product.lowestPrice || product.price)?.toLocaleString('en-IN')}
                    </p>
                  </Link>
                ))}
              </div>

              {/* Loading More */}
              {loadingMore && (
                <div className="flex justify-center py-12">
                  <RefreshCw className="w-5 h-5 animate-spin text-primary/30" />
                </div>
              )}

              {/* No More Products */}
              {!hasMore && products.length > 0 && (
                <p className="text-center text-primary/30 text-sm py-12">
                  You've seen all {products.length} products from {brand?.name}
                </p>
              )}
            </>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}

// All Brands Page Component
export default function BrandsPage() {
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBrands();
  }, []);

  const fetchBrands = async () => {
    try {
      const resp = await axios.get(`${API_URL}/scrape/status`);
      // Sort by product count descending
      const sortedBrands = (resp.data.brands || []).sort((a, b) => 
        (b.productCount || 0) - (a.productCount || 0)
      );
      setBrands(sortedBrands);
    } catch (err) {
      console.error('Failed to fetch brands');
    } finally {
      setLoading(false);
    }
  };

  const totalProducts = brands.reduce((sum, b) => sum + (b.productCount || 0), 0);

  return (
    <div className="min-h-screen bg-background text-primary">
      <Header />
      
      <main className="pt-24 pb-16">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          {/* Page Header */}
          <div className="text-center mb-16">
            <p className="text-[10px] uppercase tracking-[0.3em] text-accent mb-4">Shop By Store</p>
            <h1 className="font-serif text-4xl md:text-6xl mb-4">All Brands</h1>
            <p className="text-primary/50 text-sm">
              {brands.length} premium Indian streetwear brands • {totalProducts.toLocaleString()} products tracked
            </p>
          </div>

          {/* Brands Grid */}
          {loading ? (
            <div className="flex justify-center py-24">
              <RefreshCw className="w-6 h-6 animate-spin text-primary/30" />
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6">
              {brands.map((brand, idx) => (
                <Link
                  key={brand.key}
                  to={`/brands/${brand.storeKey || brand.key?.toUpperCase()}`}
                  className="group animate-fade-up bg-gradient-to-br from-primary/[0.02] to-accent/[0.02] border border-primary/10 hover:border-accent/40 p-6 transition-all duration-300 hover:-translate-y-2 hover:shadow-xl"
                  style={{ animationDelay: `${idx * 0.05}s` }}
                >
                  <div className="text-center">
                    {/* Brand Initial */}
                    <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-accent/10 to-primary/5 rounded-full flex items-center justify-center group-hover:from-accent/20 group-hover:to-accent/10 transition-all duration-300">
                      <span className="text-2xl font-bold text-primary/50 group-hover:text-accent transition-colors">
                        {brand.name?.charAt(0) || '?'}
                      </span>
                    </div>
                    
                    {/* Brand Name */}
                    <h3 className="font-medium text-base mb-2 group-hover:text-accent transition-colors">
                      {brand.name}
                    </h3>
                    
                    {/* Product Count */}
                    <p className="text-xs text-primary/40 mb-3">
                      {brand.productCount || 0} drops
                    </p>
                    
                    {/* Stats Bar */}
                    <div className="h-1 bg-primary/5 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-accent/40 group-hover:bg-accent transition-colors"
                        style={{ 
                          width: `${Math.min(100, ((brand.productCount || 0) / Math.max(...brands.map(b => b.productCount || 1))) * 100)}%` 
                        }}
                      />
                    </div>
                    
                    {/* Visit Store Link */}
                    <a
                      href={brand.websiteUrl || brand.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-1 mt-4 text-[10px] text-primary/30 hover:text-accent transition-colors"
                    >
                      <ExternalLink className="w-3 h-3" />
                      <span>Official Site</span>
                    </a>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
