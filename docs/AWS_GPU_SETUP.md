# Certainty Labs API — AWS GPU setup walkthrough

This guide walks you through running the Certainty Labs API on an AWS EC2 instance with a GPU. For a **serverless GPU option with no VM management**, see [MODAL_GPU_SETUP.md](./MODAL_GPU_SETUP.md). For Azure, see [AZURE_GPU_SETUP.md](./AZURE_GPU_SETUP.md). so training and inference are fast and reliable (no 502s or timeouts from shared hosting).

---

## 1. Prerequisites

- **AWS account** with permission to launch EC2 instances.
- **SSH key pair** in AWS (or create one in Step 2).
- **Project code** (this repo) and `requirements.txt` ready to deploy.

---

## 2. Launch an EC2 instance with a GPU

### 2.1 Choose region and go to EC2

1. In the AWS Console, select a **region** (e.g. `us-east-1`).
2. Open **EC2** → **Instances** → **Launch instance**.

### 2.2 Name and AMI

- **Name:** e.g. `certainty-labs-api`
- **AMI:** Use an image that already has NVIDIA drivers and CUDA (simplest):
  - **Option A (recommended):** **Deep Learning AMI** — search for “Deep Learning AMI GPU PyTorch” in the AMI picker (Amazon Linux 2 or Ubuntu). These come with CUDA, cuDNN, and Python/pip.
  - **Option B:** **Ubuntu 22.04 LTS**, then install NVIDIA drivers and CUDA yourself (see Appendix).

### 2.3 Instance type (GPU)

- **g4dn.xlarge** — 1 GPU (NVIDIA T4), 16 GB GPU RAM, good balance of cost and performance.
- **g5.xlarge** — 1 GPU (A10G), 24 GB GPU RAM, faster and more VRAM.
- **g4dn.2xlarge** — 1 T4, more vCPUs/RAM if you hit CPU or system RAM limits.

Use **g4dn.xlarge** to start; upgrade later if needed.

### 2.4 Key pair and network

- **Key pair:** Create a new key pair or select an existing one. **Download the `.pem` file** and keep it safe (you need it to SSH).
- **Network / Security group:**
  - Create or use a security group that allows:
    - **SSH (22)** from your IP (or a bastion).
    - **Custom TCP 8000** (or your chosen API port) from:
      - Your IP only (for testing), or
      - `0.0.0.0/0` if you want the API reachable from anywhere (e.g. for integration tests or a public frontend).

### 2.5 Storage

- **Root volume:** 30–50 GB is usually enough. Increase if you store large datasets on the instance.

### 2.6 Launch

- Click **Launch instance**. Wait until status is **Running** and note the **Public IPv4 address** (e.g. `54.123.45.67`).

---

## 3. Connect to the instance

From your laptop (terminal):

```bash
# Fix key permissions (required for SSH)
chmod 400 /path/to/your-key.pem

# SSH in (replace with your instance’s public IP and key path)
ssh -i /path/to/your-key.pem ec2-user@54.123.45.67
```

- **Deep Learning AMI (Amazon Linux):** user is usually `ec2-user`.
- **Deep Learning AMI (Ubuntu):** user is usually `ubuntu`.
- **Plain Ubuntu:** user is `ubuntu`.

If you get “Permission denied (publickey)”, double-check the key path, the key pair selected for the instance, and the username.

---

## 4. Install system dependencies (if needed)

**If you used a Deep Learning AMI**, Python 3 and CUDA are usually already there. Skip to Step 5.

**If you used plain Ubuntu**, install NVIDIA driver and CUDA, then reboot:

```bash
# Example for Ubuntu 22.04 (adjust for your version)
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3-pip
# Install NVIDIA driver + CUDA (follow NVIDIA/Ubuntu docs for your driver version)
# After reboot, verify: nvidia-smi
```

---

## 5. Deploy the Certainty Labs API

### 5.1 Get the project on the instance

**Option A — Clone from Git (if repo is public or you have SSH access):**

```bash
cd ~
git clone https://github.com/YOUR_ORG/Certainty_Labs.git
cd Certainty_Labs
```

**Option B — Copy from your machine with `scp`:**

From your **local** machine (in a new terminal):

```bash
cd /path/to/Certainty_Labs
scp -i /path/to/your-key.pem -r . ec2-user@54.123.45.67:~/Certainty_Labs
```

Then on the instance:

```bash
cd ~/Certainty_Labs
```

### 5.2 Create a virtual environment and install dependencies

