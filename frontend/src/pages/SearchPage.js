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
                  className="bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden hover:shadow-lg transition-shadow border border-gray-200 dark:border-gray-800"
                >
                  <div className="aspect-square bg-gray-200 dark:bg-gray-800 overflow-hidden">
                    <img 
                      src={product.imageUrl} 
                      alt={product.name}
                      className="w-full h-full object-cover"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  </div>
                  <div className="p-4">
                    <h3 className="font-bold mb-2 line-clamp-2">{product.name}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{product.brand}</p>
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-lg font-bold text-success">₹{product.lowestPrice || 'N/A'}</span>
                        {product.priceCount > 1 && (
                          <span className="text-xs text-gray-500 ml-2">from {product.priceCount} stores</span>
                        )}
                      </div>
                      {product.isTrending && (
                        <span className="text-xs bg-primary bg-opacity-10 text-primary px-2 py-1 rounded font-bold">
                          Trending
                        </span>
                      )}
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
