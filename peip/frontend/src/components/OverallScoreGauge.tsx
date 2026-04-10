"use client";

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface OverallScoreGaugeProps {
  score: number;
}

export default function OverallScoreGauge({ score }: OverallScoreGaugeProps) {
  // We represent it as a half-donut (180 degrees)
  const data = [
    { name: 'Score', value: score },
    { name: 'Remaining', value: 100 - score },
  ];

  let color = '#10b981'; // emerald by default
  if (score < 50) color = '#ef4444'; // red
  else if (score < 80) color = '#eab308'; // yellow

  return (
    <div className="glass-card p-6 flex flex-col items-center justify-center relative w-full h-64 overflow-hidden group">
      <h3 className="text-xl font-semibold mb-2 text-gray-300">Repository Health</h3>
      
      <div className="w-full h-full -mb-16">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius={70}
              outerRadius={90}
              paddingAngle={0}
              dataKey="value"
              stroke="none"
              cornerRadius={5}
            >
              <Cell key="cell-0" fill={color} className="drop-shadow-lg" />
              <Cell key="cell-1" fill="rgba(255,255,255,0.05)" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
      
      <div className="absolute bottom-8 flex flex-col items-center">
        <span className="text-4xl font-extrabold text-white animate-pulse-slow">{score}</span>
        <span className="text-xs text-gray-400 mt-1 uppercase tracking-widest">/ 100</span>
      </div>
    </div>
  );
}
