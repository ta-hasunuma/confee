import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { ChatContainer } from "../ChatContainer";
import * as chatApi from "../../api/chat";
import { ChatApiError } from "../../api/chat";

vi.mock("../../api/chat", async () => {
  const actual = await vi.importActual("../../api/chat");
  return {
    ...actual,
    sendMessage: vi.fn(),
  };
});

const sendMessageMock = vi.mocked(chatApi.sendMessage);

describe("ChatContainer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("おすすめプロンプトは初期状態で表示される", () => {
    render(<ChatContainer sessionKey={0} />);
    expect(screen.getByText("TypeScriptのカンファレンスある？")).toBeInTheDocument();
  });

  it("メッセージ送信後におすすめプロンプトが非表示になる", async () => {
    const user = userEvent.setup();
    sendMessageMock.mockResolvedValueOnce({
      response: "テスト応答",
      session_id: "test-session-id-xxxxxxxx",
    });

    render(<ChatContainer sessionKey={0} />);

    const input = screen.getByPlaceholderText("カンファレンスについて質問してみましょう...");
    await user.type(input, "テスト");
    await user.click(screen.getByText("送信"));

    await waitFor(() => {
      expect(screen.getByText("テスト応答")).toBeInTheDocument();
    });

    expect(screen.queryByText("TypeScriptのカンファレンスある？")).not.toBeInTheDocument();
  });

  it("API接続エラー時にフレンドリーなメッセージを表示する", async () => {
    const user = userEvent.setup();
    sendMessageMock.mockRejectedValueOnce(new TypeError("Failed to fetch"));

    render(<ChatContainer sessionKey={0} />);

    const input = screen.getByPlaceholderText("カンファレンスについて質問してみましょう...");
    await user.type(input, "テスト");
    await user.click(screen.getByText("送信"));

    await waitFor(() => {
      expect(screen.getByText(/サーバーに接続できませんでした/)).toBeInTheDocument();
    });
  });

  it("タイムアウトエラー時に適切なメッセージを表示する", async () => {
    const user = userEvent.setup();
    const abortError = new DOMException("The operation was aborted", "AbortError");
    sendMessageMock.mockRejectedValueOnce(abortError);

    render(<ChatContainer sessionKey={0} />);

    const input = screen.getByPlaceholderText("カンファレンスについて質問してみましょう...");
    await user.type(input, "テスト");
    await user.click(screen.getByText("送信"));

    await waitFor(() => {
      expect(screen.getByText(/応答がタイムアウトしました/)).toBeInTheDocument();
    });
  });

  it("503エラー時にサービス一時利用不可のメッセージを表示する", async () => {
    const user = userEvent.setup();
    sendMessageMock.mockRejectedValueOnce(
      new ChatApiError("Service Unavailable", 503)
    );

    render(<ChatContainer sessionKey={0} />);

    const input = screen.getByPlaceholderText("カンファレンスについて質問してみましょう...");
    await user.type(input, "テスト");
    await user.click(screen.getByText("送信"));

    await waitFor(() => {
      expect(screen.getByText(/サービスが一時的に利用できません/)).toBeInTheDocument();
    });
  });

  it("セッションタイムアウト（408）時に新しいセッションで自動リカバリする", async () => {
    const user = userEvent.setup();
    const generateSessionIdSpy = vi.spyOn(chatApi, "generateSessionId");

    // 1回目: セッションタイムアウト
    sendMessageMock.mockRejectedValueOnce(
      new ChatApiError("Session timeout", 408)
    );

    render(<ChatContainer sessionKey={0} />);

    const input = screen.getByPlaceholderText("カンファレンスについて質問してみましょう...");
    await user.type(input, "テスト");
    await user.click(screen.getByText("送信"));

    await waitFor(() => {
      expect(screen.getByText(/セッションがタイムアウトしました/)).toBeInTheDocument();
    });

    // セッションIDが再生成されたことを確認
    // 初回生成 + タイムアウト時の再生成
    expect(generateSessionIdSpy.mock.calls.length).toBeGreaterThanOrEqual(2);
  });
});
