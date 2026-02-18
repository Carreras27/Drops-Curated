import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChefHat } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const user = await login(formData.email, formData.password);
      toast.success('Welcome back!');
      navigate(user.role === 'chef' ? '/chef' : '/customer');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-main flex items-center justify-center px-6" data-testid="login-page">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-4">
            <ChefHat className="w-10 h-10 text-primary" />
            <span className="text-3xl font-fredoka font-bold text-text-main">House of Kitchens</span>
          </Link>
          <h1 className="text-3xl font-fredoka font-bold text-text-main mb-2">Welcome Back</h1>
          <p className="text-text-muted">Login to your account to continue</p>
        </div>

        <div className="bg-white rounded-3xl p-8 shadow-lg border border-border-light">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-text-main mb-2">Email</label>
              <input
                type="email"
                data-testid="login-email-input"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full bg-gray-50 border-transparent focus:border-primary focus:bg-white rounded-xl px-4 py-3 transition-all outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="chef@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-main mb-2">Password</label>
              <input
                type="password"
                data-testid="login-password-input"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full bg-gray-50 border-transparent focus:border-primary focus:bg-white rounded-xl px-4 py-3 transition-all outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              data-testid="login-submit-btn"
              disabled={loading}
              className="w-full bg-primary hover:bg-primary-hover text-white rounded-full px-8 py-3 font-bold transition-all transform hover:-translate-y-0.5 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-text-muted">
              Don't have an account?{' '}
              <Link to="/signup" data-testid="signup-link" className="text-primary font-bold hover:underline">
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
