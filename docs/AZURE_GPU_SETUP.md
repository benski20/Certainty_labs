# Certainty Labs API — Azure GPU setup walkthrough

This guide walks you through running the Certainty Labs API on an **Azure VM with a GPU**. For a **serverless GPU option with no VM management**, see [MODAL_GPU_SETUP.md](./MODAL_GPU_SETUP.md). For AWS, see [AWS_GPU_SETUP.md](./AWS_GPU_SETUP.md). so training and inference are fast and reliable (no 502s or timeouts from shared hosting).

---

## 1. Prerequisites

- **Azure account** ([azure.microsoft.com](https://azure.microsoft.com)).
- **SSH public key** (or you can use password auth; SSH key is recommended).
- **Project code** (this repo) and `requirements.txt` ready to deploy.

---

## 2. Create a resource group and GPU VM

### 2.1 Resource group

1. In the **Azure Portal**, search for **Resource groups** → **Create**.
2. **Subscription:** your subscription.
3. **Resource group:** e.g. `certainty-labs-rg`.
4. **Region:** e.g. `East US` (GPU VMs are not in every region; East US, West US 2, etc. have them).
5. Create.

### 2.2 Create the VM

1. Search for **Virtual machines** → **Create** → **Azure virtual machine**.

**Basics:**

- **Subscription / Resource group:** use the one you created (e.g. `certainty-labs-rg`).
- **Virtual machine name:** e.g. `certainty-labs-api`.
- **Region:** same as resource group (e.g. `East US`).
- **Security type:** Standard.
- **Image:** Use an image with GPU drivers and CUDA preinstalled (easiest):
  - **Option A (recommended):** **Ubuntu 22.04 LTS** — then in **Advanced** you can enable **GPU drivers** (see below), or
  - **Option B:** Search for **“Data Science Virtual Machine”** or **“Ubuntu 22.04 for GPU”** in the image marketplace (e.g. *Ubuntu 22.04 LTS – Gen2* with GPU extensions).
- **Size:** Click **See all sizes**, then search for **GPU**:
  - **NCasT4_v3** (1x NVIDIA T4, 4 vCPUs, 28 GB RAM) — good balance of cost and performance.
  - **NC4as_T4_v3** — similar T4 option.
  - **NC6s_v3** (1x V100) — faster, higher cost.
- **Authentication:** SSH public key (paste your `~/.ssh/id_rsa.pub` or create a new key) or Password.
- **Username:** e.g. `azureuser` (remember this for SSH).
- **SSH public key:** paste your key, or upload the `.pem` public part.

**Disks:**

- **OS disk:** 30–64 GB is usually enough (Premium SSD if you want better I/O).

**Networking:**

- **Virtual network:** create new or use existing.
- **Subnet:** default or new.
- **Public IP:** Yes (new).
- **NIC security group:** Create new or use existing — you will add rules in the next step.
- **Public inbound ports:** Allow **SSH (22)**.

Create the VM (you can skip “Management”, “Monitoring”, “Advanced” for a minimal setup). Wait until the VM status is **Running**.

### 2.3 Open port 8000 for the API

1. Go to the VM → **Networking** (or the **Network security group** attached to the VM’s NIC).
2. **Inbound port rules** → **Add rule**:
   - **Source:** Your IP (or **Any** for testing from anywhere).
   - **Source port ranges:** *.
   - **Destination:** Any.
   - **Service:** Custom.
   - **Destination port ranges:** `8000`.
   - **Protocol:** TCP.
   - **Action:** Allow.
   - **Priority:** e.g. 1010.
   - **Name:** e.g. `Allow-API-8000`.
3. Save.

### 2.4 Note the public IP

In the VM **Overview**, copy the **Public IP address** (e.g. `20.123.45.67`). You’ll use it for SSH and for `CERTAINTY_BASE_URL`.

---

## 3. Install NVIDIA driver and CUDA (if not preinstalled)

**If you chose a Data Science / GPU image**, the driver and CUDA are often already there. SSH in and run:

```bash
nvidia-smi
```

If that works, skip to Section 4.

**If you used plain Ubuntu 22.04**, install the driver and CUDA on the VM:

```bash
# Update and install build tools
sudo apt-get update
sudo apt-get install -y build-essential

# Install NVIDIA driver (example for Ubuntu 22.04; check Azure/NVIDIA docs for your image)
# Option 1: Azure’s script (if available on your image)
# curl -sL https://raw.githubusercontent.com/Azure/azhpc/main/scripts/install_nvidia_driver.sh | sudo bash

# Option 2: Ubuntu repo
sudo apt-get install -y nvidia-driver-535  # or newer, check nvidia-smi compatibility
sudo reboot
```

After reboot, SSH again and run `nvidia-smi`. Then install CUDA if needed (e.g. from NVIDIA’s repo for Ubuntu). Many PyTorch images work with the driver alone; you can try installing Python deps first and only add CUDA toolkit if pip’s CUDA build needs it.

---

## 4. Connect via SSH

From your **local** machine:

```bash
ssh azureuser@20.123.45.67
```

(Use the **username** you set when creating the VM and the VM’s **public IP**.)

If you use a key file:

```bash
ssh -i /path/to/your-private-key azureuser@20.123.45.67
```

---

## 5. Deploy the Certainty Labs API

### 5.1 Get the project on the VM

**Option A — Clone from Git (if repo is public or you have access):**

```bash
cd ~
git clone https://github.com/YOUR_ORG/Certainty_Labs.git
cd Certainty_Labs
```

**Option B — Copy from your machine with `scp`:**

From your **local** machine (new terminal):

```bash
cd /path/to/Certainty_Labs
scp -r . azureuser@20.123.45.67:~/Certainty_Labs
```

On the VM:

```bash
cd ~/Certainty_Labs
```

### 5.2 Python virtual environment and dependencies

On the **Azure VM**:

```bash
cd ~/Certainty_Labs

# Create venv
python3 -m venv .venv
source .venv/bin/activate

# Optional: install PyTorch with CUDA first (match CUDA version to nvidia-smi)
# For CUDA 11.8:
pip install torch --index-url https://download.pytorch.org/whl/cu118
# For CUDA 12.1:
# pip install torch --index-url https://download.pytorch.org/whl/cu121

# Install the rest from requirements.txt
pip install -r requirements.txt
```

### 5.3 Optional: environment variables

If you use Supabase (or other secrets):

```bash
nano .env
# Add, e.g.:
# SUPABASE_URL=https://xxx.supabase.co
# SUPABASE_SERVICE_ROLE_KEY=your_key
```

Save and exit.

### 5.4 Run the API

**One-off (foreground):**

```bash
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

- `--host 0.0.0.0` so the server listens on all interfaces.
- Keep this terminal open; closing it stops the API.

**Check from the VM:**

```bash
curl http://localhost:8000/health
# Expect: {"status":"ok","version":"0.1.0"}
```

**Check from your laptop:**

```bash
curl http://20.123.45.67:8000/health
```

Replace `20.123.45.67` with your VM’s public IP. If this fails, check the NSG rule for port 8000 (Section 2.3).

---

## 6. Keep the API running (systemd, optional)

On the **Azure VM**:

```bash
sudo nano /etc/systemd/system/certainty-api.service
```

Paste (adjust paths and user if different):

```ini
[Unit]
Description=Certainty Labs API
After=network.target

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/Certainty_Labs
Environment="PATH=/home/azureuser/Certainty_Labs/.venv/bin"
ExecStart=/home/azureuser/Certainty_Labs/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
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

Logs: `journalctl -u certainty-api -f`.

---

## 7. Run integration tests against the Azure API

From your **local** machine (in the repo):

```bash
cd /path/to/Certainty_Labs
export CERTAINTY_BASE_URL=http://20.123.45.67:8000
python3 -m pytest tests/test_sdk_api_integration.py -v --tb=short
```

Use your VM’s **public IP** (or a domain if you add one). With the API on an Azure GPU VM, long training requests should complete without 502s or timeouts.

---

## 8. Optional: static IP, domain, HTTPS

- **Static public IP:** In Azure, create a **Public IP** resource (static), then in the VM’s **Networking** → **NIC** → **IP configuration**, associate that IP so it doesn’t change after reboot.
- **Domain:** Point a DNS A record (e.g. `api.yourdomain.com`) to that static IP.
- **HTTPS:** Put the API behind something that terminates TLS:
  - **Azure Application Gateway** or **Azure Load Balancer** with an SSL certificate (e.g. from Azure or Let’s Encrypt), or
  - **Caddy** or **nginx** on the same VM as a reverse proxy with Let’s Encrypt.

---

## Quick reference

| Step | What to do |
|------|------------|
| 1 | Azure account + SSH key (or password) |
| 2 | Create resource group → Create VM: Ubuntu 22.04 or Data Science image, size **NCasT4_v3** (or NC4as_T4_v3), allow SSH (22) |
| 3 | Networking: add inbound rule **TCP 8000** (your IP or Any) |
| 4 | Note VM **public IP**, then SSH: `ssh azureuser@<PUBLIC_IP>` |
| 5 | (If needed) Install NVIDIA driver, reboot, `nvidia-smi` |
| 6 | Copy/clone project to VM → `python3 -m venv .venv` → `pip install torch` (CUDA) → `pip install -r requirements.txt` |
| 7 | Run: `uvicorn api.main:app --host 0.0.0.0 --port 8000` (or use systemd) |
| 8 | Test: `CERTAINTY_BASE_URL=http://<PUBLIC_IP>:8000 pytest tests/test_sdk_api_integration.py -v` |

---

## Azure GPU VM sizes (summary)

| Size | GPU | vCPUs | RAM | Use case |
|------|-----|-------|-----|----------|
| **NCasT4_v3** | 1× T4 | 4 | 28 GB | Good default, lower cost |
| **NC4as_T4_v3** | 1× T4 | 4 | 28 GB | Similar to above |
| **NC6s_v3** | 1× V100 | 6 | 112 GB | Faster training, higher cost |
| **ND96asr A100 v4** | 8× A100 | 96 | 900 GB | Large-scale training |

Start with **NCasT4_v3**; resize later if you need more CPU/RAM or a different GPU.

---

## Appendix: PyTorch CUDA versions

Match the index to the CUDA version on the VM (`nvidia-smi`):

- CUDA 11.8: `pip install torch --index-url https://download.pytorch.org/whl/cu118`
- CUDA 12.1: `pip install torch --index-url https://download.pytorch.org/whl/cu121`

Then run `pip install -r requirements.txt` so the rest of the stack uses this PyTorch.
