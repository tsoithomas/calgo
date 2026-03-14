import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import App from "./App";

describe("App error banner", () => {
  beforeEach(() => {
    // Mock fetch to always reject — simulates network failure
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("Network error"))));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders a non-blocking error banner when fetch fails", async () => {
    render(<App />);

    // Banner should appear once polling hooks surface errors
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    // Banner contains the error message
    expect(screen.getByRole("alert")).toHaveTextContent("Network error");
  });

  it("still renders all main panels when fetch fails", async () => {
    render(<App />);

    // Wait for error banner to confirm hooks have settled
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    // All panels should render their empty-state messages
    expect(screen.getByText(/no price data available/i)).toBeInTheDocument();
    expect(screen.getByText(/no signals available/i)).toBeInTheDocument();
    expect(screen.getByText(/no trades available/i)).toBeInTheDocument();
    expect(screen.getByText(/no portfolio data available/i)).toBeInTheDocument();
    expect(screen.getByText(/no logs available/i)).toBeInTheDocument();
  });

  it("dismisses the error banner when X is clicked", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    const dismissBtn = screen.getByRole("button", { name: /dismiss error/i });
    fireEvent.click(dismissBtn);

    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });
  });
});
