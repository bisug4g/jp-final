import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { api } from "@/lib/api"
import Layout from "@/components/Layout"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Smile, Frown, Meh } from "lucide-react"

const MOODS = [
  { value: "great", label: "Great", icon: <Smile className="h-5 w-5 text-green-500" /> },
  { value: "good", label: "Good", icon: <Smile className="h-5 w-5 text-emerald-400" /> },
  { value: "okay", label: "Okay", icon: <Meh className="h-5 w-5 text-yellow-400" /> },
  { value: "bad", label: "Bad", icon: <Frown className="h-5 w-5 text-orange-400" /> },
  { value: "terrible", label: "Terrible", icon: <Frown className="h-5 w-5 text-red-500" /> },
]

export default function DiaryWrite() {
  const navigate = useNavigate()
  const today = new Date().toISOString().split("T")[0]
  const [content, setContent] = useState("")
  const [mood, setMood] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")

  const save = async () => {
    if (!content.trim()) return
    setSaving(true)
    try {
      const { id } = await api.post<{ id: string }>("/diary", { content, mood: mood || null, date: today })
      navigate(`/diary/${id}`)
    } catch (e: unknown) {
      if (e instanceof Error && e.message.includes("already exists")) {
        setError("You've already written an entry for today.")
      } else {
        setError("Failed to save. Please try again.")
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto space-y-5">
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={() => navigate("/diary")}>
            <ArrowLeft className="h-4 w-4 mr-1" /> Back
          </Button>
          <Button onClick={save} disabled={saving || !content.trim()}>
            {saving ? "Saving…" : "Save Entry"}
          </Button>
        </div>

        <div>
          <p className="text-sm text-muted-foreground">
            {new Date(today).toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
          </p>
          <h1 className="text-2xl font-bold font-serif mt-1">How was your day?</h1>
        </div>

        {/* Mood selector */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-2">Mood</p>
          <div className="flex gap-2">
            {MOODS.map((m) => (
              <button
                key={m.value}
                onClick={() => setMood(m.value === mood ? "" : m.value)}
                className={`flex flex-col items-center gap-1 p-3 rounded-xl border text-xs font-medium transition-colors ${mood === m.value ? "bg-primary/10 border-primary" : "hover:bg-accent"}`}
              >
                {m.icon}
                {m.label}
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="border-t" />

        <textarea
          autoFocus
          className="w-full min-h-[50vh] bg-transparent border-none outline-none resize-none text-sm leading-relaxed placeholder:text-muted-foreground/40"
          placeholder="Write freely. This is your space…"
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
      </div>
    </Layout>
  )
}
