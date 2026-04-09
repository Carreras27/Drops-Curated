import React from 'react';
import { Helmet } from 'react-helmet';

/**
 * SEO Component for meta tags (Fix #14 #15)
 * Handles Open Graph, Twitter Cards, and basic SEO
 */
const SEO = ({
  title = "Drops Curated - India's #1 Streetwear Alerts",
  description = "Get instant WhatsApp alerts for price drops and new streetwear collections from 23+ premium Indian brands. ₹399/month.",
  image = "https://drops-curated.preview.emergentagent.com/og-image.jpg",
  url = "https://drops-curated.preview.emergentagent.com",
  type = "website",
  keywords = "streetwear, india, sneakers, fashion alerts, price drop, whatsapp, nike, jordan, yeezy, superkicks"
}) => {
  const siteName = "Drops Curated";
  const twitterHandle = "@dropscurated";

  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      <link rel="canonical" href={url} />

      <meta property="og:type" content={type} />
      <meta property="og:url" content={url} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={image} />
      <meta property="og:site_name" content={siteName} />
      <meta property="og:locale" content="en_IN" />

      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:site" content={twitterHandle} />
      <meta name="twitter:creator" content={twitterHandle} />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={image} />

      <meta name="robots" content="index, follow" />
      <meta name="theme-color" content="#001F3F" />
      <meta name="apple-mobile-web-app-capable" content="yes" />
      <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
      <meta name="apple-mobile-web-app-title" content={siteName} />
    </Helmet>
  );
};

/**
 * Product Page SEO
 */
export const ProductSEO = ({ product }) => {
  if (!product) return <SEO />;

  return (
    <SEO
      title={`${product.name} | Drops Curated`}
      description={`Get alerts for ${product.name} from ${product.brand}. Price: ₹${product.price}. Shop the latest streetwear on Drops Curated.`}
      image={product.imageUrl}
      url={`https://drops-curated.preview.emergentagent.com/product/${product.id}`}
      type="product"
    />
  );
};

/**
 * Brand Page SEO
 */
export const BrandSEO = ({ brand }) => {
  if (!brand) return <SEO />;

  return (
    <SEO
      title={`${brand.name} - Latest Drops & Prices | Drops Curated`}
      description={`Shop ${brand.name} on Drops Curated. Get instant alerts for new releases and price drops. ${brand.productCount || 0}+ products available.`}
      url={`https://drops-curated.preview.emergentagent.com/brands/${brand.key}`}
      type="website"
    />
  );
};

export default SEO;
