import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, Sparkles, Heart, LogOut } from 'lucide-react';
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

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/search?q=${encodeURIComponent(query)}`);
      setProducts(response.data.products || []);
      if (response.data.products.length === 0) {
        toast.info('No products found. Try different keywords!');
      }
    } catch (error) {
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <header className="border-b border-gray-200 dark:border-gray-800">
        <nav className="container mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/search" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">IndiaShop</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/watchlist" className="text-sm font-medium flex items-center gap-2 hover:text-primary">
              <Heart className="w-5 h-5" />
              Watchlist
            </Link>
            <button onClick={handleLogout} className="text-sm font-medium flex items-center gap-2 hover:text-primary">
              <LogOut className="w-5 h-5" />
              Logout
            </button>
          </div>
        </nav>
      </header>

      <main className="container mx-auto px-6 py-12">
        <div className="max-w-3xl mx-auto mb-12">
          <h1 className="text-4xl font-bold mb-8 text-center">Find the Best Prices</h1>
          <form onSubmit={handleSearch} className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search for shoes, clothes, cosmetics..."
                className="w-full pl-12 pr-4 py-4 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-primary hover:bg-primary-hover text-white font-bold px-8 py-4 rounded-lg disabled:opacity-50"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </form>
        </div>

        {products.length > 0 && (
          <div className="max-w-7xl mx-auto">
            <h2 className="text-2xl font-bold mb-6">{products.length} Results</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {products.map((product) => (
                <Link
                  key={product.id}
                  to={`/product/${product.id}`}
                  className="bg-white dark:bg-gray-900 rounded-lg overflow-hidden hover:shadow-xl transition-all border border-gray-200 dark:border-gray-800"
                >
                  <div className="aspect-square bg-gray-200 dark:bg-gray-800 overflow-hidden relative">
                    <img 
                      src={product.imageUrl} 
                      alt={product.name}
                      className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.parentElement.innerHTML = '<div class="w-full h-full flex items-center justify-center text-gray-400">No image</div>';
                      }}
                    />
                    {product.isTrending && (
                      <div className="absolute top-3 right-3 bg-primary text-white px-3 py-1 rounded-full text-xs font-bold">
                        🔥 Trending
                      </div>
                    )}
                  </div>
                  <div className="p-5">
                    <h3 className="font-bold mb-2 line-clamp-2 text-lg">{product.name}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{product.brand}</p>
                    
                    {/* Price Section */}
                    <div className="space-y-2">
                      <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-success">₹{product.lowestPrice?.toLocaleString() || 'N/A'}</span>
                        {product.highestPrice && product.highestPrice !== product.lowestPrice && (
                          <span className="text-sm text-gray-500 line-through">₹{product.highestPrice.toLocaleString()}</span>
                        )}
                      </div>
                      
                      {product.priceCount > 1 && (
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-500">
                            Compared from {product.priceCount} stores
                          </span>
                          {product.highestPrice && product.highestPrice !== product.lowestPrice && (
                            <span className="text-xs bg-success bg-opacity-10 text-success px-2 py-1 rounded font-bold">
                              Save ₹{(product.highestPrice - product.lowestPrice).toLocaleString()}
                            </span>
                          )}
                        </div>
                      )}
                      
                      {product.priceCount === 1 && (
                        <span className="text-xs text-gray-500">Available at 1 store</span>
                      )}
                    </div>
                    
                    {/* View Comparison CTA */}
                    <div className="mt-4 text-primary text-sm font-bold hover:underline">
                      Compare prices →
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {!loading && products.length === 0 && query && (
          <div className="text-center py-20">
            <p className="text-gray-600">No products found. Try different keywords!</p>
          </div>
        )}

        {!query && (
          <div className="text-center py-20">
            <p className="text-gray-600">Enter a search query to find products</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default SearchPage;
