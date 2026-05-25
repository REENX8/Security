import { useState } from "react";
import Layout from "../components/Layout.jsx";
import { useWhitelist, useAddWhitelistEntry, useDeleteWhitelistEntry } from "../api/queries.js";

const LIMIT = 50;

const CATEGORIES = ["go.th", "ac.th", "or.th", "co.th", "other"];

export default function Admin() {
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [offset, setOffset] = useState(0);

  const [addDomain, setAddDomain] = useState("");
  const [addAgency, setAddAgency] = useState("");
  const [addCategory, setAddCategory] = useState("other");
  const [addError, setAddError] = useState("");

  const [confirmDelete, setConfirmDelete] = useState(null);

  const params = { search: search || undefined, limit: LIMIT, offset };
  const { data, isLoading, isError, error } = useWhitelist(params);
  const addMutation = useAddWhitelistEntry();
  const deleteMutation = useDeleteWhitelistEntry();

  const applySearch = (e) => {
    e.preventDefault();
    setSearch(searchInput.trim());
    setOffset(0);
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    setAddError("");
    const domain = addDomain.trim().toLowerCase();
    if (!domain) return;
    try {
      await addMutation.mutateAsync({
        domain,
        agency_name: addAgency.trim(),
        category: addCategory,
      });
      setAddDomain("");
      setAddAgency("");
      setAddCategory("other");
    } catch (err) {
      setAddError(err.message);
    }
  };

  const handleDelete = async (domain) => {
    try {
      await deleteMutation.mutateAsync(domain);
    } catch (err) {
      alert(`ลบไม่ได้: ${err.message}`);
    } finally {
      setConfirmDelete(null);
    }
  };

  const total = data?.total ?? 0;
  const items = data?.items ?? [];

  return (
    <Layout title="จัดการ Whitelist">
      {/* Add new entry */}
      <div className="mb-6 rounded-xl border border-slate-800 bg-slate-900 p-5">
        <h2 className="mb-4 text-sm font-semibold text-slate-300">เพิ่มโดเมนที่เชื่อถือได้</h2>
        <form onSubmit={handleAdd} className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <div className="md:col-span-2">
            <label className="mb-1 block text-xs text-slate-400">โดเมน *</label>
            <input
              type="text"
              value={addDomain}
              onChange={(e) => setAddDomain(e.target.value)}
              placeholder="เช่น moe.go.th"
              required
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-400">ชื่อหน่วยงาน</label>
            <input
              type="text"
              value={addAgency}
              onChange={(e) => setAddAgency(e.target.value)}
              placeholder="กระทรวงศึกษาธิการ"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-400">หมวดหมู่</label>
            <select
              value={addCategory}
              onChange={(e) => setAddCategory(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-blue-500"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          {addError && (
            <p className="md:col-span-4 text-xs text-red-400">{addError}</p>
          )}
          <div className="md:col-span-4 flex justify-end">
            <button
              type="submit"
              disabled={addMutation.isPending}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {addMutation.isPending ? "กำลังเพิ่ม..." : "เพิ่มโดเมน"}
            </button>
          </div>
        </form>
      </div>

      {/* Search + table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <form onSubmit={applySearch} className="flex gap-2">
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="ค้นหาโดเมน..."
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium hover:bg-slate-600"
            >
              ค้นหา
            </button>
            {search && (
              <button
                type="button"
                onClick={() => { setSearch(""); setSearchInput(""); setOffset(0); }}
                className="rounded-lg px-3 py-2 text-sm text-slate-400 hover:text-white"
              >
                ล้าง
              </button>
            )}
          </form>
          <span className="text-xs text-slate-500">ทั้งหมด {total} รายการ</span>
        </div>

        {isLoading ? (
          <p className="py-8 text-center text-slate-400">กำลังโหลด...</p>
        ) : isError ? (
          <p className="py-8 text-center text-red-400">{error?.message}</p>
        ) : items.length === 0 ? (
          <p className="py-8 text-center text-slate-500">ไม่พบข้อมูล</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-xs uppercase text-slate-500">
                  <th className="pb-2 text-left">โดเมน</th>
                  <th className="pb-2 text-left">ชื่อหน่วยงาน</th>
                  <th className="pb-2 text-left">หมวดหมู่</th>
                  <th className="pb-2 text-left">เพิ่มโดย</th>
                  <th className="pb-2 text-right">จัดการ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/40">
                    <td className="py-2.5 font-mono text-xs text-blue-300">
                      {item.domain}
                    </td>
                    <td className="py-2.5 text-slate-300">
                      {item.agency_name || <span className="text-slate-600">—</span>}
                    </td>
                    <td className="py-2.5">
                      <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
                        {item.category}
                      </span>
                    </td>
                    <td className="py-2.5 text-xs text-slate-500">
                      {item.is_seeded ? "seed" : item.added_by}
                    </td>
                    <td className="py-2.5 text-right">
                      {!item.is_seeded ? (
                        <button
                          onClick={() => setConfirmDelete(item.domain)}
                          className="rounded px-2 py-1 text-xs text-red-400 hover:bg-red-900/30 hover:text-red-300"
                        >
                          ลบ
                        </button>
                      ) : (
                        <span className="text-xs text-slate-600">seed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {total > LIMIT && (
          <div className="mt-4 flex items-center justify-between text-xs text-slate-400">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
              className="rounded px-3 py-1 hover:bg-slate-800 disabled:opacity-30"
            >
              ← ก่อนหน้า
            </button>
            <span>
              {offset + 1}–{Math.min(offset + LIMIT, total)} จาก {total}
            </span>
            <button
              disabled={offset + LIMIT >= total}
              onClick={() => setOffset(offset + LIMIT)}
              className="rounded px-3 py-1 hover:bg-slate-800 disabled:opacity-30"
            >
              ถัดไป →
            </button>
          </div>
        )}
      </div>

      {/* Confirm delete modal */}
      {confirmDelete && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setConfirmDelete(null)}
        >
          <div
            className="w-full max-w-sm rounded-xl border border-slate-700 bg-slate-900 p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-3 text-base font-semibold text-white">ยืนยันการลบ</h3>
            <p className="mb-5 text-sm text-slate-300">
              ต้องการลบ <span className="font-mono text-red-300">{confirmDelete}</span>{" "}
              ออกจาก whitelist ใช่ไหม? การกระทำนี้จะทำให้ระบบ re-evaluate URLs ที่เกี่ยวข้องทันที
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmDelete(null)}
                className="rounded-lg border border-slate-700 px-4 py-2 text-sm hover:bg-slate-800"
              >
                ยกเลิก
              </button>
              <button
                onClick={() => handleDelete(confirmDelete)}
                disabled={deleteMutation.isPending}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium hover:bg-red-700 disabled:opacity-50"
              >
                {deleteMutation.isPending ? "กำลังลบ..." : "ลบออก"}
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
