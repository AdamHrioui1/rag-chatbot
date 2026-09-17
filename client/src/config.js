// Base URL of the Node/Express server. Defaults to localhost for local
// development; set REACT_APP_SERVER_API_URL in production (e.g. when
// deployed to Netlify) so the app calls the real deployed backend
// instead of the visitor's own machine.
export const SERVER_API_URL = process.env.REACT_APP_SERVER_API_URL || 'http://localhost:5000';
