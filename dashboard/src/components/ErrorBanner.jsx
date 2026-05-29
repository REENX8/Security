// Consistent error banner used across all pages instead of ad-hoc red boxes.
export default function ErrorBanner({ error, message }) {
  const text =
    message || (error && (error.message || String(error))) || "เกิดข้อผิดพลาด";
  return (
    <div className="rounded-lg border border-phishing/40 bg-phishing/10 px-4 py-3 text-sm text-phishing">
      ไม่สามารถเชื่อมต่อ API ได้: {text}
    </div>
  );
}
