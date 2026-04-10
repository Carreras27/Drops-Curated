import React from 'react';
import { Helmet } from 'react-helmet';

const SITE_URL = 'https://drops-curated.preview.emergentagent.com';
const SITE_NAME = 'Drops Curated';
const TOTAL_PRODUCTS = 11371;
const TOTAL_BRANDS = 23;

// Generate descriptive alt text for product images
export const generateProductAlt = (product) => {
  if (!product) return 'Streetwear product image';
  
  const brand = product.brand || 'Premium';
  const name = product.name || 'Streetwear Item';
  const store = product.store?.replace(/_/g, ' ') || '';
  const category = product.aiCategory || product.category || 'drop';
  
  // Create descriptive alt text
  let alt = `${name}`;
  if (brand && !name.toLowerCase().includes(brand.toLowerCase())) {
    alt = `${brand} ${name}`;
  }
  alt += ` – Limited streetwear ${category.toLowerCase()}`;
  if (store) {
    alt += ` from ${store}`;
  }
  
  return alt;
};

// Organization Schema - Enhanced with exact data
export const OrganizationSchema = () => {
  const schema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": SITE_NAME,
    "alternateName": "Drops Curated India",
    "url": SITE_URL,
    "logo": {
      "@type": "ImageObject",
      "url": `${SITE_URL}/logo.png`,
      "width": 512,
      "height": 512
    },
    "description": `Premium Indian streetwear discovery platform tracking ${TOTAL_PRODUCTS.toLocaleString()}+ products from ${TOTAL_BRANDS} brands. Real-time WhatsApp alerts for price drops and new releases.`,
    "foundingDate": "2024",
    "areaServed": {
      "@type": "Country",
      "name": "India"
    },
    "contactPoint": {
      "@type": "ContactPoint",
      "contactType": "customer service",
      "availableLanguage": ["English", "Hindi"],
      "areaServed": "IN"
    },
    "sameAs": [
      "https://instagram.com/dropscurated",
      "https://twitter.com/dropscurated"
    ],
    "knowsAbout": [
      "Streetwear",
      "Sneakers",
      "Indian Fashion",
      "Limited Edition Releases",
      "Price Tracking"
    ]
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
  );
};

// WebSite Schema with SearchAction - Enhanced with exact data
export const WebSiteSchema = () => {
  const schema = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": SITE_NAME,
    "alternateName": "Drops Curated - India's Fastest Streetwear Alerts",
    "url": SITE_URL,
    "description": `India's fastest streetwear alerts. Track ${TOTAL_PRODUCTS.toLocaleString()}+ products from ${TOTAL_BRANDS} premium brands. Price drops, new collections, restocks delivered to WhatsApp in under 10 seconds.`,
    "inLanguage": "en-IN",
    "potentialAction": {
      "@type": "SearchAction",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": `${SITE_URL}/browse?search={search_term_string}`
      },
      "query-input": "required name=search_term_string"
    },
    "publisher": {
      "@type": "Organization",
      "name": SITE_NAME,
      "url": SITE_URL
    }
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
  );
};

// Helper to determine availability schema
const getAvailabilitySchema = (product, prices = []) => {
  // Check if product is limited edition
  const isLimited = product.isLimited || 
                    product.stockLimit || 
                    (product.tags && product.tags.some(t => 
                      t.toLowerCase().includes('limited') || 
                      t.toLowerCase().includes('exclusive')
                    ));
  
  // Check stock status
  const hasStock = prices.length > 0 
    ? prices.some(p => p.inStock !== false) 
    : true;
  
  if (!hasStock) {
    return "https://schema.org/OutOfStock";
  }
  
  if (isLimited) {
    return "https://schema.org/LimitedAvailability";
  }
  
  return "https://schema.org/InStock";
};

// Generate AggregateRating based on product data
const generateAggregateRating = (product) => {
  // If product has real rating data, use it
  if (product.rating && product.reviewCount) {
    return {
      "@type": "AggregateRating",
      "ratingValue": product.rating,
      "reviewCount": product.reviewCount,
      "bestRating": 5,
      "worstRating": 1
    };
  }
  
  // For products without ratings, don't include AggregateRating
  // to avoid misleading schema
  return null;
};

