import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "NUS Job and Module Retrieval Chat",
  description: "Chat-style interface for matching NUS modules and degrees to job listings.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
