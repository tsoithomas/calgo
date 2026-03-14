const SEVERITY_CLASSES = {
  INFO: "log-info text-blue-400",
  WARNING: "log-warning text-yellow-400",
  ERROR: "log-error text-red-400",
};

export default function LogsPanel({ logs }) {
  const hasData = logs && logs.length > 0;

  if (!hasData) {
    return <p className="text-gray-400 text-sm py-8 text-center">No logs available</p>;
  }

  return (
    <div className="space-y-0">
      {logs.map((entry, i) => {
        const severityClass = SEVERITY_CLASSES[entry.severity] ?? "log-info text-gray-300";
        return (
          <div
            key={i}
            className={`text-xs font-mono flex gap-2 px-4 py-1 border-b border-gray-700 last:border-0 ${severityClass}`}
          >
            <span className="text-gray-500 shrink-0">{entry.timestamp}</span>
            <span className="font-bold shrink-0">[{entry.severity}]</span>
            <span className="text-gray-400 shrink-0">{entry.component}</span>
            <span className="text-gray-200 break-all">{entry.message}</span>
          </div>
        );
      })}
    </div>
  );
}
