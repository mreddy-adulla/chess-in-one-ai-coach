import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Chessboard } from 'react-chessboard';
const ChessboardAny = Chessboard as any;
import { getNextQuestion, answerQuestion } from '../services/games';

const GuidedQuestioning: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [question, setQuestion] = useState<any>(null);
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchQuestion = async () => {
    if (id) {
      setLoading(true);
      try {
        const q = await getNextQuestion(parseInt(id));
        console.log('[GuidedQuestioning] Next question:', q);
        if (!q || q.message === "All questions completed") {
           console.log('[GuidedQuestioning] All questions answered, moving to reflection');
           window.location.hash = `/game/${id}/reflection`;
           return;
        }
        setQuestion(q);
      } catch (err) {
        console.error('[GuidedQuestioning] Error fetching question:', err);
        // Do not auto-redirect on error, stay on page to see error
        // window.location.hash = `/game/${id}/reflection`;
      }
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestion();
  }, [id]);

  const handleSubmit = async (skipped: boolean = false) => {
    if (question) {
      await answerQuestion(question.id, answer, skipped);
      setAnswer('');
      fetchQuestion();
    }
  };

  if (loading) return <div className="p-12 text-center text-slate-500 animate-pulse">Loading next question...</div>;
  if (!question) return null;

  return (
    <div className="max-w-5xl mx-auto p-4 flex flex-col lg:flex-row gap-8">
      <div className="flex-1">
        <div className="aspect-square max-w-[500px] mx-auto shadow-2xl rounded-xl overflow-hidden border-4 border-white">
          <ChessboardAny 
            position={question.fen || 'start'} 
            arePiecesDraggable={false}
          />
        </div>
        <div className="mt-6 p-4 bg-slate-100 rounded-lg border border-slate-200">
          <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-2">Your Original Thinking</h2>
          <p className="text-slate-700 italic">"{question.original_annotation || "I didn't record any specific thoughts for this move."}"</p>
        </div>
      </div>
      
      <div className="w-full lg:w-[400px] flex flex-col">
        <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-xl flex-1 flex flex-col relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-2 bg-slate-800"></div>
          
          <div className="mb-8">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-2">Question</span>
            <h1 className="text-xl font-semibold text-slate-800 leading-tight">
              {question.question_text}
            </h1>
          </div>

          <textarea 
            className="w-full flex-1 p-4 border border-slate-200 rounded-xl text-base focus:ring-2 focus:ring-slate-800 focus:border-transparent outline-none resize-none mb-6 bg-slate-50"
            placeholder="Reflect on this position..."
            value={answer}
            onChange={e => setAnswer(e.target.value)}
          />

          <div className="flex gap-4 mt-auto">
            <button 
              onClick={() => handleSubmit(false)}
              disabled={!answer.trim()}
              className="flex-1 py-3.5 bg-slate-800 text-white rounded-xl text-sm font-bold hover:bg-slate-900 disabled:opacity-50 transition-all shadow-lg shadow-slate-200"
            >
              Submit Reflection
            </button>
            <button 
              onClick={() => handleSubmit(true)}
              className="px-6 py-3.5 bg-slate-100 text-slate-600 rounded-xl text-sm font-bold hover:bg-slate-200 transition-colors"
            >
              Skip
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GuidedQuestioning;
