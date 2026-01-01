import React from 'react';

interface GameSubmissionProps {
  canSubmit: boolean;
  isDone: boolean;
  onToggleDone: () => void;
  onSubmit: () => void;
  onContinue: () => void;
}

const GameSubmission: React.FC<GameSubmissionProps> = ({
  canSubmit,
  isDone,
  onToggleDone,
  onSubmit,
  onContinue
}) => {
  if (!canSubmit) return null;

  return (
    <div className="space-y-3">
      {!isDone ? (
        <button
          onClick={onToggleDone}
          className="w-full py-3.5 bg-slate-200 text-slate-800 rounded-xl text-sm font-black uppercase tracking-widest hover:bg-slate-300 transition-all border-b-4 border-slate-400 active:border-b-0 active:translate-y-1"
        >
          I'm Done Annotating
        </button>
      ) : (
        <div className="space-y-3 animate-in fade-in zoom-in duration-300">
          <div className="p-3 bg-blue-50 border border-blue-100 rounded-lg text-[10px] text-blue-700 font-medium leading-relaxed">
            Ready to submit? This will lock all move notes and initiate AI coaching. This action is irreversible.
          </div>
          <button
            onClick={onSubmit}
            className="w-full py-4 bg-slate-800 text-white rounded-xl text-sm font-black uppercase tracking-widest hover:bg-slate-900 shadow-xl shadow-slate-200 transition-all hover:-translate-y-0.5 active:translate-y-0"
          >
            🚀 Submit for AI Coaching
          </button>
          <button
            onClick={onContinue}
            className="w-full py-1 text-xs text-slate-400 hover:text-slate-600 font-bold uppercase tracking-tight transition-colors"
          >
            ← Continue annotating
          </button>
        </div>
      )}
    </div>
  );
};

export default GameSubmission;