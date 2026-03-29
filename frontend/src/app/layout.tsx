import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LLM Gateway — LLM-as-a-Service Platform",
  description:
    "Access GPT-4, Llama, and Mistral models via a unified API. Pay per token.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body
        className="antialiased bg-gray-950 text-gray-100 min-h-full"
        style={{ fontFamily: "system-ui, -apple-system, sans-serif" }}
      >
        {children}
      </body>
    </html>
  );
}
