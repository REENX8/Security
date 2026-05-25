import { labelInfo } from "../lib/format.js";

export default function LabelBadge({ label }) {
  const info = labelInfo(label);
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${info.bg} ${info.text}`}
    >
      {info.th}
    </span>
  );
}
