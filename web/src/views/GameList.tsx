import React, { useState, useEffect } from 'react';
import { getGames } from '../services/games';

interface Game {
  id: number;
  opponent_name: string;
  state: 'EDITABLE' | 'SUBMITTED' | 'COACHING' | 'COMPLETED';
  created_at: string;
}

const GameList: React.FC = () => {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getGames()
      .then(data => {
        setGames(data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load games:", err);
        setGames([]);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-4">Loading games...</div>;

  return (
    <div className="max-w-2xl mx-auto p-4">
      <h1 className="text-xl font-semibold mb-6">Your Games</h1>
      <button 
        className="mb-6 px-4 py-2 bg-slate-800 text-white rounded"
        onClick={() => window.location.hash = '/create'}
      >
        Create New Game
      </button>
      <div className="space-y-4">
        {games.map(game => (
          <div 
            key={game.id} 
            className="p-4 border border-slate-200 rounded flex justify-between items-center hover:bg-slate-50 cursor-pointer"
            onClick={() => window.location.hash = `/game/${game.id}`}
          >
            <div>
              <div className="font-medium">vs {game.opponent_name}</div>
              <div className="text-sm text-slate-500">{new Date(game.created_at).toLocaleDateString()}</div>
            </div>
            <div className={`px-2 py-1 rounded text-xs font-medium ${
              game.state === 'EDITABLE' ? 'bg-blue-100 text-blue-800' :
              game.state === 'SUBMITTED' ? 'bg-amber-100 text-amber-800' :
              game.state === 'COACHING' ? 'bg-purple-100 text-purple-800' :
              'bg-green-100 text-green-800'
            }`}>
              {game.state}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GameList;
