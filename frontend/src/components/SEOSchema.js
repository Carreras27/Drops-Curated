import React from 'react';
import { Helmet } from 'react-helmet';

const SITE_URL = 'https://dropscurated.com';
const SITE_NAME = 'Drops Curated';
const SITE_TAGLINE = 'Curated Excellence. Delivered Instantly.';
const SITE_DESCRIPTION = "India's most refined streetwear intelligence platform — a meticulously curated discovery ecosystem that connects discerning collectors and connoisseurs with the finest limited drops, exclusive releases, and premium collections from the country's most respected brands.";

// Generate descriptive alt text for product images
export const generateProductAlt = (product) => {
  if (!product) return 'Streetwear product image';
  
  const brand = product.brand || 'Premium';
  const name = product.name || 'Streetwear Item';
  const store = product.store?.replace(/_/g, ' ') || '';
  const category = product.aiCategory || product.category || 'drop';
  
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

// ============ AVAILABILITY HELPER ============
const getAvailabilitySchema = (product, prices = []) => {
  const isLimited = product.isLimited || 
                    product.is_limited ||
                    product.stockLimit || 
                    (product.tags && product.tags.some(t => 
                      t.toLowerCase().includes('limited') || 
                      t.toLowerCase().includes('exclusive') ||
                      t.toLowerCase().includes('collab') ||
                      t.toLowerCase().includes('rare')
                    ));
  
  const inStock = product.in_stock !== false && product.inStock !== false;
  const hasStock = prices.length > 0 
    ? prices.some(p => p.inStock !== false) 
    : inStock;
  
  if (!hasStock) {
    return "https://schema.org/OutOfStock";
  }
  
  if (isLimited) {
    return "https://schema.org/LimitedAvailability";
  }
  
  return "https://schema.org/InStock";
};

// ============ AGGREGATE RATING HELPER ============
const generateAggregateRating = (product) => {
  if (product.rating && product.reviewCount) {
    return {
      "@type": "AggregateRating",
      "ratingValue": product.rating,
      "reviewCount": product.reviewCount,
      "bestRating": 5,
      "worstRating": 1
    };
  }
  return null;
};

// ============ HOMEPAGE SCHEMAS (@graph) ============
// Combines Organization + WebSite + FAQPage + Service into a single JSON-LD block
export const HomepageSchemas = ({ totalProducts, totalBrands }) => {
  const prodCount = totalProducts || 11700;
  const brandCount = totalBrands || 24;

  const graph = {
    "@context": "https://schema.org",
    "@graph": [
      // Organization
      {
        "@type": "Organization",
        "@id": `${SITE_URL}/#organization`,
        "name": SITE_NAME,
        "alternateName": "Drops Curated India",
        "url": SITE_URL,
        "logo": {
          "@type": "ImageObject",
          "url": `${SITE_URL}/logo.png`,
          "width": 512,
          "height": 512
        },
        "description": SITE_DESCRIPTION,
        "foundingDate": "2024",
        "slogan": SITE_TAGLINE,
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
      },
      // WebSite
      {
        "@type": "WebSite",
        "@id": `${SITE_URL}/#website`,
        "name": SITE_NAME,
        "alternateName": `${SITE_NAME} - ${SITE_TAGLINE}`,
        "url": SITE_URL,
        "description": `${SITE_TAGLINE} Track ${prodCount.toLocaleString()}+ products from ${brandCount} premium Indian streetwear brands. Instant WhatsApp alerts for price drops and new releases.`,
        "inLanguage": "en-IN",
        "publisher": { "@id": `${SITE_URL}/#organization` },
        "potentialAction": {
          "@type": "SearchAction",
          "target": {
            "@type": "EntryPoint",
            "urlTemplate": `${SITE_URL}/browse?search={search_term_string}`
          },
          "query-input": "required name=search_term_string"
        }
      },
      // FAQPage
      {
        "@type": "FAQPage",
        "@id": `${SITE_URL}/#faq`,
        "mainEntity": [
          {
            "@type": "Question",
            "name": "How fast are the WhatsApp alerts?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": `Our alerts are delivered to your WhatsApp within 10 seconds of a price drop or new release being detected. We observe ${brandCount} premium brands every 15 minutes, tracking ${prodCount.toLocaleString()}+ products.`
            }
          },
          {
            "@type": "Question",
            "name": "What brands do you track?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": `We track ${brandCount}+ premium Indian and global streetwear brands including Crep Dog Crew, Huemn, Urban Monkey, VegNonVeg, Superkicks, and more. Total of ${prodCount.toLocaleString()}+ products tracked in real-time.`
            }
          },
          {
            "@type": "Question",
            "name": "How much does the subscription cost?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "The Drops Curated membership costs ₹399 per month with no hidden fees. Cancel anytime. Includes instant WhatsApp alerts, price comparisons, size-first browsing, and privileged early access to drops."
            }
          },
          {
            "@type": "Question",
            "name": "What types of products do you track?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "We track sneakers, hoodies, t-shirts, jackets, accessories, collectibles, watches, and more from premium streetwear brands. Categories include limited editions, new releases, and price drops across all sizes."
            }
          },
          {
            "@type": "Question",
            "name": "Is Drops Curated affiliated with the brands listed?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "No. Drops Curated is an independent discovery and alert platform. We are not affiliated with, endorsed by, or officially connected to any of the brands listed. All purchases are made directly through the brands' own stores."
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
      },
      // Service (Subscription)
      {
        "@type": "Service",
        "@id": `${SITE_URL}/#service`,
        "name": "Drops Curated Premium Membership",
        "serviceType": "Streetwear Intelligence & Alert Service",
        "description": `Premium WhatsApp alerts for streetwear drops and price reductions. Track ${prodCount.toLocaleString()}+ products from ${brandCount} brands. Curated excellence, delivered instantly.`,
        "provider": { "@id": `${SITE_URL}/#organization` },
        "areaServed": {
          "@type": "Country",
          "name": "India"
        },
        "hasOfferCatalog": {
          "@type": "OfferCatalog",
          "name": "Membership Plans",
          "itemListElement": [
            {
              "@type": "Offer",
              "name": "Monthly Membership",
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
          ]
        }
      }
    ]
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(graph) }} />
  );
};

