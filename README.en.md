# noblogs-backup-lite

**Complete and autonomous** backup of any [NoBlogs](https://noblogs.org) blog, packaged in a ZIP.
## Quick start (1 command, no installation)

Copy-paste one of these commands in a terminal:

| OS | Command |
|---|---|
| Linux / macOS / Tails | `bash -c "$(curl -fsSL https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.sh)"` |
| Linux / macOS (no curl) | `bash -c "$(wget -qO- https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.sh)"` |
| Windows (PowerShell) | `powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (irm https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.ps1) \| iex"` |

The tool is downloaded, installed into `~/noblogs-backup-lite` (on Tails: `~/Persistent/noblogs-backup-lite`), and the wizard starts right away. **Direct backup** of a blog in one command:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.sh)" -- backup myblog
```

The wizard asks for the slug of your blog and then backups everything into `backups/<slug>-noblogs-backup.zip`.
Only the first time, the tool automatically installs Python dependencies (1 to 2 min).

> **On Tails**: Python 3 is already included. The `python3-venv` package is not, but that's not a blocker: the tool builds its environment **without sudo or an administration password** (it installs `pip` itself, in your own space).

| Command | Action |
|---|---|
| `./noblogs` | Interactive wizard |
| `./noblogs backup myblog` | Backup → `backups/myblog-noblogs-backup.zip` |
| `./noblogs help` | Help |

> **Anonymity**: the tool uses neither Tor nor a proxy (direct HTTPS). For an anonymous backup, reboot into [Tails](https://tails.net): all traffic then goes through Tor.

## Features

| | |
|---|---|
| **Posts** | All, via paginated RSS feed (full content) |
| **Pages** | Static pages via WP REST API (paginated) |
| **Media** | Images, PDF, audio, video… with Wayback Machine rotation on 404 |
| **Attachments** | `<wp:attachment>` items in WXR (media attached to posts) |
| **Archive.org** | Wayback snapshot + `wayback/available` API |
| **Theme** | Download active theme (WordPress.org, original blog, archive.org) |
| **Fidelity** | Sidebars, menus, CSS, colors, banner |
| **Portable** | Minimal `requirements.txt` (requests + beautifulsoup4) |

## Manual installation (developers)

```bash
cd noblogs-backup-lite
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m backup myblog
```

> **Debian / Tails**: if `python3-venv` is missing, `python3 -m venv` fails. Use
> `python3 -m venv --without-pip .venv && curl -fsSL https://bootstrap.pypa.io/get-pip.py | .venv/bin/python3`
> then `source .venv/bin/activate && pip install -r requirements.txt` (no sudo required).

## Advanced options

```bash
python3 -m backup myblog --out-dir ~/backups
python3 -m backup myblog --base-url https://mirror.example.org
python3 -m backup blog1 blog2 blog3
python3 -m backup blogs.txt
python3 -m backup myblog --no-wayback
python3 -m backup myblog --no-media
python3 -m backup myblog --unpack --keep-uploads
```

## ZIP content

```
myblog-noblogs-backup.zip
├── wordpress-export.xml      # WordPress / WordPress.com import
├── uploads/                  # all media
├── theme/<theme>/            # active theme
├── fidelity.json             # widgets, menus, CSS, colors
├── README.md
└── metadata.json
```

The export can be re-imported into any WordPress instance (*Tools → Import → WordPress*), and `uploads/` should be placed into `wp-content/uploads/`.

## License

Inherited from the `~/mirroir` migration scripts. Reuse, modify, share.
