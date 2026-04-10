"use client";

import React, { useState } from 'react';
import HeroInput from '@/components/HeroInput';
import OverallScoreGauge from '@/components/OverallScoreGauge';
import RiskTable from '@/components/RiskTable';
import DualReportView from '@/components/DualReportView';
import { GitPullRequest, Star, Users } from 'lucide-react';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (url: string) => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      // Connects to local FastAPI backend
      const res = await fetch('http://127.0.0.1:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: url })
      });
      const result = await res.json();
      
      if (!res.ok || result.status === 'Error') {
        throw new Error(result.message || 'Failed to analyze repository');
      }
      
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen py-12 px-6 flex flex-col pt-24 relative z-10 w-full max-w-7xl mx-auto">
      <HeroInput onSubmit={handleAnalyze} isLoading={loading} />

      {error && (
        <div className="w-full max-w-2xl mx-auto bg-red-500/10 border border-red-500/30 text-red-400 px-6 py-4 rounded-xl text-center backdrop-blur-sm animate-fade-in-up">
          <p className="font-semibold tracking-wide">Error: {error}</p>
        </div>
      )}

      {data && data.repo && (
        <div className="w-full grid grid-cols-1 lg:grid-cols-3 gap-8 mt-12 animate-fade-in-up">
          
          <div className="lg:col-span-1 space-y-8 flex flex-col">
            <OverallScoreGauge score={data.repo.overall_health_score || 0} />
            
            <div className="glass-card p-6 flex flex-col space-y-4">
               <h3 className="text-xl font-bold text-gray-300">Repository Metadata</h3>
               <div className="flex items-center text-gray-400 gap-3">
                 <GitPullRequest className="text-brand-indigo w-5 h-5"/> 
                 <span>Language: <strong className="text-white">{data.repo.language || 'Unknown'}</strong></span>
               </div>
               <div className="flex items-center text-gray-400 gap-3">
                 <Star className="text-yellow-400 w-5 h-5"/> 
                 <span>Stars: <strong className="text-white">{data.repo.star_count || 0}</strong></span>
               </div>
               <div className="flex items-center text-gray-400 gap-3">
                 <Users className="text-brand-emerald w-5 h-5"/> 
                 <span>Contributors: <strong className="text-white">{data.repo.contributor_count || 0}</strong></span>
               </div>
            </div>
          </div>
          
          <div className="lg:col-span-2 flex flex-col space-y-8">
            <RiskTable modules={data.modules} />
            
            {data.reports && data.reports.length === 2 && (
              <DualReportView 
                devReport={data.reports.find((r:any) => r.report_type === 'developer')?.content || ''}
                ceoReport={data.reports.find((r:any) => r.report_type === 'ceo')?.content || ''}
              />
            )}
          </div>
        </div>
      )}
    </main>
  );
}
