# The three.js learning loop

A browser-based embodied cognition environment for an SOV mind: objects with distinctiveness
markers in a 3D gerund field, a hand that reaches and pushes, and a tournament that learns
through interaction. Everything visible, everything inspectable, the market cognition
running in front of you.

## The scene

A three.js scene serves two roles at once: the rendered 3D world the human observer sees,
and the gerund field the SOV mind perceives.

### Objects

Each object has two layers:

- **The gerund mesh.** The coarse shape: a cup-shaped region, a table-shaped region, a
  ball-shaped region. This is what the mind sees as "resting," "supporting," "rolling."
  Low resolution. One gerund label per region.
- **The distinctiveness markers.** Small textured patches on the surface: a scratch, a
  bump, a color variation, a chip, an asymmetric worn spot. Each marker is unique across
  the entire scene. No two objects share the same set. The markers are placed intentionally:
  some on the front, some on the side, some hidden underneath. Their positions on the object
  define its orientation.

Markers are created at scene load. Each is a small geometry (a decal, a bump, a colored
patch) with a unique ID. The mind perceives them as distinctiveness molecules in the
tournament.

### The gerund field

The 3D scene IS the field. Every region of space has a gerund state:

- `resting` — an object sitting on a surface
- `supporting` — a surface bearing weight
- `anchoring` — the floor, the walls
- `sliding` — an object in motion on a surface
- `falling` — an object unsupported
- `held` — an object gripped by the hand
- `empty` — space with nothing doing anything

The field updates when objects move. The mind reads the field, not the renderer. The
renderer draws textures and lighting for the human. The mind reads gerund labels and
distinctiveness positions.

### The hand

A gerund region the mind controls. It has its own gerund states:

- `empty` — open, not gripping anything
- `reaching` — extending toward a region of the field
- `gripping` — closed around an object
- `releasing` — opening

The hand is part of the gerund field, not separate from it. Its distinctiveness markers
(finger shapes, knuckle positions) are molecules too.

## The distinctiveness molecules

Each marker on each object is a molecule that enters the tournament when visible:

```
molecule = {
  id: "cup_a_chip_rim",        // unique across the scene
  object: "cup_a",              // which object it belongs to
  position_on_object: [0.3, 0.9, 0.1],  // where on the object (local coords)
  position_in_field: [x, y, z],          // where in the gerund field (world coords)
  gerund_context: "resting",             // the gerund of the region it sits in
  quality: { roughness, depth, edge_profile },  // the distinctiveness properties
  bonds: [],                    // current bonds to other molecules
  receipts: [],                 // funding history
}
```

### What the molecules do

**Identity.** The chip molecule bonds with the worn-patch molecule and the crack molecule
on the same object. The bonded set IS cup A. No other bonded set in the scene matches.
Seeing the chip triggers resonance for the rest of the set — the mind expects the worn
patch before it sees it.

**Orientation.** The chip is at position [0.3, 0.9, 0.1] on the object. The worn patch is
at [0.7, 0.5, 0.0]. Their relative positions are the object's facing. Rotate the object:
the world-space positions change but the on-object positions don't. The mind reads
orientation from where the distinctiveness molecules sit relative to each other in the
field.

**Gerund tracking.** The chip's gerund context changes when the object moves: "resting" →
"sliding" → "resting." The chip didn't change. Its context did. The mind tracks the
object's gerund through its distinctiveness.

**Category recognition.** The chip's quality (rough edges, impact-consistent depth, at the
rim where cups get knocked) lands in a funded region of distinctiveness space. The worn
patch's quality (friction-consistent, where hands grip) lands in another funded region.
Each marker individually makes sense as real distinctiveness on a cup. Together they fill
the cup's distinctiveness template.

## The tournament

The standard Gerundelle tournament, operating on the distinctiveness molecules and the
gerund field:

### What competes

- Distinctiveness molecules from visible objects
- The hand's own molecules (its gerund state, its position in the field)
- Bonds between hand molecules and object molecules (the reaching bond)
- Want molecules from the ownership register (the pull toward unclaimed objects)
- Condition molecules from past interactions (funded knowledge about what happens when
  you push things)

