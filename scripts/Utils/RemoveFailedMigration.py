#!/usr/bin/env python3
# coding: utf-8
from __future__ import print_function
from __future__ import division

import os
from  datetime import datetime
import argparse

from dbs.apis.dbsClient import DbsApi

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', help='migrationId to be removed', required=True)
    args = parser.parse_args()
    migrationId = int(args.id)

    # if X509 vars are not defined, use default Publisher location
    userProxy = os.getenv('X509_USER_PROXY')
    if userProxy:
        os.environ['X509_USER_CERT'] = userProxy
        os.environ['X509_USER_KEY'] = userProxy
    if not os.getenv('X509_USER_CERT'):
        os.environ['X509_USER_CERT'] = '/data/certs/servicecert.pem'
    if not os.getenv('X509_USER_KEY'):
        os.environ['X509_USER_KEY'] = '/data/certs/servicekey.pem'

    migUrl = 'https://cmsweb-prod.cern.ch/dbs/prod/phys03/DBSMigrate'
    apiMig = DbsApi(url=migUrl, debug=True)

    status = apiMig.statusMigration(migration_rqst_id=migrationId)
    if not status:
        print("Migration with ID: %d does not exist" % migrationId)
        return
    state = status[0].get("migration_status")

    if not state == 9:
        stateName = {0:'created', 1:'in progress', 2:'done', 3:'failed but being retried', 9:'terminally failed'}
        print("%id is in state %d (%s), not 9" % (migrationId, state, stateName[state]))
        print("This migrationId is not terminally failed. Will not remove it")
        return

    # before removing it, print what it was about, just in case
    tFromEpoch = status[0].get("creation_date")
    created = datetime.fromtimestamp(tFromEpoch).strftime('%Y-%m-%d %H:%M:%S')
    creator = status[0].get("create_by")
    block = status[0].get("migration_input") # CRAB migrations are always one block at a time
    print("migrationId: %d was created on %s by %s for block:" % (migrationId, created, creator))
    print(" %s" % block)

    answer = input("Do you want to remove it ? Yes/[No]: ")
    if answer in ['Yes', 'YES', 'Y', 'y', 'yes']:
        answer = 'Yes'
    if answer != 'Yes':
        return

    print("\nRemoving it...")
    try:
        apiMig.removeMigration({'migration_rqst_id': migrationId})
    except Exception as ex:
        print("Migration removal returned this exception:\n%s" % str(ex))
    print("Migration %d removed\n" % migrationId)
    print("CRAB Publisher will issue such a migration request again as/when needed.")
    print("But if you want to re-create it now, you can by answering yes here")
    answer = input("Do you want to re-create the migration request ? Yes/[No]: ")
    if answer in ['Yes', 'YES', 'Y', 'y', 'yes']:
        answer = 'Yes'
    if answer != 'Yes':
        return
    print("\nSubmitting new migration request...")
    globUrl = 'https://cmsweb-prod.cern.ch/dbs/prod/global/DBSReader'
    data = {'migration_url': globUrl, 'migration_input': block}
    result = apiMig.submitMigration(data)[0]
    newId = result.get('migration_details', {}).get('migration_request_id')
    print('new migration created: %d' % newId)
    status = apiMig.statusMigration(migration_rqst_id=newId)
    print(status)
    return

if __name__ == '__main__':
    main()
