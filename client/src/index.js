import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { ClerkProvider } from '@clerk/react'

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <ClerkProvider>
        <App />
    </ClerkProvider>
);
