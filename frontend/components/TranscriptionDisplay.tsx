export default function TranscriptionDisplay({
  partial,
  finalText,
}: {
  partial: string;
  finalText: string;
}) {
  return (
    <div className="mt-6">
      <h2 className="font-bold text-xl">Live Transcription</h2>
      <p className="text-gray-700 bg-gray-100 p-3 rounded mt-2 h-24 overflow-y-auto">
        {partial}
      </p>

      <h2 className="font-bold text-xl mt-6">Final Transcript</h2>
      <p className="text-gray-800 bg-white p-3 rounded border h-40 overflow-y-auto">
        {finalText}
      </p>
    </div>
  );
}