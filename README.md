#  Event-Driven E-commerce Backend

A production-style backend system built with Django that simulates how real-world e-commerce platforms handle **orders, payments, inventory, and asynchronous workflows**.

This project goes beyond CRUD APIs it focuses on **system design, scalability, and reliability** using an event-driven architecture.

---

##  What This Project Is About

This backend models a real checkout flow:

- Users place orders
- Inventory is reserved safely
- Payments are processed via webhooks
- Events are published asynchronously
- Notifications are triggered independently

Instead of tightly coupling everything, the system uses **events and background workers**, making it closer to how modern scalable systems are built.

---

##  Tech Stack

- **Backend:** Django + Django REST Framework  
- **Database:** PostgreSQL  
- **Cache:** Redis (cache-aside pattern)  
- **Async Tasks:** Celery + Celery Beat  
- **Event Streaming:** Kafka  
- **Payments:** Razorpay (webhook-driven)  
- **Auth:** JWT (SimpleJWT)  
- **Containerization:** Docker + Docker Compose  

##  Checkout Flow (Core Logic)

###  Success Flow

```
Checkout
 → Order created (PENDING)
 → Inventory reserved
 → Payment session created
 → Webhook received
 → Payment marked SUCCESS
 → Inventory deducted
 → Order confirmed
 → Event published
 → Notification sent
```

###  Failure Flow

```
Checkout
 → Order created
 → Inventory reserved
 → Payment fails
 → Inventory released
 → Order marked FAILED
 → Event published
```

---

##  Payments (Real-world Approach)

- Payment sessions are created **only in backend**
- Frontend never decides payment success
- **Webhooks are the source of truth**

---

##  Inventory Design

```
available → reserved → deducted
```

Prevents overselling during concurrent orders.

---

##  Event-Driven System

Uses Transactional Outbox Pattern:

1. Write event to DB inside transaction
2. After commit → Celery publishes event
3. Kafka distributes event
4. Consumers process independently

---

##  Running Locally

```bash
docker compose up --build
```

---

##  Environment Setup

An example environment file is already provided:

###  Setup Steps

1. Copy the file:
   ```bash
   cp .env.local .env
   
---

## Performance & Reliability Benchmarks

### Product Detail API

The product detail endpoint was load-tested with k6 under concurrent traffic to evaluate read-path scalability and caching effectiveness.

#### 🔹 100 Concurrent Users (Key Results)

| Scenario   | Avg Latency | p95       | p99       | RPS   | Success Rate |
| ---------- | ----------- | --------- | --------- | ----- | ------------ |
| No Cache   | 358.68 ms   | 577.43 ms | 865.94 ms | 73.16 | 100%         |
| Cold Cache | 6.55 ms     | 14.18 ms  | 44 ms     | 99.01 | 100%         |
| Warm Cache | 6.15 ms     | 12.47 ms  | 46.08 ms  | 99.19 | 100%         |

#### 🔍 Key Observations

* ~98% reduction in p95 latency (577 ms → ~12 ms) with caching
* Throughput improved from ~73 req/s → ~99 req/s (~35% increase)
* Warm cache eliminated latency spikes and stabilized tail latency
* Maintained 100% success rate across all scenarios

#### 💡 What this demonstrates

* Cache-aside pattern significantly improves scalability
* Database bottlenecks are eliminated under high concurrency
* System maintains consistent performance under heavy read load

---

### Checkout Correctness Under Concurrency

The checkout flow was tested under high contention using a single product with limited stock.

#### Test Setup

* 50 concurrent users
* Single product
* Initial stock: 20

#### Results

* 20 successful checkouts (exact stock limit)
* 0 overselling occurrences
* 0 server failures

#### What this demonstrates

* Row-level locking (`select_for_update`) ensures correctness
* Transactions prevent race conditions
* System fails safely after stock exhaustion

---

### Checkout Scalability Under Load

The checkout API was tested using multiple products with sufficient stock to minimize contention and measure system reliability.

#### Test Setup

* Up to 150 concurrent users
* ~7 minutes sustained load
* Multi-product distribution with sufficient inventory

#### Results

* 17,638 successful checkouts
* ~42 requests/sec throughput
* 100% success rate
* 0% server failures

#### What this demonstrates

* System sustains high-volume transactional load
* Checkout flow remains stable under heavy concurrency
* No crashes or unexpected failures during sustained execution

---

## Key Reliability Takeaways

* Zero server errors under checkout load
* Strong concurrency safety (no overselling)
* Stable transactional behavior under write-heavy operations
* Significant read-path optimization using Redis caching
* Reliable end-to-end system performance under sustained traffic

---

##  Key Learnings

- Event-driven systems
- Idempotency
- Transactions
- Race condition handling
- Webhook-based design
---

##  Future Improvements

- DLQ for Kafka
- Monitoring (Prometheus)
- Production deployment setup

---

