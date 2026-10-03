import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { VocabExplorer } from "./VocabExplorer";
import type { Session } from "../lib/types";

function makeDate(daysAgo: number): string {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  return d.toISOString().slice(0, 10);
}

const base: Omit<Session, "date" | "vocab_review_misses"> = {
  id: "1", name: "Test", type: "conversation", mistakes: [],
};

test("shows no-words message when all sessions have empty vocab_review_misses", () => {
  render(<VocabExplorer sessions={[{ ...base, date: makeDate(1), vocab_review_misses: [] }]} />);
  expect(screen.getByText("No words found.")).toBeInTheDocument();
});

test("deduplicates the same word across sessions and sums count", () => {
  const sessions: Session[] = [
    { ...base, id: "1", date: makeDate(2), vocab_review_misses: ["der Hund"] },
    { ...base, id: "2", date: makeDate(1), vocab_review_misses: ["der Hund"] },
  ];
  render(<VocabExplorer sessions={sessions} />);
  expect(screen.getByText("×2")).toBeInTheDocument();
});

test("tracks lastSeen as the most recent session date", () => {
  const recent = makeDate(1);
  const sessions: Session[] = [
    { ...base, id: "1", date: makeDate(10), vocab_review_misses: ["der Hund"] },
    { ...base, id: "2", date: recent,       vocab_review_misses: ["der Hund"] },
  ];
  render(<VocabExplorer sessions={sessions} />);
  expect(screen.getByText(recent)).toBeInTheDocument();
});

test("sorts words by count descending", () => {
  const sessions: Session[] = [
    { ...base, id: "1", date: makeDate(1), vocab_review_misses: ["die Katze"] },
    { ...base, id: "2", date: makeDate(2), vocab_review_misses: ["der Hund", "die Katze"] },
    { ...base, id: "3", date: makeDate(3), vocab_review_misses: ["der Hund", "die Katze"] },
  ];
  render(<VocabExplorer sessions={sessions} />);
  const allWords = screen.getAllByText(/der Hund|die Katze/);
  expect(allWords[0].textContent).toBe("die Katze"); // count 3 before count 2
});

test("filters words by search term (case-insensitive)", async () => {
  const sessions: Session[] = [
    { ...base, id: "1", date: makeDate(1), vocab_review_misses: ["der Hund", "die Katze"] },
  ];
  render(<VocabExplorer sessions={sessions} />);
  await userEvent.type(screen.getByPlaceholderText("Search words..."), "hund");
  expect(screen.getByText("der Hund")).toBeInTheDocument();
  expect(screen.queryByText("die Katze")).not.toBeInTheDocument();
});

test("marks word as stale (orange) when lastSeen is older than 30 days", () => {
  const sessions: Session[] = [
    { ...base, id: "1", date: makeDate(35), vocab_review_misses: ["der Hund"] },
  ];
  render(<VocabExplorer sessions={sessions} />);
  expect(screen.getByText("der Hund")).toHaveStyle("color: #FB923C");
});

test("does not mark recent word as stale", () => {
  const sessions: Session[] = [
    { ...base, id: "1", date: makeDate(5), vocab_review_misses: ["der Hund"] },
  ];
  render(<VocabExplorer sessions={sessions} />);
  expect(screen.getByText("der Hund")).toHaveStyle("color: #F8FAFC");
});

test("footer shows total unique word count", () => {
  const sessions: Session[] = [
    { ...base, id: "1", date: makeDate(1), vocab_review_misses: ["der Hund", "die Katze"] },
  ];
  render(<VocabExplorer sessions={sessions} />);
  expect(screen.getByText(/2 unique words/)).toBeInTheDocument();
});
