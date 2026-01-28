"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";

export default function Home() {
  const [username, setUsername] = useState("");
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim()) {
      router.push(`/${username.replace("@", "")}`);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8 bg-gradient-to-b from-gray-900 to-black">
      <div className="max-w-2xl w-full text-center">
        <h1 className="text-5xl font-bold text-white mb-4">
          X Score Optimizer
        </h1>
        <p className="text-xl text-gray-400 mb-4">
          Predict and optimize your post scores based on X algorithm
        </p>

        <p className="text-gray-300 mb-8">
          Free to use, no sign-up required
        </p>

        <form onSubmit={handleSubmit} className="flex gap-4 justify-center">
          <div className="relative flex-1 max-w-md">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">
              @
            </span>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter X handle"
              className="w-full pl-10 pr-4 py-4 rounded-xl bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
            />
          </div>
          <button
            type="submit"
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors text-lg"
          >
            Analyze
          </button>
        </form>
      </div>

      {/* Powered by Sela Network */}
      <a
        href="https://selanetwork.io"
        target="_blank"
        rel="noopener noreferrer"
        className="absolute bottom-8 flex items-center gap-3 text-gray-500 hover:text-gray-300 transition-colors"
      >
        <span className="text-lg">Powered by</span>
        <Image
          src="https://avatars.githubusercontent.com/u/177708063?s=200&v=4"
          alt="Sela Network"
          width={30}
          height={30}
          className="rounded-full"
        />
        <span className="text-lg font-medium">Sela Network</span>
      </a>
    </main>
  );
}
