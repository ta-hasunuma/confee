import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SuggestedPrompts } from "../SuggestedPrompts";
import type { SuggestedPrompt } from "../../types";

const mockPrompts: SuggestedPrompt[] = [
  { id: "1", label: "TypeScriptのカンファレンス", prompt: "TypeScriptのカンファレンスある？", category: "keyword" },
  { id: "2", label: "おすすめの勉強会", prompt: "おすすめの勉強会ある？", category: "vague" },
];

describe("SuggestedPrompts", () => {
  it("プロンプトがチップ形式で表示される", () => {
    render(<SuggestedPrompts prompts={mockPrompts} onSelect={vi.fn()} disabled={false} visible={true} />);
    expect(screen.getByText("TypeScriptのカンファレンス")).toBeInTheDocument();
    expect(screen.getByText("おすすめの勉強会")).toBeInTheDocument();
  });

  it("クリックでonSelectが呼ばれる", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<SuggestedPrompts prompts={mockPrompts} onSelect={onSelect} disabled={false} visible={true} />);

    await user.click(screen.getByText("TypeScriptのカンファレンス"));
    expect(onSelect).toHaveBeenCalledWith("TypeScriptのカンファレンスある？");
  });

  it("visible=falseの場合は表示されない", () => {
    render(<SuggestedPrompts prompts={mockPrompts} onSelect={vi.fn()} disabled={false} visible={false} />);
    expect(screen.queryByText("TypeScriptのカンファレンス")).not.toBeInTheDocument();
  });

  it("disabled=trueの場合はボタンが無効化される", () => {
    render(<SuggestedPrompts prompts={mockPrompts} onSelect={vi.fn()} disabled={true} visible={true} />);
    const buttons = screen.getAllByRole("button");
    buttons.forEach((button) => expect(button).toBeDisabled());
  });
});
