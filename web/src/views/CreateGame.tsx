import React, { useState, useRef } from 'react';
import { createGame, GameMetadata } from '../services/games';
import { Chess } from 'chess.js';

const CreateGame: React.FC = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [metadata, setMetadata] = useState<GameMetadata>({
    player_color: 'WHITE',
    opponent_name: '',
    event: '',
    date: new Date().toISOString().split('T')[0],
    time_control: '',
    pgn: ''
  });

  const handlePgnChange = (pgn: string) => {
    const chess = new Chess();
    try {
      chess.loadPgn(pgn);
      const header = chess.header();
      
      setMetadata(prev => {
        const white = header.White || '';
        const black = header.Black || '';
        // If we know the user is one of the names, we can guess the color
        // For now, we'll just pre-fill opponent if only one is found
        const opponent = prev.player_color === 'WHITE' ? black : white;

        return {
          ...prev,
          pgn,
          opponent_name: opponent || header.Black || header.White || prev.opponent_name,
          event: header.Event || prev.event,
          date: header.Date ? header.Date.replace(/\./g, '-') : prev.date,
        };
      });
    } catch (e) {
      // Invalid PGN, just update the field
      setMetadata(prev => ({ ...prev, pgn }));
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      handlePgnChange(content);
    };
    reader.readAsText(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      console.log('[CreateGame] Submitting metadata:', metadata);
      const game = await createGame(metadata);
      console.log('[CreateGame] Success:', game);
      window.location.hash = `/game/${game.id}`;
    } catch (err: any) {
      console.error('[CreateGame] Error details:', err);
      alert(`Failed to create game: ${err.message || 'Unknown error'}`);
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
            onChange={e => {
              const newColor = e.target.value as any;
              setMetadata(prev => ({...prev, player_color: newColor}));
              // Re-parse PGN to update opponent if PGN exists
              if (metadata.pgn) handlePgnChange(metadata.pgn);
            }}
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
        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="block text-sm font-medium">Import PGN (Optional)</label>
            <button 
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              Choose File
            </button>
            <input 
              type="file" 
              ref={fileInputRef}
              className="hidden"
              accept=".pgn"
              onChange={handleFileChange}
            />
          </div>
          <textarea 
            className="w-full p-2 border border-slate-200 rounded h-32 font-mono text-xs"
            placeholder={'[Event "?"]\n[Site "?"]\n...'}
            value={metadata.pgn}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => handlePgnChange(e.target.value)}
          ></textarea>
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
