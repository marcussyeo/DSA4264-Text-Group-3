import { ChatClient } from "@/components/chat-client";

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">DSA4264 Text Group 3</p>
        <h1>NUS Job and Module Retrieval Chat</h1>
        <p className="hero-copy">
          Query by module code or degree to retrieve relevant job ads, or query by job title and
          description to retrieve relevant NUS modules.
        </p>
      </section>
      <ChatClient />
    </main>
  );
}
