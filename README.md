# MMO Fishing Game gRPC Prototype

This repository contains a Python gRPC prototype for a fishing-game service with
two checked-in deployment variants:

- `server/`: a six-instance Docker Compose deployment using the same service on
  ports `50051` through `50056`
- `servermono/`: an alternate baseline variant with a separate copy of the
  runtime and compose files

The current baseline is a prototype service surface. The checked-in runtime does
not yet implement Project 3 consensus logic.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
  - [`client/`](#client)
  - [`server/`](#server)
  - [`servermono/`](#servermono)
- [Running the Code](#running-the-code)
  - [Client](#client-1)
  - [6‑Node Server Cluster](#6-node-server-cluster)
  - [Single‑Node (Mono) Server](#single-node-mono-server)
- [Performance Benchmarks](#performance-benchmarks)
  - [6‑Node System](#6-node-system)
  - [1‑Node System](#1-node-system)
- [gRPC Service Definition](#grpc-service-definition)
- [Future Work](#future-work)
- [License](#license)

---

## Overview

- **Runtime** - Python gRPC server and client with generated protobuf stubs.
- **Cluster variant** - `server/` starts six identical service instances on
  separate ports.
- **Baseline state** - user and inventory data are stored in memory inside each
  running server process.
- **Testing** - `fishing_test.js` contains a k6 load-test script for the
  baseline service surface.

---

## Project Structure

```
.
├── client/          # Simple test client (Python)
├── server/          # 6‑node cluster implementation
│   └── docker-compose.yml
├── servermono/      # Alternate baseline server variant
│   └── docker-compose.yml
├── fishing_test.js  # k6 load‑testing script
└── fishing.proto    # gRPC service definitions
```

### `client/`

A minimal interactive Python client that can:
- log in
- send location updates
- start a fishing stream
- list users
- stream current-user counts
- fetch inventory
- fetch the configured image bytes

**Run**

```bash
cd client
python3 client.py
```

### `server/`

A six-service Docker Compose setup. Each service runs `server.py` with a unique
port and image path. Each running process keeps its own in-memory state.

**Run**

```bash
cd server
docker compose up
```

### `servermono/`

An alternate baseline server variant stored in its own directory. Its compose
file defines one service named `fishing-cluster` and exposes ports
`50051-50056`.

**Run**

```bash
cd servermono
docker compose up
```

---

## Running the Code

1. **Prerequisites**

   * Docker & Docker Compose
   * Python 3 with `grpcio` and `protobuf` available for the client

2. **Start the Servers**

   ```bash
   # 6‑node cluster
   cd server && docker compose up

   # or single node
   cd servermono && docker compose up
   ```

3. **Run the Client**

   ```bash
   cd client && python3 client.py
   ```

4. **Load‑Test with k6**

   ```bash
   brew install k6          # macOS; adjust for your OS
   k6 run fishing_test.js
   ```

---

## Performance Benchmarks

### 6‑Node System

```
iteration_duration...........: avg=1.01s  min=1s       med=1.01s  max=1.05s   p(90)=1.02s   p(95)=1.03s  
iterations...................: 1000   98.283894/s
vus..........................: 100    min=100      max=100
grpc_req_duration............: avg=7.73ms  min=806.29µs med=6.65ms max=31.33ms p(90)=14.17ms p(95)=17.01ms
grpc_streams.................: 1000   98.283894/s
grpc_streams_msgs_received...: 1000   98.283894/s
grpc_streams_msgs_sent.......: 5000   491.419472/s
```

### 1‑Node System

```
iteration_duration...........: avg=1.02s  min=1s       med=1s     max=1.2s     p(90)=1.08s   p(95)=1.1s  
iterations...................: 1000   96.866251/s
vus..........................: 100    min=100      max=100
grpc_req_duration............: avg=13.4ms  min=596.66µs med=3.61ms max=176.58ms p(90)=59.39ms p(95)=79.6ms
grpc_streams.................: 1000   96.866251/s
grpc_streams_msgs_received...: 1000   96.866251/s
grpc_streams_msgs_sent.......: 5000   484.331254/s
```

> **Takeaway** – Horizontal scaling reduces request latency by ~40 % and increases throughput.

---

## gRPC Service Definition

```proto
syntax = "proto3";

package fishingapp;

import "google/protobuf/empty.proto";

service FishingService {
  rpc ListUsers (google.protobuf.Empty) returns (stream User);
  rpc Login (LoginRequest) returns (LoginResponse);
  rpc UpdateLocation (stream UpdateLocationRequest) returns (UpdateLocationResponse);
  rpc StartFishing (StartFishingRequest) returns (stream Fish);
  rpc CurrentUsers (EmptyRequest) returns (stream CurrentUsersResponse);
  rpc Inventory (InventoryRequest) returns (InventoryResponse);
  rpc GetImage (ImageRequest) returns (ImageResponse);
}
```

- **Login** - unary RPC that returns a token composed from username and password.
- **UpdateLocation** - client-streaming RPC that registers a user and updates
  `(x, y)` coordinates.
- **ListUsers** - server-streaming RPC that returns the current user snapshot.
- **StartFishing** - server-streaming RPC that emits caught fish, if any.
- **CurrentUsers** - server-streaming RPC that emits the current count and later
  count changes.
- **Inventory** - unary RPC that returns the in-memory fish inventory.
- **GetImage** - unary RPC that returns the bytes from the configured image
  file.

---

## Future Work

1. **Persistence Layer** – Integrate PocketBase (or another database) for durable storage and centralized data.  
2. **Dynamic Server Discovery** – Given an (x, y) coordinate, route the client to the responsible tile server.  
3. **Multi‑Server Client** – Build a client that can subscribe to multiple servers simultaneously, enabling seamless map rendering across tiles.  
4. **Load Balancing & Auto‑Scaling** – Use a service mesh or Kubernetes to automatically scale nodes based on player density.  
5. **Security Enhancements** – Token‑based auth, rate limiting, and data validation.
