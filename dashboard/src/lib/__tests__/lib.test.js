import { describe, it, expect } from "vitest";
import { toCsv } from "../csv.js";
import { formatPct, labelInfo, truncate } from "../format.js";
import { groupFeatures, isNotable, FEATURE_LABELS } from "../features.js";

describe("csv", () => {
  it("serializes rows with explicit headers", () => {
    const csv = toCsv([{ a: 1, b: "x" }], ["a", "b"]);
    expect(csv).toBe("a,b\n1,x");
  });

  it("quotes fields containing commas, quotes and newlines", () => {
    const csv = toCsv([{ a: 'he said "hi", ok\nnext' }], ["a"]);
    expect(csv).toBe('a\n"he said ""hi"", ok\nnext"');
  });

  it("renders null/undefined as empty", () => {
    expect(toCsv([{ a: null, b: undefined }], ["a", "b"])).toBe("a,b\n,");
  });
});

describe("format", () => {
  it("formats a 0..1 score as a percentage", () => {
    expect(formatPct(0.873)).toBe("87%");
    expect(formatPct(undefined)).toBe("0%");
  });

  it("maps known labels and falls back to unverified", () => {
    expect(labelInfo("phishing").th).toBe("ฟิชชิง");
    expect(labelInfo("???").th).toBe(labelInfo("unverified").th);
  });

  it("truncates long text", () => {
    expect(truncate("abcdef", 3)).toBe("abc…");
    expect(truncate("ab", 3)).toBe("ab");
  });
});

describe("features", () => {
  it("groups known features and humanizes labels", () => {
    const groups = groupFeatures({ has_ip: true, has_punycode: false, mystery: 1 });
    const titles = groups.map((g) => g.title);
    expect(titles).toContain("อื่น ๆ"); // unknown key bucketed
    expect(FEATURE_LABELS.has_ip).toBe("ใช้ IP แทนโดเมน");
  });

  it("flags suspicious signals as notable", () => {
    expect(isNotable("has_ip", true)).toBe(true);
    expect(isNotable("has_ip", false)).toBe(false);
    expect(isNotable("has_https", false)).toBe(true); // missing https is notable
    expect(isNotable("url_length", 120)).toBe(false);
  });
});
