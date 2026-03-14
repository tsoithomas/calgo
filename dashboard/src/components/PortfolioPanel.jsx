export default function PortfolioPanel({ snapshots }) {
  const hasData = snapshots && snapshots.length > 0;
  const latest = hasData ? snapshots[snapshots.length - 1] : null;

  if (!latest) {
    return <p className="text-gray-400 text-sm py-8 text-center">No portfolio data available</p>;
  }

  return (
    <dl className="px-4 py-2 space-y-1.5">
      {Object.entries(latest).map(([key, value]) => (
        <div key={key} className="flex justify-between text-xs border-b border-gray-700 pb-1.5 last:border-0">
          <dt className="text-gray-400 capitalize">{key.replace(/_/g, " ")}</dt>
          <dd className="text-gray-200 font-mono text-right max-w-xs truncate">
            {value != null ? String(typeof value === "object" ? JSON.stringify(value) : value) : "—"}
          </dd>
        </div>
      ))}
    </dl>
  );
}
