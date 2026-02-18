import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChefHat, Star, MapPin } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const ChefProfile = () => {
  const { chefId } = useParams();
  const [chef, setChef] = useState(null);
  const [menuItems, setMenuItems] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchChefData();
  }, [chefId]);

  const fetchChefData = async () => {
    try {
      const [menuRes, reviewsRes] = await Promise.all([
        axios.get(`${API_URL}/menu/chef/${chefId}`),
        axios.get(`${API_URL}/reviews/chef/${chefId}`),
      ]);
      
      setMenuItems(menuRes.data);
      setReviews(reviewsRes.data);
      
      // Get chef info from first menu item
      if (menuRes.data.length > 0) {
        setChef({
          id: chefId,
          name: menuRes.data[0].chef_name,
          avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${menuRes.data[0].chef_name}`,
        });
      }
    } catch (error) {
      toast.error('Failed to load chef profile');
    } finally {
      setLoading(false);
    }
  };

  const avgRating = reviews.length > 0
    ? (reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length).toFixed(1)
    : 0;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!chef) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text-muted">Chef not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-main font-dmsans py-12 px-6" data-testid="chef-profile-page">
      <div className="container mx-auto max-w-6xl">
        <Link to="/customer" className="inline-flex items-center gap-2 mb-8 text-primary hover:underline">
          ← Back to Browse
        </Link>

        {/* Chef Header */}
        <div className="bg-white rounded-3xl p-8 shadow-lg border border-border-light mb-8">
          <div className="flex items-center gap-6 mb-6">
            <img
              src={chef.avatar}
              alt={chef.name}
              className="w-24 h-24 rounded-full border-4 border-primary/10"
            />
            <div>
              <h1 className="text-3xl font-fredoka font-bold text-text-main mb-2">{chef.name}</h1>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Star className="w-5 h-5 text-accent fill-accent" />
                  <span className="font-bold text-text-main">{avgRating}</span>
                  <span className="text-text-muted">({reviews.length} reviews)</span>
                </div>
                <span className="px-3 py-1 bg-secondary/10 text-secondary rounded-full text-sm font-bold">
                  {menuItems.length} Dishes
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Menu Items */}
        <div className="mb-8">
          <h2 className="text-2xl font-fredoka font-bold text-text-main mb-6">Menu</h2>
          {menuItems.length === 0 ? (
            <p className="text-center text-text-muted py-12">No menu items available</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {menuItems.map((item) => (
                <div
                  key={item.id}
                  className="bg-white rounded-3xl overflow-hidden shadow-sm hover:shadow-md transition-all group border border-gray-100"
                >
                  <div className="relative h-48">
                    <img
                      src={item.image_url}
                      alt={item.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    <div className="absolute top-3 right-3 bg-accent text-black px-3 py-1 rounded-full text-sm font-bold">
                      ${item.price.toFixed(2)}
                    </div>
                  </div>
                  <div className="p-5">
                    <h3 className="text-xl font-fredoka font-bold text-text-main mb-2">{item.name}</h3>
                    <p className="text-text-muted text-sm mb-3 line-clamp-2">{item.description}</p>
                    <span className="text-xs bg-secondary/10 text-secondary px-2 py-1 rounded-full font-medium">
                      {item.category}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Reviews */}
        <div>
          <h2 className="text-2xl font-fredoka font-bold text-text-main mb-6">Reviews</h2>
          {reviews.length === 0 ? (
            <p className="text-center text-text-muted py-12">No reviews yet</p>
          ) : (
            <div className="space-y-4">
              {reviews.map((review) => (
                <div
                  key={review.id}
                  className="bg-white rounded-3xl p-6 border border-border-light"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <img
                        src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${review.customer_name}`}
                        alt={review.customer_name}
                        className="w-10 h-10 rounded-full"
                      />
                      <div>
                        <p className="font-bold text-text-main">{review.customer_name}</p>
                        <p className="text-xs text-text-muted">
                          {new Date(review.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`w-4 h-4 ${
                            i < review.rating
                              ? 'text-accent fill-accent'
                              : 'text-gray-300'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                  <p className="text-text-muted">{review.comment}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChefProfile;
