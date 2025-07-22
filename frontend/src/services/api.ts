import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export interface Podcast {
  id: number;
  name: string;
  description: string | null;
  cover_image_url: string | null;
}

export interface PodcastCreate {
  name: string;
  description: string;
  rss_url: string;
  cover_image_url: string;
}

export interface PodcastUpdate {
  name?: string;
  description?: string;
  rss_url?: string;
  cover_image_url?: string;
  is_active?: boolean;
}

export interface PodcastFull extends Podcast {
  rss_url: string;
  is_active: boolean;
}

export interface SubscribeRequest {
  email: string;
  name?: string;
  utm_source?: string;
  utm_medium?: string;
}

export interface SubscribeResponse {
  success: boolean;
  message: string;
  subscriber_id?: string;
}

export const api = {
  getPodcasts: async (): Promise<Podcast[]> => {
    const response = await axios.get(`${API_BASE_URL}/podcasts`);
    return response.data;
  },

  // Admin functions
  getAllPodcasts: async (): Promise<PodcastFull[]> => {
    const response = await axios.get(`${API_BASE_URL}/admin/podcasts`);
    return response.data;
  },

  createPodcast: async (podcast: PodcastCreate): Promise<PodcastFull> => {
    const response = await axios.post(`${API_BASE_URL}/admin/podcasts`, podcast);
    return response.data;
  },

  updatePodcast: async (id: number, updates: PodcastUpdate): Promise<PodcastFull> => {
    const response = await axios.put(`${API_BASE_URL}/admin/podcasts/${id}`, updates);
    return response.data;
  },

  deletePodcast: async (id: number): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/admin/podcasts/${id}`);
  },

  // Newsletter functions
  subscribeToNewsletter: async (subscribeData: SubscribeRequest): Promise<SubscribeResponse> => {
    const response = await axios.post(`${API_BASE_URL}/newsletter/subscribe`, subscribeData);
    return response.data;
  }
};