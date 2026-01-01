import React from 'react';
import { Move } from 'chess.js';

interface MoveTreeProps {
  moveHistory: Move[];
  annotations: Record<number, string>;
  currentMoveIndex: number;
  onMoveClick: (index: number) => void;
}

const MoveTree: React.FC<MoveTreeProps> = ({
  moveHistory,
  annotations,
  currentMoveIndex,
  onMoveClick
}) => {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col h-[300px]">
      <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4">Move Tree</h2>
      <div className="grid grid-cols-2 gap-2 overflow-y-auto pr-2 custom-scrollbar">
        {moveHistory.map((move, i) => (
          <div
            key={i}
            className={`p-2.5 rounded-lg text-sm cursor-pointer border transition-all ${currentMoveIndex === i ? 'bg-slate-800 text-white border-slate-800 shadow-md' : 'bg-slate-50 border-slate-100 hover:border-slate-300'}`}
            onClick={() => onMoveClick(i)}
          >
            <span className="opacity-50 mr-1">{Math.floor(i / 2) + 1}{i % 2 === 0 ? '.' : '...'}</span>
            <span className="font-bold">{move.san}</span>
            {annotations[i + 1] && <span className="ml-2 text-blue-400">●</span>}
          </div>
        ))}
        {moveHistory.length === 0 && <div className="col-span-2 py-8 text-center text-slate-400 italic text-xs">No moves entered yet.</div>}
      </div>
    </div>
  );
};

export default MoveTree;