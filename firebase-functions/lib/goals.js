const { db } = require("./admin");
const { requireAuth } = require("./authMiddleware");
const { GoogleGenerativeAI } = require("@google/generative-ai");
const express = require("express");

const router = express.Router();
router.use(requireAuth);

// List goals
router.get("/", async (req, res) => {
  try {
    const { status } = req.query;
    let query = db.collection(`users/${req.user.uid}/goals`).orderBy("createdAt", "desc");
    if (status) query = query.where("status", "==", status);
    const snap = await query.limit(50).get();

    const goals = await Promise.all(
      snap.docs.map(async (d) => {
        const tasks = await d.ref.collection("tasks").orderBy("createdAt").get();
        return {
          id: d.id,
          ...d.data(),
          tasks: tasks.docs.map((t) => ({ id: t.id, ...t.data() })),
        };
      })
    );

    res.json({ goals });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Get single goal
router.get("/:id", async (req, res) => {
  try {
    const doc = await db.doc(`users/${req.user.uid}/goals/${req.params.id}`).get();
    if (!doc.exists) return res.status(404).json({ error: "Not found" });
    const tasks = await doc.ref.collection("tasks").orderBy("createdAt").get();
    res.json({
      goal: {
        id: doc.id,
        ...doc.data(),
        tasks: tasks.docs.map((t) => ({ id: t.id, ...t.data() })),
      },
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Create goal
router.post("/", async (req, res) => {
  try {
    const { title, description, deadline, category } = req.body;
    const now = new Date().toISOString();
    const ref = await db.collection(`users/${req.user.uid}/goals`).add({
      title,
      description: description || "",
      deadline: deadline || null,
      category: category || "personal",
      status: "active",
      progress: 0,
      createdAt: now,
      updatedAt: now,
    });
    res.json({ id: ref.id });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Update goal
router.patch("/:id", async (req, res) => {
  try {
    const allowed = ["title", "description", "deadline", "category", "status", "progress"];
    const update = {};
    for (const k of allowed) if (req.body[k] !== undefined) update[k] = req.body[k];
    update.updatedAt = new Date().toISOString();
    await db.doc(`users/${req.user.uid}/goals/${req.params.id}`).update(update);
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Delete goal
router.delete("/:id", async (req, res) => {
  try {
    const ref = db.doc(`users/${req.user.uid}/goals/${req.params.id}`);
    const tasks = await ref.collection("tasks").get();
    const batch = db.batch();
    tasks.forEach((t) => batch.delete(t.ref));
    batch.delete(ref);
    await batch.commit();
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Add task to goal
router.post("/:goalId/tasks", async (req, res) => {
  try {
    const { title, dueDate } = req.body;
    const now = new Date().toISOString();
    const goalRef = db.doc(`users/${req.user.uid}/goals/${req.params.goalId}`);
    const ref = await goalRef.collection("tasks").add({
      title,
      dueDate: dueDate || null,
      completed: false,
      createdAt: now,
    });
    res.json({ id: ref.id });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Update task
router.patch("/:goalId/tasks/:taskId", async (req, res) => {
  try {
    const ref = db.doc(`users/${req.user.uid}/goals/${req.params.goalId}/tasks/${req.params.taskId}`);
    const update = {};
    if (req.body.completed !== undefined) update.completed = req.body.completed;
    if (req.body.title !== undefined) update.title = req.body.title;
    await ref.update(update);

    // Recalculate goal progress
    const tasks = await db.collection(`users/${req.user.uid}/goals/${req.params.goalId}/tasks`).get();
    const total = tasks.size;
    const done = tasks.docs.filter((d) => d.data().completed).length;
    const progress = total > 0 ? Math.round((done / total) * 100) : 0;
    await db.doc(`users/${req.user.uid}/goals/${req.params.goalId}`).update({ progress });

    res.json({ ok: true, progress });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// AI: Generate tasks for a goal
router.post("/:goalId/generate-tasks", async (req, res) => {
  try {
    const goalDoc = await db.doc(`users/${req.user.uid}/goals/${req.params.goalId}`).get();
    if (!goalDoc.exists) return res.status(404).json({ error: "Goal not found" });
    const goal = goalDoc.data();

    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

    const prompt = `Generate 5-7 actionable tasks to achieve this goal: "${goal.title}".
Description: ${goal.description || "None"}
Deadline: ${goal.deadline || "Not set"}

Return ONLY a JSON array of objects with "title" and "dueDate" (ISO date string or null). No other text.`;

    const result = await model.generateContent(prompt);
    const text = result.response.text().replace(/```json\n?|\n?```/g, "").trim();
    const tasks = JSON.parse(text);

    const now = new Date().toISOString();
    const goalRef = db.doc(`users/${req.user.uid}/goals/${req.params.goalId}`);
    const batch = db.batch();
    const ids = [];

    for (const task of tasks) {
      const ref = goalRef.collection("tasks").doc();
      batch.set(ref, { title: task.title, dueDate: task.dueDate || null, completed: false, createdAt: now });
      ids.push(ref.id);
    }
    await batch.commit();

    res.json({ tasks: tasks.map((t, i) => ({ id: ids[i], ...t, completed: false })) });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Goal progress summary
router.get("/meta/progress", async (req, res) => {
  try {
    const snap = await db.collection(`users/${req.user.uid}/goals`).get();
    const goals = snap.docs.map((d) => d.data());
    const byStatus = goals.reduce((acc, g) => {
      acc[g.status] = (acc[g.status] || 0) + 1;
      return acc;
    }, {});
    res.json({
      total: goals.length,
      active: byStatus.active || 0,
      completed: byStatus.completed || 0,
      paused: byStatus.paused || 0,
      labels: Object.keys(byStatus),
      data: Object.values(byStatus),
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

module.exports = router;
