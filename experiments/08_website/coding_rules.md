# Coding Rules: External Configuration

All configuration lives in external YAML files loaded at runtime.
Code loads config. Code does not contain config.

**The one exception:** algorithmic constants intrinsic to the code
itself may live in the code (`MAX_RETRIES = 3`, `DEFAULT_TIMEOUT = 30`).

## Examples

| Value | Where it lives |
|---|---|
| A URL or endpoint | YAML config file |
| A label, heading, or display string | YAML config file |
| A file path (except the config file itself) | YAML config file |
| `MAX_RETRIES = 3` | Code |

The path to the config file may be hardcoded as a single named constant.
