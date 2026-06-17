import { FormEvent, useEffect, useMemo, useState } from "react";

type User = { id: number; email: string };
type Doc = {
  id: number;
  owner_id: number;
  title: string;
  doc_type: string;
  content: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

type ChatRow = { role: "assistant" | "user"; content: string };

const API_BASE = "/api";

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const [authError, setAuthError] = useState("");

  const [chatInput, setChatInput] = useState("");
  const [chatRows, setChatRows] = useState<ChatRow[]>([]);
  const [knownFields, setKnownFields] = useState<Record<string, unknown>>({});
  const [docType, setDocType] = useState("Mutual NDA");

  const [docs, setDocs] = useState<Doc[]>([]);
  const [docTitle, setDocTitle] = useState("Untitled Document");
  const [loading, setLoading] = useState(false);

  const isReadyToSave = useMemo(
    () => Object.keys(knownFields).length > 0 && docTitle.trim().length > 0,
    [knownFields, docTitle]
  );

  useEffect(() => {
    void fetchMe();
    void fetchGreeting();
  }, []);

  async function fetchGreeting() {
    const res = await fetch(`${API_BASE}/chat/greeting`);
    const data = await res.json();
    setChatRows([{ role: "assistant", content: data.message }]);
  }

  async function fetchMe() {
    const res = await fetch(`${API_BASE}/auth/me`, { credentials: "include" });
    if (!res.ok) return;
    const data = (await res.json()) as User;
    setUser(data);
    await fetchDocs();
  }

  async function fetchDocs() {
    const res = await fetch(`${API_BASE}/documents`, { credentials: "include" });
    if (!res.ok) return;
    const data = (await res.json()) as Doc[];
    setDocs(data);
  }

  async function onAuthSubmit(event: FormEvent) {
    event.preventDefault();
    setAuthError("");
    const endpoint = isSignup ? "signup" : "signin";
    const res = await fetch(`${API_BASE}/auth/${endpoint}`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      setAuthError("Authentication failed");
      return;
    }

    const data = (await res.json()) as User;
    setUser(data);
    setEmail("");
    setPassword("");
    await fetchDocs();
  }

  async function signOut() {
    await fetch(`${API_BASE}/auth/signout`, {
      method: "POST",
      credentials: "include",
    });
    setUser(null);
    setDocs([]);
  }

  async function onChatSubmit(event: FormEvent) {
    event.preventDefault();
    if (!chatInput.trim()) return;

    const userRow: ChatRow = { role: "user", content: chatInput };
    setChatRows((prev) => [...prev, userRow]);
    const sendText = chatInput;
    setChatInput("");
    setLoading(true);

    const payload = {
      message: sendText,
      conversation: [...chatRows, userRow],
      doc_type: docType,
      known_fields: knownFields,
    };

    try {
      const res = await fetch(`${API_BASE}/chat/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      setChatRows((prev) => [...prev, { role: "assistant", content: data.reply }]);
      setKnownFields(data.extracted_fields || {});
    } finally {
      setLoading(false);
    }
  }

  async function saveDocument() {
    if (!isReadyToSave) return;
    const payload = {
      title: docTitle,
      doc_type: docType,
      content: knownFields,
    };
    const res = await fetch(`${API_BASE}/documents`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      await fetchDocs();
    }
  }

  async function loadDocument(doc: Doc) {
    setDocTitle(doc.title);
    setDocType(doc.doc_type);
    setKnownFields(doc.content);
    setChatRows((prev) => [
      ...prev,
      { role: "assistant", content: `Loaded ${doc.title}. Continue by adding more details.` },
    ]);
  }

  async function deleteDocument(id: number) {
    await fetch(`${API_BASE}/documents/${id}`, {
      method: "DELETE",
      credentials: "include",
    });
    await fetchDocs();
  }

  return (
    <div className="page">
      <header className="hero">
        <h1>Prelegal</h1>
        <p>AI-assisted legal draft intake with secure document persistence.</p>
      </header>

      <main className="layout">
        <section className="card auth">
          {!user ? (
            <form onSubmit={onAuthSubmit}>
              <h2>{isSignup ? "Create account" : "Sign in"}</h2>
              <label>Email</label>
              <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
              <label>Password</label>
              <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
              {authError ? <p className="error">{authError}</p> : null}
              <button type="submit">{isSignup ? "Sign up" : "Sign in"}</button>
              <button className="ghost" type="button" onClick={() => setIsSignup((v) => !v)}>
                {isSignup ? "Already have an account" : "Need an account?"}
              </button>
            </form>
          ) : (
            <div>
              <h2>{user.email}</h2>
              <p>Authenticated</p>
              <button onClick={signOut}>Sign out</button>
            </div>
          )}
        </section>

        <section className="card chat">
          <div className="toolbar">
            <input
              value={docTitle}
              onChange={(e) => setDocTitle(e.target.value)}
              placeholder="Document title"
            />
            <select value={docType} onChange={(e) => setDocType(e.target.value)}>
              {[
                "Mutual NDA",
                "Cloud Service Agreement",
                "Pilot Agreement",
                "Design Partner Agreement",
                "SLA",
                "Professional Services Agreement",
                "Partnership Agreement",
                "Software License Agreement",
                "DPA",
                "BAA",
                "AI Addendum",
              ].map((type) => (
                <option key={type}>{type}</option>
              ))}
            </select>
          </div>

          <div className="chatlog">
            {chatRows.map((row, i) => (
              <p className={row.role} key={`${row.role}-${i}`}>
                {row.content}
              </p>
            ))}
          </div>

          <form className="chatform" onSubmit={onChatSubmit}>
            <input
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Tell me what you need in the agreement"
            />
            <button disabled={loading} type="submit">
              {loading ? "Sending..." : "Send"}
            </button>
          </form>
        </section>

        <section className="card docs">
          <h2>My Documents</h2>
          <button disabled={!user || !isReadyToSave} onClick={saveDocument}>
            Save Current
          </button>
          {!user ? <p>Sign in to persist documents.</p> : null}
          <ul>
            {docs.map((doc) => (
              <li key={doc.id}>
                <span>{doc.title}</span>
                <div>
                  <button className="ghost" onClick={() => loadDocument(doc)}>
                    Load
                  </button>
                  <button className="ghost" onClick={() => deleteDocument(doc.id)}>
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
          <h3>Extracted Fields</h3>
          <pre>{JSON.stringify(knownFields, null, 2)}</pre>
        </section>
      </main>
    </div>
  );
}
