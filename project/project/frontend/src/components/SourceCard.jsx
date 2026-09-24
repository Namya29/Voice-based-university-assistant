export default function SourceCard({ source }) {
  return (
    <a
      className="source-card"
      href={source.url || "#"}
      target={source.url ? "_blank" : "_self"}
      rel="noreferrer"
      onClick={(e) => !source.url && e.preventDefault()}
      aria-disabled={!source.url}
    >
      <div className="source-card__header">
        <span className="source-card__icon">📄</span>
        <div className="source-card__title">{source.title}</div>
      </div>
      {source.page && <div className="source-card__page">Page {source.page} • Official Doc</div>}
      <p className="source-card__snippet">{source.snippet}</p>
    </a>
  );
}

