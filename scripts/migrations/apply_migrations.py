#!/usr/bin/env python3
import sqlite3
import glob
import os
DB='/Users/supeng/Documents/botong-ticket-system/tickets.db'
MIG_DIR=os.path.join(os.path.dirname(__file__), 'migrations')
if __name__=='__main__':
    files=sorted(glob.glob(os.path.join(MIG_DIR,'*.sql')))
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    for f in files:
        print('Applying',f)
        sql=open(f,'r',encoding='utf-8').read()
        try:
            cur.executescript(sql)
            conn.commit()
            print('Applied',f)
        except Exception as e:
            print('Failed',f,e)
    conn.close()
