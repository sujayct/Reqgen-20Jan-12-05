import type { Express, Request, Response, NextFunction } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertDocumentSchema, insertSettingsSchema } from "@shared/schema";
import { sendEmail } from "./email";
import htmlPdf from "html-pdf-node";
import multer from "multer";

// Temporary user credentials (will be moved to database later)
const TEMP_USERS = [
  {
    email: "analyst@reqgen.com",
    password: "analyst123",
    role: "analyst",
    name: "Business Analyst"
  },
  {
    email: "admin@reqgen.com",
    password: "admin123",
    role: "admin",
    name: "System Administrator"
  },
  {
    email: "client@reqgen.com",
    password: "client123",
    role: "client",
    name: "Client User"
  }
];

// Authorization middleware
function requireRole(allowedRoles: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    const userRole = req.headers['x-user-role'] as string;

    if (!userRole) {
      res.status(401).json({ error: "Unauthorized - No user role provided" });
      return;
    }

    if (!allowedRoles.includes(userRole)) {
      res.status(403).json({ error: "Forbidden - Insufficient permissions" });
      return;
    }

    next();
  };
}

export async function registerRoutes(app: Express): Promise<Server> {
  // Login route
  app.post("/api/login", async (req, res) => {
    try {
      const { email, password, role } = req.body;

      // Use storage layer to authenticate user
      const user = await storage.login(email, password, role);

      if (!user) {
        res.status(401).json({ error: "Invalid email, password, or role" });
        return;
      }

      // Successful login
      res.json({
        success: true,
        user: {
          email: user.email,
          role: user.role,
          name: user.name
        }
      });
    } catch (error) {
      console.error('Login error:', error);
      res.status(500).json({ error: "Login failed" });
    }
  });

  // Document routes (only admin and analyst can create)
  app.post("/api/documents", requireRole(['admin', 'analyst']), async (req, res) => {
    try {
      const validatedData = insertDocumentSchema.parse(req.body);
      const document = await storage.createDocument(validatedData);
      res.json(document);
    } catch (error) {
      res.status(400).json({ error: "Invalid document data" });
    }
  });

  app.get("/api/documents", async (req, res) => {
    try {
      const documents = await storage.getAllDocuments();
      res.json(documents);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch documents" });
    }
  });

  app.get("/api/documents/:id", async (req, res) => {
    try {
      const document = await storage.getDocument(req.params.id);
      if (!document) {
        res.status(404).json({ error: "Document not found" });
        return;
      }
      res.json(document);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch document" });
    }
  });

  app.patch("/api/documents/:id", requireRole(['admin', 'analyst', 'client']), async (req, res) => {
    try {
      const userRole = req.headers['x-user-role'] as string;
      const userName = req.headers['x-user-name'] as string;
      let updateData = req.body;
      let shouldCreateNotification = false;
      let notificationTitle = "";
      let notificationMessage = "";

      if (userRole === 'client') {
        const allowedStatuses = ['approved', 'needs_changes', 'pending'];
        if (updateData.status && !allowedStatuses.includes(updateData.status)) {
          res.status(400).json({ error: "Invalid status value" });
          return;
        }
        updateData = {
          status: updateData.status,
          clientMessage: updateData.clientMessage || null
        };

        // Create notification when client approves or requests changes
        if (updateData.status === 'approved' || updateData.status === 'needs_changes') {
          shouldCreateNotification = true;
          if (updateData.status === 'approved') {
            notificationTitle = "Document Approved";
            notificationMessage = `Document has been approved by client`;
          } else {
            notificationTitle = "Changes Requested";
            notificationMessage = `Client has requested changes to the document`;
          }
        }
      }

      const document = await storage.updateDocument(req.params.id, updateData, userName, userRole);
      if (!document) {
        res.status(404).json({ error: "Document not found" });
        return;
      }

      // Create notification for admin and analyst users
      if (shouldCreateNotification) {
        await storage.createNotification({
          title: notificationTitle,
          message: notificationMessage,
          targetRole: "all", // Send to both admin and analyst
          documentId: document.id,
          documentName: document.name,
          creatorRole: "client",
        });
      }

      res.json(document);
    } catch (error) {
      res.status(500).json({ error: "Failed to update document" });
    }
  });

  app.delete("/api/documents/:id", requireRole(['admin', 'analyst']), async (req, res) => {
    try {
      const success = await storage.deleteDocument(req.params.id);
      if (!success) {
        res.status(404).json({ error: "Document not found" });
        return;
      }
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to delete document" });
    }
  });

  // Settings routes (all users can view)
  app.get("/api/settings", async (req, res) => {
    try {
      const settings = await storage.getSettings();
      res.json(settings);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch settings" });
    }
  });

  app.put("/api/settings", requireRole(['admin']), async (req, res) => {
    try {
      console.log("Received settings data:", JSON.stringify(req.body, null, 2));
      const validatedData = insertSettingsSchema.parse(req.body);
      console.log("Validated settings data:", JSON.stringify(validatedData, null, 2));
      const settings = await storage.updateSettings(validatedData);
      res.json(settings);
    } catch (error) {
      console.error("Settings validation error:", error);
      res.status(400).json({ error: "Invalid settings data" });
    }
  });

  // Generate PDF endpoint for direct download
  app.post("/api/generate-pdf", async (req, res) => {
    try {
      const { documentHtml, documentName } = req.body;

      if (!documentHtml) {
        res.status(400).json({ error: "Missing document HTML" });
        return;
      }

      // Convert HTML to PDF
      const pdfOptions: any = {
        format: "A4",
        printBackground: true,
        margin: {
          top: "20mm",
          bottom: "20mm",
          left: "15mm",
          right: "15mm"
        },
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      };

      // Only set executablePath if running on Replit (env var is set in server/index.ts)
      if (process.env.PUPPETEER_EXECUTABLE_PATH) {
        pdfOptions.executablePath = process.env.PUPPETEER_EXECUTABLE_PATH;
      }

      const file = { content: documentHtml };
      const pdfBuffer = await htmlPdf.generatePdf(file, pdfOptions);

      // Set headers for PDF download
      res.setHeader('Content-Type', 'application/pdf');
      res.setHeader('Content-Disposition', `attachment; filename="${documentName || 'document'}.pdf"`);
      res.send(pdfBuffer);
    } catch (error: any) {
      console.error("PDF generation error:", error);
      res.status(500).json({ error: error.message || "Failed to generate PDF" });
    }
  });

  app.post("/api/send-email", requireRole(['admin', 'analyst']), async (req, res) => {
    try {
      const { recipient, subject, message, documentHtml, documentName } = req.body;

      if (!recipient || !subject || !documentHtml) {
        res.status(400).json({ error: "Missing required fields" });
        return;
      }

      const escapeHtml = (text: string) => {
        return text
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#039;");
      };

      const safeMessage = message ? escapeHtml(message) : "Please find the attached document.";

      const emailBody = `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
          <h2 style="color: #333;">Document Attached</h2>
          <p style="color: #666; line-height: 1.6;">
            ${safeMessage}
          </p>
          <p style="color: #666; line-height: 1.6;">
            The document is attached as a PDF file. You can:
          </p>
          <ul style="color: #666; line-height: 1.6;">
            <li>Open it directly in your PDF viewer</li>
            <li>Print it for your records</li>
            <li>Save it on your device</li>
          </ul>
          <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
            This email was sent from ReqGen Document Management System
          </p>
        </div>
      `;

      // Convert HTML to PDF
      const pdfOptions: any = {
        format: "A4",
        printBackground: true,
        margin: {
          top: "20mm",
          bottom: "20mm",
          left: "15mm",
          right: "15mm"
        },
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      };

      // Only set executablePath if running on Replit (env var is set in server/index.ts)
      if (process.env.PUPPETEER_EXECUTABLE_PATH) {
        pdfOptions.executablePath = process.env.PUPPETEER_EXECUTABLE_PATH;
      }

      const file = { content: documentHtml };
      const pdfBuffer = await htmlPdf.generatePdf(file, pdfOptions);

      const filename = documentName ? `${documentName}.pdf` : "document.pdf";

      await sendEmail({
        to: recipient,
        subject,
        text: message || "Please find the attached document.",
        html: emailBody,
        attachments: [
          {
            filename,
            content: pdfBuffer,
            contentType: "application/pdf",
          },
        ],
      });

      res.json({ success: true, message: "Email sent successfully" });
    } catch (error: any) {
      console.error("Email sending error:", error);
      res.status(500).json({ error: error.message || "Failed to send email" });
    }
  });

  // Vakyansh Speech-to-Text Transcription
  const upload = multer({ storage: multer.memoryStorage() });

  app.post("/api/vakyansh-transcribe", upload.single('audio'), async (req, res) => {
    try {
      if (!req.file) {
        res.status(400).json({ error: "No audio file provided" });
        return;
      }

      const language = req.body.language || 'hi'; // Default to Hindi
      const audioBuffer = req.file.buffer;

      console.log(`Vakyansh transcription request - Language: ${language}, Original audio size: ${audioBuffer.length} bytes, Format: ${req.file.mimetype}`);

      // Check if audio format is supported (Vakyansh supports: wav, mp3, flac)
      const supportedFormats = [
        'audio/wav', 'audio/wave', 'audio/x-wav',
        'audio/mpeg', 'audio/mp3',
        'audio/flac', 'audio/x-flac',
        'audio/webm', 'audio/ogg', 'audio/opus',
        'audio/m4a', 'audio/x-m4a', 'audio/mp4', 'audio/aac', 'audio/x-aac'
      ];

      const isSupported = supportedFormats.some(format => req.file!.mimetype.includes(format.split('/')[1]) || req.file!.mimetype === format);

      if (!isSupported) {
        console.error(`Unsupported audio format: ${req.file.mimetype}`);
        res.status(400).json({
          error: "Unsupported audio format",
          details: `The format ${req.file.mimetype} is not supported. Please upload WAV, MP3, FLAC, M4A, or WEBM files.`,
          supportedFormats: ['WAV', 'MP3', 'FLAC', 'M4A', 'WEBM', 'OGG']
        });
        return;
      }

      // Convert audio buffer to base64
      const base64Audio = audioBuffer.toString('base64');

      // Determine audio format from mimetype
      let audioFormat = 'wav';
      if (req.file.mimetype.includes('mpeg') || req.file.mimetype.includes('mp3')) {
        audioFormat = 'mp3';
      } else if (req.file.mimetype.includes('flac')) {
        audioFormat = 'flac';
      } else if (req.file.mimetype.includes('m4a') || req.file.mimetype.includes('mp4')) {
        // Vakyansh might not natively support m4a/mp4, but we'll try sending it or default to wav
        // If the API fails with these, we might need a converter, but let's expand the protocol first
        audioFormat = 'mp3'; // Attempt as mp3 or wav
      }

      console.log(`Using audio format: ${audioFormat} for mimetype: ${req.file.mimetype}`);

      // Vakyansh API endpoint
      const vakyanshUrl = `https://cdac.ulcacontrib.org/asr/v1/recognize/${language}`;

      // Prepare Vakyansh API request
      const vakyanshPayload = {
        config: {
          language: {
            sourceLanguage: language
          },
          transcriptionFormat: {
            value: "transcript"
          },
          audioFormat: audioFormat
        },
        audio: [
          {
            audioContent: base64Audio
          }
        ]
      };

      console.log(`Calling Vakyansh API: ${vakyanshUrl} with format: ${audioFormat}`);

      // Call Vakyansh API with timeout
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 60000); // Increased to 60 seconds

      let response;
      try {
        response = await fetch(vakyanshUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(vakyanshPayload),
          signal: controller.signal
        });
      } catch (fetchError: any) {
        clearTimeout(timeout);
        console.error('Vakyansh fetch failed, attempting fallback:', fetchError);

        // --- FALLBACK 1: PYTHON WHISPER BACKEND ---
        try {
          console.log(`Attempting fallback transcription via Python backend...`);
          const pythonBackendUrl = process.env.PYTHON_BACKEND_URL || 'http://localhost:5000';

          const formData = new FormData();
          const audioBlob = new Blob([audioBuffer], { type: req.file.mimetype });
          formData.append('audio', audioBlob, req.file.originalname);

          const pythonController = new AbortController();
          const pythonTimeout = setTimeout(() => pythonController.abort(), 30000); // 30 second timeout for fallback

          const pythonResponse = await fetch(`${pythonBackendUrl}/api/transcribe`, {
            method: 'POST',
            body: formData,
            signal: pythonController.signal
          });

          clearTimeout(pythonTimeout);

          if (pythonResponse.ok) {
            const pythonResult = await pythonResponse.json();
            console.log('Fallback transcription successful via Python/Whisper');
            return res.json({
              success: true,
              transcription: pythonResult.transcript || pythonResult.text,
              language: pythonResult.language,
              source: 'fallback-whisper'
            });
          } else {
            console.warn(`Python backend returned ${pythonResponse.status}`);
          }
        } catch (fallbackError: any) {
          console.error('Fallback 1 (Python backend) failed:', fallbackError?.message);
        }
        // --- END FALLBACK 1 ---

        // --- FALLBACK 2: OPENAI WHISPER API (for cloud deployments) ---
        if (process.env.OPENAI_API_KEY) {
          try {
            console.log(`Attempting secondary fallback via OpenAI Whisper API...`);
            
            const openaiFormData = new FormData();
            const audioBlob = new Blob([audioBuffer], { type: req.file.mimetype });
            openaiFormData.append('file', audioBlob, 'audio.webm');
            openaiFormData.append('model', 'whisper-1');
            if (language !== 'hi') {
              openaiFormData.append('language', language === 'en' ? 'en' : language);
            }

            const openaiController = new AbortController();
            const openaiTimeout = setTimeout(() => openaiController.abort(), 60000); // 60 second timeout

            const openaiResponse = await fetch('https://api.openai.com/v1/audio/transcriptions', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`
              },
              body: openaiFormData,
              signal: openaiController.signal
            });

            clearTimeout(openaiTimeout);

            if (openaiResponse.ok) {
              const openaiResult = await openaiResponse.json();
              console.log('Secondary fallback transcription successful via OpenAI Whisper');
              return res.json({
                success: true,
                transcription: openaiResult.text,
                language: language,
                source: 'openai-whisper'
              });
            } else {
              const errorText = await openaiResponse.text().catch(() => '');
              console.warn(`OpenAI API returned ${openaiResponse.status}: ${errorText}`);
            }
          } catch (openaiError: any) {
            console.error('Fallback 2 (OpenAI) also failed:', openaiError?.message);
          }
        }
        // --- END FALLBACK 2 ---

        res.status(503).json({
          error: "Transcription service unreachable",
          details: "All transcription services are currently unavailable. Please try again in a few moments.",
          technical: fetchError.message,
          suggestion: process.env.NODE_ENV === 'production' 
            ? "The transcription services are temporarily down. Please try again later." 
            : "Ensure Python backend is running or set PYTHON_BACKEND_URL environment variable"
        });
        return;
      }

      clearTimeout(timeout);

      if (!response.ok) {
        let errorText = "";
        try {
          errorText = await response.text();
        } catch (e) {
          errorText = "Could not read error response";
        }
        console.error('Vakyansh API error:', response.status, errorText);

        // --- FALLBACK TO PYTHON WHISPER ON 503/502/504 ---
        if (response.status >= 500) {
          try {
            console.log(`Vakyansh returned ${response.status}, attempting fallback transcription...`);
            const pythonBackendUrl = process.env.PYTHON_BACKEND_URL || 'http://localhost:5000';

            const formData = new FormData();
            const audioBlob = new Blob([audioBuffer], { type: req.file.mimetype });
            formData.append('audio', audioBlob, req.file.originalname);

            const pythonController = new AbortController();
            const pythonTimeout = setTimeout(() => pythonController.abort(), 30000); // 30 second timeout for fallback

            const pythonResponse = await fetch(`${pythonBackendUrl}/api/transcribe`, {
              method: 'POST',
              body: formData,
              signal: pythonController.signal
            });

            clearTimeout(pythonTimeout);

            if (pythonResponse.ok) {
              const pythonResult = await pythonResponse.json();
              console.log('Fallback transcription successful via Python/Whisper');
              return res.json({
                success: true,
                transcription: pythonResult.transcript || pythonResult.text,
                language: pythonResult.language,
                source: 'fallback-whisper'
              });
            } else {
              console.warn(`Python backend returned ${pythonResponse.status}`);
            }
          } catch (fallbackError: any) {
            console.error('Fallback 1 (Python backend) failed:', fallbackError?.message);
          }

          // --- FALLBACK 2: OPENAI WHISPER API ---
          if (process.env.OPENAI_API_KEY) {
            try {
              console.log(`Attempting secondary fallback via OpenAI Whisper API...`);
              
              const openaiFormData = new FormData();
              const audioBlob = new Blob([audioBuffer], { type: req.file.mimetype });
              openaiFormData.append('file', audioBlob, 'audio.webm');
              openaiFormData.append('model', 'whisper-1');
              if (language !== 'hi') {
                openaiFormData.append('language', language === 'en' ? 'en' : language);
              }

              const openaiController = new AbortController();
              const openaiTimeout = setTimeout(() => openaiController.abort(), 60000); // 60 second timeout

              const openaiResponse = await fetch('https://api.openai.com/v1/audio/transcriptions', {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`
                },
                body: openaiFormData,
                signal: openaiController.signal
              });

              clearTimeout(openaiTimeout);

              if (openaiResponse.ok) {
                const openaiResult = await openaiResponse.json();
                console.log('Secondary fallback transcription successful via OpenAI Whisper');
                return res.json({
                  success: true,
                  transcription: openaiResult.text,
                  language: language,
                  source: 'openai-whisper'
                });
              } else {
                const errorText = await openaiResponse.text().catch(() => '');
                console.warn(`OpenAI API returned ${openaiResponse.status}: ${errorText}`);
              }
            } catch (openaiError: any) {
              console.error('Fallback 2 (OpenAI) also failed:', openaiError?.message);
            }
          }
          // --- END FALLBACK 2 ---
        }
        // --- END FALLBACK ---

        res.status(response.status).json({
          error: "Transcription service error",
          details: `Vakyansh API returned ${response.status}. The service might be busy or the file size too large.`,
          vakyanshError: errorText.substring(0, 200),
          suggestion: response.status >= 500 ? "The service is temporarily unavailable. Please try again in a few moments." : undefined
        });
        return;
      }

      const result = await response.json();
      console.log('Vakyansh API response:', JSON.stringify(result, null, 2));

      // Extract transcription from response
      const transcription = result.output?.[0]?.source || result.output?.[0]?.text || '';

      if (!transcription) {
        console.error('No transcription in response:', result);
        res.status(500).json({
          error: "No transcription received",
          details: "The audio could not be transcribed. The audio may be too quiet, unclear, or in an unsupported language. Please try speaking more clearly or use a different audio file."
        });
        return;
      }

      console.log(`Transcription successful - Language: ${language}, Text: "${transcription}"`);

      res.json({
        success: true,
        transcription,
        language: result.config?.language?.sourceLanguage || language
      });

    } catch (error: any) {
      console.error("Vakyansh transcription error:", error);

      let errorMessage = "Transcription failed";
      let errorDetails = error.message;

      if (error.name === 'AbortError') {
        errorMessage = "Transcription timeout";
        errorDetails = "The transcription service took too long to respond. Please try again with shorter audio.";
      }

      res.status(500).json({
        error: errorMessage,
        details: errorDetails
      });
    }
  });

  // Notification routes
  app.get("/api/notifications", async (req, res) => {
    try {
      const userId = req.headers['x-user-id'] as string;
      const userRole = req.headers['x-user-role'] as string;

      if (!userId || !userRole) {
        res.status(401).json({ error: "Unauthorized - No user information provided" });
        return;
      }

      const notifications = await storage.getNotificationsForUser(userId, userRole);
      res.json(notifications);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch notifications" });
    }
  });

  app.patch("/api/notifications/:id/read", async (req, res) => {
    try {
      const userId = req.headers['x-user-id'] as string;

      if (!userId) {
        res.status(401).json({ error: "Unauthorized - No user ID provided" });
        return;
      }

      const success = await storage.markNotificationRead(req.params.id, userId);
      if (!success) {
        res.status(404).json({ error: "Notification not found" });
        return;
      }

      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to mark notification as read" });
    }
  });

  app.patch("/api/notifications/read-all", async (req, res) => {
    try {
      const userId = req.headers['x-user-id'] as string;

      if (!userId) {
        res.status(401).json({ error: "Unauthorized - No user ID provided" });
        return;
      }

      await storage.markAllNotificationsRead(userId);
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to mark all notifications as read" });
    }
  });

  // Python Backend Proxy Endpoints
  const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || "http://localhost:5000";

  // Proxy for AI summarization
  app.post("/api/python-backend/summarize", async (req, res) => {
    try {
      const { text } = req.body;
      if (!text) {
        res.status(400).json({ error: "Text is required" });
        return;
      }

      const response = await fetch(`${PYTHON_BACKEND_URL}/api/summarize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
        signal: AbortSignal.timeout(180000), // 180 second timeout for model loading
      });

      if (!response.ok) {
        throw new Error(`Python backend error: ${response.status}`);
      }

      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Summarization error:", error);
      res.status(503).json({ 
        error: "Summarization service unavailable",
        message: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  // Proxy for document generation
  app.post("/api/python-backend/generate-document", async (req, res) => {
    try {
      const { text, document_type, metadata } = req.body;
      if (!text || !document_type) {
        res.status(400).json({ error: "Text and document_type are required" });
        return;
      }

      const response = await fetch(`${PYTHON_BACKEND_URL}/api/generate-document`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, document_type, metadata }),
        signal: AbortSignal.timeout(300000), // 300 second timeout for generation with model loading
      });

      if (!response.ok) {
        throw new Error(`Python backend error: ${response.status}`);
      }

      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Document generation error:", error);
      res.status(503).json({ 
        error: "Document generation service unavailable",
        message: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
