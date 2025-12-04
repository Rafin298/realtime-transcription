"use client";

import { useEffect, useRef, useState } from "react";

export default function Page() {
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  const [isRecording, setIsRecording] = useState(false);
  const [partial, setPartial] = useState("");
  const [finalText, setFinalText] = useState("");

  const finalWordCount = finalText.trim() === "" ? 0 : finalText.trim().split(/\s+/).length;
  
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/transcribe/");
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      console.log("WebSocket opened");
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);

        if (payload.type === "partial") {
          setPartial(payload.partial || "");
        }

        if (payload.type === "final") {
          setFinalText((prev) => (prev ? prev + " " + payload.text : payload.text));
          setPartial("");
        }

        if (payload.type === "error") {
          console.error("Server error:", payload.message);
        }
      } catch (err) {
        console.log("Invalid WS message", err);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket closed");
    };

    wsRef.current = ws;
    return () => ws.close();
  }, []);

  const startRecording = async () => {
    if (!wsRef.current) return;

    wsRef.current.send(JSON.stringify({ command: "start" }));

    setFinalText("");
    setPartial("");

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream, {
      mimeType: "audio/webm;codecs=opus",
    });

    mediaRecorderRef.current = recorder;

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
        e.data.arrayBuffer().then((buf) => wsRef.current!.send(buf));
      }
    };

    recorder.start(250);
    setIsRecording(true);
  };

  const stopRecording = () => {
    if (!wsRef.current) return;

    wsRef.current.send(JSON.stringify({ command: "stop" }));

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }

    setIsRecording(false);
  };

  return (
    <div style={{ padding: 30 }}>
      <h1>Live Transcription</h1>

      <button
        onClick={isRecording ? stopRecording : startRecording}
        style={{
          background: isRecording ? "red" : "green",
          color: "white",
          padding: "8px 16px",
          borderRadius: 4,
          border: "none",
          cursor: "pointer",
        }}
      >
        {isRecording ? "Stop Recording" : "Start Recording"}
      </button>

      <h3>Partial:</h3>
      <div style={{ minHeight: 40, border: "1px solid #ddd", padding: 8 }}>
        {partial}
      </div>

      <h3>Final Transcript:</h3>
      <div style={{ minHeight: 80, border: "1px solid #ddd", padding: 8 }}>
        {finalText}
      </div>

      <p style={{ marginTop: 10, fontSize: 16 }}>
        <strong>Word Count:</strong> {finalWordCount}
      </p>

    </div>
  );
}
