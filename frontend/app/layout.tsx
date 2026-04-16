import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Second Brain AI",
  description: "Jarvis for personal knowledge",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased min-h-screen flex flex-col bg-slate-50 dark:bg-zinc-950 dark:text-zinc-50">
        <main className="flex-1 w-full max-w-6xl mx-auto p-4 md:p-8">
          {children}
        </main>
      </body>
    </html>
  );
}
