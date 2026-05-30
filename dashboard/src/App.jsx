import { Routes, Route, Navigate } from "react-router-dom";
import PrivateRoute from "./components/PrivateRoute.jsx";
import Login from "./pages/Login.jsx";
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
import Impact from "./pages/Impact.jsx";
import Learn from "./pages/Learn.jsx";
import About from "./pages/About.jsx";

function Private({ children }) {
  return <PrivateRoute>{children}</PrivateRoute>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Private><Overview /></Private>} />
      <Route path="/bulk" element={<Private><Bulk /></Private>} />
      <Route path="/history" element={<Private><History /></Private>} />
      <Route path="/stats" element={<Private><Stats /></Private>} />
      <Route path="/admin" element={<Private><Admin /></Private>} />
      <Route path="/feedback" element={<Private><Feedback /></Private>} />
      <Route path="/report" element={<Private><Report /></Private>} />
      <Route path="/watchlist" element={<Private><Watchlist /></Private>} />
      <Route path="/campaigns" element={<Private><Campaigns /></Private>} />
      <Route path="/domain" element={<Private><DomainLookup /></Private>} />
      <Route path="/impact" element={<Private><Impact /></Private>} />
      <Route path="/learn" element={<Private><Learn /></Private>} />
      <Route path="/feed" element={<Private><Feed /></Private>} />
      <Route path="/about" element={<Private><About /></Private>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
