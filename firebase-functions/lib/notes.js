const { db } = require("./admin");
const { requireAuth } = require("./authMiddleware");
const express = require("express");

const router = express.Router();
router.use(requireAuth);

// List notes
router.get("/", async (req, res) => {
  try {
    const { folder, tag, search, pinned } = req.query;
    let query = db.collection(`users/${req.user.uid}/notes`).orderBy("pinned", "desc").orderBy("updatedAt", "desc");

    const snap = await query.limit(100).get();
    let notes = snap.docs.map((d) => ({ id: d.id, ...d.data() }));

    if (folder) notes = notes.filter((n) => n.folder === folder);
    if (tag) notes = notes.filter((n) => n.tags && n.tags.includes(tag));
    if (pinned === "true") notes = notes.filter((n) => n.pinned);
    if (search) {
      const q = search.toLowerCase();
      notes = notes.filter(
        (n) =>
          n.title?.toLowerCase().includes(q) ||
          n.content?.toLowerCase().includes(q)
      );
    }

    res.json({ notes });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Get single note
router.get("/:id", async (req, res) => {
  try {
    const doc = await db.doc(`users/${req.user.uid}/notes/${req.params.id}`).get();
    if (!doc.exists) return res.status(404).json({ error: "Not found" });
    res.json({ note: { id: doc.id, ...doc.data() } });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Create note
router.post("/", async (req, res) => {
  try {
    const { title, content, folder, tags } = req.body;
    const now = new Date().toISOString();
    const ref = await db.collection(`users/${req.user.uid}/notes`).add({
      title: title || "Untitled",
      content: content || "",
      folder: folder || null,
      tags: tags || [],
      pinned: false,
      createdAt: now,
      updatedAt: now,
    });
    res.json({ id: ref.id });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Update note
router.patch("/:id", async (req, res) => {
  try {
    const allowed = ["title", "content", "folder", "tags", "pinned"];
    const update = {};
    for (const k of allowed) if (req.body[k] !== undefined) update[k] = req.body[k];
    update.updatedAt = new Date().toISOString();
    await db.doc(`users/${req.user.uid}/notes/${req.params.id}`).update(update);
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Delete note
router.delete("/:id", async (req, res) => {
  try {
    await db.doc(`users/${req.user.uid}/notes/${req.params.id}`).delete();
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// List folders
router.get("/meta/folders", async (req, res) => {
  try {
    const snap = await db.collection(`users/${req.user.uid}/notes`).get();
    const folders = [...new Set(snap.docs.map((d) => d.data().folder).filter(Boolean))].sort();
    res.json({ folders });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

module.exports = router;
