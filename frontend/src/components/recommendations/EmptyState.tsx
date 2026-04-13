interface EmptyStateProps {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-[28px] border border-dashed border-[color:var(--line)] bg-white/55 px-6 py-16 text-center">
      <p className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
        Recommendation Feed
      </p>
      <p className="mt-3 text-2xl text-[color:var(--ink)]">{title}</p>
      <p className="mt-3 max-w-sm text-sm leading-6 text-[color:var(--muted)]">
        {description}
      </p>
    </div>
  );
}
