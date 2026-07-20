import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Space_Grotesk } from "next/font/google";

import "./globals.css";
import { TopBar } from "@/components/layout/TopBar";
import { Providers } from "@/providers";

// Display face (headings + big numbers), used with restraint.
const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});
// Body/UI — IBM Plex Sans (engineering/telco heritage, dense-UI legibility).
const plexSans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});
// Data vernacular — IDs, RM, GB, tenure, tokens, cost.
const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "TIME Retention — recontract console",
  description: "Agent console for grounded recontract pitch generation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${plexSans.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="bg-paper text-ink flex min-h-full flex-col">
        <Providers>
          <TopBar />
          {children}
        </Providers>
      </body>
    </html>
  );
}
