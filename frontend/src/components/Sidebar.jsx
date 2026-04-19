import React, { useState } from 'react';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const navItems = [
    { id: 'home', label: 'Home', icon: '🏠' },
    { id: 'ask', label: 'Ask AI', icon: '🤖' },
    { id: 'about', label: 'About', icon: 'ℹ️' },
  ];

  return (
    <div style={{
      width: isCollapsed ? '60px' : '250px',
      height: '100vh',
      background: '#f8f9fa',
      borderRight: '1px solid #dee2e6',
      transition: 'width 0.3s ease',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      position: 'relative'
    }}>
      
      {/* Header / Title */}
      <div style={{ 
        padding: '20px', 
        borderBottom: '1px solid #dee2e6',
        display: 'flex',
        flexDirection: 'column',
        alignItems: isCollapsed ? 'center' : 'flex-start',
        overflow: 'hidden',
        whiteSpace: 'nowrap'
      }}>
        <h1 style={{ 
          fontSize: '1.2rem', 
          margin: 0, 
          color: '#333', 
          fontWeight: 'bold',
          display: isCollapsed ? 'none' : 'block' 
        }}>
          GEMR: KG
        </h1>
        {isCollapsed && (
             <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>KG</span>
        )}
        
        {!isCollapsed && (
          <p style={{ 
            fontSize: '0.8rem', 
            color: '#666', 
            margin: '5px 0 0 0',
            whiteSpace: 'normal',
            lineHeight: '1.2'
          }}>
            Query the Global Emerging Market Risk : Knowledge graph
          </p>
        )}
      </div>

      {/* Navigation Items */}
      <nav style={{ flexGrow: 1, paddingTop: '20px' }}>
        {navItems.map(item => (
          <div
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            style={{
              padding: '15px 20px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              background: activeTab === item.id ? '#e9ecef' : 'transparent',
              borderLeft: activeTab === item.id ? '4px solid #007bff' : '4px solid transparent',
              color: activeTab === item.id ? '#007bff' : '#333',
              fontWeight: activeTab === item.id ? 'bold' : 'normal',
              transition: 'background 0.2s'
            }}
            title={isCollapsed ? item.label : ''}
          >
            <span style={{ fontSize: '1.2rem', marginRight: isCollapsed ? 0 : '10px' }}>{item.icon}</span>
            {!isCollapsed && <span>{item.label}</span>}
          </div>
        ))}
      </nav>

      {/* Toggle Button */}
      <button
        onClick={toggleSidebar}
        style={{
          position: 'absolute',
          bottom: '20px',
          right: isCollapsed ? '50%' : '20px',
          transform: isCollapsed ? 'translateX(50%)' : 'none',
          background: 'none',
          border: '1px solid #ccc',
          borderRadius: '4px',
          cursor: 'pointer',
          padding: '5px 10px',
          color: '#666'
        }}
        title={isCollapsed ? "Expand" : "Collapse"}
      >
        {isCollapsed ? '→' : '←'}
      </button>

    </div>
  );
};

export default Sidebar;
