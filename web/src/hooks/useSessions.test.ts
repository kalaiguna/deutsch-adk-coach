import { renderHook, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";

vi.mock("../lib/firebase", () => ({ db: {} }));

const mockGetDocs    = vi.fn();
const mockCollection = vi.fn(() => "col-ref");
const mockWhere      = vi.fn(() => "where-ref");
const mockOrderBy    = vi.fn(() => "orderby-ref");
const mockQuery      = vi.fn(() => "query-ref");

vi.mock("firebase/firestore", () => ({
  collection: (...a: unknown[]) => mockCollection(...a),
  where:      (...a: unknown[]) => mockWhere(...a),
  orderBy:    (...a: unknown[]) => mockOrderBy(...a),
  query:      (...a: unknown[]) => mockQuery(...a),
  getDocs:    (...a: unknown[]) => mockGetDocs(...a),
}));

// Import after mocks are registered
const { useSessions } = await import("./useSessions");

const fakeDoc = {
  id: "s1",
  data: () => ({ date: "2026-10-01", name: "T", type: "conversation", mistakes: [], vocab_review_misses: [] }),
};

beforeEach(() => vi.clearAllMocks());

describe("useSessions", () => {
  it("returns sessions on successful Firestore fetch", async () => {
    mockGetDocs.mockResolvedValueOnce({ docs: [fakeDoc] });
    const { result } = renderHook(() => useSessions());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.sessions).toHaveLength(1);
    expect(result.current.sessions[0].type).toBe("conversation");
    expect(result.current.error).toBeNull();
  });

  it("sets error string on Firestore failure", async () => {
    mockGetDocs.mockRejectedValueOnce(new Error("network error"));
    const { result } = renderHook(() => useSessions());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toMatch(/network error/);
    expect(result.current.sessions).toHaveLength(0);
  });

  it("starts with loading=true and sessions=[]", () => {
    mockGetDocs.mockReturnValueOnce(new Promise(() => {})); // never resolves
    const { result } = renderHook(() => useSessions());
    expect(result.current.loading).toBe(true);
    expect(result.current.sessions).toHaveLength(0);
  });

  it("passes the correct date cutoff to the where clause", async () => {
    mockGetDocs.mockResolvedValueOnce({ docs: [] });
    const { result } = renderHook(() => useSessions(30));
    await waitFor(() => expect(result.current.loading).toBe(false));

    const [field, op, cutoff] = mockWhere.mock.calls[0];
    expect(field).toBe("date");
    expect(op).toBe(">=");

    const expected = new Date();
    expected.setDate(expected.getDate() - 30);
    expect(cutoff).toBe(expected.toISOString().slice(0, 10));
  });

  it("re-fetches when maxDays changes", async () => {
    mockGetDocs.mockResolvedValue({ docs: [] });
    const { rerender } = renderHook(({ days }) => useSessions(days), { initialProps: { days: 30 } });
    await waitFor(() => expect(mockGetDocs).toHaveBeenCalledTimes(1));
    rerender({ days: 90 });
    await waitFor(() => expect(mockGetDocs).toHaveBeenCalledTimes(2));
  });
});
