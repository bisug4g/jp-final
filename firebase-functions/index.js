const { onRequest } = require("firebase-functions/v2/https");
const express = require("express");
const cors = require("cors");

const notesRouter = require("./lib/notes");
const diaryRouter = require("./lib/diary");
const goalsRouter = require("./lib/goals");
const chatRouter = require("./lib/chat");
const dashboardRouter = require("./lib/dashboard");

const app = express();

app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

app.use("/notes", notesRouter);
app.use("/diary", diaryRouter);
app.use("/goals", goalsRouter);
app.use("/chat", chatRouter);
app.use("/dashboard", dashboardRouter);

app.get("/health", (_req, res) => res.json({ ok: true }));

exports.api = onRequest(
  {
    region: "asia-south1",
    timeoutSeconds: 60,
    memory: "512MiB",
    invoker: "public",
    secrets: ["GEMINI_API_KEY"],
  },
  app
);
