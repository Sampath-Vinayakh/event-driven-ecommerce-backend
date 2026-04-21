import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

// Custom metrics
const checkoutSuccessRate = new Rate("checkout_success_rate");
const checkoutFailureRate = new Rate("checkout_failure_rate");

const businessFailureRate = new Rate("checkout_business_failure_rate");
const serverFailureRate = new Rate("checkout_server_failure_rate");
const authFailureRate = new Rate("checkout_auth_failure_rate");
const validationFailureRate = new Rate("checkout_validation_failure_rate");

const checkoutDuration = new Trend("checkout_duration");
const checkoutWaiting = new Trend("checkout_waiting_time");

// Counters
const successCount = new Counter("checkout_success_count");
const businessFailureCount = new Counter("checkout_business_failure_count");
const serverFailureCount = new Counter("checkout_server_failure_count");
const authFailureCount = new Counter("checkout_auth_failure_count");
const validationFailureCount = new Counter("checkout_validation_failure_count");

const inventoryFailureCount = new Counter("checkout_inventory_failure_count");
const paymentFailureCount = new Counter("checkout_payment_failure_count");
const addressFailureCount = new Counter("checkout_address_failure_count");
const unknownBusinessFailureCount = new Counter("checkout_unknown_business_failure_count");

// Environment variables


const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";
const CHECKOUT_PATH = __ENV.CHECKOUT_PATH || "/api/checkout/create/";
const ACCESS_TOKEN = __ENV.ACCESS_TOKEN || "";

const SHIPPING_ADDRESS =
  __ENV.SHIPPING_ADDRESS || "Flat 101, Road No 12, Hyderabad, Telangana";
const BILLING_ADDRESS =
  __ENV.BILLING_ADDRESS || "Flat 101, Road No 12, Hyderabad, Telangana";

const PRODUCT_ID = __ENV.PRODUCT_ID || "";
const QUANTITY = Number(__ENV.QUANTITY || 1);

const SAME_PRODUCT_FOR_ALL =
  (__ENV.SAME_PRODUCT_FOR_ALL || "true").toLowerCase() === "true";

const PRODUCT_IDS = (__ENV.PRODUCT_IDS || "")
  .split(",")
  .map((x) => x.trim())
  .filter(Boolean);


export const options = {
  scenarios: {
    checkout_load: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "1m", target: 25 },
        { duration: "1m", target: 50 },
        { duration: "2m", target: 100 },
        { duration: "2m", target: 150 },
        { duration: "1m", target: 0 },
      ],
      gracefulRampDown: "20s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.05"],
    checkout_server_failure_rate: ["rate<0.02"],
    checkout_duration: ["p(95)<2000", "p(99)<3000"],
    http_req_duration: ["p(95)<2000", "p(99)<3000"],
  },
};


function authHeaders() {
  const headers = {
    "Content-Type": "application/json",
  };

  if (ACCESS_TOKEN) {
    headers["Authorization"] = `Bearer ${ACCESS_TOKEN}`;
  }

  return headers;
}

function pickProductId() {
  if (SAME_PRODUCT_FOR_ALL && PRODUCT_ID) {
    return PRODUCT_ID;
  }

  if (PRODUCT_IDS.length > 0) {
    return PRODUCT_IDS[Math.floor(Math.random() * PRODUCT_IDS.length)];
  }

  return PRODUCT_ID;
}

