# Interactive IAC diagrams

A static, dependency-free page with a real Simple / Complex tab switch.
The Simple view follows the README overview; Complex shows the separate
local and team-mail channels. The diagrams are editable SVG, not screenshots.

Open `index.html` directly in a browser, or serve this directory with a
static server. All five browser assets are local; no CDN, mail access,
tracking, account, package installation or agent process is needed.

```sh
node agentmail/diagram/test-switch.cjs
python3 agentmail/diagram/build.py
```

The build copies only `index.html`, `styles.css`, `switch.js`, `simple.svg`
and `complex.svg` into ignored `dist/`. That output can be hosted by any
static web host. A GitHub file link displays source, not a live HTML page.
Hosting is separate from pushing this source to the IAC repository.

The switch supports clicks, Left/Right, Home and End, with visible focus and
accessible tab/panel relationships. Without JavaScript, both diagrams remain
visible. On narrow screens the diagrams scroll horizontally to preserve
their labels. The image alternatives and captions summarize the connections.

When changing the diagrams, keep their relationships and labels aligned
with the Mermaid fallbacks in the root README. The standalone page does not
load or execute the toolkit, connection descriptor, local mail or team mail.
