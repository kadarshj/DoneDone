import './App.css'
import Stars from './components/Stars'
import Agent from './components/Agent'
import UserInput from './components/UserInput';
import { useState } from 'react';

function App() {

  const [mode, setMode] = useState('personal');

  const handleClick = (mode) => {
    setMode(mode);
  };

  return (
    <div>
      <Stars/>
      <div className="container">
        <div className="header">
          <div>
            <div className="logo">DONEDONE</div>
            <div className="subtitle">GALACTIC TASK COMMANDER v2.0</div>
          </div>
          <button className="logout-btn" id="logoutBtn" title="Logout">🚪</button>
        </div>
        <div className="main-panel">
          <div className="mode-selector">
            <button className={`mode-btn ${mode === 'work' ? 'active' : ''}`} onClick={() => handleClick('work')}>
                🏢 WORK PROTOCOL
            </button>
            <button className={`mode-btn ${mode === 'personal' ? 'active' : ''}`} onClick={() => handleClick('personal')}>
                👤 PERSONAL DIARY
            </button>
          </div>
          <UserInput/>
          <Agent mode={mode}/>
        </div>
        <div className="main-panel">
          Action Center
        </div>
      </div>
    </div>
  )
}

export default App
