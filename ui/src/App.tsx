import React from 'react';

function App() {
  return (
    <div style={{ padding: '40px', fontFamily: 'system-ui, -apple-system, sans-serif', maxWidth: '800px', margin: '0 auto', lineHeight: '1.6' }}>
      <h1 style={{ color: '#2563eb', borderBottom: '2px solid #e5e7eb', paddingBottom: '10px' }}>Qualification Microservice</h1>
      <div style={{ backgroundColor: '#f3f4f6', padding: '20px', borderRadius: '8px', marginTop: '20px' }}>
        <h2 style={{ marginTop: 0 }}>Isolated Service UI</h2>
        <p>This UI is served directly from the <strong>qualification</strong> microservice.</p>
        <p>Currently, this is a placeholder. Developers can add service-specific tools and dashboards here.</p>
      </div>
      <div style={{ marginTop: '30px' }}>
        <h3>Quick Links</h3>
        <ul>
          <li><a href="/api/docs" style={{ color: '#2563eb' }}>API Documentation (Swagger)</a></li>
          <li><a href="/health" style={{ color: '#2563eb' }}>Health Check</a></li>
        </ul>
      </div>
    </div>
  );
}

export default App;