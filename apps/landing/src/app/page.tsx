'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  BarChart3, 
  Layers, 
  Zap, 
  ShieldCheck, 
  ArrowRight,
  Globe,
  ShoppingCart,
  Boxes
} from 'lucide-react';

const Navbar = () => (
  <nav className="fixed top-0 w-full z-50 px-6 py-4">
    <div className="max-w-7xl mx-auto flex justify-between items-center glass-morphism rounded-full px-8 py-3">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 bg-michi-purple rounded-lg flex items-center justify-center font-bold text-white">道</div>
        <span className="font-outfit text-xl font-bold tracking-tight">Michi</span>
      </div>
      <div className="hidden md:flex items-center gap-8 text-sm font-medium text-michi-gray">
        <a href="#features" className="hover:text-white transition-colors">Features</a>
        <a href="#integrations" className="hover:text-white transition-colors">Integrations</a>
        <a href="#about" className="hover:text-white transition-colors">About</a>
      </div>
      <button className="bg-michi-purple hover:bg-michi-purple/90 text-white px-6 py-2 rounded-full text-sm font-semibold transition-all">
        Get Started
      </button>
    </div>
  </nav>
);

const FeatureCard = ({ icon: Icon, title, description }: { icon: any, title: string, description: string }) => (
  <motion.div 
    whileHover={{ y: -5 }}
    className="p-8 rounded-3xl glass-morphism group"
  >
    <div className="w-12 h-12 rounded-2xl bg-michi-purple/10 flex items-center justify-center mb-6 group-hover:bg-michi-purple/20 transition-colors">
      <Icon className="w-6 h-6 text-michi-purple" />
    </div>
    <h3 className="font-outfit text-xl font-bold mb-4">{title}</h3>
    <p className="text-michi-gray leading-relaxed">{description}</p>
  </motion.div>
);

