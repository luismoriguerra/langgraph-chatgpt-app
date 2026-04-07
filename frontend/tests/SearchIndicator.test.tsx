import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import SearchIndicator from "../src/components/SearchIndicator";

describe("SearchIndicator", () => {
  it('renders "Searching the web..." when visible', () => {
    render(<SearchIndicator visible />);
    expect(screen.getByText("Searching the web...")).toBeTruthy();
  });

  it("applies pulsing dot animation to three dots", () => {
    const { container } = render(<SearchIndicator visible />);
    const status = screen.getByRole("status");
    const withAnim = [...status.querySelectorAll("span")].filter((s) =>
      /searchDotPulse/i.test(s.style.animation)
    );
    expect(withAnim.length).toBe(3);
    withAnim.forEach((el) => {
      expect(el.style.animation).toMatch(/searchDotPulse/i);
    });
    expect(container.textContent).toContain("🔍");
  });

  it("accepts a visible boolean prop", () => {
    const { rerender } = render(<SearchIndicator visible={false} />);
    expect(screen.queryByText("Searching the web...")).toBeNull();
    rerender(<SearchIndicator visible />);
    expect(screen.getByText("Searching the web...")).toBeTruthy();
    rerender(<SearchIndicator visible={false} />);
    expect(screen.queryByText("Searching the web...")).toBeNull();
  });

  it("renders nothing when visible is false", () => {
    const { container } = render(<SearchIndicator visible={false} />);
    expect(container.firstChild).toBeNull();
  });
});
