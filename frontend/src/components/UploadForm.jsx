import axios from "axios";

export default function UploadForm({ files, onUpload, onRemove }) {
    const handleFiles = async (e) => {
        const selected = Array.from(e.target.files);
        for (let file of selected) {
            const formData = new FormData();
            formData.append("file", file);
            await axios.post("http://localhost:8000/upload/", formData, {
                headers: { "Content-Type": "multipart/form-data" }
            });
        }
        onUpload(selected);
    };

    return (
        <div className="bg-white p-4 rounded shadow mb-4">
            <input
                type="file"
                accept=".pdf,.doc,.docx,.txt"
                multiple
                onChange={handleFiles}
                className="mb-2"
            />
            <ul>
                {files.map(f => (
                    <li key={f.name} className="flex justify-between items-center border-b py-1">
                        <span>{f.name}</span>
                        <button className="text-red-500" onClick={() => onRemove(f.name)}>Remove</button>
                    </li>
                ))}
            </ul>
        </div>
    );
}
