import React from "react";

const ATEBOX_LINKS = [
  { id: 1, name: "Atebox-1", url: "http://192.168.3.100:8001" },
  { id: 2, name: "Atebox-2", url: "http://192.168.3.101:8001" },
  { id: 3, name: "Atebox-3", url: "http://192.168.3.102:8001" },
  { id: 4, name: "Atebox-4", url: "http://192.168.3.103:8001" },
  { id: 5, name: "Atebox-5", url: "http://192.168.3.104:8001" },
];

export const ConfigEntryPage: React.FC = () => (
  <div>
    <h2>配置入口</h2>
    <p>点击下面链接，在新标签页打开对应 Atebox 的管理界面：</p>
    <ul>
      {ATEBOX_LINKS.map((item) => (
        <li key={item.id} style={{ marginBottom: 6 }}>
          <button
            onClick={() => window.open(item.url, "_blank")}
            style={{
              padding: "6px 10px",
              borderRadius: 6,
              border: "1px solid var(--primary)",
              background: "#fff",
              color: "var(--primary)",
              cursor: "pointer",
            }}
          >
            {item.name} 配置页面
          </button>
        </li>
      ))}
    </ul>
  </div>
);
