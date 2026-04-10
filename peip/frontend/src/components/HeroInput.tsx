import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

interface HeroInputProps {
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

export default function HeroInput({ onSubmit, isLoading }: HeroInputProps) {
  const [url, setUrl] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onSubmit(url.trim());
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto mt-16 mb-12 text-center text-white">
      <h1 className="text-5xl font-extrabold mb-4 tracking-tight">
        Predictive <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-indigo to-brand-pink">Engineering</span> Intelligence
      </h1>
      <p className="text-gray-400 mb-8 max-w-xl mx-auto text-lg leading-relaxed">
        Analyze repositories in real-time. Detect churn, calculate risk, and generate actionable insights for both developers and executives.
      </p>

      <form onSubmit={handleSubmit} className="relative group w-full max-w-2xl mx-auto">
        <div className="absolute -inset-1 bg-gradient-to-r from-brand-indigo to-brand-pink rounded-full blur opacity-25 group-hover:opacity-60 transition duration-1000 group-hover:duration-200"></div>
        <div className="relative flex items-center bg-[#0F111A] border border-white/10 rounded-full px-6 py-4 shadow-2xl">
          <Search className="w-6 h-6 text-gray-400 mr-4" />
          <input
            type="url"
            disabled={isLoading}
            placeholder="https://github.com/owner/repository"
            className="flex-1 bg-transparent border-none outline-none text-white text-lg placeholder-gray-500 disabled:opacity-50"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
          <button
            type="submit"
            disabled={isLoading || !url}
            className="ml-4 bg-white text-black font-semibold px-6 py-2 rounded-full hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyzing
              </>
            ) : (
              'Analyze Run'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
