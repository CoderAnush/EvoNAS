# Logging Review (RC1)

## Current Design

- Module loggers: `logging.getLogger(__name__)`  
- Bootstrap: `evonas.infrastructure.logging.setup.setup_logging`  
- Text formatter default; optional JSON (`JsonFormatter`) with UTC timestamps  
- Context hooks: `experiment_id`, `run_id`, `dataset`, `split`, `state`

## Consistency

| Area | Assessment |
|---|---|
| Levels | INFO for lifecycle/decisions; WARNING for recoverable decode failures |
| Noise | Mock fitness / lifecycle transitions are informative for demos; acceptable at INFO |
| Errors | Failures logged with `exception` in closed-loop recovery |

## RC1 Actions Taken

- No algorithm logging changes  
- Documented expected keys for operators  
- Recommend demo runs at INFO; research ablations may use DEBUG via CLI `--verbose` where available  

## Recommendations (future, non-blocking)

1. Propagate `decision_id` / `version_id` via `LoggerAdapter` in CL + Decision paths  
2. Add `EVONAS_LOG_LEVEL` env override  
3. Keep JSON logs for pipeline mode only
