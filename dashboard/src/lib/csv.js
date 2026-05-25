// Minimal CSV serializer + browser download trigger.

function escapeField(value) {
  if (value == null) return "";
  const str = String(value);
  if (/[",\n\r]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

export function toCsv(rows, headers) {
  const cols = headers || Object.keys(rows[0] || {});
  const lines = [cols.join(",")];
  for (const row of rows) {
    lines.push(cols.map((c) => escapeField(row[c])).join(","));
  }
  return lines.join("\n");
}

export function downloadCsv(filename, content) {
  // ﻿ BOM so Excel reads Thai (UTF-8) correctly.
  const blob = new Blob(["﻿" + content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
