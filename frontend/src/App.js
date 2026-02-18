import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import { Toaster } from 'sonner';
import './App.css';

// Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import CustomerDashboard from './pages/CustomerDashboard';
import ChefDashboard from './pages/ChefDashboard';
import ChefProfile from './pages/ChefProfile';
import CheckoutPage from './pages/CheckoutPage';
import OrderSuccess from './pages/OrderSuccess';
import OrderTracking from './pages/OrderTracking';

const PrivateRoute = ({ children, role }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (role && user.role !== role) {
    return <Navigate to={user.role === 'chef' ? '/chef' : '/customer'} />;
  }

  return children;
};

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={user ? <Navigate to={user.role === 'chef' ? '/chef' : '/customer'} /> : <LandingPage />} />
      <Route path="/login" element={user ? <Navigate to={user.role === 'chef' ? '/chef' : '/customer'} /> : <LoginPage />} />
      <Route path="/signup" element={user ? <Navigate to={user.role === 'chef' ? '/chef' : '/customer'} /> : <SignupPage />} />
      <Route
        path="/customer/*"
        element={
          <PrivateRoute role="customer">
            <CustomerDashboard />
          </PrivateRoute>
        }
      />
      <Route
        path="/chef/*"
        element={
          <PrivateRoute role="chef">
            <ChefDashboard />
          </PrivateRoute>
        }
      />
      <Route path="/chef/:chefId" element={<ChefProfile />} />
      <Route
        path="/checkout"
        element={
          <PrivateRoute role="customer">
            <CheckoutPage />
          </PrivateRoute>
        }
      />
      <Route
        path="/order-success"
        element={
          <PrivateRoute role="customer">
            <OrderSuccess />
          </PrivateRoute>
        }
      />
      <Route
        path="/order/:orderId"
        element={
          <PrivateRoute>
            <OrderTracking />
          </PrivateRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <CartProvider>
          <div className="App">
            <AppRoutes />
            <Toaster position="top-center" richColors />
          </div>
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
