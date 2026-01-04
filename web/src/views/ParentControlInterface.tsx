import React, { useState, useEffect } from 'react';
import { getPciUsage, getPciSettings, updatePciSettings, getAvailableModels, getPciGames, bulkDeleteGames } from '../services/games';

const ParentControlInterface: React.FC = () => {
  const [usage, setUsage] = useState<any[]>([]);
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [maskedSettings, setMaskedSettings] = useState<Record<string, string>>({});
  const [fullSettings, setFullSettings] = useState<Record<string, string>>({});
  const [configured, setConfigured] = useState<Record<string, boolean>>({});
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [selectedModelId, setSelectedModelId] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [visibleFields, setVisibleFields] = useState<Record<string, boolean>>({});
  const [games, setGames] = useState<any[]>([]);
  const [selectedGames, setSelectedGames] = useState<Set<number>>(new Set());
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Ensure we have a token before making requests
      // The ApiService should handle this, but we'll add a small delay to ensure token is ready
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const [usageData, settingsData, modelsData, gamesData] = await Promise.all([
        getPciUsage().catch(err => {
          console.error("Failed to fetch usage:", err);
          return { usage: [] };
        }),
        getPciSettings().catch(err => {
          console.error("Failed to fetch settings:", err);
          return { settings: {}, configured: {} };
        }),
        getAvailableModels().catch(err => {
          console.error("Failed to fetch available models:", err);
          return [];
        }),
        getPciGames().catch(err => {
          console.error("Failed to fetch games:", err);
          return { games: [] };
        })
      ]);
      setUsage(usageData.usage || []);
      setSettings(settingsData?.settings || {});
      setMaskedSettings(settingsData?.masked_settings || {});
      setFullSettings(settingsData?.full_settings || {});
      setConfigured(settingsData?.configured || {});
      setAvailableModels(modelsData || []);
      setGames(gamesData.games || []);
      
      // Debug logging
      console.log('[PCI] Settings data:', {
        settings: settingsData?.settings,
        masked_settings: settingsData?.masked_settings,
        full_settings: settingsData?.full_settings,
        configured: settingsData?.configured
      });
      if (modelsData?.length > 0) {
        setSelectedModelId(modelsData[0].id);
      } else {
        console.warn("No available models returned from API");
      }
    } catch (err) {
      console.error("Failed to fetch PCI data", err);
    }
    setLoading(false);
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      // Never send secret placeholders; only send secret fields if the parent typed something.
      const nextSettings: Record<string, string> = {};
      for (const [k, v] of Object.entries(settings)) {
        const trimmed = (v ?? "").trim();
        if (!trimmed) continue;
        nextSettings[k] = trimmed;
      }

      await updatePciSettings(nextSettings);
      alert("Settings saved successfully");
      // Refresh to update "configured" flags
      await fetchData();
    } catch (err) {
      alert("Failed to save settings");
    }
    setSaving(false);
  };

  const handleToggleGameSelection = (gameId: number) => {
    const newSelected = new Set(selectedGames);
    if (newSelected.has(gameId)) {
      newSelected.delete(gameId);
    } else {
      newSelected.add(gameId);
    }
    setSelectedGames(newSelected);
  };

  const handleSelectAllGames = () => {
    if (selectedGames.size === games.length) {
      setSelectedGames(new Set());
    } else {
      setSelectedGames(new Set(games.map(g => g.id)));
    }
  };

  const handleDeleteSelectedGames = async () => {
    if (selectedGames.size === 0) {
      alert("Please select at least one game to delete");
      return;
    }

    const confirmMessage = `Are you sure you want to delete ${selectedGames.size} game(s)? This action cannot be undone.`;
    if (!window.confirm(confirmMessage)) {
      return;
    }

    setDeleting(true);
    try {
      const gameIds = Array.from(selectedGames);
      const result = await bulkDeleteGames(gameIds);
      alert(`Successfully deleted ${result.deleted_count} game(s)`);
      setSelectedGames(new Set());
      await fetchData();
    } catch (err: any) {
      console.error("Failed to delete games:", err);
      alert(`Failed to delete games: ${err.message || 'Unknown error'}`);
    }
    setDeleting(false);
  };


  if (loading) return <div className="p-8 text-center text-slate-500 font-medium">Loading Parent Control Interface...</div>;

  const currentModel = availableModels.find(m => m.id === selectedModelId);

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8 pb-20">
      <header className="border-b border-slate-200 pb-6">
        <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Parent Control Interface</h1>
        <p className="text-slate-500 text-sm mt-1">Configure AI authentication and monitor coaching usage.</p>
      </header>

      <section className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">AI Configuration</h2>
          <span className="text-[10px] bg-amber-50 text-amber-700 px-2 py-0.5 rounded font-bold">SECURE STORAGE</span>
        </div>
        
        <div className="mb-8">
          <label className="block text-xs font-bold text-slate-500 mb-2 uppercase tracking-widest">Select AI Provider</label>
          {availableModels.length === 0 ? (
            <div className="w-full p-3 border border-slate-200 rounded-lg text-sm bg-slate-50 text-slate-400">
              {loading ? "Loading providers..." : "No providers available. Check console for errors."}
            </div>
          ) : (
            <select 
              className="w-full p-3 border border-slate-200 rounded-lg text-sm bg-slate-50 outline-none focus:ring-2 focus:ring-slate-800 transition-all"
              value={selectedModelId}
              onChange={e => setSelectedModelId(e.target.value)}
            >
              {availableModels.map(m => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          )}
        </div>

        {currentModel && (
          <div className="space-y-6">
            {currentModel.fields.map((f: any) => {
              const isSensitive = f.key.includes('KEY') || f.key.includes('CREDENTIALS');
              // Check if value exists (not null/undefined) in either masked or full settings
              const hasMaskedValue = maskedSettings[f.key] != null && maskedSettings[f.key] !== '';
              const hasFullValue = fullSettings[f.key] != null && fullSettings[f.key] !== '';
              const isConfigured = configured[f.key] === true;
              // Show button if field is sensitive AND (configured OR has any values)
              // Always show for sensitive fields if configured, even if values are empty
              const hasStoredValue = isConfigured || hasMaskedValue || hasFullValue;
              const isVisible = visibleFields[f.key] || false;
              
              // Force show button for sensitive fields that are configured
              const shouldShowButton = isSensitive && (hasStoredValue || isConfigured);
              
              // Debug logging for sensitive fields
              if (isSensitive) {
                console.log(`[PCI] Field ${f.key}:`, {
                  isSensitive,
                  isConfigured,
                  configured: configured[f.key],
                  hasMaskedValue,
                  hasFullValue,
                  hasStoredValue,
                  maskedValue: maskedSettings[f.key] ? `${maskedSettings[f.key].substring(0, 50)}...` : null,
                  fullValue: fullSettings[f.key] ? `${fullSettings[f.key].substring(0, 50)}...` : null,
                  willShowButton: isSensitive && hasStoredValue
                });
              }
              
              return (
                <div key={f.key}>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest">{f.label}</label>
                    {shouldShowButton && (
                      <button
                        type="button"
                        onClick={() => setVisibleFields({...visibleFields, [f.key]: !isVisible})}
                        className="text-xs text-slate-600 hover:text-slate-800 font-semibold transition-colors flex items-center gap-1.5 px-2 py-1 rounded hover:bg-slate-100"
                        title={isVisible ? "Hide value" : "Show value"}
                      >
                        {isVisible ? (
                          <>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                            </svg>
                            Hide
                          </>
                        ) : (
                          <>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            Show
                          </>
                        )}
                      </button>
                    )}
                  </div>
                  {f.type === 'textarea' ? (
                    <textarea 
                      className="w-full p-3 border border-slate-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-slate-800 outline-none transition-all bg-slate-50 h-48"
                      placeholder={
                        hasStoredValue && !settings[f.key]
                          ? `${f.label} is configured. Click "Show" to view or enter a new value to replace it...`
                          : `Enter ${f.label.toLowerCase()}...`
                      }
                      value={
                        settings[f.key] || 
                        (hasStoredValue ? (isVisible ? (fullSettings[f.key] || '') : (maskedSettings[f.key] || '')) : '')
                      }
                      onChange={e => setSettings({...settings, [f.key]: e.target.value})}
                      onFocus={e => {
                        // Clear stored value display when user starts editing
                        if (hasStoredValue && !settings[f.key]) {
                          setSettings({...settings, [f.key]: ''});
                          e.target.select();
                        }
                      }}
                      readOnly={hasStoredValue && !settings[f.key] && !isVisible}
                    />
                  ) : (
                    <input 
                      type={isSensitive && !isVisible && !settings[f.key] ? 'password' : 'text'}
                      className="w-full p-3 border border-slate-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-slate-800 outline-none transition-all bg-slate-50"
                      placeholder={
                        hasStoredValue && !settings[f.key]
                          ? `${f.label} is configured. Click "Show" to view or enter a new value to replace it...`
                          : `Enter ${f.label.toLowerCase()}...`
                      }
                      value={
                        settings[f.key] || 
                        (hasStoredValue ? (isVisible ? (fullSettings[f.key] || '') : (maskedSettings[f.key] || '')) : '')
                      }
                      onChange={e => setSettings({...settings, [f.key]: e.target.value})}
                      onFocus={e => {
                        // Clear stored value display when user starts editing
                        if (hasStoredValue && !settings[f.key]) {
                          setSettings({...settings, [f.key]: ''});
                          e.target.select();
                        }
                      }}
                    />
                  )}
                </div>
              );
            })}
            
            <button 
              onClick={handleSaveSettings}
              disabled={saving}
              className="w-full md:w-auto px-8 py-3 bg-slate-800 text-white rounded-lg text-sm font-bold hover:bg-slate-900 disabled:opacity-50 transition-all shadow-lg shadow-slate-200"
            >
              {saving ? 'Saving Credentials...' : `Save ${currentModel.name} Settings`}
            </button>
          </div>
        )}
      </section>

      <section className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">AI Coaching History & Game Management</h2>
          <div className="flex items-center gap-4">
            <button
              onClick={handleDeleteSelectedGames}
              disabled={selectedGames.size === 0 || deleting}
              className="px-4 py-2 bg-red-600 text-white rounded-lg text-xs font-bold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {deleting ? 'Deleting...' : selectedGames.size > 0 ? `Delete Selected (${selectedGames.size})` : 'Delete Selected'}
            </button>
            <button onClick={fetchData} className="text-xs text-slate-400 hover:text-slate-600 font-medium transition-colors">Refresh</button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500 font-medium">
              <tr>
                <th className="px-6 py-4 border-b border-slate-100">
                  <input
                    type="checkbox"
                    checked={games.length > 0 && selectedGames.size === games.length}
                    onChange={handleSelectAllGames}
                    className="w-4 h-4 text-slate-800 border-slate-300 rounded focus:ring-slate-800"
                  />
                </th>
                <th className="px-6 py-4 border-b border-slate-100">Game ID</th>
                <th className="px-6 py-4 border-b border-slate-100">Opponent</th>
                <th className="px-6 py-4 border-b border-slate-100">State</th>
                <th className="px-6 py-4 border-b border-slate-100">AI Tier</th>
                <th className="px-6 py-4 border-b border-slate-100">Created</th>
                <th className="px-6 py-4 border-b border-slate-100">Event</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {games.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400 italic bg-white">No games found.</td>
                </tr>
              ) : (
                games.map((game) => {
                  // Find AI coaching history for this game
                  const coachingHistory = usage.find((u: any) => u.game_id === game.id);
                  
                  return (
                    <tr key={game.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4">
                        <input
                          type="checkbox"
                          checked={selectedGames.has(game.id)}
                          onChange={() => handleToggleGameSelection(game.id)}
                          className="w-4 h-4 text-slate-800 border-slate-300 rounded focus:ring-slate-800"
                        />
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-600">#{game.id}</td>
                      <td className="px-6 py-4 text-slate-700">{game.opponent_name || 'Unknown'}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          game.state === 'COMPLETED' ? 'bg-green-50 text-green-700' :
                          game.state === 'COACHING' ? 'bg-purple-50 text-purple-700' :
                          game.state === 'SUBMITTED' ? 'bg-amber-50 text-amber-700' :
                          'bg-blue-50 text-blue-700'
                        }`}>
                          {game.state}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {coachingHistory ? (
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            coachingHistory.tier === 'ADVANCED' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-100 text-slate-600'
                          }`}>
                            {coachingHistory.tier}
                          </span>
                        ) : (
                          <span className="text-slate-400 text-xs italic">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-slate-500 text-xs">
                        {game.created_at ? new Date(game.created_at).toLocaleString() : 'N/A'}
                      </td>
                      <td className="px-6 py-4 text-slate-500 text-xs">{game.event || '-'}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};

export default ParentControlInterface;
