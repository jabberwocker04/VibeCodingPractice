import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "자동매매봇 대시보드",
  description: "Namoo Overseas Bot — 실시간 모니터링 & 제어",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
