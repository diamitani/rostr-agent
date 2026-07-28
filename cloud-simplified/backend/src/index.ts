import express from "express";
import cors from "cors";
import helmet from "helmet";
import rateLimit from "express-rate-limit";
import { createServer } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { v4 as uuidv4 } from "uuid";
import dotenv from "dotenv";

import { ROSTRAgent } from "./agent.js";
import { AuthService } from "./auth/service.js";
import { GStackWorkspace } from "./gstack/workspace.js";

dotenv.config();

const app = express();
const server = createServer(app);
const wss = new WebSocketServer({ server });

// Initialize services
const agent = new ROSTRAgent();
const auth = new AuthService();
const gstack = new GStackWorkspace();

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || "http://localhost:3000",
  credentials: true,
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
});
app.use(limiter);

app.use(express.json());

// Health check
app.get("/health", (req, res) => {
  res.json({ 
    status: "ok", 
    timestamp: new Date().toISOString(),
    version: "1.0.0",
  });
});

// ========== AUTH ROUTES ==========

// Register
app.post("/api/auth/register", async (req, res) => {
  try {
    const { email, password, name } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({ error: "Email and password are required" });
    }

    const result = await auth.register(email, password, name);
    res.json({ success: true, ...result });
  } catch (error) {
    console.error("Register error:", error);
    res.status(400).json({ error: error instanceof Error ? error.message : "Registration failed" });
  }
});

// Login
app.post("/api/auth/login", async (req, res) => {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({ error: "Email and password are required" });
    }

    const result = await auth.login(email, password);
    res.json({ success: true, ...result });
  } catch (error) {
    console.error("Login error:", error);
    res.status(401).json({ error: error instanceof Error ? error.message : "Authentication failed" });
  }
});

// Verify token middleware
async function authenticate(req: express.Request, res: express.Response, next: express.NextFunction) {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith("Bearer ")) {
      return res.status(401).json({ error: "Unauthorized" });
    }

    const token = authHeader.substring(7);
    const decoded = await auth.verifyToken(token);
    
    (req as any).user = decoded;
    next();
  } catch (error) {
    res.status(401).json({ error: "Invalid token" });
  }
}

// Get current user
app.get("/api/me", authenticate, async (req, res) => {
  try {
    const userId = (req as any).user.userId;
    const workspaces = await auth.getUserWorkspaces(userId);
    res.json({ success: true, user: { id: userId }, workspaces });
  } catch (error) {
    res.status(500).json({ error: error instanceof Error ? error.message : "Failed to get user" });
  }
});

// ========== WORKSPACE ROUTES ==========

// Get user's workspaces
app.get("/api/workspaces", authenticate, async (req, res) => {
  try {
    const userId = (req as any).user.userId;
    const workspaces = await auth.getUserWorkspaces(userId);
    res.json({ success: true, workspaces });
  } catch (error) {
    res.status(500).json({ error: error instanceof Error ? error.message : "Failed to get workspaces" });
  }
});

// Create new workspace
app.post("/api/workspaces", authenticate, async (req, res) => {
  try {
    const userId = (req as any).user.userId;
    const { name } = req.body;
    
    if (!name) {
      return res.status(400).json({ error: "Workspace name is required" });
    }

    const workspaceId = await gstack.createWorkspace(userId, name);
    res.json({ success: true, workspaceId });
  } catch (error) {
    res.status(500).json({ error: error instanceof Error ? error.message : "Failed to create workspace" });
  }
});

// Launch workspace
app.post("/api/workspaces/:workspaceId/launch", authenticate, async (req, res) => {
  try {
    const userId = (req as any).user.userId;
    const { workspaceId } = req.params;
    
    const result = await auth.launchWorkspace(workspaceId, userId);
    res.json({ success: true, ...result });
  } catch (error) {
    res.status(500).json({ error: error instanceof Error ? error.message : "Failed to launch workspace" });
  }
});

// Get workspace messages
app.get("/api/workspaces/:workspaceId/messages", authenticate, async (req, res) => {
  try {
    const userId = (req as any).user.userId;
    const { workspaceId } = req.params;
    const limit = parseInt(req.query.limit as string) || 50;
    
    // Verify workspace belongs to user
    const workspaces = await auth.getUserWorkspaces(userId);
    const hasAccess = workspaces.some(w => w.id === workspaceId);
    
    if (!hasAccess) {
      return res.status(403).json({ error: "Access denied" });
    }

    const messages = await gstack.getMessages(workspaceId, limit);
    res.json({ success: true, messages });
  } catch (error) {
    res.status(500).json({ error: error instanceof Error ? error.message : "Failed to get messages" });
  }
});

