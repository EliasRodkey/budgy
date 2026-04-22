import { describe, expect, it, vi, afterEach } from "vitest";
import { pollJobUntilDone } from "../api/transactions";

// Mock fetch globally — use real timers since intervalMs=0 makes polls synchronous
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

afterEach(() => {
  mockFetch.mockReset();
});

function jobStatus(status: string, rowsImported = 5, errors?: string) {
  return { ok: true, json: async () => ({ jobId: "j", status, rowsImported, rowsUpdated: 0, errors: errors ?? null }) };
}

function confirmOk() {
  return { ok: true, json: async () => ({ jobId: "j", status: "complete", rowsImported: 5, rowsUpdated: 0, errors: null }) };
}

describe("pollJobUntilDone", () => {
  it("resolves when job is already complete", async () => {
    mockFetch
      .mockResolvedValueOnce(jobStatus("complete", 10))
      .mockResolvedValueOnce(confirmOk());

    const result = await pollJobUntilDone("j", 5, 0);
    expect(result.imported).toBe(10);
    expect(result.failed).toHaveLength(0);
  });

  it("polls multiple times before completing", async () => {
    mockFetch
      .mockResolvedValueOnce(jobStatus("pending"))
      .mockResolvedValueOnce(jobStatus("processing"))
      .mockResolvedValueOnce(jobStatus("complete", 7))
      .mockResolvedValueOnce(confirmOk());

    const result = await pollJobUntilDone("j", 10, 0);
    expect(result.imported).toBe(7);
    expect(mockFetch).toHaveBeenCalledTimes(4); // 3 polls + 1 confirm
  });

  it("maps errors string to a failed array entry", async () => {
    mockFetch
      .mockResolvedValueOnce(jobStatus("failed", 0, "CSV parse error"))
      .mockResolvedValueOnce(confirmOk());

    const result = await pollJobUntilDone("j", 5, 0);
    expect(result.imported).toBe(0);
    expect(result.failed).toHaveLength(1);
    expect(result.failed[0].reason).toBe("CSV parse error");
  });

  it("returns empty failed array when no errors", async () => {
    mockFetch
      .mockResolvedValueOnce(jobStatus("complete", 42))
      .mockResolvedValueOnce(confirmOk());

    const result = await pollJobUntilDone("j", 5, 0);
    expect(result.failed).toEqual([]);
  });

  it("throws when max attempts exceeded", async () => {
    mockFetch.mockResolvedValue(jobStatus("pending"));
    await expect(pollJobUntilDone("j", 3, 0)).rejects.toThrow("Import timed out");
    expect(mockFetch).toHaveBeenCalledTimes(3);
  });
});
