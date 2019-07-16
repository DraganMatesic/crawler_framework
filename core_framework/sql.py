def ora_trigger(trigger, table, sequence, when=1):
    whens = {1: 'before insert', 2: 'before update'}
    sql = f'''create TRIGGER {trigger}
    {whens.get(when)} ON {table}
    FOR EACH ROW
    BEGIN
    select {sequence}.nextval into :new.id from dual;
    END;'''
    return sql