// ============ SINGLE PRODUCT SCHEMA ============
export const ProductSchema = ({ product, prices = [] }) => {
  if (!product) return null;

  const allPrices = prices.filter(p => p.currentPrice > 0).map(p => p.currentPrice);
  const productPrice = product.lowestPrice || product.price || 0;
  const lowestPrice = allPrices.length > 0 ? Math.min(...allPrices) : productPrice;
  const highestPrice = allPrices.length > 0 ? Math.max(...allPrices) : (product.highestPrice || product.original_price || lowestPrice);

  const availability = getAvailabilitySchema(product, prices);
  const aggregateRating = generateAggregateRating(product);

  const schema = {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": product.name,
    "description": product.description || `${product.brand || ''} ${product.name} – Premium streetwear available in India. Discover on Drops Curated.`,
    "image": [product.imageUrl || product.image_url],
    "url": `${SITE_URL}/product/${product.id}`,
    "sku": product.id,
    "mpn": product.shopify_id || product.id,
    "brand": {
      "@type": "Brand",
      "name": product.brand
    },
    "category": product.aiCategory || product.category || "Streetwear",
    "audience": {
      "@type": "PeopleAudience",
      "suggestedGender": product.aiGender || "unisex"
    },
    "offers": lowestPrice !== highestPrice ? {
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
    } : {
      "@type": "Offer",
      "priceCurrency": "INR",
      "price": lowestPrice,
      "availability": availability,
      "itemCondition": "https://schema.org/NewCondition",
      "url": `${SITE_URL}/product/${product.id}`,
      "seller": {
        "@type": "Organization",
        "name": product.store?.replace(/_/g, ' ') || SITE_NAME
      },
      "priceValidUntil": new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    }
  };

  if (aggregateRating) {
    schema.aggregateRating = aggregateRating;
  }

  if (product.available_sizes?.length > 0 || product.attributes?.sizes?.length > 0) {
    schema.size = product.available_sizes || product.attributes.sizes;
  }

  if (product.attributes?.color) {
    schema.color = product.attributes.color;
  }

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
  );
};

