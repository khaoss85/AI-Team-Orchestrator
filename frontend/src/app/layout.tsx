// frontend/src/app/layout.tsx

import type { Metadata } from "next";
import "./globals.css";
import { NotificationService } from "@/components/NotificationService";
import LayoutWrapper from "@/components/LayoutWrapper";

export const metadata: Metadata = {
  title: "AI Team Orchestrator",
  description: "Piattaforma per la gestione di team di agenti AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="it">
      <body>
        <NotificationService>
          <LayoutWrapper>
            {children}
          </LayoutWrapper>
        </NotificationService>
      </body>
    </html>
  );
}