import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";


// Metrics
const successRate = new Rate("checkout_success_rate");
const businessFailureRate = new Rate("checkout_business_failure_rate");
const inventoryFailureRate = new Rate("checkout_inventory_failure_rate");
const serverFailureRate = new Rate("checkout_server_failure_rate");

const successCount = new Counter("checkout_success_count");
const businessFailureCount = new Counter("checkout_business_failure_count");
const inventoryFailureCount = new Counter("checkout_inventory_failure_count");
const serverFailureCount = new Counter("checkout_server_failure_count");
const authFailureCount = new Counter("checkout_auth_failure_count");
const validationFailureCount = new Counter("checkout_validation_failure_count");

const checkoutDuration = new Trend("checkout_duration");


// Env
const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";
const CHECKOUT_PATH = __ENV.CHECKOUT_PATH || "/api/checkout/create/";
const ACCESS_TOKEN = __ENV.ACCESS_TOKEN || "";

const PRODUCT_ID = __ENV.PRODUCT_ID || "";
const QUANTITY = Number(__ENV.QUANTITY || 1);

// important for correctness expectation
const INITIAL_STOCK = Number(__ENV.INITIAL_STOCK || 0);

// address strings
const SHIPPING_ADDRESS =
  __ENV.SHIPPING_ADDRESS || "Flat 101, Road No 12, Hyderabad, Telangana";
const BILLING_ADDRESS =
  __ENV.BILLING_ADDRESS || "Flat 101, Road No 12, Hyderabad, Telangana";

// how aggressive to be
const VUS = Number(__ENV.VUS || 50);
const DURATION = __ENV.DURATION || "30s";


// Options
export const options = {
  scenarios: {
    checkout_correctness: {
      executor: "constant-vus",
      vus: VUS,
      duration: DURATION,
      gracefulStop: "5s",
    },
  },
  thresholds: {
    checkout_server_failure_rate: ["rate==0"],
    // correctness test: business failures are expected after stock is exhausted
    // so we do NOT threshold on total failure rate
  },
};


// Helpers
function authHeaders() {
  const headers = {
    "Content-Type": "application/json",
  };

  if (ACCESS_TOKEN) {
    headers["Authorization"] = `Bearer ${ACCESS_TOKEN}`;
  }

  return headers;
}

function buildPayload() {
  return JSON.stringify({
    items: [
      {
        product_id: PRODUCT_ID,
        quantity: QUANTITY,
      },
    ],
    shipping_address: SHIPPING_ADDRESS,
    billing_address: BILLING_ADDRESS,
  });
}

function safeParseJson(res) {
  try {
    return res.json();
  } catch (e) {
    return null;
  }
}

function getResponseCode(parsed) {
  if (!parsed || typeof parsed !== "object") return "";
  return parsed.code ? String(parsed.code).toUpperCase() : "";
}

function getResponseMessage(parsed, rawBody) {
  if (!parsed) return String(rawBody || "").toLowerCase();
  if (typeof parsed === "string") return parsed.toLowerCase();

  if (parsed.message) return String(parsed.message).toLowerCase();
  if (parsed.detail) return String(parsed.detail).toLowerCase();
  if (parsed.error) return String(parsed.error).toLowerCase();

  return JSON.stringify(parsed).toLowerCase();
}

function isInventoryFailure(code, message) {
  return (
    code === "INSUFFICIENT_STOCK" ||
    code === "INVENTORY_RESERVATION_FAILED" ||
    message.includes("stock") ||
    message.includes("inventory") ||
    message.includes("insufficient quantity") ||
    message.includes("insufficient stock") ||
    message.includes("out of stock") ||
    message.includes("reservation failed") ||
    message.includes("not enough quantity")
  );
}

function isValidationFailure(code, message) {
  return (
    code === "VALIDATION_ERROR" ||
    code === "INVALID_INPUT" ||
    message.includes("required") ||
    message.includes("invalid") ||
    message.includes("blank") ||
    message.includes("null") ||
    message.includes("this field")
  );
}

function classify(res, parsed) {
  if (res.status === 201) return "success";
  if (res.status === 401 || res.status === 403) return "auth_failure";
  if (res.status >= 500) return "server_error";

  if (res.status === 400) {
    const code = getResponseCode(parsed);
    const message = getResponseMessage(parsed, res.body);

    if (isInventoryFailure(code, message)) return "inventory_failure";
    if (isValidationFailure(code, message)) return "validation_failure";
    return "business_failure";
  }

  return "unknown_error";
}


// Setup
export function setup() {
  if (!PRODUCT_ID) {
    throw new Error("PRODUCT_ID is required");
  }

  if (!ACCESS_TOKEN) {
    console.warn("ACCESS_TOKEN not provided. Protected endpoint may return 401.");
  }

  if (!INITIAL_STOCK) {
    console.warn(
      "INITIAL_STOCK not provided. You can still run the test, but final correctness expectation will be manual."
    );
  }

  return {
    initialStock: INITIAL_STOCK,
  };
}


