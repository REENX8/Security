import { useState } from "react";
import Layout from "../components/Layout.jsx";
import HistoryTable from "../components/HistoryTable.jsx";
import { useHistory } from "../api/queries.js";

const LIMIT = 25;

export default function History() {
  const [label, setLabel] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [offset, setOffset] = useState(0);

  const params = {
    limit: LIMIT,
    offset,
    label: label || undefined,
    search: search || undefined,
    dateFrom: dateFrom ? `${dateFrom}T00:00:00` : undefined,
    dateTo: dateTo ? `${dateTo}T23:59:59` : undefined,
  };
  const { data, isLoading, isError, error } = useHistory(params);

  const resetTo = (setter) => (value) => { setter(value); setOffset(0); };

  const applySearch = (e) => {
    e.preventDefault();
    setSearch(searchInput.trim());
    setOffset(0);
  };

  const clearFilters = () => {
    setLabel(""); setSearch(""); setSearchInput("");
    setDateFrom(""); setDateTo(""); setOffset(0);
  };

  return (
    <Layout title="ประวัติการตรวจสอบ">
      <div className="mb-5 rounded-xl border border-slate-800 bg-slate-900 p-4">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <form onSubmit={applySearch} className="md:col-span-2">
            <label className="mb-1 block text-xs text-slate-400">ค้นหา URL</label>
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="พิมพ์ส่วนหนึ่งของ URL แล้วกด Enter"
              className="w-full rounded-lg border border-slate-700 bg-slate-950
                         px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
          </form>

          <div>
            <label className="mb-1 block text-xs text-slate-400">ผลการตรวจ</label>
            <select
              value={label}
              onChange={(e) => resetTo(setLabel)(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950
                         px-3 py-2 text-sm outline-none focus:border-blue-500"
            >
              <option value="">ทั้งหมด</option>
              <option value="safe">ปลอดภัย</option>
              <option value="suspicious">น่าสงสัย</option>
              <option value="phishing">ฟิชชิง</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={clearFilters}
              className="w-full rounded-lg border border-slate-700 px-3 py-2
                         text-sm hover:bg-slate-800"
            >
              ล้างตัวกรอง
            </button>
          </div>

          <div>
            <label className="mb-1 block text-xs text-slate-400">ตั้งแต่วันที่</label>
            <input
              type="date" value={dateFrom}
              onChange={(e) => resetTo(setDateFrom)(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950
                         px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-400">ถึงวันที่</label>
            <input
              type="date" value={dateTo}
              onChange={(e) => resetTo(setDateTo)(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950
                         px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {isError && (
        <div className="mb-4 rounded-lg border border-phishing/40 bg-phishing/10 px-4 py-3 text-sm text-phishing">
          โหลดข้อมูลไม่สำเร็จ: {error.message}
        </div>
      )}

      <HistoryTable
        items={data?.items || []}
        total={data?.total || 0}
        limit={LIMIT}
        offset={offset}
        onPage={setOffset}
        loading={isLoading}
      />
    </Layout>
  );
}
