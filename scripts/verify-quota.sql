-- Read-only reconciliation for the operational or explicitly isolated test database.
\set ON_ERROR_STOP on
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;

SELECT version_num FROM alembic_version;

WITH counted AS (
    SELECT pool_id, count(*) AS seats FROM quota_allocations
    WHERE state IN ('HELD','CONFIRMED','RETAINED') GROUP BY pool_id
), movements AS (
    SELECT pool_id, sum(delta) AS seats FROM quota_ledger GROUP BY pool_id
)
SELECT count(*) AS inconsistent_pools FROM department_topic_quotas AS p
LEFT JOIN counted AS c ON c.pool_id=p.id LEFT JOIN movements AS m ON m.pool_id=p.id
WHERE p.occupied<>coalesce(c.seats,0) OR p.occupied<>coalesce(m.seats,0)
   OR p.occupied>p.maximum OR p.occupied<0;

WITH balances AS (
    SELECT application_id, pool_id, sum(delta) AS seats FROM quota_ledger
    GROUP BY application_id, pool_id HAVING sum(delta)<>0
), seats AS (
    SELECT application_id, pool_id FROM quota_allocations
    WHERE state IN ('HELD','CONFIRMED','RETAINED')
)
SELECT count(*) AS inconsistent_application_pool_balances FROM balances AS b
FULL JOIN seats AS s USING (application_id, pool_id)
WHERE b.seats IS DISTINCT FROM CASE WHEN s.application_id IS NULL THEN 0 ELSE 1 END;

SELECT count(*) AS invalid_transfer_pairs FROM (
    SELECT movement_id FROM quota_ledger WHERE kind='TRANSFER' GROUP BY movement_id
    HAVING count(*)<>2 OR count(DISTINCT pool_id)<>2 OR count(DISTINCT application_id)<>1
      OR min(delta)<>-1 OR max(delta)<>1 OR sum(delta)<>0
) AS invalid;

WITH releases AS (
    SELECT application_id, count(*) AS events,
        array_agg(pool_id) AS released_pools
    FROM quota_ledger
    WHERE kind<>'TRANSFER' AND delta=-1 GROUP BY application_id
)
SELECT count(*) AS inconsistent_terminal_releases FROM applications AS a
JOIN quota_allocations AS x ON x.application_id=a.id
LEFT JOIN releases AS r ON r.application_id=a.id
WHERE (a.state IN ('SEPARATED','INVALIDATED','REJECTED') AND x.state<>'RELEASED')
   OR (x.state='RELEASED' AND (coalesce(r.events,0)<>1 OR x.pool_id<>ALL(r.released_pools)))
   OR (x.state<>'RELEASED' AND r.events IS NOT NULL);

SELECT count(*) AS exception_decision_mismatches
FROM applications AS a JOIN quota_allocations AS x ON x.application_id=a.id
WHERE a.state IN ('SEPARATED', 'INVALIDATED') AND 1 <> (
    SELECT count(*) FROM academic_reconciliations AS c
    JOIN exception_case_events AS e ON e.case_id=c.id
    JOIN quota_ledger AS l ON l.application_id=a.id AND l.kind=e.action||'_RELEASE'
         AND l.pool_id=x.pool_id AND l.delta=-1
    WHERE c.application_id=a.id AND c.status='RESOLVED'
      AND e.facts->>'pool_id'=x.pool_id::text
      AND ((a.state='SEPARATED' AND c.kind='SEPARATION' AND e.action IN ('Q43','Q44','Q45','Q47'))
        OR (a.state='INVALIDATED' AND c.kind='INTEGRITY' AND e.action='INVALIDATE'))
);

SELECT count(*) AS unresolved_terminal_separation_tasks
FROM academic_reconciliations AS c JOIN applications AS a ON a.id=c.application_id
WHERE c.kind='SEPARATION' AND c.status='OPEN' AND a.state IN ('SEPARATED','INVALIDATED');

SELECT count(*) AS recorded_transfer_movements FROM
    (SELECT DISTINCT movement_id FROM quota_ledger WHERE kind='TRANSFER') AS movements;
SELECT state, count(*) AS applications FROM applications GROUP BY state ORDER BY state;
COMMIT;
