const PRIMARY_URL = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";
const FALLBACK_URLS = [
  PRIMARY_URL,
  "http://127.0.0.1:8000",
  "http://127.0.0.1:8001",
  "http://localhost:8000",
  "http://localhost:8001",
];

let workingBaseUrl = PRIMARY_URL;

async function fetchWithFallback(endpoint, options = {}) {
  const candidateUrls = Array.from(new Set([workingBaseUrl, ...FALLBACK_URLS]));
  let lastError = null;

  for (const baseUrl of candidateUrls) {
    try {
      const fullUrl = `${baseUrl}${endpoint}`;
      const res = await fetch(fullUrl, options);
      if (res.ok || res.status < 500) {
        workingBaseUrl = baseUrl;
        return res;
      }
      lastError = new Error(`Server returned HTTP ${res.status}`);
    } catch (err) {
      lastError = err;
    }
  }

  throw lastError || new Error("Failed to connect to backend API server");
}

export function getStoredToken() {
  return localStorage.getItem("auth_token");
}

export function setStoredToken(token) {
  if (token) {
    localStorage.setItem("auth_token", token);
  } else {
    localStorage.removeItem("auth_token");
  }
}

function getAuthHeaders() {
  const headers = { "Content-Type": "application/json" };
  const token = getStoredToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export async function loginUser(email, password) {
  const res = await fetchWithFallback("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(errData.detail || "Invalid login credentials");
  }
  const data = await res.json();
  setStoredToken(data.access_token);
  return data;
}

export async function registerUser(email, password, fullName, role = "student") {
  const res = await fetchWithFallback("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName, role }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: "Registration failed" }));
    throw new Error(errData.detail || "Registration failed");
  }
  const data = await res.json();
  setStoredToken(data.access_token);
  return data;
}

export async function getCurrentUser() {
  try {
    const res = await fetchWithFallback("/api/auth/me", {
      headers: getAuthHeaders(),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.user;
  } catch {
    return null;
  }
}

export async function getSpeechToken() {
  const res = await fetchWithFallback("/api/speech/token", { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Could not get speech token");
  return res.json();
}

export async function getSupportedLanguages() {
  const res = await fetchWithFallback("/api/config/languages");
  if (!res.ok) throw new Error("Could not load languages");
  return res.json();
}

export async function askAssistant(query, language, conversationId) {
  const res = await fetchWithFallback("/api/ask", {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ query, language, conversation_id: conversationId }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: "Assistant request failed" }));
    throw new Error(errData.detail || "Assistant request failed");
  }
  return res.json();
}

export async function speak(text, language) {
  const res = await fetchWithFallback("/api/speak", {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ text, language }),
  });
  if (!res.ok) throw new Error("Speech synthesis failed");
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

// Partner Finder API Endpoints

export async function getStudentProfiles() {
  const res = await fetchWithFallback("/api/partners/profiles", { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Could not load student profiles");
  return res.json();
}

export async function searchPartners(userSkills, requiredSkills, projectType) {
  const res = await fetchWithFallback("/api/partners/search", {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      user_skills: userSkills,
      required_skills: requiredSkills,
      project_type: projectType,
    }),
  });
  if (!res.ok) throw new Error("Partner search failed");
  return res.json();
}

export async function sendCollaborationRequest(payload) {
  const res = await fetchWithFallback("/api/partners/request", {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Could not send collaboration request");
  return res.json();
}

export async function getCollaborationRequests() {
  const res = await fetchWithFallback("/api/partners/requests", { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Could not load collaboration requests");
  return res.json();
}

export async function updateSmtpConfig(smtpUser, smtpPassword, smtpHost = "smtp.gmail.com", smtpPort = 587) {
  const res = await fetchWithFallback("/api/partners/smtp-config", {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      smtp_user: smtpUser,
      smtp_password: smtpPassword,
      smtp_host: smtpHost,
      smtp_port: smtpPort,
    }),
  });
  if (!res.ok) throw new Error("Could not configure SMTP");
  return res.json();
}

export async function testSmtpConnection(toEmail) {
  const res = await fetchWithFallback("/api/partners/test-smtp", {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ to_email: toEmail }),
  });
  if (!res.ok) throw new Error("SMTP connection test failed");
  return res.json();
}

export async function updateRequestStatus(requestId, status) {
  const res = await fetchWithFallback(`/api/partners/requests/${requestId}/status`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error("Could not update request status");
  return res.json();
}
