import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getReflection } from '../services/games';

const FinalReflection: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [reflection, setReflection] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      console.log(`[FinalReflection] Fetching reflection for game ${id}`);
      getReflection(parseInt(id)).then(data => {
        console.log('[FinalReflection] Received data:', data);
        if (data && (data.thinking_patterns || data.reflection)) {
           // Handle both old and new formats if necessary
           setReflection(data.reflection || data);
        } else {
           console.warn('[FinalReflection] Data received but invalid format:', data);
           setReflection(null);
        }
        setLoading(false);
      }).catch(err => {
        console.error('[FinalReflection] API call failed:', err);
        setLoading(false);
      });
    }
  }, [id]);

  if (loading) return <div className="p-12 text-center text-slate-500 animate-pulse">Finalizing your reflection...</div>;
  if (!reflection) return (
    <div className="max-w-md mx-auto p-12 text-center">
      <h1 className="text-lg font-medium text-slate-800">Reflection Not Available</h1>
      <p className="text-sm text-slate-500 mt-2 mb-6">We couldn't find the AI analysis for this game. It might still be processing or encountered an error.</p>
      <button 
        onClick={() => window.location.hash = '/'}
        className="px-8 py-2 border border-slate-300 rounded text-slate-600 hover:bg-slate-50 transition-colors"
      >
        Back to Game List
      </button>
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-8">
      <h1 className="text-2xl font-semibold border-b pb-4">Game Reflection</h1>
      
      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-4">
          How You Were Thinking
        </h2>
        <div className="prose text-slate-800">
          {reflection.thinking_patterns.map((p: string, i: number) => (
            <p key={i} className="mb-2">{p}</p>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-4">
          What Was Missing
        </h2>
        <div className="prose text-slate-800">
          {reflection.missing_elements.map((m: string, i: number) => (
            <p key={i} className="mb-2">{m}</p>
          ))}
        </div>
      </section>

      <section className="bg-slate-50 p-6 rounded-lg border border-slate-100">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-4">
          Suggested Habits
        </h2>
        <div className="prose text-slate-900 font-medium">
          {reflection.habits.map((h: string, i: number) => (
            <p key={i} className="mb-2">• {h}</p>
          ))}
        </div>
      </section>

      <div className="pt-8 text-center">
        <button 
          onClick={() => window.location.hash = '/'}
          className="px-8 py-2 border border-slate-300 rounded text-slate-600 hover:bg-slate-50 transition-colors"
        >
          Back to Game List
        </button>
      </div>
    </div>
  );
};

export default FinalReflection;
