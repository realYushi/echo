import Link from "next/link";

export default function HomePage() {
  return (
    <main className="relative flex min-h-screen items-center overflow-hidden px-6 py-12">
      <div className="pointer-events-none absolute inset-0 opacity-80">
        <div className="absolute top-[-5rem] left-[-7rem] h-64 w-64 rounded-full bg-[color:var(--accent)]/12 blur-3xl" />
        <div className="absolute right-[-4rem] bottom-[-8rem] h-72 w-72 rounded-full bg-[#b9824a]/12 blur-3xl" />
      </div>
      <section className="relative mx-auto flex w-full max-w-5xl flex-col gap-10 rounded-[40px] border border-[color:var(--line)] bg-white/65 px-8 py-10 shadow-[0_32px_90px_rgba(29,42,34,0.12)] backdrop-blur-sm lg:flex-row lg:items-end lg:justify-between lg:px-12 lg:py-14">
        <div className="max-w-2xl">
          <p className="text-[11px] tracking-[0.22em] text-[color:var(--muted)] uppercase">
            Echo
          </p>
          <h1 className="mt-4 text-5xl leading-none text-[color:var(--ink)] sm:text-6xl">
            Discovery that starts with instinct.
          </h1>
          <p className="mt-6 max-w-xl text-base leading-7 text-[color:var(--muted)] sm:text-lg">
            React to materials, moods, and product ideas in plain language. Echo
            turns that conversation into a live recommendation feed for
            architecture and home projects.
          </p>
        </div>
        <div className="flex flex-col gap-3">
          <Link
            href="/discover"
            className="inline-flex items-center justify-center rounded-[20px] bg-[color:var(--ink)] px-8 py-4 text-base font-medium text-white shadow-[0_20px_40px_rgba(29,42,34,0.18)] transition hover:bg-[color:var(--ink)]/92"
          >
            Enter Discovery Studio
          </Link>
          <p className="text-sm text-[color:var(--muted)]">
            Best on desktop, responsive on mobile.
          </p>
        </div>
      </section>
    </main>
  );
}
