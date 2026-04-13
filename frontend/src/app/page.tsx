import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6">
      <h1 className="text-4xl font-bold tracking-tight">Echo</h1>
      <p className="text-lg text-gray-600">Discover products that match your taste</p>
      <Link
        href="/discover"
        className="rounded-lg bg-gray-900 px-8 py-3 text-lg font-medium text-white transition-colors hover:bg-gray-800"
      >
        Discover
      </Link>
    </main>
  );
}
