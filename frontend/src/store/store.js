/**
 * store.js — Redux store configuration
 *
 * configureStore from Redux Toolkit:
 * - Combines all reducers (we only have complaints for now, but you can add more)
 * - Automatically adds Redux DevTools Extension support
 * - Includes redux-thunk middleware for async operations
 */
import { configureStore } from '@reduxjs/toolkit';
import complaintsReducer from './complaintsSlice';

export const store = configureStore({
  reducer: {
    complaints: complaintsReducer,
    // Add more reducers here as the app grows:
    // users: usersReducer,
    // settings: settingsReducer,
  },
  // devTools: process.env.NODE_ENV !== 'production' (auto-handled by RTK)
});

export default store;