// Consistent error banner used across all pages instead of ad-hoc red boxes.
export default function ErrorBanner({ error, message }) {
  const text =
    message || (error && (error.message || String(error))) || "เกิดข้อผิดพลาด";
  const isNetworkError = text.includes("ไม่สามารถเชื่อมต่อ") || text.includes("Failed to fetch");
  return (
    <div className="rounded-lg border border-phishing/40 bg-phishing/10 px-4 py-3 text-sm text-phishing">
      <div>{text}</div>
      {isNetworkError && (
        <div className="mt-1 text-xs opacity-80">
          ตั้งค่า <code className="font-mono">VITE_API_URL</code> ใน{" "}
          <code className="font-mono">dashboard/.env</code> ให้ชี้ไปที่ backend
        </div>
      )}
    </div>
  );
}
