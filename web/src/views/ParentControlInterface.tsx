import React, { useState, useEffect } from 'react';
import { getPciUsage, getPciSettings, updatePciSettings, getAvailableModels } from '../services/games';

const ParentControlInterface: React.FC = () => {
  const [usage, setUsage] = useState<any[]>([]);
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [selectedModelId, setSelectedModelId] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [usageData, settingsData, modelsData] = await Promise.all([
        getPciUsage(),
        getPciSettings(),
        getAvailableModels()
      ]);
      setUsage(usageData.usage || []);
      setSettings(settingsData || {});
      setAvailableModels(modelsData || []);
      if (modelsData?.length > 0) {
        setSelectedModelId(modelsData[0].id);
      }
    } catch (err) {
      console.error("Failed to fetch PCI data", err);
    }
    setLoading(false);
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      await updatePciSettings(settings);
      alert("Settings saved successfully");
    } catch (err) {
      alert("Failed to save settings");
    }
    setSaving(false);
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
          <select 
            className="w-full p-3 border border-slate-200 rounded-lg text-sm bg-slate-50 outline-none focus:ring-2 focus:ring-slate-800 transition-all"
            value={selectedModelId}
            onChange={e => setSelectedModelId(e.target.value)}
          >
            {availableModels.map(m => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </div>

        {currentModel && (
          <div className="space-y-6">
            {currentModel.fields.map((f: any) => (
              <div key={f.key}>
                <label className="block text-xs font-bold text-slate-500 mb-2 uppercase tracking-widest">{f.label}</label>
                {f.type === 'textarea' ? (
                  <textarea 
                    className="w-full p-3 border border-slate-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-slate-800 outline-none transition-all bg-slate-50 h-32"
                    placeholder={`Enter ${f.label.toLowerCase()}...`}
                    value={settings[f.key] || ''}
                    onChange={e => setSettings({...settings, [f.key]: e.target.value})}
                  />
                ) : (
                  <input 
                    type={f.key.includes('KEY') || f.key.includes('JSON') || f.key.includes('CREDENTIALS') ? 'password' : 'text'}
                    className="w-full p-3 border border-slate-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-slate-800 outline-none transition-all bg-slate-50"
                    placeholder={`Enter ${f.label.toLowerCase()}...`}
                    value={settings[f.key] || ''}
                    onChange={e => setSettings({...settings, [f.key]: e.target.value})}
                  />
                )}
              </div>
            ))}
            
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
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">AI Coaching History</h2>
          <button onClick={fetchData} className="text-xs text-slate-400 hover:text-slate-600 font-medium transition-colors">Refresh</button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500 font-medium">
              <tr>
                <th className="px-6 py-4 border-b border-slate-100">Game ID</th>
                <th className="px-6 py-4 border-b border-slate-100">Tier</th>
                <th className="px-6 py-4 border-b border-slate-100">Timestamp</th>
                <th className="px-6 py-4 border-b border-slate-100">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {usage.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-slate-400 italic bg-white">No AI coaching sessions recorded yet.</td>
                </tr>
              ) : (
                usage.map((u, i) => (
                  <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs text-slate-600">#{u.game_id}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${u.tier === 'ADVANCED' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-100 text-slate-600'}`}>
                        {u.tier}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-500">{new Date(u.created_at).toLocaleString()}</td>
                    <td className="px-6 py-4">
                      <span className="flex items-center gap-1.5 text-green-600 font-bold text-[10px]">
                        <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                        COMPLETED
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};

export default ParentControlInterface;
