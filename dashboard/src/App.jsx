import { useState, useEffect } from "react";
import Header from "./components/Header";
import Panel from "./components/Panel";
import PriceChart from "./components/PriceChart";
import SignalsTable from "./components/SignalsTable";
import TradesTable from "./components/TradesTable";
import PortfolioPanel from "./components/PortfolioPanel";
import LogsPanel from "./components/LogsPanel";
import {
  useSymbols,
  useDates,
  usePriceHistory,
  useSignals,
  useTrades,
  usePortfolio,
  useLogs,
} from "./hooks/useDataHooks";

export default function App() {
  const [selectedSymbol, setSelectedSymbol] = useState("AAPL");
  const [selectedDate, setSelectedDate] = useState(
    () => new Date().toISOString().split("T")[0]
  );
  const [bannerDismissed, setBannerDismissed] = useState(false);

  const symbols = useSymbols();
  const dates = useDates();
  const priceHistory = usePriceHistory(selectedSymbol);
  const signals = useSignals(selectedDate);
  const trades = useTrades(selectedDate);
  const portfolio = usePortfolio(selectedDate);
  const logs = useLogs(selectedDate);

  useEffect(() => {
    if (symbols.data?.length > 0) {
      setSelectedSymbol((prev) =>
        symbols.data.includes(prev) ? prev : symbols.data[0]
      );
    }
  }, [symbols.data]);

  useEffect(() => {
    if (dates.data?.signals?.length > 0) {
      setSelectedDate((prev) =>
        dates.data.signals.includes(prev) ? prev : dates.data.signals[0]
      );
    }
  }, [dates.data]);

  const errors = [
    symbols.error, dates.error, priceHistory.error,
    signals.error, trades.error, portfolio.error, logs.error,
  ].filter(Boolean);

  useEffect(() => {
    if (errors.length > 0) setBannerDismissed(false);
  }, [errors.length]);

  const showBanner = errors.length > 0 && !bannerDismissed;
  const symbolList = symbols.data ?? [];
  const dateList = dates.data?.signals ?? [];

  return (
    // Full viewport height, no overflow on the root
    <div className="h-screen bg-gray-900 text-white flex flex-col overflow-hidden">
      <Header
        symbols={symbolList}
        symbol={selectedSymbol}
        onSymbolChange={setSelectedSymbol}
        dates={dateList}
        date={selectedDate}
        onDateChange={setSelectedDate}
        isPolling={true}
      />

      {showBanner && (
        <div
          role="alert"
          className="flex items-center justify-between gap-2 px-4 py-1.5 bg-red-950 border-b border-red-800 text-red-300 text-xs shrink-0"
        >
          <span>{errors.map((e) => e?.message ?? String(e)).join(" | ")}</span>
          <button
            aria-label="Dismiss error"
            onClick={() => setBannerDismissed(true)}
            className="ml-4 text-red-400 hover:text-white font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/*
        Main grid — 2 columns, 3 rows:
          Row 1: Close Price (spans 2 cols)
          Row 2: Trading Signals | Executed Trades
          Row 3: Portfolio       | System Logs
      */}
      <main className="flex-1 min-h-0 p-3 grid gap-3
        grid-cols-1
        lg:grid-cols-2
        lg:grid-rows-[minmax(0,2fr)_minmax(0,3fr)_minmax(0,3fr)]">

        {/* Row 1 — Price chart spans both columns */}
        <div className="lg:col-span-2 min-h-0">
          <Panel title={`${selectedSymbol} — Close Price`} defaultHeight="h-full">
            <div className="h-full px-1 pb-2">
              <PriceChart data={priceHistory.data} symbol={selectedSymbol} />
            </div>
          </Panel>
        </div>

        {/* Row 2 */}
        <Panel title="Trading Signals" defaultHeight="h-full">
          <SignalsTable signals={signals.data} />
        </Panel>

        <Panel title="Executed Trades" defaultHeight="h-full">
          <TradesTable trades={trades.data} />
        </Panel>

        {/* Row 3 */}
        <Panel title="Portfolio" defaultHeight="h-full">
          <PortfolioPanel snapshots={portfolio.data} />
        </Panel>

        <Panel title="System Logs" defaultHeight="h-full">
          <LogsPanel logs={logs.data} />
        </Panel>
      </main>
    </div>
  );
}
