"use client";

import React, { useState } from 'react';
import { Terminal, Briefcase } from 'lucide-react';

interface DualReportViewProps {
  devReport: string;
  ceoReport: string;
}

export default function DualReportView({ devReport, ceoReport }: DualReportViewProps) {
  const [activeTab, setActiveTab] = useState<'dev' | 'ceo'>('dev');

  return (
    <div className="glass-card shadow-xl rounded-2xl overflow-hidden mt-8 w-full border border-white/5 flex flex-col h-[500px]">
      <div className="flex bg-black/30 border-b border-white/10">
        <button
          onClick={() => setActiveTab('dev')}
          className={`flex-1 py-4 px-6 text-sm font-semibold tracking-wide flex items-center justify-center transition-all duration-300 ${
            activeTab === 'dev' 
              ? 'text-white border-b-2 border-brand-indigo bg-white/5' 
              : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
          }`}
        >
          <Terminal className="w-4 h-4 mr-2" />
          Developer Action Plan
        </button>
        <button
          onClick={() => setActiveTab('ceo')}
          className={`flex-1 py-4 px-6 text-sm font-semibold tracking-wide flex items-center justify-center transition-all duration-300 ${
            activeTab === 'ceo' 
              ? 'text-white border-b-2 border-brand-pink bg-white/5' 
              : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
          }`}
        >
          <Briefcase className="w-4 h-4 mr-2" />
          Executive Summary
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
        <div className="prose prose-invert max-w-none">
          {/* We do a simple split and map for markdown newlines as simplistic rendering */}
          {(activeTab === 'dev' ? devReport : ceoReport).split('\n').map((line, idx) => {
            if (line.startsWith('##')) {
              return <h3 key={idx} className="text-xl font-bold text-white mt-4 mb-2">{line.replace('##', '')}</h3>;
            } else if (line.startsWith('#')) {
              return <h2 key={idx} className="text-2xl font-extrabold text-white mt-6 mb-3 bg-clip-text text-transparent bg-gradient-to-r from-brand-indigo to-brand-pink">{line.replace('#', '')}</h2>;
            } else if (line.startsWith('- ')) {
              return <li key={idx} className="text-gray-300 ml-4 mb-1">{line.replace('- ', '')}</li>;
            } else if (line.trim() === '') {
              return <br key={idx} />;
            }
            return <p key={idx} className="text-gray-300 leading-relaxed mb-2">{line}</p>;
          })}
        </div>
      </div>
    </div>
  );
}
