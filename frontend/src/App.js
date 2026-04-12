import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import './App.css';

import LandingPage from './pages/LandingPage';
import BrowsePage from './pages/BrowsePage';
import ProductPage from './pages/ProductPage';
import SubscribePage from './pages/SubscribePage';
import PartnersPage from './pages/PartnersPage';
import RafflesPage from './pages/RafflesPage';
import BrandsPage, { BrandPage } from './pages/BrandsPage';
import AdminPanel from './pages/AdminPanel';
import AboutPage from './pages/AboutPage';
import FAQPage from './pages/FAQPage';
import ContactPage from './pages/ContactPage';
import WishlistPage from './pages/WishlistPage';
import { WishlistProvider } from './context/WishlistContext';
import { ThemeProvider } from './context/ThemeContext';

// Error Boundary Component (Fix #9)
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-background flex items-center justify-center p-8">
          <div className="text-center">
            <h1 className="text-4xl font-serif text-primary mb-4">Something went wrong</h1>
            <p className="text-primary/50 mb-6">We're sorry, but something unexpected happened.</p>
            <button
              onClick={() => window.location.href = '/'}
              className="px-6 py-3 bg-accent text-background hover:bg-accent/90 transition-colors"
            >
              Go Home
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// 404 Not Found Component
function NotFound() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-8">
      <div className="text-center">
        <h1 className="text-6xl font-serif text-primary mb-4">404</h1>
        <p className="text-xl text-primary/50 mb-6">Page not found</p>
        <a
          href="/"
          className="inline-block px-6 py-3 bg-accent text-background hover:bg-accent/90 transition-colors"
        >
          Go Home
        </a>
      </div>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <WishlistProvider>
          <BrowserRouter>
            <div className="min-h-screen bg-background transition-colors duration-300">
              <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/browse" element={<BrowsePage />} />
                <Route path="/brands" element={<BrandsPage />} />
                <Route path="/brands/:brandKey" element={<BrandPage />} />
                <Route path="/product/:id" element={<ProductPage />} />
                <Route path="/subscribe" element={<SubscribePage />} />
                <Route path="/partners" element={<PartnersPage />} />
                <Route path="/raffles" element={<RafflesPage />} />
                <Route path="/about" element={<AboutPage />} />
                <Route path="/faq" element={<FAQPage />} />
                <Route path="/contact" element={<ContactPage />} />
                <Route path="/wishlist" element={<WishlistPage />} />
                <Route path="/admin" element={<AdminPanel />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
              <Toaster position="top-center" richColors />
            </div>
          </BrowserRouter>
        </WishlistProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
