// Render smoke tests for the prop-driven presentational components. We render
// to static markup with react-dom/server (already a dependency) so no jsdom /
// testing-library is needed — this is cheap insurance that these components
// mount without throwing and surface their key content.

import { describe, it, expect } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

import StatCard from "../StatCard.jsx";
import ErrorBanner from "../ErrorBanner.jsx";
import RulesPanel from "../RulesPanel.jsx";
import { Skeleton, StatCardSkeleton, CardSkeleton } from "../Skeleton.jsx";

describe("StatCard", () => {
  it("renders title and value", () => {
    const html = renderToStaticMarkup(
      <StatCard title="การตรวจทั้งหมด" value="1,234" sub="ทั้งหมด" />
    );
    expect(html).toContain("การตรวจทั้งหมด");
    expect(html).toContain("1,234");
    expect(html).toContain("ทั้งหมด");
  });
});

describe("ErrorBanner", () => {
  it("shows an explicit message", () => {
    const html = renderToStaticMarkup(<ErrorBanner message="พังจริง" />);
    expect(html).toContain("พังจริง");
  });

  it("falls back to error.message then a default", () => {
    expect(
      renderToStaticMarkup(<ErrorBanner error={new Error("boom")} />)
    ).toContain("boom");
    expect(renderToStaticMarkup(<ErrorBanner />)).toContain("เกิดข้อผิดพลาด");
  });
});

describe("RulesPanel", () => {
  it("lists fired rules with their messages", () => {
    const html = renderToStaticMarkup(
      <RulesPanel
        mlScore={0.4}
        finalScore={0.95}
        rules={{
          score_delta: 0.55,
          pinned_label: "phishing",
          hits: [{ rule_id: "AT_TRICK", delta: 0.55, message: "ใช้ @ ซ่อนปลายทาง" }],
        }}
      />
    );
    expect(html).toContain("AT_TRICK");
    expect(html).toContain("ใช้ @ ซ่อนปลายทาง");
    expect(html).toContain("ทำไมระบบจึงตัดสินแบบนี้");
  });

  it("renders an empty state when no rules fire", () => {
    const html = renderToStaticMarkup(
      <RulesPanel mlScore={0.1} finalScore={0.1} rules={{ hits: [] }} />
    );
    expect(html).toContain("ไม่มีกฎ");
  });
});

describe("Skeletons", () => {
  it("render without throwing", () => {
    expect(renderToStaticMarkup(<Skeleton className="h-4 w-4" />)).toContain("animate-pulse");
    expect(renderToStaticMarkup(<StatCardSkeleton />)).toContain("animate-pulse");
    expect(renderToStaticMarkup(<CardSkeleton rows={3} />)).toContain("animate-pulse");
  });
});
