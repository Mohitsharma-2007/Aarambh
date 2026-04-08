import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';

interface SiteEmbedProps {
  url: string;
}

export const SiteEmbed: React.FC<SiteEmbedProps> = ({ url }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSite = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.get(`http://localhost:8000/api/proxy/site`, {
          params: { url }
        });
        
        if (containerRef.current) {
          // Use Shadow DOM to isolate styles and prevent leakage
          let shadow = containerRef.current.shadowRoot;
          if (!shadow) {
            shadow = containerRef.current.attachShadow({ mode: 'open' });
          }
          
          // Inject the HTML
          shadow.innerHTML = response.data;
          
          // Re-trigger script executions if needed (though Yahoo JS will likely break)
          // We mainly care about the UI/Layout
        }
      } catch (err) {
        setError('Failed to embed site. Using fallback data view.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (url) fetchSite();
  }, [url]);

  return (
    <div className="w-full min-h-[800px] relative bg-white rounded-xl border border-[#dadce0] overflow-hidden">
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-50 z-10">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-[#5f6368] font-medium">Injecting dynamic site mirror...</p>
        </div>
      )}
      {error && (
        <div className="p-8 text-center">
          <p className="text-red-500 font-medium">{error}</p>
        </div>
      )}
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
};
