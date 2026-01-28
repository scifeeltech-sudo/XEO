import { Metadata } from "next";

interface LayoutProps {
  children: React.ReactNode;
  params: Promise<{ username: string }>;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ username: string }>;
}): Promise<Metadata> {
  const { username } = await params;
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";

  return {
    title: `@${username} - X Score Optimizer`,
    description: `Profile analysis for @${username} on X Score Optimizer`,
    openGraph: {
      title: `@${username} - Profile Analysis`,
      description: `Check out @${username}'s X profile analysis and optimization scores`,
      images: [
        {
          url: `${baseUrl}/api/og/${username}`,
          width: 1200,
          height: 630,
          alt: `@${username} Profile Analysis`,
        },
      ],
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: `@${username} - Profile Analysis`,
      description: `Check out @${username}'s X profile analysis and optimization scores`,
      images: [`${baseUrl}/api/og/${username}`],
    },
  };
}

export default function UsernameLayout({ children }: LayoutProps) {
  return <>{children}</>;
}
