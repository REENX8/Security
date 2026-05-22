import { Routes, Route, Navigate } from "react-router-dom";
import Overview from "./pages/Overview.jsx";
import History from "./pages/History.jsx";
import Stats from "./pages/Stats.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Overview />} />
      <Route path="/history" element={<History />} />
      <Route path="/stats" element={<Stats />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
