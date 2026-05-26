import { useState } from "react";
import Layout from "../components/Layout.jsx";
import { useCheckUrl, useSubmitFeedback } from "../api/queries.js";

const CHOICES = [
  { value: "phishing", label: "ฟิชชิง / หลอกลวง", color: "bg-phishing/20 text-phishing" },
  { value: "suspicious", label: "น่าสงสัย / ผิดปกติ", color: "bg-suspicious/20 text-suspicious" },
  { value: "safe", label: "ปลอดภัย (ระบบตัดสินผิด)", color: "bg-safe/20 text-safe" },
];

export default function Report() {
  const [url, setUrl] = useState("");
  const [choice, setChoice] = useState("phishing");
  const [comment, setComment] = useState("");
  const [verdict, setVerdict] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const checkUrl = useCheckUrl();
  const submitFb = useSubmitFeedback();

  const handleCheck = async () => {
    if (!url.trim()) return;
    setSubmitted(false);
    try {
      const result = await checkUrl.mutateAsync(url.trim());
      setVerdict(result);
    } catch (err) {
      setVerdict({ error: err.message });
    }
  };

  const handleSubmit = async () => {
    if (!url.trim() || !choice) return;
    await submitFb.mutateAsync({
      url: url.trim(),
      verdict_given: verdict?.label || "unverified",
      correct_verdict: choice,
      comment,
      source: "dashboard",
    });
    setSubmitted(true);
  };

  return (
    <Layout title="แจ้งเว็บฟิชชิง">
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="rounded-2xl border border-blue-600/30 bg-blue-600/10 p-5 text-sm text-blue-200">
          <div className="mb-1 text-base font-semibold text-blue-100">
            แจ้งเว็บไซต์ที่สงสัยให้ทีมงานตรวจสอบ
          </div>
          คุณไม่ต้อง login — กรอก URL ที่พบ ระบุประเภท และเพิ่มรายละเอียดถ้ามี
          การแจ้งทุกครั้งจะถูกบันทึก, ใช้ปรับปรุงโมเดลและส่งต่อให้หน่วยงานที่เกี่ยวข้องเมื่อจำเป็น
        </div>

        <section className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <label className="block text-sm font-semibold">
            URL ที่ต้องการแจ้ง
          </label>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example-phishing-site.cc/login"
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />

          <div className="flex gap-2">
            <button
              onClick={handleCheck}
              disabled={checkUrl.isPending || !url.trim()}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium hover:bg-blue-500 disabled:opacity-50"
            >
              {checkUrl.isPending ? "กำลังตรวจ..." : "ตรวจสอบก่อนแจ้ง"}
            </button>
          </div>

          {verdict?.error && (
            <div className="rounded-lg bg-phishing/10 px-3 py-2 text-sm text-phishing">
              {verdict.error}
            </div>
          )}

          {verdict?.label && (
            <div className="rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm">
              <div className="mb-1">
                ระบบประเมินว่า:{" "}
                <span
                  className={
                    verdict.label === "phishing" ? "text-phishing" :
                    verdict.label === "suspicious" ? "text-suspicious" :
                    "text-safe"
                  }
                >
                  <b>{verdict.label}</b>
                </span>{" "}
                — คะแนน {(verdict.score * 100).toFixed(0)}%
              </div>
              <div className="text-slate-300">{verdict.reason}</div>
              {verdict?.rules?.hits?.length > 0 && (
                <div className="mt-2 text-xs text-slate-400">
                  Rule ที่ทำงาน:{" "}
                  {verdict.rules.hits.map((h) => h.rule_id).join(", ")}
                </div>
              )}
            </div>
          )}
        </section>

        <section className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <label className="block text-sm font-semibold">
            คุณคิดว่า URL นี้คือ?
          </label>
          <div className="flex flex-wrap gap-2">
            {CHOICES.map((c) => (
              <button
                key={c.value}
                onClick={() => setChoice(c.value)}
                className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                  choice === c.value
                    ? c.color + " ring-2 ring-blue-400"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>

          <label className="block text-sm font-semibold pt-3">
            รายละเอียดเพิ่มเติม (ไม่จำเป็น)
          </label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="คุณพบ URL นี้จากที่ไหน? มีข้อความที่หลอกอย่างไร?"
            rows={4}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />

          <button
            onClick={handleSubmit}
            disabled={!url.trim() || submitFb.isPending || submitted}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
          >
            {submitted
              ? "ส่งรายงานเรียบร้อย ✓"
              : submitFb.isPending
              ? "กำลังส่ง..."
              : "ส่งรายงาน"}
          </button>

          {submitted && (
            <div className="rounded-lg bg-emerald-600/10 px-3 py-2 text-sm text-emerald-200">
              ขอบคุณที่ช่วยรายงาน — รายงานของคุณช่วยปกป้องคนอื่นจากเว็บปลอม
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
}
