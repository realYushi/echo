export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <p className="text-lg font-medium text-gray-400">No recommendations yet</p>
      <p className="mt-2 text-sm text-gray-400">
        Start chatting to discover products tailored to your taste
      </p>
    </div>
  );
}
