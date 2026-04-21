import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const PRODUCT_ID = __ENV.PRODUCT_ID;
const TEST_MODE = __ENV.TEST_MODE || 'warm_cache';

if (!PRODUCT_ID) {
  throw new Error('PRODUCT_ID env variable is required');
}

export const options = {
  scenarios: {
    product_detail_read: {
      executor: 'constant-vus',
      vus: Number(__ENV.VUS || 25),
      duration: __ENV.DURATION || '2m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1000', 'p(99)<1500'],
    checks: ['rate>0.99'],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

function getProductDetail() {
  const url = `${BASE_URL}/api/products/${PRODUCT_ID}/`;
  const res = http.get(url, {
    tags: {
      endpoint: 'product-detail',
      mode: TEST_MODE,
    },
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response has body': (r) => r.body && r.body.length > 0,
  });

  return res;
}

export function setup() {
  const url = `${BASE_URL}/api/products/${PRODUCT_ID}/`;

  console.log(`Running setup for TEST_MODE=${TEST_MODE}`);

  if (TEST_MODE === 'warm_cache') {
    const warmRes = http.get(url, {
      tags: { endpoint: 'product-detail-warmup' },
    });

    check(warmRes, {
      'warmup status is 200': (r) => r.status === 200,
    });

    console.log('Warm cache primed with one pre-request.');
  }

  if (TEST_MODE === 'cold_cache') {
    console.log(
      'Cold cache mode selected. Make sure Redis cache is cleared manually right before running the test.'
    );
  }

  if (TEST_MODE === 'no_cache') {
    console.log(
      'No cache mode selected. Make sure cache usage is disabled in the application settings/code.'
    );
  }

  return { mode: TEST_MODE };
}

export default function () {
  getProductDetail();
  sleep(1);
}