On the **EC2 instance**:

```bash
cd ~/Certainty_Labs   # or wherever you put the project

# Create venv
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS

# Optional but recommended: install PyTorch with CUDA first (faster training)
# Pick the CUDA version that matches your driver (nvidia-smi shows it).
# Example for CUDA 11.8:
pip install torch --index-url https://download.pytorch.org/whl/cu118

# Install the rest from requirements.txt
pip install -r requirements.txt
```

If you skip the separate `torch` install, `pip install -r requirements.txt` will still work; PyTorch may install the CPU build by default. For GPU, installing `torch` with a `cu*` index before the rest is best.

### 5.3 Optional: environment variables

If you use Supabase for API keys or other secrets:

```bash
nano .env
# Add lines, e.g.:
# SUPABASE_URL=https://xxx.supabase.co
# SUPABASE_SERVICE_ROLE_KEY=your_key
```

Save and exit. The API will load `.env` from the project root.

### 5.4 Run the API

**One-off (foreground):**

```bash
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

- `--host 0.0.0.0` so the server listens on all interfaces (not only localhost).
- Leave this terminal open; closing it will stop the API.

**Check from the instance:**

```bash
curl http://localhost:8000/health
# Expect: {"status":"ok","version":"0.1.0"}
```

**Check from your laptop:**

```bash
curl http://54.123.45.67:8000/health
```

If that works, the API is reachable. If not, check the security group (port 8000 open to your IP or 0.0.0.0/0).

---

## 6. Keep the API running (systemd, optional)

So the API restarts on reboot and survives disconnects:

On the **EC2 instance**:

```bash
sudo nano /etc/systemd/system/certainty-api.service
```

Paste (adjust paths and user if needed):

```ini
[Unit]
Description=Certainty Labs API
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/Certainty_Labs
Environment="PATH=/home/ec2-user/Certainty_Labs/.venv/bin"
ExecStart=/home/ec2-user/Certainty_Labs/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable certainty-api
sudo systemctl start certainty-api
sudo systemctl status certainty-api
```

Use `journalctl -u certainty-api -f` to watch logs.

---

## 7. Run integration tests against the AWS API

From your **local** machine (with the repo and tests):

```bash
cd /path/to/Certainty_Labs
export CERTAINTY_BASE_URL=http://54.123.45.67:8000
python3 -m pytest tests/test_sdk_api_integration.py -v --tb=short
```

Replace `54.123.45.67` with your instance’s public IP (or a domain if you set one up). With the API on a proper GPU instance, timeouts and 502s from shared hosting should be gone.

---

## 8. Optional: domain and HTTPS

- **Domain:** Point a DNS A record (e.g. `api.yourdomain.com`) to the EC2 instance’s **Elastic IP** (allocate one in EC2 and assign it to the instance so the IP doesn’t change).
- **HTTPS:** Put the API behind something that terminates TLS:
  - **Application Load Balancer (ALB):** Create an ALB, add the instance to a target group (port 8000), attach a certificate (ACM), and use the ALB URL as `CERTAINTY_BASE_URL`.
  - Or run **Caddy** or **nginx** on the same instance as a reverse proxy with Let’s Encrypt.

---

## Quick reference

| Step | What to do |
|------|------------|
| 1 | Have AWS account + SSH key |
| 2 | Launch EC2: Deep Learning AMI or Ubuntu, **g4dn.xlarge** (or g5.xlarge), open ports 22 + 8000 |
| 3 | SSH: `ssh -i your-key.pem ec2-user@<PUBLIC_IP>` |
| 4 | (If not DL AMI) Install NVIDIA driver + CUDA, reboot |
| 5 | Put project on instance (git clone or scp), `python3 -m venv .venv`, `pip install torch` (CUDA), `pip install -r requirements.txt` |
| 6 | Run: `uvicorn api.main:app --host 0.0.0.0 --port 8000` (or use systemd) |
| 7 | Test: `CERTAINTY_BASE_URL=http://<PUBLIC_IP>:8000 pytest tests/test_sdk_api_integration.py -v` |

---

## Appendix: PyTorch CUDA versions

Match the index to your CUDA version (`nvidia-smi`):

- CUDA 11.8: `pip install torch --index-url https://download.pytorch.org/whl/cu118`
- CUDA 12.1: `pip install torch --index-url https://download.pytorch.org/whl/cu121`

Then run `pip install -r requirements.txt` so the rest of the stack (transformers, etc.) uses this PyTorch.
