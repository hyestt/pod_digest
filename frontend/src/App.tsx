import React, { useState } from 'react';
import Hero from './components/Hero';
import PodcastGrid from './components/PodcastGrid';
import SubscribeSection from './components/SubscribeSection';
import AdminPanel from './components/AdminPanel';
import './index.css';

function App() {
  const [showAdmin, setShowAdmin] = useState(false);

  // Check if admin mode is requested via URL hash
  React.useEffect(() => {
    if (window.location.hash === '#admin') {
      setShowAdmin(true);
    }
  }, []);

  if (showAdmin) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white shadow-sm border-b">
          <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
            <h1 className="text-xl font-semibold">Admin Panel</h1>
            <button
              onClick={() => setShowAdmin(false)}
              className="text-blue-600 hover:text-blue-800"
            >
              ← Back to Main Site
            </button>
          </div>
        </div>
        <AdminPanel />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <Hero />
      <PodcastGrid />
      <SubscribeSection />
      
      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-4xl mx-auto text-center px-4">
          <h3 className="text-xl font-semibold mb-4">Podcast Digest</h3>
          <p className="text-gray-400 mb-4">
            让优质的英文播客内容触手可及
          </p>
          <p className="text-gray-500 text-sm">
            © 2024 Podcast Digest. All rights reserved.
          </p>
          
          {/* Hidden admin link */}
          <button
            onClick={() => setShowAdmin(true)}
            className="text-gray-700 text-xs mt-4 opacity-20 hover:opacity-50"
          >
            Admin
          </button>
        </div>
      </footer>
    </div>
  );
}

export default App;