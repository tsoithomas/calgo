import { renderHook, act, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { usePolling } from "./usePolling";

describe("usePolling", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("calls fetchFn immediately on mount", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ value: 42 });
    renderHook(() => usePolling(fetchFn, 5000));

    await act(async () => {
      await Promise.resolve();
    });

    expect(fetchFn).toHaveBeenCalledTimes(1);
  });

  it("sets data and clears error on successful fetch", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ value: 42 });
    const { result } = renderHook(() => usePolling(fetchFn, 5000));

    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.data).toEqual({ value: 42 });
    expect(result.current.error).toBeNull();
  });

  it("loading is true initially and false after first fetch", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ value: 1 });
    const { result } = renderHook(() => usePolling(fetchFn, 5000));

    expect(result.current.loading).toBe(true);

    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.loading).toBe(false);
  });

  it("calls fetchFn again after interval elapses", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ value: 1 });
    renderHook(() => usePolling(fetchFn, 5000));

    await act(async () => {
      await Promise.resolve();
    });

    expect(fetchFn).toHaveBeenCalledTimes(1);

    await act(async () => {
      vi.advanceTimersByTime(5000);
      await Promise.resolve();
    });

    expect(fetchFn).toHaveBeenCalledTimes(2);
  });

  it("sets error on fetch failure without stopping the interval", async () => {
    const err = new Error("network error");
    const fetchFn = vi.fn().mockRejectedValue(err);
    const { result } = renderHook(() => usePolling(fetchFn, 5000));

    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.error).toBe(err);
    expect(result.current.data).toBeNull();

    // Interval should still fire
    await act(async () => {
      vi.advanceTimersByTime(5000);
      await Promise.resolve();
    });

    expect(fetchFn).toHaveBeenCalledTimes(2);
  });

  it("clears error when a subsequent fetch succeeds", async () => {
    const err = new Error("fail");
    const fetchFn = vi
      .fn()
      .mockRejectedValueOnce(err)
      .mockResolvedValue({ value: 99 });

    const { result } = renderHook(() => usePolling(fetchFn, 5000));

    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.error).toBe(err);

    await act(async () => {
      vi.advanceTimersByTime(5000);
      await Promise.resolve();
    });

    expect(result.current.error).toBeNull();
    expect(result.current.data).toEqual({ value: 99 });
  });

  it("clears the interval on unmount", async () => {
    const fetchFn = vi.fn().mockResolvedValue({});
    const { unmount } = renderHook(() => usePolling(fetchFn, 5000));

    await act(async () => {
      await Promise.resolve();
    });

    unmount();

    await act(async () => {
      vi.advanceTimersByTime(10000);
      await Promise.resolve();
    });

    // Only the initial call, no more after unmount
    expect(fetchFn).toHaveBeenCalledTimes(1);
  });

  it("uses default interval of 10000ms", async () => {
    const fetchFn = vi.fn().mockResolvedValue({});
    renderHook(() => usePolling(fetchFn));

    await act(async () => {
      await Promise.resolve();
    });

    expect(fetchFn).toHaveBeenCalledTimes(1);

    await act(async () => {
      vi.advanceTimersByTime(9999);
      await Promise.resolve();
    });

    expect(fetchFn).toHaveBeenCalledTimes(1);

    await act(async () => {
      vi.advanceTimersByTime(1);
      await Promise.resolve();
    });

    expect(fetchFn).toHaveBeenCalledTimes(2);
  });
});
