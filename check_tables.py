#!/usr/bin/env python3
import psycopg2
import sys

try:
    conn = psycopg2.connect('dbname=mlops user=mlops password=mlops host=postgres-mlops port=5432')
    cur = conn.cursor()
    
    # Get counts
    cur.execute('SELECT COUNT(*) FROM retraining_decisions')
    dec_count = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM model_versions')  
    mod_count = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM monitoring_metrics')
    mon_count = cur.fetchone()[0]
    
    print(f'retraining_decisions: {dec_count}')
    print(f'model_versions: {mod_count}')
    print(f'monitoring_metrics: {mon_count}')
    
    if mod_count > 0:
        cur.execute('SELECT id, version, stage FROM model_versions ORDER BY updated_at DESC LIMIT 3')
        print('\nLatest model_versions:')
        for row in cur.fetchall():
            print(f'  Version {row[1]}: {row[2]}')
    
    conn.close()
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
