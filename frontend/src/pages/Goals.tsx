import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import Layout from "@/components/Layout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Plus, CheckSquare, Square, Sparkles, Trash2, Target } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"

interface Task {
  id: string
  title: string
  completed: boolean
}

interface Goal {
  id: string
  title: string
  description: string
  deadline: string | null
  category: string
  status: string
  progress: number
  tasks: Task[]
}

function GoalDialog({ open, onClose, onSave }: { open: boolean; onClose: () => void; onSave: (data: Partial<Goal>) => void }) {
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [deadline, setDeadline] = useState("")
  const [category, setCategory] = useState("personal")

  const submit = () => {
    if (!title.trim()) return
    onSave({ title, description, deadline: deadline || null, category })
    setTitle(""); setDescription(""); setDeadline(""); setCategory("personal")
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader><DialogTitle>New Goal</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <Input placeholder="Goal title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <Input placeholder="Description (optional)" value={description} onChange={(e) => setDescription(e.target.value)} />
          <Input type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            {["personal", "career", "health", "learning", "relationships", "financial"].map((c) => (
              <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
            ))}
          </select>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={submit}>Create Goal</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default function Goals() {
  const [goals, setGoals] = useState<Goal[]>([])
  const [loading, setLoading] = useState(true)
  const [showDialog, setShowDialog] = useState(false)
  const [generatingFor, setGeneratingFor] = useState<string | null>(null)
  const [newTaskInputs, setNewTaskInputs] = useState<Record<string, string>>({})

  const load = () => {
    api.get<{ goals: Goal[] }>("/goals").then((d) => { setGoals(d.goals); setLoading(false) })
  }

  useEffect(() => { load() }, [])

  const createGoal = async (data: Partial<Goal>) => {
    await api.post("/goals", data)
    load()
  }

  const toggleTask = async (goalId: string, taskId: string, completed: boolean) => {
    await api.patch(`/goals/${goalId}/tasks/${taskId}`, { completed })
    load()
  }

  const addTask = async (goalId: string) => {
    const title = newTaskInputs[goalId]?.trim()
    if (!title) return
    await api.post(`/goals/${goalId}/tasks`, { title })
    setNewTaskInputs((prev) => ({ ...prev, [goalId]: "" }))
    load()
  }

  const generateTasks = async (goalId: string) => {
    setGeneratingFor(goalId)
    try {
      await api.post(`/goals/${goalId}/generate-tasks`, {})
      load()
    } finally {
      setGeneratingFor(null)
    }
  }

  const deleteGoal = async (id: string) => {
    if (!confirm("Delete this goal and all its tasks?")) return
    await api.delete(`/goals/${id}`)
    setGoals((prev) => prev.filter((g) => g.id !== id))
  }

  return (
    <Layout>
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold font-serif">Goals</h1>
          <Button onClick={() => setShowDialog(true)}><Plus className="h-4 w-4 mr-2" /> New Goal</Button>
        </div>

        <GoalDialog open={showDialog} onClose={() => setShowDialog(false)} onSave={createGoal} />

        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-40 rounded-xl bg-muted animate-pulse" />)}
          </div>
        ) : goals.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <Target className="h-10 w-10 mx-auto mb-3 opacity-30" />
            <p>No goals yet. Set your first one!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {goals.map((goal) => (
              <Card key={goal.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <CardTitle className="text-base">{goal.title}</CardTitle>
                      {goal.description && <CardDescription className="text-xs mt-0.5">{goal.description}</CardDescription>}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant={goal.status === "completed" ? "default" : "secondary"} className="text-[10px]">
                        {goal.status}
                      </Badge>
                      <button onClick={() => deleteGoal(goal.id)} className="p-1 rounded hover:bg-destructive/10">
                        <Trash2 className="h-3.5 w-3.5 text-destructive" />
                      </button>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="mt-2">
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>{goal.tasks.filter((t) => t.completed).length}/{goal.tasks.length} tasks</span>
                      <span>{goal.progress}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                      <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${goal.progress}%` }} />
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-2">
                  {/* Task list */}
                  {goal.tasks.map((task) => (
                    <div
                      key={task.id}
                      onClick={() => toggleTask(goal.id, task.id, !task.completed)}
                      className="flex items-center gap-2.5 cursor-pointer group py-1"
                    >
                      {task.completed
                        ? <CheckSquare className="h-4 w-4 text-primary shrink-0" />
                        : <Square className="h-4 w-4 text-muted-foreground shrink-0" />}
                      <span className={`text-sm ${task.completed ? "line-through text-muted-foreground" : ""}`}>
                        {task.title}
                      </span>
                    </div>
                  ))}

                  {/* Add task */}
                  <div className="flex gap-2 pt-1">
                    <Input
                      placeholder="Add a task…"
                      value={newTaskInputs[goal.id] || ""}
                      onChange={(e) => setNewTaskInputs((prev) => ({ ...prev, [goal.id]: e.target.value }))}
                      onKeyDown={(e) => e.key === "Enter" && addTask(goal.id)}
                      className="h-8 text-xs"
                    />
                    <Button size="sm" variant="outline" onClick={() => addTask(goal.id)} className="h-8 text-xs">Add</Button>
                    {goal.tasks.length === 0 && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => generateTasks(goal.id)}
                        disabled={generatingFor === goal.id}
                        className="h-8 text-xs"
                      >
                        {generatingFor === goal.id ? "…" : <><Sparkles className="h-3 w-3 mr-1" />AI Tasks</>}
                      </Button>
                    )}
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
