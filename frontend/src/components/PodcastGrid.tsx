import React, { useEffect, useState } from 'react';
import { api, Podcast } from '../services/api';

const PodcastGrid: React.FC = () => {
  const [podcasts, setPodcasts] = useState<Podcast[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPodcasts = async () => {
      try {
        const data = await api.getPodcasts();
        setPodcasts(data);
      } catch (error) {
        console.error('Failed to fetch podcasts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPodcasts();
  }, []);

  // Default podcast images if none provided
  const defaultImages = [
    'https://via.placeholder.com/300x300/4F46E5/ffffff?text=Podcast+1',
    'https://via.placeholder.com/300x300/7C3AED/ffffff?text=Podcast+2',
    'https://via.placeholder.com/300x300/EC4899/ffffff?text=Podcast+3',
    'https://via.placeholder.com/300x300/F59E0B/ffffff?text=Podcast+4',
    'https://via.placeholder.com/300x300/10B981/ffffff?text=Podcast+5',
    'https://via.placeholder.com/300x300/3B82F6/ffffff?text=Podcast+6',
  ];

  if (loading) {
    return (
      <div className="py-20 text-center">
        <p className="text-gray-500">加载中...</p>
      </div>
    );
  }

  return (
    <div className="py-16 bg-gray-50">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          精选播客
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {podcasts.length > 0 ? (
            podcasts.map((podcast, index) => (
              <div
                key={podcast.id}
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
              >
                <img
                  src={podcast.cover_image_url || defaultImages[index % defaultImages.length]}
                  alt={podcast.name}
                  className="w-full h-48 object-cover rounded-t-lg"
                />
                <div className="p-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {podcast.name}
                  </h3>
                  <p className="text-gray-600 text-sm">
                    {podcast.description || '优质英文播客，每周更新'}
                  </p>
                </div>
              </div>
            ))
          ) : (
            // Show demo podcasts if no data
            ['The Tim Ferriss Show', 'TED Talks Daily', 'How I Built This', 
             'The Daily', 'Planet Money', 'Freakonomics Radio'].map((name, index) => (
              <div
                key={index}
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
              >
                <img
                  src={defaultImages[index]}
                  alt={name}
                  className="w-full h-48 object-cover rounded-t-lg"
                />
                <div className="p-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {name}
                  </h3>
                  <p className="text-gray-600 text-sm">
                    优质英文播客，每周更新
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default PodcastGrid;