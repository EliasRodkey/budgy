import { describe, it, expect, vi, afterEach } from "vitest";
import { fetchWithRetry } from "../api/utils";
import { planCSV } from "../api/ai";

// ─── fetchWithRetry ───────────────────────────────────────────────────────────

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

// Speed up backoff delays in tests
vi.useFakeTimers();

afterEach(() => {
  mockFetch.mockReset();
  vi.clearAllTimers();
});

function response(status: number, body = {}): Response {
  return { ok: status < 400, status, json: async () => body } as unknown as Response;
}

describe("fetchWithRetry", () => {
  it("returns immediately on success", async () => {
    mockFetch.mockResolvedValueOnce(response(200));
    const res = await fetchWithRetry("/url");
    expect(res.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it("retries on 500 and succeeds on second attempt", async () => {
    mockFetch
      .mockResolvedValueOnce(response(500))
      .mockResolvedValueOnce(response(200));

    const promise = fetchWithRetry("/url");
    await vi.runAllTimersAsync();
    const res = await promise;

    expect(res.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it("does not retry on 400", async () => {
    mockFetch.mockResolvedValueOnce(response(400));
    const res = await fetchWithRetry("/url");
    expect(res.status).toBe(400);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it("retries on network error and succeeds on second attempt", async () => {
    mockFetch
      .mockRejectedValueOnce(new Error("network failure"))
      .mockResolvedValueOnce(response(200));

    const promise = fetchWithRetry("/url");
    await vi.runAllTimersAsync();
    const res = await promise;

    expect(res.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it("throws after exhausting all retries on persistent 500", async () => {
    mockFetch.mockResolvedValue(response(500));

    const promise = fetchWithRetry("/url", undefined, 2);
    await vi.runAllTimersAsync();

    // Third call returns 500 and no more retries remain — returns the 500 response
    const res = await promise;
    expect(res.status).toBe(500);
    expect(mockFetch).toHaveBeenCalledTimes(3); // initial + 2 retries
  });

  it("throws after exhausting all retries on persistent network error", async () => {
    mockFetch.mockRejectedValue(new Error("network failure"));

    const promise = fetchWithRetry("/url", undefined, 2);
    // Attach handler before running timers to prevent an unhandled rejection warning
    const rejectExpect = expect(promise).rejects.toThrow("network failure");
    await vi.runAllTimersAsync();
    await rejectExpect;

    expect(mockFetch).toHaveBeenCalledTimes(3);
  });
});

// ─── planCSV response shape validation ───────────────────────────────────────

const VALID_PLAN = {
  column_map: {},
  category_map: {},
  amount_transform: "signed",
  issues: [],
  unmapped_required_columns: [],
  debit_column: null,
  credit_column: null,
  used_cache: false,
  requires_manual_review: false,
};

// planCSV reads isMock() from the store — keep it in real mode
vi.mock("../store/mockMode", () => ({
  useMockMode: { getState: () => ({ isMockMode: false }) },
}));

describe("planCSV shape validation", () => {
  it("resolves with a valid plan", async () => {
    mockFetch.mockResolvedValueOnce(response(200, VALID_PLAN));
    const plan = await planCSV(new File(["a,b"], "test.csv"));
    expect(plan.column_map).toEqual({});
  });

  it("throws a descriptive error when required fields are missing", async () => {
    const incomplete = { column_map: {}, category_map: {} }; // missing amount_transform, issues, unmapped_required_columns
    mockFetch.mockResolvedValueOnce(response(200, incomplete));
    await expect(planCSV(new File(["a,b"], "test.csv"))).rejects.toThrow("unexpected response");
  });

  it("throws when the response is not ok", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 422, json: async () => ({ detail: "Bad file" }) } as unknown as Response);
    await expect(planCSV(new File(["a,b"], "test.csv"))).rejects.toThrow("Bad file");
  });
});
