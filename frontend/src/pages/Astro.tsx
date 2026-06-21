import Layout from "@/components/Layout"
import { Star } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function Astro() {
  return (
    <Layout>
      <div className="space-y-5">
        <h1 className="text-2xl font-bold font-serif">Cosmic Guidance</h1>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star className="h-5 w-5 text-primary" /> Vedic Astrology
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Your Vedic birth chart, planetary positions, and daily cosmic guidance will appear here.
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Birth date: <strong>February 6</strong>
            </p>
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
