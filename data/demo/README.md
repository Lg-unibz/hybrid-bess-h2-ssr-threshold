# Demo Data

The files under `seasonal_weeks/` are synthetic and non-confidential.
They are designed to preserve the hourly column schema used by the model:

- `timestamp`
- `season`
- `demand_kwh`
- `pv_production_kwh`
- `price_buy_eur_kwh`
- `price_sell_eur_kwh`

They do not contain measured electricity-demand values from the case-study company.
Regenerate them with:

```bash
python scripts/create_demo_dataset.py
```

