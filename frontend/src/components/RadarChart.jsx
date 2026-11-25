import React from 'react';
import {
  Radar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import { useTheme } from '../context/ThemeContext';

export const RadarChart = ({ data }) => {
  const { isDark } = useTheme();

  if (!data || data.length === 0) return null;

  const chartData = data.map((d) => ({
    subject: d.subject,
    Candidate: d.candidate_score,
    Benchmark: d.benchmark_score,
  }));

  // Dynamic theme colors for maximum contrast in both dark and bright modes
  const gridColor = isDark ? '#334155' : '#cbd5e1';
  const angleTextColor = isDark ? '#cbd5e1' : '#1e293b';
  const radiusStrokeColor = isDark ? '#475569' : '#94a3b8';
  const radiusTextColor = isDark ? '#94a3b8' : '#64748b';
  const benchmarkColor = isDark ? '#94a3b8' : '#64748b';
  const tooltipBg = isDark ? '#0f172a' : '#ffffff';
  const tooltipBorder = isDark ? '#334155' : '#e2e8f0';
  const tooltipTextColor = isDark ? '#f8fafc' : '#0f172a';
  const legendColor = isDark ? '#94a3b8' : '#334155';

  return (
    <div className="w-full h-80 sm:h-96">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
          <PolarGrid stroke={gridColor} />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: angleTextColor, fontSize: 11, fontWeight: 600 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            stroke={radiusStrokeColor}
            tick={{ fill: radiusTextColor, fontSize: 10 }}
          />
          <Radar
            name="Candidate Score"
            dataKey="Candidate"
            stroke="#4f46e5"
            fill="#6366f1"
            fillOpacity={isDark ? 0.45 : 0.35}
          />
          <Radar
            name="Industry Benchmark"
            dataKey="Benchmark"
            stroke={benchmarkColor}
            fill={benchmarkColor}
            fillOpacity={isDark ? 0.15 : 0.12}
            strokeDasharray="3 3"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: tooltipBg,
              borderColor: tooltipBorder,
              borderRadius: '0.75rem',
              color: tooltipTextColor,
              fontSize: '12px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
          />
          <Legend
            wrapperStyle={{
              paddingTop: '10px',
              fontSize: '12px',
              color: legendColor,
              fontWeight: 500,
            }}
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
};
