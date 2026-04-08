/**
 * Data Bridge Test Script
 * Run this to verify frontend-backend connection
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5001';

export async function testDataBridge() {
  const results = {
    baseUrl: API_BASE_URL,
    tests: [] as Array<{endpoint: string, status: 'ok' | 'fail', error?: string, data?: any}>
  };

  const endpoints = [
    '/health',
    '/api/v1/market/heatmap',
    '/api/v1/events/',
    '/api/v1/signals/',
    '/api/v1/market/indices',
    '/api/v1/investors/funds',
    '/api/v1/economy/calendar',
    '/api/v1/market/earnings-calendar',
  ];

  for (const endpoint of endpoints) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`);
      const data = await response.json();
      
      results.tests.push({
        endpoint,
        status: response.ok && data.success !== false ? 'ok' : 'fail',
        data: data.success !== false ? 'connected' : data.error
      });
    } catch (err) {
      results.tests.push({
        endpoint,
        status: 'fail',
        error: err instanceof Error ? err.message : 'Unknown error'
      });
    }
  }

  console.log('=== Data Bridge Test Results ===');
  console.log(`Base URL: ${results.baseUrl}`);
  results.tests.forEach(test => {
    const icon = test.status === 'ok' ? '✓' : '✗';
    console.log(`${icon} ${test.endpoint}: ${test.status}`);
    if (test.error) console.log(`  Error: ${test.error}`);
  });
  
  return results;
}

// Auto-run in browser console
if (typeof window !== 'undefined') {
  (window as any).testDataBridge = testDataBridge;
}
