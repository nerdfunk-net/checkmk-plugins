# directory_status — Checkmk plug-in

Monitors configured directories on Linux hosts:

- number of regular files in the directory (non-recursive)
- age of the newest file (modification time)

Thresholds for both values are configurable in WATO.

## Package layout

```
agents/plugins/directory_status
agents/cfg_examples/directory_status.cfg
cmk_addons/plugins/directory_status/
  agent_based/directory_status.py   # Check API v2
  rulesets/directory_status.py      # CheckParameters + AgentConfig
  bakery/directory_status.py        # Agent bakery
  graphing/directory_status.py
  checkman/directory_status
```

## Install into a Checkmk site

### Option A: Extension package (.mkp)

Build the package from this repository:

```bash
./scripts/build_mkp.py
# -> dist/directory_status-1.0.0.mkp
```

Then on the Checkmk site:

```bash
mkp add /path/to/directory_status-1.0.0.mkp
mkp enable directory_status
cmk -R
```

Or upload it in the GUI: **Setup → Maintenance → Extension packages**.

### Option B: Copy files manually

As the site user:

```bash
SITE=~          # or /omd/sites/<sitename>
PLUGIN_SRC=/path/to/checkmk-plugin

mkdir -p "$SITE/local/lib/python3/cmk_addons/plugins"
mkdir -p "$SITE/local/share/check_mk/agents/plugins"
mkdir -p "$SITE/local/share/check_mk/agents/cfg_examples"

cp -a "$PLUGIN_SRC/cmk_addons/plugins/directory_status" \
  "$SITE/local/lib/python3/cmk_addons/plugins/"
cp "$PLUGIN_SRC/agents/plugins/directory_status" \
  "$SITE/local/share/check_mk/agents/plugins/"
chmod +x "$SITE/local/share/check_mk/agents/plugins/directory_status"
cp "$PLUGIN_SRC/agents/cfg_examples/directory_status.cfg" \
  "$SITE/local/share/check_mk/agents/cfg_examples/"

# Reload to pick up plug-ins
cmk -R
```

## Configuration

1. **Directories to monitor** (agent bakery)  
   Setup → Agents → Agent rules → **Directory status (Linux)**  
   Deploy the plug-in and list absolute directory paths.

2. **Thresholds**  
   Setup → Services → Service monitoring rules → **Directory status (file count and freshness)**  
   Set:
   - Maximum number of files
   - Maximum age of newest file

3. Activate changes, bake/sign agents if needed, update the agent on the host, then rediscover services.

### Manual agent config (without bakery)

On the monitored host, create `/etc/check_mk/directory_status.cfg` (or `$MK_CONFDIR/directory_status.cfg`):

```
/var/spool/incoming
/tmp/uploads
```

Install the agent plug-in to `/usr/lib/check_mk_agent/plugins/directory_status` and make it executable.

## Agent output

```
<<<directory_status:sep(124)>>>
/var/spool/incoming|ok|12|3600|report.csv
/tmp/uploads|ok|0||
/does/not/exist|missing|||
```

## Services

One service per directory: `Directory /path/to/dir`.
