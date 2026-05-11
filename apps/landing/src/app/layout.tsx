import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });

export const metadata: Metadata = {
  title: "Michi 道 | Omnichannel Forecasting Solutions",
  description: "Scale your business with AI-powered omnichannel forecasting. Integrate Shopify, Amazon, and WooCommerce seamlessly.",
  keywords: ["Forecasting", "Omnichannel", "Shopify", "Amazon", "WooCommerce", "AI", "Michi"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className="scroll-smooth">
      <body className={`${inter.variable} ${outfit.variable} font-inter`}>
        <div className="fixed inset-0 -z-10 bg-michi-dark" />
        <div className="fixed inset-0 -z-10 hero-gradient opacity-50" />
        {children}
      </body>
    </html>
  );
}
