import React, { createContext, useContext, useState, useEffect } from 'react';

// Wishlist Context
const WishlistContext = createContext();

// Local storage key
const WISHLIST_KEY = 'drops_curated_wishlist';

export function WishlistProvider({ children }) {
  const [wishlist, setWishlist] = useState([]);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load wishlist from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(WISHLIST_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setWishlist(Array.isArray(parsed) ? parsed : []);
      }
    } catch (e) {
      console.error('Failed to load wishlist:', e);
    }
    setIsLoaded(true);
  }, []);

  // Save to localStorage whenever wishlist changes
  useEffect(() => {
    if (isLoaded) {
      try {
        localStorage.setItem(WISHLIST_KEY, JSON.stringify(wishlist));
      } catch (e) {
        console.error('Failed to save wishlist:', e);
      }
    }
  }, [wishlist, isLoaded]);

  // Add item to wishlist
  const addToWishlist = (product) => {
    if (!product || !product.id) return false;
    
    // Check if already in wishlist
    if (wishlist.some(item => item.id === product.id)) {
      return false;
    }

    const wishlistItem = {
      id: product.id,
      name: product.name,
      brand: product.brand,
      imageUrl: product.imageUrl,
      lowestPrice: product.lowestPrice,
      category: product.aiCategory || product.category,
      addedAt: new Date().toISOString()
    };

    setWishlist(prev => [wishlistItem, ...prev]);
    return true;
  };

  // Remove item from wishlist
  const removeFromWishlist = (productId) => {
    setWishlist(prev => prev.filter(item => item.id !== productId));
  };

  // Toggle wishlist (add if not present, remove if present)
  const toggleWishlist = (product) => {
    if (isInWishlist(product.id)) {
      removeFromWishlist(product.id);
      return false; // Removed
    } else {
      addToWishlist(product);
      return true; // Added
    }
  };

  // Check if product is in wishlist
  const isInWishlist = (productId) => {
    return wishlist.some(item => item.id === productId);
  };

  // Clear entire wishlist
  const clearWishlist = () => {
    setWishlist([]);
  };

  // Get wishlist count
  const wishlistCount = wishlist.length;

  const value = {
    wishlist,
    wishlistCount,
    addToWishlist,
    removeFromWishlist,
    toggleWishlist,
    isInWishlist,
    clearWishlist,
    isLoaded
  };

  return (
    <WishlistContext.Provider value={value}>
      {children}
    </WishlistContext.Provider>
  );
}

// Hook to use wishlist
export function useWishlist() {
  const context = useContext(WishlistContext);
  if (!context) {
    throw new Error('useWishlist must be used within a WishlistProvider');
  }
  return context;
}

export default WishlistContext;
