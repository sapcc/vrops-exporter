Traceback (most recent call last):
  File "/usr/lib/python3.10/site-packages/flask/app.py", line 2447, in wsgi_app
    response = self.full_dispatch_request()
  File "/usr/lib/python3.10/site-packages/flask/app.py", line 1952, in full_dispatch_request
    rv = self.handle_user_exception(e)
  File "/usr/lib/python3.10/site-packages/flask/app.py", line 1821, in handle_user_exception
    reraise(exc_type, exc_value, tb)
  File "/usr/lib/python3.10/site-packages/flask/_compat.py", line 39, in reraise
    raise value
  File "/usr/lib/python3.10/site-packages/flask/app.py", line 1950, in full_dispatch_request
    rv = self.dispatch_request()
  File "/usr/lib/python3.10/site-packages/flask/app.py", line 1936, in dispatch_request
    return self.view_functions[rule.endpoint](**req.view_args)
  File "/vrops-exporter/InventoryBuilder.py", line 127, in alert_alertdefinitions
    return self.alertdefinitions[alert_id]
KeyError: 'AlertDefinition-VMWARE-ClusterUnexpectedCPUWorkload'
Traceback (most recent call last):
  File "/vrops-exporter/./inventory.py", line 86, in <module>
    InventoryBuilder(os.environ.get('TARGET'), os.environ['PORT'], os.environ['SLEEP'])
  File "/vrops-exporter/InventoryBuilder.py", line 46, in __init__
    self.query_inventory_permanent()
  File "/vrops-exporter/InventoryBuilder.py", line 197, in query_inventory_permanent
    self.query_vrops(self.target, vrops_short_name, self.iteration)
  File "/vrops-exporter/InventoryBuilder.py", line 243, in query_vrops
    vcenter_adapter = self.create_vcenter_objects(vrops, target, token, query_specs)
  File "/vrops-exporter/InventoryBuilder.py", line 287, in create_vcenter_objects
    Vrops.get_vms(vrops, target, token, [hs.uuid for hs in hosts], vcenter_adapter.uuid, query_specs=query_specs)
  File "/vrops-exporter/tools/Vrops.py", line 276, in get_vms
    return self.get_resources(target, token, adapterkind="VMWARE", resourcekinds=[resourcekind],
  File "/vrops-exporter/tools/Vrops.py", line 184, in get_resources
    "parent": resource.get("relatedResources", [])[0],
IndexError: list index out of range