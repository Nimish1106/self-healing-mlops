#!/usr/bin/env python3
import psycopg2

try:
    conn = psycopg2.connect('host=localhost port=5433 database=mlops user=mlops password=mlops')
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM retraining_decisions')
    dec_count = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM model_versions')
    mod_count = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM monitoring_metrics')
    mon_count = cur.fetchone()[0]
    
    print(f'retraining_decisions: {dec_count}')
    print(f'model_versions: {mod_count}')
    print(f'monitoring_metrics: {mon_count}')
    
    if dec_count > 0:
        cur.execute('SELECT id, timestamp, action, trigger_reason FROM retraining_decisions ORDER BY timestamp DESC LIMIT 3')
        print("\nLatest retraining_decisions:")
        for row in cur.fetchall():
            print(f"  {row}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
