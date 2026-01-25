"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

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
        <p className="text-xl text-gray-400 mb-12">
          X 알고리즘 기반으로 포스트 스코어를 예측하고 최적화하세요
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
              placeholder="유저네임을 입력하세요"
              className="w-full pl-10 pr-4 py-4 rounded-xl bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
            />
          </div>
          <button
            type="submit"
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors text-lg"
          >
            분석하기
          </button>
        </form>

        <p className="mt-8 text-gray-500 text-sm">
          가입 없이 무료로 바로 사용할 수 있습니다
        </p>
      </div>
    </main>
  );
}