export default function LandingPage() {
  return (
    <main className="relative min-h-screen pt-24 pb-20 px-6">
      <Navbar />

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto pt-20 pb-32 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <span className="inline-block px-4 py-1.5 rounded-full bg-michi-purple/10 border border-michi-purple/20 text-michi-purple text-xs font-bold uppercase tracking-widest mb-6">
            Smarter Inventory Intelligence
          </span>
          <h1 className="font-outfit text-5xl md:text-7xl font-extrabold mb-8 tracking-tight">
            Master Your <span className="gradient-text">Omnichannel</span> <br /> Supply Chain
          </h1>
          <p className="max-w-2xl mx-auto text-michi-gray text-lg md:text-xl mb-12 leading-relaxed">
            Michi provides AI-driven forecasting for Shopify, Amazon, and WooCommerce sellers. 
            Reduce stockouts, optimize cash flow, and scale with confidence.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button className="w-full sm:w-auto bg-michi-purple hover:bg-michi-purple/90 text-white px-8 py-4 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all">
              Book a Demo <ArrowRight className="w-5 h-5" />
            </button>
            <button className="w-full sm:w-auto glass-morphism hover:bg-white/10 px-8 py-4 rounded-2xl font-bold transition-all">
              Explore Features
            </button>
          </div>
        </motion.div>
      </section>

      {/* Social Proof / Stats */}
      <section className="max-w-7xl mx-auto mb-32">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { label: 'Forecast Accuracy', value: '98%' },
            { label: 'Revenue Growth', value: '3.5x' },
            { label: 'Stockout Reduction', value: '85%' },
            { label: 'API Integrations', value: '50+' },
          ].map((stat, idx) => (
            <div key={idx} className="text-center">
              <div className="text-3xl md:text-4xl font-outfit font-bold mb-2">{stat.value}</div>
              <div className="text-michi-gray text-sm font-medium">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="max-w-7xl mx-auto mb-32">
        <div className="text-center mb-16">
          <h2 className="font-outfit text-3xl md:text-5xl font-bold mb-6">Everything you need to grow</h2>
          <p className="text-michi-gray max-w-2xl mx-auto">
            Powerful tools designed for modern e-commerce teams managing multiple sales channels.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          <FeatureCard 
            icon={TrendingUp}
            title="Predictive Analytics"
            description="Our AI models analyze historical data and trends to predict future demand with surgical precision."
          />
          <FeatureCard 
            icon={Layers}
            title="Multi-Store Sync"
            description="Connect Shopify, Amazon, and WooCommerce in one dashboard for a single source of truth."
          />
          <FeatureCard 
            icon={Zap}
            title="Automated Replenishment"
            description="Get smart alerts when it's time to reorder, with calculated quantities based on lead times."
          />
          <FeatureCard 
            icon={ShieldCheck}
            title="Risk Mitigation"
            description="Identify potential supply chain disruptions before they happen with our risk scoring engine."
          />
          <FeatureCard 
            icon={Globe}
            title="Global Operations"
            description="Manage multiple warehouses and currencies effortlessly across international markets."
          />
          <FeatureCard 
            icon={BarChart3}
            title="Profitability Insights"
            description="Understand your true margins by accounting for shipping, storage, and platform fees."
          />
        </div>
      </section>

      {/* Integration Section */}
      <section id="integrations" className="max-w-7xl mx-auto mb-32 py-20 rounded-[3rem] bg-gradient-to-b from-white/[0.02] to-transparent border border-white/5 overflow-hidden">
        <div className="flex flex-col md:flex-row items-center gap-12 px-12">
          <div className="flex-1">
            <h2 className="font-outfit text-3xl md:text-4xl font-bold mb-6">Connect your entire <br /> ecosystem</h2>
            <p className="text-michi-gray mb-8 leading-relaxed">
              Michi integrates directly with the platforms you already use. 
              No manual CSV uploads, no messy spreadsheets. Just clean, automated data.
            </p>
            <div className="flex flex-wrap gap-4">
              <div className="px-4 py-2 rounded-xl glass-morphism flex items-center gap-2">
                <ShoppingCart className="w-4 h-4 text-michi-purple" /> <span>Shopify</span>
              </div>
              <div className="px-4 py-2 rounded-xl glass-morphism flex items-center gap-2">
                <Globe className="w-4 h-4 text-orange-400" /> <span>Amazon</span>
              </div>
              <div className="px-4 py-2 rounded-xl glass-morphism flex items-center gap-2">
                <Boxes className="w-4 h-4 text-blue-400" /> <span>WooCommerce</span>
              </div>
            </div>
          </div>
          <div className="flex-1 relative">
            <div className="w-full aspect-square max-w-[400px] mx-auto relative flex items-center justify-center">
              <div className="absolute inset-0 bg-michi-purple/20 blur-[100px] rounded-full" />
              <motion.div 
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="w-full h-full border border-white/10 rounded-full flex items-center justify-center"
              >
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-12 h-12 glass-morphism rounded-xl flex items-center justify-center">
                  <ShoppingCart className="w-6 h-6" />
                </div>
                <div className="absolute top-1/2 -right-4 -translate-y-1/2 w-12 h-12 glass-morphism rounded-xl flex items-center justify-center">
                  <Globe className="w-6 h-6" />
                </div>
                <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-12 h-12 glass-morphism rounded-xl flex items-center justify-center">
                  <Boxes className="w-6 h-6" />
                </div>
              </motion.div>
              <div className="absolute w-24 h-24 bg-michi-purple rounded-3xl flex items-center justify-center font-bold text-4xl shadow-[0_0_50px_rgba(108,92,231,0.5)]">
                道
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-5xl mx-auto text-center py-20 px-12 rounded-[3rem] bg-michi-purple relative overflow-hidden shadow-[0_0_100px_rgba(108,92,231,0.3)]">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden opacity-20 pointer-events-none">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-white blur-[100px] rounded-full" />
        </div>
        <h2 className="font-outfit text-3xl md:text-5xl font-extrabold mb-8 relative z-10">
          Ready to scale your supply chain?
        </h2>
        <p className="text-white/80 text-lg mb-12 max-w-2xl mx-auto relative z-10">
          Join hundreds of brands using Michi to automate their forecasting and inventory management.
        </p>
        <button className="bg-white text-michi-purple hover:bg-white/90 px-10 py-5 rounded-2xl font-bold text-lg transition-all relative z-10">
          Start Your Free Trial
        </button>
      </section>

      <footer className="max-w-7xl mx-auto mt-32 pt-12 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-8 text-michi-gray text-sm">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-michi-purple rounded flex items-center justify-center font-bold text-white text-[10px]">道</div>
          <span className="font-outfit font-bold text-white tracking-tight">Michi</span>
        </div>
        <div>© 2026 Michi AI Solutions. All rights reserved.</div>
        <div className="flex gap-8">
          <a href="#" className="hover:text-white transition-colors">Privacy</a>
          <a href="#" className="hover:text-white transition-colors">Terms</a>
          <a href="#" className="hover:text-white transition-colors">Status</a>
        </div>
      </footer>
    </main>
  );
}
