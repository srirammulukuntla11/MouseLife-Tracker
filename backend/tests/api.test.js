import assert from "assert";
import mongoose from "mongoose";
import { app, startServer } from "../src/server.js";
import { Mouse } from "../src/models/Mouse.js";
import { SyncBatch } from "../src/models/SyncBatch.js";
import { DailyStatistic } from "../src/models/DailyStatistic.js";

const PORT = 5001; // Test port

async function runTests() {
  console.log("=== Starting Backend & MongoDB API Integration Tests ===");
  const server = await startServer(PORT);

  try {
    const baseUrl = `http://127.0.0.1:${PORT}/api`;

    // 1. Health check
    console.log("-> Testing GET /api/health");
    const healthRes = await fetch(`${baseUrl}/health`);
    assert.strictEqual(healthRes.status, 200);
    const healthData = await healthRes.json();
    assert.strictEqual(healthData.status, "ok");
    console.log("   [PASS] Health check OK");

    // 2. Fetch default Portronics mouse
    console.log("-> Testing GET /api/mice/portronics-default-01");
    const mouseRes = await fetch(`${baseUrl}/mice/portronics-default-01`);
    assert.strictEqual(mouseRes.status, 200);
    const mouseData = await mouseRes.json();
    assert.strictEqual(mouseData.success, true);
    assert.strictEqual(mouseData.data.mouseId, "portronics-default-01");
    assert.strictEqual(mouseData.data.ratedClicks, 3000000);
    console.log("   [PASS] Default Portronics mouse auto-provisioned correctly");

    const initialTotal = mouseData.data.totalClicks;

    // 3. Batch synchronization test
    console.log("-> Testing POST /api/clicks/sync with atomic batch");
    const testBatchId = `test-batch-${Date.now()}`;
    const syncRes = await fetch(`${baseUrl}/clicks/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        batchId: testBatchId,
        mouseId: "portronics-default-01",
        clientSessionId: "test-session-integration",
        leftClicks: 50,
        rightClicks: 20,
        middleClicks: 5,
        totalClicks: 75,
        timestamp: new Date().toISOString(),
      }),
    });

    assert.strictEqual(syncRes.status, 200);
    const syncData = await syncRes.json();
    assert.strictEqual(syncData.success, true);
    assert.strictEqual(syncData.duplicate, false);
    assert.strictEqual(syncData.mouse.totalClicks, initialTotal + 75);
    assert.strictEqual(syncData.mouse.leftClicks >= 50, true);
    console.log("   [PASS] Batch synchronization incremented clicks atomically");

    // 4. Duplicate Sync Idempotency Test
    console.log("-> Testing Duplicate Sync Protection (sending SAME batchId again)");
    const dupRes = await fetch(`${baseUrl}/clicks/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        batchId: testBatchId,
        mouseId: "portronics-default-01",
        clientSessionId: "test-session-integration",
        leftClicks: 50,
        rightClicks: 20,
        middleClicks: 5,
        totalClicks: 75,
        timestamp: new Date().toISOString(),
      }),
    });

    assert.strictEqual(dupRes.status, 200);
    const dupData = await dupRes.json();
    assert.strictEqual(dupData.success, true);
    assert.strictEqual(dupData.duplicate, true, "Must flag batch as duplicate");
    // Verify totalClicks has NOT been incremented a second time
    assert.strictEqual(dupData.mouse.totalClicks, initialTotal + 75, "Total clicks must NOT double-count");
    console.log("   [PASS] Duplicate sync detected and prevented double-counting!");

    // 5. Daily statistics test
    console.log("-> Testing GET /api/mice/portronics-default-01/statistics/daily");
    const dailyRes = await fetch(`${baseUrl}/mice/portronics-default-01/statistics/daily`);
    assert.strictEqual(dailyRes.status, 200);
    const dailyData = await dailyRes.json();
    assert.strictEqual(dailyData.success, true);
    assert.strictEqual(Array.isArray(dailyData.data), true);
    assert.strictEqual(dailyData.data.length >= 1, true);
    const todayStat = dailyData.data[dailyData.data.length - 1];
    assert.strictEqual(todayStat.totalClicks >= 75, true);
    console.log("   [PASS] Daily statistics verified");

    // 6. Lifespan calculation check
    console.log("-> Testing Lifespan Calculations");
    const updatedMouseRes = await fetch(`${baseUrl}/mice/portronics-default-01`);
    const finalMouse = (await updatedMouseRes.json()).data;
    assert.strictEqual(finalMouse.remainingClicks, 3000000 - finalMouse.totalClicks);
    assert.strictEqual(typeof finalMouse.lifeUsedPercentage, "number");
    assert.strictEqual(finalMouse.remainingClicks >= 0, true);
    console.log(`   [PASS] Lifespan: ${finalMouse.totalClicks} used, ${finalMouse.remainingClicks} remaining (${finalMouse.lifeUsedPercentage}%)`);

    // 7. Session Start / End test
    console.log("-> Testing Session Lifecycle");
    const testSessionId = `test-sess-${Date.now()}`;
    const startRes = await fetch(`${baseUrl}/sessions/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId: testSessionId,
        mouseId: "portronics-default-01",
      }),
    });
    assert.strictEqual(startRes.status, 201);

    const endRes = await fetch(`${baseUrl}/sessions/end`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId: testSessionId,
        duration: 120,
        totalClicks: 25,
      }),
    });
    assert.strictEqual(endRes.status, 200);
    console.log("   [PASS] Session start and end tracking verified");

    console.log("\n>>> ALL BACKEND & MONGODB INTEGRATION TESTS PASSED! <<<");
  } finally {
    server.close();
    await mongoose.disconnect();
  }
}

runTests().catch((err) => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
