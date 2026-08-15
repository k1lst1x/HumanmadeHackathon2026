import "./styles.css";

type ApiStatus = {
  backend: string;
};

function App() {
  const status: ApiStatus = { backend: "ready to connect" };

  return (
    <main className="shell">
      <section className="workspace">
        <p className="eyebrow">Zero Human Company Hackathon</p>
        <h1>Agent-run company prototype</h1>
        <p className="summary">
          Frontend and backend are split cleanly so the product idea, Terac feedback loop,
          and agent workflows can be developed in parallel.
        </p>
        <div className="status">
          <span>Backend</span>
          <strong>{status.backend}</strong>
        </div>
      </section>
    </main>
  );
}

export default App;
