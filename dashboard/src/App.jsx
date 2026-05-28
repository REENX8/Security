import { Routes, Route, Navigate } from "react-router-dom";
import Overview from "./pages/Overview.jsx";
import History from "./pages/History.jsx";
import Stats from "./pages/Stats.jsx";
import Bulk from "./pages/Bulk.jsx";
import Admin from "./pages/Admin.jsx";
import Feedback from "./pages/Feedback.jsx";
import Report from "./pages/Report.jsx";
import Watchlist from "./pages/Watchlist.jsx";
import Campaigns from "./pages/Campaigns.jsx";
import Feed from "./pages/Feed.jsx";
import DomainLookup from "./pages/DomainLookup.jsx";
import About from "./pages/About.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Overview />} />
      <Route path="/bulk" element={<Bulk />} />
      <Route path="/history" element={<History />} />
      <Route path="/stats" element={<Stats />} />
      <Route path="/admin" element={<Admin />} />
      <Route path="/feedback" element={<Feedback />} />
      <Route path="/report" element={<Report />} />
      <Route path="/watchlist" element={<Watchlist />} />
      <Route path="/campaigns" element={<Campaigns />} />
      <Route path="/domain" element={<DomainLookup />} />
      <Route path="/feed" element={<Feed />} />
      <Route path="/about" element={<About />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
