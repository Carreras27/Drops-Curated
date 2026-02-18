import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChefHat } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const SignupPage = () => {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    phone: '',
    role: 'customer',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const user = await signup(
        formData.email,
        formData.password,
        formData.name,
        formData.role,
        formData.phone
      );
      toast.success('Account created successfully!');
      navigate(user.role === 'chef' ? '/chef' : '/customer');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-main flex items-center justify-center px-6 py-12" data-testid="signup-page">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-4">
            <ChefHat className="w-10 h-10 text-primary" />
            <span className="text-3xl font-fredoka font-bold text-text-main">House of Kitchens</span>
          </Link>
          <h1 className="text-3xl font-fredoka font-bold text-text-main mb-2">Join Us Today</h1>
          <p className="text-text-muted">Create your account and start your journey</p>
        </div>

        <div className="bg-white rounded-3xl p-8 shadow-lg border border-border-light">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-text-main mb-2">I am a</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  data-testid="role-customer-btn"
                  onClick={() => setFormData({ ...formData, role: 'customer' })}
                  className={`py-3 px-4 rounded-xl font-bold transition-all ${
                    formData.role === 'customer'
                      ? 'bg-primary text-white shadow-lg'
                      : 'bg-gray-100 text-text-muted hover:bg-gray-200'
                  }`}
                >
                  Customer
                </button>
                <button
                  type="button"
                  data-testid="role-chef-btn"
                  onClick={() => setFormData({ ...formData, role: 'chef' })}
                  className={`py-3 px-4 rounded-xl font-bold transition-all ${
                    formData.role === 'chef'
                      ? 'bg-primary text-white shadow-lg'
                      : 'bg-gray-100 text-text-muted hover:bg-gray-200'
                  }`}
                >
                  Chef
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-main mb-2">Full Name</label>
              <input
                type="text"
                data-testid="signup-name-input"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full bg-gray-50 border-transparent focus:border-primary focus:bg-white rounded-xl px-4 py-3 transition-all outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="John Doe"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-main mb-2">Email</label>
              <input
                type="email"
                data-testid="signup-email-input"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full bg-gray-50 border-transparent focus:border-primary focus:bg-white rounded-xl px-4 py-3 transition-all outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="john@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-main mb-2">Phone (Optional)</label>
              <input
                type="tel"
                data-testid="signup-phone-input"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full bg-gray-50 border-transparent focus:border-primary focus:bg-white rounded-xl px-4 py-3 transition-all outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="+1 234 567 8900"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-main mb-2">Password</label>
              <input
                type="password"
                data-testid="signup-password-input"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full bg-gray-50 border-transparent focus:border-primary focus:bg-white rounded-xl px-4 py-3 transition-all outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              data-testid="signup-submit-btn"
              disabled={loading}
              className="w-full bg-primary hover:bg-primary-hover text-white rounded-full px-8 py-3 font-bold transition-all transform hover:-translate-y-0.5 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-text-muted">
              Already have an account?{' '}
              <Link to="/login" data-testid="login-link" className="text-primary font-bold hover:underline">
                Login
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
