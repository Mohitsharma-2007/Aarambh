import { useState, useEffect } from "react";
import unifiedAPI from "../../services/api";

const Crypto = () => {
  const [cryptoData, setCryptoData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCrypto = async () => {
      try {
        const data = await unifiedAPI.getGoogleMarket("crypto");
        setCryptoData(data);
      } catch (error) {
        console.error("Failed to fetch crypto data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchCrypto();
  }, []);

  if (loading) {
    return <div className="p-4">Loading crypto data...</div>;
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Cryptocurrency Prices</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cryptoData?.map((crypto, index) => (
          <div key={index} className="border rounded p-4">
            <h3 className="font-semibold">{crypto.symbol}</h3>
            <p className="text-lg">${crypto.price?.toFixed(2)}</p>
            <p className={`text-sm ${crypto.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {crypto.change >= 0 ? '+' : ''}{crypto.change?.toFixed(2)}%
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Crypto;
