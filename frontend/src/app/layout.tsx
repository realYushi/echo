import type { Metadata } from "next";
import { Fraunces, Space_Grotesk } from "next/font/google";
import "@/styles/globals.css";

const sans = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-sans",
});

const serif = Fraunces({
  subsets: ["latin"],
  variable: "--font-serif",
});

export const metadata: Metadata = {
  title: "Echo — Product Discovery",
  description: "Discover products through guided conversation",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${sans.variable} ${serif.variable} min-h-screen bg-[color:var(--surface)] text-[color:var(--ink)] antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
