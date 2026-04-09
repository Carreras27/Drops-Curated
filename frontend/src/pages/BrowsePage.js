import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import { Search, SlidersHorizontal, X, RefreshCw, ExternalLink, Flame, Sparkles, Clock, AlertTriangle, Star, Check, Ruler } from 'lucide-react';
import { Header, Footer } from './LandingPage';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const CATEGORIES = ['All', 'SHOES', 'CLOTHES', 'ACCESSORIES'];
const SUBCATEGORIES = ['T-Shirts', 'Shirts', 'Hoodies', 'Collectables', 'Jackets', 'Pants'];
const AUTO_REFRESH_INTERVAL = 15 * 60 * 1000; // 15 minutes in ms

// ============ SIZE CONVERSION SYSTEM ============
// Comprehensive size conversion charts
const SHOE_SIZE_CONVERSIONS = {
  // UK to other formats (Men's)
  'UK5': { uk: 'UK5', us: 'US6', eu: 'EU38' },
  'UK6': { uk: 'UK6', us: 'US7', eu: 'EU39' },
  'UK7': { uk: 'UK7', us: 'US8', eu: 'EU40.5' },
  'UK8': { uk: 'UK8', us: 'US9', eu: 'EU42' },
  'UK9': { uk: 'UK9', us: 'US10', eu: 'EU43' },
  'UK10': { uk: 'UK10', us: 'US11', eu: 'EU44' },
  'UK11': { uk: 'UK11', us: 'US12', eu: 'EU45' },
  'UK12': { uk: 'UK12', us: 'US13', eu: 'EU46' },
  // US to other formats
  'US6': { uk: 'UK5', us: 'US6', eu: 'EU38' },
  'US7': { uk: 'UK6', us: 'US7', eu: 'EU39' },
  'US8': { uk: 'UK7', us: 'US8', eu: 'EU40.5' },
  'US9': { uk: 'UK8', us: 'US9', eu: 'EU42' },
  'US10': { uk: 'UK9', us: 'US10', eu: 'EU43' },
  'US11': { uk: 'UK10', us: 'US11', eu: 'EU44' },
  'US12': { uk: 'UK11', us: 'US12', eu: 'EU45' },
  'US13': { uk: 'UK12', us: 'US13', eu: 'EU46' },
  // EU to other formats
  'EU38': { uk: 'UK5', us: 'US6', eu: 'EU38' },
  'EU39': { uk: 'UK6', us: 'US7', eu: 'EU39' },
  'EU40': { uk: 'UK6.5', us: 'US7.5', eu: 'EU40' },
  'EU40.5': { uk: 'UK7', us: 'US8', eu: 'EU40.5' },
  'EU41': { uk: 'UK7.5', us: 'US8.5', eu: 'EU41' },
  'EU42': { uk: 'UK8', us: 'US9', eu: 'EU42' },
  'EU43': { uk: 'UK9', us: 'US10', eu: 'EU43' },
  'EU44': { uk: 'UK10', us: 'US11', eu: 'EU44' },
  'EU45': { uk: 'UK11', us: 'US12', eu: 'EU45' },
  'EU46': { uk: 'UK12', us: 'US13', eu: 'EU46' },
};

// Garment sizes are more universal
const GARMENT_SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL'];

// Get all equivalent sizes for a given size
const getEquivalentSizes = (size) => {
  if (!size) return [];
  const normalizedSize = size.toUpperCase().replace(/\s/g, '');
  
  // Check if it's a shoe size
  if (SHOE_SIZE_CONVERSIONS[normalizedSize]) {
    const conversions = SHOE_SIZE_CONVERSIONS[normalizedSize];
    return [conversions.uk, conversions.us, conversions.eu, 
            conversions.uk.toLowerCase(), conversions.us.toLowerCase(), conversions.eu.toLowerCase(),
            // Also add variations like "UK 10", "US 11", "EU 44"
            conversions.uk.replace('UK', 'UK '), conversions.us.replace('US', 'US '), conversions.eu.replace('EU', 'EU '),
            // Numeric only variations
            normalizedSize.replace(/[A-Z]/g, ''),
    ].filter(Boolean);
  }
  
  // For garment sizes, return the size and common variations
  if (GARMENT_SIZES.includes(normalizedSize)) {
    return [normalizedSize, normalizedSize.toLowerCase(), size];
  }
  
  return [size, normalizedSize];
};

