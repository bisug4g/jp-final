const { db } = require("./admin");
const { requireAuth } = require("./authMiddleware");
const { GoogleGenerativeAI } = require("@google/generative-ai");
const express = require("express");

const router = express.Router();
router.use(requireAuth);

const SYSTEM_PROMPT = `You are Jayti's personal AI companion — warm, thoughtful, and supportive.
You know Jayti well: she uses this app for notes, diary, goals, and personal reflection.
Be conversational, caring, and helpful. Keep responses concise unless asked for detail.
Never be overly formal. Use simple, warm language.`;

// Get chat history
router.get("/", async (req, res) => {
  try {
    const snap = await db
      .collection(`users/${req.user.uid}/chat`)
      .orderBy("createdAt", "asc")
      .limitToLast(50)
      .get();
    const messages = snap.docs.map((d) => ({ id: d.id, ...d.data() }));
    res.json({ messages });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Send message (streaming via SSE)
router.post("/", async (req, res) => {
  try {
    const { message } = req.body;
    if (!message?.trim()) return res.status(400).json({ error: "Message required" });

    const now = new Date().toISOString();

    // Save user message
    const userRef = await db.collection(`users/${req.user.uid}/chat`).add({
      role: "user",
      content: message,
      createdAt: now,
    });

    // Build history for context
    const histSnap = await db
      .collection(`users/${req.user.uid}/chat`)
      .orderBy("createdAt", "asc")
      .limitToLast(20)
      .get();

    const history = histSnap.docs
      .slice(0, -1) // exclude the message we just saved
      .map((d) => ({
        role: d.data().role === "user" ? "user" : "model",
        parts: [{ text: d.data().content }],
      }));

    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({
      model: "gemini-2.0-flash",
      systemInstruction: SYSTEM_PROMPT,
    });

    const chat = model.startChat({ history });
    const result = await chat.sendMessage(message);
    const reply = result.response.text();

    // Save assistant message
    const assistantRef = await db.collection(`users/${req.user.uid}/chat`).add({
      role: "assistant",
      content: reply,
      createdAt: new Date().toISOString(),
    });

    res.json({
      userMessageId: userRef.id,
      assistantMessageId: assistantRef.id,
      reply,
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Clear chat history
router.delete("/", async (req, res) => {
  try {
    const snap = await db.collection(`users/${req.user.uid}/chat`).get();
    const batch = db.batch();
    snap.forEach((d) => batch.delete(d.ref));
    await batch.commit();
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

module.exports = router;
