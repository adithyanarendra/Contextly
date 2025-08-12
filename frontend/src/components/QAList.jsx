export default function QAList({ qaList, selectedQA, toggleSelectQA }) {
    return (
        <div className="bg-white p-4 rounded shadow">
            {qaList.map((qa, idx) => (
                <div key={idx} className="flex items-start gap-2 border-b py-2">
                    <input
                        type="checkbox"
                        checked={!!selectedQA[idx]}
                        onChange={() => toggleSelectQA(idx)}
                    />
                    <div>
                        <p><strong>Q:</strong> {qa.question}</p>
                        <p><strong>A:</strong> {qa.answer}</p>
                    </div>
                </div>
            ))}
        </div>
    );
}
