"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { PostEditor } from "@/components/editor/PostEditor";

export default function ComposePage() {
  const params = useParams();
  const username = params.username as string;

  return (
    <main className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link
            href={`/${username}`}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ← 프로필로 돌아가기
          </Link>
          <h1 className="text-2xl font-bold text-white">포스트 작성</h1>
          <span className="text-gray-500">@{username}</span>
        </div>

        <PostEditor username={username} />
      </div>
    </main>
  );
}
