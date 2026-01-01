import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getGame } from '../services/games';

const AIProcessing: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  // Using window.location.hash for navigation as per earlier pattern, 
  // but let's stick to a consistent way if possible.
  
  useEffect(() => {
    if (!id) return;

    const poll = async () => {
      try {
        const game = await getGame(parseInt(id));
        console.log('[AIProcessing] Polling state:', game.state);
        // Explicitly check for COACHING state to move to questions
        if (game.state === 'COACHING') {
          console.log('[AIProcessing] Transitioning to Guided Questioning');
          window.location.hash = `/game/${id}/coaching`;
        } else if (game.state === 'COMPLETED') {
          console.log('[AIProcessing] Transitioning to Final Reflection');
          window.location.hash = `/game/${id}/reflection`;
        }
      } catch (err) {
        console.error("Polling error", err);
      }
    };

    const interval = setInterval(poll, 3000);
    poll(); // Initial check

    return () => clearInterval(interval);
  }, [id]);

  return (
    <div className="max-w-md mx-auto p-12 text-center">
      <div className="w-12 h-12 border-4 border-slate-200 border-t-slate-800 rounded-full animate-spin mx-auto mb-6"></div>
      <h1 className="text-lg font-medium text-slate-800">Preparing your reflection session…</h1>
      <p className="text-sm text-slate-500 mt-2">This usually takes less than a minute.</p>
    </div>
  );
};

export default AIProcessing;
