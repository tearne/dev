# Proposal: TUI Fixes
**Status: Approved**

## Intent
Two bugs in the interactive selection menu:
1. The guidance text (key hints) is set as `sub_title` on the `Header` widget, which
   centres it. On narrow terminals it is partially or fully hidden.
2. Pressing Enter does not confirm the selection — it toggles the focused item instead,
   identical to Space. This is because `SelectionList` has an internal Enter binding
   that takes priority over the app-level binding.

## Scope
- **In scope**: fixing guidance text visibility; fixing Enter to confirm
- **Out of scope**: visual redesign beyond what is needed for the fix

## Delta

### MODIFIED
- **Behaviour — Installation Process**: no change; Enter confirming the selection is the
  intended behaviour already stated in the spec.
- Guidance text is moved from `Header.sub_title` (centred, clips on narrow terminals)
  to a left-aligned `Static` label widget rendered below the `SelectionList`, styled
  dimmed so it doesn't compete visually with the list.
- The `Header` `sub_title` is removed; the title is shortened to
  `"Dev Environment Setup"`.
- The Enter binding is given `priority=True` so it takes precedence over
  `SelectionList`'s internal Enter handler.
