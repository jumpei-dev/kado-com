export default function Skeleton({ rows = 6 }: { rows?: number }) {
  return (
    <ul className="grid gap-3">
      {Array.from({ length: rows }).map((_, i) => (
        <li key={i} className="rounded-2xl bg-slate-200/60 animate-pulse h-16" />
      ))}
    </ul>
  );
}