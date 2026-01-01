import React from 'react';

interface AnnotationPanelProps {
  annotation: string;
  onAnnotationChange: (value: string) => void;
  onSaveAnnotation: () => void;
  startVoiceInput: () => void;
  isListening: boolean;
  canEdit: boolean;
  currentMoveText: string;
}

const AnnotationPanel: React.FC<AnnotationPanelProps> = ({
  annotation,
  onAnnotationChange,
  onSaveAnnotation,
  startVoiceInput,
  isListening,
  canEdit,
  currentMoveText
}) => {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex-1 flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">Self-Review</h2>
        {canEdit && (
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
        placeholder={canEdit ? currentMoveText : "Annotations are locked."}
        disabled={!canEdit}
        value={annotation}
        onChange={e => onAnnotationChange(e.target.value)}
      />

      {canEdit && (
        <div className="space-y-3">
          <div className="flex gap-2">
            <button
              onClick={onSaveAnnotation}
              disabled={!annotation}
              className="flex-1 py-3 bg-slate-100 text-slate-800 rounded-xl text-sm font-bold hover:bg-slate-200 disabled:opacity-50 transition-all border border-slate-200"
            >
              Save Move Note
            </button>
            <button
              onClick={startVoiceInput}
              className={`px-4 rounded-xl transition-all border ${isListening ? 'bg-red-50 border-red-200 text-red-600 animate-pulse' : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'}`}
              title="Voice Input"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnnotationPanel;