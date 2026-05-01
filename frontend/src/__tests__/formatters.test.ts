import { describe, expect, it } from "vitest";
import { currentMonth, formatCurrency, formatDate, formatMonth } from "../lib/formatters";

describe("formatCurrency", () => {
  it("formats positive amounts with dollar sign", () => {
    expect(formatCurrency(1234.5)).toBe("$1,234.50");
  });

  it("formats negative amounts with leading minus sign", () => {
    expect(formatCurrency(-87.43)).toBe("-$87.43");
  });

  it("formats zero as $0.00", () => {
    expect(formatCurrency(0)).toBe("$0.00");
  });

  it("formats large amounts with thousands separator", () => {
    expect(formatCurrency(3800)).toBe("$3,800.00");
  });
});

describe("formatMonth", () => {
  it("converts YYYY-MM to a human-readable label", () => {
    expect(formatMonth("2025-03")).toBe("March 2025");
  });

  it("handles January correctly", () => {
    expect(formatMonth("2025-01")).toBe("January 2025");
  });

  it("handles December correctly", () => {
    expect(formatMonth("2024-12")).toBe("December 2024");
  });
});

describe("formatDate", () => {
  it("formats an ISO date string into a short locale date", () => {
    const result = formatDate("2025-03-20");
    // Just assert it contains the year and month abbreviation
    expect(result).toContain("2025");
    expect(result).toContain("Mar");
  });
});

describe("currentMonth", () => {
  it("returns a string matching YYYY-MM format", () => {
    const result = currentMonth();
    expect(result).toMatch(/^\d{4}-\d{2}$/);
  });
});
