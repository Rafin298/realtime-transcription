"use client";

import { useState } from "react";
import AudioRecorder from "@/components/AudioRecorder";
import TranscriptionDisplay from "@/components/TranscriptionDisplay";

export default function Home() {
  const [partial, setPartial] = useState("");
  const [finalText, setFinalText] = useState("");

  return (
    <main className="p-8 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">
        Real-Time Speech-to-Text Transcription
      </h1>

      <AudioRecorder
        onTranscriptionUpdate={(text) => setPartial(text)}
        onFinalTranscript={(text) => setFinalText((prev) => prev + " " + text)}
      />

      <TranscriptionDisplay partial={partial} finalText={finalText} />
    </main>
  );
}