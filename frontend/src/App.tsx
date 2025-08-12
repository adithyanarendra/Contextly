import { useState } from "react";
import UploadForm from "./components/UploadForm";
import AskForm from "./components/AskForm";
import QAList from "./components/QAList";
import { jsPDF } from "jspdf";

export default function App() {
  const [files, setFiles] = useState([]);
  const [qaList, setQaList] = useState([]);
  const [selectedQA, setSelectedQA] = useState({});

  const handleFileUpload = (newFiles) => {
    setFiles([...files, ...newFiles]);
  };

  const handleRemoveFile = (name) => {
    setFiles(files.filter(f => f.name !== name));
  };

  const handleNewQA = (q, a) => {
    setQaList([...qaList, { question: q, answer: a }]);
  };

  const toggleSelectQA = (index) => {
    setSelectedQA(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const handleDownloadPDF = () => {
    const doc = new jsPDF();
    let y = 10;
    qaList.forEach((qa, idx) => {
      if (selectedQA[idx]) {
        doc.text(`Q: ${qa.question}`, 10, y);
        y += 8;
        doc.text(`A: ${qa.answer}`, 10, y);
        y += 12;
      }
    });
    doc.save("selected-qa.pdf");
  };

  const canDownload = Object.values(selectedQA).some(v => v);

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <h1 className="text-2xl font-bold mb-4">Contextly</h1>

      <UploadForm
        files={files}
        onUpload={handleFileUpload}
        onRemove={handleRemoveFile}
      />

      {files.length > 0 && (
        <>
          <AskForm onNewQA={handleNewQA} />
          <QAList qaList={qaList} selectedQA={selectedQA} toggleSelectQA={toggleSelectQA} />
        </>
      )}

      {canDownload && (
        <button
          className="mt-4 px-4 py-2 bg-green-500 text-white rounded"
          onClick={handleDownloadPDF}
        >
          Download Selected Q&A
        </button>
      )}
    </div>
  );
}
