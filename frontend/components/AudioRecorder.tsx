"use client";

import { useState, useRef } from "react";
import { connectWebSocket } from "@/lib/websocket";

export default function AudioRecorder({
  onTranscriptionUpdate,
  onFinalTranscript,
}: {
  onTranscriptionUpdate: (text: string) => void;
  onFinalTranscript: (text: string) => void;
}) {
  const [recording, setRecording] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: "audio/webm;codecs=opus",
    });

    mediaRecorderRef.current = mediaRecorder;

    // connect websocket
    wsRef.current = connectWebSocket(
      (data) => {
        if (data.type === "partial") {
          onTranscriptionUpdate(data.text);
        } else if (data.type === "final") {
          onFinalTranscript(data.text);
        }
      },
      () => console.log("WebSocket closed")
    );

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0 && wsRef.current?.readyState === 1) {
        wsRef.current.send(event.data);
      }
    };

    mediaRecorder.start(250); // send chunks every 250ms
    setRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    wsRef.current?.close();
    setRecording(false);
  };

  return (
    <div className="flex flex-col gap-4">
      {!recording ? (
        <button
          onClick={startRecording}
          className="bg-green-600 text-white px-4 py-2 rounded"
        >
          Start Recording
        </button>
      ) : (
        <button
          onClick={stopRecording}
          className="bg-red-600 text-white px-4 py-2 rounded"
        >
          Stop Recording
        </button>
      )}
    </div>
  );
}