import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { getReflection, getGame } from '../services/games';

const FinalReflection: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const hasRedirected = useRef(false);
  const [reflection, setReflection] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      const fetchReflection = async () => {
        try {
          // First, check game state to avoid unnecessary API calls
          console.log(`[FinalReflection] Checking game state for game ${id}, current path: ${location.pathname}`);
          const game = await getGame(parseInt(id));
          console.log(`[FinalReflection] Game state: ${game.state}`);
          
          // Check if we're actually on the reflection page (HashRouter uses hash, not pathname)
          const currentHash = window.location.hash;
          const isOnReflectionPage = currentHash.includes('/reflection');
          
          // If game is in COACHING state and we're on reflection page, redirect to coaching
          if (game.state === 'COACHING' && !hasRedirected.current && isOnReflectionPage) {
            console.log('[FinalReflection] Game in COACHING state, redirecting to coaching');
            hasRedirected.current = true;
            setLoading(false);
            navigate(`/game/${id}/coaching`);
            return;
          }
          
          // Only try to fetch reflection if game is COMPLETED
          // If not COMPLETED and we're on reflection page, redirect to coaching
          if (game.state !== 'COMPLETED' && !hasRedirected.current && isOnReflectionPage) {
            console.log(`[FinalReflection] Game state is ${game.state}, not COMPLETED. Redirecting to coaching.`);
            hasRedirected.current = true;
            setLoading(false);
            navigate(`/game/${id}/coaching`);
            return;
          }
          
          // If game is not COMPLETED, don't proceed (might be redirecting or on wrong page)
          if (game.state !== 'COMPLETED') {
            console.log(`[FinalReflection] Game state is ${game.state}, not COMPLETED. Not on reflection page or already redirected.`);
            setLoading(false);
            return;
          }
          
          console.log(`[FinalReflection] Fetching reflection for game ${id}`);
          // Try to fetch reflection - backend will handle state checking and generation
          const data = await getReflection(parseInt(id));
          console.log('[FinalReflection] Received data:', data);
          
          if (data && (data.thinking_patterns || data.reflection)) {
             // Handle both old and new formats if necessary
             setReflection(data.reflection || data);
          } else {
             console.warn('[FinalReflection] Data received but invalid format:', data);
             setReflection(null);
          }
          setLoading(false);
        } catch (err: any) {
          console.error('[FinalReflection] API call failed:', err);
          // Check if we're still on reflection page before redirecting
          const currentHash = window.location.hash;
          const isOnReflectionPage = currentHash.includes('/reflection');
          
          // If we get a 400 error, it likely means questions aren't answered or analysis isn't done
          if (err?.status === 400 || err?.response?.status === 400) {
            console.log('[FinalReflection] 400 error - questions not all answered or analysis in progress');
            if (!hasRedirected.current && isOnReflectionPage) {
              hasRedirected.current = true;
              setLoading(false);
              navigate(`/game/${id}/coaching`);
            }
            return;
          }
          // For other errors, try to check game state
          try {
            const game = await getGame(parseInt(id));
            console.log(`[FinalReflection] Game state after error: ${game.state}`);
            if ((game.state === 'COACHING' || game.state !== 'COMPLETED') && !hasRedirected.current && isOnReflectionPage) {
              console.log('[FinalReflection] Game in COACHING state, redirecting to coaching');
              hasRedirected.current = true;
              setLoading(false);
              navigate(`/game/${id}/coaching`);
              return;
            }
          } catch (gameErr) {
            console.error('[FinalReflection] Failed to fetch game state:', gameErr);
          }
          setError('Failed to load reflection. Please try again.');
          setLoading(false);
        }
      };
      
      fetchReflection();
    }
  }, [id, navigate, location.pathname]);

  if (loading) return (
    <div className="p-12 text-center">
      <div className="text-slate-500 animate-pulse mb-4">Finalizing your reflection...</div>
      <button 
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          navigate(`/game/${id}/coaching`);
        }}
        className="mt-4 px-4 py-2 text-sm border border-slate-300 rounded text-slate-600 hover:bg-slate-50 transition-colors"
      >
        Go to Questions
      </button>
    </div>
  );
  if (error || !reflection) return (
    <div className="max-w-md mx-auto p-12 text-center">
      <h1 className="text-lg font-medium text-slate-800">Reflection Not Available</h1>
      <p className="text-sm text-slate-500 mt-2 mb-6">
        {error || "We couldn't find the AI analysis for this game. It might still be processing or encountered an error."}
      </p>
      <div className="flex gap-4 justify-center">
        <button 
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            navigate(`/game/${id}/coaching`);
          }}
          className="px-8 py-2 bg-slate-800 text-white rounded hover:bg-slate-900 transition-colors"
        >
          Continue Questions
        </button>
        <button 
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            navigate('/');
          }}
          className="px-8 py-2 border border-slate-300 rounded text-slate-600 hover:bg-slate-50 transition-colors"
        >
          Back to Game List
        </button>
      </div>
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-8">
      <div className="mb-6">
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            navigate('/');
          }}
          className="flex items-center gap-2 text-slate-600 hover:text-slate-800 transition-colors mb-4"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Main Menu
        </button>
      </div>
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

      <div className="pt-8 border-t border-slate-200">
        <div className="flex gap-4 justify-center">
          <button 
            onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            navigate('/');
          }}
            className="px-8 py-3 bg-slate-800 text-white rounded-lg hover:bg-slate-900 transition-colors font-semibold"
          >
            Back to Main Menu
          </button>
          {id && (
            <button 
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                navigate(`/game/${id}`, { state: { fromReflection: true } });
              }}
              className="px-8 py-3 border border-slate-300 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors font-semibold"
            >
              View Game
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default FinalReflection;
