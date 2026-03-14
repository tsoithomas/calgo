import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

export default function PriceChart({ data, symbol }) {
  const records = data?.records;
  const hasData = records && records.length > 0;

  const chartData = hasData
    ? records.map((r) => ({
        date: r.timestamp.split("T")[0],
        close: parseFloat(r.close),
      }))
    : [];

  if (!hasData) {
    return (
      <p className="text-gray-400 text-sm py-12 text-center">
        No price data available for {symbol}
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} tickLine={false} />
        <YAxis
          tick={{ fill: "#9ca3af", fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          domain={["auto", "auto"]}
          width={55}
        />
        <Tooltip
          contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 6 }}
          labelStyle={{ color: "#d1d5db" }}
          itemStyle={{ color: "#60a5fa" }}
        />
        <Line type="monotone" dataKey="close" stroke="#60a5fa" dot={false} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}
