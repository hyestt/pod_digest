import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

interface Podcast {
  id: number;
  name: string;
  description: string | null;
  rss_url: string;
  cover_image_url: string | null;
  is_active: boolean;
}

interface NewPodcast {
  name: string;
  description: string;
  rss_url: string;
  cover_image_url: string;
}

const AdminPanel: React.FC = () => {
  const [podcasts, setPodcasts] = useState<Podcast[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [newPodcast, setNewPodcast] = useState<NewPodcast>({
    name: '',
    description: '',
    rss_url: '',
    cover_image_url: ''
  });

  useEffect(() => {
    loadPodcasts();
  }, []);

  const loadPodcasts = async () => {
    try {
      const data = await api.getAllPodcasts();
      setPodcasts(data);
    } catch (error) {
      console.error('Failed to load podcasts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createPodcast(newPodcast);
      setNewPodcast({ name: '', description: '', rss_url: '', cover_image_url: '' });
      setShowForm(false);
      loadPodcasts();
      alert('Podcast added successfully!');
    } catch (error) {
      console.error('Failed to add podcast:', error);
      alert('Failed to add podcast. Please check the RSS URL.');
    }
  };

  const togglePodcastStatus = async (id: number, currentStatus: boolean) => {
    try {
      await api.updatePodcast(id, { is_active: !currentStatus });
      loadPodcasts();
    } catch (error) {
      console.error('Failed to update podcast:', error);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Podcast Admin Panel</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          {showForm ? 'Cancel' : 'Add New Podcast'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Add New Podcast</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name *</label>
              <input
                type="text"
                required
                value={newPodcast.name}
                onChange={(e) => setNewPodcast({ ...newPodcast, name: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="e.g., The Tim Ferriss Show"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">RSS Feed URL *</label>
              <input
                type="url"
                required
                value={newPodcast.rss_url}
                onChange={(e) => setNewPodcast({ ...newPodcast, rss_url: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="https://example.com/feed.xml"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                value={newPodcast.description}
                onChange={(e) => setNewPodcast({ ...newPodcast, description: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                rows={3}
                placeholder="Brief description of the podcast"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Cover Image URL</label>
              <input
                type="url"
                value={newPodcast.cover_image_url}
                onChange={(e) => setNewPodcast({ ...newPodcast, cover_image_url: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="https://example.com/cover.jpg"
              />
            </div>
            
            <div className="flex space-x-4">
              <button
                type="submit"
                className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700"
              >
                Add Podcast
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="bg-gray-500 text-white px-6 py-2 rounded hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Current Podcasts ({podcasts.length})</h2>
        </div>
        
        <div className="divide-y divide-gray-200">
          {podcasts.map((podcast) => (
            <div key={podcast.id} className="p-6 flex items-center justify-between">
              <div className="flex items-center space-x-4">
                {podcast.cover_image_url && (
                  <img
                    src={podcast.cover_image_url}
                    alt={podcast.name}
                    className="w-16 h-16 rounded-lg object-cover"
                  />
                )}
                <div>
                  <h3 className="font-semibold text-lg">{podcast.name}</h3>
                  <p className="text-gray-600 text-sm">{podcast.description}</p>
                  <p className="text-gray-500 text-xs mt-1">{podcast.rss_url}</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  podcast.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {podcast.is_active ? 'Active' : 'Inactive'}
                </span>
                
                <button
                  onClick={() => togglePodcastStatus(podcast.id, podcast.is_active)}
                  className={`px-4 py-2 rounded text-sm font-medium ${
                    podcast.is_active
                      ? 'bg-red-100 text-red-700 hover:bg-red-200'
                      : 'bg-green-100 text-green-700 hover:bg-green-200'
                  }`}
                >
                  {podcast.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;