import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, Heart, LogOut, Camera, RefreshCw, Store, Filter, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const SearchPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchMode, setSearchMode] = useState('text');
  const [uploadedImage, setUploadedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('SHOES');
  const [brands, setBrands] = useState([]);
  const [scrapeStatus, setScrapeStatus] = useState(null);
  const [scrapingBrand, setScrapingBrand] = useState(null);
  const [selectedBrand, setSelectedBrand] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    fetchBrands();
    fetchFeaturedProducts();
  }, []);

  const fetchBrands = async () => {
    try {
      const resp = await axios.get(`${API_URL}/scrape/status`);
      setScrapeStatus(resp.data);
      setBrands(resp.data.brands || []);
    } catch {}
  };

  const fetchFeaturedProducts = async () => {
    try {
      const resp = await axios.get(`${API_URL}/search?q=jordan&limit=12`);
      if (resp.data.products?.length > 0) {
        setProducts(resp.data.products);
      }
    } catch {}
  };

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setHasSearched(true);
    setSelectedBrand(null);
    try {
      const resp = await axios.get(`${API_URL}/search?q=${encodeURIComponent(query)}&limit=40`);
      setProducts(resp.data.products || []);
      if (resp.data.products.length === 0) toast.info('No products found. Try different keywords!');
    } catch {
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleBrandFilter = async (brand) => {
    setSelectedBrand(brand);
    setLoading(true);
    setHasSearched(true);
    try {
      const resp = await axios.get(`${API_URL}/search?q=${encodeURIComponent(brand.name)}&limit=40`);
      setProducts(resp.data.products || []);
    } catch {
      toast.error('Failed to load brand products');
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshBrand = async (brandKey) => {
    setScrapingBrand(brandKey);
    toast.info('Refreshing products... This may take a moment.');
    try {
      const resp = await axios.post(`${API_URL}/scrape/${brandKey}`);
      if (resp.data.success) {
        toast.success(`Scraped ${resp.data.scraped} products from ${resp.data.brand}`);
        fetchBrands();
      }
    } catch (err) {
      toast.error('Scraping failed');
    } finally {
      setScrapingBrand(null);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { toast.error('Image must be less than 5MB'); return; }
    setUploadedImage(file);
    const reader = new FileReader();
    reader.onloadend = () => setImagePreview(reader.result);
    reader.readAsDataURL(file);
  };

  const handleImageSearch = async () => {
    if (!uploadedImage) { toast.error('Please upload an image first'); return; }
    setLoading(true);
    setHasSearched(true);
    try {
      const formData = new FormData();
      formData.append('image', uploadedImage);
      const resp = await axios.post(`${API_URL}/visual-search?category=${selectedCategory}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setProducts(resp.data.products || []);
      if (resp.data.products.length > 0) {
        toast.success(`Found ${resp.data.products.length} similar products!`);
      } else {
        toast.info('No similar products found. Try a different category.');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Visual search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => { logout(); navigate('/'); };

  return (
    <div className="min-h-screen bg-[#fafafa]" data-testid="search-page">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white border-b border-gray-100 shadow-sm">
        <nav className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/search" className="flex items-center gap-2" data-testid="logo-link">
            <div className="w-7 h-7 bg-black rounded-md flex items-center justify-center">
              <Store className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">IndiaShop</span>
          </Link>

          {/* Search bar in header */}
          <form onSubmit={handleSearch} className="hidden md:flex flex-1 max-w-xl mx-8">
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search sneakers, clothes, brands..."
                className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                data-testid="search-input"
              />
            </div>
          </form>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setSearchMode(searchMode === 'image' ? 'text' : 'image')}
              className={`p-2 rounded-lg transition-colors ${searchMode === 'image' ? 'bg-black text-white' : 'hover:bg-gray-100'}`}
              data-testid="visual-search-toggle"
              title="Visual Search"
            >
              <Camera className="w-5 h-5" />
            </button>
            <Link to="/watchlist" className="p-2 rounded-lg hover:bg-gray-100" data-testid="watchlist-link">
              <Heart className="w-5 h-5" />
            </Link>
            <button onClick={handleLogout} className="p-2 rounded-lg hover:bg-gray-100" data-testid="logout-btn">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Mobile Search */}
        <form onSubmit={handleSearch} className="md:hidden mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search sneakers, clothes, brands..."
              className="w-full pl-10 pr-4 py-3 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black"
              data-testid="mobile-search-input"
            />
          </div>
        </form>

        {/* Visual Search Panel */}
        {searchMode === 'image' && (
          <div className="mb-8 bg-white rounded-xl p-6 border border-gray-200 shadow-sm" data-testid="visual-search-panel">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Visual Search</h3>
              <button onClick={() => { setSearchMode('text'); setUploadedImage(null); setImagePreview(null); }} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex gap-2 mb-4">
              {['SHOES', 'CLOTHES', 'ACCESSORIES'].map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-4 py-1.5 rounded-full text-xs font-medium transition-colors ${selectedCategory === cat ? 'bg-black text-white' : 'bg-gray-100 hover:bg-gray-200'}`}
                  data-testid={`category-${cat.toLowerCase()}`}
                >
                  {cat.charAt(0) + cat.slice(1).toLowerCase()}
                </button>
              ))}
            </div>
            {!imagePreview ? (
              <label className="block cursor-pointer" data-testid="image-upload-area">
                <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />
                <div className="border-2 border-dashed border-gray-200 rounded-lg p-10 text-center hover:border-gray-400 transition-colors">
                  <Camera className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">Click to upload an image</p>
                  <p className="text-xs text-gray-400 mt-1">JPG, PNG, WebP (Max 5MB)</p>
                </div>
              </label>
            ) : (
              <div>
                <div className="relative mb-4">
                  <img src={imagePreview} alt="Uploaded" className="w-full h-48 object-contain bg-gray-50 rounded-lg" />
                  <button onClick={() => { setUploadedImage(null); setImagePreview(null); }} className="absolute top-2 right-2 bg-white shadow p-1.5 rounded-full">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <button onClick={handleImageSearch} disabled={loading} className="w-full bg-black text-white py-3 rounded-lg font-medium disabled:opacity-50" data-testid="search-by-image-btn">
                  {loading ? 'Searching...' : `Find Similar ${selectedCategory.charAt(0) + selectedCategory.slice(1).toLowerCase()}`}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Brand Cards */}
        {brands.length > 0 && (
          <div className="mb-8" data-testid="brands-section">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold">Live Brands</h2>
              <span className="text-xs text-gray-400">{scrapeStatus?.total_products || 0} products</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {brands.map((brand) => (
                <div
                  key={brand.key}
                  className={`bg-white rounded-lg p-4 border cursor-pointer transition-all hover:shadow-md ${selectedBrand?.key === brand.key ? 'border-black ring-1 ring-black' : 'border-gray-200'}`}
                  onClick={() => handleBrandFilter(brand)}
                  data-testid={`brand-card-${brand.key}`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-sm">{brand.name}</h3>
                      <p className="text-xs text-gray-400 mt-0.5">{brand.productCount || 0} products</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-green-400" />
                      <button
                        onClick={(e) => { e.stopPropagation(); handleRefreshBrand(brand.key); }}
                        disabled={scrapingBrand === brand.key}
                        className="p-1.5 rounded-md hover:bg-gray-100 disabled:opacity-50"
                        title="Refresh products"
                        data-testid={`refresh-${brand.key}`}
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${scrapingBrand === brand.key ? 'animate-spin' : ''}`} />
                      </button>
                    </div>
                  </div>
                  <p className="text-[10px] text-gray-300 mt-2">
                    Last updated: {brand.lastScrapedAt ? new Date(brand.lastScrapedAt).toLocaleString() : 'Never'}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Active filter */}
        {selectedBrand && (
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-600">Showing products from</span>
            <span className="text-sm font-semibold bg-black text-white px-3 py-1 rounded-full">{selectedBrand.name}</span>
            <button onClick={() => { setSelectedBrand(null); fetchFeaturedProducts(); setHasSearched(false); }} className="text-xs text-gray-400 hover:text-gray-600 ml-1">Clear</button>
          </div>
        )}

        {/* Results */}
        {loading ? (
          <div className="flex justify-center py-20">
            <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : products.length > 0 ? (
          <div data-testid="products-grid">
            <p className="text-xs text-gray-400 mb-4">{products.length} results</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {products.map((product) => (
                <Link
                  key={product.id}
                  to={`/product/${product.id}`}
                  className="bg-white rounded-lg overflow-hidden border border-gray-100 hover:shadow-lg transition-all group"
                  data-testid={`product-card-${product.id}`}
                >
                  <div className="aspect-square bg-gray-50 overflow-hidden relative">
                    <img
                      src={product.imageUrl}
                      alt={product.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                    {product.store && (
                      <span className="absolute top-2 left-2 bg-black/70 text-white text-[9px] px-2 py-0.5 rounded-full backdrop-blur-sm">
                        {product.store.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>
                  <div className="p-3">
                    <p className="text-[11px] text-gray-400 mb-0.5">{product.brand}</p>
                    <h3 className="font-medium text-xs line-clamp-2 mb-2 leading-tight">{product.name}</h3>
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-sm font-bold">
                        {product.lowestPrice > 0 ? `₹${product.lowestPrice?.toLocaleString()}` : 'Price N/A'}
                      </span>
                      {product.highestPrice > 0 && product.highestPrice !== product.lowestPrice && (
                        <span className="text-[10px] text-gray-400 line-through">₹{product.highestPrice?.toLocaleString()}</span>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ) : hasSearched ? (
          <div className="text-center py-20" data-testid="no-results">
            <p className="text-gray-400 text-sm">No products found</p>
          </div>
        ) : (
          <div className="text-center py-12" data-testid="search-prompt">
            <p className="text-gray-400 text-sm">Search for products or browse brands above</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default SearchPage;
