Step-by-step build, deploy, and operate Chess-in-One on a Mac Mini using Tailscale Funnel, with zero public exposure.

1. Hardware & OS Baseline

Device: Mac Mini (dedicated)

OS: macOS (latest stable)

User: non-admin service account

Uptime: always-on

2. Install Core Dependencies
brew install docker docker-compose tailscale


Enable:

Docker Desktop (background)

Tailscale (login required)

3. Tailscale Setup (CRITICAL)
3.1 Authenticate Mac Mini
sudo tailscale up --ssh


Verify:

tailscale status

3.2 Enable Funnel (TLS Edge)
tailscale funnel 443 localhost:8080


✅ This creates:

https://<generated-name>.ts.net → localhost:8080


Invariants

Clients do NOT join tailnet

TLS terminates at Tailscale

Backend still binds to localhost only

4. Backend Build & Run
4.1 Environment
cd backend
cp .env.example .env


Populate:

DB credentials

Redis

Encrypted AI secrets (parent-provided later)

4.2 Start Services
docker-compose up -d


Verify:

curl http://127.0.0.1:8080/health

5. Security Verification Checklist

 lsof -i :8080 shows localhost only

 No public IP bound

 AI keys only in backend secrets

 PCI inaccessible with CHILD token

6. Client Usage Flow
Child

Create game

Annotate moves (voice/text)

Submit game

Answer guided questions

Read reflection

Parent

Login via Web PCI

Configure AI tiers

Approve escalation if requested

View usage & failures

7. Operational Commands
Restart Backend
docker-compose restart

View Logs (NO AI CONTENT)
docker-compose logs api

Shutdown
docker-compose down

8. Production Compliance Gate

Deployment is INVALID if any of the following are true:

Backend reachable without Funnel

AI appears before submission

Question order altered

Parent approval bypassed

AI provider visible to child

Prompts or responses logged

9. Recovery & Maintenance

AI failures require no redeploy

Resume works automatically

Parent notified on failure

No manual DB edits permitted