### Bond strength as closeness

The bond between the hand and an object strengthens as the gerund regions between them
thin. This is computed from the field: count the intervening gerund regions between the
hand's position and the object's distinctiveness markers. Fewer intervening regions =
stronger bond = higher tournament score.

The mind doesn't measure distance. The tournament measures bond strength. The rendering
engine knows positions; the mind knows bonds.

### Attention as resolution

The tournament selects which molecules win slots. The winners get high-resolution
processing: precise marker positions, detailed quality assessment. Losers get coarse
processing: just the gerund label. This mirrors foveal attention — the mind allocates
resolution to where distinctiveness is, not uniformly.

## The interaction loop

### One reach

1. **See.** The scene renders. The gerund field updates. Visible distinctiveness molecules
   enter the tournament pool.

2. **Want.** The ownership register identifies unclaimed objects (gerund regions with
   distinctiveness not yet bonded to the hand). A want molecule forms for the nearest
   unclaimed object. Its pull enters the tournament.

3. **Bond.** The want molecule bonds with the target object's distinctiveness molecules.
   The bond is weak (many intervening gerund regions). But it has pull from the want, so
   it competes.

4. **Reach.** The bond wins a tournament slot. The mind extends the hand toward the object.
   The hand's gerund changes to "reaching." The gerund field updates: the hand's region
   moves through the intervening space.

5. **Strengthen.** Intervening gerund regions thin. The bond scores higher. It wins more
   slots. The pull increases. The reach direction is confirmed.

6. **Correct or continue.** If the bond weakens (wrong direction, intervening regions
   growing), it loses slots. The pull fades. The mind tries a different reaching direction.
   If the bond keeps strengthening, the reach continues.

7. **Contact.** The hand's gerund region and the object's gerund region share the field
   directly. No intervening regions. The bond is at maximum. Touch: a force-state change.
   A receipt on the conditions slot: "reaching toward this object's markers produces
   contact."

8. **Grip.** The hand closes. "Empty" becomes "gripping." "Resting" becomes "held." The
   object's distinctiveness molecules are now bonded to the hand's molecules directly. The
   want's slot funds. Territory claimed.

9. **Fund.** The entire reaching episode funds conditions: which direction worked, how the
   bond evolved, what the hand felt at contact. These conditions carry to the next reach
   by recall: the shape of the episode (reach toward visible markers → bond strengthens →
   contact → grip) is stored and recalled for the next object.

### One push

1. The mind releases the object on a surface. "Held" becomes "resting."
2. The mind pushes it. "Resting" becomes "sliding."
3. The object rotates during the slide. The distinctiveness markers' positions in the field
   change. The mind tracks: the chip was on the left, now it's on the right. The object
   rotated.
4. The object stops. "Sliding" becomes "resting." The markers settle in new field
   positions.
5. The conditions slot funds: "pushing this object from this side makes it slide and rotate
   this way."

### One occlusion

1. An object moves behind another object. Its distinctiveness markers leave the visual
   field.
