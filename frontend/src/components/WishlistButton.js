import React, { useState } from 'react';
import { Heart } from 'lucide-react';
import { useWishlist } from '../context/WishlistContext';
import { toast } from 'sonner';

export default function WishlistButton({ product, size = 'md', showLabel = false, className = '' }) {
  const { toggleWishlist, isInWishlist } = useWishlist();
  const [isAnimating, setIsAnimating] = useState(false);
  
  const isWishlisted = isInWishlist(product?.id);
  
  const handleClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!product) return;
    
    setIsAnimating(true);
    const added = toggleWishlist(product);
    
    // Show toast notification
    if (added) {
      toast.success('Added to Wishlist', {
        description: product.name?.slice(0, 40) + (product.name?.length > 40 ? '...' : ''),
        duration: 2000
      });
    } else {
      toast('Removed from Wishlist', {
        duration: 2000
      });
    }
    
    setTimeout(() => setIsAnimating(false), 300);
  };
  
  // Size variants
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12'
  };
  
  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };
  
  if (!product) return null;
  
  return (
    <button
      onClick={handleClick}
      className={`
        ${sizeClasses[size]} 
        flex items-center justify-center gap-2
        ${isWishlisted 
          ? 'bg-red-500 text-white' 
          : 'bg-background/80 backdrop-blur-sm text-primary hover:bg-background hover:text-red-500'
        }
        rounded-full border border-primary/10
        transition-all duration-200
        ${isAnimating ? 'scale-125' : 'scale-100'}
        ${className}
      `}
      title={isWishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
      data-testid={`wishlist-btn-${product.id}`}
    >
      <Heart 
        className={`${iconSizes[size]} ${isWishlisted ? 'fill-current' : ''}`} 
        strokeWidth={2}
      />
      {showLabel && (
        <span className="text-sm font-medium">
          {isWishlisted ? 'Saved' : 'Save'}
        </span>
      )}
    </button>
  );
}

// Inline wishlist button for product cards (absolute positioned)
export function WishlistButtonOverlay({ product, className = '' }) {
  return (
    <div className={`absolute top-3 right-3 z-10 ${className}`}>
      <WishlistButton product={product} size="sm" />
    </div>
  );
}
