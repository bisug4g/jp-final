import { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Heart } from "lucide-react"

const SLIDES = [
  "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=1200",
  "https://images.unsplash.com/photo-1518621736915-f3b1c41bfd00?w=1200",
  "https://images.unsplash.com/photo-1468327768560-75b778cbb551?w=1200",
  "https://images.unsplash.com/photo-1487530811176-3780de880c2d?w=1200",
]

export default function Login() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [slide, setSlide] = useState(0)
  const [time, setTime] = useState(new Date())
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (user) navigate("/dashboard", { replace: true })
  }, [user, navigate])

  useEffect(() => {
    intervalRef.current = setInterval(() => setSlide((s) => (s + 1) % SLIDES.length), 8000)
    const clock = setInterval(() => setTime(new Date()), 1000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
      clearInterval(clock)
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await login(email, password)
      navigate("/dashboard")
    } catch {
      setError("Invalid credentials. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const greeting = () => {
    const h = time.getHours()
    if (h < 12) return "Good morning"
    if (h < 17) return "Good afternoon"
    return "Good evening"
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{
        background:
          "radial-gradient(circle at top left, rgba(251,111,146,0.25), transparent 32%), radial-gradient(circle at bottom right, rgba(255,194,209,0.35), transparent 28%), linear-gradient(160deg,#fff3f6 0%,#ffe6ee 42%,#ffeef3 100%)",
      }}
    >
      <div className="w-full max-w-5xl grid md:grid-cols-[460px_1fr] bg-white/80 backdrop-blur-lg border border-pink-200/25 rounded-[32px] shadow-2xl overflow-hidden">
        {/* Left panel */}
        <section className="p-8 md:p-10 flex flex-col justify-center bg-white/96">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-pink-50 border border-pink-200/50 text-xs font-bold tracking-widest uppercase text-pink-700 mb-5 w-fit">
            <Heart className="h-3 w-3" />
            Personal Companion
          </div>

          <h1 className="text-5xl font-bold font-serif text-gray-900 mb-3">Jayti</h1>
          <p className="text-gray-500 leading-relaxed mb-6">
            A calmer, more intentional place for your notes, diary, goals, astrology, and Tangred wardrobe intelligence.
          </p>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-widest text-pink-700 mb-1.5">
                Email
              </label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                className="rounded-2xl border-pink-200/50 h-12"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-widest text-pink-700 mb-1.5">
                Password
              </label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                className="rounded-2xl border-pink-200/50 h-12"
              />
            </div>
            <Button type="submit" disabled={loading} className="w-full h-11 rounded-2xl text-base font-semibold">
              {loading ? "Signing in…" : "Enter Jayti"}
            </Button>
          </form>

          <p className="mt-4 text-sm text-gray-500 p-3 rounded-xl bg-pink-50/60 border border-pink-100">
            <strong>Private by design:</strong> your writing, planning, and Tangred sessions stay personal.
          </p>

          <div className="mt-4 flex flex-wrap gap-2">
            {["Notes, diary, goals", "Tangred wardrobe AI", "Vedic astrology"].map((t) => (
              <span key={t} className="px-3 py-1 rounded-full bg-white border border-pink-200/50 text-xs text-gray-600 font-medium">
                {t}
              </span>
            ))}
          </div>
        </section>

        {/* Right visual */}
        <aside className="relative min-h-[420px] md:min-h-0 overflow-hidden bg-gray-900">
          {SLIDES.map((src, i) => (
            <div
              key={src}
              className="absolute inset-0 bg-cover bg-center transition-opacity duration-[1800ms]"
              style={{ backgroundImage: `url(${src})`, opacity: i === slide ? 1 : 0 }}
            />
          ))}
          <div
            className="absolute inset-0"
            style={{
              background:
                "linear-gradient(180deg,rgba(28,21,25,0.18),rgba(28,21,25,0.8)),linear-gradient(135deg,rgba(251,111,146,0.38),rgba(28,21,25,0.24))",
            }}
          />
          <div className="relative z-10 h-full p-8 flex flex-col justify-between">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/20 bg-white/8 text-xs font-bold tracking-widest uppercase text-white/90 w-fit">
              ✨ Daily Thought
            </div>
            <div>
              <blockquote className="font-serif text-2xl md:text-3xl leading-snug text-white mb-3">
                "The present moment is the only moment available to us."
              </blockquote>
              <p className="text-white/70 font-serif">— Thich Nhat Hanh</p>
            </div>
            <div className="self-end min-w-[200px] p-4 rounded-2xl bg-white/10 backdrop-blur border border-white/15">
              <p className="text-white/80 text-sm mb-1">{greeting()}</p>
              <p className="text-white font-serif text-4xl leading-none">
                {time.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false })}
              </p>
              <p className="text-white/70 text-sm mt-1">
                {time.toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
              </p>
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}
