import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MedVoice AI | The Future of Clinical Operations",
  description: "Enterprise-grade clinical coordination platform with sub-second neural intake and ultra-low latency inference. Built for modern medical facilities.",
  keywords: ["Medical AI", "Clinical Intake", "Neural Scheduling", "Healthcare Automation", "HIPAA Compliant AI"],
  authors: [{ name: "MedVoice AI" }],
  openGraph: {
    title: "MedVoice AI - Neural Clinical Intelligence",
    description: "Orchestrate your medical facility with sub-second voice intelligence.",
    type: "website",
  },
};

import { AuthProvider } from "./context/AuthContext";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} ${outfit.variable} antialiased`}
      >
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
