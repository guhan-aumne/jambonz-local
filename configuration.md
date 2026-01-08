# Jambonz Local PoC - Configuration & Setup Documentation

This document serves as a comprehensive Proof of Concept (PoC) reference for deploying jambonz locally using Docker Compose. It documents the UI-created configuration, explains how system components integrate, and captures all setup challenges encountered and resolved during deployment.

---

## Repository Overview

**What this repository provides:**  
A complete local deployment of [jambonz](https://www.jambonz.org/), an open-source CPaaS (Communications Platform as a Service) that enables programmable voice and messaging applications via webhooks and JSON-based call control.

**PoC Scope:**  
- Full jambonz microservices stack (12 containers) running via Docker Compose
- Pre-seeded MySQL database with default service provider, account, applications, and SIP users
- SIP client registration (MicroSIP) calling a cloud-hosted "hello world" application
- Inbound call routing from local SIP clients to jambonz applications

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Docker Compose Stack                             │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤
│   MySQL     │   Redis     │  InfluxDB   │  FreeSWITCH │   RTPEngine     │
│  (jambones) │   (cache)   │ (metrics)   │   (media)   │    (RTP)        │
├─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┤
│                                                                         │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │drachtio  │  │ sbc-inbound  │  │ sbc-outbound │  │  sbc-call-router │ │
│  │ (SIP)    │  │              │  │              │  │                  │ │
│  └────┬─────┘  └──────────────┘  └──────────────┘  └──────────────────┘ │
│       │                                                                 │
│  ┌────┴────────────────┐  ┌───────────────────┐  ┌────────────────────┐ │
│  │ sbc-sip-sidecar     │  │  feature-server   │  │    api-server      │ │
│  │ (SIP registration)  │  │  (call handling)  │  │    (REST API)      │ │
│  └─────────────────────┘  └───────────────────┘  └────────────────────┘ │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                         webapp (UI)                                │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
         │                                          │
         │ SIP (UDP/TCP 5060)                       │ HTTP (:3001 UI, :3000 API)
         ▼                                          ▼
    ┌────────────┐                              ┌──────────┐
    │ MicroSIP   │                              │ Browser  │
    │(Softphone) │                              │          │
    └────────────┘                              └──────────┘
```

---

## How Components Work Together

### 1. Docker Compose (`docker-compose.yaml`)

Orchestrates 12 microservices required for a complete jambonz deployment:

| Service | Purpose | Ports Exposed |
|---------|---------|---------------|
| `mysql` | Persistent database (schema + seed data) | - |
| `redis` | Session state & caching | - |
| `influxdb` | Time-series metrics | - |
| `drachtio` | SIP server (entry point for SIP traffic) | **5060/udp, 5060/tcp**, 9022 |
| `freeswitch` | Media server (TTS, recording, conferencing) | 8021, 30000-30100/udp |
| `rtpengine` | RTP proxy for media relay | 22222/udp, 40000-40100/udp |
| `sbc-inbound` | Handles inbound SIP calls | - |
| `sbc-outbound` | Handles outbound SIP calls | - |
| `sbc-call-router` | Routes calls to feature servers | - |
| `sbc-sip-sidecar` | SIP device registration | - |
| `feature-server` | Executes jambonz applications | - |
| `api-server` | REST API for management | **3000** |
| `webapp` | Admin UI | **3001** |

### 2. Database Seed Script (`init-db.sql`)

The `init-db.sql` file is mounted into MySQL and executed on first container start. It contains:

- **Complete jambonz schema** (cloned from `jambonz-api-server/db/jambones-sql.sql`)
- **Pre-configured seed data:**
  - Service provider: `default service provider`
  - Account: `default account`
  - Applications: `hello world`, `dial time`
  - Webhooks pointing to `https://public-apps.jambonz.cloud/`
  - Admin user: `joe@foo.bar` / password: `admin`
  - API keys for programmatic access
  - Predefined carriers (Twilio, Voxbone, Simwood, TelecomsXChange)

### 3. Drachtio Configuration (`drachtio.conf.xml`)

The drachtio SIP server configuration specifies:

```xml
<drachtio>
    <admin port="9022" secret="cymru">0.0.0.0</admin>
    <sip>
        <contacts>
            <contact external-ip="192.168.1.45" local-net="172.18.0.0/16">
                sip:*:5060;transport=udp,tcp
            </contact>
        </contacts>
    </sip>
    <logging>
        <loglevel>debug</loglevel>
        <sofia-loglevel>3</sofia-loglevel>
    </logging>
</drachtio>
```

**Key settings:**
- `external-ip`: Your host machine's LAN IP (SIP clients connect here)
- `local-net`: Docker network CIDR (for NAT traversal)
- `port 9022`: Admin port for jambonz microservices to connect

---

## UI Configuration Reference

The following configurations were created via the jambonz web UI (http://localhost:3001) and are pre-seeded in the database:

### Account Configuration

```yaml
account:
  sid: 9351f46a-678c-43f5-b8a6-d4eb58d131af
  name: default account
  max_calls: 0              # 0 = unlimited
  sip_realm: sip.jambonz.local
  webhook_secret: wh_secret_cJqgtMDPzDhhnjmaJH6Mtk
  sip_application:
    name: hello world
    purpose: inbound SIP device calls
```

### System Settings

```yaml
system:
  domain_name: jambonz.local
  sip_domain_name: sip.jambonz.local
  private_network_cidr: 172.18.0.0/16
  monitoring_domain_name: monitoring.jambonz.local
  log_level: debug
  admin_type: service_provider
```

### SIP Users (Clients)

```yaml
sip_users:
  - username: "1001"
    password: "password"
  - username: "1002"
    password: "password"
```

> SIP registration domain: `sip:sip.jambonz.local`

### Application Configuration

```yaml
application:
  sid: 7087fe50-8acb-4f3b-b820-97b573723aab
  name: hello world
  account: default account

  calling_webhook:
    url: https://public-apps.jambonz.cloud/hello-world
    method: POST
    auth: none

  call_status_webhook:
    url: https://public-apps.jambonz.cloud/call-status
    method: POST
    auth: none

  speech_synthesis:
    vendor: google
    language: en-US
    voice: Wavenet-C

  speech_recognition:
    vendor: google
    language: en-US
```

### Carrier Configuration (Inbound SIP Gateway)

```yaml
carrier:
  name: Test
  active: true

  inbound:
    allowed_ips:
      - network: 192.168.1.45   # Host machine IP
        netmask: 32

  outbound: disabled
  registration: disabled

  media:
    pad_crypto: true
```

---

## MicroSIP Softphone Configuration

```yaml
Account Name: Jambonz
SIP Server: sip.jambonz.local
SIP Proxy: 192.168.1.45    # Host machine LAN IP

Username: 1001
Login: 1001
Password: password

Domain: sip.jambonz.local
Transport: UDP

# Full SIP URI for registration:
sip_uri: sip:1001@sip.jambonz.local
```

> **Important:** Both `SIP Server` (domain) AND `SIP Proxy` (IP) must be configured for successful registration when the domain is not DNS-resolvable.

---

## Setup Challenges & Resolutions

This section documents all issues encountered during the local deployment setup and how each was resolved.

### 1. Initial Minimal Setup Failure

**Problem:** Attempted to run jambonz with only essential containers (mysql, redis, drachtio, api-server, webapp). SIP registration and call handling failed.

**Resolution:** Jambonz requires the complete "mini" microservices stack. All 12 services are interdependent:
- `sbc-sip-sidecar` handles SIP REGISTER requests
- `sbc-inbound` / `sbc-outbound` handle call routing  
- `sbc-call-router` routes to `feature-server`
- `feature-server` executes application logic

**Lesson:** Do not attempt to reduce the container count—each microservice has a specific responsibility.

---

### 2. Proper Database Seeding

**Problem:** Empty database caused UI to fail loading, and manually created configurations lacked proper foreign key relationships.

**Resolution:** Cloned the complete schema from `jambonz-api-server/db/jambones-sql.sql` and merged it with seed data from `seed-production-database-open-source.sql`. The combined `init-db.sql` creates:
- All required tables with proper indexes and foreign keys
- Default service provider and account
- Pre-configured applications with webhook references
- Admin user with proper permissions

**Lesson:** Use the official jambonz-api-server schema as source of truth for database structure.

---

### 3. Why Direct SQL Injection Was Avoided

**Problem:** Considered inserting SIP users and carriers directly via SQL.

**Resolution:** This approach was avoided because:
- UI-created configurations establish proper foreign key relationships
- Some records require associated webhook entries in separate tables
- Password hashing and encryption secrets are handled by the API
- The UI generates proper UUIDs and validates referential integrity

**Lesson:** Use the jambonz UI or REST API for configuration—not raw SQL—to ensure data integrity.

---

### 4. Port Exposure and Drachtio Entry Point

**Problem:** SIP clients could not reach jambonz from the host network.

**Resolution:** Drachtio is the **only SIP entry point** and must expose:
- `5060/udp` - Primary SIP signaling (most softphones use UDP)
- `5060/tcp` - Alternative SIP transport
- `9022` - Admin port for internal microservice connections

Docker Compose port mapping:
```yaml
ports:
  - "5060:5060/udp"
  - "5060:5060/tcp"
  - "9022:9022"
```

**Lesson:** Drachtio handles all external SIP traffic—no other containers need SIP ports exposed.

---

### 5. Windows Firewall Permissions

**Problem:** SIP traffic blocked by Windows Firewall even with correct port exposure.

**Resolution:** Create inbound firewall rules:
```powershell
# Allow SIP signaling
New-NetFirewallRule -DisplayName "Jambonz SIP UDP" -Direction Inbound -Protocol UDP -LocalPort 5060 -Action Allow
New-NetFirewallRule -DisplayName "Jambonz SIP TCP" -Direction Inbound -Protocol TCP -LocalPort 5060 -Action Allow

# Allow RTP media (if needed for audio)
New-NetFirewallRule -DisplayName "Jambonz RTP" -Direction Inbound -Protocol UDP -LocalPort 30000-30100 -Action Allow
```

**Lesson:** Windows firewall operates independently of Docker port mapping.

---

### 6. Drachtio Configuration XML Updates

**Problem:** After modifying `drachtio.conf.xml`, changes were not taking effect.

**Resolution:** Drachtio does not hot-reload configuration. After any XML changes:
```bash
docker-compose restart drachtio
```

Additionally, ensure the XML syntax is valid—drachtio may fail silently with malformed config. Key configuration points:
- `external-ip` must match your host's LAN IP
- `local-net` must match Docker's network CIDR (172.18.0.0/16)
- Admin `secret` must match `DRACHTIO_SECRET` in other containers

**Lesson:** Always restart drachtio after config changes and verify syntax.

---

### 7. Drachtio External IP Configuration

**Problem:** SIP clients received responses with internal Docker IPs, causing one-way audio or registration failures.

**Resolution:** The `external-ip` attribute in drachtio.conf.xml must be set to your host machine's **actual LAN IP address**:
```xml
<contact external-ip="192.168.1.45" local-net="172.18.0.0/16">
```

This enables drachtio to rewrite SIP headers with the correct external address for NAT traversal.

**Lesson:** Update `external-ip` whenever the host's IP changes.

---

### 8. MicroSIP Domain + Proxy Configuration

**Problem:** MicroSIP failed to register when only `SIP Server` was set to the domain name.

**Resolution:** MicroSIP (and similar softphones) require **both**:
- `SIP Server` / `Domain`: `sip.jambonz.local` (used in SIP headers)
- `SIP Proxy`: `192.168.1.45` (actual IP to send packets to)

Since `sip.jambonz.local` is not DNS-resolvable, the proxy field provides the IP routing while the domain maintains proper SIP addressing.

**Lesson:** For non-DNS-resolvable domains, configure both domain name and proxy IP in softphone settings.

---

## Quick Start

1. **Clone and navigate:**
   ```bash
   cd jambonz
   ```

2. **Update drachtio.conf.xml with your LAN IP:**
   ```xml
   <contact external-ip="YOUR_LAN_IP" local-net="172.18.0.0/16">
   ```

3. **Start the stack:**
   ```bash
   docker-compose up -d
   ```

4. **Access the UI:**
   - Web UI: http://localhost:3001
   - Default login: `joe@foo.bar` / `admin`

5. **Configure MicroSIP:**
   - SIP Server: `sip.jambonz.local`
   - SIP Proxy: `YOUR_LAN_IP`
   - Username: `1001` / Password: `password`

6. **Make a test call:**
   - Dial any number from MicroSIP
   - Hear the "hello world" greeting from the cloud application

---

## File Manifest

| File | Purpose |
|------|---------|
| `docker-compose.yaml` | Complete microservices orchestration (12 services) |
| `init-db.sql` | Combined schema + seed data (from jambonz-api-server) |
| `drachtio.conf.xml` | Drachtio SIP server configuration |
| `configuration.md` | This documentation file |
| `jambonz-api-server/` | Cloned for schema reference |
| `freeswitch/` | FreeSWITCH log volume mount |