2. The molecules go to storage with warming keys (the markers' IDs and qualities).
3. The mind looks around. New markers from a different angle appear. If any match the
   stored set's qualities, resonance fires: same object, seen from the other side.
4. If the object reappears entirely, the full set of molecules returns from storage. The
   identity is confirmed.
5. If the object does NOT reappear where expected, the prediction is contradicted. The
   slot reopens: "where is it?"

## The visualization

The browser shows two views side by side:

### The 3D scene (left panel)

The rendered world: objects on a table, a hand reaching, things moving. Standard three.js
rendering with textures, lighting, shadows. This is what the human sees. Overlaid:

- **Gerund field coloring.** Each region tinted by its gerund state: green for resting,
  blue for supporting, yellow for sliding, red for falling, purple for held. Toggle on/off.
- **Distinctiveness markers highlighted.** Each marker outlined with its molecule ID. The
  markers the mind is currently attending to (tournament winners) are brighter. Toggle
  on/off.
- **Bond lines.** Visible lines between bonded molecules: hand-to-object bonds, within-
  object identity bonds. Line thickness = bond strength. Toggle on/off.

### The tournament view (right panel)

A live visualization of the mind's internal state:

- **Active molecules.** A list or graph of molecules currently in the tournament pool, with
  their bond strengths and gerund contexts.
- **The ownership register.** Which objects are unclaimed, controlled, held, contested,
  lost. Color-coded by territory state.
- **The want.** Which want is active, its pull, the bond it flows through.
- **Conditions funded.** A running log of conditions the mind has learned: "reaching toward
  cup A's chip produces contact," "pushing cup B from the left makes it slide right."
- **Distinctiveness space.** A 2D projection of where each marker lands in distinctiveness
  space: funded regions (real, interacted with) vs unfunded regions (novel, not yet
  explored). Markers that land in funded regions are recognized. Markers in unfunded regions
  are unknown.

## The curriculum

### Level 1: three distinct objects, plain table

Three objects on a table, each heavily marked with 5-8 unique distinctiveness markers. The
objects are different shapes (cup, ball, box). The mind explores: reach, push, pick up,
rotate. Fund the basics: identity, orientation, gerund tracking, reaching conditions.

### Level 2: similar objects, subtle marks

Three cups, similar shapes, fewer markers (2-3 each). The mind must attend more carefully
to tell them apart. The tournament must select finer distinctiveness. The funded conditions
from level 1 (how reaching works, how pushing works) carry over.

### Level 3: rotation and occlusion

Objects rotate and pass behind each other. The mind must track identity through rotation
(the markers move but the set stays) and through occlusion (the markers disappear and
reappear). Storage and recall are tested.

### Level 4: the fake

One CGI-generated object among real ones. Its markers are procedurally generated: too
regular, too clean, uncorrelated with forces. The mind's funded distinctiveness conditions
should flag it — its markers land in an unfunded region of distinctiveness space. Measured:
does the mind treat it differently? Does the conflation detector fire?

### Level 5: novel objects

An object the mind has never seen, with a shape it has never encountered. Its markers are
new. But the quality of its distinctiveness — rough edges on chips, wear where things
contact, asymmetry from use — lands in funded regions. The mind should recognize it as
real (the distinctiveness makes sense) without recognizing what it is (no category template
matches). The open slot: "what IS this?" The gerund field and interaction will answer.

## Implementation notes

### The gerund field as a spatial hash

The gerund field doesn't need to be a full voxel grid. A spatial hash maps regions of
the scene to gerund states. When an object moves, only its region and the regions it
enters and leaves are updated. The field is sparse: most of the scene is "empty" and
doesn't need a hash entry.

### Distinctiveness markers as decals

Three.js decals or custom shader patches on object surfaces. Each marker has a unique
texture, a position on the object (UV space), and a quality descriptor (roughness, depth,
edge profile) stored as metadata. The mind reads the metadata; the renderer draws the
texture.

### The tournament as a loop

Each frame:
1. Update the gerund field from the physics/scene state
2. Collect visible distinctiveness molecules (frustum culling + occlusion)
3. Run the tournament: score bonds, select winners, update experience records
4. The highest-pull action wins: reach direction, grip, push, or wait
5. Apply the action to the scene (move the hand, push an object)
6. Render both panels

The tournament runs in JavaScript, not in a shader. The molecules are plain objects. The
bonds are scored by structural fit (intervening regions, quality match, funded conditions).
The scene is three.js. The mind is the SOV algebra in JS.

### What this proves

A working three.js demo would prove:
- The gerund field is implementable as a spatial representation
- Distinctiveness molecules track identity, orientation, and category through the tournament
- The reaching bond strengthens by gerund-field convergence, not by distance
- The SOV mind learns from interaction without gradients
- The funded conditions transfer across objects and levels
- The distinctiveness space separates real from fake without labels

All in a browser. All visible. All inspectable.
