import xmlrpc.client
try:
    sock = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/object')
    module_id = sock.execute_kw('wigo_db', 2, 'admin', 'ir.module.module', 'search', [[['name', '=', 'wigo_cobranza']]])
    if module_id:
        print("Module ID found:", module_id[0])
        res = sock.execute_kw('wigo_db', 2, 'admin', 'ir.module.module', 'button_immediate_upgrade', [[module_id[0]]])
        print("Upgrade result:", res)
    else:
        print("Module not found")
except Exception as e:
    print("Error:", e)
