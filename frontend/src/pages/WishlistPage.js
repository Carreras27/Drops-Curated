import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine
} from "recharts";
import { Header, Footer } from './LandingPage';
import { useWishlist } from '../context/WishlistContext';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

// ── Helpers ───────────────────────────────────────────────────────────────────
const fmt = (n) => "₹" + (n || 0).toLocaleString("en-IN");
const pct = (cur, add) => add ? (((cur - add) / add) * 100).toFixed(1) : "0.0";
const isUp = (cur, add) => cur >= add;

// ── Animated Number ───────────────────────────────────────────────────────────
function AnimatedNumber({ value, prefix = "₹", duration = 1200 }) {
  const [display, setDisplay] = useState(0);
  const start = useRef(0);
  const raf = useRef(null);

  useEffect(() => {
    const startVal = start.current;
    const startTime = performance.now();
    const animate = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 4);
      setDisplay(Math.floor(startVal + (value - startVal) * ease));
      if (progress < 1) raf.current = requestAnimationFrame(animate);
      else start.current = value;
    };
    raf.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf.current);
  }, [value, duration]);

  return <span>{prefix}{display.toLocaleString("en-IN")}</span>;
}

// ── Sparkline Tooltip ─────────────────────────────────────────────────────────
function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "rgba(10,10,15,0.95)",
      border: "1px solid rgba(255,255,255,0.1)",
      borderRadius: 8,
      padding: "6px 12px",
      fontSize: 12,
      color: "#fff",
      backdropFilter: "blur(8px)"
    }}>
      {fmt(payload[0].value)}
    </div>
  );
}