function buildPayload() {
  const productId = pickProductId();
  return JSON.stringify({
    items: [
      {
        product_id: productId,
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
  if (!parsed || typeof parsed !== "object") {
    return "";
  }

  if (parsed.code) {
    return String(parsed.code).toUpperCase();
  }

  return "";
}

function getResponseMessage(parsed, body) {
  if (!parsed) {
    return (body || "").toString().toLowerCase();
  }

  if (typeof parsed === "string") {
    return parsed.toLowerCase();
  }

  // Use "message" first because you said business validation is there
  if (parsed.message) {
    return String(parsed.message).toLowerCase();
  }

  if (parsed.detail) {
    return String(parsed.detail).toLowerCase();
  }

  if (parsed.error) {
    return String(parsed.error).toLowerCase();
  }

  return JSON.stringify(parsed).toLowerCase();
}

function isInventoryFailure(code, message) {
  return (
    code === "INSUFFICIENT_STOCK" ||
    code === "INVENTORY_RESERVATION_FAILED" ||
    message.includes("stock") ||
    message.includes("inventory") ||
    message.includes("not enough quantity") ||
    message.includes("insufficient quantity") ||
    message.includes("insufficient stock") ||
    message.includes("out of stock") ||
    message.includes("reservation failed")
  );
}

function isAddressFailure(code, message) {
  return (
    code === "INVALID_ADDRESS" ||
    code === "ADDRESS_REQUIRED" ||
    message.includes("address") ||
    message.includes("shipping address") ||
    message.includes("billing address")
  );
}

function isPaymentFailure(code, message) {
  return (
    code === "PAYMENT_FAILED" ||
    code === "PAYMENT_PROVIDER_ERROR" ||
    code === "CHECKOUT_SESSION_FAILED" ||
    message.includes("payment") ||
    message.includes("razorpay") ||
    message.includes("checkout session")
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
    message.includes("must be") ||
    message.includes("this field")
  );
}

function classifyError(res, parsed) {
  if (res.status === 201) {
    return "success";
  }

  if (res.status === 401 || res.status === 403) {
    return "auth_failure";
  }

  if (res.status >= 500) {
    return "server_error";
  }

  if (res.status === 400) {
    const code = getResponseCode(parsed);
    const message = getResponseMessage(parsed, res.body);

    if (isInventoryFailure(code, message)) {
      return "inventory_failure";
    }

    if (isAddressFailure(code, message)) {
      return "address_failure";
    }

    if (isPaymentFailure(code, message)) {
      return "payment_failure";
    }

    if (isValidationFailure(code, message)) {
      return "validation_failure";
    }

    return "business_failure";
  }

  return "unknown_error";
}


// Setup
export function setup() {
  if (!PRODUCT_ID && PRODUCT_IDS.length === 0) {
    throw new Error("Provide PRODUCT_ID or PRODUCT_IDS env variable.");
  }

  if (!ACCESS_TOKEN) {
    console.warn("ACCESS_TOKEN not provided. Protected endpoint may return 401.");
  }

  return {};
}


// Main
export default function () {
  const url = `${BASE_URL}${CHECKOUT_PATH}`;
  const payload = buildPayload();

  const params = {
    headers: authHeaders(),
    tags: {
      endpoint: "checkout_create",
    },
    timeout: "30s",
  };

  const res = http.post(url, payload, params);

  checkoutDuration.add(res.timings.duration);
  checkoutWaiting.add(res.timings.waiting);

  const parsed = safeParseJson(res);
  const errorType = classifyError(res, parsed);

  const hasOrderId = parsed && (parsed.order_id || parsed.id);
  const hasPaymentData =
    parsed &&
    (parsed.payment_id ||
      parsed.provider_order_id ||
      parsed.key);


  check(res, {
    "status is expected": (r) =>
      [201, 400, 401, 403, 500, 502, 503, 504].includes(r.status),
    "success response has order/payment data": (r) =>
      r.status !== 201 || (hasOrderId && hasPaymentData),
  });

  switch (errorType) {
    case "success":
      checkoutSuccessRate.add(true);
      checkoutFailureRate.add(false);
      businessFailureRate.add(false);
      serverFailureRate.add(false);
      authFailureRate.add(false);
      validationFailureRate.add(false);
      successCount.add(1);
      break;

    case "inventory_failure":
      checkoutSuccessRate.add(false);
      checkoutFailureRate.add(true);
      businessFailureRate.add(true);
      serverFailureRate.add(false);
      authFailureRate.add(false);
      validationFailureRate.add(false);
      businessFailureCount.add(1);
      inventoryFailureCount.add(1);
      break;

    case "payment_failure":
      checkoutSuccessRate.add(false);
      checkoutFailureRate.add(true);
      businessFailureRate.add(true);
      serverFailureRate.add(false);
      authFailureRate.add(false);
      validationFailureRate.add(false);
      businessFailureCount.add(1);
      paymentFailureCount.add(1);
      break;

    case "address_failure":
      checkoutSuccessRate.add(false);
      checkoutFailureRate.add(true);
      businessFailureRate.add(true);
      serverFailureRate.add(false);
      authFailureRate.add(false);
      validationFailureRate.add(false);
      businessFailureCount.add(1);
      addressFailureCount.add(1);
      break;

    case "validation_failure":
      checkoutSuccessRate.add(false);
      checkoutFailureRate.add(true);
      businessFailureRate.add(true);
      serverFailureRate.add(false);
      authFailureRate.add(false);
      validationFailureRate.add(true);
      businessFailureCount.add(1);
      validationFailureCount.add(1);
      break;

    case "business_failure":
      checkoutSuccessRate.add(false);
      checkoutFailureRate.add(true);
      businessFailureRate.add(true);
      serverFailureRate.add(false);
      authFailureRate.add(false);
      validationFailureRate.add(false);
      businessFailureCount.add(1);
      unknownBusinessFailureCount.add(1);
      break;

    case "auth_failure":
      checkoutSuccessRate.add(false);
      checkoutFailureRate.add(true);
      businessFailureRate.add(false);
      serverFailureRate.add(false);
      authFailureRate.add(true);
      validationFailureRate.add(false);
      authFailureCount.add(1);
      console.error(`Auth failure: status=${res.status}, body=${res.body}`);
      break;

    case "server_error":
      checkoutSuccessRate.add(false);
      checkoutFailureRate.add(true);
      businessFailureRate.add(false);
      serverFailureRate.add(true);
      authFailureRate.add(false);
      validationFailureRate.add(false);
      serverFailureCount.add(1);
      console.error(`Server error: status=${res.status}, body=${res.body}`);
      break;

    default:
      checkoutSuccessRate.add(false);
      checkoutFailureRate.add(true);
      businessFailureRate.add(false);
      serverFailureRate.add(true);
      authFailureRate.add(false);
      validationFailureRate.add(false);
      serverFailureCount.add(1);
      console.error(`Unknown error type: status=${res.status}, body=${res.body}`);
      break;
  }

  sleep(0.2);
}