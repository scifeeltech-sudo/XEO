"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { PolishType } from "@/types/api";

interface PolishButtonsProps {
  content: string;
  onPolished: (polishedContent: string) => void;
  disabled?: boolean;
}

const POLISH_OPTIONS: {
  type: PolishType;
  label: string;
  icon: string;
  description: string;
}[] = [
  {
    type: "grammar",
    label: "어조 유지 다듬기",
    icon: "✍️",
    description: "문법 교정, 원본 톤 유지",
  },
  {
    type: "twitter",
    label: "트위터 스타일",
    icon: "🐦",
    description: "캐주얼하고 임팩트 있게",
  },
  {
    type: "280char",
    label: "280자 조정",
    icon: "📏",
    description: "핵심 유지하며 압축",
  },
];

export function PolishButtons({
  content,
  onPolished,
  disabled,
}: PolishButtonsProps) {
  const [polishing, setPolishing] = useState<PolishType | null>(null);

  const handlePolish = async (type: PolishType) => {
    if (!content.trim() || polishing) return;

    setPolishing(type);
    try {
      const result = await api.polishPost({
        content,
        polish_type: type,
      });
      onPolished(result.polished_content);
    } catch (error) {
      console.error("Failed to polish:", error);
    } finally {
      setPolishing(null);
    }
  };

  return (
    <div className="flex flex-wrap gap-2">
      {POLISH_OPTIONS.map((option) => (
        <button
          key={option.type}
          onClick={() => handlePolish(option.type)}
          disabled={disabled || !content.trim() || polishing !== null}
          className={`
            flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
            transition-all duration-200
            ${
              polishing === option.type
                ? "bg-blue-600 text-white"
                : "bg-gray-700 text-gray-300 hover:bg-gray-600"
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
          title={option.description}
        >
          <span>{option.icon}</span>
          <span>{option.label}</span>
          {polishing === option.type && (
            <span className="ml-1 animate-spin">⏳</span>
          )}
        </button>
      ))}
    </div>
  );
}
