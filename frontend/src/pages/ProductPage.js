import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Sparkles } from 'lucide-react';

const ProductPage = () => {
  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <header className="border-b border-gray-200 dark:border-gray-800">
        <nav className="container mx-auto px-6 py-4">
          <Link to="/search" className="flex items-center gap-2 hover:text-primary">
            <ArrowLeft className="w-5 h-5" />
            <span className="font-medium">Back to Search</span>
          </Link>
        </nav>
      </header>
      <main className="container mx-auto px-6 py-12">
        <div className="text-center py-20">
          <Sparkles className="w-16 h-16 text-primary mx-auto mb-4" />
          <h1 className="text-3xl font-bold mb-4">Product Detail Page</h1>
          <p className="text-gray-600">Coming soon - Price comparison across stores</p>
        </div>
      </main>
    </div>
  );
};

export default ProductPage;
