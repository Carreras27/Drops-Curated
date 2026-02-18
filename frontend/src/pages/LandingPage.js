import React from 'react';
import { Link } from 'react-router-dom';
import { Search, Sparkles, Bell, TrendingUp } from 'lucide-react';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <header className="border-b border-gray-200 dark:border-gray-800">
        <nav className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">IndiaShop</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-sm font-medium text-gray-600 hover:text-gray-900">
              Login
            </Link>
            <Link to="/signup" className="text-sm font-bold bg-primary hover:bg-primary-hover text-white px-6 py-2 rounded">
              Sign Up
            </Link>
          </div>
        </nav>
      </header>

      <section className="container mx-auto px-6 py-20">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            Find the <span className="text-primary">Best Prices</span><br />Across India
          </h1>
          <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
            Compare shoes, clothes, and cosmetics from Amazon, Flipkart, Myntra, and 20+ streetwear brands.
          </p>
          <Link to="/signup" className="text-lg font-bold bg-primary hover:bg-primary-hover text-white px-10 py-4 rounded inline-block">
            Start Searching
          </Link>
        </div>
      </section>

      <section className="container mx-auto px-6 py-20 border-t border-gray-200">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
          {[
            { icon: <Search className="w-6 h-6" />, title: 'Smart Search', desc: 'Search by text or image' },
            { icon: <Bell className="w-6 h-6" />, title: 'Price Alerts', desc: 'Get notified on price drops' },
            { icon: <TrendingUp className="w-6 h-6" />, title: 'Trending Drops', desc: 'Never miss limited editions' },
            { icon: <Sparkles className="w-6 h-6" />, title: 'Instagram Drops', desc: 'Track brand releases' },
          ].map((f, i) => (
            <div key={i} className="text-center">
              <div className="w-12 h-12 bg-primary bg-opacity-10 rounded flex items-center justify-center mx-auto mb-4">
                <div className="text-primary">{f.icon}</div>
              </div>
              <h3 className="text-lg font-bold mb-2">{f.title}</h3>
              <p className="text-sm text-gray-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