// Check if a product size matches user's preferred sizes
const doesProductMatchSize = (productSizes, userSizes) => {
  if (!userSizes || userSizes.length === 0) return true; // No filter = show all
  if (!productSizes || productSizes.length === 0) return true; // No size info = show it
  
  // Get all equivalent sizes for user's preferences
  const allEquivalentSizes = userSizes.flatMap(s => getEquivalentSizes(s));
  
  // Check if any product size matches any equivalent size
  return productSizes.some(ps => {
    const normalizedPS = ps.toUpperCase().replace(/\s/g, '');
    return allEquivalentSizes.some(es => {
      const normalizedES = es.toUpperCase().replace(/\s/g, '');
      return normalizedPS.includes(normalizedES) || normalizedES.includes(normalizedPS);
    });
  });
};

// ============ SIZE FIRST MODAL ============
const SizeFirstModal = ({ isOpen, onClose, onSave, initialSizes = {} }) => {
  const [selectedGarmentSizes, setSelectedGarmentSizes] = useState(initialSizes.garments || []);
  const [selectedShoeSizes, setSelectedShoeSizes] = useState(initialSizes.shoes || []);
  const [sizeSystem, setSizeSystem] = useState(initialSizes.system || 'UK'); // UK, US, EU
  
  const toggleGarmentSize = (size) => {
    setSelectedGarmentSizes(prev => 
      prev.includes(size) ? prev.filter(s => s !== size) : [...prev, size]
    );
  };
  
  const toggleShoeSize = (size) => {
    setSelectedShoeSizes(prev => 
      prev.includes(size) ? prev.filter(s => s !== size) : [...prev, size]
    );
  };
  
  const handleSave = () => {
    const sizePrefs = {
      garments: selectedGarmentSizes,
      shoes: selectedShoeSizes,
      system: sizeSystem,
      allSizes: [...selectedGarmentSizes, ...selectedShoeSizes],
    };
    onSave(sizePrefs);
    onClose();
  };
  
  const handleSkip = () => {
    onSave({ garments: [], shoes: [], system: sizeSystem, allSizes: [], skipped: true });
    onClose();
  };
  
  // Get shoe sizes based on selected system
  const getShoeSizesForSystem = () => {
    switch (sizeSystem) {
      case 'US':
        return ['US6', 'US7', 'US8', 'US9', 'US10', 'US11', 'US12', 'US13'];
      case 'EU':
        return ['EU38', 'EU39', 'EU40', 'EU41', 'EU42', 'EU43', 'EU44', 'EU45', 'EU46'];
      default: // UK
        return ['UK5', 'UK6', 'UK7', 'UK8', 'UK9', 'UK10', 'UK11', 'UK12'];
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary/70 backdrop-blur-sm" data-testid="size-first-modal">
      <div className="bg-background border border-primary/10 max-w-lg w-full max-h-[90vh] overflow-y-auto animate-fade-up">
        <div className="p-6 border-b border-primary/10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-accent/10 flex items-center justify-center">
              <Ruler className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h2 className="font-serif text-xl">Size First</h2>
              <p className="text-xs text-primary/50">See only products in your size</p>
            </div>
          </div>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Size System Selector */}
          <div>
            <p className="text-xs text-primary/40 uppercase tracking-widest mb-3">Size System</p>
            <div className="grid grid-cols-3 gap-2">
              {['UK', 'US', 'EU'].map(system => (
                <button
                  key={system}
                  onClick={() => {
                    setSizeSystem(system);
                    setSelectedShoeSizes([]); // Reset shoe sizes when system changes
                  }}
                  className={`py-3 border text-sm font-medium transition-all ${
                    sizeSystem === system 
                      ? 'border-accent bg-accent/10 text-primary' 
                      : 'border-primary/10 text-primary/50 hover:border-primary/30'
                  }`}
                  data-testid={`size-system-${system}`}
                >
                  {system}
                </button>
              ))}
            </div>
            <p className="text-[10px] text-primary/30 mt-2">
              We'll automatically convert to other formats (UK 10 = US 11 = EU 44)
            </p>
          </div>
          
          {/* Garment Sizes */}
          <div>
            <p className="text-xs text-primary/40 uppercase tracking-widest mb-3">Garments (T-shirts, Hoodies, Jackets)</p>
            <div className="grid grid-cols-6 gap-2">
              {GARMENT_SIZES.slice(0, 6).map(size => (
                <button
                  key={size}
                  onClick={() => toggleGarmentSize(size)}
                  className={`py-2.5 border text-xs font-medium transition-all ${
                    selectedGarmentSizes.includes(size)
                      ? 'border-accent bg-accent/10 text-primary'
                      : 'border-primary/10 text-primary/50 hover:border-primary/30'
                  }`}
                  data-testid={`garment-size-${size}`}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>
          
          {/* Shoe Sizes */}
          <div>
            <p className="text-xs text-primary/40 uppercase tracking-widest mb-3">Shoes ({sizeSystem} Sizes)</p>
            <div className="grid grid-cols-4 gap-2">
              {getShoeSizesForSystem().map(size => (
                <button
                  key={size}
                  onClick={() => toggleShoeSize(size)}
                  className={`py-2.5 border text-xs font-medium transition-all ${
                    selectedShoeSizes.includes(size)
                      ? 'border-accent bg-accent/10 text-primary'
                      : 'border-primary/10 text-primary/50 hover:border-primary/30'
                  }`}
                  data-testid={`shoe-size-${size}`}
                >
                  {size}
                </button>
              ))}
            </div>
            
            {/* Show equivalent sizes */}
            {selectedShoeSizes.length > 0 && (
              <div className="mt-3 p-3 bg-green-50 border border-green-200 text-xs">
                <p className="text-green-700 font-medium mb-1">Auto-converting your sizes:</p>
                <div className="text-green-600 space-y-0.5">
                  {selectedShoeSizes.map(size => {
                    const conversions = SHOE_SIZE_CONVERSIONS[size];
                    if (conversions) {
                      return (
                        <p key={size}>
                          {conversions.uk} = {conversions.us} = {conversions.eu}
                        </p>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>
            )}
          </div>
          
          {/* Summary */}
          {(selectedGarmentSizes.length > 0 || selectedShoeSizes.length > 0) && (
            <div className="p-4 bg-accent/5 border border-accent/20">
              <p className="text-xs font-medium text-primary mb-2">Your Sizes</p>
              <div className="flex flex-wrap gap-2">
                {selectedGarmentSizes.map(s => (
                  <span key={s} className="px-2 py-1 bg-primary/10 text-xs">{s}</span>
                ))}
                {selectedShoeSizes.map(s => (
                  <span key={s} className="px-2 py-1 bg-accent/20 text-xs">{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="p-6 border-t border-primary/10 space-y-3">
          <button
            onClick={handleSave}
            disabled={selectedGarmentSizes.length === 0 && selectedShoeSizes.length === 0}
            className="w-full bg-primary text-background py-3.5 font-medium text-sm flex items-center justify-center gap-2 hover:-translate-y-0.5 transition-all disabled:opacity-40"
            data-testid="save-sizes-btn"
          >
            <Check className="w-4 h-4" />
            Show Products in My Size
          </button>
          <button
            onClick={handleSkip}
            className="w-full border border-primary/10 text-primary/50 py-3 text-sm hover:border-primary/30 transition-colors"
            data-testid="skip-sizes-btn"
          >
            Skip - Show All Sizes
          </button>
        </div>
      </div>
    </div>
  );
};

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

// Celebrity Style Card Component
const CelebrityCard = ({ celebrity, products, idx }) => {
  return (
    <div 
      className="group animate-fade-up bg-gradient-to-br from-primary/[0.02] to-accent/[0.02] border border-primary/10 hover:border-accent/30 transition-all duration-300"
      style={{ animationDelay: `${idx * 0.1}s` }}
      data-testid={`celebrity-card-${celebrity.id}`}
    >
      {/* Celebrity Header */}
      <div className="flex items-center gap-4 p-4 border-b border-primary/5">
        <div className="w-14 h-14 rounded-full overflow-hidden border-2 border-accent/20 flex-shrink-0">
          <img 
            src={celebrity.image} 
            alt={celebrity.name}
            className="w-full h-full object-cover"
            onError={(e) => { 
              e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(celebrity.name)}&background=c9a961&color=001f3f&size=100`;
            }}
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <Star className="w-3.5 h-3.5 text-accent fill-accent" />
            <span className="text-[10px] uppercase tracking-widest text-accent font-medium">Celebrity Pick</span>
          </div>
          <h3 className="font-serif text-lg truncate">{celebrity.name}</h3>
          <p className="text-[10px] text-primary/40 uppercase tracking-wider">{celebrity.category}</p>
        </div>
      </div>
      
      {/* Products Grid */}
      <div className="grid grid-cols-2 gap-2 p-3">
        {products.slice(0, 4).map((product) => (
          <Link
            key={product.id}
            to={`/product/${product.id}`}
            className="group/item"
            data-testid={`celeb-product-${product.id}`}
          >
            <div className="aspect-square overflow-hidden bg-white mb-2">
              <img
                src={product.imageUrl}
                alt={product.name}
                className="w-full h-full object-cover group-hover/item:scale-105 transition-transform duration-300"
                loading="lazy"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            </div>
            <p className="text-[10px] text-primary/60 line-clamp-1">{product.brand}</p>
            <p className="text-xs font-medium line-clamp-1 group-hover/item:text-accent transition-colors">{product.name}</p>
            <p className="text-xs font-medium text-accent">
              ₹{product.lowestPrice?.toLocaleString('en-IN') || '—'}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
};

// Celebrity Style Section
const CelebrityStyleSection = ({ celebrityPicks }) => {
  if (!celebrityPicks || celebrityPicks.length === 0) return null;
  
  return (
    <div className="mb-16" data-testid="celebrity-section">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 flex items-center justify-center bg-purple-500/10 text-purple-500">
          <Star className="w-4 h-4" strokeWidth={2} />
        </div>
        <div>
          <h2 className="font-serif text-2xl">Celebrity Style</h2>
          <p className="text-xs text-primary/40">Shop looks worn by icons</p>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {celebrityPicks.map((pick, idx) => (
          <CelebrityCard
            key={pick.celebrity.id}
            celebrity={pick.celebrity}
            products={pick.products}
            idx={idx}
          />
        ))}
      </div>
    </div>
  );
};

// All Brands Section
const AllBrandsSection = ({ brands, onBrandClick }) => {
  if (!brands || brands.length === 0) return null;
  
  return (
    <div className="mb-16" data-testid="all-brands-section">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 flex items-center justify-center bg-accent/10 text-accent">
          <ExternalLink className="w-4 h-4" strokeWidth={2} />
        </div>
        <div>
          <h2 className="font-serif text-2xl">Shop By Brand</h2>
          <p className="text-xs text-primary/40">{brands.length} premium Indian streetwear brands</p>
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {brands.map((brand, idx) => (
          <div
            key={brand.key || idx}
            className="group relative bg-gradient-to-br from-primary/[0.02] to-accent/[0.02] border border-primary/10 hover:border-accent/40 p-4 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg cursor-pointer"
            style={{ animationDelay: `${idx * 0.05}s` }}
            data-testid={`brand-card-${brand.key}`}
            onClick={() => onBrandClick(brand)}
          >
            <div className="text-center">
              <div className="w-12 h-12 mx-auto mb-3 bg-primary/5 rounded-full flex items-center justify-center group-hover:bg-accent/10 transition-colors">
                <span className="text-lg font-bold text-primary/60 group-hover:text-accent transition-colors">
                  {(brand.name || brand.key || '?').charAt(0).toUpperCase()}
                </span>
              </div>
              <h3 className="text-sm font-medium truncate group-hover:text-accent transition-colors">
                {brand.name || brand.key}
              </h3>
              <p className="text-[10px] text-primary/40 mt-1">
                {brand.productCount || 0} drops
              </p>
              {/* External link to official store */}
              <a
                href={brand.websiteUrl || brand.url || '#'}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="inline-flex items-center gap-1 mt-2 text-[10px] text-accent/60 hover:text-accent transition-colors"
              >
                <ExternalLink className="w-2.5 h-2.5" />
                <span>Visit Store</span>
              </a>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 text-center">
        <p className="text-xs text-primary/30">Click a brand to see their drops • "Visit Store" opens official website</p>
      </div>
    </div>
  );
};

export default function BrowsePage() {
  const [searchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [curatedDrops, setCuratedDrops] = useState({ limited_edition: [], trending: [], new_drops: [] });
  const [celebrityPicks, setCelebrityPicks] = useState([]);
  const [allProducts, setAllProducts] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [query, setQuery] = useState('');
  const [selectedBrand, setSelectedBrand] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedSubcategory, setSelectedSubcategory] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [totalProducts, setTotalProducts] = useState(0);
  
  // Ref for filter section to scroll into view
  const filterSectionRef = useRef(null);
  
  // Size First feature
  const [showSizeFirstModal, setShowSizeFirstModal] = useState(false);
  const [userSizePrefs, setUserSizePrefs] = useState(null);
  const [sizeFilterActive, setSizeFilterActive] = useState(false);
  
  // Load size preferences from localStorage or show modal
  useEffect(() => {
    const savedSizePrefs = localStorage.getItem('dropsCurated_sizePrefs');
    if (savedSizePrefs) {
      const prefs = JSON.parse(savedSizePrefs);
      setUserSizePrefs(prefs);
      setSizeFilterActive(!prefs.skipped && prefs.allSizes?.length > 0);
    } else {
      // Show size first modal for new visitors
      const timer = setTimeout(() => {
        setShowSizeFirstModal(true);
      }, 1500); // Show after 1.5 seconds
      return () => clearTimeout(timer);
    }
  }, []);
  
  // Handle saving size preferences
  const handleSaveSizePrefs = (prefs) => {
    setUserSizePrefs(prefs);
    localStorage.setItem('dropsCurated_sizePrefs', JSON.stringify(prefs));
    setSizeFilterActive(!prefs.skipped && prefs.allSizes?.length > 0);
  };
  
  // Clear size filter
  const clearSizeFilter = () => {
    setSizeFilterActive(false);
  };
  
  // Edit size preferences
  const editSizePrefs = () => {
    setShowSizeFirstModal(true);
  };

  // Check for brand filter in URL params
  useEffect(() => {
    const brandParam = searchParams.get('brand');
    if (brandParam && brands.length > 0) {
      const matchedBrand = brands.find(b => 
        b.storeKey === brandParam || 
        b.key?.toUpperCase() === brandParam ||
        b.store_key === brandParam
      );
      if (matchedBrand) {
        setSelectedBrand(matchedBrand);
        fetchAllProducts(1, brandParam, null);
      }
    }
  }, [searchParams, brands]);

  useEffect(() => {
    fetchBrands();
    fetchCuratedDrops();
    fetchCelebrityStyles();
    
    // Only fetch all products if no brand param in URL
    const brandParam = searchParams.get('brand');
    if (!brandParam) {
      fetchAllProducts(1);
    }
    
    // Auto-refresh every 15 minutes
    const refreshTimer = setInterval(() => {
      fetchCuratedDrops(true);
      fetchCelebrityStyles();
    }, AUTO_REFRESH_INTERVAL);
    
    return () => clearInterval(refreshTimer);
  }, []);

  const fetchCelebrityStyles = async () => {
    try {
      const resp = await axios.get(`${API_URL}/celebrity/styles`);
      setCelebrityPicks(resp.data.celebrity_picks || []);
    } catch {}
  };

  const fetchBrands = async () => {
    try {
      const resp = await axios.get(`${API_URL}/scrape/status`);
      setBrands(resp.data.brands || []);
      setTotalProducts(resp.data.total_products || 0);
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

  const fetchAllProducts = async (pageNum, storeFilter = null, searchQuery = null) => {
    if (pageNum === 1) {
      setLoading(true);
    } else {
      setLoadingMore(true);
    }
    try {
      let url = `${API_URL}/search?limit=24&skip=${(pageNum - 1) * 24}`;
      
      // Add search query
      if (searchQuery) {
        url += `&q=${encodeURIComponent(searchQuery)}`;
      }
      
      // Add store filter (for filtering by brand/store like CREPDOG_CREW)
      if (storeFilter) {
        url += `&store=${encodeURIComponent(storeFilter)}`;
      }
      
      // Use shuffle sort when no specific search to keep content fresh
      if (!searchQuery && !storeFilter) {
        url += '&sort=shuffle';
      } else {
        url += '&sort=date'; // Sort by drop date when searching
      }
      
      const resp = await axios.get(url);
      const newProducts = resp.data.products || [];
      
      if (pageNum === 1) {
        setAllProducts(newProducts);
      } else {
        setAllProducts(prev => [...prev, ...newProducts]);
      }
      
      setHasMore(newProducts.length === 24);
      setPage(pageNum);
    } catch {} finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const handleManualRefresh = () => {
    fetchCuratedDrops(true);
    const storeKey = selectedBrand?.storeKey || selectedBrand?.store_key || selectedBrand?.key?.toUpperCase();
    fetchAllProducts(1, storeKey, query);
  };

  const loadMore = () => {
    if (!loadingMore && hasMore) {
      const storeKey = selectedBrand?.storeKey || selectedBrand?.store_key || selectedBrand?.key?.toUpperCase();
      fetchAllProducts(page + 1, storeKey, query);
    }
  };

  // Infinite scroll - detect when user scrolls near bottom
  useEffect(() => {
    const handleScroll = () => {
      if (loadingMore || !hasMore) return;
      
      const scrollTop = window.scrollY;
      const windowHeight = window.innerHeight;
      const docHeight = document.documentElement.scrollHeight;
      
      // Load more when user is 500px from bottom
      if (scrollTop + windowHeight >= docHeight - 500) {
        loadMore();
      }
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [loadingMore, hasMore, page, selectedBrand, query]);

  // Ref for scrolling to new products
  const newProductsRef = useRef(null);

  const fetchProducts = async (q, storeKey) => {
    setPage(1);
    fetchAllProducts(1, storeKey, q);
  };

  const handleSearch = (e) => {
    e?.preventDefault();
    setSelectedBrand(null);
    setPage(1);
    if (query.trim()) {
      fetchAllProducts(1, null, query);
    } else {
      fetchAllProducts(1);
    }
  };

  const handleBrandClick = (brand) => {
    setSelectedBrand(brand);
    setQuery('');
    setPage(1);
    // Use storeKey for accurate filtering
    const storeKey = brand.storeKey || brand.store_key || brand.key?.toUpperCase();
    fetchAllProducts(1, storeKey, null);
    
    // Scroll to the All Drops section
    setTimeout(() => {
      const allDropsSection = document.querySelector('[data-testid="all-products-grid"]');
      if (allDropsSection) {
        allDropsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
  };

  const clearFilters = () => {
    setSelectedBrand(null);
    setSelectedCategory('All');
    setSelectedSubcategory(null);
    setQuery('');
    setPage(1);
    fetchAllProducts(1);
  };

  // Handle filter toggle with auto-scroll
  const handleFilterToggle = () => {
    const newShowFilters = !showFilters;
    setShowFilters(newShowFilters);
    
    // If opening filters, scroll to the filter section
    if (newShowFilters) {
      // Small delay to allow the filter panel to render
      setTimeout(() => {
        if (filterSectionRef.current) {
          filterSectionRef.current.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
          });
        } else {
          // Fallback: scroll to top
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      }, 100);
    }
  };

  // Apply category filter, subcategory filter, and size filter
  const filteredProducts = allProducts.filter(p => {
    // Category filter
    if (selectedCategory !== 'All' && p.category !== selectedCategory) {
      return false;
    }
    
    // Subcategory/Item Type filter (searches in name, tags, description)
    if (selectedSubcategory) {
      const searchTerm = selectedSubcategory.toLowerCase();
      const productName = (p.name || '').toLowerCase();
      const productTags = (p.tags || []).join(' ').toLowerCase();
      const productDesc = (p.description || '').toLowerCase();
      
      // Handle different subcategory search patterns
      let matches = false;
      if (searchTerm === 't-shirts') {
        matches = productName.includes('t-shirt') || productName.includes('tee') || 
                  productTags.includes('t-shirt') || productTags.includes('tee') ||
                  productDesc.includes('t-shirt') || productDesc.includes('tee');
      } else if (searchTerm === 'shirts') {
        // Match "shirt" but not "t-shirt"
        const hasShirt = productName.includes('shirt') || productTags.includes('shirt') || productDesc.includes('shirt');
        const isTShirt = productName.includes('t-shirt') || productName.includes('tee') || 
                         productTags.includes('t-shirt') || productTags.includes('tee');
        matches = hasShirt && !isTShirt;
      } else if (searchTerm === 'collectables') {
        matches = productName.includes('collectab') || productName.includes('collectib') ||
                  productName.includes('figure') || productName.includes('toy') ||
                  productName.includes('bearbrick') || productName.includes('funko') ||
                  productTags.includes('collectab') || productTags.includes('collectib') ||
                  productTags.includes('figure') || productTags.includes('bearbrick');
      } else if (searchTerm === 'hoodies') {
        // Match hoodie, hood, sweatshirt variations
        matches = productName.includes('hoodie') || productName.includes('hood') ||
                  productName.includes('sweatshirt') || productName.includes('pullover') ||
                  productTags.includes('hoodie') || productTags.includes('hood') ||
                  productTags.includes('sweatshirt') ||
                  productDesc.includes('hoodie') || productDesc.includes('sweatshirt');
      } else if (searchTerm === 'jackets') {
        // Match jacket, bomber, windbreaker, coat variations
        matches = productName.includes('jacket') || productName.includes('bomber') ||
                  productName.includes('windbreaker') || productName.includes('coat') ||
                  productName.includes('varsity') || productName.includes('puffer') ||
                  productTags.includes('jacket') || productTags.includes('bomber') ||
                  productTags.includes('outerwear') ||
                  productDesc.includes('jacket');
      } else if (searchTerm === 'pants') {
        // Match pants, trousers, joggers, cargos variations
        matches = productName.includes('pant') || productName.includes('trouser') ||
                  productName.includes('jogger') || productName.includes('cargo') ||
                  productName.includes('jeans') || productName.includes('denim') ||
                  productName.includes('shorts') ||
                  productTags.includes('pants') || productTags.includes('trouser') ||
                  productTags.includes('jogger') || productTags.includes('bottoms') ||
                  productDesc.includes('pant') || productDesc.includes('trouser');
      } else {
        // General fallback search
        matches = productName.includes(searchTerm) || 
                  productTags.includes(searchTerm) || 
                  productDesc.includes(searchTerm);
      }
      
      if (!matches) return false;
    }
    
    // Size filter (if active)
    if (sizeFilterActive && userSizePrefs && userSizePrefs.allSizes?.length > 0) {
      const productSizes = p.attributes?.sizes || p.sizes || [];
      if (!doesProductMatchSize(productSizes, userSizePrefs.allSizes)) {
        return false;
      }
    }
    
    return true;
  });

  return (
    <div className="bg-background min-h-screen" data-testid="browse-page">
      <Header />
      
      {/* Size First Modal */}
      <SizeFirstModal
        isOpen={showSizeFirstModal}
        onClose={() => setShowSizeFirstModal(false)}
        onSave={handleSaveSizePrefs}
        initialSizes={userSizePrefs || {}}
      />
      
      {/* Size Filter Active Banner */}
      {sizeFilterActive && userSizePrefs && (
        <div className="bg-accent/10 border-b border-accent/20 py-2 px-6">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs">
              <Ruler className="w-4 h-4 text-accent" />
              <span className="text-primary/70">Showing products in your size:</span>
              <div className="flex gap-1">
                {userSizePrefs.allSizes?.slice(0, 4).map(s => (
                  <span key={s} className="px-2 py-0.5 bg-accent/20 text-accent text-[10px] font-medium">{s}</span>
                ))}
                {userSizePrefs.allSizes?.length > 4 && (
                  <span className="px-2 py-0.5 bg-primary/10 text-[10px]">+{userSizePrefs.allSizes.length - 4} more</span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={editSizePrefs}
                className="text-[10px] text-accent hover:underline"
                data-testid="edit-sizes-btn"
              >
                Edit
              </button>
              <button
                onClick={clearSizeFilter}
                className="text-[10px] text-primary/40 hover:text-primary"
                data-testid="clear-size-filter"
              >
                Show All Sizes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sticky Search Bar */}
      <div className="sticky top-16 z-40 bg-background/95 backdrop-blur-sm border-b border-primary/5">
        <div className="max-w-7xl mx-auto px-6 md:px-12 py-4">
          <div className="flex flex-col md:flex-row gap-3">
            <form onSubmit={handleSearch} className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/30" strokeWidth={1.5} />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search Nike, Jordan, Yeezy, hoodies, sneakers..."
                className="w-full pl-11 pr-4 py-3 bg-surface border border-primary/10 text-sm placeholder:text-primary/30 focus:outline-none focus:border-accent transition-colors"
                data-testid="search-input"
              />
            </form>
            <button
              onClick={handleFilterToggle}
              className={`inline-flex items-center justify-center gap-2 border px-5 py-3 text-sm transition-colors ${
                showFilters ? 'border-accent bg-accent/5' : 'border-primary/10 hover:border-accent'
              }`}
              data-testid="filter-toggle"
            >
              <SlidersHorizontal className="w-4 h-4" strokeWidth={1.5} />
              Filters
              {showFilters && <X className="w-3 h-3 ml-1" />}
            </button>
          </div>
          
          {/* Last Updated - compact in sticky bar */}
          <div className="flex items-center justify-between mt-3">
            <LastUpdatedBadge 
              lastUpdated={lastUpdated} 
              isRefreshing={isRefreshing}
              onRefresh={handleManualRefresh}
            />
            <p className="text-xs text-primary/30">{totalProducts.toLocaleString()} products tracked</p>
          </div>
        </div>
      </div>

      <main className="pt-6 pb-16">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          {/* Title */}
          <div className="mb-8">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent mb-3">Explore</p>
            <h1 className="font-serif text-4xl md:text-5xl tracking-tight">All Drops</h1>
          </div>

          {/* Filter panel */}
          {showFilters && (
            <div ref={filterSectionRef} className="mb-8 p-6 border border-primary/10 bg-surface animate-fade-up" data-testid="filter-panel">
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
              <div className="mb-6">
                <p className="text-xs text-primary/50 mb-3">Category</p>
                <div className="flex flex-wrap gap-2">
                  {CATEGORIES.map(c => (
                    <button
                      key={c}
                      onClick={() => {
                        setSelectedCategory(c);
                        setSelectedSubcategory(null); // Clear subcategory when changing main category
                      }}
                      className={`text-xs px-4 py-2 border transition-colors ${selectedCategory === c ? 'border-accent text-accent bg-accent/5' : 'border-primary/10 text-primary/60 hover:border-primary/30'}`}
                      data-testid={`category-filter-${c.toLowerCase()}`}
                    >
                      {c === 'All' ? 'All' : c.charAt(0) + c.slice(1).toLowerCase()}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Subcategories / Item Types */}
              <div className="mb-6">
                <p className="text-xs text-primary/50 mb-3">Item Type</p>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setSelectedSubcategory(null)}
                    className={`text-xs px-4 py-2 border transition-colors ${!selectedSubcategory ? 'border-accent text-accent bg-accent/5' : 'border-primary/10 text-primary/60 hover:border-primary/30'}`}
                    data-testid="subcategory-filter-all"
                  >
                    All Types
                  </button>
                  {SUBCATEGORIES.map(sub => (
                    <button
                      key={sub}
                      onClick={() => setSelectedSubcategory(sub)}
                      className={`text-xs px-4 py-2 border transition-colors ${selectedSubcategory === sub ? 'border-accent text-accent bg-accent/5' : 'border-primary/10 text-primary/60 hover:border-primary/30'}`}
                      data-testid={`subcategory-filter-${sub.toLowerCase().replace(/\s/g, '-')}`}
                    >
                      {sub}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Size Filter */}
              <div>
                <p className="text-xs text-primary/50 mb-3">My Size</p>
                <div className="flex items-center gap-3">
                  <button
                    onClick={editSizePrefs}
                    className={`text-xs px-4 py-2 border transition-colors flex items-center gap-2 ${
                      sizeFilterActive 
                        ? 'border-accent text-accent bg-accent/5' 
                        : 'border-primary/10 text-primary/60 hover:border-primary/30'
                    }`}
                    data-testid="size-filter-btn"
                  >
                    <Ruler className="w-3 h-3" />
                    {sizeFilterActive && userSizePrefs?.allSizes?.length > 0
                      ? `${userSizePrefs.allSizes.slice(0, 3).join(', ')}${userSizePrefs.allSizes.length > 3 ? '...' : ''}`
                      : 'Select My Size'
                    }
                  </button>
                  {sizeFilterActive && (
                    <button
                      onClick={clearSizeFilter}
                      className="text-xs text-primary/30 hover:text-primary"
                    >
                      Clear
                    </button>
                  )}
                </div>
                {sizeFilterActive && userSizePrefs?.allSizes?.length > 0 && (
                  <p className="text-[10px] text-green-600 mt-2">
                    Auto-converting: UK ↔ US ↔ EU sizes
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Active filters */}
          {(selectedBrand || selectedCategory !== 'All' || selectedSubcategory) && (
            <div className="flex items-center gap-3 mb-6 text-sm flex-wrap">
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
              {selectedSubcategory && (
                <span className="border border-amber-500/50 text-amber-600 text-xs uppercase tracking-widest px-3 py-1 rounded-full flex items-center gap-1">
                  {selectedSubcategory}
                  <button 
                    onClick={() => setSelectedSubcategory(null)} 
                    className="hover:text-amber-800 ml-1"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              <button onClick={clearFilters} className="text-xs text-primary/30 hover:text-primary ml-2">Clear All</button>
            </div>
          )}

          {/* Content */}
          {loading ? (
            <div className="flex justify-center py-24">
              <RefreshCw className="w-5 h-5 animate-spin text-primary/20" />
            </div>
          ) : (
            <>
              {/* Show curated sections only when no search/filter active */}
              {!query && !selectedBrand && (
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

                  {/* Celebrity Style Section */}
                  <CelebrityStyleSection celebrityPicks={celebrityPicks} />

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

                  {/* All Brands Section */}
                  <AllBrandsSection brands={brands} onBrandClick={handleBrandClick} />
                </>
              )}

              {/* All Products Section */}
              <div className="mt-8">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 flex items-center justify-center bg-primary/5 text-primary">
                      <Clock className="w-4 h-4" strokeWidth={2} />
                    </div>
                    <div>
                      <h2 className="font-serif text-2xl">
                        {query ? `Search: "${query}"` : selectedBrand ? selectedBrand.name : 'All Drops'}
                      </h2>
                      <p className="text-xs text-primary/40">
                        {filteredProducts.length} of {totalProducts.toLocaleString()} products
                      </p>
                    </div>
                  </div>
                </div>

                {filteredProducts.length > 0 ? (
                  <>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-8" data-testid="all-products-grid">
                      {filteredProducts.map((product, idx) => (
                        <ProductCard 
                          key={product.id} 
                          product={product} 
                          idx={idx} 
                          showDate={true}
                        />
                      ))}
                    </div>
                    
                    {/* Infinite scroll loading indicator */}
                    {hasMore && (
                      <div className="flex flex-col items-center justify-center py-12">
                        {loadingMore ? (
                          <div className="flex items-center gap-3 text-primary/40">
                            <RefreshCw className="w-5 h-5 animate-spin text-accent" />
                            <span className="text-sm">Loading more drops...</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 text-xs text-primary/30">
                            <span className="w-8 h-[1px] bg-primary/10" />
                            <span>Scroll for more</span>
                            <span className="w-8 h-[1px] bg-primary/10" />
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* End of results */}
                    {!hasMore && filteredProducts.length > 0 && (
                      <div className="flex flex-col items-center justify-center py-12 text-primary/30">
                        <p className="text-sm">You've seen all {totalProducts.toLocaleString()} drops</p>
                      </div>
                    )}
                    
                    {/* Scroll to top button */}
                    <div className="fixed bottom-20 right-6 z-40">
                      <button
                        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                        className="w-10 h-10 bg-primary text-background flex items-center justify-center shadow-lg hover:bg-accent transition-colors"
                        title="Back to top"
                      >
                        ↑
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-24" data-testid="no-results">
                    <p className="font-serif text-2xl text-primary/30 mb-2">No drops found</p>
                    <p className="text-sm text-primary/20">Try adjusting your search or filters</p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
