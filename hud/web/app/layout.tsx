import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Assistant HUD",
  description: "Configurable assistant HUD",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
