# Workflow Studio

Workflow Studio is the visual workflow editor at `/studio`. It uses XYFlow for
the canvas and the existing FlowPilot workflow API for persistence and
validation.

## Editor capabilities

- Searchable, expandable node library with click-to-add and drag-and-drop.
- Custom nodes for triggers, AI, logic, integrations, approvals, notifications,
  and output.
- Typed handles, condition true/false branches, duplicate-edge prevention, and
  basic invalid-connection prevention.
- Node selection, deletion, duplication, keyboard shortcuts, undo/redo,
  auto-layout, minimap, grid, pan, and zoom.
- Node-specific configuration fields plus JSON configuration editing.
- Saved workflow name, graph, node positions, edges, and viewport are persisted.
- Validate, test, publish, and execute actions are available from the toolbar.

## API

The Studio uses:

- `GET /api/v1/workflows`
- `POST /api/v1/workflows`
- `GET /api/v1/workflows/{id}`
- `PUT /api/v1/workflows/{id}`
- `POST /api/v1/workflows/{id}/validate`
- `POST /api/v1/workflows/{id}/publish`
- `GET /api/v1/workflows/{id}/versions`
- `POST /api/v1/workflows/{id}/execute`

All workflow operations are scoped to the authenticated user's workspace.
Draft edits create immutable `WorkflowVersion` snapshots. Publishing validates
the current draft, marks it published, and unpublishes older versions.
Execution selects the latest published version.

## Validation

The backend validates registered node types, node and edge identifiers,
required configuration fields, edge references, ports, trigger presence, and
cycles. Frontend validation provides immediate feedback, but backend
validation remains authoritative.

## Known limitations

- Validation errors currently use human-readable strings rather than a
  separate `{node_id, field}` error object.
- Integration nodes do not invent connection status; Gmail execution requires
  a real configured integration or the existing sandbox behavior.
- No frontend test runner existed in the repository when this milestone was
  implemented; production TypeScript/build verification and backend tests are
  used until a frontend test harness is introduced.
- The repository's database bootstrap already creates the existing workflow
  and version tables. No destructive migration is needed for this milestone;
  future schema changes should be added through the configured Alembic
  dependency.
