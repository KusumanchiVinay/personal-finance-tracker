/**
 * components/insights/HealthScoreRing.tsx
 * Animated SVG ring gauge for the financial health score
 */
import React from "react";

interface Props {
  score: number;   // 0-100
  grade: string;   // A | B | C | D
  size?: number;
}

const GRADE_COLOR: Record<string, string> = {
  A: "#10b981",
  B: "#6366f1",
  C: "#f59e0b",
  D: "#ef4444",
};

export default function HealthScoreRing({ score, grade, size = 120 }: Props) {
  const r      = size * 0.38;
  const cx     = size / 2;
  const cy     = size / 2;
  const circ   = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color  = GRADE_COLOR[grade] ?? "#6366f1";

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="shrink-0">
      {/* Track */}
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#334155" strokeWidth={size * 0.07} />
      {/* Progress */}
      <circle
        cx={cx} cy={cy} r={r}
        fill="none"
        stroke={color}
        strokeWidth={size * 0.07}
        strokeLinecap="round"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        transform={`rotate(-90 ${cx} ${cy})`}
        style={{ transition: "stroke-dashoffset 1s ease-in-out" }}
      />
      {/* Glow */}
      <circle
        cx={cx} cy={cy} r={r}
        fill="none"
        stroke={color}
        strokeWidth={size * 0.03}
        strokeLinecap="round"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        transform={`rotate(-90 ${cx} ${cy})`}
        opacity={0.3}
        filter="blur(3px)"
      />
      {/* Score text */}
      <text x={cx} y={cy - size * 0.04} textAnchor="middle" fill="white"
        fontSize={size * 0.22} fontWeight="700" fontFamily="system-ui">
        {score}
      </text>
      {/* Grade */}
      <text x={cx} y={cy + size * 0.18} textAnchor="middle" fill={color}
        fontSize={size * 0.14} fontWeight="600" fontFamily="system-ui">
        Grade {grade}
      </text>
    </svg>
  );
}
