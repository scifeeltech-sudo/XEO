export default function Loading() {
  return (
    <main className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="animate-pulse">
          <div className="h-10 bg-gray-700 rounded w-48 mb-4"></div>
          <div className="h-6 bg-gray-700 rounded w-32 mb-8"></div>

          <div className="bg-gray-800 rounded-2xl p-6 mb-8">
            <div className="h-[350px] bg-gray-700 rounded"></div>
          </div>

          <div className="bg-gray-800 rounded-2xl p-6">
            <div className="h-6 bg-gray-700 rounded w-24 mb-4"></div>
            <div className="space-y-4">
              <div className="h-20 bg-gray-700 rounded"></div>
              <div className="h-20 bg-gray-700 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
