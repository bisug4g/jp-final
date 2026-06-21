import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { AuthProvider, useAuth } from "@/contexts/AuthContext"
import Login from "@/pages/Login"
import Dashboard from "@/pages/Dashboard"
import Notes from "@/pages/Notes"
import NoteEditor from "@/pages/NoteEditor"
import Diary from "@/pages/Diary"
import DiaryWrite from "@/pages/DiaryWrite"
import Goals from "@/pages/Goals"
import Chat from "@/pages/Chat"
import Astro from "@/pages/Astro"
import Tangred from "@/pages/Tangred"
import { ReactNode } from "react"

function PrivateRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="h-6 w-6 rounded-full border-2 border-primary border-t-transparent animate-spin" /></div>
  return user ? <>{children}</> : <Navigate to="/login" replace />
}

function PublicRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return null
  return user ? <Navigate to="/dashboard" replace /> : <>{children}</>
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/notes" element={<PrivateRoute><Notes /></PrivateRoute>} />
          <Route path="/notes/new" element={<PrivateRoute><NoteEditor /></PrivateRoute>} />
          <Route path="/notes/:id" element={<PrivateRoute><NoteEditor /></PrivateRoute>} />
          <Route path="/diary" element={<PrivateRoute><Diary /></PrivateRoute>} />
          <Route path="/diary/write" element={<PrivateRoute><DiaryWrite /></PrivateRoute>} />
          <Route path="/diary/:id" element={<PrivateRoute><Diary /></PrivateRoute>} />
          <Route path="/goals" element={<PrivateRoute><Goals /></PrivateRoute>} />
          <Route path="/chat" element={<PrivateRoute><Chat /></PrivateRoute>} />
          <Route path="/astro" element={<PrivateRoute><Astro /></PrivateRoute>} />
          <Route path="/tangred" element={<PrivateRoute><Tangred /></PrivateRoute>} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
