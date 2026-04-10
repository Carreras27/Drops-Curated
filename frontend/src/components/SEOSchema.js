import React from 'react';
import { Helmet } from 'react-helmet';

const SITE_URL = 'https://drops-curated.preview.emergentagent.com';
const SITE_NAME = 'Drops Curated';

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

// Organization Schema
export const OrganizationSchema = () => {
  const schema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": SITE_NAME,
    "url": SITE_URL,
    "logo": `${SITE_URL}/logo.png`,
    "description": "Premium Indian streetwear discovery platform with real-time WhatsApp alerts for price drops and new releases.",
    "foundingDate": "2024",
    "contactPoint": {
      "@type": "ContactPoint",
      "contactType": "customer service",
      "availableLanguage": ["English", "Hindi"]
    },
    "sameAs": [
      "https://instagram.com/dropscurated",
      "https://twitter.com/dropscurated"
    ]
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
  );
};

// WebSite Schema with SearchAction
export const WebSiteSchema = () => {
  const schema = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": SITE_NAME,
    "url": SITE_URL,
    "description": "India's fastest streetwear alerts. Track 11,371+ products from 23 premium brands. Price drops, new collections, restocks delivered to WhatsApp in under 10 seconds.",
    "potentialAction": {
      "@type": "SearchAction",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": `${SITE_URL}/browse?search={search_term_string}`
      },
      "query-input": "required name=search_term_string"
    }
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
  );
};

// Single Product Schema
export const ProductSchema = ({ product, prices = [] }) => {
  if (!product) return null;

  const lowestPrice = prices.length > 0 
    ? Math.min(...prices.map(p => p.currentPrice || Infinity))
    : product.lowestPrice || 0;
  
  const highestPrice = prices.length > 0 
    ? Math.max(...prices.map(p => p.currentPrice || 0))
    : product.highestPrice || lowestPrice;

  const inStock = prices.length > 0 
    ? prices.some(p => p.inStock)
    : true;

  const schema = {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": product.name,
    "description": product.description || `${product.brand} ${product.name} - Premium streetwear available in India. Track price drops and get instant WhatsApp alerts.`,
    "image": product.imageUrl,
    "url": `${SITE_URL}/product/${product.id}`,
    "brand": {
      "@type": "Brand",
      "name": product.brand
    },
    "category": product.aiCategory || product.category || "Streetwear",
    "sku": product.id,
    "offers": {
      "@type": "AggregateOffer",
      "priceCurrency": "INR",
      "lowPrice": lowestPrice,
      "highPrice": highestPrice,
      "offerCount": prices.length || 1,
      "availability": inStock 
        ? "https://schema.org/InStock" 
        : "https://schema.org/OutOfStock",
      "seller": {
        "@type": "Organization",
        "name": product.store?.replace(/_/g, ' ') || SITE_NAME
      }
    }
  };

  // Add sizes if available
  if (product.attributes?.sizes?.length > 0) {
    schema.size = product.attributes.sizes;
  }

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
  );
};

// Product Card Schema (lightweight for lists)
export const ProductCardSchema = ({ product }) => {
  if (!product) return null;

  const schema = {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": product.name,
    "image": product.imageUrl,
    "url": `${SITE_URL}/product/${product.id}`,
    "brand": {
      "@type": "Brand",
      "name": product.brand
    },
    "offers": {
      "@type": "Offer",
      "priceCurrency": "INR",
      "price": product.lowestPrice || 0,
      "availability": "https://schema.org/InStock",
      "url": `${SITE_URL}/product/${product.id}`
    }
  };

  return schema;
};

// ItemList Schema for product collections
export const ItemListSchema = ({ products, listName, description }) => {
  if (!products || products.length === 0) return null;

  const schema = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": listName || "Streetwear Drops",
    "description": description || "Curated streetwear products from premium Indian brands",
    "numberOfItems": products.length,
    "itemListElement": products.slice(0, 50).map((product, index) => ({
      "@type": "ListItem",
      "position": index + 1,
      "item": {
        "@type": "Product",
        "name": product.name,
        "image": product.imageUrl,
        "url": `${SITE_URL}/product/${product.id}`,
        "brand": {
          "@type": "Brand",
          "name": product.brand
        },
        "offers": {
          "@type": "Offer",
          "priceCurrency": "INR",
          "price": product.lowestPrice || 0,
          "availability": "https://schema.org/InStock"
        }
      }
    }))
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
  );
};

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

// FAQ Schema (for landing page)
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
          "text": "Our alerts are delivered to your WhatsApp within 10 seconds of a price drop or new release being detected. We scan 23 premium brands every 15 minutes."
        }
      },
      {
        "@type": "Question",
        "name": "What brands do you track?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "We track 23+ premium Indian and global streetwear brands including Crep Dog Crew, Huemn, Urban Monkey, AMIRI, Nike, and more."
        }
      },
      {
        "@type": "Question",
        "name": "How much does the subscription cost?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "The Drops Curated membership costs ₹399 per month with no hidden fees. You can cancel anytime."
        }
      }
    ]
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
  );
};

// Combined Homepage Schema Component
export const HomepageSchemas = () => (
  <>
    <OrganizationSchema />
    <WebSiteSchema />
    <FAQSchema />
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
  // Ensure all values are strings to avoid Helmet errors
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
  BreadcrumbSchema,
  FAQSchema,
  HomepageSchemas,
  PageSEO
};
