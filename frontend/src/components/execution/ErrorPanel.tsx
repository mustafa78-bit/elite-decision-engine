interface Props {
  errors: string[];
}

export default function ErrorPanel({ errors }: Props) {
  if (errors.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded p-4">
        <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-2">Errors</h3>
        <p className="text-green-400 text-xs">No errors</p>
      </div>
    );
  }

  return (
    <div className="bg-[var(--bg-elevated)] border border-[var(--accent-red)]/30 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-red-400 mb-2">
        Errors ({errors.length})
      </h3>
      <ul className="space-y-1">
        {errors.map((err, i) => (
          <li key={i} className="text-xs text-red-300">- {err}</li>
        ))}
      </ul>
    </div>
  );
}
