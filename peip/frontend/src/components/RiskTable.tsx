import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle2 } from 'lucide-react';

interface ModuleScore {
  file_path: string;
  risk_classification: string;
  health_score: number;
  churn_count: number;
  complexity_score: number;
}

interface RiskTableProps {
  modules: ModuleScore[];
}

export default function RiskTable({ modules }: RiskTableProps) {
  if (!modules || modules.length === 0) return null;

  return (
    <div className="glass-card shadow-2xl rounded-2xl overflow-hidden mt-8 w-full border border-white/5">
      <div className="bg-white/5 backdrop-blur-xl px-6 py-4 border-b border-white/10 flex items-center justify-between">
        <h3 className="text-xl font-bold text-white tracking-wide">High-Risk Modules</h3>
        <span className="text-xs text-gray-400 bg-black/50 px-3 py-1 rounded-full border border-white/10">{modules.length} Detected</span>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-black/20 text-gray-400 text-sm tracking-wider uppercase">
              <th className="px-6 py-4 font-medium border-b border-white/5">File Path</th>
              <th className="px-6 py-4 font-medium border-b border-white/5">Risk Level</th>
              <th className="px-6 py-4 font-medium border-b border-white/5 text-right">Health Score</th>
              <th className="px-6 py-4 font-medium border-b border-white/5 text-right">Churn Count</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-gray-300">
            {modules.map((mod, idx) => {
              const isHigh = mod.risk_classification === 'High';
              const isMed = mod.risk_classification === 'Medium';
              
              return (
                <tr key={idx} className="hover:bg-white/5 transition-colors duration-200">
                  <td className="px-6 py-4 font-mono text-sm max-w-sm truncate text-gray-200" title={mod.file_path}>
                    {mod.file_path}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold
                      ${isHigh ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 
                        isMed ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' : 
                                'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'}`
                    }>
                      {isHigh && <AlertTriangle className="w-3 h-3 mr-1.5" />}
                      {isMed && <AlertCircle className="w-3 h-3 mr-1.5" />}
                      {!isHigh && !isMed && <CheckCircle2 className="w-3 h-3 mr-1.5" />}
                      {mod.risk_classification}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right font-medium">
                    <span className={mod.health_score < 50 ? 'text-red-400' : 'text-gray-300'}>{mod.health_score}</span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-gray-400">{mod.churn_count}</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
