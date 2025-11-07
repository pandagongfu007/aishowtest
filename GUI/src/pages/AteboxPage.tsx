import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";

type TestResult = {
  case_name: string;
  start_time: string;
  end_time: string;
  result: string;
  message?: string | null;
};

export const AteboxPage: React.FC = () => {
  const { id } = useParams();
  const [rows, setRows] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    api
      .get<TestResult[]>(`/atebox/${id}/results`)
      .then((res) => setRows(res.data))
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <div>
      <h2>Atebox-{id} 测试结果</h2>
      <div style={{ marginBottom: 8 }}>
        <Link to="/">← 返回总览</Link>
      </div>
      {loading ? (
        <div>加载中…</div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th>用例名称</th>
              <th>开始时间</th>
              <th>结束时间</th>
              <th>结果</th>
              <th>备注</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.case_name}>
                <td>{r.case_name}</td>
                <td>{r.start_time}</td>
                <td>{r.end_time}</td>
                <td
                  style={{
                    color: r.result === "PASS" ? "#16a34a" : "#dc2626",
                    fontWeight: 600,
                  }}
                >
                  {r.result}
                </td>
                <td>{r.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};
