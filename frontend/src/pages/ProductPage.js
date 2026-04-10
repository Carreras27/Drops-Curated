import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ExternalLink, Bell, Share2, Check, Heart } from 'lucide-react';
import { Header, Footer } from './LandingPage';
import axios from 'axios';
import { toast } from 'sonner';
import { generateProductAlt, ProductSchema, BreadcrumbSchema, OrganizationSchema } from '../components/SEOSchema';
import { useWishlist } from '../context/WishlistContext';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

export default function ProductPage() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [prices, setPrices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSize, setSelectedSize] = useState(null);
  const [sizeError, setSizeError] = useState(false);
  
  // Wishlist hook must be called before any early returns
  const { toggleWishlist, isInWishlist } = useWishlist();

  useEffect(() => {
    fetchProduct();
  }, [id]);

  const fetchProduct = async () => {
    try {
      const resp = await axios.get(`${API_URL}/products/${id}`);
      setProduct(resp.data.product);
      setPrices(resp.data.prices || []);
    } catch {
      toast.error('Product not found');
    } finally {
      setLoading(false);
    }
  };
  
  const handleWishlistClick = () => {
    if (!product) return;
    
    // Check if product has sizes and none is selected
    const hasSizes = product.attributes?.sizes?.length > 0;
    if (hasSizes && !selectedSize) {
      setSizeError(true);
      toast.error('Please select a size first');
      // Scroll to sizes section
      document.getElementById('sizes-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }
    
    // Add size info to product when adding to wishlist
    const productWithSize = {
      ...product,
      selectedSize: selectedSize,
    };
    
    const added = toggleWishlist(productWithSize);
    if (added) {
      toast.success(`Added to Wishlist${selectedSize ? ` (Size: ${selectedSize})` : ''}`);
    } else {
      toast('Removed from Wishlist');
    }
    setSizeError(false);
  };
  
  const handleSizeSelect = (size) => {
    setSelectedSize(size);
    setSizeError(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-6 h-6 border border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen bg-background" data-testid="product-not-found">
        <Header />
        <div className="pt-32 text-center">
          <p className="font-serif text-3xl text-primary/30">Product not found</p>
          <Link to="/browse" className="text-sm text-accent mt-4 inline-block">Back to drops</Link>
        </div>
      </div>
    );
  }

  const lowestPrice = prices.length > 0 ? Math.min(...prices.map(p => p.currentPrice)) : 0;
  const highestPrice = prices.length > 0 ? Math.max(...prices.map(p => p.currentPrice)) : 0;
  const savings = highestPrice - lowestPrice;
  
  // Generate SEO-friendly alt text
  const productAltText = generateProductAlt(product);
  
  // Check if product is in wishlist
  const isWishlisted = isInWishlist(product?.id);

  return (
    <div className="bg-background min-h-screen" data-testid="product-page">
      {/* Product Schema for Rich Snippets */}
      <ProductSchema product={product} prices={prices} />
      <OrganizationSchema />
      
      {/* Breadcrumb Schema */}
      <BreadcrumbSchema items={[
        { name: 'Home', url: '/' },
        { name: 'All Drops', url: '/browse' },
        { name: product.brand, url: `/browse?brand=${product.brand}` },
        { name: product.name }
      ]} />
      
      <Header />

      <main className="pt-24 pb-16">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          {/* Breadcrumb */}
          <Link to="/browse" className="inline-flex items-center gap-2 text-sm text-primary/40 hover:text-primary mb-8 transition-colors" data-testid="back-link">
            <ArrowLeft className="w-4 h-4" strokeWidth={1.5} />
            Back to drops
          </Link>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16">
            {/* Image */}
            <div className="lg:col-span-7">
              <div className="aspect-square overflow-hidden bg-surface">
                <img
                  src={product.imageUrl}
                  alt={productAltText}
                  title={`${product.brand} ${product.name} - Price comparison from ${prices.length} Indian stores`}
                  className="w-full h-full object-cover"
                  data-testid="product-image"
                />
              </div>
            </div>

            {/* Info */}
            <div className="lg:col-span-5">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-3">{product.brand}</p>
              <h1 className="font-serif text-3xl md:text-4xl tracking-tight mb-4" data-testid="product-name">{product.name}</h1>

              {product.description && (
                <p className="text-sm text-primary/50 leading-relaxed mb-8">{product.description}</p>
              )}

              {/* Price block */}
              <div className="border border-primary/10 p-6 mb-6" data-testid="price-summary">
                <div className="flex items-baseline gap-3 mb-2">
                  <span className="font-serif text-4xl">{lowestPrice > 0 ? `₹${lowestPrice.toLocaleString('en-IN')}` : '—'}</span>
                  {savings > 0 && (
                    <span className="text-sm text-primary/30 line-through">₹{highestPrice.toLocaleString('en-IN')}</span>
                  )}
                </div>
                <p className="text-xs text-primary/40 mb-4">
                  {prices.length > 0 ? `Best price from ${prices.length} source${prices.length > 1 ? 's' : ''}` : 'Price unavailable'}
                </p>
                {savings > 0 && (
                  <div className="inline-flex items-center gap-2 border border-accent/30 text-accent text-xs uppercase tracking-widest px-3 py-1.5">
                    <Check className="w-3 h-3" strokeWidth={1.5} />
                    Save ₹{savings.toLocaleString('en-IN')}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-3 mb-8">
                <Link
                  to="/subscribe"
                  className="flex-1 inline-flex items-center justify-center gap-2 bg-primary text-background py-3.5 font-medium text-sm hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300"
                  data-testid="alert-cta"
                >
                  <Bell className="w-4 h-4" strokeWidth={1.5} />
                  Get Price Alerts
                </Link>
                <button
                  onClick={handleWishlistClick}
                  className={`px-4 py-3.5 border transition-all ${
                    isWishlisted 
                      ? 'bg-red-500 border-red-500 text-white' 
                      : 'border-primary/10 hover:border-accent hover:text-accent'
                  }`}
                  data-testid="wishlist-btn"
                  title={isWishlisted ? 'Remove from Wishlist' : 'Add to Wishlist'}
                >
                  <Heart className={`w-5 h-5 ${isWishlisted ? 'fill-current' : ''}`} strokeWidth={1.5} />
                </button>
                <button
                  onClick={() => { navigator.clipboard.writeText(window.location.href); toast.success('Link copied!'); }}
                  className="border border-primary/10 px-4 hover:border-accent transition-colors"
                  data-testid="share-btn"
                >
                  <Share2 className="w-4 h-4" strokeWidth={1.5} />
                </button>
              </div>

              {/* Attributes - Sizes */}
              {product.attributes && product.attributes.sizes?.length > 0 && (
                <div className="mb-8" id="sizes-section">
                  <p className={`text-xs uppercase tracking-widest mb-3 ${sizeError ? 'text-red-500 font-semibold' : 'text-primary/40'}`}>
                    {sizeError ? '⚠ Please Select a Size' : 'Available Sizes'}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {product.attributes.sizes.map((s, i) => (
                      <button
                        key={i}
                        onClick={() => handleSizeSelect(s)}
                        className={`text-xs px-4 py-2.5 transition-all duration-200 cursor-pointer ${
                          selectedSize === s
                            ? 'bg-accent text-background border-accent font-semibold'
                            : sizeError
                              ? 'border-red-500/50 text-red-400 hover:border-red-500 hover:bg-red-500/10'
                              : 'border border-primary/20 text-primary/70 hover:border-accent hover:text-accent hover:bg-accent/5'
                        }`}
                        data-testid={`size-${s}`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                  {selectedSize && (
                    <p className="text-xs text-accent mt-2">
                      Selected: <span className="font-semibold">{selectedSize}</span>
                    </p>
                  )}
                </div>
              )}

              {/* Tags */}
              {product.tags?.length > 0 && (
                <div>
                  <p className="text-xs text-primary/40 uppercase tracking-widest mb-3">Tags</p>
                  <div className="flex flex-wrap gap-2">
                    {product.tags.slice(0, 8).map((t, i) => (
                      <span key={i} className="text-[10px] text-primary/30 uppercase tracking-widest">#{t}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Price Comparison */}
          {prices.length > 0 && (
            <div className="mt-16 md:mt-24">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-3">Price Comparison</p>
              <h2 className="font-serif text-3xl tracking-tight mb-8">Where to Buy</h2>

              {/* Desktop table */}
              <div className="hidden md:block border border-primary/10" data-testid="price-table">
                <div className="grid grid-cols-5 border-b border-primary/10 text-xs text-primary/40 uppercase tracking-widest">
                  <div className="px-6 py-4">Store</div>
                  <div className="px-6 py-4">Price</div>
                  <div className="px-6 py-4">Original</div>
                  <div className="px-6 py-4">Stock</div>
                  <div className="px-6 py-4 text-right">Action</div>
                </div>
                {prices.sort((a, b) => a.currentPrice - b.currentPrice).map((price, i) => (
                  <div
                    key={price.id || i}
                    className={`grid grid-cols-5 border-b border-primary/10 items-center hover:bg-primary/[0.02] transition-colors ${i === 0 ? 'bg-accent/[0.03]' : ''}`}
                    data-testid={`price-row-${i}`}
                  >
                    <div className="px-6 py-5 flex items-center gap-3">
                      <span className="text-sm font-medium">{price.store?.replace(/_/g, ' ')}</span>
                      {i === 0 && (
                        <span className="border border-accent text-accent text-[9px] uppercase tracking-widest px-2 py-0.5">Best</span>
                      )}
                    </div>
                    <div className="px-6 py-5">
                      <span className={`text-lg font-medium ${i === 0 ? 'text-accent' : ''}`}>
                        ₹{price.currentPrice?.toLocaleString('en-IN')}
                      </span>
                    </div>
                    <div className="px-6 py-5">
                      {price.originalPrice && price.originalPrice !== price.currentPrice ? (
                        <span className="text-sm text-primary/30 line-through">₹{price.originalPrice?.toLocaleString('en-IN')}</span>
                      ) : (
                        <span className="text-sm text-primary/20">—</span>
                      )}
                    </div>
                    <div className="px-6 py-5">
                      <span className={`text-xs ${price.inStock ? 'text-success' : 'text-danger'}`}>
                        {price.inStock ? 'In Stock' : 'Out of Stock'}
                      </span>
                    </div>
                    <div className="px-6 py-5 text-right">
                      {price.productUrl && (
                        <a
                          href={price.productUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 bg-primary text-background text-xs font-medium px-4 py-2 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-300"
                          data-testid={`buy-btn-${i}`}
                        >
                          Buy Now
                          <ExternalLink className="w-3 h-3" strokeWidth={1.5} />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Mobile cards */}
              <div className="md:hidden space-y-3">
                {prices.sort((a, b) => a.currentPrice - b.currentPrice).map((price, i) => (
                  <div key={price.id || i} className={`border border-primary/10 p-5 ${i === 0 ? 'bg-accent/[0.03]' : ''}`}>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{price.store?.replace(/_/g, ' ')}</span>
                        {i === 0 && (
                          <span className="border border-accent text-accent text-[9px] uppercase tracking-widest px-2 py-0.5">Best</span>
                        )}
                      </div>
                      <span className={`text-xs ${price.inStock ? 'text-success' : 'text-danger'}`}>
                        {price.inStock ? 'In Stock' : 'Out'}
                      </span>
                    </div>
                    <div className="flex items-baseline gap-2 mb-4">
                      <span className={`text-2xl font-medium ${i === 0 ? 'text-accent' : ''}`}>
                        ₹{price.currentPrice?.toLocaleString('en-IN')}
                      </span>
                      {price.originalPrice && price.originalPrice !== price.currentPrice && (
                        <span className="text-sm text-primary/30 line-through">₹{price.originalPrice?.toLocaleString('en-IN')}</span>
                      )}
                    </div>
                    {price.productUrl && (
                      <a
                        href={price.productUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block w-full text-center bg-primary text-background text-sm font-medium py-3 hover:bg-primary-hover transition-colors"
                      >
                        Buy Now
                      </a>
                    )}
                  </div>
                ))}
              </div>

              <p className="text-[10px] text-primary/20 mt-4">
                Prices updated: {prices[0]?.lastScrapedAt ? new Date(prices[0].lastScrapedAt).toLocaleString() : 'Recently'}
              </p>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
