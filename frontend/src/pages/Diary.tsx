import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { api } from "@/lib/api"
import Layout from "@/components/Layout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BookOpen, Plus, Smile, Frown, Meh, ChevronLeft, ChevronRight } from "lucide-react"

interface DiaryEntry {
  id: string
  date: string
  content: string
  mood: string | null
  tags: string[]
}

const MOOD_ICON: Record<string, React.ReactNode> = {
  great: <Smile className="h-4 w-4 text-green-500" />,
  good: <Smile className="h-4 w-4 text-emerald-400" />,
  okay: <Meh className="h-4 w-4 text-yellow-400" />,
  bad: <Frown className="h-4 w-4 text-orange-400" />,
  terrible: <Frown className="h-4 w-4 text-red-500" />,
}

export default function Diary() {
  const navigate = useNavigate()
  const now = new Date()
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear] = useState(now.getFullYear())
  const [entries, setEntries] = useState<DiaryEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.get<{ entries: DiaryEntry[] }>(`/diary?month=${month}&year=${year}`)
      .then((d) => { setEntries(d.entries); setLoading(false) })
      .catch(() => setLoading(false))
  }, [month, year])

  const prevMonth = () => {
    if (month === 1) { setMonth(12); setYear((y) => y - 1) }
    else setMonth((m) => m - 1)
  }

  const nextMonth = () => {
    if (month === 12) { setMonth(1); setYear((y) => y + 1) }
    else setMonth((m) => m + 1)
  }

  const monthLabel = new Date(year, month - 1).toLocaleDateString("en-IN", { month: "long", year: "numeric" })

  return (
    <Layout>
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold font-serif">Diary</h1>
          <Button onClick={() => navigate("/diary/write")}>
            <Plus className="h-4 w-4 mr-2" /> Write Today
          </Button>
        </div>

        {/* Month nav */}
        <div className="flex items-center gap-3">
          <Button variant="outline" size="icon" onClick={prevMonth}><ChevronLeft className="h-4 w-4" /></Button>
          <span className="text-sm font-medium min-w-[160px] text-center">{monthLabel}</span>
          <Button variant="outline" size="icon" onClick={nextMonth}><ChevronRight className="h-4 w-4" /></Button>
        </div>

        {/* Entries */}
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-24 rounded-xl bg-muted animate-pulse" />)}
          </div>
        ) : entries.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <BookOpen className="h-10 w-10 mx-auto mb-3 opacity-30" />
            <p>No entries this month.</p>
            <Button variant="link" onClick={() => navigate("/diary/write")}>Write your first entry →</Button>
          </div>
        ) : (
          <div className="space-y-3">
            {entries.map((entry) => (
              <Card
                key={entry.id}
                onClick={() => navigate(`/diary/${entry.id}`)}
                className="cursor-pointer hover:shadow-md transition-shadow"
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">
                      {new Date(entry.date).toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" })}
                    </CardTitle>
                    {entry.mood && MOOD_ICON[entry.mood]}
                  </div>
                  <CardDescription className="line-clamp-2 text-xs">
                    {entry.content?.substring(0, 150)}
                  </CardDescription>
                </CardHeader>
                {entry.tags?.length > 0 && (
                  <CardContent className="pt-0">
                    <div className="flex flex-wrap gap-1">
                      {entry.tags.map((t) => <Badge key={t} variant="outline" className="text-[10px]">{t}</Badge>)}
                    </div>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  )
}
