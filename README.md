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

