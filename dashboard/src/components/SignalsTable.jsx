export default function SignalsTable({ signals }) {
  const hasData = signals && signals.length > 0;

  if (!hasData) {
    return <p className="text-gray-400 text-sm py-8 text-center">No signals available</p>;
  }

  return (
    <table className="w-full text-sm text-left">
      <thead className="sticky top-0 bg-gray-800">
        <tr className="text-gray-400 border-b border-gray-700">
          <th className="pb-2 pr-4 pl-4 pt-2 font-medium">Symbol</th>
          <th className="pb-2 pr-4 font-medium">Timestamp</th>
          <th className="pb-2 pr-4 font-medium">Rec.</th>
          <th className="pb-2 pr-4 font-medium">Conf.</th>
          <th className="pb-2 pr-4 font-medium">Model</th>
        </tr>
      </thead>
      <tbody>
        {signals.map((signal, i) => (
          <tr key={i} className="border-b border-gray-700 last:border-0 text-gray-300">
            <td className="py-1.5 pr-4 pl-4 font-mono text-blue-400 text-xs">{signal.symbol}</td>
            <td className="py-1.5 pr-4 text-xs text-gray-400">{signal.timestamp}</td>
            <td className="py-1.5 pr-4 capitalize text-xs">{signal.recommendation}</td>
            <td className="py-1.5 pr-4 text-xs">
              {signal.confidence != null ? (signal.confidence * 100).toFixed(1) + "%" : "—"}
            </td>
            <td className="py-1.5 pr-4 font-mono text-xs text-gray-400">{signal.model_id}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
