# Cost Tracking & Budget Limits - Implementation Plan

## Status: COMPLETE

## Tasks
- [x] 1. Add budget config to `src/config.py`
- [x] 2. Add `CostTracker` to `src/models.py`
- [x] 3. Update `src/scoring/scorer.py` - capture token usage
- [x] 4. Update `src/ingestion/twitter.py` - capture Apify cost
- [x] 5. Update `src/delivery/emailer.py` - track emails sent
- [x] 6. Create migration SQL `scripts/migrate_add_costs.sql` + update `init_db.sql`
- [x] 7. Update `src/db.py` - cost fields + budget queries
- [x] 8. Update `src/pipeline.py` - orchestrate cost tracking + budget gates
- [x] 9. Update `streamlit_app/app.py` - show costs in digest history
