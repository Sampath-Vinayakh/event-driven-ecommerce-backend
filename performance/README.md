# Performance Testing

This project uses k6 to validate scalability, caching effectiveness, and concurrency correctness.

---

## Scripts

* `checkout_performance.js` → multi-product scalability test
* `checkout_correctness.js` → single-product contention test
* `product_detail.js` → read path performance (cache vs DB)

---

## Product Detail API (Cache Testing)

This test evaluates the impact of caching on read performance.

### Supported Modes

* `warm_cache` → cache is primed before test
* `cold_cache` → cache is empty (manually clear before test)
* `no_cache` → cache disabled in application

---

## Required Environment Variables

| Variable     | Description             | Example                     |
| ------------ | ----------------------- | --------------------------- |
| `BASE_URL`   | Backend base URL        | `http://127.0.0.1:8000`     |
| `PRODUCT_ID` | Product ID to test      | `uuid`                      |
| `TEST_MODE`  | Cache mode              | `warm_cache` / `cold_cache` |
| `VUS`        | Number of virtual users | `25`, `50`, `100`           |
| `DURATION`   | Test duration           | `2m`                        |

---

## How to Run

### 1️⃣ Warm Cache Test

```bash
k6 run performance/k6/product_detail.js \
  -e BASE_URL=http://127.0.0.1:8000 \
  -e PRODUCT_ID=<product_uuid> \
  -e TEST_MODE=warm_cache \
  -e VUS=100 \
  -e DURATION=2m
```

---

### 2️⃣ Cold Cache Test

⚠️ Clear Redis before running

```bash
k6 run performance/k6/product_detail.js \
  -e BASE_URL=http://127.0.0.1:8000 \
  -e PRODUCT_ID=<product_uuid> \
  -e TEST_MODE=cold_cache \
  -e VUS=100 \
  -e DURATION=2m
```

---

### 3️⃣ No Cache Test

⚠️ Disable caching in application settings

```bash
k6 run performance/k6/product_detail.js \
  -e BASE_URL=http://127.0.0.1:8000 \
  -e PRODUCT_ID=<product_uuid> \
  -e TEST_MODE=no_cache \
  -e VUS=100 \
  -e DURATION=2m
```

---

## Notes

* For accurate cold cache testing, ensure Redis is flushed:

  ```bash
  docker exec -it redis redis-cli FLUSHALL
  ```
* Warm cache mode automatically primes cache using a pre-request
* No cache mode requires disabling cache in Django settings

---

## Goal of These Tests

* Measure **read scalability**
* Compare **DB vs cache performance**
* Validate **tail latency improvements**
* Ensure **system stability under concurrent reads**
