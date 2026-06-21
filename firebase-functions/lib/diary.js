const { db } = require("./admin");
const { requireAuth } = require("./authMiddleware");
const express = require("express");

const router = express.Router();
router.use(requireAuth);

// List diary entries (paginated)
router.get("/", async (req, res) => {
  try {
    const { month, year, limit = 30 } = req.query;
    let query = db.collection(`users/${req.user.uid}/diary`).orderBy("date", "desc");

    if (month && year) {
      const start = `${year}-${String(month).padStart(2, "0")}-01`;
      const end = `${year}-${String(month).padStart(2, "0")}-31`;
      query = query.where("date", ">=", start).where("date", "<=", end);
    }

    const snap = await query.limit(Number(limit)).get();
    const entries = snap.docs.map((d) => ({ id: d.id, ...d.data() }));
    res.json({ entries });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Get single entry
router.get("/:id", async (req, res) => {
  try {
    const doc = await db.doc(`users/${req.user.uid}/diary/${req.params.id}`).get();
    if (!doc.exists) return res.status(404).json({ error: "Not found" });
    res.json({ entry: { id: doc.id, ...doc.data() } });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Create entry
router.post("/", async (req, res) => {
  try {
    const { date, content, mood, tags } = req.body;
    const today = date || new Date().toISOString().split("T")[0];
    const now = new Date().toISOString();

    // Check if entry for this date exists
    const existing = await db
      .collection(`users/${req.user.uid}/diary`)
      .where("date", "==", today)
      .limit(1)
      .get();

    if (!existing.empty) {
      return res.status(409).json({ error: "Entry for this date already exists", id: existing.docs[0].id });
    }

    const ref = await db.collection(`users/${req.user.uid}/diary`).add({
      date: today,
      content: content || "",
      mood: mood || null,
      tags: tags || [],
      createdAt: now,
      updatedAt: now,
    });

    // Update activity
    await updateActivity(req.user.uid, today, "diary");

    res.json({ id: ref.id });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Update entry
router.patch("/:id", async (req, res) => {
  try {
    const allowed = ["content", "mood", "tags"];
    const update = {};
    for (const k of allowed) if (req.body[k] !== undefined) update[k] = req.body[k];
    update.updatedAt = new Date().toISOString();
    await db.doc(`users/${req.user.uid}/diary/${req.params.id}`).update(update);
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Delete entry
router.delete("/:id", async (req, res) => {
  try {
    await db.doc(`users/${req.user.uid}/diary/${req.params.id}`).delete();
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Mood trends
router.get("/meta/mood-trends", async (req, res) => {
  try {
    const snap = await db
      .collection(`users/${req.user.uid}/diary`)
      .where("mood", "!=", null)
      .orderBy("mood")
      .orderBy("date", "desc")
      .limit(30)
      .get();

    const entries = snap.docs.map((d) => d.data()).sort((a, b) => a.date.localeCompare(b.date));
    const moodMap = { great: 5, good: 4, okay: 3, bad: 2, terrible: 1 };

    res.json({
      labels: entries.map((e) => e.date.slice(5)),
      data: entries.map((e) => moodMap[e.mood] || 3),
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

async function updateActivity(uid, date, type) {
  const ref = db.doc(`users/${uid}/activity/${date}`);
  const doc = await ref.get();
  const current = doc.exists ? doc.data() : { diary: 0, notes: 0, goals: 0, tasks: 0 };
  current[type] = (current[type] || 0) + 1;
  current.date = date;
  await ref.set(current, { merge: true });
}

module.exports = router;
