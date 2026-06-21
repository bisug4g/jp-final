import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { api } from "@/lib/api"
import Layout from "@/components/Layout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Plus, Search, Pin, Trash2, FileText } from "lucide-react"

interface Note {
  id: string
  title: string
  content: string
  folder: string | null
  tags: string[]
  pinned: boolean
  updatedAt: string
}

export default function Notes() {
  const navigate = useNavigate()
  const [notes, setNotes] = useState<Note[]>([])
  const [search, setSearch] = useState("")
  const [activeFolder, setActiveFolder] = useState("")
  const [folders, setFolders] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    const params = new URLSearchParams()
    if (search) params.set("search", search)
    if (activeFolder) params.set("folder", activeFolder)
    api.get<{ notes: Note[] }>(`/notes?${params}`).then((d) => {
      setNotes(d.notes)
      setLoading(false)
    })
    api.get<{ folders: string[] }>("/notes/meta/folders").then((d) => setFolders(d.folders))
  }

  useEffect(() => { load() }, [search, activeFolder])

  const createNote = async () => {
    const { id } = await api.post<{ id: string }>("/notes", { title: "Untitled", content: "" })
    navigate(`/notes/${id}`)
  }

  const togglePin = async (note: Note, e: React.MouseEvent) => {
    e.stopPropagation()
    await api.patch(`/notes/${note.id}`, { pinned: !note.pinned })
    load()
  }

  const deleteNote = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm("Delete this note?")) return
    await api.delete(`/notes/${id}`)
    setNotes((prev) => prev.filter((n) => n.id !== id))
  }

  return (
    <Layout>
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold font-serif">Notes</h1>
          <Button onClick={createNote}>
            <Plus className="h-4 w-4 mr-2" /> New Note
          </Button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search notes…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 rounded-xl"
          />
        </div>

        {/* Folders */}
        {folders.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setActiveFolder("")}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${!activeFolder ? "bg-primary text-primary-foreground" : "hover:bg-accent"}`}
            >
              All
            </button>
            {folders.map((f) => (
              <button
                key={f}
                onClick={() => setActiveFolder(f === activeFolder ? "" : f)}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${activeFolder === f ? "bg-primary text-primary-foreground" : "hover:bg-accent"}`}
              >
                {f}
              </button>
            ))}
          </div>
        )}

        {/* Notes grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-32 rounded-xl bg-muted animate-pulse" />
            ))}
          </div>
        ) : notes.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <FileText className="h-10 w-10 mx-auto mb-3 opacity-30" />
            <p>No notes yet. Create your first one!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {notes.map((note) => (
              <Card
                key={note.id}
                onClick={() => navigate(`/notes/${note.id}`)}
                className="cursor-pointer hover:shadow-md transition-shadow group"
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-sm line-clamp-1">{note.title}</CardTitle>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button onClick={(e) => togglePin(note, e)} className="p-1 rounded hover:bg-accent">
                        <Pin className={`h-3.5 w-3.5 ${note.pinned ? "text-primary fill-primary" : "text-muted-foreground"}`} />
                      </button>
                      <button onClick={(e) => deleteNote(note.id, e)} className="p-1 rounded hover:bg-destructive/10">
                        <Trash2 className="h-3.5 w-3.5 text-destructive" />
                      </button>
                    </div>
                  </div>
                  <CardDescription className="line-clamp-2 text-xs">
                    {note.content?.replace(/<[^>]*>/g, "") || "Empty note"}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center justify-between">
                    <div className="flex flex-wrap gap-1">
                      {note.folder && <Badge variant="secondary" className="text-[10px]">{note.folder}</Badge>}
                      {note.tags?.slice(0, 2).map((t) => (
                        <Badge key={t} variant="outline" className="text-[10px]">{t}</Badge>
                      ))}
                    </div>
                    <span className="text-[10px] text-muted-foreground">
                      {new Date(note.updatedAt).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  )
}
