import { useState } from "react";

/**
 * Panel wrapper — fixed height with internal scroll by default.
 * An expand button lets the user toggle to full height.
 */
export default function Panel({ title, children, defaultHeight = "h-48" }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`bg-gray-800 rounded-lg flex flex-col min-h-0 ${expanded ? "h-full" : defaultHeight}`}>
      {/* Panel header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700 shrink-0">
        <h2 className="text-white font-semibold text-xs tracking-wide uppercase">{title}</h2>
        <button
          onClick={() => setExpanded((e) => !e)}
          title={expanded ? "Collapse" : "Expand"}
          className="text-gray-500 hover:text-gray-300 transition-colors text-xs leading-none"
        >
          {expanded ? "⊟" : "⊞"}
        </button>
      </div>

      {/* Scrollable body — fills remaining panel height */}
      <div className="flex-1 min-h-0 overflow-y-auto overflow-x-auto">
        {children}
      </div>
    </div>
  );
}
