import React, { useState } from 'react';
import { createGame, GameMetadata } from '../services/games';

const CreateGame: React.FC = () => {
  const [metadata, setMetadata] = useState<GameMetadata>({
    player_color: 'WHITE',
    opponent_name: '',
    event: '',
    date: new Date().toISOString().split('T')[0],
    time_control: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const game = await createGame(metadata);
      window.location.hash = `/game/${game.id}`;
    } catch (err) {
      alert('Failed to create game');
    }
  };

  return (
    <div className="max-w-md mx-auto p-4">
      <h1 className="text-xl font-semibold mb-6">Create New Game</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Your Color</label>
          <select 
            className="w-full p-2 border border-slate-200 rounded"
            value={metadata.player_color}
            onChange={e => setMetadata({...metadata, player_color: e.target.value as any})}
          >
            <option value="WHITE">White</option>
            <option value="BLACK">Black</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Opponent Name</label>
          <input 
            type="text" 
            className="w-full p-2 border border-slate-200 rounded"
            required
            value={metadata.opponent_name}
            onChange={e => setMetadata({...metadata, opponent_name: e.target.value})}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Event</label>
          <input 
            type="text" 
            className="w-full p-2 border border-slate-200 rounded"
            value={metadata.event}
            onChange={e => setMetadata({...metadata, event: e.target.value})}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Date</label>
          <input 
            type="date" 
            className="w-full p-2 border border-slate-200 rounded"
            required
            value={metadata.date}
            onChange={e => setMetadata({...metadata, date: e.target.value})}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Time Control</label>
          <input 
            type="text" 
            placeholder="e.g. 15+10"
            className="w-full p-2 border border-slate-200 rounded"
            value={metadata.time_control}
            onChange={e => setMetadata({...metadata, time_control: e.target.value})}
          />
        </div>
        <button 
          type="submit"
          className="w-full py-2 bg-slate-800 text-white rounded font-medium"
        >
          Create Game
        </button>
      </form>
    </div>
  );
};

export default CreateGame;
