import { useState, useEffect } from "react";
import { collection, query, orderBy, where, getDocs } from "firebase/firestore";
import { db } from "../lib/firebase";
import type { Session } from "../lib/types";

const USER_ID = import.meta.env.VITE_FIRESTORE_USER_ID || "default_user";

export function useSessions(maxDays = 90) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - maxDays);
    const cutoffStr = cutoff.toISOString().slice(0, 10);

    (async () => {
      try {
        const q = query(
          collection(db, "users", USER_ID, "sessions"),
          where("date", ">=", cutoffStr),
          orderBy("date", "desc"),
        );
        const snap = await getDocs(q);
        const docs: Session[] = snap.docs.map(d => ({ id: d.id, ...d.data() } as Session));
        if (mounted) setSessions(docs);
      } catch (e) {
        if (mounted) setError(String(e));
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => { mounted = false; };
  }, [maxDays]);

  return { sessions, loading, error };
}
