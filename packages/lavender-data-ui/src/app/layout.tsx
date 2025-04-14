'use client';

import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/app-sidebar';
import { Toaster } from '@/components/ui/sonner';
import '../styles/globals.css';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </head>
      <body className="w-full min-h-screen">
        <SidebarProvider>
          <AppSidebar />
          <div className="w-full bg-muted">
            {children}
            <Toaster />
          </div>
        </SidebarProvider>
      </body>
    </html>
  );
}
