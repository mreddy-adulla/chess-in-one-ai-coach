import React, { useEffect } from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import GameList from './views/GameList';
import CreateGame from './views/CreateGame';
import GameEntry from './views/GameEntry';
import GuidedQuestioning from './views/GuidedQuestioning';
import FinalReflection from './views/FinalReflection';
import AIProcessing from './views/AIProcessing';
import ParentControlInterface from './views/ParentControlInterface';

const App: React.FC = () => {
  const [isPci, setIsPci] = React.useState(false);

  useEffect(() => {
    const checkPci = () => {
      // Check both pathname and hash for PCI related routes
      const path = window.location.pathname;
      const hash = window.location.hash;
      
      // Strict check: if we are at /game/ we are DEFINITELY not in PCI
      if (hash.includes('/game/')) {
        setIsPci(false);
        return;
      }

      const isPciUrl = path.startsWith('/pci-ui') || 
                       path.startsWith('/pci-gui') ||
                       hash.startsWith('#/pci');
      setIsPci(isPciUrl);
    };

    checkPci();
    window.addEventListener('hashchange', checkPci);
    return () => window.removeEventListener('hashchange', checkPci);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans antialiased">
      {!isPci && (
        <nav className="p-4 bg-white border-b border-slate-200 mb-8">
          <div className="max-w-4xl mx-auto flex justify-between items-center">
            <span className="font-bold tracking-tight text-slate-800">CHESS-IN-ONE AI COACH</span>
            <div className="flex items-center gap-4">
              <a href="#/pci" className="text-xs text-slate-400 hover:text-slate-600 uppercase tracking-widest transition-colors">Parent Control</a>
              <span className="text-xs text-slate-400 uppercase tracking-widest">Disciplined Learning</span>
            </div>
          </div>
        </nav>
      )}

      <main className="max-w-4xl mx-auto pb-12">
        <HashRouter>
          <Routes>
            <Route path="/" element={isPci ? <ParentControlInterface /> : <GameList />} />
            <Route path="/create" element={<CreateGame />} />
            <Route path="/game/:id" element={<GameEntry />} />
            <Route path="/game/:id/coaching" element={<GuidedQuestioning />} />
            <Route path="/game/:id/reflection" element={<FinalReflection />} />
            <Route path="/game/:id/waiting" element={<AIProcessing />} />
            <Route path="/pci" element={<ParentControlInterface />} />
          </Routes>
        </HashRouter>
      </main>
    </div>
  );
};

export default App;
