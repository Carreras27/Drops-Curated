import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import './App.css';

import LandingPage from './pages/LandingPage';
import BrowsePage from './pages/BrowsePage';
import ProductPage from './pages/ProductPage';
import SubscribePage from './pages/SubscribePage';
import PartnersPage from './pages/PartnersPage';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/browse" element={<BrowsePage />} />
          <Route path="/product/:id" element={<ProductPage />} />
          <Route path="/subscribe" element={<SubscribePage />} />
          <Route path="/partners" element={<PartnersPage />} />
        </Routes>
        <Toaster position="top-center" richColors />
      </div>
    </BrowserRouter>
  );
}

export default App;