// ========== CHAT ROUTES ==========

// Chat endpoint
app.post("/api/chat", authenticate, async (req, res) => {
  try {
    const userId = (req as any).user.userId;
    const { message, history = [], workspaceId, config = {} } = req.body;
    
    if (!message) {
      return res.status(400).json({ error: "Message is required" });
    }

    const result = await agent.processMessage(
      message,
      history,
      {
        userId,
        workspaceId,
        model: config.model,
        enablePAL: config.enablePAL ?? true,
        enableNPAO: config.enableNPAO ?? true,
        enableRAG: config.enableRAG ?? true,
      }
    );

    res.json({
      success: true,
      response: result.response,
      metadata: result.metadata,
    });
  } catch (error) {
    console.error("Chat error:", error);
    res.status(500).json({
      error: error instanceof Error ? error.message : "Internal server error",
    });
  }
});

// Streaming chat endpoint
app.post("/api/chat/stream", authenticate, async (req, res) => {
  try {
    const userId = (req as any).user.userId;
    const { message, history = [], workspaceId, config = {} } = req.body;
    
    if (!message) {
      return res.status(400).json({ error: "Message is required" });
    }

    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");

    const result = await agent.processMessage(
      message,
      history,
      {
        userId,
        workspaceId,
        model: config.model,
        enablePAL: config.enablePAL ?? true,
        enableNPAO: config.enableNPAO ?? true,
        enableRAG: config.enableRAG ?? true,
      },
      (chunk) => {
        res.write(`data: ${JSON.stringify({ type: "chunk", content: chunk })}\n\n`);
      }
    );

    res.write(`data: ${JSON.stringify({ type: "done", metadata: result.metadata })}\n\n`);
    res.end();
  } catch (error) {
    console.error("Stream error:", error);
    res.write(`data: ${JSON.stringify({ type: "error", message: error instanceof Error ? error.message : "Internal server error" })}\n\n`);
    res.end();
  }
});

// WebSocket for real-time chat
wss.on("connection", async (ws: WebSocket, req) => {
  console.log("WebSocket client connected");
  let userId: string | null = null;
  let workspaceId: string | null = null;

  ws.on("message", async (data: string) => {
    try {
      const payload = JSON.parse(data);
      const { type, token, message, history = [], config = {} } = payload;

      if (type === "auth") {
        // Authenticate connection
        try {
          const decoded = await auth.verifyToken(token);
          userId = decoded.userId;
          workspaceId = config.workspaceId;
          ws.send(JSON.stringify({ type: "auth", status: "success", userId }));
        } catch (error) {
          ws.send(JSON.stringify({ type: "auth", status: "error", message: "Invalid token" }));
          ws.close();
        }
        return;
      }

      if (type === "chat" && userId) {
        await agent.processMessage(
          message,
          history,
          {
            userId,
            workspaceId,
            model: config.model,
            enablePAL: config.enablePAL ?? true,
            enableNPAO: config.enableNPAO ?? true,
            enableRAG: config.enableRAG ?? true,
          },
          (chunk) => {
            ws.send(JSON.stringify({ type: "chunk", content: chunk }));
          }
        );

        ws.send(JSON.stringify({ type: "done" }));
      }
    } catch (error) {
      console.error("WebSocket error:", error);
      ws.send(JSON.stringify({
        type: "error",
        message: error instanceof Error ? error.message : "Internal server error",
      }));
    }
  });

  ws.on("close", () => {
    console.log("WebSocket client disconnected");
  });

  ws.on("error", (error) => {
    console.error("WebSocket error:", error);
  });

  // Send welcome message
  ws.send(JSON.stringify({
    type: "connected",
    message: "Connected to ROSTR Agent",
  }));
});

// Start server
const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`ROSTR Cloud Backend running on port ${PORT}`);
  console.log(`WebSocket available at ws://localhost:${PORT}`);
  console.log(`API Documentation:`);
  console.log(`  POST /api/auth/register - Register new user`);
  console.log(`  POST /api/auth/login - Login user`);
  console.log(`  GET  /api/workspaces - List workspaces`);
  console.log(`  POST /api/workspaces - Create workspace`);
  console.log(`  POST /api/workspaces/:id/launch - Launch workspace`);
  console.log(`  POST /api/chat - Send message`);
});