// ── Price Graph ───────────────────────────────────────────────────────────────
function PriceGraph({ history, addedPrice, up }) {
  const color = up ? "#00e676" : "#ff1744";
  const gradId = `grad-${Math.random().toString(36).slice(2)}`;

  // Generate mock history if not available
  const chartData = history?.length > 0 ? history : [
    { t: "Day 1", p: addedPrice },
    { t: "Day 2", p: addedPrice * (1 + (Math.random() - 0.5) * 0.05) },
    { t: "Day 3", p: addedPrice * (1 + (Math.random() - 0.5) * 0.05) },
    { t: "Day 4", p: addedPrice * (1 + (Math.random() - 0.5) * 0.05) },
    { t: "Now", p: addedPrice }
  ];

  return (
    <div style={{ width: "100%", height: 80, marginTop: 8 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.35} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="t" hide />
          <YAxis domain={["dataMin - 500", "dataMax + 500"]} hide />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine
            y={addedPrice}
            stroke="rgba(255,255,255,0.2)"
            strokeDasharray="4 4"
          />
          <Area
            type="monotone"
            dataKey="p"
            stroke={color}
            strokeWidth={2}
            fill={`url(#${gradId})`}
            dot={false}
            activeDot={{ r: 4, fill: color, strokeWidth: 0 }}
            animationDuration={1200}
            animationEasing="ease-out"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Size Dots ─────────────────────────────────────────────────────────────────
function SizeDots({ sizes }) {
  if (!sizes || sizes.length === 0) return null;
  
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", margin: "10px 0" }}>
      {sizes.map((s, i) => (
        <div key={i} style={{
          display: "flex", flexDirection: "column", alignItems: "center", gap: 3
        }}>
          <div style={{
            width: 8, height: 8, borderRadius: "50%",
            background: s.available ? "#16a34a" : "#dc2626",
            boxShadow: s.available ? "0 0 6px #16a34a" : "0 0 6px #dc2626",
            transition: "all 0.3s"
          }} />
          <span style={{ fontSize: 9, color: "#64748b", fontFamily: "monospace" }}>{s.size}</span>
        </div>
      ))}
    </div>
  );
}

// ── Wishlist Card ─────────────────────────────────────────────────────────────
function WishlistCard({ item, index, onRemove, livePrice }) {
  const currentPrice = livePrice || item.lowestPrice || item.addedPrice;
  const addedPrice = item.addedPrice || item.lowestPrice || currentPrice;
  const up = isUp(currentPrice, addedPrice);
  const diff = currentPrice - addedPrice;
  const pctVal = pct(currentPrice, addedPrice);
  const [visible, setVisible] = useState(false);
  const [flash, setFlash] = useState(null);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), index * 120);
    return () => clearTimeout(t);
  }, [index]);

  useEffect(() => {
    if (livePrice && livePrice !== addedPrice) {
      setFlash(up ? "up" : "down");
      const t = setTimeout(() => setFlash(null), 800);
      return () => clearTimeout(t);
    }
  }, [livePrice, addedPrice, up]);

  const isFlat = Math.abs(diff) < 1;
  const inStock = item.inStock !== false;
  const stock = item.stock || 10;

  return (
    <div style={{
      background: inStock
        ? "linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%)"
        : "rgba(255,255,255,0.02)",
      border: `1px solid ${flash === "up" ? "rgba(0,230,118,0.5)" : flash === "down" ? "rgba(255,23,68,0.5)" : "rgba(255,255,255,0.07)"}`,
      borderRadius: 20,
      padding: "20px",
      opacity: visible ? (inStock ? 1 : 0.5) : 0,
      transform: visible ? "translateY(0)" : "translateY(24px)",
      transition: "all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)",
      position: "relative",
      overflow: "hidden",
    }}>

      {/* Out of stock overlay */}
      {!inStock && (
        <div style={{
          position: "absolute", top: 14, left: 14,
          background: "rgba(255,23,68,0.15)",
          border: "1px solid rgba(255,23,68,0.4)",
          borderRadius: 20, padding: "3px 10px",
          fontSize: 10, fontWeight: 700, color: "#ff1744",
          letterSpacing: 1,
        }}>
          SOLD OUT
        </div>
      )}

      {/* Top row */}
      <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
        <div style={{ position: "relative", flexShrink: 0 }}>
          <img
            src={item.imageUrl || 'https://placehold.co/72x72/1a1a2e/c9a84c?text=DC'}
            alt={item.name}
            style={{
              width: 72, height: 72, borderRadius: 12,
              objectFit: "cover",
              filter: inStock ? "none" : "grayscale(80%)",
              border: "1px solid rgba(255,255,255,0.08)"
            }}
            onError={(e) => { e.target.src = 'https://placehold.co/72x72/1a1a2e/c9a84c?text=DC'; }}
          />
          {inStock && stock <= 5 && (
            <div style={{
              position: "absolute", bottom: -4, left: "50%",
              transform: "translateX(-50%)",
              background: "#ff6d00",
              borderRadius: 8, padding: "1px 6px",
              fontSize: 8, fontWeight: 800, color: "#fff",
              whiteSpace: "nowrap"
            }}>
              LOW STOCK
            </div>
          )}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: 9, fontWeight: 800, color: "#c9a84c",
            letterSpacing: 2, marginBottom: 3, fontFamily: "monospace"
          }}>
            {item.brand?.toUpperCase() || 'DROPS CURATED'}
          </div>
          <div style={{
            fontSize: 13, fontWeight: 700, color: "#1a1a2e",
            lineHeight: 1.3, marginBottom: 6,
            overflow: "hidden", textOverflow: "ellipsis",
            display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical"
          }}>
            {item.name}
          </div>

          {/* Price */}
          <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
            <span style={{
              fontSize: 20, fontWeight: 900, color: "#1a1a2e",
              fontFamily: "monospace",
              transition: "color 0.3s",
              textShadow: flash === "up" ? "0 0 20px rgba(0,230,118,0.8)" : flash === "down" ? "0 0 20px rgba(255,23,68,0.8)" : "none"
            }}>
              {fmt(currentPrice)}
            </span>
            {!isFlat && (
              <span style={{
                fontSize: 12, fontWeight: 700,
                color: up ? "#dc2626" : "#16a34a",
                display: "flex", alignItems: "center", gap: 2
              }}>
                {up ? "▲" : "▼"} {fmt(Math.abs(diff))} ({up ? "+" : ""}{pctVal}%)
              </span>
            )}
          </div>

          {/* Added price */}
          <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>
            Added at {fmt(addedPrice)} · {item.store || item.category || 'Streetwear'}
            {item.selectedSize && <span style={{ color: "#c9a84c" }}> · Size {item.selectedSize}</span>}
          </div>
        </div>
      </div>

      {/* Graph */}
      <PriceGraph history={item.history} addedPrice={addedPrice} up={!up} />

      {/* Sizes */}
      <SizeDots sizes={item.sizes} />

      {/* Actions */}
      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <Link
          to={`/product/${item.id}`}
          style={{
            flex: 1, background: inStock
              ? "linear-gradient(135deg, #c9a84c, #f0d080)"
              : "rgba(255,255,255,0.06)",
            color: inStock ? "#000" : "rgba(255,255,255,0.3)",
            border: "none", borderRadius: 12,
            padding: "10px 0", fontWeight: 800, fontSize: 12,
            textAlign: "center", textDecoration: "none",
            cursor: inStock ? "pointer" : "not-allowed",
            letterSpacing: 0.5,
            transition: "all 0.2s",
          }}
        >
          {inStock ? "VIEW DROP →" : "OUT OF STOCK"}
        </Link>
        <button
          onClick={() => onRemove(item.id)}
          style={{
            background: "rgba(255,23,68,0.1)",
            border: "1px solid rgba(255,23,68,0.2)",
            borderRadius: 12, padding: "10px 14px",
            color: "#ff1744", cursor: "pointer", fontSize: 14,
            transition: "all 0.2s",
          }}
          data-testid={`remove-${item.id}`}
        >
          ✕
        </button>
      </div>
    </div>
  );
}

