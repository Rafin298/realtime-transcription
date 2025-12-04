"use client";

import { useEffect, useRef, useState } from "react";

export default function Page() {
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [partial, setPartial] = useState("");
  const [finalText, setFinalText] = useState("");

  useEffect(() => {
    // create websocket when component mounts
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
        } else if (payload.type === "final") {
          // append final text and clear partial
          setFinalText((p) => (p ? p + " " + payload.text : payload.text));
          setPartial("");
        } else if (payload.type === "error") {
          console.error("Server error:", payload.message);
        }
      } catch (e) {
        console.error("invalid message", e);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket closed");
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

  const startRecording = async () => {
    setFinalText("");
    setPartial("");

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    // Use webm/opus (default in most browsers). MediaRecorder will produce that.
    const options = { mimeType: "audio/webm;codecs=opus" };

    const recorder = new MediaRecorder(stream, options);
    mediaRecorderRef.current = recorder;

    recorder.ondataavailable = (e: BlobEvent) => {
      if (e.data && e.data.size > 0 && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        // Convert blob to arrayBuffer then send binary via websocket
        e.data.arrayBuffer().then((buf) => {
          wsRef.current!.send(buf);
        });
      }
    };

    recorder.onstop = () => {
      // Optionally signal EOF by closing the websocket
      // Or send a special text frame. We'll close ws to finalize.
      // wsRef.current?.close();
      setIsRecording(false);
    };

    // chunk/interval: 250 ms or 500 ms (smaller = lower latency, more messages)
    const timeslice = 250;
    recorder.start(timeslice);
    setIsRecording(true);
  };

  const stopRecording = () => {
    const rec = mediaRecorderRef.current;
    if (rec && rec.state !== "inactive") {
      rec.stop();
      // don't close websocket here if you want to record again; you can keep it open
    }
    setIsRecording(false);
  };

  // return (
  //   <div style={{ padding: 30 }}>
  //     <h1>Live transcription</h1>

  //     <div>
  //       <button onClick={startRecording} disabled={isRecording}>
  //         Start Recording
  //       </button>
  //       <button onClick={stopRecording} disabled={!isRecording} style={{ marginLeft: 10 }}>
  //         Stop Recording
  //       </button>
  //     </div>

  //     <h3>Partial:</h3>
  //     <div style={{ minHeight: 40, border: "1px solid #ddd", padding: 8 }}>{partial}</div>

  //     <h3>Final Transcript:</h3>
  //     <div style={{ minHeight: 80, border: "1px solid #ddd", padding: 8 }}>{finalText}</div>
  //   </div>
  // );
  return (
  <div style={{ padding: 30 }}>
    <h1>Live Transcription</h1>

    <div>
      <button
        onClick={isRecording ? stopRecording : startRecording}
        style={{
          background: isRecording ? "red" : "green",
          color: "white",
          padding: "8px 16px",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
        }}
      >
        {isRecording ? "Stop Recording" : "Start Recording"}
      </button>
    </div>

    <h3>Partial:</h3>
    <div style={{ minHeight: 40, border: "1px solid #ddd", padding: 8 }}>
      {partial}
    </div>

    <h3>Final Transcript:</h3>
    <div style={{ minHeight: 80, border: "1px solid #ddd", padding: 8 }}>
      {finalText}
    </div>
  </div>
);
}