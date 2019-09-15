from sqlalchemy import event, DDL
from sqlalchemy.orm import sessionmaker
try:
    from core_framework.db_engine import DbEngine
    from core_framework.tables.tables import *
except:
    from db_engine import DbEngine
    from tables.tables import *

def ora_trigger(trigger, table, sequence, when=1):
    whens = {1: 'before insert', 2: 'before update'}
    sql = f'''create TRIGGER {trigger}
    {whens.get(when)} ON {table}
    FOR EACH ROW
    BEGIN
    select {sequence}.nextval into :new.id from dual;
    END;'''
    return sql


# ======================================================================
#                            DEPLOYMENT PART
# ======================================================================


class Deploy(DbEngine):
    def __init__(self, conn_id):
        DbEngine.__init__(self)
        self.engine = self.connect(conn_id, echo=False)
        self.start()

    def status(self):
        """return status of deployment 400 = failed, 200= success"""
        if self.engine == 400:
            return 400
        return 200

    def start(self):
        """deploying table structure if it is for first time.
        Don't use this method if you are migrating to another server."""
        if self.engine != 400:

            if self.db_type in ['ora']:
                # prepare triggers
                trigger_sql = DDL(ora_trigger('tr_proxy_list', ProxyListOra.__table__, 'proxy_list_seq'))
                event.listen(ProxyListOra.__table__, 'after_create', trigger_sql)

                trigger_sql = DDL(ora_trigger('tr_tor_list', TorListOra.__table__, 'tor_list_seq'))
                event.listen(TorListOra.__table__, 'after_create', trigger_sql)

                # create tables
                BaseOra.metadata.create_all(self.engine)

            elif self.db_type in ['ms']:
                # creates auto triggers and tables
                BaseMs.metadata.create_all(self.engine)

            elif self.db_type in ['pstg']:
                # creates auto triggers and tables
                BasePstg.metadata.create_all(self.engine)

            # add or remove data from tables
            session = sessionmaker(bind=self.engine)()

            # ============================================
            #           TABLE ROW DESCRIPTION
            # ============================================
            rows = dict()
            session_tables = {'ora': TableRowDescriptionOra, 'ms': TableRowDescriptionMS, 'pstg': TableRowDescriptionPstg}
            session_table = session_tables.get(self.db_type)
            [rows.update({len(rows): k}) for k in list_desc]
            # add new records, delete those that don't exist or changed in any way
            self.merge(session_table.__tablename__, rows, {}, delete=True)
            session.commit()

            # ============================================
            #       ANONYMITY CODES ROW DESCRIPTION
            # ============================================
            rows = dict()
            session_tables = {'ora': AnonymityCodesOra, 'ms': AnonymityCodesMS, 'pstg': AnonymityCodesPstg}
            session_table = session_tables.get(self.db_type)
            [rows.update({len(rows): k}) for k in anonymity_desc]
            # add new records, delete those that don't exist or changed in any way
            self.merge(session_table.__tablename__, rows, {}, delete=True)
            session.commit()

# api = Deploy(0)