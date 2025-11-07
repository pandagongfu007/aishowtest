import React from "react";
import { Link, Routes, Route, useLocation } from "react-router-dom";
import { OverviewPage } from "./pages/OverviewPage";
import { AteboxPage } from "./pages/AteboxPage";
import { ConfigEntryPage } from "./pages/ConfigEntryPage";

const Sidebar: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { to: "/", label: "总览" },
    ...Array.from({ length: 5 }).map((_, i) => ({
      to: `/atebox/${i + 1}`,
      label: `Atebox-${i + 1}`,
    })),
    { to: "/config", label: "配置入口" },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-title">Aishow 自动化系统</div>
      {navItems.map((item) => (
        <Link
          key={item.to}
          to={item.to}
          className={
            "nav-link" + (location.pathname === item.to ? " active" : "")
          }
        >
          {item.label}
        </Link>
      ))}
    </div>
  );
};

const App: React.FC = () => (
  <div className="app-root">
    <Sidebar />
    <main className="main">
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/atebox/:id" element={<AteboxPage />} />
        <Route path="/config" element={<ConfigEntryPage />} />
      </Routes>
    </main>
  </div>
);

export default App;
