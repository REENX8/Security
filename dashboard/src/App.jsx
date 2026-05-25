import { Routes, Route, Navigate } from "react-router-dom";
import Overview from "./pages/Overview.jsx";
import History from "./pages/History.jsx";
import Stats from "./pages/Stats.jsx";
import Bulk from "./pages/Bulk.jsx";
import Admin from "./pages/Admin.jsx";
import Feedback from "./pages/Feedback.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Overview />} />
      <Route path="/bulk" element={<Bulk />} />
      <Route path="/history" element={<History />} />
      <Route path="/stats" element={<Stats />} />
      <Route path="/admin" element={<Admin />} />
      <Route path="/feedback" element={<Feedback />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