// Single Product Schema - Enhanced with AggregateRating and LimitedAvailability
export const ProductSchema = ({ product, prices = [] }) => {
  if (!product) return null;

  const lowestPrice = prices.length > 0 
    ? Math.min(...prices.filter(p => p.currentPrice > 0).map(p => p.currentPrice))
    : product.lowestPrice || 0;
  
  const highestPrice = prices.length > 0 
    ? Math.max(...prices.filter(p => p.currentPrice > 0).map(p => p.currentPrice))
    : product.highestPrice || lowestPrice;

  const availability = getAvailabilitySchema(product, prices);
  const aggregateRating = generateAggregateRating(product);

  const schema = {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": product.name,
    "description": product.description || `${product.brand} ${product.name} - Premium streetwear available in India. Track price drops and get instant WhatsApp alerts on Drops Curated.`,
    "image": [product.imageUrl],
    "url": `${SITE_URL}/product/${product.id}`,
    "sku": product.id,
    "mpn": product.id,
    "brand": {
      "@type": "Brand",
      "name": product.brand
    },
    "category": product.aiCategory || product.category || "Streetwear",
    "audience": {
      "@type": "PeopleAudience",
      "suggestedGender": product.aiGender || "unisex"
    },
    "offers": {
      "@type": "AggregateOffer",
      "priceCurrency": "INR",
      "lowPrice": lowestPrice,
      "highPrice": highestPrice,
      "offerCount": prices.length || 1,
      "availability": availability,
      "itemCondition": "https://schema.org/NewCondition",
      "seller": {
        "@type": "Organization",
        "name": product.store?.replace(/_/g, ' ') || SITE_NAME
      },
      "priceValidUntil": new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    }
  };

  // Add AggregateRating if available
  if (aggregateRating) {
    schema.aggregateRating = aggregateRating;
  }

  // Add sizes if available
  if (product.attributes?.sizes?.length > 0) {
    schema.size = product.attributes.sizes;
  }

  // Add color if available
  if (product.attributes?.color) {
    schema.color = product.attributes.color;
  }

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
  );
};

// Product Card Schema for lists - Enhanced with availability
export const ProductCardSchema = ({ product }) => {
  if (!product) return null;

  const availability = getAvailabilitySchema(product);

  const schema = {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": product.name,
    "image": product.imageUrl,
    "url": `${SITE_URL}/product/${product.id}`,
    "sku": product.id,
    "brand": {
      "@type": "Brand",
      "name": product.brand
    },
    "offers": {
      "@type": "Offer",
      "priceCurrency": "INR",
      "price": product.lowestPrice || 0,
      "availability": availability,
      "itemCondition": "https://schema.org/NewCondition",
      "url": `${SITE_URL}/product/${product.id}`
    }
  };

  // Add rating if available
  if (product.rating) {
    schema.aggregateRating = {
      "@type": "AggregateRating",
      "ratingValue": product.rating,
      "reviewCount": product.reviewCount || 1,
      "bestRating": 5
    };
  }

  return schema;
};

// ItemList Schema for product collections - Enhanced with full product data
export const ItemListSchema = ({ products, listName, description, listType = 'ItemList' }) => {
  if (!products || products.length === 0) return null;

  const schema = {
    "@context": "https://schema.org",
    "@type": listType,
    "name": listName || "Streetwear Drops",
    "description": description || `Curated streetwear products from ${TOTAL_BRANDS} premium Indian brands`,
    "numberOfItems": products.length,
    "itemListOrder": "https://schema.org/ItemListOrderDescending",
    "itemListElement": products.slice(0, 50).map((product, index) => {
      const availability = getAvailabilitySchema(product);
      
      return {
        "@type": "ListItem",
        "position": index + 1,
        "item": {
          "@type": "Product",
          "name": product.name,
          "image": product.imageUrl,
          "url": `${SITE_URL}/product/${product.id}`,
          "sku": product.id,
          "brand": {
            "@type": "Brand",
            "name": product.brand
          },
          "category": product.aiCategory || product.category || "Streetwear",
          "offers": {
            "@type": "Offer",
            "priceCurrency": "INR",
            "price": product.lowestPrice || 0,
            "availability": availability,
            "itemCondition": "https://schema.org/NewCondition"
          }
        }
      };
    })
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
  );
};

// Specific section schemas for Browse page
export const NewDropsSchema = ({ products }) => (
  <ItemListSchema 
    products={products}
    listName="New Streetwear Drops"
    description={`Latest streetwear releases from ${TOTAL_BRANDS} premium Indian brands. Fresh drops updated every 15 minutes.`}
  />
);

export const TrendingSchema = ({ products }) => (
  <ItemListSchema 
    products={products}
    listName="Trending Streetwear Now"
    description="Most popular streetwear items trending in India right now. Hottest sneakers, hoodies, and limited editions."
  />
);

export const LimitedEditionSchema = ({ products }) => (
  <ItemListSchema 
    products={products}
    listName="Limited Edition Drops"
    description="Exclusive limited availability streetwear drops. Get instant alerts before they sell out."
  />
);

