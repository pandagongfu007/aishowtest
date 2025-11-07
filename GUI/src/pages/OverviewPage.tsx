import React, { useEffect, useState } from "react";
import { api } from "../api/client";

type AteboxStatus = {
  id: number;
  name: string;
  online: boolean;
  last_result?: string | null;
  last_updated?: string | null;
};

export const OverviewPage: React.FC = () => {
  const [items, setItems] = useState<AteboxStatus[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<AteboxStatus[]>("/overview")
      .then((res) => setItems(res.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>加载中…</div>;

  return (
    <div>
      <h2>加固机 / Atebox 总览</h2>
      <div className="card-grid">
        {items.map((it) => (
          <div className="card" key={it.id}>
            <div className="card-title">{it.name}</div>
            <div>
              <span
                className="badge-dot"
                style={{ background: it.online ? "#22c55e" : "#cbd5e1" }}
              />
              {it.online ? "在线" : "离线"}
            </div>
            <div>最近结果：{it.last_result ?? "—"}</div>
            <div>更新时间：{it.last_updated ?? "—"}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
