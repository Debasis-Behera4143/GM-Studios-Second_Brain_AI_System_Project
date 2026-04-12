import React, { useState } from "react";
import axios from "axios";

function App() {
  const [note, setNote] = useState("");
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");

  const addNote = async () => {
    try {
      const res = await axios.post("http://127.0.0.1:8000/add_note", {
        content: note,
      });

      alert(res.data.message); // ✅ show success
    } catch (err) {
      console.error(err);
      alert("Error saving note");
    }
  };
  const askQuestion = async () => {
    try {
      const res = await axios.post("http://127.0.0.1:8000/query", {
        query: query,
      });

      console.log(res.data); 

      setResponse(res.data.answer);
    } catch (err) {
      console.error(err);
      alert("Error fetching answer");
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Second Brain MVP</h2>

      <textarea
        placeholder="Write note..."
        onChange={(e) => setNote(e.target.value)}
      />
      <br />
      <button onClick={addNote}>Save Note</button>

      <hr />

      <input
        placeholder="Ask question..."
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={askQuestion}>Ask</button>

      <p>{response}</p>
    </div>
  );
}

export default App;