// ── Portfolio Header ──────────────────────────────────────────────────────────
function PortfolioHeader({ items, livePrices }) {
  const total = items.reduce((s, i) => s + (livePrices[i.id] || i.lowestPrice || 0), 0);
  const added = items.reduce((s, i) => s + (i.addedPrice || i.lowestPrice || 0), 0);
  const diff = total - added;
  const up = diff >= 0;
  const pctTotal = added > 0 ? ((diff / added) * 100).toFixed(1) : "0.0";
  const inStockCount = items.filter(i => i.inStock !== false).length;

  // Mini portfolio sparkline
  const sparkData = [
    { v: added * 0.98 }, { v: added * 1.01 }, { v: added * 0.99 },
    { v: added * 1.02 }, { v: added * 1.015 }, { v: total }
  ];

  return (
    <div style={{
      background: "linear-gradient(135deg, rgba(201,168,76,0.12) 0%, rgba(201,168,76,0.04) 50%, rgba(10,10,15,0) 100%)",
      border: "1px solid rgba(201,168,76,0.2)",
      borderRadius: 24, padding: "24px",
      marginBottom: 24, position: "relative", overflow: "hidden"
    }}>
      {/* Background decoration */}
      <div style={{
        position: "absolute", top: -40, right: -40,
        width: 180, height: 180, borderRadius: "50%",
        background: "radial-gradient(circle, rgba(201,168,76,0.08) 0%, transparent 70%)",
        pointerEvents: "none"
      }} />

      <div style={{ fontSize: 10, fontWeight: 800, color: "rgba(201,168,76,0.9)", letterSpacing: 3, marginBottom: 8, fontFamily: "monospace" }}>
        MY PORTFOLIO
      </div>

      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: 36, fontWeight: 900, color: "#1a1a2e", fontFamily: "monospace", lineHeight: 1 }}>
            <AnimatedNumber value={total} />
          </div>
          <div style={{
            display: "flex", alignItems: "center", gap: 6, marginTop: 6
          }}>
            <span style={{
              fontSize: 14, fontWeight: 700,
              color: up ? "#dc2626" : "#16a34a",
              display: "flex", alignItems: "center", gap: 4
            }}>
              {up ? "▲" : "▼"} {fmt(Math.abs(diff))}
            </span>
            <span style={{
              fontSize: 12,
              background: up ? "rgba(220,38,38,0.15)" : "rgba(22,163,74,0.15)",
              color: up ? "#dc2626" : "#16a34a",
              padding: "2px 8px", borderRadius: 20, fontWeight: 700
            }}>
              {up ? "+" : ""}{pctTotal}%
            </span>
          </div>
          <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>
            since items added · {inStockCount}/{items.length} in stock
          </div>
        </div>

        {/* Sparkline */}
        <div style={{ width: 100, height: 50 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={sparkData}>
              <defs>
                <linearGradient id="portfolioGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#c9a84c" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#c9a84c" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area
                type="monotone" dataKey="v"
                stroke="#c9a84c" strokeWidth={2}
                fill="url(#portfolioGrad)" dot={false}
                animationDuration={1500}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Stats row */}
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 1fr 1fr",
        gap: 12, marginTop: 20,
        borderTop: "1px solid rgba(255,255,255,0.06)",
        paddingTop: 16
      }}>
        {[
          { label: "ITEMS", value: items.length },
          { label: "IN STOCK", value: inStockCount },
          { label: "PRICE ALERTS", value: items.filter(i => Math.abs(parseFloat(pct(livePrices[i.id] || i.lowestPrice, i.addedPrice || i.lowestPrice))) > 5).length }
        ].map(stat => (
          <div key={stat.label} style={{ textAlign: "center" }}>
            <div style={{ fontSize: 20, fontWeight: 900, color: "#1a1a2e", fontFamily: "monospace" }}>
              {stat.value}
            </div>
            <div style={{ fontSize: 9, color: "#64748b", letterSpacing: 2, marginTop: 2 }}>
              {stat.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Live Ticker ───────────────────────────────────────────────────────────────
function LiveTicker({ items, livePrices }) {
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setOffset(o => o - 1);
    }, 30);
    return () => clearInterval(interval);
  }, []);

  const text = items.slice(0, 5).map(i => {
    const cur = livePrices[i.id] || i.lowestPrice || 0;
    const add = i.addedPrice || i.lowestPrice || cur;
    const up = isUp(cur, add);
    const p = pct(cur, add);
    return `${i.brand?.toUpperCase() || 'DROP'} ${fmt(cur)} ${up ? "▲" : "▼"}${Math.abs(parseFloat(p))}%`;
  }).join("   ·   ");

  if (!text) return null;

  return (
    <div style={{
      background: "rgba(201,168,76,0.08)",
      border: "1px solid rgba(201,168,76,0.15)",
      borderRadius: 12, padding: "8px 16px",
      marginBottom: 20, overflow: "hidden",
      position: "relative"
    }}>
      <div style={{
        display: "flex", gap: 0, alignItems: "center",
        transform: `translateX(${offset % 800}px)`,
        whiteSpace: "nowrap", transition: "none"
      }}>
        <span style={{ fontSize: 10, color: "#92400e", fontFamily: "monospace", fontWeight: 700 }}>
          {text} · {text} · {text}
        </span>
      </div>
    </div>
  );
}

