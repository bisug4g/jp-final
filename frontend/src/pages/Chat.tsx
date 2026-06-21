import { useEffect, useRef, useState } from "react"
import { api } from "@/lib/api"
import Layout from "@/components/Layout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Trash2, Bot, User } from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  createdAt: string
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.get<{ messages: Message[] }>("/chat").then((d) => setMessages(d.messages))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const send = async () => {
    const text = input.trim()
    if (!text || sending) return
    setInput("")
    setSending(true)

    const tempUser: Message = { id: "tmp-user", role: "user", content: text, createdAt: new Date().toISOString() }
    const tempBot: Message = { id: "tmp-bot", role: "assistant", content: "…", createdAt: new Date().toISOString() }
    setMessages((prev) => [...prev, tempUser, tempBot])

    try {
      const { reply, userMessageId, assistantMessageId } = await api.post<{
        reply: string
        userMessageId: string
        assistantMessageId: string
      }>("/chat", { message: text })

      setMessages((prev) =>
        prev.map((m) => {
          if (m.id === "tmp-user") return { ...m, id: userMessageId }
          if (m.id === "tmp-bot") return { ...m, id: assistantMessageId, content: reply }
          return m
        })
      )
    } catch {
      setMessages((prev) => prev.filter((m) => m.id !== "tmp-bot").map((m) => m.id === "tmp-user" ? { ...m, id: "err" } : m))
    } finally {
      setSending(false)
    }
  }

  const clearChat = async () => {
    if (!confirm("Clear all chat history?")) return
    await api.delete("/chat")
    setMessages([])
  }

  return (
    <Layout>
      <div className="flex flex-col h-[calc(100vh-8rem)]">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold font-serif">Ask Jayti</h1>
          {messages.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clearChat} className="text-muted-foreground">
              <Trash2 className="h-4 w-4 mr-1" /> Clear
            </Button>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
              <Bot className="h-12 w-12 mb-3 opacity-30" />
              <p className="text-sm">Hi! I'm your personal AI companion.</p>
              <p className="text-sm">Ask me anything — I'm here to help.</p>
            </div>
          )}
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
              <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${msg.role === "user" ? "bg-primary" : "bg-muted"}`}>
                {msg.role === "user" ? <User className="h-3.5 w-3.5 text-primary-foreground" /> : <Bot className="h-3.5 w-3.5" />}
              </div>
              <div
                className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground rounded-tr-sm"
                    : "bg-muted rounded-tl-sm"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="flex gap-2 mt-4 pt-4 border-t">
          <Input
            placeholder="Message Jayti…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            disabled={sending}
            className="rounded-xl"
          />
          <Button size="icon" onClick={send} disabled={sending || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Layout>
  )
}
