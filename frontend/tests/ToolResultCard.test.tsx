import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import ToolResultCard from "../src/components/ToolResultCard";

describe("ToolResultCard", () => {
  it("renders tool name and input for calculate tool", () => {
    render(
      <ToolResultCard
        toolName="calculate"
        toolInput="125 * 8"
        result="1000"
        status="done"
      />
    );

    expect(screen.getByText("Calculator")).toBeTruthy();
    expect(screen.getByText("125 * 8")).toBeTruthy();
    expect(screen.getByText("1000")).toBeTruthy();
  });

  it("renders web_search tool with correct label", () => {
    render(
      <ToolResultCard
        toolName="web_search"
        toolInput="weather NYC"
        result='[{"title": "NYC Weather"}]'
        status="done"
      />
    );

    expect(screen.getByText("Web Search")).toBeTruthy();
  });

  it("renders calling state with dots", () => {
    render(
      <ToolResultCard
        toolName="calculate"
        toolInput="5 + 3"
        status="calling"
      />
    );

    expect(screen.getByText("Calculator")).toBeTruthy();
    expect(screen.getByText("5 + 3")).toBeTruthy();
    expect(screen.queryByText("Result:")).toBeNull();
  });

  it("renders error state when result starts with Error:", () => {
    render(
      <ToolResultCard
        toolName="calculate"
        toolInput="5 / 0"
        result="Error: division by zero"
        status="error"
      />
    );

    expect(screen.getByText("Error:")).toBeTruthy();
    expect(screen.getByText("division by zero")).toBeTruthy();
  });

  it("sets data-tool-name attribute", () => {
    render(
      <ToolResultCard
        toolName="calculate"
        toolInput="1+1"
        result="2"
        status="done"
      />
    );

    const card = screen.getByRole("status");
    expect(card.getAttribute("data-tool-name")).toBe("calculate");
  });
});
