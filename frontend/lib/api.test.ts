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
