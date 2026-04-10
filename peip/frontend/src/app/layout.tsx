import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PEIP Dashboard",
  description: "Real-time AI-powered technical risk insights and codebase analytics.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col font-sans">{children}</body>
    </html>
  );
}
