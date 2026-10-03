import { render, screen } from "@testing-library/react";
import { ActivityHeatmap } from "./ActivityHeatmap";
import type { Session } from "../lib/types";

function makeDate(daysAgo: number): string {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  return d.toISOString().slice(0, 10);
}

function makeSession(daysAgo: number, type: Session["type"]): Session {
  return { id: `${daysAgo}-${type}`, date: makeDate(daysAgo), name: "Test", type, mistakes: [], vocab_review_misses: [] };
}

test("renders the Activity heading", () => {
  render(<ActivityHeatmap sessions={[]} />);
  expect(screen.getByText("Activity")).toBeInTheDocument();
});

test("renders legend for all session types", () => {
  render(<ActivityHeatmap sessions={[]} />);
  for (const t of ["conversation", "vocab", "quiz", "reading", "listening", "review"]) {
    expect(screen.getByText(t)).toBeInTheDocument();
  }
});

test("cell for a session date carries the type in its title", () => {
  const session = makeSession(2, "conversation");
  const { container } = render(<ActivityHeatmap sessions={[session]} />);
  expect(container.querySelector(`[title="${session.date}: conversation"]`)).not.toBeNull();
});

test("combines types for two sessions on the same date", () => {
  const date = makeDate(3);
  const sessions: Session[] = [
    { id: "a", date, name: "A", type: "conversation", mistakes: [], vocab_review_misses: [] },
    { id: "b", date, name: "B", type: "quiz",         mistakes: [], vocab_review_misses: [] },
  ];
  const { container } = render(<ActivityHeatmap sessions={sessions} />);
  expect(container.querySelector(`[title="${date}: conversation, quiz"]`)).not.toBeNull();
});

test("empty date cells have no type in their title", () => {
  const { container } = render(<ActivityHeatmap sessions={[]} />);
  const withTypes = Array.from(container.querySelectorAll("[title]")).filter(
    el => el.getAttribute("title")?.includes(":"),
  );
  expect(withTypes).toHaveLength(0);
});

test("sessions older than 52 weeks do not appear in the grid", () => {
  const session = makeSession(52 * 7 + 10, "conversation");
  const { container } = render(<ActivityHeatmap sessions={[session]} />);
  expect(container.querySelector(`[title*="${session.date}"]`)).toBeNull();
});
