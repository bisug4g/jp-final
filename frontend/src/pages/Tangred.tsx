import Layout from "@/components/Layout"
import { Wand2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function Tangred() {
  return (
    <Layout>
      <div className="space-y-5">
        <h1 className="text-2xl font-bold font-serif">Tangred</h1>
        <Card className="bg-gradient-to-br from-[#8B0000] via-[#DC143C] to-black border-0 text-white">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Wand2 className="h-5 w-5" /> Wardrobe AI
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-white/80 text-sm">
              Agentic wardrobe analysis, style sessions, and Tan Studio are coming here.
            </p>
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
