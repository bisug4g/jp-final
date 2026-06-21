import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Sparkles, RefreshCw } from "lucide-react"

interface Screen {
  id: number
  title: string
  prompt: string
  status: "READY" | "PROCESSING" | "ERROR"
  created_at: string
}

interface TangredStudioProps {
  projectId: number
  projectTitle: string
  screens: Screen[]
  generateUrl: string
}

export default function TangredStudio({ projectTitle, screens, generateUrl }: TangredStudioProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">{projectTitle}</h2>
          <p className="text-sm text-muted-foreground">{screens.length} screen{screens.length !== 1 ? "s" : ""}</p>
        </div>
        <Button asChild>
          <a href={generateUrl}>
            <Sparkles className="mr-2 h-4 w-4" />
            Generate Screen
          </a>
        </Button>
      </div>

      <Separator />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {screens.map((screen) => (
          <Card key={screen.id} className="group hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-base line-clamp-1">{screen.title}</CardTitle>
                <Badge
                  variant={
                    screen.status === "READY"
                      ? "default"
                      : screen.status === "PROCESSING"
                      ? "secondary"
                      : "destructive"
                  }
                >
                  {screen.status === "PROCESSING" && (
                    <RefreshCw className="mr-1 h-3 w-3 animate-spin" />
                  )}
                  {screen.status}
                </Badge>
              </div>
              <CardDescription className="line-clamp-2 text-xs">{screen.prompt}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                {new Date(screen.created_at).toLocaleDateString("en-IN", {
                  day: "numeric",
                  month: "short",
                  year: "numeric",
                })}
              </p>
            </CardContent>
          </Card>
        ))}

        {screens.length === 0 && (
          <div className="col-span-full flex flex-col items-center justify-center py-12 text-center">
            <Sparkles className="mb-3 h-8 w-8 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">No screens yet. Generate your first one!</p>
          </div>
        )}
      </div>
    </div>
  )
}
