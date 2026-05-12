import { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Michi AI Supply Chain',
    short_name: 'Michi',
    description: 'AI-powered omnichannel forecasting solutions.',
    start_url: '/',
    display: 'standalone',
    background_color: '#0f172a',
    theme_color: '#6c5ce7',
    icons: [
      {
        src: '/favicon.ico',
        sizes: 'any',
        type: 'image/x-icon',
      },
    ],
  };
}
