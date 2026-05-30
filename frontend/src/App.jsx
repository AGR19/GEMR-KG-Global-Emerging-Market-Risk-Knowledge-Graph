import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Home from './components/Home';
import About from './components/About';
import AskAI from './components/AskAI';

function App() {
  const [activeTab, setActiveTab] = useState('home');

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      display: 'flex',
      overflow: 'hidden'
    }}>
      {/* Sidebar Navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <main style={{
        flexGrow: 1,
        height: '100%',
        overflow: 'auto',
        position: 'relative',
        padding: '20px',
        boxSizing: 'border-box'
      }}>
        {activeTab === 'home' && <Home />}
        {activeTab === 'ask' && <AskAI />}
        {activeTab === 'about' && <About />}
      </main>
    </div>
  );
}

export default App;
