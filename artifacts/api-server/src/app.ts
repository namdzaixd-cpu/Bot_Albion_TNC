import express, { type Express } from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import router from "./routes";
import { logger } from "./lib/logger";

const app: Express = express();

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return {
          id: req.id,
          method: req.method,
          url: req.url?.split("?")[0],
        };
      },
      res(res) {
        return {
          statusCode: res.statusCode,
        };
      },
    },
  }),
);
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use("/api", router);

app.use("/bot", async (req, res) => {
  const targetPath = req.originalUrl.replace(/^\/bot/, "") || "/";
  const target = `http://127.0.0.1:5000${targetPath}`;
  try {
    const upstream = await fetch(target, {
      method: req.method,
      headers: { accept: req.headers.accept ?? "*/*" },
    });
    res.status(upstream.status);
    upstream.headers.forEach((value, key) => {
      if (key.toLowerCase() === "content-encoding") return;
      res.setHeader(key, value);
    });
    const buf = Buffer.from(await upstream.arrayBuffer());
    res.send(buf);
  } catch (err) {
    res.status(502).json({
      error: "Discord bot status server unreachable",
      detail: String(err),
    });
  }
});

export default app;
