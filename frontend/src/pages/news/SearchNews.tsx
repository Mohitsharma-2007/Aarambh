import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import unifiedAPI from "../../services/api";

const SearchNews = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get("q") || "";
  const [news, setNews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!query) return;

    const searchNews = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await unifiedAPI.searchNews(query);
        setNews(data.articles || []);
      } catch (err: any) {
        setError(err.message || "Failed to search news");
        console.error("Failed to search news:", err);
      } finally {
        setLoading(false);
      }
    };

    searchNews();
  }, [query]);

  if (loading) {
    return <div className="p-4">Searching for "{query}"...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-600">Error: {error}</div>;
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Search Results for "{query}"</h1>
      <div className="space-y-4">
        {news.map((article, index) => (
          <div key={index} className="border rounded p-4">
            <h3 className="font-semibold mb-2">{article.title}</h3>
            <p className="text-sm text-gray-600 mb-2">{article.summary}</p>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">{article.source}</span>
              <a 
                href={article.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline text-sm"
              >
                Read more
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchNews;
