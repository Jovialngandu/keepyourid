export default function ProfileTabs({ profiles, activeId, onChange }) {
  return (
    <div
      className="guide-tabs"
      role="tablist"
      aria-label="Profils utilisateurs"
    >
      {profiles.map((item) => (
        <button
          key={item.id}
          type="button"
          role="tab"
          aria-selected={item.id === activeId}
          className={`guide-tab ${item.id === activeId ? "guide-tab-active" : ""}`}
          onClick={() => onChange(item.id)}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
