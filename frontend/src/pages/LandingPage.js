import React from 'react';
import { Link } from 'react-router-dom';
import { ChefHat, Clock, Star, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';

const LandingPage = () => {
  return (
    <div className="min-h-screen font-dmsans">
      {/* Header */}
      <header className="fixed top-0 w-full bg-white/90 backdrop-blur-md z-50 border-b border-border-light">
        <nav className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ChefHat className="w-8 h-8 text-primary" />
            <span className="text-2xl font-fredoka font-bold text-text-main">House of Kitchens</span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              to="/login"
              data-testid="login-link"
              className="text-text-main hover:text-primary transition-colors font-medium"
            >
              Login
            </Link>
            <Link
              to="/signup"
              data-testid="signup-link"
              className="bg-primary hover:bg-primary-hover text-white rounded-full px-6 py-2.5 font-bold transition-all transform hover:-translate-y-0.5 shadow-lg"
            >
              Get Started
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section - Bento Grid */}
      <section className="pt-32 pb-20 px-6" data-testid="hero-section">
        <div className="container mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-fredoka font-bold text-text-main mb-6 leading-tight">
              Homemade Food,
              <br />
              <span className="text-primary">Made With Love</span>
            </h1>
            <p className="text-lg md:text-xl text-text-muted max-w-2xl mx-auto mb-8">
              Connect with talented home chefs in your neighborhood and enjoy authentic,
              delicious homemade meals delivered to your door.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/signup"
                data-testid="hero-get-started-btn"
                className="bg-primary hover:bg-primary-hover text-white rounded-full px-10 py-4 text-lg font-bold transition-all transform hover:-translate-y-0.5 shadow-lg inline-block"
              >
                Order Now
              </Link>
              <Link
                to="/signup"
                data-testid="hero-become-chef-btn"
                className="bg-white border-2 border-primary text-primary hover:bg-orange-50 rounded-full px-10 py-4 text-lg font-bold transition-all inline-block"
              >
                Become a Chef
              </Link>
            </div>
          </motion.div>

          {/* Bento Grid */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 max-w-7xl mx-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="md:col-span-7 rounded-3xl overflow-hidden shadow-lg h-[400px]"
            >
              <img
                src="https://images.unsplash.com/photo-1758522484068-4ba2b78add9e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwxfHxob21lJTIwY2hlZiUyMGNvb2tpbmclMjBraXRjaGVuJTIwaGFwcHl8ZW58MHx8fHwxNzcxNDAxMzE1fDA&ixlib=rb-4.1.0&q=85"
                alt="Happy home chef cooking"
                className="w-full h-full object-cover"
              />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="md:col-span-5 rounded-3xl overflow-hidden shadow-lg h-[400px]"
            >
              <img
                src="https://images.unsplash.com/photo-1696385793103-71f51f6fd3b7?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwxfHxkZWxpY2lvdXMlMjBob21lbWFkZSUyMGZvb2QlMjBzcHJlYWQlMjB2aWJyYW50fGVufDB8fHx8MTc3MTQwMTMxNnww&ixlib=rb-4.1.0&q=85"
                alt="Delicious food spread"
                className="w-full h-full object-cover"
              />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="md:col-span-5 rounded-3xl overflow-hidden shadow-lg h-[300px]"
            >
              <img
                src="https://images.pexels.com/photos/3785706/pexels-photo-3785706.jpeg"
                alt="Chef preparing meal"
                className="w-full h-full object-cover"
              />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="md:col-span-7 rounded-3xl overflow-hidden shadow-lg h-[300px]"
            >
              <img
                src="https://images.unsplash.com/photo-1727018953313-403d17215a1b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwzfHxkZWxpY2lvdXMlMjBob21lbWFkZSUyMGZvb2QlMjBzcHJlYWQlMjB2aWJyYW50fGVufDB8fHx8MTc3MTQwMTMxNnww&ixlib=rb-4.1.0&q=85"
                alt="Traditional Indian Thali"
                className="w-full h-full object-cover"
              />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 bg-white" data-testid="features-section">
        <div className="container mx-auto max-w-6xl">
          <h2 className="text-4xl md:text-5xl font-fredoka font-bold text-center text-text-main mb-16">
            Why Choose Us?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                icon: <ChefHat className="w-10 h-10 text-primary" />,
                title: 'Talented Chefs',
                description: 'Connect with skilled home chefs who cook with passion',
              },
              {
                icon: <Clock className="w-10 h-10 text-primary" />,
                title: 'Fresh & Fast',
                description: 'Order fresh homemade meals prepared on demand',
              },
              {
                icon: <Star className="w-10 h-10 text-primary" />,
                title: 'Quality Assured',
                description: 'Rated and reviewed by our community',
              },
              {
                icon: <ShieldCheck className="w-10 h-10 text-primary" />,
                title: 'Safe & Secure',
                description: 'Verified chefs and secure payment processing',
              },
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="bg-bg-main rounded-3xl p-8 text-center border border-border-light hover:shadow-lg transition-all"
              >
                <div className="flex justify-center mb-4">{feature.icon}</div>
                <h3 className="text-xl font-fredoka font-bold text-text-main mb-3">
                  {feature.title}
                </h3>
                <p className="text-text-muted">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gradient-to-r from-primary to-accent" data-testid="cta-section">
        <div className="container mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-fredoka font-bold text-white mb-6">
            Ready to Start?
          </h2>
          <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
            Join our community of food lovers and talented home chefs today!
          </p>
          <Link
            to="/signup"
            data-testid="cta-signup-btn"
            className="bg-white text-primary hover:bg-gray-50 rounded-full px-10 py-4 text-lg font-bold transition-all transform hover:-translate-y-0.5 shadow-lg inline-block"
          >
            Join Now
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-text-main text-white py-12 px-6">
        <div className="container mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <ChefHat className="w-6 h-6" />
            <span className="text-xl font-fredoka font-bold">House of Kitchens</span>
          </div>
          <p className="text-white/70">
            Connecting home chefs with food lovers since 2025
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
