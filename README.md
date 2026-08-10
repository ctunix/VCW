# VCW

VCW (Voice Cloning Workflow) is a local web interface for voice conversion,
model training, and real-time voice processing.

## Quick start

### 1. Create an environment

Python 3.12 is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

On Windows, activate the environment with:

```powershell
.venv\Scripts\activate
```

### 2. Install dependencies

Choose the requirements file that matches your hardware:

```bash
python -m pip install -r requirments_cpu_py312.txt
```

For NVIDIA systems, install the matching CUDA-enabled PyTorch build first,
then use `requirments_cu118_py312.txt` or `requirments_cu128_py312.txt`.

### 3. Start VCW

```bash
python webui.py
```

For a server without a desktop:

```bash
python webui.py --noautoopen
```

The default port is `7865`.

### Share securely with a Cloudflare Quick Tunnel

Install `cloudflared`, then start VCW with a protected login and a free
Cloudflare Quick Tunnel:

```bash
python webui.py --noautoopen --tunnel
```

VCW prints a random password and the `trycloudflare.com` URL in the terminal
or notebook output. Log in as `vcw` with that password. A new password is
created every time it starts. To keep a specific password, set `VCW_PASSWORD`
before launching. Quick Tunnel URLs are temporary and should only be shared
with people you trust.

The **VCW Workflow** tab accepts a ZIP containing WAV files, creates a
training folder for the existing Training tab, and creates a downloadable ZIP
containing the exported model and index after training.

## Models

Place model files in these folders:

```text
assets/weights/   # .pth models
assets/indices/   # .index files
```

Additional runtime models may be required under `assets/` and `logs/`. See
the included scripts and configuration files for the expected paths.

## License

VCW keeps the original project licenses and notices. Check `LICENSE` and the
license files in subdirectories before distributing changes.

## Credits

VCW is based on the original project:

https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI
