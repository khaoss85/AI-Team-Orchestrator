// frontend/src/app/layout.tsx

import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import { NotificationService } from "@/components/NotificationService";


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
          <div className="flex h-screen bg-gray-50">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
              <Header />
              <main className="flex-1 overflow-y-auto p-4 bg-gray-50">
                {children}
              </main>
            </div>
          </div>
        </NotificationService>
      </body>
    </html>
  );
}