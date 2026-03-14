export default function TradesTable({ trades }) {
  const hasData = trades && trades.length > 0;

  if (!hasData) {
    return <p className="text-gray-400 text-sm py-8 text-center">No trades available</p>;
  }

  const columns = Array.from(new Set(trades.flatMap((t) => Object.keys(t))));

  return (
    <table className="w-full text-sm text-left">
      <thead className="sticky top-0 bg-gray-800">
        <tr className="text-gray-400 border-b border-gray-700">
          {columns.map((col) => (
            <th key={col} className="pb-2 pr-4 pl-4 pt-2 font-medium capitalize text-xs">
              {col.replace(/_/g, " ")}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {trades.map((trade, i) => (
          <tr key={i} className="border-b border-gray-700 last:border-0 text-gray-300">
            {columns.map((col) => (
              <td key={col} className="py-1.5 pr-4 pl-4 text-xs">
                {trade[col] != null ? String(trade[col]) : "—"}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
