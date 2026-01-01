import React, { useState, useEffect } from 'react';
import { getGames, deleteGame } from '../services/games';

interface Game {
  id: number;
  opponent_name: string;
  state: 'EDITABLE' | 'SUBMITTED' | 'COACHING' | 'COMPLETED';
  created_at: string;
}

const GameList: React.FC = () => {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchGames = () => {
    setLoading(true);
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
  };

  useEffect(() => {
    fetchGames();
  }, []);

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this game?')) return;
    try {
      await deleteGame(id);
      fetchGames();
    } catch (err) {
      alert('Failed to delete game');
    }
  };

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
            <div className="flex-1">
              <div className="font-medium">vs {game.opponent_name}</div>
              <div className="text-sm text-slate-500">{new Date(game.created_at).toLocaleDateString()}</div>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`px-2 py-1 rounded text-xs font-medium ${
                game.state === 'EDITABLE' ? 'bg-blue-100 text-blue-800' :
                game.state === 'SUBMITTED' ? 'bg-amber-100 text-amber-800' :
                game.state === 'COACHING' ? 'bg-purple-100 text-purple-800' :
                'bg-green-100 text-green-800'
              }`}>
                {game.state}
              </div>
              <button 
                onClick={(e) => handleDelete(e, game.id)}
                className="text-slate-400 hover:text-red-600 transition-colors"
                title="Delete Game"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GameList;