// Main
export default function () {
  const url = `${BASE_URL}${CHECKOUT_PATH}`;
  const payload = buildPayload();

  const res = http.post(url, payload, {
    headers: authHeaders(),
    timeout: "30s",
    tags: {
      endpoint: "checkout_create",
      test_type: "correctness_single_product",
    },
  });

  checkoutDuration.add(res.timings.duration);

  const parsed = safeParseJson(res);
  const type = classify(res, parsed);

  check(res, {
    "status is expected": (r) =>
      [201, 400, 401, 403, 500, 502, 503, 504].includes(r.status),
  });

  switch (type) {
    case "success":
      successRate.add(true);
      businessFailureRate.add(false);
      inventoryFailureRate.add(false);
      serverFailureRate.add(false);
      successCount.add(1);
      break;

    case "inventory_failure":
      successRate.add(false);
      businessFailureRate.add(true);
      inventoryFailureRate.add(true);
      serverFailureRate.add(false);
      businessFailureCount.add(1);
      inventoryFailureCount.add(1);
      break;

    case "validation_failure":
      successRate.add(false);
      businessFailureRate.add(true);
      inventoryFailureRate.add(false);
      serverFailureRate.add(false);
      businessFailureCount.add(1);
      validationFailureCount.add(1);
      console.error(`Validation failure: status=${res.status}, body=${res.body}`);
      break;

    case "business_failure":
      successRate.add(false);
      businessFailureRate.add(true);
      inventoryFailureRate.add(false);
      serverFailureRate.add(false);
      businessFailureCount.add(1);
      console.error(`Business failure: status=${res.status}, body=${res.body}`);
      break;

    case "auth_failure":
      successRate.add(false);
      businessFailureRate.add(false);
      inventoryFailureRate.add(false);
      serverFailureRate.add(false);
      authFailureCount.add(1);
      console.error(`Auth failure: status=${res.status}, body=${res.body}`);
      break;

    case "server_error":
      successRate.add(false);
      businessFailureRate.add(false);
      inventoryFailureRate.add(false);
      serverFailureRate.add(true);
      serverFailureCount.add(1);
      console.error(`Server error: status=${res.status}, body=${res.body}`);
      break;

    default:
      successRate.add(false);
      businessFailureRate.add(false);
      inventoryFailureRate.add(false);
      serverFailureRate.add(true);
      serverFailureCount.add(1);
      console.error(`Unknown error: status=${res.status}, body=${res.body}`);
      break;
  }

  // keep near-zero sleep to maximize overlap on the same row
  sleep(0.05);
}


// Summary
export function handleSummary(data) {
  const success = data.metrics.checkout_success_count
    ? data.metrics.checkout_success_count.values.count
    : 0;

  const inventoryFailures = data.metrics.checkout_inventory_failure_count
    ? data.metrics.checkout_inventory_failure_count.values.count
    : 0;

  const businessFailures = data.metrics.checkout_business_failure_count
    ? data.metrics.checkout_business_failure_count.values.count
    : 0;

  const serverFailures = data.metrics.checkout_server_failure_count
    ? data.metrics.checkout_server_failure_count.values.count
    : 0;

  const authFailures = data.metrics.checkout_auth_failure_count
    ? data.metrics.checkout_auth_failure_count.values.count
    : 0;

  const validationFailures = data.metrics.checkout_validation_failure_count
    ? data.metrics.checkout_validation_failure_count.values.count
    : 0;

  let interpretation = "";
  interpretation += `\nCorrectness summary:\n`;
  interpretation += `- Successful checkouts: ${success}\n`;
  interpretation += `- Inventory failures: ${inventoryFailures}\n`;
  interpretation += `- Other business failures: ${businessFailures - inventoryFailures}\n`;
  interpretation += `- Validation failures: ${validationFailures}\n`;
  interpretation += `- Auth failures: ${authFailures}\n`;
  interpretation += `- Server failures: ${serverFailures}\n`;

  if (INITIAL_STOCK > 0) {
    const maxExpectedSuccess = Math.floor(INITIAL_STOCK / QUANTITY);
    interpretation += `- Initial stock: ${INITIAL_STOCK}\n`;
    interpretation += `- Quantity per checkout: ${QUANTITY}\n`;
    interpretation += `- Max expected successful checkouts: ${maxExpectedSuccess}\n`;

    if (success <= maxExpectedSuccess && serverFailures === 0) {
      interpretation += `- Result: PASS from a no-oversell perspective (successful checkouts did not exceed theoretical stock limit).\n`;
    } else if (success > maxExpectedSuccess) {
      interpretation += `- Result: FAIL from a no-oversell perspective (successful checkouts exceeded theoretical stock limit).\n`;
    } else {
      interpretation += `- Result: Review manually.\n`;
    }
  } else {
    interpretation += `- INITIAL_STOCK not provided, so no automatic no-oversell assertion was made.\n`;
  }

  return {
    stdout: `${JSON.stringify(data, null, 2)}\n${interpretation}`,
  };
}