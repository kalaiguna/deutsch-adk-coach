import { useState, useRef, useCallback } from "react";

type CallStatus = "idle" | "connecting" | "live" | "ended" | "error";

const TOKEN_ENDPOINT = import.meta.env.VITE_TOKEN_ENDPOINT as string;

const COACH_SYSTEM_PROMPT = `You are a German B2 conversation coach conducting a real-time spoken practice call.
Speak entirely in German unless the learner asks for an English explanation.
After each learner turn, give a brief spoken B2-Umformulierung if they made a notable error, then continue the conversation naturally.
Keep responses concise (2-4 sentences) to maintain a flowing call rhythm.
Start by greeting the learner warmly and asking what they'd like to talk about today.`;

export function GespraechPanel() {
  const [status, setStatus]         = useState<CallStatus>("idle");
  const [transcript, setTranscript] = useState<{ role: "user" | "coach"; text: string }[]>([]);
  const [errorMsg, setErrorMsg]     = useState("");

  const wsRef          = useRef<WebSocket | null>(null);
  // Two separate AudioContexts: mic input at 16kHz, speaker output at 24kHz
  const micCtxRef      = useRef<AudioContext | null>(null);
  const outCtxRef      = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const streamRef      = useRef<MediaStream | null>(null);
  const outputQueueRef = useRef<Float32Array[]>([]);
  const playingRef     = useRef(false);

  const appendTranscript = (role: "user" | "coach", text: string) =>
    setTranscript(prev => [...prev, { role, text }]);

  const getOrCreateOutCtx = useCallback((): AudioContext => {
    if (!outCtxRef.current || outCtxRef.current.state === "closed") {
      outCtxRef.current = new AudioContext({ sampleRate: 24000 });
    }
    return outCtxRef.current;
  }, []);

  const playNextChunk = useCallback(() => {
    if (playingRef.current || outputQueueRef.current.length === 0) return;
    playingRef.current = true;
    const ctx   = getOrCreateOutCtx();
    const chunk = outputQueueRef.current.shift()!;
    const buf   = ctx.createBuffer(1, chunk.length, 24000);
    buf.getChannelData(0).set(chunk);
    const src   = ctx.createBufferSource();
    src.buffer  = buf;
    src.connect(ctx.destination);
    src.onended = () => { playingRef.current = false; playNextChunk(); };
    src.start();
  }, [getOrCreateOutCtx]);

  const startCall = useCallback(async () => {
    setStatus("connecting");
    setTranscript([]);
    setErrorMsg("");

    try {
      // 1. Fetch ephemeral token from Cloud Function
      const tokenRes = await fetch(TOKEN_ENDPOINT, { method: "POST" });
      if (!tokenRes.ok) throw new Error(`Token endpoint returned ${tokenRes.status}`);
      const { token, model } = await tokenRes.json();

      // 2. Set up 16kHz mic AudioContext + worklet
      const micCtx = new AudioContext({ sampleRate: 16000 });
      micCtxRef.current = micCtx;
      await micCtx.audioWorklet.addModule("/worklet/pcm-processor.js");

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const source  = micCtx.createMediaStreamSource(stream);
      const worklet = new AudioWorkletNode(micCtx, "pcm-processor");
      workletNodeRef.current = worklet;
      source.connect(worklet);

      // 3. Open Gemini Live WebSocket
      const wsUrl = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key=${token}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      // 4. Wire mic → server immediately (before any server message arrives)
      worklet.port.onmessage = (e: MessageEvent<Float32Array>) => {
        if (ws.readyState !== WebSocket.OPEN) return;
        const float32 = e.data;
        const int16   = new Int16Array(float32.length);
        for (let i = 0; i < float32.length; i++)
          int16[i] = Math.max(-32768, Math.min(32767, Math.round(float32[i] * 32767)));
        const bytes = new Uint8Array(int16.buffer);
        const b64   = btoa(String.fromCharCode(...bytes));
        ws.send(JSON.stringify({
          realtime_input: { media_chunks: [{ mime_type: "audio/pcm;rate=16000", data: b64 }] },
        }));
      };

      ws.onopen = () => {
        ws.send(JSON.stringify({
          setup: {
            model,
            generation_config: { response_modalities: ["AUDIO", "TEXT"] },
            system_instruction: { parts: [{ text: COACH_SYSTEM_PROMPT }] },
          },
        }));
      };

      ws.onmessage = async (ev) => {
        const msg = JSON.parse(typeof ev.data === "string" ? ev.data : await (ev.data as Blob).text());

        if (msg.setupComplete) setStatus("live");

        const parts = msg.serverContent?.modelTurn?.parts ?? [];
        for (const p of parts) {
          if (p.text) appendTranscript("coach", p.text);
          if (p.inlineData?.mimeType?.startsWith("audio/pcm")) {
            const raw   = atob(p.inlineData.data as string);
            const int16 = new Int16Array(raw.length / 2);
            for (let i = 0; i < int16.length; i++)
              int16[i] = raw.charCodeAt(i * 2) | (raw.charCodeAt(i * 2 + 1) << 8);
            const float32 = new Float32Array(int16.length);
            for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768;
            outputQueueRef.current.push(float32);
            playNextChunk();
          }
        }
      };

      ws.onerror = () => { setStatus("error"); setErrorMsg("WebSocket error."); };
      // Unconditional: avoids stale-closure bug where `status` is always "connecting"
      ws.onclose = () => setStatus(prev => prev === "live" || prev === "connecting" ? "ended" : prev);

    } catch (e) {
      setStatus("error");
      setErrorMsg(String(e));
    }
  }, [playNextChunk]);

  const endCall = useCallback(() => {
    wsRef.current?.close();
    streamRef.current?.getTracks().forEach(t => t.stop());
    micCtxRef.current?.close();
    outCtxRef.current?.close();
    workletNodeRef.current?.disconnect();
    outputQueueRef.current = [];
    playingRef.current = false;
    setStatus("ended");
  }, []);

  const statusLabel: Record<CallStatus, string> = {
    idle: "Ready", connecting: "Connecting...", live: "Live", ended: "Call ended", error: "Error",
  };
  const statusColor: Record<CallStatus, string> = {
    idle: "#94A3B8", connecting: "#FB923C", live: "#34D399", ended: "#64748B", error: "#F87171",
  };

  return (
    <div>
      <h3 style={{ fontSize: 15, fontWeight: 600, color: "#F8FAFC", marginBottom: 4 }}>Gespräch — Live Call</h3>
      <p style={{ fontSize: 12, color: "#64748B", marginBottom: 16 }}>
        Real-time spoken B2 practice powered by Gemini Live API.
      </p>

      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 10, height: 10, borderRadius: "50%",
            background: statusColor[status],
            boxShadow: status === "live" ? `0 0 8px ${statusColor[status]}` : "none",
          }} />
          <span style={{ fontSize: 13, color: statusColor[status] }}>{statusLabel[status]}</span>
        </div>

        {(status === "idle" || status === "ended" || status === "error") && (
          <button onClick={startCall} style={{
            padding: "8px 20px", borderRadius: 8, border: "none", cursor: "pointer",
            background: "#8B5CF6", color: "#fff", fontSize: 14, fontWeight: 600,
          }}>
            📞 Start Call
          </button>
        )}
        {status === "live" && (
          <button onClick={endCall} style={{
            padding: "8px 20px", borderRadius: 8, border: "none", cursor: "pointer",
            background: "#F87171", color: "#fff", fontSize: 14, fontWeight: 600,
          }}>
            ✕ End Call
          </button>
        )}
        {status === "connecting" && (
          <button disabled style={{
            padding: "8px 20px", borderRadius: 8, border: "none",
            background: "#334155", color: "#64748B", fontSize: 14,
          }}>Connecting...</button>
        )}
      </div>

      {errorMsg && (
        <div style={{ background: "#3B1212", border: "1px solid #F87171", borderRadius: 8, padding: "10px 14px", marginBottom: 12, fontSize: 13, color: "#F87171" }}>
          {errorMsg}
        </div>
      )}

      {!TOKEN_ENDPOINT && (
        <div style={{ background: "#1C1400", border: "1px solid #D97706", borderRadius: 8, padding: "10px 14px", marginBottom: 12, fontSize: 12, color: "#FDE68A" }}>
          VITE_TOKEN_ENDPOINT not set. Deploy the Cloud Function and add it to .env.local.
        </div>
      )}

      <div style={{ background: "#1E293B", borderRadius: 10, padding: 16, minHeight: 200, maxHeight: 400, overflowY: "auto" }}>
        {transcript.length === 0 && (
          <div style={{ color: "#475569", fontSize: 13 }}>Transcript will appear here during the call.</div>
        )}
        {transcript.map((t, i) => (
          <div key={i} style={{ marginBottom: 10 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: t.role === "coach" ? "#8B5CF6" : "#34D399", marginRight: 8 }}>
              {t.role === "coach" ? "🤖 Coach" : "👤 You"}
            </span>
            <span style={{ fontSize: 13, color: "#CBD5E1" }}>{t.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
