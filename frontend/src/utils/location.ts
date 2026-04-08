/**
 * Geofencing and Location Utilities
 * Detects user location and provides location-based news
 */

import React from 'react';

export interface LocationInfo {
  country: string;
  countryCode: string;
  city?: string;
  region?: string;
  latitude?: number;
  longitude?: number;
  source: 'gps' | 'ip' | 'manual' | 'cached';
}

class LocationService {
  private cacheKey = 'user_location';
  private cacheExpiry = 24 * 60 * 60 * 1000; // 24 hours

  /**
   * Get user location with multiple fallback methods
   */
  async getLocation(): Promise<LocationInfo> {
    // Check cache first
    const cachedLocation = this.getCachedLocation();
    if (cachedLocation) {
      return cachedLocation;
    }

    // Try GPS first (most accurate)
    try {
      const gpsLocation = await this.getGPSLocation();
      if (gpsLocation) {
        this.cacheLocation(gpsLocation);
        return gpsLocation;
      }
    } catch (error) {
      console.log('GPS location failed:', error);
    }

    // Fallback to IP geolocation
    try {
      const ipLocation = await this.getIPLocation();
      if (ipLocation) {
        this.cacheLocation(ipLocation);
        return ipLocation;
      }
    } catch (error) {
      console.log('IP location failed:', error);
    }

    // Final fallback to browser locale
    const localeLocation = this.getLocaleLocation();
    this.cacheLocation(localeLocation);
    return localeLocation;
  }

  /**
   * Get GPS location using browser geolocation API
   */
  private async getGPSLocation(): Promise<LocationInfo | null> {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            const { latitude, longitude } = position.coords;
            
            // Reverse geocoding to get country info
            const countryInfo = await this.reverseGeocode(latitude, longitude);
            
            resolve({
              ...countryInfo,
              latitude,
              longitude,
              source: 'gps'
            });
          } catch (error) {
            reject(error);
          }
        },
        (error) => reject(error),
        {
          timeout: 10000,
          enableHighAccuracy: true,
          maximumAge: 300000 // 5 minutes
        }
      );
    });
  }

  /**
   * Get location from IP address using geolocation API
   */
  private async getIPLocation(): Promise<LocationInfo | null> {
    try {
      // Using free ip-api.com service
      const response = await fetch('http://ip-api.com/json/?fields=status,country,countryCode,city,region,lat,lon');
      const data = await response.json();

      if (data.status === 'success') {
        return {
          country: data.country,
          countryCode: data.countryCode,
          city: data.city,
          region: data.region,
          latitude: data.lat,
          longitude: data.lon,
          source: 'ip'
        };
      }
    } catch (error) {
      console.error('IP geolocation failed:', error);
    }

    return null;
  }

  /**
   * Get location from browser locale (last resort)
   */
  private getLocaleLocation(): LocationInfo {
    const locale = navigator.language || 'en-US';
    const countryCode = locale.split('-')[1] || 'US';
    
    const countryMap: { [key: string]: { country: string; countryCode: string } } = {
      'US': { country: 'United States', countryCode: 'US' },
      'GB': { country: 'United Kingdom', countryCode: 'GB' },
      'IN': { country: 'India', countryCode: 'IN' },
      'CA': { country: 'Canada', countryCode: 'CA' },
      'AU': { country: 'Australia', countryCode: 'AU' },
      'DE': { country: 'Germany', countryCode: 'DE' },
      'FR': { country: 'France', countryCode: 'FR' },
      'JP': { country: 'Japan', countryCode: 'JP' },
      'CN': { country: 'China', countryCode: 'CN' },
      'BR': { country: 'Brazil', countryCode: 'BR' },
      'RU': { country: 'Russia', countryCode: 'RU' },
      'ZA': { country: 'South Africa', countryCode: 'ZA' }
    };

    const location = countryMap[countryCode] || countryMap['US'];
    
    return {
      ...location,
      source: 'manual'
    };
  }

  /**
   * Reverse geocoding to get country from coordinates
   */
  private async reverseGeocode(lat: number, lon: number): Promise<LocationInfo> {
    try {
      // Using Nominatim (OpenStreetMap) reverse geocoding
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10`
      );
      const data = await response.json();

      if (data && data.address) {
        const address = data.address;
        return {
          country: address.country || 'Unknown',
          countryCode: address.country_code?.toUpperCase() || 'US',
          city: address.city || address.town || address.village,
          region: address.state || address.region,
          source: 'gps'
        };
      }
    } catch (error) {
      console.error('Reverse geocoding failed:', error);
    }

    // Fallback to locale
    return this.getLocaleLocation();
  }

  /**
   * Cache location data
   */
  private cacheLocation(location: LocationInfo): void {
    try {
      const cacheData = {
        location,
        timestamp: Date.now()
      };
      localStorage.setItem(this.cacheKey, JSON.stringify(cacheData));
    } catch (error) {
      console.error('Failed to cache location:', error);
    }
  }

  /**
   * Get cached location if valid
   */
  private getCachedLocation(): LocationInfo | null {
    try {
      const cached = localStorage.getItem(this.cacheKey);
      if (!cached) return null;

      const cacheData = JSON.parse(cached);
      const age = Date.now() - cacheData.timestamp;

      if (age < this.cacheExpiry) {
        return cacheData.location;
      } else {
        localStorage.removeItem(this.cacheKey);
      }
    } catch (error) {
      console.error('Failed to read cached location:', error);
    }

    return null;
  }

  /**
   * Clear location cache
   */
  clearCache(): void {
    localStorage.removeItem(this.cacheKey);
  }

  /**
   * Get country code for news API
   */
  async getCountryCode(): Promise<string> {
    const location = await this.getLocation();
    return location.countryCode || 'US';
  }

  /**
   * Check if user is in specific country
   */
  async isInCountry(countryCode: string): Promise<boolean> {
    const location = await this.getLocation();
    return location.countryCode === countryCode.toUpperCase();
  }

  /**
   * Get timezone offset for location
   */
  async getTimezone(): Promise<string> {
    try {
      const location = await this.getLocation();
      if (location.latitude && location.longitude) {
        // You could use a timezone API here
        // For now, return browser timezone
        return Intl.DateTimeFormat().resolvedOptions().timeZone;
      }
    } catch (error) {
      console.error('Failed to get timezone:', error);
    }

    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  }
}

// Export singleton instance
export const locationService = new LocationService();

// Hook for React components
export function useLocation() {
  const [location, setLocation] = React.useState<LocationInfo | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const fetchLocation = async () => {
      try {
        setLoading(true);
        const loc = await locationService.getLocation();
        setLocation(loc);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Location detection failed');
      } finally {
        setLoading(false);
      }
    };

    fetchLocation();
  }, []);

  return { location, loading, error };
}
