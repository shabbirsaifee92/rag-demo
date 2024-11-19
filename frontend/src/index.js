import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App'; // Ensure this matches the `App.js` file in your `src` folder

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
