// API service module - re-exports from unified API
import { unifiedAPI } from '../api/unified';

export { unifiedAPI as default, unifiedAPI };

// Create named exports for compatibility
export const financeAPI = unifiedAPI;
export const newsAPI = unifiedAPI;
export const useAPI = unifiedAPI;
