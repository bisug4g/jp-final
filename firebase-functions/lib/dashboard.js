const { db } = require("./admin");
const { requireAuth } = require("./authMiddleware");
const { GoogleGenerativeAI } = require("@google/generative-ai");
const express = require("express");

const router = express.Router();
router.use(requireAuth);

// Activity calendar (Feb 6 to today)
router.get("/activity", async (req, res) => {
  try {
    const START = "2026-02-06";
    const today = new Date().toISOString().split("T")[0];

    const snap = await db
      .collection(`users/${req.user.uid}/activity`)
      .where("date", ">=", START)
      .where("date", "<=", today)
      .get();

    const activityMap = {};
    snap.docs.forEach((d) => { activityMap[d.data().date] = d.data(); });

    const calendar = [];
    const cur = new Date(START);
    const end = new Date(today);
    let streak = 0;
    let maxStreak = 0;
    let activeDays = 0;

    while (cur <= end) {
      const dateStr = cur.toISOString().split("T")[0];
      const data = activityMap[dateStr] || {};
      const total = (data.diary || 0) + (data.notes || 0) + (data.goals || 0) + (data.tasks || 0);
      const score = Math.min(100, total * 25);
      const hasActivity = total > 0;

      if (hasActivity) {
        streak++;
        activeDays++;
        maxStreak = Math.max(maxStreak, streak);
      } else {
        streak = 0;
      }

      const weekday = (cur.getDay() + 6) % 7; // Mon=0
      calendar.push({ date: dateStr, day: cur.getDate(), weekday, activity_score: score, has_activity: hasActivity, details: data });

      cur.setDate(cur.getDate() + 1);
    }

    const inactiveDays = calendar.length - activeDays;
    res.json({ calendar, stats: { current_streak: streak, max_streak: maxStreak, active_days: activeDays, inactive_days: inactiveDays } });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Dashboard stats
router.get("/stats", async (req, res) => {
  try {
    const [notesSnap, diarySnap, goalsSnap] = await Promise.all([
      db.collection(`users/${req.user.uid}/notes`).count().get(),
      db.collection(`users/${req.user.uid}/diary`).count().get(),
      db.collection(`users/${req.user.uid}/goals`).get(),
    ]);

    const goals = goalsSnap.docs.map((d) => d.data());
    const activeGoals = goals.filter((g) => g.status === "active").length;

    // Pending tasks across all active goals
    let pendingTasks = 0;
    await Promise.all(
      goalsSnap.docs
        .filter((d) => d.data().status === "active")
        .map(async (d) => {
          const tasks = await d.ref.collection("tasks").where("completed", "==", false).count().get();
          pendingTasks += tasks.data().count;
        })
    );

    // Birthday countdown (Feb 6)
    const now = new Date();
    const nextBirthday = new Date(now.getFullYear(), 1, 6);
    if (nextBirthday < now) nextBirthday.setFullYear(now.getFullYear() + 1);
    const daysUntilBirthday = Math.ceil((nextBirthday - now) / (1000 * 60 * 60 * 24));
    const isBirthday = now.getMonth() === 1 && now.getDate() === 6;

    res.json({
      recent_notes: notesSnap.data().count,
      recent_diary: diarySnap.data().count,
      active_goals: activeGoals,
      pending_tasks: pendingTasks,
      birthday: { days_until: daysUntilBirthday, is_today: isBirthday },
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Daily briefing
router.get("/briefing", async (req, res) => {
  try {
    const today = new Date().toISOString().split("T")[0];
    const cached = await db.doc(`users/${req.user.uid}/briefings/${today}`).get();
    if (cached.exists) return res.json({ briefing: cached.data().content });

    const [notesSnap, diarySnap, goalsSnap] = await Promise.all([
      db.collection(`users/${req.user.uid}/notes`).orderBy("updatedAt", "desc").limit(3).get(),
      db.collection(`users/${req.user.uid}/diary`).orderBy("date", "desc").limit(3).get(),
      db.collection(`users/${req.user.uid}/goals`).where("status", "==", "active").limit(5).get(),
    ]);

    const context = [
      `Recent notes: ${notesSnap.docs.map((d) => d.data().title).join(", ") || "None"}`,
      `Recent diary: ${diarySnap.docs.map((d) => d.data().date).join(", ") || "None"}`,
      `Active goals: ${goalsSnap.docs.map((d) => d.data().title).join(", ") || "None"}`,
    ].join(". ");

    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });
    const result = await model.generateContent(
      `Write a warm, personal 2-sentence daily briefing for Jayti based on: ${context}. Be encouraging and personal.`
    );
    const briefing = result.response.text();

    await db.doc(`users/${req.user.uid}/briefings/${today}`).set({ content: briefing, date: today });
    res.json({ briefing });
  } catch (e) {
    res.status(500).json({ error: "Briefing unavailable" });
  }
});

// Daily thought
router.get("/thought", async (req, res) => {
  try {
    const today = new Date().toISOString().split("T")[0];
    const doc = await db.doc(`daily_thoughts/${today}`).get();
    if (doc.exists) return res.json(doc.data());

    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });
    const result = await model.generateContent(
      `Generate an inspiring, thoughtful quote for today (${today}). Return JSON: {"content": "...", "author": "..."}`
    );
    const text = result.response.text().replace(/```json\n?|\n?```/g, "").trim();
    const thought = JSON.parse(text);
    thought.date = today;

    await db.doc(`daily_thoughts/${today}`).set(thought);
    res.json(thought);
  } catch (e) {
    res.json({ content: "Every day is a new beginning.", author: null });
  }
});

module.exports = router;
