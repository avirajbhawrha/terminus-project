# Fix Race Condition in Vehicle Damage Event Counter (Python)

The vehicle damage event aggregator at `/app/src/damage_aggregator.py` processes 50,000 damage inspection events across multiple concurrent worker threads and writes a summary report to `/app/output/counts.txt`. Under concurrent load, the aggregator produces incorrect results.

### Problems to Fix:
1. **Incorrect event counts**: When multiple worker threads record damage events simultaneously, non-atomic dictionary increments cause race conditions. Some event counts are lost or overwritten. The final report does not match the expected totals.
2. **Thread-safety violation**: The shared counter dictionary used for counting damage events is modified without thread synchronization (`threading.Lock` / `threading.RLock`), causing lost updates and data races under concurrent execution across worker threads.

### Constraints:
- The application must run via `python3 src/damage_aggregator.py <output_path>`.
- The output file must contain one line per damage event type in the format `TYPE=COUNT` (e.g., `SCRATCH=10000`).
- All 50,000 events must be accounted for in the final report (sum of all counts must equal 50,000, exactly 10,000 for each damage event type: `SCRATCH`, `DENT`, `CRACK`, `GLASS_DAMAGE`, `BROKEN_LAMP`).
- The application must complete without throwing any exceptions or unhandled errors.
- The entry point signature and CLI execution behavior must remain intact.

### Deliverables:
- Fix the concurrency bugs in `/app/src/damage_aggregator.py`.
- Ensure the output file `/app/output/counts.txt` is correct under concurrent execution.
