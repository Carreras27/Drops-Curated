import React from 'react';
import { Link } from 'react-router-dom';
import { Header, Footer } from './LandingPage';
import { Heart, Trash2, ExternalLink, ShoppingBag, ArrowRight } from 'lucide-react';
import { useWishlist } from '../context/WishlistContext';
import { generateProductAlt } from '../components/SEOSchema';

export default function WishlistPage() {
  const { wishlist, removeFromWishlist, clearWishlist, wishlistCount } = useWishlist();

  // Format price
  const formatPrice = (price) => {
    if (!price || price === 0) return '—';
    return `₹${price.toLocaleString('en-IN')}`;
  };

  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch {
      return '';
    }
  };

  return (
    <div className="bg-background min-h-screen" data-testid="wishlist-page">
      <Header />
      
      {/* Hero */}
      <section className="pt-28 pb-8 md:pt-36 md:pb-12 bg-gradient-to-b from-primary/5 to-transparent">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
            <div>
              <span className="inline-block text-[10px] font-semibold uppercase tracking-[0.2em] text-accent mb-4">My Wishlist</span>
              <h1 className="text-4xl md:text-5xl font-serif mb-2">Saved Drops</h1>
              <p className="text-primary/60">
                {wishlistCount === 0 
                  ? "You haven't saved any drops yet" 
                  : `${wishlistCount} ${wishlistCount === 1 ? 'item' : 'items'} saved`
                }
              </p>
            </div>
            
            {wishlistCount > 0 && (
              <button
                onClick={() => {
                  if (window.confirm('Clear all items from your wishlist?')) {
                    clearWishlist();
                  }
                }}
                className="flex items-center gap-2 text-sm text-primary/50 hover:text-red-500 transition-colors"
                data-testid="clear-wishlist"
              >
                <Trash2 className="w-4 h-4" />
                Clear All
              </button>
            )}
          </div>
        </div>
      </section>
      
      {/* Wishlist Content */}
      <section className="py-12 md:py-16">
        <div className="max-w-6xl mx-auto px-6">
          
          {/* Empty State */}
          {wishlistCount === 0 ? (
            <div className="text-center py-16">
              <div className="w-20 h-20 bg-primary/5 rounded-full flex items-center justify-center mx-auto mb-6">
                <Heart className="w-10 h-10 text-primary/30" />
              </div>
              <h2 className="text-2xl font-serif mb-3">Your wishlist is empty</h2>
              <p className="text-primary/60 mb-8 max-w-md mx-auto">
                Save drops you're interested in by clicking the heart icon on any product. 
                They'll appear here so you can track them and buy when you're ready.
              </p>
              <Link
                to="/browse"
                className="inline-flex items-center gap-2 bg-primary text-background px-6 py-3 font-medium hover:-translate-y-0.5 hover:shadow-lift transition-all"
                data-testid="browse-drops-cta"
              >
                <ShoppingBag className="w-4 h-4" />
                Browse Drops
              </Link>
            </div>
          ) : (
            <>
              {/* Wishlist Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {wishlist.map((item, idx) => (
                  <div 
                    key={item.id}
                    className="group bg-surface border border-primary/5 overflow-hidden animate-fade-up"
                    style={{ animationDelay: `${idx * 0.05}s` }}
                    data-testid={`wishlist-item-${item.id}`}
                  >
                    {/* Image */}
                    <Link to={`/product/${item.id}`} className="block">
                      <div className="aspect-square overflow-hidden relative">
                        <img
                          src={item.imageUrl}
                          alt={generateProductAlt(item)}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                          loading="lazy"
                          onError={(e) => { e.target.style.display = 'none'; }}
                        />
                        {/* Category Badge */}
                        {item.category && (
                          <span className="absolute top-3 left-3 bg-background/90 px-2 py-1 text-[10px] uppercase tracking-wider">
                            {item.category}
                          </span>
                        )}
                      </div>
                    </Link>
                    
                    {/* Details */}
                    <div className="p-4">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-accent mb-1">
                        {item.brand}
                      </p>
                      <Link to={`/product/${item.id}`}>
                        <h3 className="font-medium leading-snug line-clamp-2 mb-2 group-hover:text-accent transition-colors">
                          {item.name}
                        </h3>
                      </Link>
                      
                      <div className="flex items-center justify-between mt-3">
                        <span className="text-lg font-medium">
                          {formatPrice(item.lowestPrice)}
                        </span>
                        <span className="text-xs text-primary/40">
                          Saved {formatDate(item.addedAt)}
                        </span>
                      </div>
                      
                      {/* Actions */}
                      <div className="flex gap-2 mt-4 pt-4 border-t border-primary/5">
                        <Link
                          to={`/product/${item.id}`}
                          className="flex-1 flex items-center justify-center gap-2 bg-primary text-background py-2.5 text-sm font-medium hover:bg-primary/90 transition-colors"
                        >
                          <ExternalLink className="w-4 h-4" />
                          View Drop
                        </Link>
                        <button
                          onClick={() => removeFromWishlist(item.id)}
                          className="p-2.5 border border-primary/10 hover:border-red-500 hover:text-red-500 transition-colors"
                          title="Remove from wishlist"
                          data-testid={`remove-${item.id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Continue Shopping */}
              <div className="text-center mt-12 pt-8 border-t border-primary/10">
                <p className="text-primary/60 mb-4">Looking for more?</p>
                <Link
                  to="/browse"
                  className="inline-flex items-center gap-2 text-accent hover:gap-3 transition-all"
                >
                  Continue Browsing
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </>
          )}
        </div>
      </section>
      
      <Footer />
    </div>
  );
}