export const AllDropsSchema = ({ products, totalCount }) => (
  <ItemListSchema 
    products={products}
    listName="All Streetwear Drops"
    description={`Browse ${totalCount || TOTAL_PRODUCTS}+ streetwear products from ${TOTAL_BRANDS} premium Indian and global brands.`}
  />
);

// BreadcrumbList Schema
export const BreadcrumbSchema = ({ items }) => {
  if (!items || items.length === 0) return null;

  const schema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": items.map((item, index) => ({
      "@type": "ListItem",
      "position": index + 1,
      "name": item.name,
      "item": item.url ? `${SITE_URL}${item.url}` : undefined
    }))
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
  );
};

// FAQ Schema - Enhanced
export const FAQSchema = () => {
  const schema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "How fast are the WhatsApp alerts?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": `Our alerts are delivered to your WhatsApp within 10 seconds of a price drop or new release being detected. We scan ${TOTAL_BRANDS} premium brands every 15 minutes, tracking ${TOTAL_PRODUCTS.toLocaleString()}+ products.`
        }
      },
      {
        "@type": "Question",
        "name": "What brands do you track?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": `We track ${TOTAL_BRANDS}+ premium Indian and global streetwear brands including Crep Dog Crew, Huemn, Urban Monkey, AMIRI, Nike, On Running, and more. Total of ${TOTAL_PRODUCTS.toLocaleString()}+ products tracked in real-time.`
        }
      },
      {
        "@type": "Question",
        "name": "How much does the subscription cost?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "The Drops Curated membership costs ₹399 per month with no hidden fees. You can cancel anytime. Get instant WhatsApp alerts, price comparisons, and member-only early access to drops."
        }
      },
      {
        "@type": "Question",
        "name": "What types of products do you track?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "We track sneakers, hoodies, t-shirts, jackets, accessories, and collectibles from premium streetwear brands. Categories include limited editions, new releases, and price drops across all sizes."
        }
      },
      {
        "@type": "Question",
        "name": "How do I get alerts for my size?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Set your preferred sizes (UK/US/EU for shoes, XS-XXL for garments) in your profile. We automatically convert sizes and only alert you when products in YOUR size are available or drop in price."
        }
      }
    ]
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
  );
};

// Service Schema for the subscription
export const ServiceSchema = () => {
  const schema = {
    "@context": "https://schema.org",
    "@type": "Service",
    "name": "Drops Curated Premium Membership",
    "serviceType": "Streetwear Alert Service",
    "description": `Premium WhatsApp alerts for streetwear drops and price reductions. Track ${TOTAL_PRODUCTS.toLocaleString()}+ products from ${TOTAL_BRANDS} brands.`,
    "provider": {
      "@type": "Organization",
      "name": SITE_NAME
    },
    "areaServed": {
      "@type": "Country",
      "name": "India"
    },
    "offers": {
      "@type": "Offer",
      "price": "399",
      "priceCurrency": "INR",
      "availability": "https://schema.org/InStock",
      "priceSpecification": {
        "@type": "UnitPriceSpecification",
        "price": "399",
        "priceCurrency": "INR",
        "billingDuration": "P1M",
        "unitText": "month"
      }
    }
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
  );
};

// Combined Homepage Schema Component - Enhanced
export const HomepageSchemas = () => (
  <>
    <OrganizationSchema />
    <WebSiteSchema />
    <FAQSchema />
    <ServiceSchema />
  </>
);

// Page-specific SEO with Helmet
export const PageSEO = ({ 
  title, 
  description, 
  path = '',
  image,
  type = 'website'
}) => {
  const safeTitle = title ? String(title) : 'Streetwear Drops';
  const safeDescription = description ? String(description) : 'Premium Indian streetwear drops with price comparison';
  const fullTitle = safeTitle + ' | ' + SITE_NAME;
  const fullUrl = SITE_URL + path;
  
  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={safeDescription} />
      <link rel="canonical" href={fullUrl} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={safeDescription} />
      <meta property="og:url" content={fullUrl} />
      <meta property="og:type" content={type} />
      {image ? <meta property="og:image" content={String(image)} /> : null}
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={safeDescription} />
    </Helmet>
  );
};

export default {
  generateProductAlt,
  OrganizationSchema,
  WebSiteSchema,
  ProductSchema,
  ProductCardSchema,
  ItemListSchema,
  NewDropsSchema,
  TrendingSchema,
  LimitedEditionSchema,
  AllDropsSchema,
  BreadcrumbSchema,
  FAQSchema,
  ServiceSchema,
  HomepageSchemas,
  PageSEO
};
