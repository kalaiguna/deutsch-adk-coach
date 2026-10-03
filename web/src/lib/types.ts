export interface Mistake {
  category: string;
  original: string;
  correction: string;
}

export interface Session {
  id: string;
  date: string;         // YYYY-MM-DD
  name: string;
  type: "conversation" | "vocab" | "quiz" | "reading" | "listening" | "review";
  mistakes: Mistake[];
  vocab_review_misses: string[];
  source_url?: string;
  notes?: string;
  stats?: Record<string, number>;
}

export type MistakeCategory =
  | "Artikel/Genus"
  | "Kasus"
  | "Wortstellung"
  | "Verbform"
  | "Präposition"
  | "Wortwahl"
  | "Vokabular"
  | "Rechtschreibung"
  | "Komposition"
  | "Anglizismus/False Friend"
  | "Sonstiges";

export const ALL_CATEGORIES: MistakeCategory[] = [
  "Artikel/Genus", "Kasus", "Wortstellung", "Verbform", "Präposition",
  "Wortwahl", "Vokabular", "Rechtschreibung", "Komposition",
  "Anglizismus/False Friend", "Sonstiges",
];
