/**
 * components/shared/Spinner.tsx
 */
import React from "react";

export default function Spinner({ text = "Loading…" }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4">
      <div className="w-10 h-10 border-4 border-slate-700 border-t-indigo-500 rounded-full animate-spin" />
      <p className="text-slate-400 text-sm">{text}</p>
    </div>
  );
}
