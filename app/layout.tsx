import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "MOE Curriculum-to-Career Alignment Copilot",
  description:
    "Natural-language chat app for searching MyCareersFuture job ads, relevant NUS courses, and degree-job alignment.",
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
