import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Sparkles, Heart, ExternalLink, TrendingUp } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const ProductPage = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const [product, setProduct] = useState(null);
  const [prices, setPrices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProduct();
  }, [id]);

  const fetchProduct = async () => {
    try {
      const response = await axios.get(`${API_URL}/products/${id}`);
      setProduct(response.data.product);
      setPrices(response.data.prices);
    } catch (error) {
      toast.error('Failed to load product');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToWatchlist = async () => {
    try {
      await axios.post(`${API_URL}/watchlist?product_id=${id}`);
      toast.success('Added to watchlist!');
    } catch (error) {
      toast.error('Failed to add to watchlist');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white dark:bg-black flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen bg-white dark:bg-black flex items-center justify-center">
        <p className="text-gray-600">Product not found</p>
      </div>
    );
  }

  const lowestPrice = prices.length > 0 ? Math.min(...prices.map(p => p.currentPrice)) : 0;
  const highestPrice = prices.length > 0 ? Math.max(...prices.map(p => p.currentPrice)) : 0;

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-800">
        <nav className="container mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/search" className="flex items-center gap-2 hover:text-primary">
            <ArrowLeft className="w-5 h-5" />
            <span className="font-medium">Back to Search</span>
          </Link>
          <Link to="/search" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">IndiaShop</span>
          </Link>
        </nav>
      </header>

      <main className="container mx-auto px-6 py-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12">
            {/* Product Image */}
            <div className="aspect-square bg-gray-100 dark:bg-gray-900 rounded-lg overflow-hidden">
              <img 
                src={product.imageUrl} 
                alt={product.name}
                className="w-full h-full object-cover"
              />
            </div>

            {/* Product Info */}
            <div>
              <div className="mb-4">
                <span className="text-sm text-gray-600 dark:text-gray-400">{product.brand}</span>
                {product.isTrending && (
                  <span className="ml-2 text-xs bg-primary bg-opacity-10 text-primary px-2 py-1 rounded font-bold">
                    🔥 Trending
                  </span>
                )}
              </div>
              
              <h1 className="text-4xl font-bold mb-4">{product.name}</h1>
              
              {product.description && (
                <p className="text-gray-600 dark:text-gray-400 mb-6">{product.description}</p>
              )}

              {/* Price Summary */}
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-6">
                <div className="flex items-baseline gap-3 mb-2">
                  <span className="text-4xl font-bold text-success">₹{lowestPrice.toLocaleString()}</span>
                  {highestPrice !== lowestPrice && (
                    <span className="text-xl text-gray-500 line-through">₹{highestPrice.toLocaleString()}</span>
                  )}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  Lowest price from {prices.length} store{prices.length !== 1 ? 's' : ''}
                </p>
                {highestPrice !== lowestPrice && (
                  <div className="bg-success bg-opacity-10 text-success px-4 py-2 rounded inline-block font-bold">
                    💰 Save up to ₹{(highestPrice - lowestPrice).toLocaleString()}
                  </div>
                )}
              </div>

              {/* Product Attributes */}
              {product.attributes && Object.keys(product.attributes).length > 0 && (
                <div className="mb-6">
                  <h3 className="font-bold mb-3">Details</h3>
                  <div className="space-y-2">
                    {Object.entries(product.attributes).map(([key, value]) => (
                      <div key={key} className="flex gap-2">
                        <span className="text-gray-600 dark:text-gray-400 capitalize">{key}:</span>
                        <span className="font-medium">
                          {Array.isArray(value) ? value.join(', ') : value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Add to Watchlist */}
              <button
                onClick={handleAddToWatchlist}
                className="w-full bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-800 hover:border-primary text-foreground font-bold py-3 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Heart className="w-5 h-5" />
                Add to Watchlist
              </button>
            </div>
          </div>

          {/* Price Comparison Table */}
          <div>
            <h2 className="text-3xl font-bold mb-6">Price Comparison</h2>
            
            {/* Mobile Card Layout */}
            <div className="lg:hidden space-y-4">
              {prices.sort((a, b) => a.currentPrice - b.currentPrice).map((price, index) => (
                <div 
                  key={price.id}
                  className={`bg-white dark:bg-gray-900 rounded-lg border-2 p-5 ${
                    index === 0 ? 'border-success bg-success bg-opacity-5' : 'border-gray-200 dark:border-gray-800'
                  }`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-bold text-lg">{price.store.replace(/_/g, ' ')}</h3>
                      {index === 0 && (
                        <span className="text-xs bg-success text-white px-2 py-1 rounded font-bold mt-1 inline-block">
                          LOWEST PRICE
                        </span>
                      )}
                    </div>
                    {price.inStock ? (
                      <span className="text-success font-bold text-sm">In Stock</span>
                    ) : (
                      <span className="text-red-500 font-bold text-sm">Out of Stock</span>
                    )}
                  </div>
                  
                  <div className="mb-4">
                    <div className="flex items-baseline gap-2 mb-2">
                      <span className={`text-3xl font-bold ${index === 0 ? 'text-success' : ''}`}>
                        ₹{price.currentPrice.toLocaleString()}
                      </span>
                      {price.originalPrice && price.originalPrice !== price.currentPrice && (
                        <span className="text-lg text-gray-500 line-through">
                          ₹{price.originalPrice.toLocaleString()}
                        </span>
                      )}
                    </div>
                    {price.discountPercent && (
                      <span className="text-warning font-bold text-sm">
                        {price.discountPercent}% OFF
                      </span>
                    )}
                  </div>
                  
                  <a
                    href={price.productUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full bg-primary hover:bg-primary-hover text-white text-center px-6 py-3 rounded-lg font-bold transition-colors"
                  >
                    Buy Now from {price.store.replace(/_/g, ' ')}
                  </a>
                </div>
              ))}
            </div>

            {/* Desktop Table Layout */}
            <div className="hidden lg:block bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="text-left px-6 py-4 font-bold">Store</th>
                      <th className="text-left px-6 py-4 font-bold">Price</th>
                      <th className="text-left px-6 py-4 font-bold">Discount</th>
                      <th className="text-left px-6 py-4 font-bold">Stock</th>
                      <th className="text-right px-6 py-4 font-bold">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {prices.sort((a, b) => a.currentPrice - b.currentPrice).map((price, index) => (
                      <tr 
                        key={price.id}
                        className={`border-t border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
                          index === 0 ? 'bg-success bg-opacity-5' : ''
                        }`}
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <span className="font-bold">{price.store.replace(/_/g, ' ')}</span>
                            {index === 0 && (
                              <span className="text-xs bg-success text-white px-2 py-1 rounded font-bold">
                                LOWEST
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div>
                            <span className={`text-xl font-bold ${index === 0 ? 'text-success' : ''}`}>
                              ₹{price.currentPrice.toLocaleString()}
                            </span>
                            {price.originalPrice && price.originalPrice !== price.currentPrice && (
                              <span className="text-sm text-gray-500 line-through ml-2">
                                ₹{price.originalPrice.toLocaleString()}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          {price.discountPercent ? (
                            <span className="text-warning font-bold">{price.discountPercent}% OFF</span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          {price.inStock ? (
                            <span className="text-success font-medium">In Stock</span>
                          ) : (
                            <span className="text-red-500 font-medium">Out of Stock</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <a
                            href={price.productUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 bg-primary hover:bg-primary-hover text-white px-4 py-2 rounded font-bold transition-colors"
                          >
                            Buy Now
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Last Updated */}
            <p className="text-sm text-gray-500 mt-4">
              Prices last updated: {new Date(prices[0]?.lastScrapedAt || Date.now()).toLocaleString()}
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ProductPage;