// ============ PRODUCT CARD SCHEMA (for inline use in lists) ============
export const ProductCardSchema = ({ product }) => {
  if (!product) return null;

  const availability = getAvailabilitySchema(product);
  const price = product.lowestPrice || product.price || 0;

  return {
    "@type": "Product",
    "name": product.name,
    "image": product.imageUrl || product.image_url,
    "url": `${SITE_URL}/product/${product.id}`,
    "sku": product.id,
    "brand": {
      "@type": "Brand",
      "name": product.brand
    },
    "offers": {
      "@type": "Offer",
      "priceCurrency": "INR",
      "price": price,
      "availability": availability,
      "itemCondition": "https://schema.org/NewCondition",
      "url": `${SITE_URL}/product/${product.id}`
    }
  };
};

// ============ ITEM LIST SCHEMA ============
export const ItemListSchema = ({ products, listName, description, listType = 'ItemList' }) => {
  if (!products || products.length === 0) return null;

  const schema = {
    "@context": "https://schema.org",
    "@type": listType,
    "name": listName || "Streetwear Drops",
    "description": description || "Curated streetwear products from premium Indian brands",
    "numberOfItems": products.length,
    "itemListOrder": "https://schema.org/ItemListOrderDescending",
    "itemListElement": products.slice(0, 50).map((product, index) => {
      const availability = getAvailabilitySchema(product);
      const price = product.lowestPrice || product.price || 0;
      
      return {
        "@type": "ListItem",
        "position": index + 1,
        "item": {
          "@type": "Product",
          "name": product.name,
          "image": product.imageUrl || product.image_url,
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
            "price": price,
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

// ============ SECTION-SPECIFIC SCHEMAS ============
export const NewDropsSchema = ({ products }) => (
  <ItemListSchema 
    products={products}
    listName="New Streetwear Drops"
    description="Latest streetwear releases from premium Indian brands. Fresh drops updated every 15 minutes."
  />
);

export const TrendingSchema = ({ products }) => (
  <ItemListSchema 
    products={products}
    listName="Trending Streetwear Now"
    description="Most popular streetwear items trending in India right now."
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
    description={`Browse ${(totalCount || 11700).toLocaleString()}+ streetwear products from premium Indian and global brands.`}
  />
);

// ============ BREADCRUMB SCHEMA ============
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

// ============ STANDALONE SCHEMAS (backward compat) ============
export const OrganizationSchema = () => {
  const schema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": SITE_NAME,
    "url": SITE_URL,
    "logo": `${SITE_URL}/logo.png`,
    "description": SITE_DESCRIPTION,
    "slogan": SITE_TAGLINE,
    "areaServed": { "@type": "Country", "name": "India" }
  };
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />;
};

export const FAQSchema = () => null; // Merged into HomepageSchemas @graph
export const ServiceSchema = () => null; // Merged into HomepageSchemas @graph
export const WebSiteSchema = () => null; // Merged into HomepageSchemas @graph

// ============ PAGE SEO WITH HELMET ============
export const PageSEO = ({ 
  title, 
  description, 
  path = '',
  image,
  type = 'website'
}) => {
  const safeTitle = title ? String(title) : 'Streetwear Drops';
  const safeDescription = description ? String(description) : SITE_DESCRIPTION;
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
      <meta property="og:site_name" content={SITE_NAME} />
      {image ? <meta property="og:image" content={String(image)} /> : null}
      <meta name="twitter:card" content="summary_large_image" />
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
