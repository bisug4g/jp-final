import { useEffect, useState, useRef } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { api } from "@/lib/api"
import Layout from "@/components/Layout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Pin, Trash2 } from "lucide-react"

interface Note {
  id: string
  title: string
  content: string
  folder: string | null
  tags: string[]
  pinned: boolean
}

export default function NoteEditor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [note, setNote] = useState<Note | null>(null)
  const [title, setTitle] = useState("")
  const [content, setContent] = useState("")
  const [folder, setFolder] = useState("")
  const [tagInput, setTagInput] = useState("")
  const [tags, setTags] = useState<string[]>([])
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(true)
  const saveTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!id) return
    api.get<{ note: Note }>(`/notes/${id}`).then(({ note: n }) => {
      setNote(n)
      setTitle(n.title)
      setContent(n.content)
      setFolder(n.folder || "")
      setTags(n.tags || [])
    })
  }, [id])

  const scheduleSave = (updates: Partial<Note>) => {
    setSaved(false)
    if (saveTimeout.current) clearTimeout(saveTimeout.current)
    saveTimeout.current = setTimeout(async () => {
      setSaving(true)
      await api.patch(`/notes/${id}`, updates)
      setSaving(false)
      setSaved(true)
    }, 1000)
  }

  const handleTitleChange = (v: string) => {
    setTitle(v)
    scheduleSave({ title: v, content, folder: folder || null, tags })
  }

  const handleContentChange = (v: string) => {
    setContent(v)
    scheduleSave({ title, content: v, folder: folder || null, tags })
  }

  const addTag = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && tagInput.trim()) {
      const newTags = [...tags, tagInput.trim()]
      setTags(newTags)
      setTagInput("")
      scheduleSave({ title, content, folder: folder || null, tags: newTags })
    }
  }

  const removeTag = (tag: string) => {
    const newTags = tags.filter((t) => t !== tag)
    setTags(newTags)
    scheduleSave({ title, content, folder: folder || null, tags: newTags })
  }

  const togglePin = async () => {
    await api.patch(`/notes/${id}`, { pinned: !note?.pinned })
    setNote((n) => n ? { ...n, pinned: !n.pinned } : n)
  }

  const deleteNote = async () => {
    if (!confirm("Delete this note?")) return
    await api.delete(`/notes/${id}`)
    navigate("/notes")
  }

  if (!note) return <Layout><div className="animate-pulse h-8 w-48 bg-muted rounded-lg" /></Layout>

  return (
    <Layout>
      <div className="space-y-4">
        {/* Toolbar */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={() => navigate("/notes")}>
            <ArrowLeft className="h-4 w-4 mr-1" /> Back
          </Button>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">{saving ? "Saving…" : saved ? "Saved" : "Unsaved"}</span>
            <Button variant="ghost" size="icon" onClick={togglePin} title="Pin">
              <Pin className={`h-4 w-4 ${note.pinned ? "text-primary fill-primary" : ""}`} />
            </Button>
            <Button variant="ghost" size="icon" onClick={deleteNote} title="Delete">
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        </div>

        {/* Title */}
        <input
          className="w-full text-2xl font-bold font-serif bg-transparent border-none outline-none placeholder:text-muted-foreground/50"
          placeholder="Untitled"
          value={title}
          onChange={(e) => handleTitleChange(e.target.value)}
        />

        {/* Folder + tags */}
        <div className="flex flex-wrap items-center gap-2">
          <Input
            placeholder="Folder…"
            value={folder}
            onChange={(e) => {
              setFolder(e.target.value)
              scheduleSave({ title, content, folder: e.target.value || null, tags })
            }}
            className="h-7 w-32 text-xs rounded-full"
          />
          <div className="flex flex-wrap gap-1">
            {tags.map((t) => (
              <Badge key={t} variant="secondary" className="text-xs cursor-pointer" onClick={() => removeTag(t)}>
                {t} ×
              </Badge>
            ))}
          </div>
          <Input
            placeholder="Add tag + Enter"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={addTag}
            className="h-7 w-36 text-xs rounded-full"
          />
        </div>

        <div className="border-t" />

        {/* Content */}
        <textarea
          className="w-full min-h-[60vh] bg-transparent border-none outline-none resize-none text-sm leading-relaxed placeholder:text-muted-foreground/40"
          placeholder="Start writing…"
          value={content}
          onChange={(e) => handleContentChange(e.target.value)}
        />
      </div>
    </Layout>
  )
}
