import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Chess, Move } from 'chess.js';
import { getGame, addAnnotation, submitGame } from '../services/games';
import ChessBoard from '../components/ChessBoard';
import MoveNavigator from '../components/MoveNavigator';
import AnnotationPanel from '../components/AnnotationPanel';
import GameSubmission from '../components/GameSubmission';

const GameEntry: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [gameData, setGameData] = useState<any>(null);
  const [chess, setChess] = useState(new Chess());
  const [annotation, setAnnotation] = useState('');
  const [annotations, setAnnotations] = useState<Record<number, string>>({});
  const [isListening, setIsListening] = useState(false);
  const [moveHistory, setMoveHistory] = useState<Move[]>([]);
  const [currentMoveIndex, setCurrentMoveIndex] = useState(-1);
  const [isDone, setIsDone] = useState(false);

  useEffect(() => {
    if (id) {
      getGame(parseInt(id)).then(data => {
        setGameData(data);
        if (data.pgn) {
          const newChess = new Chess();
          newChess.loadPgn(data.pgn);
          setChess(newChess);
          const history = newChess.history({ verbose: true });
          setMoveHistory(history);
          setCurrentMoveIndex(history.length - 1);
          
          // Load annotations
          const annoMap: Record<number, string> = {};
          data.annotations?.forEach((a: any) => {
            annoMap[a.move_number] = a.content;
          });
          setAnnotations(annoMap);
          setAnnotation(annoMap[history.length] || '');
        }
      });
    }
  }, [id]);

  const navigateToMove = (index: number) => {
    if (index < -1 || index >= moveHistory.length) return;
    const tempChess = new Chess();
    for (let j = 0; j <= index; j++) tempChess.move(moveHistory[j]);
    setChess(tempChess);
    setCurrentMoveIndex(index);
    setAnnotation(annotations[index + 1] || '');
  };

  const onDrop = (sourceSquare: string, targetSquare: string) => {
    if (gameData?.state !== 'EDITABLE') return false;

    try {
      // Use a clone to test the move
      const chessCopy = new Chess();
      chessCopy.loadPgn(chess.pgn());
      
      const move = chessCopy.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q',
      });

      if (move) {
        setChess(chessCopy);
        const history = chessCopy.history({ verbose: true });
        setMoveHistory(history);
        setCurrentMoveIndex(history.length - 1);
        return true;
      }
    } catch (e) {
      return false;
    }
    return false;
  };

  const handleAddAnnotation = async () => {
    if (id && currentMoveIndex >= 0) {
      await addAnnotation(parseInt(id), currentMoveIndex + 1, annotation);
      setAnnotations(prev => ({ ...prev, [currentMoveIndex + 1]: annotation }));
      alert("Annotation saved");
    }
  };

  const handleSubmit = async () => {
    if (id && window.confirm("Are you sure? This will lock annotations and start AI coaching. This action is irreversible.")) {
      console.log(`[GameEntry] Submitting game ${id} to AI...`);
      try {
        const response = await submitGame(parseInt(id), chess.pgn());
        console.log('[GameEntry] Submission success:', response);
        window.location.hash = `/game/${id}/waiting`;
      } catch (err: any) {
        console.error('[GameEntry] Submission failed:', err);
        alert(`Failed to submit game: ${err.message || 'Unknown error'}`);
      }
    }
  };

  const startVoiceInput = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice recognition not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setAnnotation(prev => prev + (prev ? ' ' : '') + transcript);
    };
    recognition.start();
  };

  if (!gameData) return <div className="p-4">Loading game...</div>;

  return (
    <div className="max-w-6xl mx-auto p-4 flex flex-col gap-4">
      {/* Game Metadata Header */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-wrap gap-6 items-center shadow-sm">
        <div className="flex flex-col">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Opponent</span>
          <span className="text-sm font-bold text-slate-700">{gameData.opponent_name || 'Anonymous'}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Event</span>
          <span className="text-sm font-bold text-slate-700">{gameData.event || 'Casual Game'}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Date</span>
          <span className="text-sm font-bold text-slate-700">{gameData.date ? new Date(gameData.date).toLocaleDateString() : 'N/A'}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Your Color</span>
          <span className={`text-xs font-black px-2 py-0.5 rounded border ${gameData.player_color === 'WHITE' ? 'bg-white text-slate-800 border-slate-300' : 'bg-slate-800 text-white border-slate-800'}`}>
            {gameData.player_color}
          </span>
        </div>
        {gameData.time_control && (
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Time Control</span>
            <span className="text-sm font-bold text-slate-700">{gameData.time_control}</span>
          </div>
        )}
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        <div className="flex-1">
          <ChessBoard
            position={chess.fen()}
            onPieceDrop={onDrop}
            boardOrientation={gameData.player_color === 'BLACK' ? 'black' : 'white'}
          />
          <MoveNavigator
            moveHistory={moveHistory}
            currentMoveIndex={currentMoveIndex}
            onNavigate={navigateToMove}
          />
        </div>
        
        <div className="w-full lg:w-96 flex flex-col gap-6">
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col h-[300px]">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4">Move Tree</h2>
            <div className="grid grid-cols-2 gap-2 overflow-y-auto pr-2 custom-scrollbar">
              {moveHistory.map((move, i) => (
                <div 
                  key={i} 
                  className={`p-2.5 rounded-lg text-sm cursor-pointer border transition-all ${currentMoveIndex === i ? 'bg-slate-800 text-white border-slate-800 shadow-md' : 'bg-slate-50 border-slate-100 hover:border-slate-300'}`}
                  onClick={() => navigateToMove(i)}
                >
                  <span className="opacity-50 mr-1">{Math.floor(i / 2) + 1}{i % 2 === 0 ? '.' : '...'}</span>
                  <span className="font-bold">{move.san}</span>
                  {annotations[i + 1] && <span className="ml-2 text-blue-400">●</span>}
                </div>
              ))}
              {moveHistory.length === 0 && <div className="col-span-2 py-8 text-center text-slate-400 italic text-xs">No moves entered yet.</div>}
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex-1 flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">Self-Review</h2>
              {gameData.state === 'EDITABLE' && (
                <button 
                  onClick={startVoiceInput}
                  className={`p-2 rounded-full transition-colors ${isListening ? 'bg-red-100 text-red-600 animate-pulse' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                  title="Voice Input"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                  </svg>
                </button>
              )}
            </div>

            <textarea 
              className="w-full flex-1 p-4 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-slate-800 focus:border-transparent outline-none resize-none mb-4 bg-slate-50 shadow-inner transition-all"
              placeholder={gameData.state === 'EDITABLE' ? (currentMoveIndex >= 0 ? `What were you thinking at move ${Math.floor(currentMoveIndex / 2) + 1}${currentMoveIndex % 2 === 0 ? '.' : '...'}` : "Select a move to annotate.") : "Annotations are locked."}
              disabled={gameData.state !== 'EDITABLE' || currentMoveIndex < 0}
              value={annotation}
              onChange={e => setAnnotation(e.target.value)}
            />

            {gameData.state === 'EDITABLE' && (
              <div className="space-y-3">
                <div className="flex gap-2">
                  <button 
                    onClick={handleAddAnnotation}
                    disabled={!annotation || currentMoveIndex < 0}
                    className="flex-1 py-3 bg-slate-100 text-slate-800 rounded-xl text-sm font-bold hover:bg-slate-200 disabled:opacity-50 transition-all border border-slate-200"
                  >
                    Save Move Note
                  </button>
                  <button 
                    onClick={startVoiceInput}
                    disabled={currentMoveIndex < 0}
                    className={`px-4 rounded-xl transition-all border ${isListening ? 'bg-red-50 border-red-200 text-red-600 animate-pulse' : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'}`}
                    title="Voice Input"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
                
                {!isDone ? (
                  <button 
                    onClick={() => {
                      if (moveHistory.length === 0) {
                        alert("Please enter some moves first.");
                        return;
                      }
                      setIsDone(true);
                    }}
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
                      onClick={handleSubmit}
                      className="w-full py-4 bg-slate-800 text-white rounded-xl text-sm font-black uppercase tracking-widest hover:bg-slate-900 shadow-xl shadow-slate-200 transition-all hover:-translate-y-0.5 active:translate-y-0"
                    >
                      🚀 Submit for AI Coaching
                    </button>
                    <button 
                      onClick={() => setIsDone(false)}
                      className="w-full py-1 text-xs text-slate-400 hover:text-slate-600 font-bold uppercase tracking-tight transition-colors"
                    >
                      ← Continue annotating
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameEntry;
