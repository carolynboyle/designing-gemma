# animation.md

**Path:** experiments/03_srb_animation/prompts/animation.md
**Syntax:** markdown
**Generated:** 2026-05-14 07:38:25

```markdown
# Task: Sr. Barbara Animation Logic

You need to implement CSS animations for the nun sprite (#sr-barbara) in the sentence diagramming game. The goal is to provide visual feedback for three specific game states: approval (correct), disapproval (incorrect), and celebration (level complete).

## Implementation Details

### 1. CSS (static/css/style.css)
Define three keyframe animations. Keep them character-appropriate for a stern but encouraging nun:
- **Approval:** Maybe a subtle nod or a gentle "hop."
- **Disapproval:** A sharp horizontal shake (the classic "no").
- **Celebration:** Something more energetic—a sequence of scales or rotations.

### 2. JavaScript (static/js/ui.js)
You must hook into `handleChoice()` and `checkCompletion()`. 
- Do not touch `main.js`. 
- When an event occurs, add the corresponding CSS class to the `#sr-barbara` element.
- **The Reset Trick:** To ensure the animation triggers every time (even if the same event happens twice), you must remove the class before adding it, or use a `setTimeout` / `animationend` listener to clean up the DOM state. If the class stays on the element, the animation won't play again.

## Constraints
- Standard Web APIs only. No external libraries (No GSAP, no jQuery).
- Maintain the existing modular boundary; keep logic in `ui.js` and styles in `style.css`.
```
