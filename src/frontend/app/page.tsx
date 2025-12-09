import LandingPage from "@/components/landing-page"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { User } from "lucide-react"

export default function HomePage() {
  return (
    <div>
      <LandingPage />

      <div className="fixed bottom-6 right-6 z-50">
        <Link href="/story-select">
          <Button className="bg-primary text-primary-foreground hover:bg-primary/90 magical-glow flex items-center gap-2">
            <User className="w-4 h-4" />
            Start Adventure
          </Button>
        </Link>
      </div>
    </div>
  )
}
