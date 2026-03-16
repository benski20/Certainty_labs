import { PlatformSidebar } from '@/components/platform-sidebar'

export default function PlatformLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen bg-white">
      <PlatformSidebar />
      <main className="flex-1">{children}</main>
    </div>
  )
}
