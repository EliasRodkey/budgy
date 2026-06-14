import { useMockMode } from "../store/mockMode";

// API tests exercise the mock-data branches of api/* functions, which are
// gated behind isMockMode. Force it on for the test environment so relative
// fetch() calls (invalid in Node without a base URL) are never reached.
// Some test files vi.mock this store with a minimal stub (no setMockMode) to
// exercise the real-fetch branch — skip those rather than throwing.
useMockMode.getState().setMockMode?.(true);
