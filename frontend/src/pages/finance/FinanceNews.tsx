import { useState, useEffect } from "react";
import unifiedAPI from "../../services/api";

const FinanceNews = () => {
  const [news, setNews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const data = await unifiedAPI.getFinanceNews();
        setNews(data.articles || []);
      } catch (error) {
        console.error("Failed to fetch finance news:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, []);

  if (loading) {
    return <div className="p-4">Loading finance news...</div>;
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Finance News</h1>
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

export default FinanceNews;
