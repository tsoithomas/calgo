export default function Header({
  symbols,
  symbol,
  onSymbolChange,
  dates,
  date,
  onDateChange,
  isPolling,
}) {
  return (
    <header className="flex items-center gap-4 px-4 py-2.5 bg-gray-900 border-b border-gray-700 shrink-0">
      {/* Branding */}
      <div className="flex items-center gap-2 mr-2">
        <span className="text-blue-400 font-bold text-lg tracking-tight">calgo</span>
        <span className="text-gray-600 text-xs font-light hidden sm:inline">trading dashboard</span>
      </div>

      <div className="w-px h-5 bg-gray-700" />

      <div className="flex items-center gap-2">
        <label htmlFor="symbol-select" className="text-gray-500 text-xs">Symbol</label>
        <select
          id="symbol-select"
          value={symbol}
          onChange={(e) => onSymbolChange(e.target.value)}
          className="bg-gray-800 text-white text-xs rounded px-2 py-1 border border-gray-700 focus:outline-none focus:border-blue-500"
        >
          {symbols.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-2">
        <label htmlFor="date-select" className="text-gray-500 text-xs">Date</label>
        <select
          id="date-select"
          value={date}
          onChange={(e) => onDateChange(e.target.value)}
          className="bg-gray-800 text-white text-xs rounded px-2 py-1 border border-gray-700 focus:outline-none focus:border-blue-500"
        >
          {dates.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>

      {isPolling && (
        <div className="ml-auto flex items-center gap-1.5 text-green-500 text-xs">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
          live
        </div>
      )}
    </header>
  );
}