// ── Empty State ───────────────────────────────────────────────────────────────
function EmptyState() {
  return (
    <div style={{
      textAlign: "center", padding: "60px 20px"
    }}>
      <div style={{
        fontSize: 64, marginBottom: 16,
        animation: "float 3s ease-in-out infinite"
      }}>👟</div>
      <h3 style={{ color: "#1a1a2e", fontWeight: 900, fontSize: 20, margin: "0 0 8px" }}>
        Your portfolio is empty
      </h3>
      <p style={{ color: "#64748b", fontSize: 14, margin: "0 0 24px" }}>
        Start adding drops to track prices like a pro
      </p>
      <Link 
        to="/browse"
        style={{
          display: "inline-block",
          background: "linear-gradient(135deg, #c9a84c, #f0d080)",
          color: "#000", border: "none", borderRadius: 12,
          padding: "12px 24px", fontWeight: 800, fontSize: 14,
          cursor: "pointer", textDecoration: "none"
        }}
      >
        Browse Drops →
      </Link>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function WishlistPage() {
  const { wishlist, removeFromWishlist, isLoaded } = useWishlist();
  const [livePrices, setLivePrices] = useState({});
  const [lastUpdate, setLastUpdate] = useState("Just now");

  // Fetch live prices for wishlist items
  useEffect(() => {
    if (wishlist.length === 0) return;

    const fetchPrices = async () => {
      try {
        const productIds = wishlist.map(item => item.id);
        // Fetch current prices from API
        const response = await axios.post(`${API_URL}/products/prices`, { ids: productIds });
        if (response.data?.prices) {
          setLivePrices(response.data.prices);
        }
        setLastUpdate("Just now");
      } catch (err) {
        console.log('Price fetch skipped - using cached prices');
      }
    };

    fetchPrices();
    
    // Refresh prices every 15 minutes
    const interval = setInterval(fetchPrices, 15 * 60 * 1000);
    return () => clearInterval(interval);
  }, [wishlist]);

  // Prepare items with added price (price when added to wishlist)
  const items = wishlist.map(item => ({
    ...item,
    addedPrice: item.lowestPrice || 0,
    currentPrice: livePrices[item.id] || item.lowestPrice || 0,
  }));

  if (!isLoaded) {
    return (
      <div className="bg-background min-h-screen">
        <Header />
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="bg-background min-h-screen" data-testid="wishlist-page">
      <Header />
      
      <div style={{
        minHeight: "calc(100vh - 200px)",
        fontFamily: "'DM Sans', 'Helvetica Neue', sans-serif",
        paddingTop: 100,
        paddingBottom: 40,
      }}>
        <style>{`
          @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.8;transform:scale(1.05)} }
          @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
          @keyframes glow { 0%,100%{box-shadow:0 0 10px rgba(201,168,76,0.3)} 50%{box-shadow:0 0 25px rgba(201,168,76,0.6)} }
        `}</style>

        {/* Header */}
        <div style={{
          padding: "0 20px 20px",
          borderBottom: "1px solid rgba(255,255,255,0.05)",
          marginBottom: 24,
          background: "linear-gradient(180deg, rgba(201,168,76,0.05) 0%, transparent 100%)"
        }}>
          <div className="max-w-2xl mx-auto">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingBottom: 16 }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{
                    width: 8, height: 8, borderRadius: "50%",
                    background: "#00e676",
                    boxShadow: "0 0 8px #00e676",
                    animation: "pulse 2s ease-in-out infinite"
                  }} />
                  <span style={{ fontSize: 10, color: "#00e676", fontWeight: 700, letterSpacing: 2, fontFamily: "monospace" }}>
                    LIVE · {lastUpdate}
                  </span>
                </div>
                <h1 style={{
                  margin: "4px 0 0",
                  fontSize: 26, fontWeight: 900, color: "#1a1a2e",
                  letterSpacing: -0.5
                }}>
                  <span style={{ color: "#1a1a2e" }}>Wishlist</span> <span style={{ color: "#c9a84c" }}>Portfolio</span>
                </h1>
              </div>
              <div style={{
                background: "rgba(201,168,76,0.1)",
                border: "1px solid rgba(201,168,76,0.2)",
                borderRadius: 12, padding: "8px 12px",
                fontSize: 10, color: "#c9a84c", fontWeight: 800,
                letterSpacing: 1, fontFamily: "monospace",
                animation: "glow 3s ease-in-out infinite",
                textAlign: "center"
              }}>
                AUTO-REFRESH<br />15 MIN
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-2xl mx-auto" style={{ padding: "0 16px" }}>
          {/* Live ticker */}
          {items.length > 0 && <LiveTicker items={items} livePrices={livePrices} />}

          {/* Portfolio summary */}
          {items.length > 0 && <PortfolioHeader items={items} livePrices={livePrices} />}

          {/* Cards */}
          {items.length === 0 ? (
            <EmptyState />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {items.map((item, i) => (
                <WishlistCard 
                  key={item.id} 
                  item={item} 
                  index={i} 
                  onRemove={removeFromWishlist}
                  livePrice={livePrices[item.id]}
                />
              ))}
            </div>
          )}

          {/* Legend */}
          {items.length > 0 && (
            <div style={{
              marginTop: 24, padding: 16,
              background: "rgba(201,168,76,0.08)",
              borderRadius: 16, border: "1px solid rgba(201,168,76,0.2)"
            }}>
              <div style={{ fontSize: 10, color: "#92400e", letterSpacing: 2, marginBottom: 12, fontWeight: 700 }}>
                LEGEND
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                {[
                  { dot: "#16a34a", label: "Price down (save!)" },
                  { dot: "#dc2626", label: "Price up" },
                  { dot: "#ea580c", label: "Low stock" },
                  { dot: "#c9a84c", label: "Your tracked items" },
                ].map(l => (
                  <div key={l.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{
                      width: 8, height: 8, borderRadius: "50%",
                      background: l.dot, boxShadow: `0 0 4px ${l.dot}`,
                      flexShrink: 0
                    }} />
                    <span style={{ fontSize: 11, color: "#64748b" }}>{l.label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      
      <Footer />
    </div>
  );
}
