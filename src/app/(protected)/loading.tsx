export default function Loading() {
  return (
    <div className="space-y-4">
      <div className="h-10 w-56 animate-pulse rounded-2xl bg-white/55 backdrop-blur-xl" />
      <div className="grid gap-4 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="h-28 animate-pulse rounded-[28px] border border-white/70 bg-white/40 backdrop-blur-xl" />
        ))}
      </div>
    </div>
  );
}
