import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect } from "vitest";
import "@testing-library/jest-dom";
import App from "./App";
import * as api from "./api/assistantApi";

describe("App", () => {
  it("sends a typed question and renders the assistant reply", async () => {
    vi.spyOn(api, "askAssistant").mockResolvedValue({
      answer: "The library opens at 8am.",
      language: "en-US",
      verified: true,
      sources: [{ title: "Library Hours", page: 1, snippet: "Opens 8am." }],
      conversation_id: "abc123",
    });
    vi.spyOn(api, "speak").mockResolvedValue(null);

    render(<App />);
    fireEvent.change(screen.getByLabelText(/type your question/i), {
      target: { value: "When does the library open?" },
    });
    fireEvent.click(screen.getByText(/send/i));

    await waitFor(() =>
      expect(screen.getByText(/library opens at 8am/i)).toBeInTheDocument()
    );
  });

  it("handles Hinglish partner finder voice query and displays matched student cards", async () => {
    vi.spyOn(api, "askAssistant").mockResolvedValue({
      answer: "मैंने 2 बेहतरीन मैच ढूंढे हैं!",
      language: "hi-IN",
      verified: true,
      sources: [],
      conversation_id: "partner-123",
      partner_data: {
        intent: { is_partner_intent: true, user_skills: ["AI/ML", "React"], member_count: 2 },
        project_type: "Hackathon",
        matches: [
          {
            profile: {
              id: "std-101",
              name: "Namya Jain",
              department: "Computer Science",
              year: "3rd Year",
              my_skills: ["UI/UX Design", "Figma"],
              looking_for_skills: ["AI/ML"],
              availability: "Weekend Hackathon",
              rating: 4.9,
              bio: "Passionate UI/UX designer",
            },
            match_score: 96,
            match_reasons: ["Possesses requested skills: UI/UX"],
          },
        ],
      },
    });
    vi.spyOn(api, "speak").mockResolvedValue(null);

    render(<App />);
    fireEvent.change(screen.getByLabelText(/type your question/i), {
      target: { value: "Mujhe AI ML aur React aata hai. Mujhe 2 members chahiye hackathon project ke liye." },
    });
    fireEvent.click(screen.getByText(/send/i));

    await waitFor(() => {
      expect(screen.getByText(/Namya Jain/i)).toBeInTheDocument();
      expect(screen.getByText(/96% Skill Match/i)).toBeInTheDocument();
    });
  });
});
