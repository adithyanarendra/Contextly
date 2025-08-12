import { useState } from "react";
import axios from "axios";

export default function AskForm({ onNewQA }) {
    const [question, setQuestion] = useState("");

    const handleAsk = async () => {
        const res = await axios.post("http://localhost:8000/ask/", { question });
        onNewQA(question, res.data.answer);
        setQuestion("");
    };

    return (
        <div className="bg-white p-4 rounded shadow mb-4 flex gap-2">
            <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question..."
                className="flex-1 border p-2 rounded"
            />
            <button
                className="px-4 py-2 bg-blue-500 text-white rounded"
                onClick={handleAsk}
                disabled={!question.trim()}
            >
                Ask
            </button>
        </div>
    );
}
