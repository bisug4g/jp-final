const { onRequest } = require("firebase-functions/v2/https");
const logger = require("firebase-functions/logger");

const RAILWAY_ORIGIN =
  process.env.RAILWAY_ORIGIN || "https://jp-production-3f28.up.railway.app";

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "content-encoding",
  "content-length",
  "host",
  "transfer-encoding",
]);

exports.railwayProxy = onRequest(
  {
    region: "europe-west1",
    timeoutSeconds: 60,
    memory: "256MiB",
    invoker: "public",
  },
  async (req, res) => {
    const upstreamUrl = new URL(req.originalUrl || req.url, RAILWAY_ORIGIN);
    const headers = new Headers();

    for (const [key, value] of Object.entries(req.headers)) {
      if (value === undefined || HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
        continue;
      }

      headers.set(key, Array.isArray(value) ? value.join(", ") : value);
    }

    headers.set("host", upstreamUrl.host);
    headers.set("x-forwarded-host", req.headers.host || "");
    headers.set("x-forwarded-proto", "https");

    if (req.ip) {
      headers.set("x-forwarded-for", req.ip);
    }

    const method = req.method.toUpperCase();
    const upstreamResponse = await fetch(upstreamUrl, {
      method,
      headers,
      body: method === "GET" || method === "HEAD" ? undefined : req.rawBody,
      redirect: "manual",
    });

    res.status(upstreamResponse.status);

    upstreamResponse.headers.forEach((value, key) => {
      if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
        res.setHeader(key, value);
      }
    });

    if (typeof upstreamResponse.headers.getSetCookie === "function") {
      const cookies = upstreamResponse.headers.getSetCookie();
      if (cookies.length) {
        res.setHeader("set-cookie", cookies);
      }
    }

    const body = Buffer.from(await upstreamResponse.arrayBuffer());
    res.send(body);
  }
);

logger.info("Firebase Hosting proxy configured", { railwayOrigin: RAILWAY_ORIGIN });
