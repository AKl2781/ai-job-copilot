import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { API_BASE_URL, ApiError, api, apiFetch } from "./api.ts";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
});

test("apiFetch builds the API URL and returns JSON", async () => {
  let requestedUrl = "";
  globalThis.fetch = async (input) => {
    requestedUrl = String(input);
    return new Response(JSON.stringify([{ id: "job-1" }]), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };

  const result = await apiFetch<Array<{ id: string }>>("/api/v1/jobs");
  assert.equal(requestedUrl, `${API_BASE_URL}/api/v1/jobs`);
  assert.deepEqual(result, [{ id: "job-1" }]);
});

test("apiFetch surfaces FastAPI errors", async () => {
  globalThis.fetch = async () => new Response(
    JSON.stringify({ detail: "job not found" }),
    { status: 404, headers: { "Content-Type": "application/json" } },
  );

  await assert.rejects(
    () => apiFetch("/api/v1/jobs/missing"),
    (error) => error instanceof ApiError
      && error.status === 404
      && error.message === "job not found",
  );
});

test("job detail IDs are URL encoded", async () => {
  let requestedUrl = "";
  globalThis.fetch = async (input) => {
    requestedUrl = String(input);
    return new Response(JSON.stringify({ id: "a/b" }), { status: 200 });
  };

  await api.getJob("a/b");
  assert.equal(requestedUrl, `${API_BASE_URL}/api/v1/jobs/a%2Fb`);
});

test("createJob persists a manual or extension payload", async () => {
  let requestedInit: RequestInit | undefined;
  globalThis.fetch = async (_input, init) => {
    requestedInit = init;
    return new Response(JSON.stringify({ id: "job-2" }), { status: 201 });
  };
  const payload = {
    title: "Backend Engineer",
    company: "Example",
    description: "Build APIs",
    source_url: null,
    source_type: "manual",
  };

  await api.createJob(payload);

  assert.equal(requestedInit?.method, "POST");
  assert.equal(requestedInit?.body, JSON.stringify(payload));
});

test("createJob returns the idempotent creation status", async () => {
  globalThis.fetch = async () => new Response(JSON.stringify({
    id: "job-2",
    job_id: "job-2",
    status: "duplicate",
    message: "该岗位已保存",
  }), { status: 200 });

  const result = await api.createJob({
    title: "Backend Engineer",
    company: "Example",
    description: "Build APIs",
    source_url: "https://example.test/jobs/2",
    source_type: "manual",
  });

  assert.equal(result.status, "duplicate");
  assert.equal(result.job_id, "job-2");
});

test("analyzeJob posts to the saved-job workflow", async () => {
  let requestedUrl = "";
  let requestedMethod = "";
  globalThis.fetch = async (input, init) => {
    requestedUrl = String(input);
    requestedMethod = init?.method ?? "GET";
    return new Response(JSON.stringify({ id: "analysis-1", status: "completed" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };

  await api.analyzeJob("job/1");
  assert.equal(requestedUrl, `${API_BASE_URL}/api/v1/jobs/job%2F1/analyze`);
  assert.equal(requestedMethod, "POST");
});

test("agent run APIs create and poll encoded runs", async () => {
  const requests: Array<{ url: string; init?: RequestInit }> = [];
  globalThis.fetch = async (input, init) => {
    requests.push({ url: String(input), init });
    return new Response(JSON.stringify({ run_id: "run/1", status: "running" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };

  await api.createAgentRun("job-1");
  await api.getAgentRun("run/1");

  assert.equal(requests[0].url, `${API_BASE_URL}/api/v1/agent/runs`);
  assert.equal(requests[0].init?.method, "POST");
  assert.equal(requests[0].init?.body, JSON.stringify({ job_id: "job-1" }));
  assert.equal(requests[1].url, `${API_BASE_URL}/api/v1/agent/runs/run%2F1`);
});

test("document APIs use encoded user-scoped document paths", async () => {
  const requestedUrls: string[] = [];
  globalThis.fetch = async (input) => {
    requestedUrls.push(String(input));
    return new Response(JSON.stringify([]), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };

  await api.getDocuments();
  await api.getDocument("resume/a");
  await api.getDocumentChunks("resume/a");

  assert.deepEqual(requestedUrls, [
    `${API_BASE_URL}/api/v1/documents`,
    `${API_BASE_URL}/api/v1/documents/resume%2Fa`,
    `${API_BASE_URL}/api/v1/documents/resume%2Fa/chunks`,
  ]);
});

test("semantic search posts query and top_k", async () => {
  let requestedUrl = "";
  let requestedInit: RequestInit | undefined;
  globalThis.fetch = async (input, init) => {
    requestedUrl = String(input);
    requestedInit = init;
    return new Response(JSON.stringify([]), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };

  await api.searchDocuments("FastAPI 后端经验", 3);

  assert.equal(requestedUrl, `${API_BASE_URL}/api/v1/retrieval/search`);
  assert.equal(requestedInit?.method, "POST");
  assert.equal(requestedInit?.body, JSON.stringify({ query: "FastAPI 后端经验", top_k: 3 }));
});
